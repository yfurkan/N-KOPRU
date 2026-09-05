"""N-KÖPRÜ v1.1.1 - kanıt odaklı tartışma zekâsı katmanı.

Bu modül üç işi aynı veri akışında birleştirir:
1) İddia Radarı: yapısal sinyaller + mevcut mDeBERTa-XNLI zero-shot modeliyle
   doğrulanabilir iddia adaylarını ayırır ve doğrulama ihtiyacını açıklar.
2) Ortak Zemin: AI görüş kümelerinin birden fazlasında tekrar eden temaları bulur;
   tek bir görüşü "uzlaşı" diye sunmaz.
3) Köprü Oluştur: ortak tema + ana ayrışma + eksik kanıtı birlikte kullanarak
   kanıta dayalı, kontrollü bir Köprü sorusu üretir.

Üretken model zorunlu değildir. Transformer kurulu değilse deterministik ve test
edilebilir yapısal katman devreye girer.
"""
from __future__ import annotations

import math
import re
import time
from collections import Counter, defaultdict
from typing import Iterable

from .claim_cache import (
    CLAIM_INFERENCE_LOCK,
    claim_cache_discard,
    claim_cache_get,
    claim_cache_key,
    claim_cache_size,
    claim_cache_store,
)
from .models import ClaimItem, Comment, CommonGroundItem, StanceDetail
from .stance_engine import load_model, status as stance_status

SOURCE_MARKERS = (
    'http://', 'https://', 'doi:', 'kaynak:', 'araştırmaya göre', 'raporuna göre',
    'çalışmaya göre', 'verilere göre', 'istatistiklerine göre',
)

NUMERIC_PATTERNS = (
    r'%\s?\d+(?:[.,]\d+)?',
    r'\b\d+(?:[.,]\d+)?\s?(?:kişi|öğrenci|katılımcı|yıl|ay|saat|gün|oran|puan)\b',
    r'\b(?:yüzde|oran)\s+\d+(?:[.,]\d+)?\b',
)
CAUSAL_SIGNALS = (
    'artırıyor', 'arttırıyor', 'azaltıyor', 'düşürüyor', 'yükseltiyor', 'etkiliyor',
    'neden oluyor', 'sebep oluyor', 'zarar veriyor', 'zarar görüyor', 'güçlendiriyor',
    'zayıflatıyor', 'başarıyı artır', 'başarıyı azalt', 'öğrenmeyi artır',
    'öğrenmeyi azalt', 'düşünmeyi bırak', 'bağımlı hale', 'bağımlı hâle',
)
PREVALENCE_SIGNALS = (
    'bazı öğrenciler', 'çoğu öğrenci', 'öğrencilerin çoğu', 'öğrenciler ',
    'sınıfımızın', 'katılımcıların', 'kullanıcıların', 'yaygın', 'sıklıkla', 'genellikle',
)
COMPARISON_SIGNALS = (
    'daha fazla', 'daha az', 'daha yüksek', 'daha düşük', 'karşılaştır', 'fark ',
    'oranla', 'kıyasla',
)
EVIDENCE_REQUEST_SIGNALS = (
    'kaynak', 'araştırma', 'çalışma', 'veri', 'kanıt', 'ölç', 'istatistik', 'başarı düzeyi',
)
# Kaynak farkındalığı metriği, yalnızca iddiaların URL/atıf içerip içermediğine
# bakmaz. Bir yorumun kaynak, araştırma, veri, kanıt, istatistik veya ölçüm ihtiyacını
# açıkça gündeme getirmesini de kanıt farkındalığı olarak sayar.
SOURCE_AWARENESS_SIGNALS = (
    'kaynak', 'araştırma', 'veri', 'kanıt', 'istatistik', 'ölç', 'referans', 'doi:',
)
NORMATIVE_SIGNALS = (
    'bence', 'olmalı', 'olmamalı', 'yasaklanmalı', 'yasaklanmamalı', 'zorunlu',
    'mantıklı', 'yanlış olur', 'doğru olur', 'gerekli', 'öneriyorum', 'öğretmeli',
)
PERSONAL_SIGNALS = ('ben ', 'bana ', 'kendi ', 'ders çalışırken', 'kullanıyorum', 'yaptırmıyorum')

