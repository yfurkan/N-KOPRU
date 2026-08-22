from pydantic import BaseModel, Field
from typing import List


class Comment(BaseModel):
    id: int
    author: str
    text: str
    created_at: str
    likes: int = 0


class Post(BaseModel):
    id: int
    author: str
    handle: str
    text: str
    created_at: str
    comments: List[Comment]


class ViewpointEvidence(BaseModel):
    comment_id: int
    author: str = ''
    text: str
    confidence: float = 0.0
    engine: str = ''


class Viewpoint(BaseModel):
    name: str
    percentage: int
    summary: str
    display_name: str = ''
    comment_count: int = 0
    main_argument: str = ''
    evidence_comment_ids: List[int] = Field(default_factory=list)
    representative_comments: List[ViewpointEvidence] = Field(default_factory=list)
    dominant_themes: List[str] = Field(default_factory=list)
    shared_themes: List[str] = Field(default_factory=list)
    opposing_viewpoint_names: List[str] = Field(default_factory=list)
    relationship_note: str = ''
    related_claim_comment_ids: List[int] = Field(default_factory=list)
    related_question_comment_ids: List[int] = Field(default_factory=list)
    structural_comment_count: int = 0
    model_comment_count: int = 0
    average_model_confidence: float = 0.0


class StanceDetail(BaseModel):
    comment_id: int
    text: str
    label: str
    confidence: float
    engine: str


class ClaimItem(BaseModel):
    comment_id: int
    text: str
    source_status: str
    claim_type: str = 'Genel olgusal iddia'
    verification_need: str = ''
    priority: str = 'Orta'
    confidence: float = 0.0
    engine: str = 'Yapısal doğrulanabilirlik analizi'
    detection_reason: str = ''


class CommonGroundItem(BaseModel):
    theme: str
    text: str
    support_count: int = 0
    stance_count: int = 0
    evidence_comment_ids: List[int] = Field(default_factory=list)
    confidence: float = 0.0
    engine: str = 'Görüş kümeleri arası çapraz-tema analizi'


class QuestionItem(BaseModel):
    comment_id: int
    text: str
    question_type: str = 'Bilgi / Açıklama Sorusu'
    answer_status: str = 'Cevapsız'
    priority: str = 'Orta'
    confidence: float = 0.0
    evidence_comment_ids: List[int] = Field(default_factory=list)
    repeated_comment_ids: List[int] = Field(default_factory=list)
    answer_comment_ids: List[int] = Field(default_factory=list)
    affected_viewpoints: List[str] = Field(default_factory=list)
    impact: str = ''
    engine: str = 'Yapısal-semantik soru analizi'
    detection_reason: str = ''
    identity_key: str = ''


class AnalysisResult(BaseModel):
    post_id: int
    short_summary: str
    common_ground: List[str]
    common_ground_details: List[CommonGroundItem] = Field(default_factory=list)
    key_disagreements: List[str]
    viewpoints: List[Viewpoint]
    stance_details: List[StanceDetail] = []
    claims: List[ClaimItem]
    unanswered_questions: List[QuestionItem]
    rhetorical_questions: List[QuestionItem] = Field(default_factory=list)
    indicators: dict
    bridge: dict
    changes_since_last_visit: List[str]
    engine: dict = {}


class RewriteRequest(BaseModel):
    text: str
    context: str = ''
    use_ai: bool = True


class RewriteResponse(BaseModel):
    original: str
    suggestion: str
    reason: str
    engine: str = 'contextual-fallback'
    elapsed_ms: int = 0
    signals: List[str] = []


class DiscussionAnalyzeRequest(BaseModel):
    title: str = Field(min_length=3, max_length=500)
    comments: List[str] = Field(min_length=3, max_length=500)
    use_ai: bool = True


class DiscussionAnalyzeResponse(BaseModel):
    post: Post
    analysis: AnalysisResult


class CommentCreateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1200)
    author: str = Field(default='', max_length=120)
    use_ai: bool = True


class CommentAppendResponse(BaseModel):
    post: Post
    comment: Comment
    analysis: AnalysisResult
    history_id: int
    notifications_created: int = 0


class ExploreTopic(BaseModel):
    id: int
    category: str
    title: str
    summary: str
    badge: str
    tags: List[str] = Field(default_factory=list)
    comment_count: int = 0


class ExploreResponse(BaseModel):
    categories: List[str]
    topics: List[ExploreTopic]


class NotificationItem(BaseModel):
    id: int
    kind: str
    title: str
    text: str
    created_at: str
    relative_time: str
    is_read: bool = False
    post_id: int | None = None
    tab_index: int | None = None
    badge: str = 'Bilgi'
    priority: str = 'normal'


class NotificationResponse(BaseModel):
    total_count: int
    read_count: int
    unread_count: int
    notifications: List[NotificationItem]


class NotificationActionResponse(BaseModel):
    ok: bool
    total_count: int
    read_count: int
    unread_count: int
    notification: NotificationItem | None = None
    changed: int = 0
    deleted_ids: List[int] = Field(default_factory=list)


