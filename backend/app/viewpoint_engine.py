"""N-KÖPRÜ v1.2.2: açıklanabilir ve geriye uyumlu Görüş Haritası.

``Viewpoint.name`` önceki snapshot, Köprü ve bildirim olay kimliğidir.
Bu modül onu değiştirmez; tartışma bağlamı ve dayanaklarını ek alanlarda taşır.
"""
from __future__ import annotations

import re
import time
from collections import Counter

from .models import (
    ClaimItem,
    Comment,
    CommonGroundItem,
    QuestionItem,
    StanceDetail,
    Viewpoint,
    ViewpointEvidence,
)


THEME_SIGNALS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ('Öğrenme ve öğrenci başarısı', ('öğren', 'başarı', 'öğrenci', 'düşün', 'eğitim', 'ders', 'ödev', 'sınav')),
    ('Akademik güvenilirlik ve şeffaflık', ('akademik', 'güvenilir', 'şeffaf', 'kaynak göster', 'intihal', 'etik', 'açıkça belirtil')),
    ('Açık kurallar ve denetim', ('kontrollü', 'kontrol', 'kural', 'denet', 'yönerge', 'koşul', 'şart', 'sınır', 'düzen')),
    ('Faydalı kullanım ve erişim', ('faydalı', 'yararlı', 'destek', 'kolay', 'açıklama almak', 'okuryazar', 'kullanım alan')),
    ('Risk ve olumsuz etki', ('risk', 'zarar', 'tehlik', 'problem', 'sorun', 'bırakıyor', 'bağıml')),
    ('Kanıt ve araştırma ihtiyacı', ('araştırma', 'kanıt', ' veri', 'veri ', 'kaynak', 'ölç', 'istatistik', 'örneklem', 'karşılaştır')),
    ('Kullanıcı tercihi ve özgürlüğü', ('özgür', 'tercih', 'seçim', 'engelle', 'serbest', 'kullanıcı')),
    ('Uyku ve bildirim etkisi', ('uyku', 'bildirim', 'gece', 'sessiz')),
)

NEUTRAL_NAMES = {'Soru / Tarafsız', 'Diğer / Nötr'}


def _is_restriction_context(title: str, comments: list[Comment]) -> bool:
    title_lower = title.casefold()
    if any(signal in title_lower for signal in ('yasak', 'kısıt', 'sınır', 'düzenlen', 'kontrol')):
        return True
    restricted_comments = sum(
        any(signal in comment.text.casefold() for signal in ('yasak', 'kısıt', 'serbest', 'kontrollü'))
        for comment in comments
    )
    return restricted_comments >= max(2, round(len(comments) * 0.30))


def _display_name(canonical_name: str, restricted: bool) -> str:
    restricted_names = {
        'Koşullu / Dengeli': 'Kontrollü ve kurallı kullanım',
        'Karşı / Sınırlayıcı': 'Tam yasak veya güçlü sınırlama',
        'Destekleyen': 'Yasağa karşı / kullanım alanlarını koruma',
        'Soru / Tarafsız': 'Kanıt talebi / tarafsız değerlendirme',
        'Diğer / Nötr': 'Kararsız veya ek değerlendirme',
    }
    general_names = {
        'Koşullu / Dengeli': 'Koşullu ve dengeli değerlendirme',
        'Karşı / Sınırlayıcı': 'Öneriye karşı çıkan / sınırlayıcı yaklaşım',
        'Destekleyen': 'Öneriyi veya mevcut yaklaşımı destekleyenler',
        'Soru / Tarafsız': 'Kanıt talebi / tarafsız değerlendirme',
        'Diğer / Nötr': 'Kararsız veya ek değerlendirme',
    }
    mapping = restricted_names if restricted else general_names
    return mapping.get(canonical_name, canonical_name)


def _comment_themes(text: str) -> list[str]:
    lower = f' {text.casefold()} '
    return [theme for theme, signals in THEME_SIGNALS if any(signal in lower for signal in signals)]