CLAIM_AI_LABELS = [
    'ölçüm, araştırma veya dış verilerle doğrulanabilecek somut bir olgusal iddia içeriyor',
    'kişisel görüş, değer yargısı veya politika önerisi ağırlıklı',
    'kişisel deneyim veya öznel anlatım ağırlıklı',
]
CLAIM_HYPOTHESIS_TEMPLATE = 'Bu yorum {}.'
CLAIM_FACTUAL_THRESHOLD = 0.52

THEMES = {
    'Şeffaflık ve kaynak kullanımı': (
        'kaynak', 'şeffaf', 'açıkça belirtil', 'güvenilirlik', 'kanıt', 'araştırma', 'veri',
    ),
    'Kurallı ve bağlama duyarlı kullanım': (
        'kontrollü', 'kural', 'yönerge', 'denetim', 'sınav', 'kullanım amacı', 'bağlama göre',
        'etik kullanım', 'nasıl kullandığımız', 'hangi kullanım',
    ),
    'Öğrenme etkisinin ölçülmesi': (
        'öğrenme', 'öğrenmeyi', 'öğrenmenin', 'başarı', 'düşünme', 'ölç', 'faydalı', 'yararlı', 'zarar', 'etki',
    ),
    'Yapay zekâ okuryazarlığı ve rehberlik': (
        'okuryazarlık', 'öğret', 'nasıl kullanılacağını', 'rehber', 'eğitim',
    ),
}


def _has_any(text: str, signals: Iterable[str]) -> bool:
    lower = text.casefold()
    return any(signal in lower for signal in signals)


def _has_numeric(text: str) -> bool:
    lower = text.casefold()
    return any(re.search(pattern, lower) for pattern in NUMERIC_PATTERNS)


def source_awareness_stats(comments: list[Comment]) -> dict:
    """Kaynak/kanıt farkındalığını benzersiz yorumlar üzerinden ölçer.

    Payda tüm benzersiz yorumlardır. Pay ise kaynak sunan *veya* kaynak/araştırma/
    veri/kanıt/ölçüm ihtiyacını açıkça dile getiren yorumlardır. Böylece "kaynak var mı?"
    gibi sağlıklı kanıt talepleri, ortada URL olmadığı için yanlışlıkla %0'a düşmez.
    """
    aware_ids: set[int] = set()
    provided_ids: set[int] = set()
    request_ids: set[int] = set()

    for comment in comments:
        lower = comment.text.casefold()
        if any(marker in lower for marker in SOURCE_MARKERS):
            provided_ids.add(comment.id)
            aware_ids.add(comment.id)
        if any(signal in lower for signal in SOURCE_AWARENESS_SIGNALS):
            aware_ids.add(comment.id)
        if '?' in comment.text and any(signal in lower for signal in EVIDENCE_REQUEST_SIGNALS):
            request_ids.add(comment.id)
            aware_ids.add(comment.id)

    total = len(comments)
    score = round(len(aware_ids) * 100 / total) if total else 0
    return {
        'score': score,
        'aware_comment_count': len(aware_ids),
        'provided_source_count': len(provided_ids),
        'evidence_request_count': len(request_ids),
        'comment_count': total,
    }


def _source_status(text: str) -> str:
    lower = text.casefold()
    return 'Kaynak işareti var' if any(marker in lower for marker in SOURCE_MARKERS) else 'Kaynak gerekli'


