import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .demo import DEMO_POST
from .explore import categories as explore_categories, get_post as get_explore_post, list_topics as list_explore_topics
from .analyzer import analyze_post, build_custom_post
from .stance_engine import status as stance_status
from .coach_engine import status as coach_status, rewrite_with_ai
from .notifications import delete_notification, delete_read_notifications, list_notifications, mark_all_read, mark_read, mark_unread, notification_counts, record_analysis, restore_notifications
from .messages import get_conversation, list_conversations, send_message, share_bridge
from .bookmarks import count_bookmarks, create_bookmark, delete_bookmark, get_bookmark, list_bookmarks
from .lists import add_entry as add_list_entry, count_lists, create_list, delete_entry as delete_list_entry, delete_list, get_list, list_lists
from .history import allocate_custom_post_id, append_post_comment, get_custom_post, get_history, history_count, list_history, record_analysis_snapshot, save_custom_post
from .profile import get_profile, update_profile
from .evaluation import get_technical_status, run_holdout_evaluation, run_scenario_evaluation, run_technical_evaluation
from .pilot import export_csv as export_pilot_csv, get_overview as get_pilot_overview, get_session as get_pilot_session, start_session as start_pilot_session, submit_phase as submit_pilot_phase
from .readiness import get_system_readiness
from .version import APP_VERSION
from .models import (
    AnalysisResult,
    Post,
    RewriteRequest,
    RewriteResponse,
    DiscussionAnalyzeRequest,
    DiscussionAnalyzeResponse,
    CommentCreateRequest,
    CommentAppendResponse,
    AIStatus,
    ExploreResponse,
    NotificationResponse,
    NotificationActionResponse,
    NotificationRestoreRequest,
    ConversationListResponse,
    ConversationDetail,
    MessageItem,
    SendMessageRequest,
    ShareBridgeRequest,
    BookmarkCreateRequest,
    BookmarkResponse,
    BookmarkActionResponse,
    TopicListCreateRequest,
    TopicListEntryCreateRequest,
    TopicListResponse,
    TopicListDetail,
    TopicListActionResponse,
    AnalysisHistoryResponse,
    AnalysisHistoryDetail,
    ProfileResponse,
    ProfileUpdateRequest,
    TechnicalEvaluationRequest,
    ScenarioEvaluationRequest,
    SystemReadinessResponse,
    PilotOverviewResponse,
    PilotSessionStartRequest,
    PilotSessionResponse,
    PilotPhaseSubmitRequest,
    PilotPhaseSubmitResponse,
)

app = FastAPI(
    title='N-KÖPRÜ API',
    version=APP_VERSION,
    description='Yapay Zekâ Destekli Sosyal Tartışma Zekâsı Sistemi — hibrit AI yerel çalışma API’si',
)

_default_origins = 'http://localhost:3000,http://127.0.0.1:3000'
_cors_origins = [item.strip() for item in os.getenv('N_KOPRU_CORS_ORIGINS', _default_origins).split(',') if item.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health')
def health():
    return {'status': 'ok', 'project': 'N-KÖPRÜ', 'version': APP_VERSION, 'storage': 'sqlite'}


@app.get('/api/system/readiness', response_model=SystemReadinessResponse)
def system_readiness():
    return get_system_readiness()


@app.get('/api/pilot', response_model=PilotOverviewResponse)
def pilot_overview():
    return get_pilot_overview()


@app.post('/api/pilot/sessions', response_model=PilotSessionResponse)
def pilot_session_start(req: PilotSessionStartRequest):
    try:
        return start_pilot_session(consent=req.consent, practice=req.practice)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get('/api/pilot/sessions/{session_id}', response_model=PilotSessionResponse)
def pilot_session_get(session_id: int):
    session = get_pilot_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail='Pilot oturumu bulunamadı')
    return session


@app.post('/api/pilot/sessions/{session_id}/phases', response_model=PilotPhaseSubmitResponse)
def pilot_phase_submit(session_id: int, req: PilotPhaseSubmitRequest):
    try:
        return submit_pilot_phase(
            session_id,
            phase_index=req.phase_index,
            selected_answer=req.selected_answer,
            duration_ms=req.duration_ms,
            clarity_rating=req.clarity_rating,
            confidence_rating=req.confidence_rating,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc).strip("'")) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get('/api/pilot/results.csv')
