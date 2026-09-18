import re
import time
from collections import Counter
from .models import AnalysisResult, Viewpoint, Comment, Post, StanceDetail
from .demo import DEMO_POST
from .stance_engine import classify_stances, semantic_guardrail_label, status as ai_status
from .argument_engine import analyze_claims, build_common_ground, build_bridge, source_awareness_stats
from .question_engine import analyze_questions
from .viewpoint_engine import enrich_viewpoints

OFFENSIVE_WORDS = {
    'saçmalık', 'aptal', 'cahil', 'gerizekalı', 'salak', 'beyinsiz', 'ahmak',
    'embesil', 'dangalak', 'şerefsiz', 'ezik', 'anlamıyorsun', 'bilmiyorsun'
}
OFFENSIVE_PATTERNS = [
    r'\bmal\s*beyinli\b',
    r'\byavşak\b',
    r'\bgeri\s*zek[aâ]l[ıi]\b',
    r'\bgerizek[aâ]l[ıi]\b',
    r'\bşerefsiz\b',
    r'\bsiktir\b',
    r'\borospu\b',
    r'\bpiç\b',
    r'\bbeyinsiz\b',
    r'\bdangalak\b',
    r'\bembesil\b',
]
SUPPORT_WORDS = {
    'katılıyorum', 'destekliyorum', 'faydalı', 'yararlı', 'doğru', 'gerekli', 'olumlu',
    'serbest', 'mantıklı', 'iyi olur', 'desteklenmeli'
}
OPPOSE_WORDS = {
    'katılmıyorum', 'karşıyım', 'yanlış', 'yasak', 'zararlı', 'tehlikeli', 'sorun',
    'riskli', 'olumsuz', 'engellenmeli', 'ciddi problem'
}
CONDITIONAL_WORDS = {
    'kontrollü', 'koşullu', 'ancak', 'ama', 'şartıyla', 'şart', 'denetim', 'kural',
    'yönerge', 'sınırlandır', 'dengeli', 'bağlama göre'
}

VIEWPOINT_SUMMARIES = {
    'Destekleyen': 'Ana öneriyi veya yaklaşımı olumlu değerlendiren katkılar.',
    'Karşı / Sınırlayıcı': 'Ana öneriye karşı çıkan ya da daha güçlü sınırlama isteyen katkılar.',
    'Koşullu / Dengeli': 'Bağlama, kurallara veya belirli koşullara göre değerlendirme öneren katkılar.',
    'Soru / Tarafsız': 'Kanıt, açıklama veya ek bilgi isteyen; doğrudan taraf belirtmeyen katkılar.',
    'Diğer / Nötr': 'Belirgin bir destek/karşıtlık sinyali taşımayan veya farklı boyut ekleyen katkılar.',
}


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return re.sub(r'[.!?]+$', '', text)


def base_demo_text(text: str) -> str:
    for marker in [
        ' Bu ayrımın yönetmelikte',
        ' Özellikle birinci sınıflarda',
        ' Öğretim elemanlarının da',
    ]:
        text = text.split(marker)[0]
    return text.strip()


def deduplicate_comments(comments, demo_mode: bool = False):
    seen = set()
    result = []
    for comment in comments:
        text = base_demo_text(comment.text) if demo_mode else comment.text.strip()
        key = normalize_text(text)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append((comment, text))
    return result


def classify_viewpoint_heuristic(text: str, title: str = '') -> str:
    t = text.lower()
    if '?' in text:
        return 'Soru / Tarafsız'

    guarded_label, _ = semantic_guardrail_label(text, title)
    if guarded_label is not None:
        return guarded_label

    support = sum(1 for word in SUPPORT_WORDS if word in t)
    oppose = sum(1 for word in OPPOSE_WORDS if word in t)
    conditional = sum(
        1
        for word in CONDITIONAL_WORDS
        if (
            bool(re.search(rf'\b{re.escape(word)}(?!siz|sız)\w*', t))
            if word in {'denetim', 'kural', 'şart'}
            else bool(re.search(rf'\b{re.escape(word)}\b', t))
            if word in {'ama', 'ancak'}
            else word in t
        )
    )

    if conditional >= max(support, oppose) and conditional > 0:
        return 'Koşullu / Dengeli'
    if support > oppose:
        return 'Destekleyen'
    if oppose > support:
        return 'Karşı / Sınırlayıcı'
    return 'Diğer / Nötr'


