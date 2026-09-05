"""N-KÖPRÜ kullanıcı etki pilotu.

Bu modül sonuç uydurmaz: anonim, karşı dengelenmiş iki görevli bir A/B
protokolünü çalıştırır ve yalnızca tamamlanmış gerçek oturumları özetler.
Deneme oturumları aynı akışı sınamak için saklanır ancak sonuçlara katılmaz.
"""
from __future__ import annotations

import csv
import io
import secrets
import statistics
from datetime import datetime, timezone
from typing import Any

from .analyzer import analyze_post, build_custom_post
from .database import connection, transaction


PROTOCOL_VERSION = '1.0-2026-09-05'
MINIMUM_SAMPLE_SIZE = 8

SCENARIOS: dict[str, dict[str, Any]] = {
    'night-transport': {
        'title': 'Kampüste gece ulaşımı 01.00’e kadar sürmeli mi?',
        'comments': [
            'Geç saatte çalışan öğrenciler için gece servisinin sürmesini destekliyorum.',
            'Talep çok düşükken bütün hatları açık tutmaya karşıyım; bu gereksiz maliyet oluşturur.',
            'Yalnızca yurtlar ve ana duraklar arasında kontrollü bir gece hattı kalabilir.',
            'Gece vardiyasından çıkan personel için bu hizmet gerekli.',
            'Saat 23.00’ten sonra servisin sürmesi güvenlik açısından riskli.',
            'Kullanım sayıları ve güvenlik olaylarına ilişkin veri paylaşılmalı.',
            'Yoğun günlerde süre uzatılıp diğer günlerde talebe göre dengeli bir plan yapılabilir.',
            'Bütçe sınırlı olsa da gece ulaşımının sürdürülmesi doğru olur.',
        ],
        'question': 'Tartışmadaki ana karar ayrışmasını en doğru hangi seçenek özetliyor?',
        'choices': [
            'Servis araçlarının renginin değiştirilmesi',
            'Hizmetin sürmesi, kaldırılması veya talep ve güvenliğe göre sınırlı yürütülmesi',
            'Ders programlarının sabah saatlerine alınması',
            'Kampüste yeni yurt yapılması',
        ],
        'correct_answer': 1,
    },
    'park-hours': {
        'title': 'Mahalle parkları 22.00’den sonra açık kalmalı mı?',
        'comments': [
            'Vardiyalı aileler için parkların geç saate kadar açık kalmasını destekliyorum.',
            'Gece gürültüsü nedeniyle 22.00’den sonra park kullanımına karşıyım.',
            'Aydınlatma ve güvenlik denetimi sağlanırsa hafta sonu saatleri uzatılabilir.',
            'Gençlerin ücretsiz açık alana erişiminin korunması gerekli.',
            'Gece park kullanımını çevrede yaşayanlar için riskli buluyorum.',
            'Şikâyet sayısı ve gece kullanım yoğunluğu açıklanıyor mu?',
            'Sessiz alan ve etkinlik alanı ayrılarak dengeli kullanım sağlanabilir.',
            'Tek kapanış saati yerine mevsime göre farklı kurallar uygulanabilir.',
        ],
        'question': 'Tartışmadaki ana karar ayrışmasını en doğru hangi seçenek özetliyor?',
        'choices': [
            'Park mobilyalarının yenilenmesi',
            'Mahallede yeni otopark yapılması',
            'Geç saat erişimi, erken kapanış veya güvenlik ve sessizlik koşullu kullanım',
            'Parkta satılan ürünlerin fiyatı',
        ],
        'correct_answer': 2,
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _phase_specs(assignment: str) -> list[tuple[str, str]]:
    if assignment == 'BA':
        return [('nkopru', 'night-transport'), ('raw', 'park-hours')]
    return [('raw', 'night-transport'), ('nkopru', 'park-hours')]


def _analysis_payload(scenario_key: str) -> dict[str, Any]:
    scenario = SCENARIOS[scenario_key]
    post = build_custom_post(scenario['title'], scenario['comments'])
    result = analyze_post(post, demo_mode=False, use_ai=False)
    return {
        'short_summary': result.short_summary,
        'common_ground': result.bridge['common_acceptance'],
        'main_divergence': result.bridge['main_divergence'],
        'bridge_question': result.bridge['bridge_question'],
        'viewpoints': [
            {
                'name': item.display_name or item.name,
                'percentage': item.percentage,
                'comment_count': item.comment_count,
            }
            for item in result.viewpoints
        ],
        'claim_count': len(result.claims),
        'open_question_count': sum(
            item.answer_status in {'Cevapsız', 'Kısmen cevaplandı'}
            for item in result.unanswered_questions
        ),
        'engine': 'N-KÖPRÜ yapısal analiz motoru',
    }


def _phase_payload(assignment: str, phase_index: int) -> dict[str, Any]:
    variant, scenario_key = _phase_specs(assignment)[phase_index]
    scenario = SCENARIOS[scenario_key]
    return {
        'phase_index': phase_index,
        'variant': variant,
        'scenario_key': scenario_key,
        'title': scenario['title'],
        'instructions': (
            'N-KÖPRÜ özetini ve görüş haritasını inceleyip soruyu yanıtla.'
            if variant == 'nkopru'
            else 'Yorumları doğrudan okuyup soruyu yanıtla.'
        ),
        'question': scenario['question'],
        'choices': list(scenario['choices']),
        'comments': list(scenario['comments']),
        'analysis': _analysis_payload(scenario_key) if variant == 'nkopru' else None,
    }


def _session_response(row, completed_phase_count: int | None = None) -> dict[str, Any]:
    if completed_phase_count is None:
        with connection() as conn:
            completed_phase_count = int(conn.execute(
                'SELECT COUNT(*) AS count FROM pilot_phase_results WHERE session_id = ?',
                (int(row['id']),),
            ).fetchone()['count'])
    completed = completed_phase_count >= 2 or bool(row['completed_at'])
    return {
        'session_id': int(row['id']),
        'participant_code': str(row['participant_code']),
        'practice': bool(row['practice']),
        'assignment': str(row['assignment']),
        'completed_phase_count': completed_phase_count,
        'completed': completed,
        'current_phase': None if completed else _phase_payload(str(row['assignment']), completed_phase_count),
    }


def start_session(*, consent: bool, practice: bool) -> dict[str, Any]:
    if not consent:
        raise ValueError('Pilot oturumu için bilgilendirilmiş onay gereklidir.')

    with transaction(immediate=True) as conn:
        sequence = int(conn.execute('SELECT COUNT(*) AS count FROM pilot_sessions').fetchone()['count'])
        assignment = 'AB' if sequence % 2 == 0 else 'BA'
        while True:
            participant_code = f'NK-{secrets.token_hex(3).upper()}'
            exists = conn.execute(
                'SELECT 1 FROM pilot_sessions WHERE participant_code = ?',
                (participant_code,),
            ).fetchone()
            if not exists:
                break
        cursor = conn.execute(
            'INSERT INTO pilot_sessions(participant_code, assignment, practice, consented_at) '
            'VALUES(?, ?, ?, ?)',
            (participant_code, assignment, int(practice), _now()),
        )
        row = conn.execute('SELECT * FROM pilot_sessions WHERE id = ?', (int(cursor.lastrowid),)).fetchone()
    return _session_response(row, 0)


def get_session(session_id: int) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute('SELECT * FROM pilot_sessions WHERE id = ?', (session_id,)).fetchone()
        if row is None:
            return None
        count = int(conn.execute(
            'SELECT COUNT(*) AS count FROM pilot_phase_results WHERE session_id = ?',
            (session_id,),
        ).fetchone()['count'])
    return _session_response(row, count)


def submit_phase(
    session_id: int,
    *,
    phase_index: int,
    selected_answer: int,
    duration_ms: int,
    clarity_rating: int,
    confidence_rating: int,
) -> dict[str, Any]:
    with transaction(immediate=True) as conn:
        session = conn.execute('SELECT * FROM pilot_sessions WHERE id = ?', (session_id,)).fetchone()
        if session is None:
            raise KeyError('Pilot oturumu bulunamadı.')

        existing = conn.execute(
            'SELECT * FROM pilot_phase_results WHERE session_id = ? AND phase_index = ?',
            (session_id, phase_index),
        ).fetchone()
        if existing is not None:
            result = dict(existing)
            completed_count = int(conn.execute(
                'SELECT COUNT(*) AS count FROM pilot_phase_results WHERE session_id = ?',
                (session_id,),
            ).fetchone()['count'])
        else:
            completed_count = int(conn.execute(
                'SELECT COUNT(*) AS count FROM pilot_phase_results WHERE session_id = ?',
                (session_id,),
            ).fetchone()['count'])
            if phase_index != completed_count:
                raise ValueError('Pilot adımları sırayla tamamlanmalıdır.')

            variant, scenario_key = _phase_specs(str(session['assignment']))[phase_index]
            scenario = SCENARIOS[scenario_key]
            correct = int(selected_answer == int(scenario['correct_answer']))
            completed_at = _now()
            cursor = conn.execute(
                'INSERT INTO pilot_phase_results('
                'session_id, phase_index, variant, scenario_key, selected_answer, correct, '
                'duration_ms, clarity_rating, confidence_rating, completed_at'
                ') VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    session_id, phase_index, variant, scenario_key, selected_answer, correct,
                    duration_ms, clarity_rating, confidence_rating, completed_at,
                ),
            )
            result = dict(conn.execute(
                'SELECT * FROM pilot_phase_results WHERE id = ?',
                (int(cursor.lastrowid),),
            ).fetchone())
            completed_count += 1
            if completed_count >= 2:
                conn.execute(
                    'UPDATE pilot_sessions SET completed_at = ? WHERE id = ?',
                    (completed_at, session_id),
                )
                session = conn.execute('SELECT * FROM pilot_sessions WHERE id = ?', (session_id,)).fetchone()

    return {
        'result': {
            'phase_index': int(result['phase_index']),
            'variant': str(result['variant']),
            'scenario_key': str(result['scenario_key']),
            'correct': bool(result['correct']),
            'duration_ms': int(result['duration_ms']),
            'clarity_rating': int(result['clarity_rating']),
            'confidence_rating': int(result['confidence_rating']),
        },
        'session': _session_response(session, completed_count),
    }


def _variant_metrics(rows: list, variant: str) -> dict[str, Any]:
    selected = [row for row in rows if row['variant'] == variant]
    if not selected:
        return {
            'variant': variant,
            'completed_task_count': 0,
            'median_duration_ms': None,
            'accuracy_percent': None,
            'average_clarity': None,
            'average_confidence': None,
        }
    return {
        'variant': variant,
        'completed_task_count': len(selected),
        'median_duration_ms': round(float(statistics.median(int(row['duration_ms']) for row in selected)), 1),
        'accuracy_percent': round(sum(int(row['correct']) for row in selected) * 100 / len(selected), 1),
        'average_clarity': round(sum(int(row['clarity_rating']) for row in selected) / len(selected), 2),
        'average_confidence': round(sum(int(row['confidence_rating']) for row in selected) / len(selected), 2),
    }


def get_overview() -> dict[str, Any]:
    with connection() as conn:
        completed = int(conn.execute(
            'SELECT COUNT(*) AS count FROM pilot_sessions WHERE practice = 0 AND completed_at IS NOT NULL'
        ).fetchone()['count'])
        active = int(conn.execute(
            'SELECT COUNT(*) AS count FROM pilot_sessions WHERE practice = 0 AND completed_at IS NULL'
        ).fetchone()['count'])
        practice = int(conn.execute(
            'SELECT COUNT(*) AS count FROM pilot_sessions WHERE practice = 1'
        ).fetchone()['count'])
        rows = list(conn.execute(
            'SELECT r.* FROM pilot_phase_results r '
            'JOIN pilot_sessions s ON s.id = r.session_id '
            'WHERE s.practice = 0 AND s.completed_at IS NOT NULL '
            'ORDER BY r.id'
        ).fetchall())

    raw = _variant_metrics(rows, 'raw')
    nkopru = _variant_metrics(rows, 'nkopru')
    time_gain = None
    if raw['median_duration_ms'] and nkopru['median_duration_ms'] is not None:
        time_gain = round((raw['median_duration_ms'] - nkopru['median_duration_ms']) * 100 / raw['median_duration_ms'], 1)
    accuracy_gain = None
    if raw['accuracy_percent'] is not None and nkopru['accuracy_percent'] is not None:
        accuracy_gain = round(nkopru['accuracy_percent'] - raw['accuracy_percent'], 1)
    clarity_gain = None
    if raw['average_clarity'] is not None and nkopru['average_clarity'] is not None:
        clarity_gain = round(nkopru['average_clarity'] - raw['average_clarity'], 2)

    minimum_reached = completed >= MINIMUM_SAMPLE_SIZE
    if not minimum_reached:
        conclusion = (
            f'Sonuç çıkarılmadı: en az {MINIMUM_SAMPLE_SIZE} tamamlanmış gerçek katılımcı gerekir; '
            f'şu anda {completed} tamamlandı.'
        )
    else:
        conclusion = (
            'Ekrandaki farklar bu proje içi kullanıcı pilotunun betimsel sonuçlarıdır; '
            'nedensel veya toplum geneline yayılan bir başarı iddiası değildir.'
        )

    return {
        'protocol_version': PROTOCOL_VERSION,
        'recommended_participants': '8–12 gerçek katılımcı',
        'completed_session_count': completed,
        'active_session_count': active,
        'practice_session_count': practice,
        'minimum_sample_reached': minimum_reached,
        'raw': raw,
        'nkopru': nkopru,
        'time_gain_percent': time_gain,
        'accuracy_gain_points': accuracy_gain,
        'clarity_gain': clarity_gain,
        'conclusion': conclusion,
        'integrity_note': (
            'İsim, e-posta veya serbest metin yanıtı toplanmaz. Atama sırası dönüşümlü AB/BA yapılır; '
            'deneme oturumları metriklere katılmaz ve yalnız tamamlanmış gerçek oturumlar karşılaştırılır.'
        ),
    }


def export_csv() -> str:
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow([
        'protocol_version', 'participant_code', 'assignment', 'phase_index', 'variant',
        'scenario_key', 'correct', 'duration_ms', 'clarity_rating', 'confidence_rating',
        'completed_at',
    ])
    with connection() as conn:
        rows = conn.execute(
            'SELECT s.participant_code, s.assignment, r.phase_index, r.variant, r.scenario_key, '
            'r.correct, r.duration_ms, r.clarity_rating, r.confidence_rating, r.completed_at '
            'FROM pilot_phase_results r JOIN pilot_sessions s ON s.id = r.session_id '
            'WHERE s.practice = 0 AND s.completed_at IS NOT NULL ORDER BY s.id, r.phase_index'
        ).fetchall()
    for row in rows:
        writer.writerow([
            PROTOCOL_VERSION, row['participant_code'], row['assignment'], row['phase_index'],
            row['variant'], row['scenario_key'], row['correct'], row['duration_ms'],
            row['clarity_rating'], row['confidence_rating'], row['completed_at'],
        ])
    return output.getvalue()