def pilot_results_csv():
    return Response(
        content=export_pilot_csv(),
        media_type='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename="nkopru-pilot-results.csv"'},
    )


@app.get('/api/ai/status', response_model=AIStatus)
def ai_status():
    return stance_status(load=False)


@app.post('/api/ai/load', response_model=AIStatus)
def ai_load():
    return stance_status(load=True)

@app.get('/api/coach/status', response_model=AIStatus)
def get_coach_status():
    return coach_status(load=False)


@app.post('/api/coach/load', response_model=AIStatus)
def load_coach_model():
    return coach_status(load=True)


@app.get('/api/evaluation')
def technical_evaluation_status():
    return get_technical_status()


@app.post('/api/evaluation/run')
def technical_evaluation_run(req: TechnicalEvaluationRequest):
    try:
        return run_technical_evaluation(iterations=req.iterations, use_ai=req.use_ai)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post('/api/evaluation/scenarios/run')
def technical_scenario_evaluation_run(req: ScenarioEvaluationRequest):
    return run_scenario_evaluation(use_ai=req.use_ai)


@app.post('/api/evaluation/holdout/run')
def technical_holdout_evaluation_run(req: ScenarioEvaluationRequest):
    try:
        return run_holdout_evaluation(use_ai=req.use_ai)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc



@app.get('/api/posts/demo', response_model=Post)
def get_demo_post():
    return get_custom_post(DEMO_POST.id) or DEMO_POST


def _resolve_post(post_id: int) -> Post | None:
    persisted = get_custom_post(post_id)
    if persisted is not None:
        return persisted
    if post_id == DEMO_POST.id:
        return DEMO_POST
    return get_explore_post(post_id)


@app.get('/api/posts/{post_id}', response_model=Post)
def get_post(post_id: int):
    post = _resolve_post(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail='Gönderi bulunamadı')
    return post


@app.get('/api/explore', response_model=ExploreResponse)
def explore(category: str | None = Query(default=None), q: str | None = Query(default=None)):
    return ExploreResponse(categories=explore_categories(), topics=list_explore_topics(category=category, q=q))


@app.get('/api/explore/{topic_id}', response_model=Post)
def explore_post(topic_id: int):
    base_post = get_explore_post(topic_id)
    if base_post is None:
        raise HTTPException(status_code=404, detail='Keşfet tartışması bulunamadı')
    return get_custom_post(topic_id) or base_post


@app.get('/api/analyze/{post_id}', response_model=AnalysisResult)
def analyze(post_id: int, use_ai: bool = Query(default=True)):
    post = _resolve_post(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail='Gönderi bulunamadı')
    result = analyze_post(post, demo_mode=post.id == DEMO_POST.id, use_ai=use_ai)
    result, history_id = record_analysis_snapshot(post, result)
    record_analysis(post, result, history_id=history_id)
    return result


@app.post('/api/analyze-discussion', response_model=DiscussionAnalyzeResponse)
def analyze_discussion(req: DiscussionAnalyzeRequest):
    post = build_custom_post(req.title, req.comments).model_copy(update={'id': allocate_custom_post_id()})
    if len(post.comments) < 3:
        raise HTTPException(status_code=400, detail='En az 3 dolu yorum gerekli')
    save_custom_post(post)
    analysis = analyze_post(post, demo_mode=False, use_ai=req.use_ai)
    analysis, history_id = record_analysis_snapshot(post, analysis)
    record_analysis(post, analysis, history_id=history_id)
    return DiscussionAnalyzeResponse(post=post, analysis=analysis)