class NotificationRestoreRequest(BaseModel):
    ids: List[int] = Field(default_factory=list, max_length=200)


class AIStatus(BaseModel):
    installed: bool
    loaded: bool
    model: str
    device: str
    mode: str
    message: str
    error: str | None = None


class MessageAttachment(BaseModel):
    kind: str = 'bridge'
    title: str
    post_id: int | None = None
    tab_index: int | None = 7
    summary: str = ''
    common_acceptance: str = ''
    main_divergence: str = ''
    missing_information: str = ''
    bridge_question: str = ''


class MessageItem(BaseModel):
    id: int
    conversation_id: int
    author: str
    text: str
    created_at: str
    relative_time: str
    is_mine: bool = False
    attachment: MessageAttachment | None = None


class ConversationSummary(BaseModel):
    id: int
    title: str
    subtitle: str
    badge: str = 'Ekip'
    unread_count: int = 0
    last_message: str = ''
    last_time: str = ''


class ConversationListResponse(BaseModel):
    conversations: List[ConversationSummary]


class ConversationDetail(BaseModel):
    conversation: ConversationSummary
    messages: List[MessageItem]


class SendMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class ShareBridgeRequest(BaseModel):
    conversation_id: int = 2
    post_id: int
    title: str = Field(min_length=1, max_length=500)
    summary: str = ''
    common_acceptance: str = ''
    main_divergence: str = ''
    missing_information: str = ''
    bridge_question: str = Field(min_length=1, max_length=3000)


class BookmarkItem(BaseModel):
    id: int
    kind: str
    post_id: int
    title: str
    text: str
    tab_index: int | None = None
    comment_id: int | None = None
    created_at: str
    relative_time: str = 'Şimdi'


class BookmarkCreateRequest(BaseModel):
    kind: str = Field(min_length=3, max_length=32)
    post_id: int
    title: str = Field(min_length=1, max_length=500)
    text: str = Field(min_length=1, max_length=4000)
    tab_index: int | None = None
    comment_id: int | None = None


class BookmarkResponse(BaseModel):
    count: int
    bookmarks: List[BookmarkItem]


class BookmarkActionResponse(BaseModel):
    ok: bool
    created: bool = False
    count: int
    bookmark: BookmarkItem | None = None


class TopicList(BaseModel):
    id: int
    name: str
    description: str = ''
    created_at: str
    relative_time: str = 'Şimdi'
    item_count: int = 0
    discussion_count: int = 0
    claim_count: int = 0
    bridge_count: int = 0


class TopicListEntry(BaseModel):
    id: int
    list_id: int
    kind: str
    post_id: int
    title: str
    text: str
    tab_index: int | None = None
    comment_id: int | None = None
    created_at: str
    relative_time: str = 'Şimdi'


class TopicListCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default='', max_length=500)


class TopicListEntryCreateRequest(BaseModel):
    kind: str = Field(min_length=3, max_length=32)
    post_id: int
    title: str = Field(min_length=1, max_length=500)
    text: str = Field(min_length=1, max_length=4000)
    tab_index: int | None = None
    comment_id: int | None = None


class TopicListResponse(BaseModel):
    count: int
    lists: List[TopicList]


class TopicListDetail(BaseModel):
    list: TopicList
    items: List[TopicListEntry]


class TopicListActionResponse(BaseModel):
    ok: bool
    created: bool = False
    count: int
    list: TopicList | None = None
    item: TopicListEntry | None = None


class AnalysisHistoryItem(BaseModel):
    id: int
    post_id: int
    title: str
    analyzed_at: str
    relative_time: str = 'Şimdi'
    comment_count: int = 0
    viewpoint_count: int = 0
    claim_count: int = 0
    question_count: int = 0
    engine_mode: str = ''
    changed_count: int = 0


class AnalysisHistoryResponse(BaseModel):
    count: int
    analyses: List[AnalysisHistoryItem]


class AnalysisHistoryDetail(BaseModel):
    item: AnalysisHistoryItem
    post: Post
    analysis: AnalysisResult


class ProfileUser(BaseModel):
    display_name: str
    handle: str
    bio: str = ''
    created_at: str
    updated_at: str


class ProfileStats(BaseModel):
    analysis_count: int = 0
    unique_discussions: int = 0
    saved_bridge_count: int = 0
    bookmark_count: int = 0
    list_count: int = 0
    list_item_count: int = 0
    notification_count: int = 0
    sent_message_count: int = 0
    last_analyzed_at: str | None = None


class ProfileResponse(BaseModel):
    user: ProfileUser
    stats: ProfileStats
    recent_analyses: List[AnalysisHistoryItem] = Field(default_factory=list)


class ProfileUpdateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    handle: str = Field(default='@yerel', max_length=80)
    bio: str = Field(default='', max_length=500)


class TechnicalEvaluationRequest(BaseModel):
    iterations: int = Field(default=5, ge=1, le=10)
    use_ai: bool = True


class ScenarioEvaluationRequest(BaseModel):
    use_ai: bool = True