def _theme_counts(comments: list[Comment]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for comment in comments:
        counts.update(_comment_themes(comment.text))
    return counts


def _human_theme_list(themes: list[str], max_items: int = 2) -> str:
    chosen = [theme.casefold() for theme in themes[:max_items]]
    if not chosen:
        return 'tartışmanın sonuçları ve uygulanabilirliği'
    if len(chosen) == 1:
        return chosen[0]
    return f'{chosen[0]} ile {chosen[1]}'


def _main_argument(name: str, themes: list[str], restricted: bool) -> str:
    focus = _human_theme_list(themes)
    if name == 'Koşullu / Dengeli':
        if restricted:
            return f'Tam yasak yerine açık kurallar, denetim ve bağlama göre kullanım öneriliyor; ana gerekçe {focus}.'
        return f'Kesin kabul veya ret yerine koşulların, kuralların ve {focus} boyutunun birlikte değerlendirilmesi isteniyor.'
    if name == 'Karşı / Sınırlayıcı':
        if restricted:
            return f'{focus.capitalize()} konusundaki sakıncalar nedeniyle tam yasaklama veya daha güçlü sınırlama savunuluyor.'
        return f'Önerinin olası sakıncaları ve {focus} nedeniyle daha sınırlayıcı bir yaklaşım benimseniyor.'
    if name == 'Destekleyen':
        if restricted:
            return f'Kullanımın tamamen yasaklanmasına karşı çıkılıyor; {focus} açısından yararlı kullanım alanlarının korunması savunuluyor.'
        return f'Önerinin veya mevcut yaklaşımın {focus} açısından sağlayabileceği yararlar öne çıkarılıyor.'
    if name == 'Soru / Tarafsız':
        return f'Doğrudan taraf seçmeden kararın {focus} açısından güvenilir veri, açıklama veya araştırmayla desteklenmesi isteniyor.'
    return f'Belirgin bir taraf seçmek yerine {focus} konusunda ek gözlem, koşul veya değerlendirme sunuluyor.'


def _representative_score(comment: Comment, detail: StanceDetail, themes: list[str]) -> tuple[float, int, int]:
    matched = len(set(_comment_themes(comment.text)) & set(themes[:3]))
    words = len(comment.text.split())
    readable = 1 if 5 <= words <= 28 else 0
    model_signal = min(detail.confidence, 1.0) if detail.confidence > 0 else 0.30
    score = matched * 2 + readable + model_signal + min(comment.likes, 30) / 30
    return score, min(comment.likes, 30), -comment.id


def _representative_comments(
    comments: list[Comment],
    stance_by_id: dict[int, StanceDetail],
    themes: list[str],
) -> list[ViewpointEvidence]:
    ranked = sorted(
        comments,
        key=lambda item: _representative_score(item, stance_by_id[item.id], themes),
        reverse=True,
    )
    representatives: list[ViewpointEvidence] = []
    seen: set[str] = set()
    for comment in ranked:
        normalized = re.sub(r'\s+', ' ', comment.text.casefold()).strip()
        if normalized in seen:
            continue
        seen.add(normalized)
        detail = stance_by_id[comment.id]
        representatives.append(ViewpointEvidence(
            comment_id=comment.id,
            author=comment.author,
            text=comment.text,
            confidence=detail.confidence,
            engine=detail.engine,
        ))
        if len(representatives) == 2:
            break
    return representatives


def _opposing_names(name: str, available: set[str]) -> list[str]:
    priorities = {
        'Koşullu / Dengeli': ['Karşı / Sınırlayıcı', 'Destekleyen'],
        'Karşı / Sınırlayıcı': ['Destekleyen', 'Koşullu / Dengeli'],
        'Destekleyen': ['Karşı / Sınırlayıcı', 'Koşullu / Dengeli'],
        'Soru / Tarafsız': [],
        'Diğer / Nötr': [],
    }
    return [other for other in priorities.get(name, []) if other in available][:2]


def _relationship_note(name: str, opponents: list[str], shared_themes: list[str], restricted: bool) -> str:
    if name in NEUTRAL_NAMES:
        return 'Bu grup karşıt bir karar tarafı değildir; diğer görüşleri sınamak için soru, kanıt veya ek değerlendirme sağlar.'
    if not opponents:
        return 'Bu analizde doğrudan karşılaştırılabilecek belirgin bir karşıt görüş kümesi bulunmuyor.'
    if name == 'Koşullu / Dengeli' and restricted:
        difference = 'Tam yasak ile geniş serbestlik arasında koşul ve denetim üzerinden ara bir yaklaşım sunar.'
    elif name == 'Karşı / Sınırlayıcı' and restricted:
        difference = 'Kullanım alanlarını koruyan veya kontrollü izin veren kümelerden sınırın sertliği konusunda ayrışır.'
    elif name == 'Destekleyen' and restricted:
        difference = 'Tam yasak isteyen kümeden kullanımın sürdürülmesi; koşullu kümeden ise sınırların genişliği konusunda ayrışır.'
    else:
        difference = 'Diğer görüşlerle önerinin yararı, riski ve uygulanma koşulları bakımından ayrışır.'
    if shared_themes:
        return f'{difference} Kesişim alanı: {shared_themes[0]}.'
    return difference


def enrich_viewpoints(
    title: str,
    comments: list[Comment],
    viewpoints: list[Viewpoint],
    stance_details: list[StanceDetail],
    claims: list[ClaimItem],
    questions: list[QuestionItem],
    common_ground: list[CommonGroundItem],
) -> tuple[list[Viewpoint], dict]:
    started = time.perf_counter()
    restricted = _is_restriction_context(title, comments)
    stance_by_id = {item.comment_id: item for item in stance_details}
    available_names = {item.name for item in viewpoints}
    enriched: list[Viewpoint] = []

    for viewpoint in viewpoints:
        group_comments = [comment for comment in comments if stance_by_id.get(comment.id) and stance_by_id[comment.id].label == viewpoint.name]
        group_ids = {item.id for item in group_comments}
        themes = [theme for theme, _ in _theme_counts(group_comments).most_common(3)]
        shared = [
            item.theme for item in common_ground
            if group_ids.intersection(item.evidence_comment_ids)
        ]
        model_confidences = [
            stance_by_id[item.id].confidence
            for item in group_comments
            if stance_by_id[item.id].confidence > 0
        ]
        opposing = _opposing_names(viewpoint.name, available_names)
        linked_questions = [
            item.comment_id for item in questions
            if viewpoint.name in item.affected_viewpoints
            or group_ids.intersection(item.evidence_comment_ids)
        ]
        enriched.append(viewpoint.model_copy(update={
            'display_name': _display_name(viewpoint.name, restricted),
            'comment_count': len(group_comments),
            'main_argument': _main_argument(viewpoint.name, themes, restricted),
            'evidence_comment_ids': [item.id for item in group_comments],
            'representative_comments': _representative_comments(group_comments, stance_by_id, themes),
            'dominant_themes': themes,
            'shared_themes': list(dict.fromkeys(shared))[:2],
            'opposing_viewpoint_names': opposing,
            'relationship_note': _relationship_note(viewpoint.name, opposing, shared, restricted),
            'related_claim_comment_ids': [item.comment_id for item in claims if item.comment_id in group_ids],
            'related_question_comment_ids': list(dict.fromkeys(linked_questions)),
            'model_comment_count': len(model_confidences),
            'structural_comment_count': len(group_comments) - len(model_confidences),
            'average_model_confidence': round(sum(model_confidences) / len(model_confidences), 4) if model_confidences else 0.0,
        }))

    info = {
        'mode': 'contextual-evidence-grounded-viewpoints',
        'context': 'restriction-policy' if restricted else 'general-discussion',
        'cluster_count': len(enriched),
        'representative_count': sum(len(item.representative_comments) for item in enriched),
        'model_comment_count': sum(item.model_comment_count for item in enriched),
        'structural_comment_count': sum(item.structural_comment_count for item in enriched),
        'elapsed_ms': round((time.perf_counter() - started) * 1000),
    }
    return enriched, info