def _claim_profile(text: str) -> dict:
    """Deterministik ön eleme ve öncelik puanı."""
    lower = text.casefold().strip()
    if not lower or '?' in text:
        return {'candidate': False, 'score': 0, 'claim_type': 'Soru', 'reason': 'Soru biçimi'}

    numeric = _has_numeric(text)
    causal = _has_any(text, CAUSAL_SIGNALS)
    prevalence = _has_any(text, PREVALENCE_SIGNALS)
    comparison = _has_any(text, COMPARISON_SIGNALS)
    normative = _has_any(text, NORMATIVE_SIGNALS)
    personal = _has_any(text, PERSONAL_SIGNALS)

    score = 0
    reasons: list[str] = []
    if numeric:
        score += 5
        reasons.append('nicel/sayısal ifade')
    if causal:
        score += 4
        reasons.append('etki/nedensellik ifadesi')
    if comparison:
        score += 3
        reasons.append('karşılaştırılabilir ifade')
    if prevalence:
        score += 2
        reasons.append('yaygınlık/davranış genellemesi')
    if normative:
        score -= 2
        reasons.append('normatif öneri sinyali')
    if personal and not (numeric or causal or comparison):
        score -= 3
        reasons.append('kişisel deneyim ağırlığı')

    if numeric:
        claim_type = 'Nicel / İstatistiksel'
        need = 'Örneklem, dönem, yüzde/oran hesabı ve mümkünse bağımsız karşılaştırma verisi.'
    elif comparison:
        claim_type = 'Karşılaştırmalı'
        need = 'Karşılaştırılan gruplar, ölçütler ve aynı koşullarda elde edilmiş veri.'
    elif causal:
        claim_type = 'Etki / Nedensellik'
        need = 'Kontrollü veya karşılaştırmalı çalışma; mümkünse sistematik derleme ya da güçlü gözlemsel veri.'
    elif prevalence:
        claim_type = 'Yaygınlık / Davranış'
        need = 'Temsili örneklem, kullanım sıklığı ve ölçüm yöntemini açıklayan veri.'
    else:
        claim_type = 'Genel olgusal iddia'
        need = 'Güvenilir araştırma, rapor veya birincil veri ile doğrulama.'

    return {
        'candidate': score >= 3,
        'ambiguous': 1 <= score < 3,
        'score': score,
        'claim_type': claim_type,
        'verification_need': need,
        'reason': ', '.join(reasons) if reasons else 'belirgin doğrulanabilirlik sinyali yok',
    }


def _claim_model_cache_key(title: str, text: str, classifier, model_state: dict) -> str:
    return claim_cache_key(
        title,
        text,
        model_name=str(model_state.get('model', '')),
        device=str(model_state.get('device', 'cpu')),
        model_identity=id(classifier),
        candidate_labels=CLAIM_AI_LABELS,
        hypothesis_template=CLAIM_HYPOTHESIS_TEMPLATE,
        threshold=CLAIM_FACTUAL_THRESHOLD,
    )


def invalidate_claim_cache_for(title: str, comments: list[Comment]) -> int:
    """Gerçek soğuk ölçüm için yalnızca ilgili tartışmanın model girdilerini siler."""
    model_state = stance_status(load=False)
    if not model_state.get('loaded'):
        return 0
    classifier = load_model()
    if classifier is None:
        return 0
    keys = [
        _claim_model_cache_key(title, comment.text, classifier, model_state)
        for comment in comments
        if _claim_profile(comment.text).get('ambiguous')
    ]
    return claim_cache_discard(keys)


