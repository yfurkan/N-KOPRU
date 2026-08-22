from __future__ import annotations

import hashlib
import re
import time
import unicodedata
from dataclasses import dataclass

from .models import ClaimItem, Comment, QuestionItem, StanceDetail


QUESTION_SUFFIX_PATTERN = re.compile(r'\b(mi|mu)\b', re.IGNORECASE)

UNMARKED_QUESTION_PATTERNS = (
    r'^(?:ne|neden|nicin|nasil|hangi|kim|kac|nerede|nereye|nereden|ne zaman)\b',
    r'\b(?:nedir|kimdir|kactir|nerededir)\s*$',
    r'\bnasil\b.*\b(?:calisiyor|isliyor|oluyor|yapiliyor|belirleniyor)\s*$',
    r'\b(?:soyler|aciklar|paylasir) misin\s*$',
)

EVIDENCE_PATTERNS = (
    r'\bkaynak\w*\b',
    r'\barastir\w*\b',
    r'\bcalisma\w*\b',
    r'\bveri\w*\b',
    r'\bkanit\w*\b',
    r'\bistatistik\w*\b',
    r'\banket\w*\b',
    r'\bolcum\w*\b',
    r'\breferans\w*\b',
    r'\bdayan\w*\b',
)

EVIDENCE_REQUEST_PATTERNS = (
    r'kayna(?:k|gi)\s+(?:nedir|ne|var mi|paylas)',
    r'(?:arastirma|calisma|veri|kanit|istatistik|anket)\s+(?:var mi|nedir)',
    r'(?:kaynak|referans)\s+(?:paylasilmali|paylasabilir|gosterilmeli|sunulmali|bekleniyor)',
    r'(?:hangi|ne)\s+(?:kaynaga|veriye|kanita|arastirmaya|calismaya)',
    r'(?:kaynak|veri|kanit|arastirma|calisma)\s+(?:gerekli|bekleniyor|sunulmali|gosterilmeli)',
    r'dayandigi\s+(?:kaynak|veri|kanit)',
    r'(?:guvenilir|karsilastirmali)\s+(?:arastirma|calisma|veri|kanit)\s+(?:gerekli|bekleniyor|var mi|bulunuyor mu)',
)

RHETORICAL_PATTERNS = (
    r'\bsaka mi\b',
    r'\bciddi misin\b',
    r'\bbuna kim inanir\b',
    r'\bbunu kim savunur\b',
    r'\bbu nasil (?:mantik|sacmalik)\b',
    r'\bbaska ne beklenirdi\b',
    r'\bne anlami var\b',
    r'\banlamamak mumkun mu\b',
    r'\bdaha ne olsun\b',
)

DECISION_PATTERNS = (
    r'\b(?:olmali|olmamali|yapilmali|yapilmamali|yasaklanmali|duzenlenmeli|uygulanmali)\s+(?:mi|mu)\b',
    r'\b\w+(?:mali|meli)\s+(?:mi|mu)\b',
    r'\bne yapilmali\b',
    r'\bnasil (?:duzenlenmeli|uygulanmali|karar verilmeli)\b',
)

ANSWER_MARKERS = (
    'cunku', 'nedeni', 'bu nedenle', 'bu yuzden', 'cevabi', 'soyle aciklanabilir',
    'arastirmaya gore', 'calismaya gore', 'verilere gore', 'rapora gore', 'ankete gore',
)

SOURCE_PROVIDED_PATTERNS = (
    r'https?://', r'\bwww\.', r'\bdoi\b', r'\b10\.\d{4,9}/',
    r'\b(?:19|20)\d{2}\b.*\b(?:arastirma|calisma|rapor|anket)\b',
    r'\b(?:arastirma|calisma|rapor|anket)\b.*\b(?:19|20)\d{2}\b',
    r'\b(?:arastirmaya|calismaya|verilere|rapora|ankete) gore\b',
)

STOPWORDS = {
    'acaba', 'ama', 'ancak', 'bu', 'buna', 'bunu', 'bunun', 'da', 'daha', 'de', 'diye',
    'gibi', 'icin', 'ile', 'ise', 'mi', 'mu', 'ne', 'neden', 'nasil',
    'hangi', 'kim', 'kac', 'nerede', 'nedir', 'olan', 'olarak', 'oldugu',
    've', 'veya', 'ya', 'var', 'yok', 'bir', 'gercekten', 'konuda', 'sence',
}