@app.post('/api/posts/{post_id}/comments', response_model=CommentAppendResponse)
def add_post_comment(post_id: int, req: CommentCreateRequest):
    base_post = _resolve_post(post_id)
    if base_post is None:
        raise HTTPException(status_code=404, detail='Yorum eklenecek tartışma bulunamadı')

    clean_text = ' '.join(req.text.strip().split())
    if not clean_text:
        raise HTTPException(status_code=400, detail='Yorum metni boş olamaz')

    author = ' '.join(req.author.strip().split())
    if not author:
        author = get_profile().user.display_name

    try:
        updated_post, comment = append_post_comment(base_post, clean_text, author)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    analysis = analyze_post(
        updated_post,
        demo_mode=updated_post.id == DEMO_POST.id,
        use_ai=req.use_ai,
    )
    analysis, history_id = record_analysis_snapshot(updated_post, analysis)
    notifications_created = record_analysis(updated_post, analysis, history_id=history_id)
    return CommentAppendResponse(
        post=updated_post,
        comment=comment,
        analysis=analysis,
        history_id=history_id,
        notifications_created=notifications_created,
    )


@app.get('/api/notifications', response_model=NotificationResponse)
def notifications(
    status: str = Query(default='all'),
    unread_only: bool = Query(default=False),
):
    # unread_only eski istemcilerle geriye dönük uyumluluk için korunur.
    if unread_only:
        status = 'unread'
    if status not in {'all', 'unread', 'read'}:
        raise HTTPException(status_code=400, detail='Geçersiz bildirim filtresi')
    total, read, unread = notification_counts()
    return NotificationResponse(total_count=total, read_count=read, unread_count=unread, notifications=list_notifications(status=status))


def _notification_action(*, notification=None, changed: int = 0, deleted_ids: list[int] | None = None):
    total, read, unread = notification_counts()
    return NotificationActionResponse(
        ok=True,
        total_count=total,
        read_count=read,
        unread_count=unread,
        notification=notification,
        changed=changed,
        deleted_ids=deleted_ids or [],
    )


