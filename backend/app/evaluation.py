"""Gerçek, izole ve açık sınırlara sahip yerel teknik doğrulama.

Bu modül bağımsız akademik benchmark iddiasında bulunmaz. Görüş başarısı
yalnızca burada açıkça tanımlanan küçük, elle etiketlenmiş iç senaryolarla
ölçülür; gecikme ise gerçek analiz motoru tekrar çalıştırılarak hesaplanır.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import math
import os
import time
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from statistics import mean, median
from uuid import uuid4

from .analyzer import analyze_post, build_custom_post, build_viewpoints_heuristic
from .argument_engine import invalidate_claim_cache_for
from .claim_cache import CACHE_MAX_ENTRIES
from .database import connection, meta_get, meta_set, transaction
from .demo import DEMO_POST
from .evaluation_holdout import HOLDOUT_SCENARIOS, holdout_dataset_info
from .evaluation_scenarios import SCENARIOS, scenario_dataset_info
from .stance_engine import classify_stances, status as stance_status
from .version import APP_VERSION


RESULT_META_KEY = 'technical_evaluation:last_result:v1'
SCENARIO_RESULT_META_KEY = 'technical_evaluation:last_scenario_result:v1'
HOLDOUT_RESULT_META_KEY = 'technical_evaluation:last_holdout_result:v1'
DATASET_NAME = 'N-KÖPRÜ elle etiketlenmiş iç doğrulama seti'
DATASET_VERSION = '2026.08.22-v1'
LIMITATION = (
    'Bu sonuç yalnızca 20 elle etiketlenmiş, küçük ve proje içi Türkçe '
    'doğrulama cümlesi için geçerlidir. Bağımsız veri seti, akademik benchmark '
    'veya gerçek kullanıcı performansı olarak yorumlanamaz.'
)

LABELS = (
    'Destekleyen',
    'Karşı / Sınırlayıcı',
    'Koşullu / Dengeli',
    'Soru / Tarafsız',
)

PROFILE_STAGES = (
    ('stance', 'Görüş sınıflandırması'),
    ('claims', 'İddia Radarı'),
    ('questions', 'Cevapsız Sorular'),
    ('common_ground', 'Ortak Zemin'),
    ('viewpoints', 'Görüş Haritası'),
    ('bridge', 'Köprü Oluştur'),
)

PROFILE_NOTE = (
    'Her katman aynı demo analizinin kendi çalışma aralığında yüksek '
    'çözünürlüklü zamanlayıcıyla ölçülür. Kalan süre; yorum hazırlığı, '
    'göstergeler, özet oluşturma ve sonuç nesnesi üretimini kapsar. '
    'İlk soğuk çalışma ile önbellekli tekrarlar ayrı gösterilir.'
)

MODEL_USAGE_NOTE = (
    'İç setteki görüş çıkarımları ile demo tartışmasındaki görüş ve İddia '
    'Radarı çıkarımları ayrı sayılır. Görüş sayacının sıfır olması tüm '
    'analiz hattında Transformer kullanılmadığı anlamına gelmez. '
    'Önbellekten kullanılan model kararları yeni çıkarım sayılmaz.'
)

CACHE_NOTE = (
    'İddia modelinin doğrulanmış kararı yalnızca aynı model, cihaz, tartışma '
    'başlığı ve tam yorum içeriği için süreç belleğinde yeniden kullanılır. '
    'İlk demo tekrarı gerçek soğuk çalışmadır; sonraki örnekler sıcak '
    'önbellekle ölçülür. Önbellek SQLite üzerinde tutulmaz.'
)

LABELED_CASES: tuple[tuple[str, str], ...] = (
    ('Yapay zekâ doğru kullanılırsa çok faydalı olur.', 'Destekleyen'),
    ('Tamamen yasaklamak yanlış, yararlı kullanım sürmeli.', 'Destekleyen'),
    ('Yapay zekâ kullanımının yasaklanmasına karşıyım.', 'Destekleyen'),
    ('Öğrencilerin bu araçları kullanması serbest olmalı.', 'Destekleyen'),
    ('Tamamen engellemek gerçekçi değil.', 'Destekleyen'),
    ('Kesinlikle yasaklanmalı, öğrenciler düşünmeyi bırakıyor.', 'Karşı / Sınırlayıcı'),
    ('Üniversitelerde yapay zekâ kullanımı yasaklanmalı.', 'Karşı / Sınırlayıcı'),
    ('Ödevin tamamını yapay zekâya yaptırmak ciddi sorun.', 'Karşı / Sınırlayıcı'),
    ('Bu kullanım öğrenciye zarar veriyor.', 'Karşı / Sınırlayıcı'),
    ('Bütün ödevi yapay zekâya yaptırmak ciddi problem.', 'Karşı / Sınırlayıcı'),
    ('Kontrollü kullanım ve açık kurallar gerekli.', 'Koşullu / Dengeli'),
    ('Üniversiteler ortak kullanım yönergesi hazırlamalı.', 'Koşullu / Dengeli'),
    ('Şeffaflık ve denetim altında kullanılabilir.', 'Koşullu / Dengeli'),
    ('Yasak yerine etik kullanım kuralları belirlenmeli.', 'Koşullu / Dengeli'),
    (
        'Ben ders çalışırken açıklama almak için kullanıyorum, ödevimi ona yazdırmıyorum.',
        'Koşullu / Dengeli',
    ),
    ('Bu konuda güvenilir bir araştırma var mı?', 'Soru / Tarafsız'),
    ('Öğrenmeyi azalttığını gösteren veri nedir?', 'Soru / Tarafsız'),
    ('Bu oranın kaynağı nerede?', 'Soru / Tarafsız'),
    ('Kaynak belirtilmediği sürece yüzde vermek çok anlamlı değil.', 'Soru / Tarafsız'),
    ('Öğrencilerin başarı düzeyi nasıl ölçülecek?', 'Soru / Tarafsız'),
)


def _dataset_info() -> dict:
    return {
        'name': DATASET_NAME,
        'version': DATASET_VERSION,
        'sample_count': len(LABELED_CASES),
        'label_count': len(LABELS),
        'label_distribution': {
            label: sum(expected == label for _, expected in LABELED_CASES)
            for label in LABELS
        },
        'is_external_benchmark': False,
        'limitation': LIMITATION,
    }


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    if len(ordered) == 1:
        return round(ordered[0], 2)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return round(ordered[lower], 2)
    weight = position - lower
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * weight, 2)


def _class_metrics(predictions: list[dict]) -> tuple[list[dict], list[dict], float, float]:
    predicted_extras = sorted(
        {item['predicted_label'] for item in predictions} - set(LABELS)
    )
    matrix_labels = [*LABELS, *predicted_extras]
    metrics = []
    confusion = []

    for label in LABELS:
        expected_rows = [item for item in predictions if item['expected_label'] == label]
        true_positive = sum(item['predicted_label'] == label for item in expected_rows)
        false_positive = sum(
            item['expected_label'] != label and item['predicted_label'] == label
            for item in predictions
        )
        false_negative = len(expected_rows) - true_positive
        precision = true_positive / max(1, true_positive + false_positive)
        recall = true_positive / max(1, true_positive + false_negative)
        f1 = 2 * precision * recall / max(1e-12, precision + recall)
        metrics.append({
            'label': label,
            'support': len(expected_rows),
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1': round(f1, 4),
        })
        confusion.append({
            'expected_label': label,
            'predicted_counts': {
                predicted: sum(item['predicted_label'] == predicted for item in expected_rows)
                for predicted in matrix_labels
            },
        })

    accuracy = sum(item['correct'] for item in predictions) / max(1, len(predictions))
    macro_f1 = mean(item['f1'] for item in metrics)
    return metrics, confusion, round(accuracy, 4), round(macro_f1, 4)


def _invariant(key: str, label: str, expected: str, actual: str, passed: bool) -> dict:
    return {
        'key': key,
        'label': label,
        'expected': expected,
        'actual': actual,
        'passed': bool(passed),
    }


def _demo_invariants(result) -> list[dict]:
    word_count = len(result.bridge.get('bridge_question', '').split())
    high_priority = sum(item.priority == 'Yüksek' for item in result.claims)
    open_count = int(result.indicators.get('unanswered_question_count', 0))
    unique_count = int(result.indicators.get('comment_count', 0))
    source_awareness = int(result.indicators.get('source_awareness', 0))
    stances = {item.comment_id: item.label for item in result.stance_details}
    contrast = result.bridge.get('contrast_viewpoint_names', [])
    return [
        _invariant(
            'raw_demo_comments', 'Demo ham yorum sayısı', '80', str(len(DEMO_POST.comments)),
            len(DEMO_POST.comments) == 80,
        ),
        _invariant(
            'unique_demo_comments', 'Tekilleştirilmiş yorum sayısı', '20', str(unique_count),
            unique_count == 20,
        ),
        _invariant(
            'source_awareness', 'Kaynak farkındalığı', '%25', f'%{source_awareness}',
            source_awareness == 25,
        ),
        _invariant(
            'open_questions', 'Açık kaynak / bilgi soruları', '2', str(open_count),
            open_count == 2,
        ),
        _invariant(
            'priority_claim', 'Yüksek öncelikli doğrulanabilir iddia', '1', str(high_priority),
            high_priority == 1,
        ),
        _invariant(
            'bridge_length', 'Köprü sorusu kelime sınırı', '≤ 28', str(word_count),
            0 < word_count <= 28,
        ),
        _invariant(
            'minority_in_bridge', 'Azınlık görüşünün Köprü kapsamı', 'Kısıtlama görüşü dahil',
            'Dahil' if 'Karşı / Sınırlayıcı' in contrast else 'Dahil değil',
            'Karşı / Sınırlayıcı' in contrast,
        ),
        _invariant(
            'bounded_use_guardrail', '#7 sınırlı kişisel kullanım', 'Koşullu / Dengeli',
            stances.get(7, 'Bulunamadı'), stances.get(7) == 'Koşullu / Dengeli',
        ),
        _invariant(
            'evidence_guardrail', '#11 kaynak/veri eleştirisi', 'Soru / Tarafsız',
            stances.get(11, 'Bulunamadı'), stances.get(11) == 'Soru / Tarafsız',
        ),
    ]


def _latency(samples: list[float], unique_comments: int) -> dict:
    typical = median(samples) if samples else 0.0
    cold = round(samples[0], 2) if samples else None
    warm_samples = [round(value, 2) for value in samples[1:]]
    warm_typical = median(warm_samples) if warm_samples else None
    return {
        'iterations': len(samples),
        'samples_ms': [round(value, 2) for value in samples],
        'minimum_ms': round(min(samples), 2) if samples else 0.0,
        'median_ms': round(typical, 2),
        'p95_ms': _percentile(samples, 0.95),
        'maximum_ms': round(max(samples), 2) if samples else 0.0,
        'mean_ms': round(mean(samples), 2) if samples else 0.0,
        'unique_comment_count': unique_comments,
        'raw_comment_count': len(DEMO_POST.comments),
        'estimated_comments_per_second': (
            round(unique_comments * 1000 / typical, 2) if typical > 0 else 0.0
        ),
        'cold_ms': cold,
        'warm_samples_ms': warm_samples,
        'warm_median_ms': round(warm_typical, 2) if warm_typical is not None else None,
        'warm_p95_ms': _percentile(warm_samples, 0.95) if warm_samples else None,
        'speedup_factor': (
            round(cold / warm_typical, 2)
            if cold is not None and warm_typical is not None and warm_typical > 0 else None
        ),
    }


def _read_torch_capabilities() -> dict:
    """Model yüklemeden mevcut PyTorch/CUDA çalışma koşullarını okur."""
    baseline = {
        'torch_available': False,
        'torch_version': None,
        'cuda_build_version': None,
        'cuda_available': False,
        'cuda_device_count': 0,
        'cuda_device_name': None,
        'probe_error': None,
    }

    try:
        if importlib.util.find_spec('torch') is None:
            return baseline
        torch = importlib.import_module('torch')
        baseline['torch_available'] = True
        baseline['torch_version'] = str(getattr(torch, '__version__', '')) or None
        baseline['cuda_build_version'] = getattr(getattr(torch, 'version', None), 'cuda', None)
        baseline['cuda_available'] = bool(torch.cuda.is_available())
        if baseline['cuda_available']:
            baseline['cuda_device_count'] = int(torch.cuda.device_count())
            if baseline['cuda_device_count']:
                baseline['cuda_device_name'] = str(torch.cuda.get_device_name(0))
    except Exception as exc:
        baseline['probe_error'] = f'{type(exc).__name__}: {exc}'

    return baseline


def _hardware_diagnostics(model_status: dict) -> dict:
    capabilities = _read_torch_capabilities()
    active_device = str(model_status.get('device') or 'cpu')
    model_loaded = bool(model_status.get('loaded'))
    acceleration_active = model_loaded and active_device.casefold().startswith('cuda')

    if capabilities['probe_error']:
        diagnosis_key = 'probe-error'
        diagnosis = (
            'PyTorch/CUDA bilgisi güvenli biçimde okunamadı; aktif model cihazı '
            f'{active_device} olarak bildiriliyor.'
        )
    elif not capabilities['torch_available']:
        diagnosis_key = 'torch-missing'
        diagnosis = 'PyTorch bulunamadı; Transformer ve CUDA hızlandırması kullanılamıyor.'
    elif acceleration_active:
        diagnosis_key = 'cuda-active'
        device_name = capabilities['cuda_device_name'] or 'CUDA aygıtı'
        diagnosis = f'Model CUDA üzerinde çalışıyor: {device_name}.'
    elif not capabilities['cuda_build_version']:
        diagnosis_key = 'cpu-only-torch'
        diagnosis = (
            'Kurulu PyTorch derlemesinde CUDA desteği yok; mevcut model CPU '
            'üzerinde çalışır. Fiziksel ekran kartı varlığı bu bilgiyle doğrulanamaz.'
        )
    elif not capabilities['cuda_available']:
        diagnosis_key = 'cuda-unavailable'
        diagnosis = (
            'PyTorch CUDA destekli ancak kullanılabilir CUDA aygıtı algılanmadı; '
            'mevcut çalışma CPU üzerindedir.'
        )
    elif model_loaded:
        diagnosis_key = 'cuda-ready-model-on-cpu'
        diagnosis = (
            'CUDA aygıtı kullanılabilir ancak mevcut model CPU üzerinde yüklü; '
            'GPU kullanımı için modelin yeniden yüklenmesi gerekir.'
        )
    else:
        diagnosis_key = 'cuda-ready-model-unloaded'
        diagnosis = (
            'CUDA aygıtı kullanılabilir; model yüklendiğinde GPU seçimi '
            'yeniden doğrulanacaktır.'
        )

    return {
        **capabilities,
        'active_device': active_device,
        'model_loaded': model_loaded,
        'acceleration_active': acceleration_active,
        'cpu_core_count': int(os.cpu_count() or 1),
        'diagnosis_key': diagnosis_key,
        'diagnosis': diagnosis,
    }


def _stage_profile(timings: list[float], demo_runs: list[dict]) -> dict:
    total_median = round(median(timings), 2) if timings else 0.0
    stages = []

    for key, label in PROFILE_STAGES:
        samples = [
            max(0.0, float(run.get('stage_profile_ms', {}).get(key, 0.0)))
            for run in demo_runs
        ]
        model_counts = [
            max(0, int(run.get(
                'transformer_count' if key == 'stance' else 'claim_transformer_count',
                0,
            ))) if key in {'stance', 'claims'} else 0
            for run in demo_runs
        ]
        cache_hits = [
            max(0, int(run.get('claim_cache_hit_count', 0))) if key == 'claims' else 0
            for run in demo_runs
        ]
        typical = round(median(samples), 3) if samples else 0.0
        warm_samples = samples[1:]
        stages.append({
            'key': key,
            'label': label,
            'samples_ms': [round(value, 3) for value in samples],
            'minimum_ms': round(min(samples), 3) if samples else 0.0,
            'median_ms': typical,
            'p95_ms': _percentile(samples, 0.95),
            'maximum_ms': round(max(samples), 3) if samples else 0.0,
            'mean_ms': round(mean(samples), 3) if samples else 0.0,
            'share_of_total_percent': round(typical * 100 / total_median, 1) if total_median else 0.0,
            'transformer_inference_counts': model_counts,
            'transformer_inference_total': sum(model_counts),
            'cold_ms': round(samples[0], 3) if samples else None,
            'warm_median_ms': round(median(warm_samples), 3) if warm_samples else None,
            'cache_hit_counts': cache_hits,
            'cache_hit_total': sum(cache_hits),
        })

    overhead = [
        max(0.0, elapsed - sum(
            max(0.0, float(run.get('stage_profile_ms', {}).get(key, 0.0)))
            for key, _ in PROFILE_STAGES
        ))
        for elapsed, run in zip(timings, demo_runs)
    ]
    bottleneck = max(stages, key=lambda item: (item['median_ms'], item['mean_ms']), default=None)
    if bottleneck is not None and bottleneck['median_ms'] <= 0:
        bottleneck = None
    cold_bottleneck = max(
        stages,
        key=lambda item: (item['cold_ms'] or 0.0, item['mean_ms']),
        default=None,
    )
    if cold_bottleneck is not None and (cold_bottleneck['cold_ms'] or 0.0) <= 0:
        cold_bottleneck = None

    return {
        'available': bool(demo_runs),
        'iterations': len(demo_runs),
        'stages': stages,
        'overhead_samples_ms': [round(value, 3) for value in overhead],
        'overhead_median_ms': round(median(overhead), 3) if overhead else 0.0,
        'bottleneck': ({
            'key': bottleneck['key'],
            'label': bottleneck['label'],
            'median_ms': bottleneck['median_ms'],
            'share_of_total_percent': bottleneck['share_of_total_percent'],
        } if bottleneck else None),
        'cold_bottleneck': ({
            'key': cold_bottleneck['key'],
            'label': cold_bottleneck['label'],
            'cold_ms': cold_bottleneck['cold_ms'],
        } if cold_bottleneck else None),
        'note': PROFILE_NOTE,
    }


def _model_usage(quality_result, predictions: list[dict], demo_runs: list[dict]) -> dict:
    internal_stance = sum(item['model_confidence'] is not None for item in predictions)
    internal_claim = max(0, int(quality_result.engine.get('claim_transformer_count', 0)))
    stance_counts = [max(0, int(run.get('transformer_count', 0))) for run in demo_runs]
    claim_counts = [max(0, int(run.get('claim_transformer_count', 0))) for run in demo_runs]
    cache_hit_counts = [max(0, int(run.get('claim_cache_hit_count', 0))) for run in demo_runs]
    cache_miss_counts = [max(0, int(run.get('claim_cache_miss_count', 0))) for run in demo_runs]
    last_demo = demo_runs[-1] if demo_runs else {}
    fresh_comment_ids = sorted({
        int(comment_id)
        for run in demo_runs
        for comment_id in run.get('claim_transformer_comment_ids', [])
    })
    model_comment_ids = sorted({
        int(comment_id)
        for run in demo_runs
        for comment_id in run.get('claim_model_comment_ids', [])
    })
    cache_comment_ids = sorted({
        int(comment_id)
        for run in demo_runs
        for comment_id in run.get('claim_cache_comment_ids', [])
    })

    return {
        'internal_set': {
            'sample_count': len(predictions),
            'structural_decision_count': len(predictions) - internal_stance,
            'stance_transformer_count': internal_stance,
            'claim_transformer_count': internal_claim,
            'total_transformer_count': internal_stance + internal_claim,
            'claim_transformer_comment_ids': list(
                quality_result.engine.get('claim_transformer_comment_ids', [])
            ),
        },
        'demo': {
            'available': bool(demo_runs),
            'iterations': len(demo_runs),
            'stance_transformer_counts': stance_counts,
            'claim_transformer_counts': claim_counts,
            'stance_transformer_total': sum(stance_counts),
            'claim_transformer_total': sum(claim_counts),
            'transformer_total': sum(stance_counts) + sum(claim_counts),
            'stance_transformer_per_run': stance_counts[-1] if stance_counts else 0,
            'claim_transformer_per_run': claim_counts[-1] if claim_counts else 0,
            'claim_transformer_comment_ids': fresh_comment_ids,
            'claim_model_comment_ids': model_comment_ids,
            'claim_cache_comment_ids': cache_comment_ids,
            'claim_cache_hit_counts': cache_hit_counts,
            'claim_cache_miss_counts': cache_miss_counts,
            'claim_cache_hit_total': sum(cache_hit_counts),
            'claim_cache_miss_total': sum(cache_miss_counts),
            'cold_claim_transformer_count': claim_counts[0] if claim_counts else 0,
            'warm_claim_transformer_counts': claim_counts[1:],
            'warm_claim_cache_hit_total': sum(cache_hit_counts[1:]),
        },
        'note': MODEL_USAGE_NOTE,
    }


def _cache_profile(timings: list[float], demo_runs: list[dict]) -> dict:
    hits = [max(0, int(run.get('claim_cache_hit_count', 0))) for run in demo_runs]
    misses = [max(0, int(run.get('claim_cache_miss_count', 0))) for run in demo_runs]
    total_hits = sum(hits)
    total_misses = sum(misses)
    warm_timings = [round(value, 2) for value in timings[1:]]
    warm_median = median(warm_timings) if warm_timings else None
    cold = round(timings[0], 2) if timings else None
    return {
        'available': bool(demo_runs),
        'storage': 'process-memory',
        'persistent': False,
        'max_entries': CACHE_MAX_ENTRIES,
        'cold_ms': cold,
        'warm_median_ms': round(warm_median, 2) if warm_median is not None else None,
        'warm_sample_count': len(warm_timings),
        'speedup_factor': (
            round(cold / warm_median, 2)
            if cold is not None and warm_median is not None and warm_median > 0 else None
        ),
        'hit_counts': hits,
        'miss_counts': misses,
        'hit_total': total_hits,
        'miss_total': total_misses,
        'hit_rate_percent': (
            round(total_hits * 100 / (total_hits + total_misses), 1)
            if total_hits + total_misses else 0.0
        ),
        'avoided_model_inference_count': total_hits,
        'note': CACHE_NOTE,
    }


def _normalize_saved_result(result: dict | None, hardware: dict) -> dict | None:
    if not isinstance(result, dict):
        return None
    if (
        'stage_profile' in result
        and 'model_usage' in result
        and 'hardware' in result
        and 'cache_profile' in result
    ):
        return result

    legacy = deepcopy(result)
    old_stance_count = max(0, int(result.get('transformer_inference_count', 0)))
    if 'stage_profile' not in legacy:
        legacy['stage_profile'] = {
        'available': False,
        'iterations': 0,
        'stages': [],
        'overhead_samples_ms': [],
        'overhead_median_ms': 0.0,
        'bottleneck': None,
        'note': (
            'Bu kayıt katman bazlı ölçüm eklenmeden önce oluşturuldu. '
            'Eksik değerler uydurulmaz; yeni gerçek ölçüm başlatın.'
        ),
        }
    legacy['stage_profile'].setdefault('cold_bottleneck', None)
    for stage in legacy['stage_profile'].get('stages', []):
        stage.setdefault('cold_ms', None)
        stage.setdefault('warm_median_ms', None)
        stage.setdefault('cache_hit_counts', [])
        stage.setdefault('cache_hit_total', None)
    if 'model_usage' not in legacy:
        legacy['model_usage'] = {
        'internal_set': {
            'sample_count': int(result.get('sample_count', 0)),
            'structural_decision_count': int(result.get('structural_decision_count', 0)),
            'stance_transformer_count': old_stance_count,
            'claim_transformer_count': None,
            'total_transformer_count': None,
            'claim_transformer_comment_ids': [],
        },
        'demo': {
            'available': False,
            'iterations': 0,
            'stance_transformer_counts': [],
            'claim_transformer_counts': [],
            'stance_transformer_total': None,
            'claim_transformer_total': None,
            'transformer_total': None,
            'stance_transformer_per_run': None,
            'claim_transformer_per_run': None,
            'claim_transformer_comment_ids': [],
        },
        'note': 'Eski ölçümde demo katmanlarının ayrı model sayaçları saklanmamıştır.',
        }
    demo = legacy['model_usage']['demo']
    for key in ('claim_model_comment_ids', 'claim_cache_comment_ids', 'claim_cache_hit_counts',
                'claim_cache_miss_counts', 'warm_claim_transformer_counts'):
        demo.setdefault(key, [])
    for key in ('claim_cache_hit_total', 'claim_cache_miss_total',
                'cold_claim_transformer_count', 'warm_claim_cache_hit_total'):
        demo.setdefault(key, None)
    for key in ('cold_ms', 'warm_median_ms', 'warm_p95_ms', 'speedup_factor'):
        legacy.setdefault('latency', {}).setdefault(key, None)
    legacy['latency'].setdefault('warm_samples_ms', [])
    legacy.setdefault('hardware', hardware)
    legacy['cache_profile'] = {
        'available': False,
        'storage': 'process-memory',
        'persistent': False,
        'max_entries': CACHE_MAX_ENTRIES,
        'cold_ms': None,
        'warm_median_ms': None,
        'warm_sample_count': 0,
        'speedup_factor': None,
        'hit_counts': [],
        'miss_counts': [],
        'hit_total': None,
        'miss_total': None,
        'hit_rate_percent': None,
        'avoided_model_inference_count': None,
        'note': (
            'Bu ölçüm önbellek ve soğuk/sıcak ayrımı eklenmeden önce kaydedildi. '
            'Eksik değerler uydurulmaz; yeni gerçek ölçüm başlatın.'
        ),
    }
    return legacy


def get_technical_status() -> dict:
    latest = None
    scenario_latest = None
    holdout_latest = None
    with connection() as conn:
        raw = meta_get(conn, RESULT_META_KEY)
        scenario_raw = meta_get(conn, SCENARIO_RESULT_META_KEY)
        holdout_raw = meta_get(conn, HOLDOUT_RESULT_META_KEY)
    if raw:
        try:
            latest = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            latest = None
    if scenario_raw:
        try:
            parsed = json.loads(scenario_raw)
            scenario_latest = parsed if isinstance(parsed, dict) else None
        except (json.JSONDecodeError, TypeError):
            scenario_latest = None
    if holdout_raw:
        try:
            parsed = json.loads(holdout_raw)
            holdout_latest = parsed if isinstance(parsed, dict) else None
        except (json.JSONDecodeError, TypeError):
            holdout_latest = None

    model_status = stance_status(load=False)
    hardware = _hardware_diagnostics(model_status)
    return {
        'version': APP_VERSION,
        'storage': 'sqlite',
        'dataset': _dataset_info(),
        'scenario_dataset': scenario_dataset_info(),
        'holdout_dataset': holdout_dataset_info(),
        'model_status': model_status,
        'hardware': hardware,
        'latest_result': _normalize_saved_result(latest, hardware),
        'latest_scenario_result': scenario_latest,
        'latest_holdout_result': holdout_latest,
    }


def _scenario_difficulty_metrics(predictions: list[dict]) -> list[dict]:
    return [
        {
            'key': level,
            'label': 'Temel ifadeler' if level == 'temel' else 'Zor ve örtük ifadeler',
            'sample_count': len(items),
            'correct_count': sum(item['correct'] for item in items),
            'accuracy': round(
                sum(item['correct'] for item in items) / max(1, len(items)),
                4,
            ),
        }
        for level in ('temel', 'zor')
        if (items := [item for item in predictions if item['difficulty'] == level])
    ]


def _run_scenario_suite(
    *,
    use_ai: bool,
    scenarios: tuple,
    dataset: dict,
    meta_key: str,
    suite_label: str,
) -> dict:
    """Bir elle etiketli iç seti gerçek ürün motoruyla izole biçimde ölçer."""
    initial_model = stance_status(load=False)
    requested_effective_ai = bool(use_ai and initial_model.get('loaded'))
    predictions: list[dict] = []
    scenario_results: list[dict] = []
    started = time.perf_counter()
    classification_modes: list[str] = []

    for scenario in scenarios:
        post = build_custom_post(
            scenario.title,
            [case.text for case in scenario.cases],
        )
        scenario_started = time.perf_counter()
        details = []
        engine_mode = 'heuristic-fallback'

        if requested_effective_ai:
            details, engine_info = classify_stances(scenario.title, post.comments)
            engine_mode = str(engine_info.get('mode', engine_mode))

        if not details:
            _, details = build_viewpoints_heuristic(post.comments, scenario.title)
            engine_mode = 'heuristic-fallback'

        classification_modes.append(engine_mode)
        detail_map = {int(item['comment_id']): item for item in details}
        topic_predictions: list[dict] = []

        for index, case in enumerate(scenario.cases, start=1):
            detail = detail_map.get(index)
            predicted = str(detail['label']) if detail is not None else 'Sınıflandırılamadı'
            confidence = float(detail.get('confidence', 0.0)) if detail else 0.0
            row = {
                'id': len(predictions) + 1,
                'scenario_key': scenario.key,
                'scenario_title': scenario.title,
                'scenario_topic': scenario.topic,
                'text': case.text,
                'expected_label': case.expected_label,
                'predicted_label': predicted,
                'correct': predicted == case.expected_label,
                'difficulty': case.difficulty,
                'challenge': case.challenge,
                'decision_engine': str(detail.get('engine', 'Sınıflandırılamadı')) if detail else 'Sınıflandırılamadı',
                'model_confidence': round(confidence, 4) if confidence > 0 else None,
            }
            predictions.append(row)
            topic_predictions.append(row)

        class_metrics, confusion, accuracy, macro_f1 = _class_metrics(topic_predictions)
        scenario_results.append({
            'key': scenario.key,
            'title': scenario.title,
            'topic': scenario.topic,
            'description': scenario.description,
            'sample_count': len(topic_predictions),
            'correct_count': sum(item['correct'] for item in topic_predictions),
            'accuracy': accuracy,
            'macro_f1': macro_f1,
            'class_metrics': class_metrics,
            'confusion_matrix': confusion,
            'difficulty_metrics': _scenario_difficulty_metrics(topic_predictions),
            'error_count': sum(not item['correct'] for item in topic_predictions),
            'errors': [item for item in topic_predictions if not item['correct']],
            'structural_decision_count': sum(item['model_confidence'] is None for item in topic_predictions),
            'transformer_inference_count': sum(item['model_confidence'] is not None for item in topic_predictions),
            'semantic_guardrail_count': sum(
                item['decision_engine'].startswith('anlamsal tutarlılık:')
                for item in topic_predictions
            ),
            'elapsed_ms': round((time.perf_counter() - scenario_started) * 1000, 2),
            'engine_mode': engine_mode,
        })

    metrics, confusion, accuracy, macro_f1 = _class_metrics(predictions)
    structural_count = sum(item['model_confidence'] is None for item in predictions)
    transformer_count = len(predictions) - structural_count
    effective_ai = requested_effective_ai and any(
        mode == 'hybrid-transformer' for mode in classification_modes
    )
    if not use_ai:
        engine_note = f'{suite_label} kullanıcı isteğiyle heuristik yedek motorla çalıştırıldı.'
    elif not initial_model.get('loaded'):
        engine_note = (
            'Transformer modeli bellekte hazır olmadığı için heuristik yedek motor '
            'kullanıldı; model otomatik yüklenmedi.'
        )
    elif not effective_ai:
        engine_note = 'Hibrit model sonuç üretemedi; tüm konular heuristik yedek motorla değerlendirildi.'
    elif transformer_count == 0:
        engine_note = 'Model hazırdı; bütün cümleler yüksek kesinlikli yapısal sinyallerle ayrıldı.'
    else:
        engine_note = (
            f'{transformer_count} örtük yorum gerçek Transformer ile, '
            f'{structural_count} yorum yapısal Türkçe sinyallerle sınıflandırıldı.'
        )

    result = {
        'run_id': str(uuid4()),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'version': APP_VERSION,
        'dataset': dataset,
        'sample_count': len(predictions),
        'scenario_count': len(scenario_results),
        'correct_count': sum(item['correct'] for item in predictions),
        'error_count': sum(not item['correct'] for item in predictions),
        'accuracy': accuracy,
        'macro_f1': macro_f1,
        'class_metrics': metrics,
        'confusion_matrix': confusion,
        'difficulty_metrics': _scenario_difficulty_metrics(predictions),
        'scenarios': scenario_results,
        'predictions': predictions,
        'errors': [item for item in predictions if not item['correct']],
        'label_distribution': dict(Counter(item['expected_label'] for item in predictions)),
        'structural_decision_count': structural_count,
        'transformer_inference_count': transformer_count,
        'semantic_guardrail_count': sum(
            item['decision_engine'].startswith('anlamsal tutarlılık:')
            for item in predictions
        ),
        'elapsed_ms': round((time.perf_counter() - started) * 1000, 2),
        'requested_ai': use_ai,
        'effective_ai': effective_ai,
        'engine_mode': 'hybrid-transformer' if effective_ai else 'heuristic-fallback',
        'model_status': stance_status(load=False),
        'engine_note': engine_note,
        'isolation_note': (
            'Senaryo doğrulaması kayıtlı kullanıcı tartışmalarını, analiz geçmişini, '
            'bildirimleri, mesajları, yer imlerini, listeleri ve referans ölçümünü değiştirmez.'
            if meta_key == SCENARIO_RESULT_META_KEY else
            'Ayrı kontrol, kayıtlı tartışmaları, analiz geçmişini, bildirimleri, '
            'mesajları, yer imlerini, listeleri, referans ölçümünü ve önceki '
            '80 örnekli kalibrasyon sonucunu değiştirmez.'
        ),
    }

    with transaction(immediate=True) as conn:
        meta_set(conn, meta_key, json.dumps(result, ensure_ascii=False))

    return result


def run_scenario_evaluation(*, use_ai: bool = True) -> dict:
    """Önceki dört konulu kalibrasyon setinin geriye uyumlu ölçümüdür."""
    return _run_scenario_suite(
        use_ai=use_ai,
        scenarios=SCENARIOS,
        dataset=scenario_dataset_info(),
        meta_key=SCENARIO_RESULT_META_KEY,
        suite_label='Çok senaryolu doğrulama',
    )


def run_holdout_evaluation(*, use_ai: bool = True) -> dict:
    """Eski metinleri ve konuları kullanmayan ayrı proje içi kontrolü ölçer."""
    dataset = holdout_dataset_info()
    if not dataset['is_disjoint_from_calibration']:
        raise ValueError('Ayrı kontrol seti önceki kalibrasyon metinleriyle çakışıyor.')
    return _run_scenario_suite(
        use_ai=use_ai,
        scenarios=HOLDOUT_SCENARIOS,
        dataset=dataset,
        meta_key=HOLDOUT_RESULT_META_KEY,
        suite_label='Ayrılmış yeni iç kontrol',
    )


def run_technical_evaluation(*, iterations: int = 5, use_ai: bool = True) -> dict:
    if not 1 <= iterations <= 10:
        raise ValueError('Tekrar sayısı 1 ile 10 arasında olmalıdır.')

    initial_model = stance_status(load=False)
    effective_ai = bool(use_ai and initial_model.get('loaded'))

    quality_post = build_custom_post(
        'Üniversitelerde yapay zekâ kullanımı nasıl düzenlenmeli?',
        [text for text, _ in LABELED_CASES],
    )
    quality_result = analyze_post(quality_post, demo_mode=False, use_ai=effective_ai)
    details = {item.comment_id: item for item in quality_result.stance_details}
    predictions = []

    for index, (text, expected) in enumerate(LABELED_CASES, start=1):
        actual = details.get(index)
        predicted = actual.label if actual is not None else 'Sınıflandırılamadı'
        model_confidence = (
            round(float(actual.confidence), 4)
            if actual is not None and actual.confidence > 0 else None
        )
        predictions.append({
            'id': index,
            'text': text,
            'expected_label': expected,
            'predicted_label': predicted,
            'correct': predicted == expected,
            'decision_engine': actual.engine if actual is not None else 'Sınıflandırılamadı',
            'model_confidence': model_confidence,
        })

    class_metrics, confusion, accuracy, macro_f1 = _class_metrics(predictions)
    timings = []
    demo_runs = []
    demo_result = None

    if effective_ai:
        # Önceki kullanıcı analizi demoyu ısıtmış olsa bile ilk örnek gerçek
        # soğuk ölçüm olmalıdır. Diğer tartışmaların kayıtları korunur.
        invalidate_claim_cache_for(DEMO_POST.text, DEMO_POST.comments)

    for _ in range(iterations):
        started = time.perf_counter()
        demo_result = analyze_post(DEMO_POST, demo_mode=True, use_ai=effective_ai)
        timings.append((time.perf_counter() - started) * 1000)
        demo_runs.append(dict(demo_result.engine))

    assert demo_result is not None
    invariant_results = _demo_invariants(demo_result)
    structural_count = sum(item['model_confidence'] is None for item in predictions)
    transformer_count = len(predictions) - structural_count
    model_status = stance_status(load=False)
    hardware = _hardware_diagnostics(model_status)
    model_usage = _model_usage(quality_result, predictions, demo_runs)
    fallback_reason = ''

    if not use_ai:
        fallback_reason = 'Ölçüm kullanıcı isteğiyle heuristik yedek motorla çalıştırıldı.'
    elif not initial_model.get('loaded'):
        fallback_reason = (
            'Transformer modeli bellekte hazır olmadığı için ölçüm heuristik yedek motorla '
            'yapıldı; model otomatik indirilmedi veya yüklenmedi.'
        )
    elif transformer_count == 0:
        fallback_reason = (
            'Model hazırdı ancak iç setteki tüm cümleler yüksek kesinlikli Türkçe '
            'yapısal sinyallerle ayrıldı; görüş katmanında Transformer çıkarımı '
            'yapılmadı. Demo İddia Radarı çıkarımları ayrı gösterilir.'
        )

    result = {
        'run_id': str(uuid4()),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'version': APP_VERSION,
        'dataset': _dataset_info(),
        'accuracy': accuracy,
        'macro_f1': macro_f1,
        'correct_count': sum(item['correct'] for item in predictions),
        'sample_count': len(predictions),
        'class_metrics': class_metrics,
        'confusion_matrix': confusion,
        'predictions': predictions,
        'latency': _latency(timings, int(demo_result.indicators.get('comment_count', 0))),
        'stage_profile': _stage_profile(timings, demo_runs),
        'model_usage': model_usage,
        'cache_profile': _cache_profile(timings, demo_runs),
        'hardware': hardware,
        'invariants': invariant_results,
        'passed_invariant_count': sum(item['passed'] for item in invariant_results),
        'invariant_count': len(invariant_results),
        'requested_ai': use_ai,
        'effective_ai': effective_ai,
        'engine_mode': str(quality_result.engine.get('mode', 'heuristic-fallback')),
        'structural_decision_count': structural_count,
        'transformer_inference_count': transformer_count,
        'model_status': model_status,
        'engine_note': fallback_reason,
        'isolation_note': (
            'İç doğrulama kayıtlı tartışmaları, analiz geçmişini, bildirimleri, '
            'mesajları, yer imlerini veya listeleri değiştirmez.'
        ),
        'label_distribution': dict(Counter(item['expected_label'] for item in predictions)),
    }

    with transaction(immediate=True) as conn:
        meta_set(conn, RESULT_META_KEY, json.dumps(result, ensure_ascii=False))

    return result