def is_offensive(text: str) -> bool:
    t = text.lower()
    if any(word in t for word in OFFENSIVE_WORDS):
        return True
    return any(re.search(pattern, t, flags=re.IGNORECASE) for pattern in OFFENSIVE_PATTERNS)


def build_viewpoints_from_details(details: list[dict], total: int) -> list[Viewpoint]:
    counts = Counter(d['label'] for d in details)
    return [
        Viewpoint(name=name, percentage=round(count * 100 / max(1, total)), summary=VIEWPOINT_SUMMARIES[name])
        for name, count in counts.most_common()
    ]


def build_viewpoints_heuristic(
    comments,
    title: str = '',
) -> tuple[list[Viewpoint], list[dict]]:
    details = [
        {
            'comment_id': c.id,
            'text': c.text,
            'label': classify_viewpoint_heuristic(c.text, title),
            'confidence': 0.0,
            'engine': semantic_guardrail_label(c.text, title)[1] or 'heuristik yedek',
        }
        for c in comments
    ]
    return build_viewpoints_from_details(details, len(comments)), details


def _stance_execution_description(engine_info: dict, stance_details: list[StanceDetail]) -> tuple[str, str]:
    model_count = sum(item.confidence > 0 for item in stance_details)
    structural_count = len(stance_details) - model_count
    hybrid = engine_info.get('mode') in {'transformer-zero-shot', 'hybrid-transformer'}

    if not hybrid:
        return 'Görüş katmanı yapısal heuristik yedekle çıkarıldı.', 'heuristic-fallback'
    if model_count == 0:
        return (
            'Görüş katmanı hibrit analiz motorunun yapısal Türkçe sinyalleriyle çıkarıldı; '
            'bu analizde Transformer çıkarımı gerekmedi.',
            'structural-only',
        )
    if structural_count == 0:
        return (
            f'Görüş katmanı hibrit analiz motorunun {model_count} Transformer çıkarımıyla oluşturuldu.',
            'transformer-only',
        )
    return (
        f'Görüş katmanı hibrit analiz motorunun {structural_count} yapısal kararı '
        f've {model_count} Transformer çıkarımıyla oluşturuldu.',
        'hybrid-structural-transformer',
    )


def _localize_question_impacts(questions, viewpoints):
    labels = {
        item.name: item.display_name or item.name
        for item in viewpoints
    }
    localized = []
    for question in questions:
        impact = question.impact
        for canonical, display_name in sorted(labels.items(), key=lambda item: len(item[0]), reverse=True):
            if canonical != display_name:
                impact = impact.replace(canonical, display_name)
        localized.append(question.model_copy(update={'impact': impact}))
    return localized