def analyze_claims(title: str, comments: list[Comment], *, use_ai: bool = True) -> tuple[list[ClaimItem], dict]:
    started = time.perf_counter()
    profiles = {c.id: _claim_profile(c.text) for c in comments}
    ambiguous = [c for c in comments if profiles[c.id].get('ambiguous')]
    ai_decisions: dict[int, tuple[bool, float]] = {}
    transformer_count = 0
    transformer_comment_ids: list[int] = []
    cache_comment_ids: list[int] = []
    cache_miss_count = 0
    # Görüş katmanı model yüklemeyi zaten denemiştir. Burada başarısız bir model
    # yüklemesini ikinci kez tetiklemek yerine yalnızca hazır modeli yeniden kullanırız.
    model_state = stance_status(load=False) if use_ai and ambiguous else {}
    classifier = load_model() if use_ai and ambiguous and model_state.get('loaded') else None

    if classifier is not None and ambiguous:
        try:
            # Ortak model hattı aynı anda yalnızca bir çıkarım çalıştırır. Kilit
            # içinde tekrar kontrol edildiğinden eşzamanlı istek de aynı metni
            # ikinci kez modele göndermez.
            with CLAIM_INFERENCE_LOCK:
                missing: dict[str, list[Comment]] = {}
                for comment in ambiguous:
                    key = _claim_model_cache_key(title, comment.text, classifier, model_state)
                    cached = claim_cache_get(key)
                    if cached is not None:
                        ai_decisions[comment.id] = cached
                        cache_comment_ids.append(comment.id)
                    elif key in missing:
                        missing[key].append(comment)
                    else:
                        missing[key] = [comment]

                cache_miss_count = len(missing)
                if missing:
                    owners = [items[0] for items in missing.values()]
                    sequences = [f'Konu: {title}\nYorum: {comment.text}' for comment in owners]
                    outputs = classifier(
                        sequences,
                        candidate_labels=CLAIM_AI_LABELS,
                        hypothesis_template=CLAIM_HYPOTHESIS_TEMPLATE,
                        multi_label=False,
                        batch_size=4,
                    )
                    if isinstance(outputs, dict):
                        outputs = [outputs]
                    if not isinstance(outputs, list) or len(outputs) != len(owners):
                        raise ValueError('Model çıktı sayısı yorum sayısıyla eşleşmedi.')

                    parsed: list[tuple[str, list[Comment], tuple[bool, float]]] = []
                    for (key, grouped_comments), result in zip(missing.items(), outputs):
                        top_label = str(result['labels'][0])
                        top_score = float(result['scores'][0])
                        if not math.isfinite(top_score) or not 0.0 <= top_score <= 1.0:
                            raise ValueError('Model güven değeri geçersiz.')
                        decision = (
                            top_label == CLAIM_AI_LABELS[0] and top_score >= CLAIM_FACTUAL_THRESHOLD,
                            top_score,
                        )
                        parsed.append((key, grouped_comments, decision))

                    # Önce bütün çıktılar doğrulanır; hatalı toplu sonuçtan hiçbir
                    # kısmi kayıt önbelleğe yazılmaz.
                    for key, grouped_comments, decision in parsed:
                        claim_cache_store(key, decision)
                        owner, *repeated = grouped_comments
                        ai_decisions[owner.id] = decision
                        transformer_comment_ids.append(owner.id)
                        for comment in repeated:
                            ai_decisions[comment.id] = decision
                            cache_comment_ids.append(comment.id)
                    transformer_count = len(parsed)
        except Exception:
            ai_decisions = {}
            transformer_count = 0
            transformer_comment_ids = []
            cache_comment_ids = []

    claims: list[ClaimItem] = []
    for comment in comments:
        profile = profiles[comment.id]
        ai_candidate, ai_conf = ai_decisions.get(comment.id, (False, 0.0))
        if not profile.get('candidate') and not ai_candidate:
            continue
        score = int(profile.get('score', 0))
        structural_conf = min(0.96, max(0.58, 0.56 + max(0, score) * 0.07))
        confidence = round(max(structural_conf, ai_conf if ai_candidate else 0.0), 3)
        if score >= 6 or _has_numeric(comment.text):
            priority = 'Yüksek'
        elif score >= 3 or ai_candidate:
            priority = 'Orta'
        else:
            priority = 'Düşük'
        engine = 'mDeBERTa-XNLI + yapısal sinyal' if ai_candidate else 'Yapısal doğrulanabilirlik analizi'
        claims.append(ClaimItem(
            comment_id=comment.id,
            text=comment.text,
            source_status=_source_status(comment.text),
            claim_type=str(profile.get('claim_type', 'Genel olgusal iddia')),
            verification_need=str(profile.get('verification_need', 'Güvenilir kaynakla doğrulama.')),
            priority=priority,
            confidence=confidence,
            engine=engine,
            detection_reason=str(profile.get('reason', '')),
        ))

    claims.sort(key=lambda item: ({'Yüksek': 3, 'Orta': 2, 'Düşük': 1}.get(item.priority, 0), item.confidence), reverse=True)
    info = {
        'mode': 'hybrid-semantic-claim' if ai_decisions else 'structural-semantic-claim',
        'transformer_count': transformer_count,
        'transformer_comment_ids': sorted(transformer_comment_ids),
        'model_comment_ids': sorted(ai_decisions),
        'cache_hit_count': len(cache_comment_ids),
        'cache_miss_count': cache_miss_count,
        'cache_comment_ids': sorted(cache_comment_ids),
        'cache_size': claim_cache_size(),
        'candidate_count': len(claims),
        'elapsed_ms': round((time.perf_counter() - started) * 1000),
    }
    return claims, info


def _theme_matches(text: str) -> list[str]:
    lower = text.casefold()
    return [theme for theme, words in THEMES.items() if any(word in lower for word in words)]