GENERIC_SEMANTIC_TOKENS = {'evidence', 'question', 'decision'}

ROOT_PREFIXES = (
    ('kaynak', 'evidence'), ('arastir', 'evidence'), ('calisma', 'evidence'),
    ('veri', 'evidence'), ('kanit', 'evidence'), ('istatistik', 'evidence'),
    ('anket', 'evidence'), ('olcum', 'evidence'), ('referans', 'evidence'),
    ('basari', 'learning'), ('ogren', 'learning'), ('akademik', 'learning'),
    ('performans', 'learning'), ('yasak', 'restriction'), ('yasag', 'restriction'), ('kisit', 'restriction'),
    ('sinir', 'restriction'), ('etki', 'effect'), ('artir', 'increase'), ('artis', 'increase'),
    ('azalt', 'decrease'), ('kullan', 'usage'), ('uygula', 'implementation'),
    ('duzen', 'regulation'), ('gizli', 'privacy'), ('mahrem', 'privacy'),
    ('guven', 'trust'), ('seffaf', 'transparency'), ('bildirim', 'notification'),
    ('uyku', 'sleep'), ('maliyet', 'cost'), ('butce', 'cost'),
)


@dataclass
class _Candidate:
    comment_id: int
    text: str
    question_type: str
    rhetorical: bool
    confidence: float
    reason: str
    tokens: set[str]


def _fold(text: str) -> str:
    normalized = unicodedata.normalize('NFKD', (text or '').casefold())
    stripped = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
    return stripped.replace('ı', 'i')


def _normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9\s]', ' ', _fold(text))).strip()


def _semantic_root(token: str) -> str:
    for prefix, root in ROOT_PREFIXES:
        if token.startswith(prefix):
            return root
    for suffix in ('lar', 'ler', 'lari', 'leri', 'nin', 'nın', 'nun', 'nün', 'dan', 'den', 'dir', 'dır'):
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            return token[:-len(suffix)]
    return token


def _semantic_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for token in re.findall(r'[a-z0-9]+', _fold(text)):
        if len(token) < 3 or token in STOPWORDS:
            continue
        tokens.add(_semantic_root(token))
    return tokens


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    folded = _fold(text)
    return any(re.search(pattern, folded, flags=re.IGNORECASE) for pattern in patterns)


def _has_evidence_signal(text: str) -> bool:
    return _matches_any(text, EVIDENCE_PATTERNS)


def _is_evidence_request(text: str) -> bool:
    if not _has_evidence_signal(text):
        return False
    return '?' in text or _matches_any(text, EVIDENCE_REQUEST_PATTERNS)


def _split_sentences(text: str) -> list[str]:
    rows = re.split(r'(?<=[?!])\s+|(?<=\.)\s+', (text or '').strip())
    return [row.strip() for row in rows if row.strip()]


def _classify_candidate(text: str, comment_id: int) -> _Candidate | None:
    folded = _fold(text)
    evidence_request = _is_evidence_request(text)
    unmarked_question = not text.rstrip().endswith('.') and _matches_any(text, UNMARKED_QUESTION_PATTERNS)
    has_question_form = (
        '?' in text
        or QUESTION_SUFFIX_PATTERN.search(folded) is not None
        or unmarked_question
    )
    if not evidence_request and not has_question_form:
        return None

    rhetorical = not evidence_request and _matches_any(text, RHETORICAL_PATTERNS)
    if rhetorical:
        question_type = 'Retorik / Meydan Okuma'
        confidence = 0.93
        reason = 'Retorik kalıp tespit edildi; doğrudan bilgi talebi olarak değerlendirilmedi.'
    elif evidence_request:
        question_type = 'Kaynak / Kanıt Talebi'
        confidence = 0.98 if '?' in text else 0.88
        reason = 'Kaynak, araştırma, veri veya kanıt ihtiyacı açıkça ifade ediliyor.'
    elif _matches_any(text, DECISION_PATTERNS):
        question_type = 'Uygulama / Karar Sorusu'
        confidence = 0.93
        reason = 'Bir kararın veya uygulama biçiminin nasıl olması gerektiği soruluyor.'
    else:
        question_type = 'Bilgi / Açıklama Sorusu'
        confidence = 0.92 if '?' in text else 0.82
        reason = 'Açıklama ya da bilgi isteyen soru yapısı tespit edildi.'

    return _Candidate(
        comment_id=comment_id,
        text=text,
        question_type=question_type,
        rhetorical=rhetorical,
        confidence=confidence,
        reason=reason,
        tokens=_semantic_tokens(text),
    )