def analyze_post(post: Post, demo_mode: bool = False, use_ai: bool = True) -> AnalysisResult:
    analysis_started = time.perf_counter()
    unique = deduplicate_comments(post.comments, demo_mode=demo_mode)
    clean_comments = [
        Comment(id=c.id, author=c.author, text=text, created_at=c.created_at, likes=c.likes)
        for c, text in unique
    ]

    stance_started = time.perf_counter()
    stance_raw: list[dict] = []
    engine_info = ai_status(load=False)
    if use_ai:
        stance_raw, engine_info = classify_stances(post.text, clean_comments)

    if stance_raw:
        viewpoints = build_viewpoints_from_details(stance_raw, len(clean_comments))
    else:
        viewpoints, stance_raw = build_viewpoints_heuristic(clean_comments, post.text)
        engine_info = dict(engine_info)
        engine_info['mode'] = 'heuristic-fallback'
        if use_ai:
            engine_info['message'] = engine_info.get('message') or 'AI kullanılamadı; heuristik yedek kullanıldı.'
        else:
            engine_info['message'] = 'Kullanıcı isteğiyle heuristik motor kullanıldı.'

    stance_details = [StanceDetail(**d) for d in stance_raw]
    engine_info['semantic_guardrail_count'] = sum(
        'anlamsal tutarlılık:' in item.engine for item in stance_details
    )
    stance_profile_elapsed_ms = round((time.perf_counter() - stance_started) * 1000, 3)

    # v1.1.0: İddia Radarı artık yalnızca anahtar sözcük aramaz. Önce yapısal
    # doğrulanabilirlik sinyalleriyle aday çıkarır; gerekli olduğunda mevcut
    # mDeBERTa-XNLI modelini ikinci karar katmanı olarak kullanır.
    claim_started = time.perf_counter()
    claims, claim_info = analyze_claims(post.text, clean_comments, use_ai=use_ai)
    claim_profile_elapsed_ms = round((time.perf_counter() - claim_started) * 1000, 3)

    # v1.2.0: Soru katmanı artık soru işareti araması değildir. Bilgi ve karar
    # soruları, açık kaynak/kanıt talepleri, tekrarlar, yanıt durumu ve retorik
    # ifadeler ayrı değerlendirilir.
    question_started = time.perf_counter()
    unanswered, rhetorical_questions, question_info = analyze_questions(
        clean_comments,
        stance_details,
        claims,
    )
    question_profile_elapsed_ms = round((time.perf_counter() - question_started) * 1000, 3)
    open_questions = [item for item in unanswered if item.answer_status in {'Cevapsız', 'Kısmen cevaplandı'}]

    offensive_count = sum(1 for c in clean_comments if is_offensive(c.text))
    duplicates = max(0, len(post.comments) - len(clean_comments))
    # v1.1.1: Kaynak farkındalığı artık yalnızca iddia kartlarında URL/atıf olup
    # olmadığına göre hesaplanmaz. Kaynak/araştırma/veri/kanıt/ölçüm talep eden
    # yorumlar da sağlıklı kanıt farkındalığı olarak hesaba katılır.
    source_stats = source_awareness_stats(clean_comments)
    source_awareness = source_stats['score']
    constructive = max(0, 100 - round(offensive_count * 100 / max(1, len(clean_comments))))
    repetition_rate = round(duplicates * 100 / max(1, len(post.comments)))

    ground_started = time.perf_counter()
    common_ground_details, ground_info = build_common_ground(
        clean_comments,
        stance_details,
        claims,
        title=post.text,
    )
    ground_profile_elapsed_ms = round((time.perf_counter() - ground_started) * 1000, 3)
    common_ground = [item.text for item in common_ground_details]

    # v1.2.1: canonical name alanı history/Köprü/bildirim kimliği olarak
    # korunur; bağlama uygun etiket ve yorum dayanakları ek alanlarda taşınır.
    viewpoint_started = time.perf_counter()
    viewpoints, viewpoint_info = enrich_viewpoints(
        post.text,
        clean_comments,
        viewpoints,
        stance_details,
        claims,
        unanswered,
        common_ground_details,
    )
    viewpoint_profile_elapsed_ms = round((time.perf_counter() - viewpoint_started) * 1000, 3)

    unanswered = _localize_question_impacts(unanswered, viewpoints)
    rhetorical_questions = _localize_question_impacts(rhetorical_questions, viewpoints)
    method_summary, execution_mode = _stance_execution_description(engine_info, stance_details)
    decision_viewpoints = [
        item for item in viewpoints
        if item.name in {'Destekleyen', 'Karşı / Sınırlayıcı', 'Koşullu / Dengeli'}
    ]
    visible_viewpoints = decision_viewpoints[:3] or viewpoints[:2]
    top = [f'{item.display_name or item.name} (%{item.percentage})' for item in visible_viewpoints]
    summary = (
        f"'{post.text}' başlıklı tartışmada {len(clean_comments)} benzersiz yorum incelendi. "
        f'{method_summary} '
        f"Tartışmadaki karar yaklaşımları {', '.join(top) if top else 'henüz belirgin değil'}. "
        f"Sistem {len(claims)} doğrulanabilir iddia adayı ve {len(open_questions)} açık soru tespit etti."
    )

    bridge_started = time.perf_counter()
    bridge, bridge_info = build_bridge(
        post.text,
        clean_comments,
        stance_details,
        viewpoints,
        common_ground_details,
        claims,
    )
    bridge_profile_elapsed_ms = round((time.perf_counter() - bridge_started) * 1000, 3)

    key_disagreements = [bridge['main_divergence']]
    if claims:
        high_priority = sum(1 for item in claims if item.priority == 'Yüksek')
        if high_priority:
            key_disagreements.append(f'{high_priority} yüksek öncelikli doğrulanabilir iddianın hangi kanıtla destekleneceği.')
        else:
            key_disagreements.append('Doğrulanabilir iddiaların hangi kaynak ve ölçütlerle sınanacağı.')
    if open_questions:
        key_disagreements.append('Cevapsız kalan veri/kaynak sorularının tartışmanın sonucunu nasıl değiştireceği.')

    engine_info = dict(engine_info)
    engine_info['stance_execution_mode'] = execution_mode
    engine_info['stance_transformer_used'] = execution_mode in {'transformer-only', 'hybrid-structural-transformer'}
    engine_info['stance_comment_count'] = len(stance_details)
    engine_info['viewpoint_engine'] = viewpoint_info['mode']
    engine_info['viewpoint_context'] = viewpoint_info['context']
    engine_info['viewpoint_topic_key'] = viewpoint_info['topic_key']
    engine_info['viewpoint_topic_subject'] = viewpoint_info['topic_subject']
    engine_info['viewpoint_topic_specific'] = viewpoint_info['topic_specific']
    engine_info['viewpoint_cluster_count'] = viewpoint_info['cluster_count']
    engine_info['viewpoint_representative_count'] = viewpoint_info['representative_count']
    engine_info['viewpoint_model_comment_count'] = viewpoint_info['model_comment_count']
    engine_info['viewpoint_structural_comment_count'] = viewpoint_info['structural_comment_count']
    engine_info['viewpoint_elapsed_ms'] = viewpoint_info['elapsed_ms']
    engine_info['claim_engine'] = claim_info['mode']
    engine_info['claim_transformer_count'] = claim_info['transformer_count']
    engine_info['claim_transformer_comment_ids'] = claim_info.get('transformer_comment_ids', [])
    engine_info['claim_model_comment_ids'] = claim_info.get('model_comment_ids', [])
    engine_info['claim_cache_hit_count'] = claim_info.get('cache_hit_count', 0)
    engine_info['claim_cache_miss_count'] = claim_info.get('cache_miss_count', 0)
    engine_info['claim_cache_comment_ids'] = claim_info.get('cache_comment_ids', [])
    engine_info['claim_cache_size'] = claim_info.get('cache_size', 0)
    engine_info['claim_elapsed_ms'] = claim_info['elapsed_ms']
    engine_info['common_ground_engine'] = ground_info['mode']
    engine_info['common_ground_elapsed_ms'] = ground_info['elapsed_ms']
    engine_info['bridge_engine'] = bridge_info['mode']
    engine_info['bridge_elapsed_ms'] = bridge_info['elapsed_ms']
    engine_info['bridge_evidence_count'] = bridge_info['evidence_count']
    engine_info['bridge_contrast_strategy'] = bridge_info['contrast_strategy']
    engine_info['bridge_contrast_viewpoint_count'] = bridge_info['contrast_viewpoint_count']
    engine_info['bridge_question_word_count'] = bridge_info.get('question_word_count', len(bridge['bridge_question'].split()))
    engine_info['bridge_question_max_words'] = bridge_info.get('question_max_words', 28)
    engine_info['question_engine'] = question_info['mode']
    engine_info['question_elapsed_ms'] = question_info['elapsed_ms']
    engine_info['question_candidate_count'] = question_info['candidate_count']
    engine_info['question_actionable_count'] = question_info['actionable_count']
    engine_info['question_unanswered_count'] = question_info['unanswered_count']
    engine_info['question_partial_count'] = question_info['partial_count']
    engine_info['question_answered_count'] = question_info['answered_count']
    engine_info['question_rhetorical_count'] = question_info['rhetorical_count']
    engine_info['question_grouped_repeat_count'] = question_info['grouped_repeat_count']
    engine_info['source_awareness_engine'] = 'comment-level-evidence-awareness'
    engine_info['source_awareness_comment_count'] = source_stats['aware_comment_count']
    engine_info['source_provided_count'] = source_stats['provided_source_count']
    engine_info['evidence_request_count'] = source_stats['evidence_request_count']
    engine_info['stage_profile_ms'] = {
        'stance': stance_profile_elapsed_ms,
        'claims': claim_profile_elapsed_ms,
        'questions': question_profile_elapsed_ms,
        'common_ground': ground_profile_elapsed_ms,
        'viewpoints': viewpoint_profile_elapsed_ms,
        'bridge': bridge_profile_elapsed_ms,
    }
    engine_info['total_elapsed_ms'] = round((time.perf_counter() - analysis_started) * 1000)

    return AnalysisResult(
        post_id=post.id,
        short_summary=summary,
        common_ground=common_ground[:3],
        common_ground_details=common_ground_details[:3],
        key_disagreements=key_disagreements[:3],
        viewpoints=viewpoints,
        stance_details=stance_details[:20],
        claims=claims[:8],
        unanswered_questions=unanswered[:8],
        rhetorical_questions=rhetorical_questions[:8],
        indicators={
            'constructive_contribution': constructive,
            'source_awareness': source_awareness,
            'repetition_rate': repetition_rate,
            'offensive_language_rate': 100 - constructive,
            'question_count': len(unanswered),
            'unanswered_question_count': question_info['unanswered_count'],
            'partially_answered_question_count': question_info['partial_count'],
            'answered_question_count': question_info['answered_count'],
            'rhetorical_question_count': question_info['rhetorical_count'],
            'comment_count': len(clean_comments),
            'ai_average_confidence': (
                round(sum(d.confidence for d in stance_details if d.confidence > 0) / max(1, sum(1 for d in stance_details if d.confidence > 0)) * 100)
                if any(d.confidence > 0 for d in stance_details) else 0
            ),
        },
        bridge=bridge,
        changes_since_last_visit=(
            [
                'Bu tartışma için ilk analiz anlık görüntüsü oluşturuldu.',
                f'{len(clean_comments)} benzersiz yorum başlangıç noktası olarak kaydedildi.',
                'Karşılaştırmalı değişim analizi için önceki anlık görüntü kaydı henüz bağlı değil.',
            ]
            if not demo_mode else
            [
                'Demo veri setindeki tekrar yorumlar tekilleştirildi.',
                f'{len(clean_comments)} benzersiz yorum analiz kapsamına alındı.',
                f'{len(claims)} iddia adayı ve {len(open_questions)} açık soru görünür hâle getirildi.',
                'API akışında bu analiz SQLite anlık görüntüsü olarak kaydedilir ve sonraki analiz gerçek değişimlerle karşılaştırılır.',
            ]
        ),
        engine=engine_info,
    )