def build_common_ground(
    comments: list[Comment],
    stance_details: list[StanceDetail],
    claims: list[ClaimItem],
    title: str = '',
) -> tuple[list[CommonGroundItem], dict]:
    started = time.perf_counter()
    from .topic_context import resolve_topic_context

    topic = resolve_topic_context(title) if title else None
    stance_by_id = {item.comment_id: item.label for item in stance_details}
    theme_comments: dict[str, list[int]] = defaultdict(list)
    theme_stances: dict[str, set[str]] = defaultdict(set)

    for comment in comments:
        label = stance_by_id.get(comment.id, 'Diğer / Nötr')
        for theme in _theme_matches(comment.text):
            theme_comments[theme].append(comment.id)
            theme_stances[theme].add(label)

    candidates: list[CommonGroundItem] = []
    for theme in THEMES:
        ids = theme_comments.get(theme, [])
        stances = theme_stances.get(theme, set())
        if len(ids) < 2 or len(stances) < 2:
            continue
        confidence = min(0.96, 0.50 + 0.08 * len(stances) + 0.025 * min(8, len(ids)))
        if theme == 'Şeffaflık ve kaynak kullanımı':
            text = 'Farklı görüş kümeleri, iddiaların şeffaf biçimde açıklanması ve gerektiğinde kaynak/kanıtla desteklenmesi ihtiyacında kesişiyor.'
        elif theme == 'Kurallı ve bağlama duyarlı kullanım':
            text = (
                f'Farklı görüş kümelerinde, {topic.subject if topic and topic.is_specific else "yapay zekâ kullanımı"} '
                'için açık koşullar ve sınırların konuşulması ortak bir tema olarak görünüyor.'
            )
        elif theme == 'Öğrenme etkisinin ölçülmesi':
            text = (
                f'Karşıt görüşler, {topic.subject if topic and topic.is_specific else "kararın"} '
                'gerçek etkilerinin açık ölçütlerle değerlendirilmesi gerektiği noktasında kesişen sinyaller taşıyor.'
            )
        else:
            text = (
                f'Farklı görüş kümeleri, {topic.subject if topic and topic.is_specific else "uygulamanın"} '
                'nasıl işleyeceğinin anlaşılır rehberlik ve ortak kurallarla desteklenmesi temasında buluşuyor.'
            )
        candidates.append(CommonGroundItem(
            theme=theme,
            text=text,
            support_count=len(ids),
            stance_count=len(stances),
            evidence_comment_ids=ids[:8],
            confidence=round(confidence, 3),
            engine='Görüş kümeleri arası çapraz-tema analizi',
        ))

    # Kaynak/kanıt ihtiyacı, farklı tutumlardan açıkça gelmese bile iddia + soru kombinasyonu
    # varsa düşük güvenli bir "tartışma kalitesi ortaklığı" olarak eklenebilir.
    if not any(item.theme == 'Şeffaflık ve kaynak kullanımı' for item in candidates):
        unsourced = [item for item in claims if item.source_status != 'Kaynak işareti var']
        source_request_ids = [c.id for c in comments if '?' in c.text and _has_any(c.text, EVIDENCE_REQUEST_SIGNALS)]
        if unsourced and source_request_ids:
            ids = [unsourced[0].comment_id, *source_request_ids[:4]]
            candidates.append(CommonGroundItem(
                theme='Şeffaflık ve kaynak kullanımı',
                text='Tartışmada doğrulanabilir iddialar ile bunlara yönelen kaynak/veri talepleri birlikte görünüyor; kanıtın görünür olması ortak bir kalite ihtiyacı oluşturuyor.',
                support_count=len(ids),
                stance_count=max(1, len({stance_by_id.get(i, 'Diğer / Nötr') for i in ids})),
                evidence_comment_ids=ids,
                confidence=0.68,
                engine='İddia–kaynak talebi çapraz sinyali',
            ))

    # Konusu tanınan tartışmalarda yalnızca genel bir "ortak ölçüt" cümlesi
    # göstermek yerine, kararın hangi somut boyutlarla değerlendirileceğini açıklar.
    # Bu kayıt bir içerik uzlaşısı iddia etmez; farklı kümelerden seçilen yorumlarla
    # desteklenen ortak değerlendirme çerçevesidir.
    if topic is not None and topic.is_specific and topic.common_ground_text:
        evidence_ids: list[int] = []
        seen_stances: set[str] = set()
        for comment in comments:
            stance = stance_by_id.get(comment.id, 'Diğer / Nötr')
            if stance in seen_stances:
                continue
            seen_stances.add(stance)
            evidence_ids.append(comment.id)
        if len(seen_stances) >= 2:
            candidates.append(CommonGroundItem(
                theme=f'{topic.subject.capitalize()} karar ölçütleri',
                text=topic.common_ground_text,
                support_count=len(evidence_ids),
                stance_count=len(seen_stances),
                evidence_comment_ids=evidence_ids[:8],
                confidence=min(0.86, round(0.54 + 0.06 * len(seen_stances), 3)),
                engine='Konu bağlamı + görüş kümeleri arası değerlendirme',
            ))

    if not candidates:
        all_ids = [c.id for c in comments[:6]]
        stance_count = len({stance_by_id.get(cid, 'Diğer / Nötr') for cid in all_ids})
        candidates.append(CommonGroundItem(
            theme='Ortak değerlendirme ölçütleri',
            text='Belirgin bir içerik uzlaşısı henüz oluşmasa da farklı görüşleri aynı açık ölçütler ve doğrulanabilir veriler üzerinden karşılaştırma ihtiyacı ortak değerlendirme zemini oluşturuyor.',
            support_count=len(all_ids),
            stance_count=max(1, stance_count),
            evidence_comment_ids=all_ids,
            confidence=0.55,
            engine='Düşük güvenli ortak değerlendirme zemini',
        ))

    candidates.sort(key=lambda item: (item.stance_count, item.support_count, item.confidence), reverse=True)
    info = {
        'mode': 'cross-stance-semantic-ground',
        'candidate_count': len(candidates),
        'elapsed_ms': round((time.perf_counter() - started) * 1000),
    }
    return candidates[:3], info