def _same_question(left: _Candidate, right: _Candidate) -> bool:
    if left.question_type != right.question_type:
        return False
    if _normalize(left.text) == _normalize(right.text):
        return True
    left_topic = left.tokens - GENERIC_SEMANTIC_TOKENS
    right_topic = right.tokens - GENERIC_SEMANTIC_TOKENS
    shared = left_topic & right_topic
    if not shared:
        return False
    containment = len(shared) / max(1, min(len(left_topic), len(right_topic)))
    if len(shared) >= 3 and containment >= 0.5:
        return True
    if left.question_type == 'Kaynak / Kanıt Talebi' and len(shared) >= 2:
        return True
    return False


def _group_candidates(candidates: list[_Candidate]) -> list[list[_Candidate]]:
    groups: list[list[_Candidate]] = []
    for candidate in candidates:
        for group in groups:
            if any(_same_question(candidate, item) for item in group):
                group.append(candidate)
                break
        else:
            groups.append([candidate])
    return groups


def _source_provided(text: str) -> bool:
    return _matches_any(text, SOURCE_PROVIDED_PATTERNS)


def _answer_strength(question: _Candidate, comment: Comment) -> int:
    if comment.id <= question.comment_id:
        return 0
    candidate = _classify_candidate(comment.text, comment.id)
    if candidate is not None and not _source_provided(comment.text):
        return 0

    answer_tokens = _semantic_tokens(comment.text)
    shared = (question.tokens - GENERIC_SEMANTIC_TOKENS) & (answer_tokens - GENERIC_SEMANTIC_TOKENS)
    if not shared:
        return 0

    folded = _fold(comment.text)
    has_answer_marker = any(marker in folded for marker in ANSWER_MARKERS)
    if question.question_type == 'Kaynak / Kanıt Talebi':
        if _source_provided(comment.text):
            return 2
        if len(shared) >= 2 and (_has_evidence_signal(comment.text) or re.search(r'\d', comment.text)):
            return 1
        return 0

    if has_answer_marker and len(shared) >= 1:
        return 2
    if _source_provided(comment.text) and len(shared) >= 1:
        return 2
    if '?' not in comment.text and len(shared) >= 2:
        return 1
    return 0


def _affected_viewpoints(group: list[_Candidate], comments: list[Comment], stances: list[StanceDetail]) -> list[str]:
    group_tokens = set().union(*(item.tokens for item in group)) - GENERIC_SEMANTIC_TOKENS
    labels_by_id = {item.comment_id: item.label for item in stances}
    counts: dict[str, int] = {}
    for comment in comments:
        label = labels_by_id.get(comment.id, '')
        if not label or label in {'Soru / Tarafsız', 'Diğer / Nötr'}:
            continue
        shared = group_tokens & (_semantic_tokens(comment.text) - GENERIC_SEMANTIC_TOKENS)
        if shared:
            counts[label] = counts.get(label, 0) + len(shared)
    return [label for label, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:3]]


def _linked_claim(group: list[_Candidate], claims: list[ClaimItem]) -> bool:
    group_tokens = set().union(*(item.tokens for item in group)) - GENERIC_SEMANTIC_TOKENS
    for claim in claims:
        claim_tokens = _semantic_tokens(claim.text) - GENERIC_SEMANTIC_TOKENS
        if len(group_tokens & claim_tokens) >= 2:
            return True
    return False


def _impact_text(question_type: str, status: str, affected: list[str], linked_claim: bool) -> str:
    if status == 'Cevaplandı':
        return 'Yanıt bağlantısı bulundu; tartışmada bu yanıtın güvenilirliği ve farklı görüşleri karşılayıp karşılamadığı değerlendirilebilir.'
    if question_type == 'Kaynak / Kanıt Talebi':
        base = 'Yanıtlanırsa iddiaların kanıt düzeyi ve görüşleri karşılaştırmak için kullanılacak ölçütler netleşebilir.'
    elif question_type == 'Uygulama / Karar Sorusu':
        base = 'Yanıtlanırsa önerilerin uygulanabilirliği ve ortak karar ölçütleri daha açık hâle gelebilir.'
    else:
        base = 'Yanıtlanırsa tartışmadaki belirsizlik azalabilir ve görüşler aynı bilgi üzerinden karşılaştırılabilir.'
    if linked_claim:
        base = base.replace('iddiaların', 'tespit edilen iddiaların')
    if affected:
        return f'{base} Özellikle {", ".join(affected[:2])} kümeleri arasındaki değerlendirmeyi etkileyebilir.'
    return base