def analyze_demo(post_id: int = 1, use_ai: bool = True) -> AnalysisResult:
    return analyze_post(DEMO_POST, demo_mode=True, use_ai=use_ai)


def build_custom_post(title: str, comments: list[str]) -> Post:
    comment_models = [
        Comment(
            id=i + 1,
            author=f'Katılımcı {i + 1}',
            text=text.strip(),
            created_at='şimdi',
            likes=0,
        )
        for i, text in enumerate(comments)
        if text.strip()
    ]
    return Post(
        id=9001,
        author='Yeni Tartışma',
        handle='@nkopru_demo',
        text=title.strip(),
        created_at='şimdi',
        comments=comment_models,
    )


def rewrite_constructively(text: str) -> tuple[str, str]:
    clean = text.strip()
    lower = clean.lower()

    if is_offensive(clean):
        if any(token in lower for token in ['bilgin yok', 'bilmiyorsun', 'anlamıyorsun', 'mal beyinli', 'yavşak']):
            suggestion = (
                'Bu görüşün yeterli bilgi veya kanıtla desteklenmediğini düşünüyorum. '
                'Dayandığın bilgi ya da kaynakları paylaşabilir misin?'
            )
        else:
            suggestion = (
                'Bu görüşe katılmıyorum. Gerekçenin yeterince desteklenmediğini düşünüyorum. '
                'Bunu hangi bilgi, örnek veya kaynağa dayandırdığını açıklayabilir misin?'
            )
        reason = (
            'Kişisel saldırı veya hakaret sinyali tespit edildi; ifade, kişiyi hedeflemek yerine '
            'gerekçe ve kanıt üzerinden tartışılabilecek bir biçime dönüştürüldü.'
        )
    elif any(token in lower for token in ['sen bu konudan hiçbir şey anlamıyorsun', 'hiçbir şey bilmiyorsun']):
        suggestion = (
            'Bu görüşe katılmıyorum. Özellikle gerekçenin yeterince desteklenmediğini düşünüyorum. '
            'Bununla ilgili bir kaynak veya veri paylaşabilir misin?'
        )
        reason = 'Kişiye yönelik ifadeyi azaltıp görüş ayrılığını gerekçe ve kaynak talebine dönüştürüyor.'
    else:
        suggestion = clean
        reason = 'Metinde belirgin bir kişisel saldırı tespit edilmedi; özgün ifade korunuyor.'
    return suggestion, reason