def _representative_comment(label: str, comments: list[Comment], stance_details: list[StanceDetail]) -> int | None:
    ids = [item.comment_id for item in stance_details if item.label == label]
    if not ids:
        return None
    likes = {c.id: c.likes for c in comments}
    return max(ids, key=lambda cid: likes.get(cid, 0))


def _restriction_policy_context(title: str, viewpoints) -> bool:
    lowered = title.casefold()
    if any(signal in lowered for signal in ('yasak', 'kısıt', 'sınır', 'düzenlen', 'kontrol')):
        return True
    return any(
        getattr(item, 'display_name', '').startswith(('Tam yasak', 'Yasağa karşı', 'Kontrollü ve kurallı'))
        for item in viewpoints
    )


def _select_divergence_labels(title: str, viewpoints) -> tuple[list[str], bool, str]:
    substantive_names = {'Destekleyen', 'Karşı / Sınırlayıcı', 'Koşullu / Dengeli'}
    ordered = [item.name for item in viewpoints if item.name in substantive_names]
    available = set(ordered)
    restricted = _restriction_policy_context(title, viewpoints)

    if restricted and 'Karşı / Sınırlayıcı' in available:
        labels = [name for name in ('Karşı / Sınırlayıcı', 'Koşullu / Dengeli', 'Destekleyen') if name in available]
        return labels, restricted, 'policy-spectrum' if len(labels) >= 2 else 'single-position'

    if {'Destekleyen', 'Karşı / Sınırlayıcı'} <= available:
        labels = [name for name in ('Destekleyen', 'Koşullu / Dengeli', 'Karşı / Sınırlayıcı') if name in available]
        return labels, restricted, 'substantive-opposition'

    return ordered[:2], restricted, 'substantive-opposition' if len(ordered) >= 2 else 'single-position'


