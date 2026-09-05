"""Jüri sunumu öncesi hızlı, yan etkisiz sistem hazırlık denetimi."""
from __future__ import annotations

from datetime import datetime, timezone

from .analyzer import analyze_post
from .coach_engine import status as coach_status
from .database import connection
from .demo import DEMO_POST
from .stance_engine import status as stance_status
from .version import APP_VERSION


REQUIRED_TABLES = {
    'app_meta', 'notifications', 'conversations', 'messages', 'bookmarks',
    'topic_lists', 'topic_list_entries', 'custom_posts', 'analysis_history',
    'profiles', 'pilot_sessions', 'pilot_phase_results',
}


def _check(key: str, label: str, status: str, detail: str, *, required: bool = True) -> dict:
    return {
        'key': key,
        'label': label,
        'status': status,
        'detail': detail,
        'required': required,
    }


def get_system_readiness() -> dict:
    checks: list[dict] = []

    try:
        with connection() as conn:
            quick = str(conn.execute('PRAGMA quick_check').fetchone()[0])
            tables = {
                str(row['name'])
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
        checks.append(_check(
            'database', 'SQLite kalıcılığı',
            'ready' if quick == 'ok' else 'failed',
            'Veritabanı bütünlük kontrolü başarılı.' if quick == 'ok' else f'Bütünlük sonucu: {quick}',
        ))
        missing = sorted(REQUIRED_TABLES - tables)
        checks.append(_check(
            'schema', 'Ürün veri şeması',
            'ready' if not missing else 'failed',
            'Tüm kalıcı ürün ve pilot tabloları hazır.' if not missing else f'Eksik tablolar: {", ".join(missing)}',
        ))
    except Exception as exc:
        checks.append(_check('database', 'SQLite kalıcılığı', 'failed', f'{type(exc).__name__}: veritabanı açılamadı.'))
        checks.append(_check('schema', 'Ürün veri şeması', 'failed', 'Veritabanı açılamadığı için şema doğrulanamadı.'))

    try:
        analysis = analyze_post(DEMO_POST, demo_mode=True, use_ai=False)
        module_contract = (
            bool(analysis.short_summary)
            and bool(analysis.common_ground_details)
            and bool(analysis.viewpoints)
            and isinstance(analysis.claims, list)
            and isinstance(analysis.unanswered_questions, list)
            and bool(analysis.changes_since_last_visit)
            and bool(analysis.bridge.get('bridge_question'))
        )
        checks.append(_check(
            'demo', 'Sabit jüri demo verisi',
            'ready' if analysis.indicators.get('comment_count') == 20 else 'failed',
            f"{analysis.indicators.get('comment_count', 0)} benzersiz yorum okunup analiz edildi.",
        ))
        checks.append(_check(
            'analysis', 'Sekiz adımlı analiz sözleşmesi',
            'ready' if module_contract else 'failed',
            'Özet, ortak zemin, görüş, iddia, soru, koç bağlamı, değişim ve Köprü çıktıları hazır.'
            if module_contract else 'Analiz modüllerinden en az biri beklenen çıktıyı üretmedi.',
        ))
        bridge_words = len(str(analysis.bridge.get('bridge_question', '')).split())
        checks.append(_check(
            'bridge', 'Köprü sunum sınırı',
            'ready' if 0 < bridge_words <= 28 else 'failed',
            f'Köprü sorusu {bridge_words} kelime; 28 kelimelik sınır korunuyor.',
        ))
    except Exception as exc:
        detail = f'{type(exc).__name__}: demo analizi tamamlanamadı.'
        checks.extend([
            _check('demo', 'Sabit jüri demo verisi', 'failed', detail),
            _check('analysis', 'Sekiz adımlı analiz sözleşmesi', 'failed', detail),
            _check('bridge', 'Köprü sunum sınırı', 'failed', detail),
        ])

    stance = stance_status(load=False)
    checks.append(_check(
        'stance_model', 'mDeBERTa görüş modeli',
        'ready' if stance.get('loaded') else 'optional',
        str(stance.get('message') or 'Model durumu okunamadı.'),
        required=False,
    ))
    coach = coach_status(load=False)
    checks.append(_check(
        'coach_model', 'Qwen Yanıt Koçu',
        'ready' if coach.get('loaded') else 'optional',
        str(coach.get('message') or 'Model durumu okunamadı.'),
        required=False,
    ))

    required = [item for item in checks if item['required']]
    ready_count = sum(item['status'] == 'ready' for item in required)
    presentation_ready = ready_count == len(required)
    if any(item['status'] == 'failed' for item in required):
        status = 'failed'
    elif presentation_ready:
        status = 'ready'
    else:
        status = 'degraded'

    return {
        'version': APP_VERSION,
        'checked_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
        'presentation_ready': presentation_ready,
        'required_ready_count': ready_count,
        'required_check_count': len(required),
        'checks': checks,
        'note': (
            'Zorunlu kontroller sunum akışını doğrular. Transformer modelleri isteğe bağlıdır; '
            'yüklenmemeleri yapısal yedek motorla jüri demosunu engellemez.'
        ),
    }