def _identity_key(group: list[_Candidate]) -> str:
    representative = min(group, key=lambda item: (item.comment_id, _normalize(item.text)))
    payload = f'{representative.question_type}|{_normalize(representative.text)}'
    return 'q120|' + hashlib.sha256(payload.encode('utf-8')).hexdigest()[:20]


def _to_question_item(
    group: list[_Candidate],
    comments: list[Comment],
    stances: list[StanceDetail],
    claims: list[ClaimItem],
) -> QuestionItem:
    representative = min(group, key=lambda item: item.comment_id)
    answer_ids: list[int] = []
    strongest = 0
    for comment in comments:
        if comment.id in {item.comment_id for item in group}:
            continue
        strength = max(_answer_strength(item, comment) for item in group)
        if strength:
            answer_ids.append(comment.id)
            strongest = max(strongest, strength)

    if representative.rhetorical:
        answer_status = 'Retorik'
    elif strongest >= 2:
        answer_status = 'Cevaplandı'
    elif strongest == 1:
        answer_status = 'Kısmen cevaplandı'
    else:
        answer_status = 'Cevapsız'

    affected = _affected_viewpoints(group, comments, stances)
    linked_claim = _linked_claim(group, claims)
    if answer_status in {'Cevaplandı', 'Retorik'}:
        priority = 'Düşük'
    elif representative.question_type == 'Kaynak / Kanıt Talebi' or linked_claim or len(affected) >= 2:
        priority = 'Yüksek'
    else:
        priority = 'Orta'

    evidence_ids = sorted({item.comment_id for item in group})
    confidence = min(0.99, max(item.confidence for item in group) + (0.01 if len(group) > 1 else 0.0))
    return QuestionItem(
        comment_id=representative.comment_id,
        text=representative.text,
        question_type=representative.question_type,
        answer_status=answer_status,
        priority=priority,
        confidence=round(confidence, 3),
        evidence_comment_ids=evidence_ids,
        repeated_comment_ids=[item for item in evidence_ids if item != representative.comment_id],
        answer_comment_ids=sorted(set(answer_ids)),
        affected_viewpoints=affected,
        impact=_impact_text(representative.question_type, answer_status, affected, linked_claim),
        engine='Yapısal-semantik soru analizi',
        detection_reason=representative.reason,
        identity_key=_identity_key(group),
    )


def analyze_questions(
    comments: list[Comment],
    stance_details: list[StanceDetail],
    claims: list[ClaimItem],
) -> tuple[list[QuestionItem], list[QuestionItem], dict]:
    started = time.perf_counter()
    candidates: list[_Candidate] = []
    for comment in comments:
        for sentence in _split_sentences(comment.text):
            candidate = _classify_candidate(sentence, comment.id)
            if candidate is not None:
                candidates.append(candidate)

    actionable_groups = _group_candidates([item for item in candidates if not item.rhetorical])
    rhetorical_groups = _group_candidates([item for item in candidates if item.rhetorical])
    questions = [_to_question_item(group, comments, stance_details, claims) for group in actionable_groups]
    rhetorical = [_to_question_item(group, comments, stance_details, claims) for group in rhetorical_groups]

    priority_order = {'Yüksek': 0, 'Orta': 1, 'Düşük': 2}
    status_order = {'Cevapsız': 0, 'Kısmen cevaplandı': 1, 'Cevaplandı': 2, 'Retorik': 3}
    questions.sort(key=lambda item: (status_order.get(item.answer_status, 9), priority_order.get(item.priority, 9), item.comment_id))
    rhetorical.sort(key=lambda item: item.comment_id)

    info = {
        'mode': 'structural-semantic-question',
        'candidate_count': len(candidates),
        'actionable_count': len(questions),
        'unanswered_count': sum(item.answer_status == 'Cevapsız' for item in questions),
        'partial_count': sum(item.answer_status == 'Kısmen cevaplandı' for item in questions),
        'answered_count': sum(item.answer_status == 'Cevaplandı' for item in questions),
        'rhetorical_count': len(rhetorical),
        'grouped_repeat_count': sum(len(item.repeated_comment_ids) for item in [*questions, *rhetorical]),
        'elapsed_ms': round((time.perf_counter() - started) * 1000),
    }
    return questions, rhetorical, info