def _divergence_text(
    labels: list[str],
    restriction_context: bool = True,
    topic=None,
) -> str:
    if topic is not None:
        contextual = topic.contrast(labels)
        if contextual:
            return f'{contextual.capitalize()} yaklaşımları arasında ayrışma var.'
    positions = set(labels)
    if {'Destekleyen', 'Karşı / Sınırlayıcı', 'Koşullu / Dengeli'} <= positions:
        if restriction_context:
            return 'Tam yasaklama, açık kurallarla kontrollü kullanım ve yararlı kullanım alanlarını koruma yaklaşımları arasında ayrışma var.'
        return 'Öneriyi destekleme, koşullu uygulama ve karşı çıkma yaklaşımları arasında ayrışma var.'

    pair = set(labels[:2])
    if {'Destekleyen', 'Karşı / Sınırlayıcı'} <= pair:
        if restriction_context:
            return 'Tam yasaklama/kısıtlama ile yararlı ve meşru kullanım alanlarını koruma yaklaşımı arasında ayrışma var.'
        return 'Öneriyi destekleyen ve öneriye karşı çıkan yaklaşımlar arasında ayrışma var.'
    if {'Koşullu / Dengeli', 'Karşı / Sınırlayıcı'} <= pair:
        if restriction_context:
            return 'Sert kısıtlama ile açık kurallar altında kontrollü kullanıma izin verme yaklaşımı arasında ayrışma var.'
        return 'Öneriye karşı çıkma ile belirli koşullarda uygulama yaklaşımları arasında ayrışma var.'
    if {'Destekleyen', 'Koşullu / Dengeli'} <= pair:
        if restriction_context:
            return 'Geniş kullanım serbestisi ile kurallı/denetimli kullanımın sınırları konusunda ayrışma var.'
        return 'Öneriyi doğrudan destekleme ile koşullu uygulama yaklaşımları arasında ayrışma var.'
    if labels:
        return 'Tek belirgin karar yaklaşımı görülüyor; farklı görüşlerin oluşması için ortak karar ölçütleri netleştirilebilir.'
    return 'Belirgin görüş ayrılığı sınırlı; karar ölçütlerinin netleştirilmesi gerekiyor.'


def _bridge_contrast(
    labels: list[str],
    restriction_context: bool = True,
    topic=None,
) -> str:
    if topic is not None:
        contextual = topic.contrast(labels)
        if contextual:
            return contextual
    positions = set(labels)
    if {'Destekleyen', 'Karşı / Sınırlayıcı', 'Koşullu / Dengeli'} <= positions:
        if restriction_context:
            return 'tam yasak, kontrollü kullanım ve kullanım alanlarını koruma'
        return 'öneriyi destekleme, koşullu uygulama ve karşı çıkma'

    pair = set(labels[:2])
    if {'Destekleyen', 'Karşı / Sınırlayıcı'} <= pair:
        return 'geniş kullanım ile sert kısıtlama' if restriction_context else 'öneriyi destekleme ile karşı çıkma'
    if {'Koşullu / Dengeli', 'Karşı / Sınırlayıcı'} <= pair:
        return 'sert kısıtlama ile kontrollü kullanım' if restriction_context else 'karşı çıkma ile koşullu uygulama'
    if {'Destekleyen', 'Koşullu / Dengeli'} <= pair:
        return 'geniş kullanım ile kurallı kullanım' if restriction_context else 'doğrudan destek ile koşullu uygulama'
    return 'farklı yaklaşımlar'


def _keep_bridge_compact(question: str, contrast: str, max_words: int = 28) -> str:
    """Köprü sorusunu sosyal akışta okunabilir bir üst sınırda tutar.

    Normal şablonlar zaten kısa üretilir. Dinamik tema adı beklenmedik biçimde uzarsa
    kırpılmış/yarım bir cümle vermek yerine kısa, tam bir yedek soru kullanılır.
    """
    if len(question.split()) <= max_words:
        return question
    return (
        f'{contrast.capitalize()} seçeneklerini hangi ortak ölçütlerle karşılaştırmalı '
        've bu ölçütleri hangi güvenilir verilerle sınamalıyız?'
    )