@app.post('/api/notifications/{notification_id}/read', response_model=NotificationActionResponse)
def notification_read(notification_id: int):
    item = mark_read(notification_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Bildirim bulunamadı')
    return _notification_action(notification=item)


@app.post('/api/notifications/{notification_id}/unread', response_model=NotificationActionResponse)
def notification_unread(notification_id: int):
    item = mark_unread(notification_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Bildirim bulunamadı')
    return _notification_action(notification=item)


@app.post('/api/notifications/read-all', response_model=NotificationActionResponse)
def notifications_read_all():
    changed = mark_all_read()
    return _notification_action(changed=changed)


@app.delete('/api/notifications/read', response_model=NotificationActionResponse)
def notifications_delete_read():
    deleted_ids = delete_read_notifications()
    return _notification_action(changed=len(deleted_ids), deleted_ids=deleted_ids)


@app.delete('/api/notifications/{notification_id}', response_model=NotificationActionResponse)
def notifications_delete_one(notification_id: int):
    item = delete_notification(notification_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Bildirim bulunamadı')
    return _notification_action(notification=item, changed=1, deleted_ids=[notification_id])


@app.post('/api/notifications/restore', response_model=NotificationActionResponse)
def notifications_restore(req: NotificationRestoreRequest):
    restored = restore_notifications(req.ids)
    return _notification_action(changed=restored)


@app.get('/api/messages', response_model=ConversationListResponse)
def messages_list():
    return ConversationListResponse(conversations=list_conversations())


@app.get('/api/messages/{conversation_id}', response_model=ConversationDetail)
def messages_detail(conversation_id: int):
    detail = get_conversation(conversation_id, mark_read=True)
    if detail is None:
        raise HTTPException(status_code=404, detail='Konuşma bulunamadı')
    return detail


@app.post('/api/messages/{conversation_id}', response_model=MessageItem)
def messages_send(conversation_id: int, req: SendMessageRequest):
    item = send_message(conversation_id, req.text)
    if item is None:
        raise HTTPException(status_code=404, detail='Konuşma bulunamadı')
    return item


@app.post('/api/messages/bridge/share', response_model=MessageItem)
def messages_share_bridge(req: ShareBridgeRequest):
    item = share_bridge(
        req.conversation_id,
        post_id=req.post_id,
        title=req.title,
        summary=req.summary,
        common_acceptance=req.common_acceptance,
        main_divergence=req.main_divergence,
        missing_information=req.missing_information,
        bridge_question=req.bridge_question,
    )
    if item is None:
        raise HTTPException(status_code=404, detail='Konuşma bulunamadı')
    return item


@app.get('/api/bookmarks', response_model=BookmarkResponse)
def bookmarks_list(kind: str | None = Query(default=None)):
    if kind not in (None, 'all', 'discussion', 'claim', 'bridge'):
        raise HTTPException(status_code=400, detail='Geçersiz yer imi filtresi')
    return BookmarkResponse(count=count_bookmarks(), bookmarks=list_bookmarks(kind=kind))


@app.post('/api/bookmarks', response_model=BookmarkActionResponse)
def bookmarks_create(req: BookmarkCreateRequest):
    try:
        item, created = create_bookmark(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return BookmarkActionResponse(ok=True, created=created, count=count_bookmarks(), bookmark=item)


@app.delete('/api/bookmarks/{bookmark_id}', response_model=BookmarkActionResponse)
def bookmarks_delete(bookmark_id: int):
    item = delete_bookmark(bookmark_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Yer imi bulunamadı')
    return BookmarkActionResponse(ok=True, created=False, count=count_bookmarks(), bookmark=item)


@app.get('/api/bookmarks/{bookmark_id}', response_model=BookmarkActionResponse)
def bookmarks_detail(bookmark_id: int):
    item = get_bookmark(bookmark_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Yer imi bulunamadı')
    return BookmarkActionResponse(ok=True, created=False, count=count_bookmarks(), bookmark=item)


@app.get('/api/lists', response_model=TopicListResponse)
def topic_lists():
    return TopicListResponse(count=count_lists(), lists=list_lists())


@app.post('/api/lists', response_model=TopicListActionResponse)
def topic_lists_create(req: TopicListCreateRequest):
    try:
        item, created = create_list(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TopicListActionResponse(ok=True, created=created, count=count_lists(), list=item)


@app.get('/api/lists/{list_id}', response_model=TopicListDetail)
def topic_lists_detail(list_id: int):
    detail = get_list(list_id)
    if detail is None:
        raise HTTPException(status_code=404, detail='Liste bulunamadı')
    return detail


@app.delete('/api/lists/{list_id}', response_model=TopicListActionResponse)
def topic_lists_delete(list_id: int):
    item = delete_list(list_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Liste bulunamadı')
    return TopicListActionResponse(ok=True, created=False, count=count_lists(), list=item)


@app.post('/api/lists/{list_id}/items', response_model=TopicListActionResponse)
def topic_lists_add_item(list_id: int, req: TopicListEntryCreateRequest):
    try:
        item, created = add_list_entry(list_id, req)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='Liste bulunamadı') from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    detail = get_list(list_id)
    return TopicListActionResponse(ok=True, created=created, count=detail.list.item_count if detail else 0, list=detail.list if detail else None, item=item)


@app.delete('/api/lists/{list_id}/items/{item_id}', response_model=TopicListActionResponse)
def topic_lists_delete_item(list_id: int, item_id: int):
    detail = get_list(list_id)
    if detail is None:
        raise HTTPException(status_code=404, detail='Liste bulunamadı')
    item = delete_list_entry(list_id, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Liste öğesi bulunamadı')
    updated = get_list(list_id)
    return TopicListActionResponse(ok=True, created=False, count=updated.list.item_count if updated else 0, list=updated.list if updated else None, item=item)


@app.get('/api/history', response_model=AnalysisHistoryResponse)
def analysis_history(limit: int = Query(default=30, ge=1, le=200), post_id: int | None = Query(default=None)):
    rows = list_history(limit=limit, post_id=post_id)
    return AnalysisHistoryResponse(count=history_count(post_id=post_id), analyses=rows)


@app.get('/api/history/{history_id}', response_model=AnalysisHistoryDetail)
def analysis_history_detail(history_id: int):
    detail = get_history(history_id)
    if detail is None:
        raise HTTPException(status_code=404, detail='Analiz geçmişi kaydı bulunamadı')
    return detail


@app.get('/api/profile', response_model=ProfileResponse)
def profile_get():
    return get_profile()


@app.put('/api/profile', response_model=ProfileResponse)
def profile_update(req: ProfileUpdateRequest):
    try:
        return update_profile(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post('/api/rewrite', response_model=RewriteResponse)
def rewrite(req: RewriteRequest):
    result = rewrite_with_ai(req.text, context=req.context, use_ai=req.use_ai)
    return RewriteResponse(original=req.text, **result)