def build_bridge(
    title: str,
    comments: list[Comment],
    stance_details: list[StanceDetail],
    viewpoints,
    common_ground: list[CommonGroundItem],
    claims: list[ClaimItem],
) -> tuple[dict, dict]:
    started = time.perf_counter()
    from .topic_context import resolve_topic_context

    topic = resolve_topic_context(title)
    labels, restricted, contrast_strategy = _select_divergence_labels(title, viewpoints)
    display_names = {item.name: getattr(item, 'display_name', '') or item.name for item in viewpoints}
    divergence = _divergence_text(labels, restricted, topic)
    acceptance = common_ground[0].text if common_ground else 'Farklı görüşlerin aynı ölçütler ve doğrulanabilir veriler üzerinden karşılaştırılması tartışmayı ilerletebilir.'

    source_questions = [c for c in comments if '?' in c.text and _has_any(c.text, EVIDENCE_REQUEST_SIGNALS)]
    unsourced = [c for c in claims if c.source_status != 'Kaynak işareti var']
    evidence_ids: list[int] = []
    if source_questions:
        q = source_questions[0]
        missing = f'Cevapsız kaynak/veri talebi #{q.id}: {q.text}'
        evidence_focus = topic.evidence_focus
        evidence_ids.append(q.id)
    elif unsourced:
        claim = unsourced[0]
        missing = f'İddia #{claim.comment_id} henüz kaynakla desteklenmiyor. Doğrulama ihtiyacı: {claim.verification_need}'
        evidence_focus = claim.verification_need.rstrip('.').casefold()
        evidence_ids.append(claim.comment_id)
    else:
        evidence_focus = topic.evidence_focus
        missing = f'Belirgin bir kaynak boşluğu görünmüyor; {evidence_focus} için ortak karar ölçütlerinin netleştirilmesi gerekiyor.'

    for label in labels:
        cid = _representative_comment(label, comments, stance_details)
        if cid is not None and cid not in evidence_ids:
            evidence_ids.append(cid)
    if common_ground:
        for cid in common_ground[0].evidence_comment_ids[:3]:
            if cid not in evidence_ids:
                evidence_ids.append(cid)

    # v1.1.1: Köprü sorusu, ayrıntı kartlarını tekrarlamak yerine tek bir kısa
    # karar sorusuna sıkıştırılır. Ortak zemin + ana ayrışma + kanıt ihtiyacı korunur.
    theme = common_ground[0].theme.casefold() if common_ground else 'ortak ölçütler'
    if topic.is_specific:
        theme = topic.criteria_phrase
    contrast = _bridge_contrast(labels, restricted, topic)
    if topic.is_specific:
        bridge_question = (
            f'{contrast.capitalize()} seçeneklerini {theme} bakımından hangi ortak ölçütler '
            've güvenilir verilerle karşılaştırmalıyız?'
        )
    elif source_questions:
        bridge_question = (
            f'{contrast.capitalize()} seçeneklerini {theme} açısından hangi ortak ölçütlerle karşılaştırmalı '
            f've bu ölçütleri hangi güvenilir verilerle sınamalıyız?'
        )
    elif unsourced:
        bridge_question = (
            f'{contrast.capitalize()} seçeneklerini {theme} açısından hangi ortak ölçütlerle karşılaştırmalı '
            f've hangi kanıt görüşümüzü değiştirmeye yeterli sayılmalı?'
        )
    else:
        bridge_question = (
            f'{contrast.capitalize()} seçeneklerini {theme} açısından hangi ortak ölçütlerle karşılaştırmalı '
            f've bu ölçütleri hangi verilerle sınamalıyız?'
        )
    bridge_question = _keep_bridge_compact(bridge_question, contrast)

    confidence = 0.58
    if len(labels) >= 2:
        confidence += 0.12
    if common_ground:
        confidence += 0.12
    if source_questions or unsourced:
        confidence += 0.10
    confidence = min(0.95, confidence)

    bridge = {
        'common_acceptance': acceptance,
        'main_divergence': divergence,
        'missing_information': missing,
        'bridge_question': bridge_question,
        'evidence_comment_ids': evidence_ids[:8],
        'contrast_viewpoint_names': labels,
        'contrast_viewpoint_labels': [display_names[label] for label in labels if label in display_names],
        'confidence': round(confidence, 3),
        'engine': 'Kanıta dayalı Köprü sentezi',
    }
    info = {
        'mode': 'evidence-grounded-bridge',
        'elapsed_ms': round((time.perf_counter() - started) * 1000),
        'evidence_count': len(bridge['evidence_comment_ids']),
        'contrast_strategy': contrast_strategy,
        'contrast_viewpoint_count': len(labels),
        'question_word_count': len(bridge_question.split()),
        'question_max_words': 28,
        'topic_key': topic.key,
        'topic_specific': topic.is_specific,
    }
    return bridge, info
