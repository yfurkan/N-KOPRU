'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { addTopicListItem, analyzeDiscussion, analyzePost, appendComment, clearReadNotifications, createBookmark, createTopicList, deleteBookmark, deleteNotification, deleteTopicList, deleteTopicListItem, getAIStatus, getAnalysisHistoryDetail, getBookmarks, getCoachStatus, getConversation, getConversations, getDemoPost, getExplorePost, getExploreTopics, getNotifications, getPostById, getProfile, getTechnicalStatus, getTopicList, getTopicLists, loadAIModel, loadCoachModel, markAllNotificationsRead, markNotificationRead, markNotificationUnread, restoreNotifications, rewriteComment, runScenarioEvaluation, runTechnicalEvaluation, sendConversationMessage, shareBridgeToConversation, updateProfile } from '../lib/api';
import type { AIStatus, Analysis, AnalysisHistoryDetail, AnalysisHistoryItem, BookmarkItem, BookmarkKind, ConversationDetail, ConversationSummary, ExploreTopic, NotificationItem, Post, ProfileResponse, RewriteResult, TechnicalEvaluation, TechnicalScenarioEvaluation, TechnicalStatus, TopicList, TopicListDetail, TopicListEntry } from '../lib/types';

type NavPage = 'Ana Sayfa' | 'Keşfet' | 'Bildirimler' | 'Mesajlar' | 'Yer İmleri' | 'Listeler' | 'Profil' | 'Teknik Doğrulama';

const navItems: NavPage[] = ['Ana Sayfa','Keşfet','Bildirimler','Mesajlar','Yer İmleri','Listeler','Profil','Teknik Doğrulama'];

const tabs = [
  'Tartışmayı Anla', 'Ortak Zemin', 'Görüş Haritası', 'İddia Radarı',
  'Cevapsız Sorular', 'Yanıt Koçu', 'Ben Yokken Ne Değişti?', 'Köprü Oluştur',
];

const customExample = `Kesinlikle yasaklanmalı, öğrenciler düşünmeyi bırakıyor.
Tamamen yasaklamak yanlış; doğru kullanıldığında faydalı olabilir.
Bence kontrollü kullanım ve açık kurallar gerekli.
Geçen dönem sınıfımızın %70'i üretken yapay zekâ kullandı.
Bu %70 oranının kaynağı nedir?
Akademik çalışmalarda kullanılan yapay zekâ açıkça belirtilmeli.
Ben karşıyım, ödevlerin tamamını yapay zekâya yaptırmak ciddi sorun.
Hangi kullanım biçimlerinin öğrenmeyi gerçekten güçlendirdiğini gösteren bir araştırma var mı?`;

export default function Home() {
  const [post, setPost] = useState<Post | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [active, setActive] = useState(0);
  const [draft, setDraft] = useState('Sen bu konudan hiçbir şey anlamıyorsun.');
  const [rewrite, setRewrite] = useState<RewriteResult | null>(null);
  const [rewriteLoading, setRewriteLoading] = useState(false);
  const [coachStatus, setCoachStatus] = useState<AIStatus | null>(null);
  const [coachLoading, setCoachLoading] = useState(false);
  const [customOpen, setCustomOpen] = useState(false);
  const [customTitle, setCustomTitle] = useState('Üniversitelerde yapay zekâ kullanımı nasıl düzenlenmeli?');
  const [customComments, setCustomComments] = useState(customExample);
  const [message, setMessage] = useState('');
  const [aiStatus, setAIStatus] = useState<AIStatus | null>(null);
  const [aiLoading, setAILoading] = useState(false);
  const [useAI, setUseAI] = useState(true);
  const [navPage, setNavPage] = useState<NavPage>('Ana Sayfa');
  const [showAllComments, setShowAllComments] = useState(false);
  const [liveComment, setLiveComment] = useState('');
  const [commentSubmitting, setCommentSubmitting] = useState(false);
  const [commentFeedback, setCommentFeedback] = useState('');
  const [latestLiveComment, setLatestLiveComment] = useState<Post['comments'][number] | null>(null);
  const [explorePreviewTopic, setExplorePreviewTopic] = useState<ExploreTopic | null>(null);
  const [explorePreviewPost, setExplorePreviewPost] = useState<Post | null>(null);
  const [explorePreviewLoading, setExplorePreviewLoading] = useState(false);
  const [explorePreviewError, setExplorePreviewError] = useState('');
  const explorePreviewRequestId = useRef(0);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [notificationTotalCount, setNotificationTotalCount] = useState(0);
  const [notificationReadCount, setNotificationReadCount] = useState(0);
  const [notificationUnreadCount, setNotificationUnreadCount] = useState(0);
  const [notificationLoading, setNotificationLoading] = useState(false);
  const [notificationError, setNotificationError] = useState('');
  const [notificationFilter, setNotificationFilter] = useState<'Tümü'|'Okunmamış'|'Okunanlar'>('Tümü');
  const [selectedNotification, setSelectedNotification] = useState<NotificationItem | null>(null);
  const [notificationOpening, setNotificationOpening] = useState(false);
  const [notificationUndo, setNotificationUndo] = useState<{ids:number[]; label:string} | null>(null);
  const notificationUndoTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [conversationDetail, setConversationDetail] = useState<ConversationDetail | null>(null);
  const [conversationLoading, setConversationLoading] = useState(false);
  const [conversationSending, setConversationSending] = useState(false);
  const [conversationError, setConversationError] = useState('');
  const [conversationDraft, setConversationDraft] = useState('');
  const [bridgeShareFeedback, setBridgeShareFeedback] = useState('');
  const [messageBridgeOpening, setMessageBridgeOpening] = useState(false);
  const [bookmarks, setBookmarks] = useState<BookmarkItem[]>([]);
  const [bookmarkCount, setBookmarkCount] = useState(0);
  const [bookmarkFilter, setBookmarkFilter] = useState<BookmarkKind | 'all'>('all');
  const [bookmarkLoading, setBookmarkLoading] = useState(false);
  const [bookmarkError, setBookmarkError] = useState('');
  const [bookmarkSavingKey, setBookmarkSavingKey] = useState('');
  const [selectedBookmarkId, setSelectedBookmarkId] = useState<number | null>(null);
  const [bookmarkOpening, setBookmarkOpening] = useState(false);
  const [topicLists, setTopicLists] = useState<TopicList[]>([]);
  const [topicListCount, setTopicListCount] = useState(0);
  const [selectedTopicListId, setSelectedTopicListId] = useState<number | null>(null);
  const [topicListDetail, setTopicListDetail] = useState<TopicListDetail | null>(null);
  const [topicListLoading, setTopicListLoading] = useState(false);
  const [topicListError, setTopicListError] = useState('');
  const [topicListSavingKey, setTopicListSavingKey] = useState('');
  const [topicListOpening, setTopicListOpening] = useState(false);
  const [topicListSourceLoading, setTopicListSourceLoading] = useState(false);
  const [topicListSourceError, setTopicListSourceError] = useState('');
  const topicListSourceBusyRef = useRef(false);
  const [profileData, setProfileData] = useState<ProfileResponse | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileError, setProfileError] = useState('');
  const [selectedHistoryId, setSelectedHistoryId] = useState<number | null>(null);
  const [historyDetail, setHistoryDetail] = useState<AnalysisHistoryDetail | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyOpening, setHistoryOpening] = useState(false);
  const [technicalStatus, setTechnicalStatus] = useState<TechnicalStatus | null>(null);
  const [technicalResult, setTechnicalResult] = useState<TechnicalEvaluation | null>(null);
  const [technicalScenarioResult, setTechnicalScenarioResult] = useState<TechnicalScenarioEvaluation | null>(null);
  const [technicalLoading, setTechnicalLoading] = useState(false);
  const [technicalRunning, setTechnicalRunning] = useState(false);
  const [technicalScenarioRunning, setTechnicalScenarioRunning] = useState(false);
  const [technicalError, setTechnicalError] = useState('');

  useEffect(() => { loadDemo(); getAIStatus().then(setAIStatus).catch(() => null); getCoachStatus().then(setCoachStatus).catch(() => null); refreshNotifications('Tümü').catch(() => null); getConversations().then(data => { setConversations(data.conversations); setSelectedConversationId(data.conversations[0]?.id ?? null); }).catch(() => null); refreshBookmarks('all').catch(() => null); refreshTopicLists(null).catch(() => null); }, []);
  useEffect(() => {
    setLiveComment('');
    setCommentFeedback('');
    setLatestLiveComment(null);
  }, [post?.id]);

  const displayedComments = useMemo(() => showAllComments ? (post?.comments ?? []) : (post?.comments.slice(0, 12) ?? []), [post, showAllComments]);
  const totalElapsedMs = analysis && typeof analysis.engine.total_elapsed_ms === 'number' ? analysis.engine.total_elapsed_ms : 0;
  const stanceElapsedMs = analysis && typeof analysis.engine.elapsed_ms === 'number' ? analysis.engine.elapsed_ms : 0;
  const transformerCount = analysis && typeof analysis.engine.transformer_count === 'number' ? analysis.engine.transformer_count : 0;
  const ruleCount = analysis && typeof analysis.engine.rule_count === 'number' ? analysis.engine.rule_count : 0;
  const semanticGuardrailCount = analysis && typeof analysis.engine.semantic_guardrail_count === 'number' ? analysis.engine.semantic_guardrail_count : 0;
  const claimTransformerCount = analysis && typeof analysis.engine.claim_transformer_count === 'number' ? analysis.engine.claim_transformer_count : 0;
  const claimCacheHitCount = analysis && typeof analysis.engine.claim_cache_hit_count === 'number' ? analysis.engine.claim_cache_hit_count : 0;
  const claimElapsedMs = analysis && typeof analysis.engine.claim_elapsed_ms === 'number' ? analysis.engine.claim_elapsed_ms : 0;
  const groundElapsedMs = analysis && typeof analysis.engine.common_ground_elapsed_ms === 'number' ? analysis.engine.common_ground_elapsed_ms : 0;
  const bridgeElapsedMs = analysis && typeof analysis.engine.bridge_elapsed_ms === 'number' ? analysis.engine.bridge_elapsed_ms : 0;
  const questionElapsedMs = analysis && typeof analysis.engine.question_elapsed_ms === 'number' ? analysis.engine.question_elapsed_ms : 0;
  const viewpointElapsedMs = analysis && typeof analysis.engine.viewpoint_elapsed_ms === 'number' ? analysis.engine.viewpoint_elapsed_ms : 0;
  const viewpointModelCommentCount = analysis && typeof analysis.engine.viewpoint_model_comment_count === 'number' ? analysis.engine.viewpoint_model_comment_count : transformerCount;
  const questionActionableCount = analysis && typeof analysis.engine.question_actionable_count === 'number' ? analysis.engine.question_actionable_count : (analysis?.unanswered_questions.length ?? 0);
  const questionUnansweredCount = analysis && typeof analysis.engine.question_unanswered_count === 'number' ? analysis.engine.question_unanswered_count : (analysis?.unanswered_questions.filter(item => item.answer_status === 'Cevapsız').length ?? 0);
  const questionPartialCount = analysis && typeof analysis.engine.question_partial_count === 'number' ? analysis.engine.question_partial_count : (analysis?.unanswered_questions.filter(item => item.answer_status === 'Kısmen cevaplandı').length ?? 0);
  const questionAnsweredCount = analysis && typeof analysis.engine.question_answered_count === 'number' ? analysis.engine.question_answered_count : (analysis?.unanswered_questions.filter(item => item.answer_status === 'Cevaplandı').length ?? 0);
  const questionRhetoricalCount = analysis && typeof analysis.engine.question_rhetorical_count === 'number' ? analysis.engine.question_rhetorical_count : (analysis?.rhetorical_questions?.length ?? 0);
  const questionGroupedRepeatCount = analysis && typeof analysis.engine.question_grouped_repeat_count === 'number' ? analysis.engine.question_grouped_repeat_count : 0;
  const sourceAwarenessCommentCount = analysis && typeof analysis.engine.source_awareness_comment_count === 'number' ? analysis.engine.source_awareness_comment_count : 0;
  const evidenceRequestCount = analysis && typeof analysis.engine.evidence_request_count === 'number' ? analysis.engine.evidence_request_count : 0;
  const conversationUnreadCount = useMemo(() => conversations.reduce((sum, item) => sum + item.unread_count, 0), [conversations]);
  const viewpointLabelMap = useMemo(() => Object.fromEntries((analysis?.viewpoints ?? []).map(item => [item.name, item.display_name || item.name])), [analysis]);
  const visibleBookmarks = useMemo(() => bookmarkFilter === 'all' ? bookmarks : bookmarks.filter(item => item.kind === bookmarkFilter), [bookmarks, bookmarkFilter]);
  const selectedBookmark = useMemo(() => visibleBookmarks.find(item => item.id === selectedBookmarkId) ?? visibleBookmarks[0] ?? null, [visibleBookmarks, selectedBookmarkId]);
  const discussionBookmark = useMemo(() => post ? bookmarks.find(item => item.kind === 'discussion' && item.post_id === post.id) ?? null : null, [bookmarks, post]);
  const bridgeBookmark = useMemo(() => post && analysis ? bookmarks.find(item => item.kind === 'bridge' && item.post_id === post.id && item.text === analysis.bridge.bridge_question) ?? null : null, [bookmarks, post, analysis]);

  async function refreshBookmarks(kind: BookmarkKind | 'all' = bookmarkFilter) {
    setBookmarkLoading(true);
    setBookmarkError('');
    try {
      const data = await getBookmarks('all');
      setBookmarks(data.bookmarks);
      setBookmarkCount(data.count);
      const visible = kind === 'all' ? data.bookmarks : data.bookmarks.filter(item => item.kind === kind);
      setSelectedBookmarkId(current => current && visible.some(item => item.id === current) ? current : (visible[0]?.id ?? null));
    } catch (e) {
      setBookmarkError(e instanceof Error ? e.message : 'Yer imleri yüklenemedi');
    } finally {
      setBookmarkLoading(false);
    }
  }

  async function setBookmarkMode(kind: BookmarkKind | 'all') {
    setBookmarkFilter(kind);
    await refreshBookmarks(kind);
  }

  async function saveBookmark(payload:{kind:BookmarkKind; post_id:number; title:string; text:string; tab_index?:number|null; comment_id?:number|null}, key:string) {
    if (bookmarkSavingKey) return;
    setBookmarkSavingKey(key);
    setBookmarkError('');
    try {
      const result = await createBookmark(payload);
      setBookmarkCount(result.count);
      const data = await getBookmarks('all');
      setBookmarks(data.bookmarks);
      if (result.bookmark && (bookmarkFilter === 'all' || bookmarkFilter === result.bookmark.kind)) setSelectedBookmarkId(result.bookmark.id);
    } catch (e) {
      setBookmarkError(e instanceof Error ? e.message : 'Yer imi kaydedilemedi');
    } finally {
      setBookmarkSavingKey('');
    }
  }

  async function removeBookmark(bookmarkId:number, key='remove') {
    if (bookmarkSavingKey) return;
    setBookmarkSavingKey(key);
    setBookmarkError('');
    try {
      const result = await deleteBookmark(bookmarkId);
      setBookmarkCount(result.count);
      const data = await getBookmarks('all');
      setBookmarks(data.bookmarks);
      setSelectedBookmarkId(current => current === bookmarkId ? (data.bookmarks[0]?.id ?? null) : current);
    } catch (e) {
      setBookmarkError(e instanceof Error ? e.message : 'Yer imi kaldırılamadı');
    } finally {
      setBookmarkSavingKey('');
    }
  }

  async function toggleDiscussionBookmark() {
    if (!post) return;
    if (discussionBookmark) {
      await removeBookmark(discussionBookmark.id, `discussion-${post.id}`);
      return;
    }
    await saveBookmark({kind:'discussion', post_id:post.id, title:post.text, text:`${post.comments.length} yorum içeren tartışma`, tab_index:0}, `discussion-${post.id}`);
  }

  async function toggleClaimBookmark(commentId:number, text:string) {
    if (!post) return;
    const current = bookmarks.find(item => item.kind === 'claim' && item.post_id === post.id && item.comment_id === commentId);
    if (current) {
      await removeBookmark(current.id, `claim-${commentId}`);
      return;
    }
    await saveBookmark({kind:'claim', post_id:post.id, title:`${post.text} • İddia #${commentId}`, text, tab_index:3, comment_id:commentId}, `claim-${commentId}`);
  }

  async function toggleBridgeBookmark() {
    if (!post || !analysis?.bridge.bridge_question) return;
    if (bridgeBookmark) {
      await removeBookmark(bridgeBookmark.id, `bridge-${post.id}`);
      return;
    }
    await saveBookmark({kind:'bridge', post_id:post.id, title:`${post.text} • Köprü Sorusu`, text:analysis.bridge.bridge_question, tab_index:7}, `bridge-${post.id}`);
  }

  async function openBookmarkTarget(item:BookmarkItem) {
    if (bookmarkOpening) return;
    setBookmarkOpening(true);
    setBookmarkError('');
    setMessage('');
    try {
      const alreadyOpen = post?.id === item.post_id && analysis?.post_id === item.post_id;
      if (!alreadyOpen) {
        const [targetPost, targetAnalysis] = await Promise.all([getPostById(item.post_id), analyzePost(item.post_id, useAI)]);
        setPost(targetPost);
        setAnalysis(targetAnalysis);
      }
      setActive(Math.max(0, Math.min(7, item.tab_index ?? 0)));
      setRewrite(null);
      setCustomOpen(false);
      setShowAllComments(false);
      setNavPage('Ana Sayfa');
      refreshNotifications('Tümü').catch(() => null);
    } catch (e) {
      setBookmarkError(e instanceof Error ? e.message : 'Kaydedilen içerik açılamadı');
    } finally {
      setBookmarkOpening(false);
    }
  }

  async function ensureTopicListSourceAnalysis() {
    if (!post) return;
    if (analysis?.post_id === post.id) {
      setTopicListSourceError('');
      return;
    }
    if (topicListSourceBusyRef.current) return;

    topicListSourceBusyRef.current = true;
    setTopicListSourceLoading(true);
    setTopicListSourceError('');
    try {
      const result = await analyzePost(post.id, useAI);
      setAnalysis(result);
      refreshNotifications('Tümü').catch(() => null);
    } catch (e) {
      setTopicListSourceError(e instanceof Error ? e.message : 'İddia ve Köprü verileri hazırlanamadı');
    } finally {
      topicListSourceBusyRef.current = false;
      setTopicListSourceLoading(false);
    }
  }

  async function refreshTopicLists(preferredId: number | null = selectedTopicListId) {
    setTopicListLoading(true);
    setTopicListError('');
    try {
      const data = await getTopicLists();
      setTopicLists(data.lists);
      setTopicListCount(data.count);
      const targetId = preferredId && data.lists.some(item => item.id === preferredId)
        ? preferredId
        : (data.lists[0]?.id ?? null);
      setSelectedTopicListId(targetId);
      if (targetId != null) {
        const detail = await getTopicList(targetId);
        setTopicListDetail(detail);
      } else {
        setTopicListDetail(null);
      }
    } catch (e) {
      setTopicListError(e instanceof Error ? e.message : 'Listeler yüklenemedi');
    } finally {
      setTopicListLoading(false);
    }
  }

  async function selectTopicList(item: TopicList) {
    setSelectedTopicListId(item.id);
    setTopicListLoading(true);
    setTopicListError('');
    try {
      setTopicListDetail(await getTopicList(item.id));
    } catch (e) {
      setTopicListError(e instanceof Error ? e.message : 'Liste ayrıntısı yüklenemedi');
    } finally {
      setTopicListLoading(false);
    }
  }

  async function createUserTopicList(name: string, description: string) {
    if (topicListSavingKey || !name.trim()) return;
    setTopicListSavingKey('create-list');
    setTopicListError('');
    try {
      const result = await createTopicList({name:name.trim(), description:description.trim()});
      const targetId = result.list?.id ?? null;
      await refreshTopicLists(targetId);
    } catch (e) {
      setTopicListError(e instanceof Error ? e.message : 'Liste oluşturulamadı');
    } finally {
      setTopicListSavingKey('');
    }
  }

  async function removeUserTopicList(listId: number) {
    if (topicListSavingKey) return;
    setTopicListSavingKey(`delete-list-${listId}`);
    setTopicListError('');
    try {
      await deleteTopicList(listId);
      await refreshTopicLists(null);
    } catch (e) {
      setTopicListError(e instanceof Error ? e.message : 'Liste silinemedi');
    } finally {
      setTopicListSavingKey('');
    }
  }

  async function addCurrentToTopicList(payload:{kind:BookmarkKind; post_id:number; title:string; text:string; tab_index?:number|null; comment_id?:number|null}, key:string) {
    if (!selectedTopicListId || topicListSavingKey) return;
    setTopicListSavingKey(key);
    setTopicListError('');
    try {
      await addTopicListItem(selectedTopicListId, payload);
      const detail = await getTopicList(selectedTopicListId);
      setTopicListDetail(detail);
      const data = await getTopicLists();
      setTopicLists(data.lists);
      setTopicListCount(data.count);
    } catch (e) {
      setTopicListError(e instanceof Error ? e.message : 'İçerik listeye eklenemedi');
    } finally {
      setTopicListSavingKey('');
    }
  }

  async function removeTopicListEntry(listId:number, itemId:number) {
    if (topicListSavingKey) return;
    setTopicListSavingKey(`remove-item-${itemId}`);
    setTopicListError('');
    try {
      await deleteTopicListItem(listId, itemId);
      setTopicListDetail(await getTopicList(listId));
      const data = await getTopicLists();
      setTopicLists(data.lists);
      setTopicListCount(data.count);
    } catch (e) {
      setTopicListError(e instanceof Error ? e.message : 'Liste öğesi çıkarılamadı');
    } finally {
      setTopicListSavingKey('');
    }
  }

  async function openTopicListEntry(item:TopicListEntry) {
    if (topicListOpening) return;
    setTopicListOpening(true);
    setTopicListError('');
    try {
      const alreadyOpen = post?.id === item.post_id && analysis?.post_id === item.post_id;
      if (!alreadyOpen) {
        const [targetPost, targetAnalysis] = await Promise.all([getPostById(item.post_id), analyzePost(item.post_id, useAI)]);
        setPost(targetPost);
        setAnalysis(targetAnalysis);
      }
      setActive(Math.max(0, Math.min(7, item.tab_index ?? 0)));
      setRewrite(null);
      setCustomOpen(false);
      setShowAllComments(false);
      setNavPage('Ana Sayfa');
    } catch (e) {
      setTopicListError(e instanceof Error ? e.message : 'Liste öğesinin analizi açılamadı');
    } finally {
      setTopicListOpening(false);
    }
  }

  function notificationStatus(mode:'Tümü'|'Okunmamış'|'Okunanlar' = notificationFilter) {
    return mode === 'Okunmamış' ? 'unread' as const : mode === 'Okunanlar' ? 'read' as const : 'all' as const;
  }

  function applyNotificationCounts(data:{total_count:number; read_count:number; unread_count:number}) {
    setNotificationTotalCount(data.total_count);
    setNotificationReadCount(data.read_count);
    setNotificationUnreadCount(data.unread_count);
  }

  async function refreshNotifications(mode:'Tümü'|'Okunmamış'|'Okunanlar' = notificationFilter) {
    setNotificationLoading(true);
    setNotificationError('');
    try {
      const data = await getNotifications(notificationStatus(mode));
      setNotifications(data.notifications);
      applyNotificationCounts(data);
      setSelectedNotification(current => {
        if (current && data.notifications.some(item => item.id === current.id)) {
          return data.notifications.find(item => item.id === current.id) ?? null;
        }
        return data.notifications[0] ?? null;
      });
    } catch (e) {
      setNotificationError(e instanceof Error ? e.message : 'Bildirimler yüklenemedi');
    } finally {
      setNotificationLoading(false);
    }
  }

  async function setNotificationMode(mode:'Tümü'|'Okunmamış'|'Okunanlar') {
    setNotificationFilter(mode);
    await refreshNotifications(mode);
  }

  async function selectNotification(item:NotificationItem) {
    setSelectedNotification(item);
    if (item.is_read) return;
    try {
      await markNotificationRead(item.id);
      await refreshNotifications(notificationFilter);
    } catch (e) {
      setNotificationError(e instanceof Error ? e.message : 'Bildirim güncellenemedi');
    }
  }

  function armNotificationUndo(ids:number[], label:string) {
    if (notificationUndoTimer.current) clearTimeout(notificationUndoTimer.current);
    setNotificationUndo({ids, label});
    notificationUndoTimer.current = setTimeout(() => setNotificationUndo(null), 5000);
  }

  async function toggleNotificationReadState(item:NotificationItem) {
    setNotificationError('');
    try {
      if (item.is_read) await markNotificationUnread(item.id);
      else await markNotificationRead(item.id);
      await refreshNotifications(notificationFilter);
    } catch (e) {
      setNotificationError(e instanceof Error ? e.message : 'Bildirim durumu güncellenemedi');
    }
  }

  async function removeNotification(item:NotificationItem) {
    setNotificationError('');
    try {
      const result = await deleteNotification(item.id);
      applyNotificationCounts(result);
      armNotificationUndo(result.deleted_ids, 'Bildirim silindi.');
      await refreshNotifications(notificationFilter);
    } catch (e) {
      setNotificationError(e instanceof Error ? e.message : 'Bildirim silinemedi');
    }
  }

  async function clearReadNotificationItems() {
    if (notificationReadCount === 0) return;
    setNotificationError('');
    try {
      const result = await clearReadNotifications();
      applyNotificationCounts(result);
      if (result.deleted_ids.length) armNotificationUndo(result.deleted_ids, `${result.deleted_ids.length} okunan bildirim temizlendi.`);
      await refreshNotifications(notificationFilter);
    } catch (e) {
      setNotificationError(e instanceof Error ? e.message : 'Okunan bildirimler temizlenemedi');
    }
  }

  async function undoNotificationDelete() {
    if (!notificationUndo?.ids.length) return;
    const ids = notificationUndo.ids;
    if (notificationUndoTimer.current) clearTimeout(notificationUndoTimer.current);
    setNotificationUndo(null);
    setNotificationError('');
    try {
      await restoreNotifications(ids);
      await refreshNotifications(notificationFilter);
    } catch (e) {
      setNotificationError(e instanceof Error ? e.message : 'Bildirim geri alınamadı');
    }
  }

  async function refreshConversations(preferredId: number | null = selectedConversationId) {
    setConversationLoading(true);
    setConversationError('');
    try {
      const data = await getConversations();
      setConversations(data.conversations);
      const targetId = preferredId && data.conversations.some(item => item.id === preferredId)
        ? preferredId
        : (data.conversations[0]?.id ?? null);
      setSelectedConversationId(targetId);
      if (targetId != null) {
        const detail = await getConversation(targetId);
        setConversationDetail(detail);
        setConversations(rows => rows.map(item => item.id === targetId ? {...item, unread_count:0} : item));
      } else {
        setConversationDetail(null);
      }
    } catch (e) {
      setConversationError(e instanceof Error ? e.message : 'Mesajlar yüklenemedi');
    } finally {
      setConversationLoading(false);
    }
  }

  async function openConversation(conversationId: number) {
    setSelectedConversationId(conversationId);
    setConversationLoading(true);
    setConversationError('');
    try {
      const detail = await getConversation(conversationId);
      setConversationDetail(detail);
      setConversations(rows => rows.map(item => item.id === conversationId ? {...item, unread_count:0} : item));
    } catch (e) {
      setConversationError(e instanceof Error ? e.message : 'Konuşma açılamadı');
    } finally {
      setConversationLoading(false);
    }
  }

  async function sendMessageToConversation() {
    const conversationId = conversationDetail?.conversation.id ?? selectedConversationId;
    const clean = conversationDraft.trim();
    if (conversationId == null || !clean) return;
    setConversationSending(true);
    setConversationError('');
    try {
      await sendConversationMessage(conversationId, clean);
      setConversationDraft('');
      const detail = await getConversation(conversationId);
      setConversationDetail(detail);
      const list = await getConversations();
      setConversations(list.conversations.map(item => item.id === conversationId ? {...item, unread_count:0} : item));
    } catch (e) {
      setConversationError(e instanceof Error ? e.message : 'Mesaj gönderilemedi');
    } finally {
      setConversationSending(false);
    }
  }

  async function openBridgeFromMessages(postId:number, tabIndex:number | null) {
    if (messageBridgeOpening) return;
    const targetTab = Math.max(0, Math.min(7, tabIndex ?? 7));
    setConversationError('');
    setMessage('');
    setMessageBridgeOpening(true);

    try {
      // Köprü kartı mevcut açık tartışmaya aitse yeniden API/AI çağrısı yapma.
      // Bu, Mesajlar -> Köprü Oluştur geçişini tek tıkta anlık hâle getirir.
      if (post?.id === postId && analysis) {
        setActive(targetTab);
        setRewrite(null);
        setCustomOpen(false);
        setShowAllComments(false);
        setNavPage('Ana Sayfa');
        refreshNotifications('Tümü').catch(() => null);
        return;
      }

      // Farklı bir tartışma kartı açılıyorsa ilk tıkta kullanıcıya durum göster;
      // aynı isteğin art arda birkaç kez başlatılmasını engelle.
      setLoading(true);
      const [loadedPost, loadedAnalysis] = await Promise.all([
        getPostById(postId),
        analyzePost(postId, useAI),
      ]);
      setPost(loadedPost);
      setAnalysis(loadedAnalysis);
      setActive(targetTab);
      setRewrite(null);
      setCustomOpen(false);
      setShowAllComments(false);
      setNavPage('Ana Sayfa');
      refreshNotifications('Tümü').catch(() => null);
    } catch (e) {
      setConversationError(e instanceof Error ? e.message : 'Paylaşılan tartışma açılamadı');
    } finally {
      setLoading(false);
      setMessageBridgeOpening(false);
    }
  }

  async function shareCurrentBridgeToMessages() {
    if (!post || !analysis?.bridge.bridge_question) {
      setMessage('Önce bir tartışmayı analiz edip Köprü kartını oluştur.');
      return;
    }
    setBridgeShareFeedback('Köprü kartı Mesajlar bölümüne aktarılıyor…');
    try {
      await shareBridgeToConversation({
        conversation_id: 2,
        post_id: post.id,
        title: post.text,
        summary: analysis.short_summary,
        common_acceptance: analysis.bridge.common_acceptance,
        main_divergence: analysis.bridge.main_divergence,
        missing_information: analysis.bridge.missing_information,
        bridge_question: analysis.bridge.bridge_question,
      });
      setNavPage('Mesajlar');
      setCustomOpen(false);
      setBridgeShareFeedback('Köprü kartı Ekip görüşmesine eklendi.');
      await refreshConversations(2);
    } catch (e) {
      const error = e instanceof Error ? e.message : 'Köprü kartı paylaşılamadı';
      setBridgeShareFeedback(error);
      setMessage(error);
    }
  }

  async function readAllNotifications() {
    try {
      const result = await markAllNotificationsRead();
      applyNotificationCounts(result);
      await refreshNotifications(notificationFilter);
    } catch (e) {
      setNotificationError(e instanceof Error ? e.message : 'Bildirimler güncellenemedi');
    }
  }

  async function openNotificationTarget(item:NotificationItem) {
    if (item.post_id == null || item.tab_index == null || notificationOpening) return;
    setNotificationOpening(true);
    setMessage('');
    try {
      if (!item.is_read) await markNotificationRead(item.id).catch(() => null);
      const alreadyOpen = post?.id === item.post_id && analysis?.post_id === item.post_id;
      if (!alreadyOpen) {
        const [targetPost, targetAnalysis] = await Promise.all([
          getPostById(item.post_id),
          analyzePost(item.post_id, useAI),
        ]);
        setPost(targetPost);
        setAnalysis(targetAnalysis);
      }
      setActive(Math.max(0, Math.min(7, item.tab_index)));
      setRewrite(null);
      setCustomOpen(false);
      setShowAllComments(false);
      setNavPage('Ana Sayfa');
      refreshNotifications('Tümü').catch(() => null);
    } catch (e) {
      setNotificationError(e instanceof Error ? e.message : 'Bildirim hedefi açılamadı');
    } finally { setNotificationOpening(false); }
  }

  async function loadDemo() {
    setMessage('');
    const demo = await getDemoPost();
    setPost(demo);
    setAnalysis(null);
    setCustomOpen(false);
    setNavPage('Ana Sayfa');
    setRewrite(null);
    setShowAllComments(false);
  }

  async function runAnalysis() {
    if (!post) return;
    setLoading(true); setMessage('');
    try {
      const result = await analyzePost(post.id, useAI);
      setAnalysis(result); setActive(0); refreshNotifications('Tümü').catch(() => null);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Analiz hatası');
    } finally { setLoading(false); }
  }

  async function addLiveComment() {
    const clean = liveComment.trim();
    if (!post || !clean || commentSubmitting) return;
    setCommentSubmitting(true);
    setCommentFeedback('');
    setMessage('');
    try {
      const result = await appendComment(post.id, clean, useAI);
      setPost(result.post);
      setAnalysis(result.analysis);
      setLatestLiveComment(result.comment);
      setLiveComment('');
      setActive(6);
      const notificationNote = result.notifications_created > 0
        ? ` ${result.notifications_created} ilgili bildirim üretildi.`
        : ' Yeni bir bildirim gerektiren ek değişiklik oluşmadı.';
      setCommentFeedback(`#${result.comment.id} numaralı yorum kaydedildi ve yeni anlık görüntü oluşturuldu.${notificationNote}`);
      refreshNotifications('Tümü').catch(() => null);
    } catch (e) {
      setCommentFeedback(e instanceof Error ? e.message : 'Yorum eklenemedi');
    } finally {
      setCommentSubmitting(false);
    }
  }

  async function runCustomAnalysis() {
    const comments = customComments.split('\n').map(x => x.trim()).filter(Boolean);
    if (comments.length < 3) {
      setMessage('En az 3 yorumu ayrı satırlara yaz.');
      return;
    }
    setLoading(true); setMessage('');
    try {
      const result = await analyzeDiscussion(customTitle, comments, useAI);
      setPost(result.post);
      setAnalysis(result.analysis);
      setActive(0);
      setCustomOpen(false);
      setShowAllComments(false);
      refreshNotifications('Tümü').catch(() => null);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Yeni tartışma analiz edilemedi');
    } finally { setLoading(false); }
  }


  async function openExploreTopic(topicId: number, analyzeNow = false) {
    setLoading(true); setMessage('');
    try {
      if (analyzeNow) {
        const [nextPost, result] = await Promise.all([getExplorePost(topicId), analyzePost(topicId, useAI)]);
        setPost(nextPost);
        setAnalysis(result);
        refreshNotifications('Tümü').catch(() => null);
      } else {
        const nextPost = await getExplorePost(topicId);
        setPost(nextPost);
        setAnalysis(null);
      }
      setActive(0);
      setRewrite(null);
      setCustomOpen(false);
      setShowAllComments(false);
      setNavPage('Ana Sayfa');
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Keşfet tartışması açılamadı');
    } finally { setLoading(false); }
  }

  const previewExploreTopic = useCallback(async (topic: ExploreTopic) => {
    const requestId = ++explorePreviewRequestId.current;
    setExplorePreviewTopic(topic);
    setExplorePreviewPost(null);
    setExplorePreviewError('');
    setExplorePreviewLoading(true);
    try {
      const nextPost = await getExplorePost(topic.id);
      if (requestId === explorePreviewRequestId.current) setExplorePreviewPost(nextPost);
    } catch (e) {
      if (requestId === explorePreviewRequestId.current) {
        setExplorePreviewError(e instanceof Error ? e.message : 'Tartışma önizlemesi yüklenemedi');
      }
    } finally {
      if (requestId === explorePreviewRequestId.current) setExplorePreviewLoading(false);
    }
  }, []);

  const clearExplorePreview = useCallback(() => {
    explorePreviewRequestId.current += 1;
    setExplorePreviewTopic(null);
    setExplorePreviewPost(null);
    setExplorePreviewError('');
    setExplorePreviewLoading(false);
  }, []);


  async function refreshProfile(selectHistory = true) {
    setProfileLoading(true);
    setProfileError('');
    try {
      const data = await getProfile();
      setProfileData(data);
      if (selectHistory) {
        const targetId = selectedHistoryId && data.recent_analyses.some(item => item.id === selectedHistoryId)
          ? selectedHistoryId
          : (data.recent_analyses[0]?.id ?? null);
        setSelectedHistoryId(targetId);
        if (targetId) await loadHistoryDetail(targetId);
        else setHistoryDetail(null);
      }
    } catch (e) {
      setProfileError(e instanceof Error ? e.message : 'Profil yüklenemedi');
    } finally {
      setProfileLoading(false);
    }
  }

  async function refreshTechnicalStatus() {
    setTechnicalLoading(true);
    setTechnicalError('');
    try {
      const result = await getTechnicalStatus();
      setTechnicalStatus(result);
      setTechnicalResult(result.latest_result);
      setTechnicalScenarioResult(result.latest_scenario_result);
    } catch (e) {
      setTechnicalError(e instanceof Error ? e.message : 'Teknik doğrulama yüklenemedi');
    } finally {
      setTechnicalLoading(false);
    }
  }

  async function startTechnicalEvaluation() {
    if (technicalRunning || technicalScenarioRunning) return;
    setTechnicalRunning(true);
    setTechnicalError('');
    try {
      const result = await runTechnicalEvaluation(5, useAI);
      setTechnicalResult(result);
      setTechnicalStatus(current => current ? {
        ...current,
        latest_result: result,
        model_status: result.model_status,
      } : null);
    } catch (e) {
      setTechnicalError(e instanceof Error ? e.message : 'Teknik doğrulama tamamlanamadı');
    } finally {
      setTechnicalRunning(false);
    }
  }

  async function startScenarioEvaluation() {
    if (technicalRunning || technicalScenarioRunning) return;
    setTechnicalScenarioRunning(true);
    setTechnicalError('');
    try {
      const result = await runScenarioEvaluation(useAI);
      setTechnicalScenarioResult(result);
      setTechnicalStatus(current => current ? {
        ...current,
        latest_scenario_result: result,
        model_status: result.model_status,
      } : null);
    } catch (e) {
      setTechnicalError(e instanceof Error ? e.message : 'Çok senaryolu doğrulama tamamlanamadı');
    } finally {
      setTechnicalScenarioRunning(false);
    }
  }

  async function loadHistoryDetail(historyId:number) {
    setSelectedHistoryId(historyId);
    setHistoryLoading(true);
    setProfileError('');
    try {
      const detail = await getAnalysisHistoryDetail(historyId);
      setHistoryDetail(detail);
    } catch (e) {
      setProfileError(e instanceof Error ? e.message : 'Analiz geçmişi kaydı yüklenemedi');
    } finally {
      setHistoryLoading(false);
    }
  }

  async function saveProfile(payload:{display_name:string;handle:string;bio:string}) {
    if (profileSaving) return;
    setProfileSaving(true);
    setProfileError('');
    try {
      const data = await updateProfile(payload);
      setProfileData(data);
    } catch (e) {
      setProfileError(e instanceof Error ? e.message : 'Profil güncellenemedi');
    } finally {
      setProfileSaving(false);
    }
  }

  async function openHistorySnapshot(item:AnalysisHistoryItem) {
    if (historyOpening) return;
    setHistoryOpening(true);
    setProfileError('');
    try {
      const detail = historyDetail?.item.id === item.id ? historyDetail : await getAnalysisHistoryDetail(item.id);
      setHistoryDetail(detail);
      setSelectedHistoryId(item.id);
      setPost(detail.post);
      setAnalysis(detail.analysis);
      setActive(0);
      setNavPage('Ana Sayfa');
      setShowAllComments(false);
      refreshNotifications('Tümü').catch(() => null);
      refreshBookmarks('all').catch(() => null);
    } catch (e) {
      setProfileError(e instanceof Error ? e.message : 'Geçmiş analiz açılamadı');
    } finally {
      setHistoryOpening(false);
    }
  }

  async function prepareAI() {
    setAILoading(true); setMessage('');
    try {
      const stance = await loadAIModel();
      setAIStatus(stance);
      if (!stance.loaded) setMessage(stance.error || stance.message);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'AI modeli hazırlanamadı');
    } finally { setAILoading(false); }
  }

  async function prepareCoach() {
    setCoachLoading(true); setMessage('');
    try {
      const status = await loadCoachModel();
      setCoachStatus(status);
      if (!status.loaded) setMessage(status.error || status.message);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Yanıt Koçu modeli hazırlanamadı');
    } finally { setCoachLoading(false); }
  }

  async function runRewrite() {
    if (!draft.trim()) return;
    setRewriteLoading(true); setMessage('');
    try {
      const result = await rewriteComment(draft, post?.text ?? '', useAI);
      setRewrite(result);
      if (useAI) getCoachStatus().then(setCoachStatus).catch(() => null);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Yanıt Koçu çalıştırılamadı');
    } finally { setRewriteLoading(false); }
  }

  return (
    <main className='appShell'>
      <aside className='sidebar'>
        <div className='brand'>
          <div className='logo'>🌉</div>
          <div><strong>N-KÖPRÜ</strong><span>Farklı düşün. Daha iyi konuş.</span></div>
        </div>
        <nav>
          {navItems.map(x => (
            <button
              key={x}
              className={navPage === x ? 'navActive' : ''}
              onClick={() => { setNavPage(x); setCustomOpen(false); if (x === 'Bildirimler') refreshNotifications(notificationFilter).catch(() => null); if (x === 'Mesajlar') refreshConversations().catch(() => null); if (x === 'Yer İmleri') refreshBookmarks(bookmarkFilter).catch(() => null); if (x === 'Listeler') { refreshTopicLists(selectedTopicListId).catch(() => null); ensureTopicListSourceAnalysis().catch(() => null); } if (x === 'Profil') refreshProfile(true).catch(() => null); if (x === 'Teknik Doğrulama') refreshTechnicalStatus().catch(() => null); }}
            >
              <span>{x}</span>{x === 'Bildirimler' && notificationUnreadCount > 0 && <em className='navCount'>{notificationUnreadCount > 99 ? '99+' : notificationUnreadCount}</em>}{x === 'Mesajlar' && conversationUnreadCount > 0 && <em className='navCount'>{conversationUnreadCount > 99 ? '99+' : conversationUnreadCount}</em>}{x === 'Yer İmleri' && bookmarkCount > 0 && <em className='navCount'>{bookmarkCount > 99 ? '99+' : bookmarkCount}</em>}{x === 'Listeler' && topicListCount > 0 && <em className='navCount'>{topicListCount > 99 ? '99+' : topicListCount}</em>}
            </button>
          ))}
        </nav>
        <div className='goalBox'>
          <b>HEDEFİMİZ</b>
          <p>Konuşmaları susturmak değil, anlayışı ve nitelikli etkileşimi büyütmek.</p>
        </div>
      </aside>

      <section className='feed'>
        <header className='topbar'>
          <div className='topBrand'><span className='eyebrow'>NSosyal demo</span><h1>N-KÖPRÜ</h1></div>
          {navPage === 'Ana Sayfa' ? (
            <div className='topActions'>
              <button className={`aiButton ${aiStatus?.loaded ? 'aiReady' : ''}`} onClick={prepareAI} disabled={aiLoading} title={aiStatus?.message ?? 'AI model durumu'}>
                {aiLoading ? 'AI hazırlanıyor…' : aiStatus?.loaded ? '● AI Hazır' : '◇ AI Modelini Hazırla'}
              </button>
              <label className='aiToggle' title='Kapalıyken heuristik yedek motor kullanılır'>
                <input type='checkbox' checked={useAI} onChange={e => setUseAI(e.target.checked)} />
                <span>Gerçek AI</span>
              </label>
              <button className='ghost' onClick={loadDemo}>Örneğe Dön</button>
              <button className='primary noMargin' onClick={() => setCustomOpen(v => !v)}>＋ Yeni Tartışma</button>
            </div>
          ) : (
            <button className='ghost' onClick={() => setNavPage('Ana Sayfa')}>← Ana Sayfaya Dön</button>
          )}
        </header>

        {navPage === 'Ana Sayfa' ? (
          <>
                    {customOpen && (
                      <div className='customCard'>
                        <div className='customHeader'>
                          <div><span className='eyebrow'>N-KÖPRÜ • HİBRİT AI GİRDİSİ</span><h3>Yeni Tartışma Analiz Et</h3></div>
                          <button className='closeButton' onClick={() => setCustomOpen(false)}>×</button>
                        </div>
                        <label className='fieldLabel'>Gönderi / tartışma başlığı</label>
                        <input className='textInput' value={customTitle} onChange={e => setCustomTitle(e.target.value)} />
                        <label className='fieldLabel spaced'>Yorumlar — her satıra bir yorum</label>
                        <textarea className='commentsInput' value={customComments} onChange={e => setCustomComments(e.target.value)} />
                        <div className='customFooter'>
                          <span>{customComments.split('\n').filter(x => x.trim()).length} yorum</span>
                          <button className='primary noMargin' onClick={runCustomAnalysis} disabled={loading}>
                            {loading ? 'Analiz ediliyor…' : '✨ Bu Tartışmayı Analiz Et'}
                          </button>
                        </div>
                      </div>
                    )}

                    {message && <div className='errorBox'>{message}</div>}

                    {!post ? <div className='card'>Gönderi yükleniyor…</div> : (
                      <article className='postCard'>
                        <div className='postMeta'>
                          <div className='avatar'>{post.author.slice(0,2).toUpperCase()}</div>
                          <div><b>{post.author}</b> <span>{post.handle} · {post.created_at}</span></div>
                        </div>
                        <h2>{post.text}</h2>
                        <div className='engagement'><span>💬 {post.comments.length}</span><span>↻ 83</span><span>♡ 342</span></div>
                        <div className='postActionRow'>
                          <button className='primary' onClick={analysis ? () => setActive(0) : runAnalysis} disabled={loading}>
                            {loading ? 'Analiz ediliyor…' : analysis ? '✓ N-KÖPRÜ Analizi Hazır' : '✨ N-KÖPRÜ ile Tartışmayı Anla'}
                          </button>
                          <button className={`ghost bookmarkToggle ${discussionBookmark ? 'bookmarkSaved' : ''}`} onClick={() => void toggleDiscussionBookmark()} disabled={bookmarkSavingKey === `discussion-${post.id}`}>
                            {bookmarkSavingKey === `discussion-${post.id}` ? 'Kaydediliyor…' : discussionBookmark ? '★ Kaydedildi' : '☆ Tartışmayı Kaydet'}
                          </button>
                        </div>

                        <div className='liveCommentComposer'>
                          <div className='liveCommentHeading'>
                            <div><b>Tartışmaya yeni yorum ekle</b><span>Yorum SQLite’a kaydedilir; analiz ve değişim anlık görüntüsü otomatik güncellenir.</span></div>
                            <span className='liveBadge'>CANLI</span>
                          </div>
                          <textarea
                            value={liveComment}
                            onChange={e => setLiveComment(e.target.value)}
                            placeholder='Tartışmaya katkını yaz…'
                            maxLength={1200}
                            disabled={commentSubmitting}
                          />
                          <div className='liveCommentFooter'>
                            <small>{liveComment.length}/1200</small>
                            <button className='primary noMargin' onClick={() => void addLiveComment()} disabled={commentSubmitting || !liveComment.trim()}>
                              {commentSubmitting ? 'Yorum ekleniyor ve analiz güncelleniyor…' : '＋ Yorumu Ekle ve Analizi Güncelle'}
                            </button>
                          </div>
                          {commentFeedback && <div className={`liveCommentFeedback ${commentFeedback.includes('kaydedildi') ? 'success' : 'failure'}`}>{commentFeedback}</div>}
                          {latestLiveComment && <div className='latestLiveComment'><div><b>Son eklenen yorum · #{latestLiveComment.id}</b><span>{latestLiveComment.author}</span></div><p>{latestLiveComment.text}</p></div>}
                        </div>

                        <div className='comments'>
                          {displayedComments.map(c => (
                            <div className='comment' key={c.id}>
                              <div className='avatar small'>{c.author.split(' ').map(s => s[0]).join('').slice(0,2)}</div>
                              <div><b>{c.author}</b> <span>· {c.created_at}</span><p>{c.text}</p><small>♡ {c.likes}</small></div>
                            </div>
                          ))}
                          {post.comments.length > 12 && (
                            <button className='ghost' onClick={() => setShowAllComments(v => !v)}>
                              {showAllComments ? 'Yorumları daralt' : `Diğer yorumları gör (${post.comments.length - 12})`}
                            </button>
                          )}
                        </div>
                      </article>
                    )}

          </>
        ) : navPage === 'Keşfet' ? (
          <ExploreWorkspace
            onOpenTopic={openExploreTopic}
            onPreviewTopic={previewExploreTopic}
            onClearPreview={clearExplorePreview}
            selectedTopicId={explorePreviewTopic?.id ?? null}
          />
        ) : navPage === 'Bildirimler' ? (
          <NotificationWorkspace
            notifications={notifications}
            totalCount={notificationTotalCount}
            readCount={notificationReadCount}
            unreadCount={notificationUnreadCount}
            loading={notificationLoading}
            error={notificationError}
            filter={notificationFilter}
            selectedId={selectedNotification?.id ?? null}
            undo={notificationUndo}
            onFilter={setNotificationMode}
            onRefresh={() => refreshNotifications(notificationFilter)}
            onSelect={selectNotification}
            onToggleRead={toggleNotificationReadState}
            onDelete={removeNotification}
            onReadAll={readAllNotifications}
            onClearRead={clearReadNotificationItems}
            onUndo={undoNotificationDelete}
          />
        ) : navPage === 'Mesajlar' ? (
          <MessageWorkspace
            conversations={conversations}
            selectedId={selectedConversationId}
            loading={conversationLoading}
            error={conversationError}
            onSelect={openConversation}
            onRefresh={() => refreshConversations(selectedConversationId)}
          />
        ) : navPage === 'Yer İmleri' ? (
          <BookmarkWorkspace
            bookmarks={visibleBookmarks}
            totalCount={bookmarkCount}
            filter={bookmarkFilter}
            selectedId={selectedBookmark?.id ?? null}
            loading={bookmarkLoading}
            error={bookmarkError}
            savingKey={bookmarkSavingKey}
            onFilter={setBookmarkMode}
            onRefresh={() => refreshBookmarks(bookmarkFilter)}
            onSelect={item => setSelectedBookmarkId(item.id)}
            onOpen={openBookmarkTarget}
            onRemove={removeBookmark}
          />
        ) : navPage === 'Listeler' ? (
          <ListWorkspace
            lists={topicLists}
            selectedId={selectedTopicListId}
            loading={topicListLoading}
            error={topicListError}
            savingKey={topicListSavingKey}
            onSelect={selectTopicList}
            onRefresh={() => refreshTopicLists(selectedTopicListId)}
            onCreate={createUserTopicList}
            onDelete={removeUserTopicList}
          />
        ) : navPage === 'Profil' ? (
          <ProfileWorkspace
            profile={profileData}
            loading={profileLoading}
            saving={profileSaving}
            error={profileError}
            selectedHistoryId={selectedHistoryId}
            opening={historyOpening}
            onRefresh={() => refreshProfile(true)}
            onSelectHistory={loadHistoryDetail}
            onOpenHistory={openHistorySnapshot}
            onSave={saveProfile}
          />
        ) : navPage === 'Teknik Doğrulama' ? (
          <TechnicalWorkspace
            status={technicalStatus}
            result={technicalResult}
            scenarioResult={technicalScenarioResult}
            currentPost={post}
            currentAnalysis={analysis}
            loading={technicalLoading}
            running={technicalRunning}
            scenarioRunning={technicalScenarioRunning}
            error={technicalError}
            onRefresh={refreshTechnicalStatus}
            onRun={startTechnicalEvaluation}
            onRunScenarios={startScenarioEvaluation}
          />
        ) : (
          <NavWorkspace page={navPage} onOpenHome={() => setNavPage('Ana Sayfa')} />
        )}
      </section>

      <section className='analysisPanel'>
        {navPage === 'Ana Sayfa' ? (
          <>
                    <div className='panelHeader'>
                      <div><span className='eyebrow'>N-KÖPRÜ ANALİZİ</span><h2>{analysis ? 'Tartışma Haritası Hazır' : 'Analiz bekleniyor'}</h2></div>
                      {analysis && <span className='status good'>● Canlı</span>}
                    </div>

                    {!analysis ? (
                      <div className='emptyState'>
                        <div className='bigIcon'>{loading ? '⟳' : '🧠'}</div>
                        <h3>{loading ? 'Tartışma analiz ediliyor' : 'Tartışmayı anlaşılır hâle getir'}</h3>
                        <p>{loading ? 'Görüş, iddia ve soru katmanları çıkarılıyor…' : 'Demo gönderisini analiz et veya “Yeni Tartışma” ile kendi yorumlarını gir.'}</p>
                      </div>
                    ) : (
                      <>
                        <div className='analysisBadges'>
                          <span>{analysis.indicators.comment_count} benzersiz yorum</span>
                          <span>{analysis.viewpoints.length} görüş kümesi</span>
                          <span>{analysis.claims.length} iddia adayı</span>
                          <span>{questionUnansweredCount + questionPartialCount} açık soru</span>
                          <span className={['transformer-zero-shot','hybrid-transformer'].includes(analysis.engine.mode) ? 'realAIChip' : 'fallbackChip'}>
                            {['transformer-zero-shot','hybrid-transformer'].includes(analysis.engine.mode) ? 'AI • Hibrit' : 'Yedek • Heuristik'}
                          </span>
                          {totalElapsedMs > 0 && <span className='timingChip'>⏱ {formatDuration(totalElapsedMs)}</span>}
                        </div>
                        <div className='tabStrip'>
                          {tabs.map((tab,i) => <button key={tab} className={active === i ? 'activeTab' : ''} onClick={() => setActive(i)} title={tab}>{i+1}<small>{tab}</small></button>)}
                        </div>

                        <div className='moduleCard'>
                          <div className='moduleTitle'><span>{active+1}</span><h3>{tabs[active]}</h3></div>

                          {active === 0 && <>
                            <p className='lead'>{analysis.short_summary}</p>
                            <h4>Temel görüş ayrılıkları</h4>
                            <ul>{analysis.key_disagreements.map(x => <li key={x}>{x}</li>)}</ul>
                            <div className='metricGrid'>
                              <Metric label='Yorum' value={analysis.indicators.comment_count} />
                              <Metric label='Yapıcı katkı*' value={`%${analysis.indicators.constructive_contribution}`} />
                              <Metric label='Kaynak farkındalığı*' value={`%${analysis.indicators.source_awareness}`} />
                              <Metric label='Tekrar oranı*' value={`%${analysis.indicators.repetition_rate}`} />
                            </div>
                            <p className='metricDefinition'>* Kaynak farkındalığı; kaynak, araştırma, veri, kanıt, istatistik veya ölçüm ihtiyacını açıkça gündeme getiren benzersiz yorumların oranıdır. Kaynak talebi de farkındalık sayılır.{sourceAwarenessCommentCount > 0 ? ` Bu analizde ${sourceAwarenessCommentCount} yorum sinyali` : ''}{evidenceRequestCount > 0 ? ` ve ${evidenceRequestCount} açık kaynak/veri talebi` : ''}{sourceAwarenessCommentCount > 0 ? ' tespit edildi.' : ''}</p>
                            <p className='prototypeWarning'>Analiz çekirdeği: <b>{['transformer-zero-shot','hybrid-transformer'].includes(analysis.engine.mode) ? transformerCount > 0 ? `mDeBERTa-XNLI (${transformerCount} çıkarım) + yapısal Türkçe sinyaller` : 'hibrit motor · yapısal Türkçe sinyaller (Transformer hazır)' : 'yapısal yedek'}</b>. İddia Radarı doğrulanabilirlik sinyalleri ve gerektiğinde aynı Transformer katmanını kullanır; Ortak Zemin görüş kümeleri arası çapraz-tema analiziyle, Köprü ise ortak tema + gerçek görüş ayrışması + eksik kanıt üzerinden üretilir.</p>
                          </>}

                          {active === 1 && <div className='stack'>
                            <div className='engineBanner semanticEngineBanner'>
                              <div><b>Görüş kümeleri arası ortaklık analizi</b><p>Bir görüşü tek başına “uzlaşı” saymak yerine, aynı temanın farklı görüş kümelerinde tekrar edip etmediği kontrol edilir.</p><small>{analysis.common_ground_details?.length ?? 0} ortak tema{groundElapsedMs > 0 ? ` • ${formatDuration(groundElapsedMs)}` : ''}</small></div>
                              <span>Kanıt izli</span>
                            </div>
                            {(analysis.common_ground_details?.length ? analysis.common_ground_details : analysis.common_ground.map((text,i) => ({theme:`Ortak zemin ${i+1}`,text,support_count:0,stance_count:0,evidence_comment_ids:[],confidence:0,engine:'Uyumluluk görünümü'}))).map((item,i) => <div className='insight green semanticInsight' key={`${item.theme}-${i}`}><div className='semanticTitleRow'><b>{item.theme}</b>{item.confidence > 0 && <span className='confidenceChip'>%{Math.round(item.confidence*100)} güven</span>}</div><p>{item.text}</p><div className='semanticMetaRow'>{item.stance_count > 0 && <span>{item.stance_count} görüş kümesi</span>}{item.support_count > 0 && <span>{item.support_count} yorum sinyali</span>}{item.evidence_comment_ids?.length > 0 && <span>Kanıt: #{item.evidence_comment_ids.join(', #')}</span>}</div></div>)}
                          </div>}

                          {active === 2 && <div className='stack'>
                            <div className='engineBanner viewpointEngineBanner'>
                              <div>
                                <b>{['transformer-zero-shot','hybrid-transformer'].includes(analysis.engine.mode) ? 'Hibrit AI görüş sınıflandırması' : 'Heuristik yedek sınıflandırma'}</b>
                                <p>{String(analysis.engine.message ?? '')}</p>
                                {(ruleCount > 0 || transformerCount > 0) && (
                                  <small>{ruleCount} yapısal sinyal • {transformerCount} Transformer çıkarımı{stanceElapsedMs > 0 ? ` • görüş katmanı ${formatDuration(stanceElapsedMs)}` : ''}</small>
                                )}
                                {semanticGuardrailCount > 0 && <small>{semanticGuardrailCount} yorum anlam tutarlılığı kontrolüyle doğru kümeye bağlandı.</small>}
                                {viewpointElapsedMs > 0 && <small>Görüş gerekçeleri ve yorum bağlantıları {formatDuration(viewpointElapsedMs)} içinde eşleştirildi.</small>}
                              </div>
                              {['transformer-zero-shot','hybrid-transformer'].includes(analysis.engine.mode) && (
                                transformerCount > 0
                                  ? <span>%{analysis.indicators.ai_average_confidence} model ort. güven</span>
                                  : <span className='noModelNeeded'>Model çıkarımı gerekmedi</span>
                              )}
                            </div>
                            {viewpointModelCommentCount > 0 && <p className='viewpointConfidenceNote'>Model güveni yalnızca Transformer ile değerlendirilen {viewpointModelCommentCount} yorumun sınıflandırma güvenidir; tüm yorumların doğruluğunu veya görüşün haklılığını göstermez.</p>}
                            {analysis.viewpoints.map(v => {
                              const representedCount = v.comment_count || analysis.stance_details.filter(item => item.label === v.name).length;
                              const guardrailComments = analysis.stance_details.filter(item => item.label === v.name && item.engine.startsWith('anlamsal tutarlılık:'));
                              return <div className={`viewpoint semanticViewpointCard ${v.name === 'Soru / Tarafsız' || v.name === 'Diğer / Nötr' ? 'neutralViewpointCard' : ''}`} key={v.name}>
                                <div className='vpRow semanticViewpointHeading'><div><b>{v.display_name || v.name}</b><span>{representedCount} yorum</span></div><strong>%{v.percentage}</strong></div>
                                <div className='bar'><span style={{width:`${v.percentage}%`}} /></div>
                                <div className='viewpointArgument'><b>Bu görüş neyi savunuyor?</b><p>{v.main_argument || v.summary}</p></div>
                                <details className='viewpointDetails'>
                                  <summary><span>Görüş ayrıntıları ve temsilci yorumlar</span><small>{v.representative_comments?.length || 0} yorum</small></summary>
                                  <div className='viewpointDetailsContent'>
                                    {v.dominant_themes?.length > 0 && <div className='viewpointThemeRow'>{v.dominant_themes.slice(0,2).map(theme => <span key={theme}>{theme}</span>)}</div>}
                                    {(v.relationship_note || v.opposing_viewpoint_names?.length > 0 || v.shared_themes?.length > 0) && <div className='viewpointRelationship'>
                                      <b>Diğer görüşlerle ilişkisi</b>
                                      {v.relationship_note && <p>{v.relationship_note}</p>}
                                      {v.opposing_viewpoint_names?.length > 0 && <span>Ayrıştığı yaklaşım: {v.opposing_viewpoint_names.map(name => viewpointLabelMap[name] || name).join(' • ')}</span>}
                                      {v.shared_themes?.length > 0 && <span>Ortak zemin: {v.shared_themes.join(' • ')}</span>}
                                    </div>}
                                    {v.representative_comments?.length > 0 && <div className='viewpointRepresentatives'>
                                      <b>Temsilci yorumlar</b>
                                      {v.representative_comments.map(item => <div className='viewpointRepresentative' key={item.comment_id}><div><strong>#{item.comment_id} · {item.author}</strong><span>{item.confidence > 0 ? `%${Math.round(item.confidence*100)} model güveni` : 'Yapısal sinyal'}</span></div><p>{item.text}</p></div>)}
                                    </div>}
                                    {guardrailComments.length > 0 && <div className='viewpointGuardrailComments'>
                                      <b>Anlam tutarlılığıyla doğrulanan yorumlar</b>
                                      {guardrailComments.map(item => <div className='viewpointGuardrailComment' key={`guard-${item.comment_id}`}><strong>#{item.comment_id}</strong><p>{item.text}</p><span>{item.engine.replace('anlamsal tutarlılık: ', '')}</span></div>)}
                                    </div>}
                                    {v.evidence_comment_ids?.length > 0 && <div className='viewpointAllComments'><b>Kümedeki tüm yorumlar</b><span>#{v.evidence_comment_ids.join(', #')}</span></div>}
                                    {(v.related_claim_comment_ids?.length > 0 || v.related_question_comment_ids?.length > 0) && <div className='viewpointEvidenceLinks'>
                                      {v.related_claim_comment_ids?.length > 0 && <span>İddia bağlantısı: #{v.related_claim_comment_ids.join(', #')}</span>}
                                      {v.related_question_comment_ids?.length > 0 && <span>Soru bağlantısı: #{v.related_question_comment_ids.join(', #')}</span>}
                                    </div>}
                                    <div className='viewpointMethodNote'>{v.structural_comment_count || representedCount - (v.model_comment_count || 0)} yapısal değerlendirme{v.model_comment_count > 0 ? ` • ${v.model_comment_count} Transformer çıkarımı` : ''}{v.average_model_confidence > 0 ? ` • %${Math.round(v.average_model_confidence*100)} model ortalaması` : ''}</div>
                                  </div>
                                </details>
                              </div>;
                            })}
                            {['transformer-zero-shot','hybrid-transformer'].includes(analysis.engine.mode) && <details className='stanceExamplesDetails'>
                              <summary>AI sınıflandırma ayrıntılarını göster</summary>
                              <div className='stanceExamples'>
                                <h4>AI sınıflandırma örnekleri</h4>
                                {analysis.stance_details.slice(0,6).map(s => <div className='stanceExample' key={s.comment_id}><div><b>#{s.comment_id} • {viewpointLabelMap[s.label] || s.label}</b><span>{s.confidence > 0 ? `%${Math.round(s.confidence*100)} model güveni` : 'Yapısal sinyal'}</span></div><p>{s.text}</p></div>)}
                              </div>
                            </details>}
                          </div>}

                          {active === 3 && <div className='stack'>
                            <div className='engineBanner semanticEngineBanner'>
                              <div><b>Hibrit doğrulanabilirlik analizi</b><p>Sayısal, nedensel, karşılaştırmalı ve yaygınlık iddiaları ayrılır; belirsiz adaylarda mevcut mDeBERTa-XNLI katmanı ikinci karar olarak kullanılabilir.</p><small>{analysis.claims.length} aday • {claimTransformerCount} yeni Transformer kararı{claimCacheHitCount > 0 ? ` • ${claimCacheHitCount} önbellek kararı` : ''}{claimElapsedMs > 0 ? ` • ${formatDuration(claimElapsedMs)}` : ''}</small></div>
                              <span>{claimTransformerCount > 0 ? 'AI + Yapısal' : claimCacheHitCount > 0 ? 'AI + Önbellek' : 'Yapısal'}</span>
                            </div>
                            {analysis.claims.length === 0 && <div className='emptyMini'>Doğrulanabilir iddia adayı tespit edilmedi.</div>}
                            {analysis.claims.map(c => { const savedClaim = bookmarks.find(item => item.kind === 'claim' && item.post_id === post?.id && item.comment_id === c.comment_id); return <div className='insight amber claimBookmarkCard semanticClaimCard' key={c.comment_id}><div className='insightTitleRow'><div className='claimTitleCluster'><b>İddia #{c.comment_id}</b><span className={`claimPriority claimPriority-${c.priority.toLowerCase()}`}>{c.priority} öncelik</span><span className='claimTypeChip'>{c.claim_type}</span></div><button className={`miniBookmark ${savedClaim ? 'bookmarkSaved' : ''}`} onClick={() => void toggleClaimBookmark(c.comment_id, c.text)} disabled={bookmarkSavingKey === `claim-${c.comment_id}`}>{bookmarkSavingKey === `claim-${c.comment_id}` ? '…' : savedClaim ? '★ Kayıtlı' : '☆ Kaydet'}</button></div><p>{c.text}</p><div className='claimVerification'><b>Doğrulama için:</b><span>{c.verification_need}</span></div><div className='semanticMetaRow'><span>{c.source_status}</span>{c.confidence > 0 && <span>%{Math.round(c.confidence*100)} aday güveni</span>}<span>{c.engine}</span></div></div>})}
                          </div>}

                          {active === 4 && <div className='stack'>
                            <div className='engineBanner semanticEngineBanner questionEngineBanner'>
                              <div>
                                <b>Yapısal-semantik soru analizi</b>
                                <p>Bilgi arayan sorular, kaynak talepleri ve karar soruları ayrılır; tekrarlar gruplanır, sonraki yorumlarda yanıt bağlantısı aranır.</p>
                                <small>{questionActionableCount} bilgi/karar sorusu • {questionUnansweredCount} cevapsız • {questionPartialCount} kısmi • {questionAnsweredCount} yanıtlı{questionRhetoricalCount > 0 ? ` • ${questionRhetoricalCount} retorik ayrıldı` : ''}{questionGroupedRepeatCount > 0 ? ` • ${questionGroupedRepeatCount} tekrar birleştirildi` : ''}{questionElapsedMs > 0 ? ` • ${formatDuration(questionElapsedMs)}` : ''}</small>
                              </div>
                              <span>Yanıt izli</span>
                            </div>
                            <p className='questionConfidenceNote'>Soru tespit güveni, ifadenin ilgili soru türüne ait olduğuna ilişkin sistem güvenidir; verilen yanıtın doğruluğunu göstermez.</p>
                            {analysis.unanswered_questions.length === 0 && <div className='emptyMini'>Bilgi arayan veya karar vermeyi destekleyen soru tespit edilmedi.</div>}
                            {analysis.unanswered_questions.map((q,i) => { const statusClass = q.answer_status === 'Cevapsız' ? 'open' : q.answer_status === 'Kısmen cevaplandı' ? 'partial' : 'answered'; return <div className={`insight purple semanticQuestionCard questionStatus-${statusClass}`} key={q.identity_key || `${q.comment_id}-${i}`}>
                              <div className='questionTitleRow'><div><b>❓ Soru #{q.comment_id}</b><span className='questionTypeChip'>{q.question_type}</span></div><div><span className={`questionStatusChip questionStatusChip-${statusClass}`}>{q.answer_status}</span><span className={`questionPriority questionPriority-${q.priority.toLowerCase()}`}>{q.priority} öncelik</span></div></div>
                              <p className='questionText'>{q.text}</p>
                              <div className='questionEvidenceGrid'>
                                <div><span>Dayanak yorumlar</span><b>#{(q.evidence_comment_ids?.length ? q.evidence_comment_ids : [q.comment_id]).join(', #')}</b></div>
                                <div><span>Etkilediği görüşler</span><b>{q.affected_viewpoints?.length ? q.affected_viewpoints.map(name => viewpointLabelMap[name] || name).join(' • ') : 'Belirgin küme bağlantısı yok'}</b></div>
                                <div><span>Yanıt bağlantıları</span><b>{q.answer_comment_ids?.length ? `#${q.answer_comment_ids.join(', #')}` : 'Henüz bulunmadı'}</b></div>
                              </div>
                              <div className='questionImpact'><b>Bu soru cevaplanırsa ne değişebilir?</b><span>{q.impact}</span></div>
                              <div className='semanticMetaRow'><span>%{Math.round(q.confidence*100)} soru tespit güveni</span>{q.repeated_comment_ids?.length > 0 && <span>{q.repeated_comment_ids.length} benzer tekrar birleştirildi</span>}<span>{q.engine}</span></div>
                            </div>})}
                            {analysis.rhetorical_questions?.length > 0 && <div className='rhetoricalSection'><div><b>Retorik ifadeler ayrı tutuldu</b><span>Doğrudan bilgi veya kaynak talebi olmadıkları için cevapsız soru sayısına eklenmez.</span></div>{analysis.rhetorical_questions.map((q,i) => <div className='rhetoricalQuestion' key={q.identity_key || `r-${q.comment_id}-${i}`}><b>Yorum #{q.comment_id}</b><p>{q.text}</p></div>)}</div>}
                          </div>}

                          {active === 5 && <div>
                            <div className='coachHeader'>
                              <div>
                                <span className='eyebrow'>BAĞLAMA DUYARLI YANIT KOÇU</span>
                                <p>Mesajın ana fikrini korur; kişiselleştirme, ton, soru ve kanıt ihtiyacını tartışma bağlamına göre değerlendirir.</p>
                              </div>
                              <div className='coachStatusArea'>
                                <span className={coachStatus?.loaded ? 'coachReadyChip' : 'coachWaitChip'}>
                                  {coachStatus?.loaded ? '● Üretken AI hazır' : '◇ Üretken AI bekliyor'}
                                </span>
                                {!coachStatus?.loaded && useAI && (
                                  <button className='ghost compact' onClick={prepareCoach} disabled={coachLoading}>
                                    {coachLoading ? 'Model hazırlanıyor…' : 'AI Koçunu Hazırla'}
                                  </button>
                                )}
                              </div>
                            </div>
                            <label className='fieldLabel'>Yorumun</label>
                            <textarea value={draft} onChange={e => { setDraft(e.target.value); setRewrite(null); }} />
                            <button className='primary' onClick={runRewrite} disabled={rewriteLoading}>
                              {rewriteLoading ? 'AI mesajı analiz ediyor…' : '✨ Mesajı analiz et ve yeniden yaz'}
                            </button>
                            {rewrite && <div className='coachBox'>
                              <div className='coachResultTop'>
                                <span className='eyebrow'>AI ÖNERİSİ</span>
                                <span className='coachEngineChip'>{rewrite.engine === 'qwen-generative' ? 'Denetimli Üretken AI' : rewrite.engine === 'hybrid-safe' ? 'Hibrit Güvenli Katman' : rewrite.engine === 'preserve-safe' ? 'Değişiklik Gerekmedi' : 'Bağlamsal Güvenli Motor'} • {formatDuration(rewrite.elapsed_ms)}</span>
                              </div>
                              <p>{rewrite.suggestion}</p>
                              {rewrite.signals?.length > 0 && <div className='signalRow'>{rewrite.signals.map(s => <span key={s}>{s}</span>)}</div>}
                              <small>{rewrite.reason}</small>
                              <div className='coachActions'><button className='primary compact' onClick={() => setDraft(rewrite.suggestion)}>Öneriyi Kullan</button><button className='ghost compact' onClick={() => setRewrite(null)}>Orijinali Koru</button></div>
                            </div>}
                          </div>}

                          {active === 6 && <div className='stack'>{analysis.changes_since_last_visit.map(x => <div className='timeline' key={x}><span>✓</span><p>{x}</p></div>)}</div>}

                          {active === 7 && <div className='bridgeBox'><div className='bridgeEngineSummary'><div><span className='eyebrow'>KANITA DAYALI KÖPRÜ SENTEZİ</span><b>{analysis.bridge.engine ?? 'Köprü sentezi'}</b></div><div className='bridgeEngineChips'>{typeof analysis.bridge.confidence === 'number' && <span>%{Math.round(analysis.bridge.confidence*100)} güven</span>}{analysis.bridge.evidence_comment_ids?.length ? <span>{analysis.bridge.evidence_comment_ids.length} kanıt yorumu</span> : null}{bridgeElapsedMs > 0 && <span>{formatDuration(bridgeElapsedMs)}</span>}</div></div><Bridge label='Ortak kabul' text={analysis.bridge.common_acceptance} /><Bridge label='Asıl ayrışma' text={analysis.bridge.main_divergence} />{analysis.bridge.contrast_viewpoint_labels?.length ? <div className='bridgeContrastRow'><b>Karşılaştırılan yaklaşımlar</b><div>{analysis.bridge.contrast_viewpoint_labels.map(label => <span key={label}>{label}</span>)}</div></div> : null}<Bridge label='Eksik bilgi / doğrulama ihtiyacı' text={analysis.bridge.missing_information} />{analysis.bridge.evidence_comment_ids?.length ? <div className='bridgeEvidenceRow'><b>Dayanak yorumlar</b><span>#{analysis.bridge.evidence_comment_ids.join(', #')}</span></div> : null}<Bridge label='🌉 Tartışmayı ilerletecek Köprü Sorusu' text={analysis.bridge.bridge_question} strong /><div className='bridgeActionRow'><button className='primary' onClick={() => void shareCurrentBridgeToMessages()}>Köprüyü Mesajlarda Paylaş</button><button className={`ghost bookmarkToggle ${bridgeBookmark ? 'bookmarkSaved' : ''}`} onClick={() => void toggleBridgeBookmark()} disabled={bookmarkSavingKey === `bridge-${post?.id}`}>{bookmarkSavingKey === `bridge-${post?.id}` ? 'Kaydediliyor…' : bridgeBookmark ? '★ Köprü Kaydedildi' : '☆ Köprüyü Kaydet'}</button></div>{bridgeShareFeedback && <small className='bridgeShareFeedback'>{bridgeShareFeedback}</small>}</div>}
                        </div>
                      </>
                    )}

          </>
        ) : navPage === 'Keşfet' ? (
          <ExplorePreviewPanel
            topic={explorePreviewTopic}
            post={explorePreviewPost}
            loading={explorePreviewLoading}
            error={explorePreviewError}
            onOpenTopic={openExploreTopic}
          />
        ) : navPage === 'Bildirimler' ? (
          <NotificationPanel
            notification={selectedNotification}
            opening={notificationOpening}
            onOpen={openNotificationTarget}
            onToggleRead={toggleNotificationReadState}
            onDelete={removeNotification}
          />
        ) : navPage === 'Mesajlar' ? (
          <MessagePanel
            detail={conversationDetail}
            loading={conversationLoading}
            error={conversationError}
            draft={conversationDraft}
            sending={conversationSending}
            onDraft={setConversationDraft}
            onSend={sendMessageToConversation}
            openingPost={messageBridgeOpening}
            onOpenPost={openBridgeFromMessages}
          />
        ) : navPage === 'Yer İmleri' ? (
          <BookmarkPanel
            bookmark={selectedBookmark}
            opening={bookmarkOpening}
            savingKey={bookmarkSavingKey}
            onOpen={openBookmarkTarget}
            onRemove={removeBookmark}
          />
        ) : navPage === 'Listeler' ? (
          <ListPanel
            detail={topicListDetail}
            post={post}
            analysis={analysis}
            loading={topicListLoading}
            error={topicListError}
            sourceLoading={topicListSourceLoading}
            sourceError={topicListSourceError}
            savingKey={topicListSavingKey}
            opening={topicListOpening}
            onAdd={addCurrentToTopicList}
            onPrepareSource={ensureTopicListSourceAnalysis}
            onRemove={removeTopicListEntry}
            onOpen={openTopicListEntry}
          />
        ) : navPage === 'Profil' ? (
          <ProfilePanel
            detail={historyDetail}
            loading={historyLoading}
            opening={historyOpening}
            onOpen={openHistorySnapshot}
          />
        ) : navPage === 'Teknik Doğrulama' ? (
          <TechnicalPanel result={technicalResult} scenarioResult={technicalScenarioResult} loading={technicalLoading} running={technicalRunning || technicalScenarioRunning} />
        ) : (
          <NavContext page={navPage} />
        )}
      </section>
    </main>
  );
}


async function shareBridge(title: string, question: string) {
  const text = `N-KÖPRÜ • ${title}\n\nTartışmayı ilerletecek Köprü Sorusu:\n${question}`;
  try {
    if (navigator.share) {
      await navigator.share({ title: 'N-KÖPRÜ', text });
      return;
    }
    await navigator.clipboard.writeText(text);
    window.alert('Köprü kartı panoya kopyalandı.');
  } catch {
    // Kullanıcı paylaşım penceresini kapatırsa sessizce devam et.
  }
}

function formatDuration(ms: number) {
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(1)} sn`;
}


function ExploreWorkspace({
  onOpenTopic,
  onPreviewTopic,
  onClearPreview,
  selectedTopicId,
}:{
  onOpenTopic:(topicId:number, analyzeNow?:boolean)=>Promise<void>;
  onPreviewTopic:(topic:ExploreTopic)=>Promise<void>;
  onClearPreview:()=>void;
  selectedTopicId:number | null;
}) {
  const [topics, setTopics] = useState<ExploreTopic[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [category, setCategory] = useState('Tümü');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [openingId, setOpeningId] = useState<number | null>(null);
  const hasFilters = category !== 'Tümü' || query.trim().length > 0;

  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(async () => {
      setLoading(true); setError('');
      try {
        const data = await getExploreTopics(category, query);
        if (!active) return;
        setTopics(data.topics);
        setCategories(data.categories);
        if (data.topics.length === 0) {
          onClearPreview();
        } else if (!data.topics.some(topic => topic.id === selectedTopicId)) {
          void onPreviewTopic(data.topics[0]);
        }
      } catch (e) {
        if (active) setError(e instanceof Error ? e.message : 'Keşfet gündemi yüklenemedi');
      } finally {
        if (active) setLoading(false);
      }
    }, query ? 220 : 0);
    return () => { active = false; window.clearTimeout(timer); };
  }, [category, query, onClearPreview, onPreviewTopic, selectedTopicId]);

  async function open(topicId:number, analyzeNow=false) {
    setOpeningId(topicId);
    try { await onOpenTopic(topicId, analyzeNow); }
    finally { setOpeningId(null); }
  }

  function clearFilters() {
    setCategory('Tümü');
    setQuery('');
  }

  return (
    <div className='navWorkspace exploreWorkspace'>
      <div className='workspaceHero exploreHero'>
        <div>
          <span className='eyebrow'>N-KÖPRÜ • KEŞFET</span>
          <h2>Keşfet</h2>
          <p>Gündemdeki tartışmaları ara, konuya göre filtrele ve tek tıkla N-KÖPRÜ analizine taşı.</p>
        </div>
        <span className='liveDataChip'>● Demo gündem aktif</span>
      </div>

      <div className='exploreControls'>
        <div className='exploreSearchWrap'>
          <span>⌕</span>
          <input
            className='exploreSearch'
            placeholder='Tartışma, konu veya etiket ara…'
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
          {query && <button className='clearSearch' onClick={() => setQuery('')} aria-label='Aramayı temizle'>×</button>}
        </div>
        <div className='categoryStrip'>
          {['Tümü', ...categories].map(item => (
            <button key={item} className={category === item ? 'categoryActive' : ''} onClick={() => setCategory(item)}>{item}</button>
          ))}
        </div>
      </div>

      <div className='exploreStats'>
        <span><b>{topics.length}</b> tartışma</span>
        <span><b>{topics.reduce((sum,t) => sum + t.comment_count, 0)}</b> yorum</span>
        {category !== 'Tümü' && <span><b>{category}</b></span>}
        {query.trim() && <span>Arama: <b>“{query.trim()}”</b></span>}
        {!hasFilters && <span><b>Tüm gündem</b></span>}
        {hasFilters && <button className='filterReset' onClick={clearFilters}>Filtreleri temizle</button>}
      </div>

      {error && <div className='errorBox'>{error}</div>}
      {loading ? (
        <div className='exploreLoading'>Keşfet gündemi hazırlanıyor…</div>
      ) : topics.length === 0 ? (
        <div className='exploreEmpty'>
          <b>Eşleşen tartışma bulunamadı.</b>
          <span>Arama metnini değiştir veya filtreleri temizleyerek tüm gündeme dön.</span>
          {hasFilters && <button className='ghost compact' onClick={clearFilters}>Filtreleri temizle</button>}
        </div>
      ) : (
        <div className='exploreGrid'>
          {topics.map(topic => (
            <article
              className={`exploreCard ${selectedTopicId === topic.id ? 'exploreCardSelected' : ''}`}
              key={topic.id}
              onClick={() => void onPreviewTopic(topic)}
              role='button'
              tabIndex={0}
              onKeyDown={e => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  void onPreviewTopic(topic);
                }
              }}
            >
              <div className='exploreCardTop'>
                <span className='exploreCategory'>{topic.category}</span>
                <span className='exploreBadge'>{topic.badge}</span>
              </div>
              <h3>{topic.title}</h3>
              <p>{topic.summary}</p>
              <div className='tagRow'>{topic.tags.map(tag => <span key={tag}>#{tag}</span>)}</div>
              <div className='exploreCardFooter'>
                <span>💬 {topic.comment_count} yorum</span>
                <div>
                  <button
                    className='ghost compact'
                    onClick={e => { e.stopPropagation(); void open(topic.id, false); }}
                    disabled={openingId !== null}
                    title='Tartışmayı yorumlarıyla ana akışta aç; analizi sen başlat.'
                  >
                    {openingId === topic.id ? 'Açılıyor…' : 'Tartışmayı Aç'}
                  </button>
                  <button
                    className='primary compact noMargin'
                    onClick={e => { e.stopPropagation(); void open(topic.id, true); }}
                    disabled={openingId !== null}
                    title='Tartışmayı aç ve N-KÖPRÜ analizini doğrudan başlat.'
                  >
                    {openingId === topic.id ? 'Analiz ediliyor…' : '✨ Hızlı Analiz'}
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      <div className='workspaceNote exploreNote'>
        <b>İki farklı geçiş seçeneği</b>
        <p><b>Tartışmayı Aç</b> yorumları önce ana akışta gösterir ve analiz kararını sana bırakır. <b>Hızlı Analiz</b> aynı tartışmayı doğrudan N-KÖPRÜ analiz motoruna gönderir.</p>
      </div>
    </div>
  );
}

function ExplorePreviewPanel({
  topic,
  post,
  loading,
  error,
  onOpenTopic,
}:{
  topic:ExploreTopic | null;
  post:Post | null;
  loading:boolean;
  error:string;
  onOpenTopic:(topicId:number, analyzeNow?:boolean)=>Promise<void>;
}) {
  const [openingMode, setOpeningMode] = useState<'open'|'analyze'|null>(null);

  async function run(mode:'open'|'analyze') {
    if (!topic) return;
    setOpeningMode(mode);
    try { await onOpenTopic(topic.id, mode === 'analyze'); }
    finally { setOpeningMode(null); }
  }

  return (
    <>
      <div className='panelHeader'>
        <div><span className='eyebrow'>N-KÖPRÜ KEŞFET</span><h2>Tartışma önizlemesi</h2></div>
        <span className='status'>Hazır</span>
      </div>

      {!topic ? (
        <div className='emptyState explorePreviewEmpty'>
          <div className='bigIcon'>⌕</div>
          <h3>Bir tartışma seç</h3>
          <p>Soldaki kartlardan birini seçtiğinde başlık, etiketler ve örnek yorumlar burada görünür.</p>
        </div>
      ) : (
        <div className='moduleCard explorePreviewCard'>
          <div className='previewTopLine'>
            <span className='exploreCategory'>{topic.category}</span>
            <span className='exploreBadge'>{topic.badge}</span>
          </div>
          <h3 className='previewTitle'>{topic.title}</h3>
          <p className='previewSummary'>{topic.summary}</p>
          <div className='tagRow previewTags'>{topic.tags.map(tag => <span key={tag}>#{tag}</span>)}</div>

          <div className='previewMetaRow'>
            <span>💬 <b>{topic.comment_count}</b> yorum</span>
            <span>Kontrollü demo verisi</span>
          </div>

          {error && <div className='errorBox'>{error}</div>}
          {loading ? (
            <div className='previewLoading'>Yorum önizlemesi yükleniyor…</div>
          ) : post ? (
            <div className='previewComments'>
              <div className='previewSectionTitle'>Örnek yorumlar</div>
              {post.comments.slice(0,4).map(comment => (
                <div className='previewComment' key={comment.id}>
                  <div className='avatar small'>{comment.author.split(' ').map(s => s[0]).join('').slice(0,2)}</div>
                  <div><b>{comment.author}</b><p>{comment.text}</p></div>
                </div>
              ))}
              {post.comments.length > 4 && <small>+ {post.comments.length - 4} yorum daha</small>}
            </div>
          ) : null}

          <div className='previewActions'>
            <button className='ghost' onClick={() => void run('open')} disabled={openingMode !== null || loading}>
              {openingMode === 'open' ? 'Açılıyor…' : 'Tartışmayı Aç'}
            </button>
            <button className='primary noMargin' onClick={() => void run('analyze')} disabled={openingMode !== null || loading}>
              {openingMode === 'analyze' ? 'Analiz ediliyor…' : '✨ N-KÖPRÜ ile Analiz Et'}
            </button>
          </div>
          <div className='previewActionHelp'>
            <span><b>Tartışmayı Aç:</b> önce yorumları incele.</span>
            <span><b>Analiz Et:</b> doğrudan 8 adımlı N-KÖPRÜ haritasını oluştur.</span>
          </div>
        </div>
      )}
    </>
  );
}


function NotificationWorkspace({
  notifications,
  totalCount,
  readCount,
  unreadCount,
  loading,
  error,
  filter,
  selectedId,
  undo,
  onFilter,
  onRefresh,
  onSelect,
  onToggleRead,
  onDelete,
  onReadAll,
  onClearRead,
  onUndo,
}:{
  notifications:NotificationItem[];
  totalCount:number;
  readCount:number;
  unreadCount:number;
  loading:boolean;
  error:string;
  filter:'Tümü'|'Okunmamış'|'Okunanlar';
  selectedId:number | null;
  undo:{ids:number[]; label:string} | null;
  onFilter:(mode:'Tümü'|'Okunmamış'|'Okunanlar')=>Promise<void>;
  onRefresh:()=>Promise<void>;
  onSelect:(item:NotificationItem)=>Promise<void>;
  onToggleRead:(item:NotificationItem)=>Promise<void>;
  onDelete:(item:NotificationItem)=>Promise<void>;
  onReadAll:()=>Promise<void>;
  onClearRead:()=>Promise<void>;
  onUndo:()=>Promise<void>;
}) {
  const [menuId, setMenuId] = useState<number | null>(null);

  return (
    <div className='navWorkspace notificationWorkspace'>
      <div className='workspaceHero notificationHero'>
        <div>
          <span className='eyebrow'>N-KÖPRÜ • BİLDİRİM MERKEZİ</span>
          <h2>Bildirimler</h2>
          <p>Yalnızca anlamlı analiz değişikliklerini, yeni iddiaları, kaynak ihtiyaçlarını ve Köprü güncellemelerini tek akışta izle.</p>
        </div>
        <span className={`notificationLiveChip ${unreadCount > 0 ? 'hasUnread' : ''}`}>● {unreadCount > 0 ? `${unreadCount} okunmamış` : 'Tümü okundu'}</span>
      </div>

      <div className='notificationSummaryRow'>
        <span><b>{totalCount}</b> toplam</span>
        <span><b>{unreadCount}</b> okunmamış</span>
        <span><b>{readCount}</b> okunan</span>
      </div>

      <div className='notificationToolbar'>
        <div className='notificationFilters'>
          {(['Tümü','Okunmamış','Okunanlar'] as const).map(mode => (
            <button key={mode} className={filter === mode ? 'notificationFilterActive' : ''} onClick={() => void onFilter(mode)}>
              {mode}{mode === 'Okunmamış' && unreadCount > 0 ? ` (${unreadCount})` : mode === 'Okunanlar' && readCount > 0 ? ` (${readCount})` : ''}
            </button>
          ))}
        </div>
        <div className='notificationActions'>
          <button className='ghost compact' onClick={() => void onRefresh()} disabled={loading}>↻ Yenile</button>
          <button className='ghost compact' onClick={() => void onReadAll()} disabled={unreadCount === 0}>Tümünü okundu yap</button>
          <button className='ghost compact dangerGhost' onClick={() => void onClearRead()} disabled={readCount === 0}>Okunanları temizle</button>
        </div>
      </div>

      {error && <div className='errorBox'>{error}</div>}
      {loading ? (
        <div className='notificationEmpty'>Bildirim akışı yenileniyor…</div>
      ) : notifications.length === 0 ? (
        <div className='notificationEmpty'>
          <b>{filter === 'Okunmamış' ? 'Okunmamış bildirim yok.' : filter === 'Okunanlar' ? 'Okunmuş bildirim yok.' : 'Henüz bildirim yok.'}</b>
          <span>{filter === 'Okunmamış' ? 'Tüm bildirimleri görmek için “Tümü” filtresine geç.' : filter === 'Okunanlar' ? 'Okuduğun bildirimler burada görünür.' : 'Yeni ve anlamlı bir analiz değişikliği oluştuğunda burada bildirim göreceksin.'}</span>
        </div>
      ) : (
        <div className='notificationList'>
          {notifications.map(item => (
            <div
              className={`notificationItem ${!item.is_read ? 'notificationUnread' : ''} ${selectedId === item.id ? 'notificationSelected' : ''}`}
              key={item.id}
              role='button'
              tabIndex={0}
              onClick={() => { setMenuId(null); void onSelect(item); }}
              onKeyDown={e => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  setMenuId(null);
                  void onSelect(item);
                }
              }}
            >
              <span className={`notificationDot ${item.priority === 'high' ? 'notificationDotHigh' : ''}`} />
              <div className='notificationItemBody'>
                <div className='notificationItemTop'>
                  <b>{item.title}</b>
                  <span>{item.relative_time}</span>
                </div>
                <p>{item.text}</p>
                <div className='notificationMeta'>
                  <span>{item.badge}</span>
                  {!item.is_read && <em>Yeni</em>}
                </div>
              </div>
              <div className='notificationMenuWrap'>
                <button
                  className='notificationMenuButton'
                  aria-label='Bildirim seçenekleri'
                  aria-expanded={menuId === item.id}
                  onClick={e => { e.stopPropagation(); setMenuId(current => current === item.id ? null : item.id); }}
                >⋯</button>
                {menuId === item.id && (
                  <div className='notificationMenu' onClick={e => e.stopPropagation()}>
                    <button onClick={() => { setMenuId(null); void onToggleRead(item); }}>{item.is_read ? 'Okunmadı yap' : 'Okundu yap'}</button>
                    <button className='notificationDeleteAction' onClick={() => { setMenuId(null); void onDelete(item); }}>Bildirimi sil</button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {undo && (
        <div className='notificationUndoToast' role='status'>
          <span>{undo.label}</span>
          <button onClick={() => void onUndo()}>Geri Al</button>
        </div>
      )}

      <div className='workspaceNote notificationNote'>
        <b>Bildirimler analiz akışına bağlı</b>
        <p>Aynı tartışmayı değişiklik olmadan yeniden analiz etmek yeni bildirim üretmez. Yalnızca yeni görüş, iddia, soru, ortak zemin veya Köprü değişikliği olduğunda ilgili olay burada görünür. Okunan bildirimleri tek tek silebilir veya topluca temizleyebilirsin.</p>
      </div>
    </div>
  );
}

function NotificationPanel({
  notification,
  opening,
  onOpen,
  onToggleRead,
  onDelete,
}:{
  notification:NotificationItem | null;
  opening:boolean;
  onOpen:(item:NotificationItem)=>Promise<void>;
  onToggleRead:(item:NotificationItem)=>Promise<void>;
  onDelete:(item:NotificationItem)=>Promise<void>;
}) {
  const destinationNames = tabs;
  return (
    <>
      <div className='panelHeader'>
        <div><span className='eyebrow'>N-KÖPRÜ BİLDİRİMLER</span><h2>Bildirim detayı</h2></div>
        <span className='status'>Hazır</span>
      </div>

      {!notification ? (
        <div className='emptyState notificationPreviewEmpty'>
          <div className='bigIcon'>🔔</div>
          <h3>Bir bildirim seç</h3>
          <p>Soldaki akıştan bir öğe seçtiğinde olayın detayı ve ilgili N-KÖPRÜ adımı burada görünür.</p>
        </div>
      ) : (
        <div className='moduleCard notificationDetailCard'>
          <div className='notificationDetailTop'>
            <span className='notificationTypeBadge'>{notification.badge}</span>
            <span className={notification.is_read ? 'notificationReadState' : 'notificationUnreadState'}>{notification.is_read ? 'Okundu' : 'Okunmamış'}</span>
          </div>
          <h3>{notification.title}</h3>
          <p className='notificationDetailText'>{notification.text}</p>

          <div className='notificationDestination'>
            <span className='eyebrow'>HEDEF</span>
            <b>{notification.tab_index != null ? `${notification.tab_index + 1}. ${destinationNames[notification.tab_index] ?? 'N-KÖPRÜ'}` : 'N-KÖPRÜ ana akışı'}</b>
            <p>İlgili tartışmayı yükleyip doğrudan bağlantılı analiz adımını açabilirsin.</p>
          </div>

          <div className='notificationDetailMeta'>
            <div><span>Tartışma</span><b>#{notification.post_id ?? '—'}</b></div>
            <div><span>Zaman</span><b>{notification.relative_time}</b></div>
            <div><span>Öncelik</span><b>{notification.priority === 'high' ? 'Dikkat' : 'Normal'}</b></div>
          </div>

          <div className='notificationDetailActions'>
            {notification.post_id != null && notification.tab_index != null && (
              <button className='primary notificationOpenButton' onClick={() => void onOpen(notification)} disabled={opening}>
                {opening ? 'İlgili analiz açılıyor…' : `→ ${destinationNames[notification.tab_index] ?? 'N-KÖPRÜ'} adımına git`}
              </button>
            )}
            <button className='ghost' onClick={() => void onToggleRead(notification)}>{notification.is_read ? 'Okunmadı yap' : 'Okundu yap'}</button>
            <button className='ghost dangerGhost' onClick={() => void onDelete(notification)}>Bildirimi sil</button>
          </div>
          <small className='notificationSessionNote'>Bildirimler SQLite üzerinde kalıcı saklanır; backend yeniden başlasa da okunma ve silme durumları korunur.</small>
        </div>
      )}
    </>
  );
}


function MessageWorkspace({
  conversations,
  selectedId,
  loading,
  error,
  onSelect,
  onRefresh,
}:{
  conversations:ConversationSummary[];
  selectedId:number | null;
  loading:boolean;
  error:string;
  onSelect:(conversationId:number)=>Promise<void>;
  onRefresh:()=>Promise<void>;
}) {
  const unread = conversations.reduce((sum, item) => sum + item.unread_count, 0);
  return (
    <div className='navWorkspace messageWorkspace'>
      <div className='workspaceHero messageHero'>
        <div>
          <span className='eyebrow'>N-KÖPRÜ • MESAJLAR</span>
          <h2>Mesajlar</h2>
          <p>Köprü kartlarını, analiz özetlerini ve ekip notlarını konuşma akışında paylaş.</p>
        </div>
        <span className={`messageLiveChip ${unread > 0 ? 'hasUnread' : ''}`}>● {unread > 0 ? `${unread} okunmamış` : 'Ekip akışı hazır'}</span>
      </div>

      <div className='messageToolbar'>
        <div>
          <b>Konuşmalar</b>
          <span>{conversations.length} aktif alan</span>
        </div>
        <button className='ghost compact' onClick={() => void onRefresh()} disabled={loading}>↻ Yenile</button>
      </div>

      {error && <div className='errorBox'>{error}</div>}
      {loading && conversations.length === 0 ? (
        <div className='messageEmpty'>Konuşmalar yükleniyor…</div>
      ) : conversations.length === 0 ? (
        <div className='messageEmpty'>Henüz konuşma bulunmuyor.</div>
      ) : (
        <div className='conversationList'>
          {conversations.map(item => (
            <button
              key={item.id}
              className={`conversationItem ${selectedId === item.id ? 'conversationSelected' : ''}`}
              onClick={() => void onSelect(item.id)}
            >
              <div className='conversationAvatar'>{item.title === 'N-KÖPRÜ Sistem' ? 'N' : 'DG'}</div>
              <div className='conversationBody'>
                <div className='conversationTop'>
                  <b>{item.title}</b>
                  <span>{item.last_time}</span>
                </div>
                <span className='conversationSubtitle'>{item.subtitle}</span>
                <p>{item.last_message}</p>
                <div className='conversationMeta'>
                  <em>{item.badge}</em>
                  {item.unread_count > 0 && <strong>{item.unread_count} yeni</strong>}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      <div className='workspaceNote messageNote'>
        <b>Köprü Oluştur → Mesajlar bağlantısı aktif</b>
        <p>Bir tartışmanın 8. adımındaki “Köprüyü Mesajlarda Paylaş” düğmesi, kartı doğrudan Ekip görüşmesine ekler. Kart üzerindeki bağlantı ile ilgili tartışmaya ve Köprü adımına geri dönebilirsin.</p>
      </div>
    </div>
  );
}

function MessagePanel({
  detail,
  loading,
  error,
  draft,
  sending,
  openingPost,
  onDraft,
  onSend,
  onOpenPost,
}:{
  detail:ConversationDetail | null;
  loading:boolean;
  error:string;
  draft:string;
  sending:boolean;
  openingPost:boolean;
  onDraft:(value:string)=>void;
  onSend:()=>Promise<void>;
  onOpenPost:(postId:number, tabIndex:number | null)=>Promise<void>;
}) {
  return (
    <>
      <div className='panelHeader'>
        <div><span className='eyebrow'>N-KÖPRÜ MESAJLAR</span><h2>{detail?.conversation.title ?? 'Mesajlaşma katmanı'}</h2></div>
        <span className='status'>Hazır</span>
      </div>

      {!detail ? (
        <div className='emptyState messagePreviewEmpty'>
          <div className='bigIcon'>💬</div>
          <h3>{loading ? 'Konuşma yükleniyor' : 'Bir konuşma seç'}</h3>
          <p>{error || 'Soldaki listeden ekip veya sistem konuşmasını aç.'}</p>
        </div>
      ) : (
        <div className='messagePanelCard'>
          <div className='messageConversationHeader'>
            <div className='messageConversationIcon'>{detail.conversation.title === 'N-KÖPRÜ Sistem' ? 'N' : 'DG'}</div>
            <div>
              <b>{detail.conversation.title}</b>
              <span>{detail.conversation.subtitle}</span>
            </div>
            <em>{detail.conversation.badge}</em>
          </div>

          {error && <div className='errorBox'>{error}</div>}

          <div className='messageThread'>
            {detail.messages.map(item => (
              <div key={item.id} className={`messageBubbleRow ${item.is_mine ? 'mine' : ''}`}>
                <div className={`messageBubble ${item.is_mine ? 'mine' : ''}`}>
                  <div className='messageBubbleTop'><b>{item.author}</b><span>{item.relative_time}</span></div>
                  <p>{item.text}</p>
                  {item.attachment?.kind === 'bridge' && (
                    <div className='messageBridgeCard'>
                      <span className='eyebrow'>🌉 N-KÖPRÜ KÖPRÜ KARTI</span>
                      <h4>{item.attachment.title}</h4>
                      {item.attachment.summary && <p className='messageBridgeSummary'>{item.attachment.summary}</p>}
                      <div className='messageBridgeGrid'>
                        <div><span>Ortak kabul</span><b>{item.attachment.common_acceptance || '—'}</b></div>
                        <div><span>Asıl ayrışma</span><b>{item.attachment.main_divergence || '—'}</b></div>
                        <div><span>Eksik bilgi</span><b>{item.attachment.missing_information || '—'}</b></div>
                      </div>
                      <div className='messageBridgeQuestion'>
                        <span>Tartışmayı ilerletecek Köprü Sorusu</span>
                        <b>{item.attachment.bridge_question}</b>
                      </div>
                      {item.attachment.post_id != null && (
                        <button
                          className='ghost compact messageBridgeOpen'
                          onClick={() => void onOpenPost(item.attachment!.post_id!, item.attachment!.tab_index)}
                          disabled={openingPost}
                          aria-busy={openingPost}
                        >
                          {openingPost ? '⏳ Köprü açılıyor…' : '→ İlgili Köprü analizini aç'}
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className='messageComposer'>
            <textarea
              value={draft}
              onChange={e => onDraft(e.target.value)}
              placeholder='Ekip notunu veya yanıtını yaz…'
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  void onSend();
                }
              }}
            />
            <div>
              <span>Enter gönderir • Shift+Enter yeni satır</span>
              <button className='primary noMargin' onClick={() => void onSend()} disabled={sending || !draft.trim()}>{sending ? 'Gönderiliyor…' : 'Gönder'}</button>
            </div>
          </div>
          <small className='messageSessionNote'>Mesajlar ve paylaşılan Köprü kartları SQLite üzerinde kalıcı saklanır.</small>
        </div>
      )}
    </>
  );
}

function bookmarkKindLabel(kind:BookmarkKind) {
  if (kind === 'discussion') return 'Tartışma';
  if (kind === 'claim') return 'İddia';
  return 'Köprü Sorusu';
}

function bookmarkKindIcon(kind:BookmarkKind) {
  if (kind === 'discussion') return '💬';
  if (kind === 'claim') return '◈';
  return '🌉';
}

function BookmarkWorkspace({
  bookmarks,
  totalCount,
  filter,
  selectedId,
  loading,
  error,
  savingKey,
  onFilter,
  onRefresh,
  onSelect,
  onOpen,
  onRemove,
}:{
  bookmarks:BookmarkItem[];
  totalCount:number;
  filter:BookmarkKind|'all';
  selectedId:number|null;
  loading:boolean;
  error:string;
  savingKey:string;
  onFilter:(kind:BookmarkKind|'all')=>Promise<void>;
  onRefresh:()=>Promise<void>;
  onSelect:(item:BookmarkItem)=>void;
  onOpen:(item:BookmarkItem)=>Promise<void>;
  onRemove:(id:number,key?:string)=>Promise<void>;
}) {
  const filters:{key:BookmarkKind|'all';label:string}[] = [
    {key:'all',label:'Tümü'},
    {key:'discussion',label:'Tartışmalar'},
    {key:'claim',label:'İddialar'},
    {key:'bridge',label:'Köprü Soruları'},
  ];

  return (
    <div className='navWorkspace bookmarkWorkspace'>
      <div className='workspaceHero bookmarkHero'>
        <div>
          <span className='eyebrow'>N-KÖPRÜ • YER İMLERİ</span>
          <h2>Yer İmleri</h2>
          <p>Tartışmaları, doğrulanabilir iddiaları ve Köprü sorularını tek tıkla kaydet; sonra doğrudan ilgili analiz adımına dön.</p>
        </div>
        <span className='bookmarkCountChip'>★ {totalCount} kayıt</span>
      </div>

      <div className='bookmarkToolbar'>
        <div className='bookmarkFilters'>
          {filters.map(item => (
            <button key={item.key} className={filter === item.key ? 'bookmarkFilterActive' : ''} onClick={() => void onFilter(item.key)}>{item.label}</button>
          ))}
        </div>
        <button className='ghost compact' onClick={() => void onRefresh()} disabled={loading}>↻ Yenile</button>
      </div>

      {error && <div className='errorBox'>{error}</div>}
      {loading ? (
        <div className='bookmarkEmpty'>Kaydedilen içerikler yenileniyor…</div>
      ) : bookmarks.length === 0 ? (
        <div className='bookmarkEmpty'>
          <div className='bigIcon'>☆</div>
          <b>{filter === 'all' ? 'Henüz yer imi yok.' : 'Bu türde kayıt yok.'}</b>
          <span>Ana tartışmada “Tartışmayı Kaydet”, İddia Radarı’nda “Kaydet” veya Köprü Oluştur’da “Köprüyü Kaydet” düğmesini kullan.</span>
        </div>
      ) : (
        <div className='bookmarkList'>
          {bookmarks.map(item => (
            <article className={`bookmarkCard ${selectedId === item.id ? 'bookmarkCardSelected' : ''}`} key={item.id} onClick={() => onSelect(item)}>
              <div className='bookmarkCardTop'>
                <span className={`bookmarkKind bookmarkKind-${item.kind}`}>{bookmarkKindIcon(item.kind)} {bookmarkKindLabel(item.kind)}</span>
                <span>{item.relative_time}</span>
              </div>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
              <div className='bookmarkCardFooter'>
                <span>Analiz adımı {typeof item.tab_index === 'number' ? item.tab_index + 1 : 1}</span>
                <div>
                  <button className='ghost compact' onClick={e => { e.stopPropagation(); void onOpen(item); }}>İlgili Analizi Aç</button>
                  <button className='ghost compact bookmarkRemove' onClick={e => { e.stopPropagation(); void onRemove(item.id, `remove-${item.id}`); }} disabled={savingKey === `remove-${item.id}`}>{savingKey === `remove-${item.id}` ? '…' : 'Kaldır'}</button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      <div className='workspaceNote bookmarkNote'>
        <b>Yer imi yalnızca saklama değil, geri dönüş noktasıdır.</b>
        <p>Her kayıt hangi tartışma ve analiz adımından geldiğini korur. Böylece kayıtlı bir iddia doğrudan İddia Radarı’na, Köprü sorusu ise Köprü Oluştur adımına geri götürür.</p>
      </div>
    </div>
  );
}

function BookmarkPanel({
  bookmark,
  opening,
  savingKey,
  onOpen,
  onRemove,
}:{
  bookmark:BookmarkItem|null;
  opening:boolean;
  savingKey:string;
  onOpen:(item:BookmarkItem)=>Promise<void>;
  onRemove:(id:number,key?:string)=>Promise<void>;
}) {
  return (
    <>
      <div className='panelHeader'>
        <div><span className='eyebrow'>N-KÖPRÜ YER İMLERİ</span><h2>Kaydedilen içerik</h2></div>
        <span className='status'>Hazır</span>
      </div>
      {!bookmark ? (
        <div className='emptyState bookmarkPanelEmpty'>
          <div className='bigIcon'>☆</div>
          <h3>Bir kayıt seç</h3>
          <p>Soldaki Yer İmleri listesinden bir kayıt seçtiğinde kaynak tartışma ve geri dönüş adımı burada görünür.</p>
        </div>
      ) : (
        <div className='moduleCard bookmarkDetailCard'>
          <div className='bookmarkDetailTop'>
            <span className={`bookmarkKind bookmarkKind-${bookmark.kind}`}>{bookmarkKindIcon(bookmark.kind)} {bookmarkKindLabel(bookmark.kind)}</span>
            <span className='bookmarkSavedChip'>★ Kaydedildi</span>
          </div>
          <h3>{bookmark.title}</h3>
          <p className='bookmarkDetailText'>{bookmark.text}</p>
          <div className='bookmarkDetailMeta'>
            <div><span>Gönderi</span><b>#{bookmark.post_id}</b></div>
            <div><span>Hedef adım</span><b>{typeof bookmark.tab_index === 'number' ? `${bookmark.tab_index + 1}. ${tabs[bookmark.tab_index] ?? 'Analiz'}` : '1. Tartışmayı Anla'}</b></div>
            <div><span>Tür</span><b>{bookmarkKindLabel(bookmark.kind)}</b></div>
          </div>
          {bookmark.comment_id != null && <div className='bookmarkSourceNote'>İlgili yorum / iddia numarası: <b>#{bookmark.comment_id}</b></div>}
          <div className='bookmarkDetailActions'>
            <button className='primary noMargin' onClick={() => void onOpen(bookmark)} disabled={opening}>{opening ? 'Analiz açılıyor…' : '→ İlgili Analizi Aç'}</button>
            <button className='ghost' onClick={() => void onRemove(bookmark.id, `panel-remove-${bookmark.id}`)} disabled={savingKey === `panel-remove-${bookmark.id}`}>{savingKey === `panel-remove-${bookmark.id}` ? 'Kaldırılıyor…' : 'Yer İmini Kaldır'}</button>
          </div>
          <small className='bookmarkSessionNote'>Yer İmleri SQLite üzerinde kalıcı saklanır ve backend yeniden başlatıldığında korunur.</small>
        </div>
      )}
    </>
  );
}

function ListWorkspace({
  lists,
  selectedId,
  loading,
  error,
  savingKey,
  onSelect,
  onRefresh,
  onCreate,
  onDelete,
}:{
  lists:TopicList[];
  selectedId:number | null;
  loading:boolean;
  error:string;
  savingKey:string;
  onSelect:(item:TopicList)=>Promise<void>;
  onRefresh:()=>Promise<void>;
  onCreate:(name:string,description:string)=>Promise<void>;
  onDelete:(listId:number)=>Promise<void>;
}) {
  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  async function createNow() {
    if (!name.trim()) return;
    await onCreate(name, description);
    setName('');
    setDescription('');
    setCreateOpen(false);
  }

  return (
    <div className='listWorkspace'>
      <div className='workspaceHero listHero'>
        <div>
          <span className='eyebrow'>N-KÖPRÜ • LİSTELER</span>
          <h2>Listeler</h2>
          <p>Tartışma, doğrulanabilir iddia ve Köprü sorularını kendi konu listelerinde topla; sonra ilgili analiz adımına tek tıkla dön.</p>
        </div>
        <span className='listCountChip'>☷ {lists.length} liste</span>
      </div>

      <div className='listToolbar'>
        <button className='primary noMargin' onClick={() => setCreateOpen(v => !v)}>＋ Yeni Liste</button>
        <button className='ghost compact' onClick={() => void onRefresh()} disabled={loading}>{loading ? 'Yenileniyor…' : '↻ Yenile'}</button>
      </div>

      {createOpen && (
        <div className='listCreateCard'>
          <div className='listCreateHeader'><b>Yeni konu listesi oluştur</b><button className='closeButton' onClick={() => setCreateOpen(false)}>×</button></div>
          <label className='fieldLabel'>Liste adı</label>
          <input className='textInput' value={name} onChange={e => setName(e.target.value)} placeholder='Örn. Yapay zekâ ve akademik etik' maxLength={120} />
          <label className='fieldLabel spaced'>Kısa açıklama</label>
          <textarea className='listDescriptionInput' value={description} onChange={e => setDescription(e.target.value)} placeholder='Bu listede hangi tartışmaları toplayacağını kısaca yaz.' maxLength={500} />
          <div className='listCreateFooter'><span>{name.trim().length}/120</span><button className='primary noMargin' onClick={() => void createNow()} disabled={!name.trim() || savingKey === 'create-list'}>{savingKey === 'create-list' ? 'Oluşturuluyor…' : 'Listeyi Oluştur'}</button></div>
        </div>
      )}

      {error && <div className='errorBox'>{error}</div>}

      {lists.length === 0 ? (
        <div className='listEmpty'><b>Henüz liste yok</b><span>“Yeni Liste” ile ilk konu listenizi oluşturabilirsiniz.</span></div>
      ) : (
        <div className='topicListCards'>
          {lists.map(item => (
            <div key={item.id} className={`topicListCard ${selectedId === item.id ? 'topicListCardSelected' : ''}`} onClick={() => void onSelect(item)}>
              <div className='topicListCardTop'><div><span className='listIcon'>☷</span><b>{item.name}</b></div><span>{item.item_count} öğe</span></div>
              <p>{item.description || 'Açıklama eklenmemiş.'}</p>
              <div className='topicListCounters'>
                <span>💬 {item.discussion_count} tartışma</span>
                <span>◇ {item.claim_count} iddia</span>
                <span>🌉 {item.bridge_count} Köprü</span>
              </div>
              <div className='topicListCardFooter'>
                <small>{item.relative_time}</small>
                <div>
                  <button className='ghost compact' onClick={e => { e.stopPropagation(); void onSelect(item); }}>Listeyi Aç</button>
                  <button className='ghost compact listDelete' onClick={e => { e.stopPropagation(); void onDelete(item.id); }} disabled={savingKey === `delete-list-${item.id}`}>{savingKey === `delete-list-${item.id}` ? 'Siliniyor…' : 'Sil'}</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className='workspaceNote listNote'>
        <b>Liste mantığı</b>
        <p>Bir içerik aynı listede ikinci kez eklenmez. Aynı tartışmayı farklı listelere ekleyebilirsin. Kayıtlar SQLite üzerinde kalıcı tutulur.</p>
      </div>
    </div>
  );
}

function ListPanel({
  detail,
  post,
  analysis,
  loading,
  error,
  sourceLoading,
  sourceError,
  savingKey,
  opening,
  onAdd,
  onPrepareSource,
  onRemove,
  onOpen,
}:{
  detail:TopicListDetail | null;
  post:Post | null;
  analysis:Analysis | null;
  loading:boolean;
  error:string;
  sourceLoading:boolean;
  sourceError:string;
  savingKey:string;
  opening:boolean;
  onAdd:(payload:{kind:BookmarkKind;post_id:number;title:string;text:string;tab_index?:number|null;comment_id?:number|null},key:string)=>Promise<void>;
  onPrepareSource:()=>Promise<void>;
  onRemove:(listId:number,itemId:number)=>Promise<void>;
  onOpen:(item:TopicListEntry)=>Promise<void>;
}) {
  const [itemFilter, setItemFilter] = useState<BookmarkKind | 'all'>('all');
  const rows = detail?.items ?? [];
  const visibleRows = itemFilter === 'all' ? rows : rows.filter(item => item.kind === itemFilter);
  const hasDiscussion = !!(detail && post && rows.some(item => item.kind === 'discussion' && item.post_id === post.id));
  const analysisMatchesPost = !!(post && analysis?.post_id === post.id);
  const sourceClaims = analysisMatchesPost ? (analysis?.claims ?? []) : [];
  const sourceBridgeQuestion = analysisMatchesPost ? (analysis?.bridge.bridge_question ?? '') : '';
  const hasBridge = !!(detail && post && sourceBridgeQuestion && rows.some(item => item.kind === 'bridge' && item.post_id === post.id && item.text === sourceBridgeQuestion));

  return (
    <>
      <div className='panelHeader'>
        <div><span className='eyebrow'>N-KÖPRÜ LİSTELER</span><h2>{detail ? detail.list.name : 'Liste ayrıntısı'}</h2></div>
        <span className='status'>Hazır</span>
      </div>

      {!detail ? (
        <div className='emptyState listPanelEmpty'>
          <div className='bigIcon'>☷</div>
          <h3>Bir liste seç</h3>
          <p>Soldaki listelerden birini seçtiğinde içerikler ve hızlı ekleme araçları burada görünür.</p>
        </div>
      ) : (
        <div className='listDetailStack'>
          <div className='moduleCard listDetailHeaderCard'>
            <div className='listDetailTitleRow'><div><span className='listIcon large'>☷</span><h3>{detail.list.name}</h3></div><span className='listSavedChip'>{detail.list.item_count} öğe</span></div>
            <p>{detail.list.description || 'Bu liste için açıklama eklenmemiş.'}</p>
            <div className='listDetailMetrics'>
              <div><strong>{detail.list.discussion_count}</strong><span>Tartışma</span></div>
              <div><strong>{detail.list.claim_count}</strong><span>İddia</span></div>
              <div><strong>{detail.list.bridge_count}</strong><span>Köprü</span></div>
            </div>
          </div>

          <div className='moduleCard listQuickAddCard'>
            <div className='listSectionHeading'><div><span className='eyebrow'>HIZLI EKLE</span><h3>Mevcut analizden ekle</h3></div></div>
            {!post ? (
              <div className='emptyMini'>Ana sayfada bir tartışma açtıktan sonra buraya içerik ekleyebilirsin.</div>
            ) : (
              <div className='listQuickAddRows'>
                <div className='listQuickRow'>
                  <div><b>💬 Tartışma</b><p>{post.text}</p></div>
                  <button className={`ghost compact ${hasDiscussion ? 'listAlreadyAdded' : ''}`} onClick={() => void onAdd({kind:'discussion',post_id:post.id,title:post.text,text:`${post.comments.length} yorum içeren tartışma`,tab_index:0},`list-discussion-${post.id}`)} disabled={hasDiscussion || !!savingKey}>{hasDiscussion ? '✓ Listede' : savingKey === `list-discussion-${post.id}` ? 'Ekleniyor…' : '＋ Ekle'}</button>
                </div>

                {sourceLoading ? (
                  <div className='listSourceState'>
                    <div><b>✦ İddia ve Köprü verileri hazırlanıyor…</b><span>Mevcut tartışma analiz edilerek doğrulanabilir iddialar ve Köprü sorusu getiriliyor.</span></div>
                  </div>
                ) : sourceError ? (
                  <div className='listSourceState listSourceStateError'>
                    <div><b>Analiz verileri hazırlanamadı</b><span>{sourceError}</span></div>
                    <button className='ghost compact' onClick={() => void onPrepareSource()}>↻ Tekrar Dene</button>
                  </div>
                ) : !analysisMatchesPost ? (
                  <div className='listSourceState'>
                    <div><b>İddia ve Köprü seçenekleri için analiz gerekli</b><span>Tartışmayı yeniden açmadan bu ekrandan hazırlayabilirsin.</span></div>
                    <button className='ghost compact' onClick={() => void onPrepareSource()}>✦ Analizi Hazırla</button>
                  </div>
                ) : (
                  <>
                    {sourceClaims.length > 0 ? sourceClaims.map(claim => {
                      const exists = rows.some(item => item.kind === 'claim' && item.post_id === post.id && item.comment_id === claim.comment_id);
                      return <div className='listQuickRow' key={`claim-${claim.comment_id}`}>
                        <div><b>◇ İddia #{claim.comment_id}</b><p>{claim.text}</p></div>
                        <button className={`ghost compact ${exists ? 'listAlreadyAdded' : ''}`} onClick={() => void onAdd({kind:'claim',post_id:post.id,title:`${post.text} • İddia #${claim.comment_id}`,text:claim.text,tab_index:3,comment_id:claim.comment_id},`list-claim-${claim.comment_id}`)} disabled={exists || !!savingKey}>{exists ? '✓ Listede' : savingKey === `list-claim-${claim.comment_id}` ? 'Ekleniyor…' : '＋ Ekle'}</button>
                      </div>;
                    }) : (
                      <div className='listQuickRow listQuickRowMuted'><div><b>◇ İddia</b><p>Bu analizde doğrulanabilir iddia adayı bulunamadı.</p></div><span>0 aday</span></div>
                    )}

                    {sourceBridgeQuestion ? (
                      <div className='listQuickRow'>
                        <div><b>🌉 Köprü Sorusu</b><p>{sourceBridgeQuestion}</p></div>
                        <button className={`ghost compact ${hasBridge ? 'listAlreadyAdded' : ''}`} onClick={() => void onAdd({kind:'bridge',post_id:post.id,title:`${post.text} • Köprü Sorusu`,text:sourceBridgeQuestion,tab_index:7},`list-bridge-${post.id}`)} disabled={hasBridge || !!savingKey}>{hasBridge ? '✓ Listede' : savingKey === `list-bridge-${post.id}` ? 'Ekleniyor…' : '＋ Ekle'}</button>
                      </div>
                    ) : (
                      <div className='listQuickRow listQuickRowMuted'><div><b>🌉 Köprü Sorusu</b><p>Bu analiz için Köprü sorusu üretilemedi.</p></div><span>Hazır değil</span></div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>

          <div className='moduleCard listItemsCard'>
            <div className='listItemsTop'>
              <div><span className='eyebrow'>LİSTE İÇERİĞİ</span><h3>Kaydedilen öğeler</h3></div>
              <div className='listItemFilters'>
                {([['all','Tümü'],['discussion','Tartışmalar'],['claim','İddialar'],['bridge','Köprüler']] as const).map(([value,label]) => <button key={value} className={itemFilter === value ? 'listItemFilterActive' : ''} onClick={() => setItemFilter(value)}>{label}</button>)}
              </div>
            </div>
            {error && <div className='errorBox'>{error}</div>}
            {loading && rows.length === 0 ? <div className='emptyMini'>Liste yükleniyor…</div> : visibleRows.length === 0 ? (
              <div className='listItemsEmpty'>Bu filtrede kayıt yok. Yukarıdaki “Hızlı Ekle” alanından içerik ekleyebilirsin.</div>
            ) : (
              <div className='listEntryRows'>
                {visibleRows.map(item => <div className='listEntryRow' key={item.id}>
                  <div className='listEntryBody'>
                    <span className={`bookmarkKind bookmarkKind-${item.kind}`}>{bookmarkKindIcon(item.kind)} {bookmarkKindLabel(item.kind)}</span>
                    <b>{item.title}</b>
                    <p>{item.text}</p>
                    <small>Analiz adımı {typeof item.tab_index === 'number' ? item.tab_index + 1 : 1} • {item.relative_time}</small>
                  </div>
                  <div className='listEntryActions'>
                    <button className='ghost compact' onClick={() => void onOpen(item)} disabled={opening}>{opening ? 'Açılıyor…' : 'İlgili Analizi Aç'}</button>
                    <button className='ghost compact listDelete' onClick={() => void onRemove(detail.list.id,item.id)} disabled={savingKey === `remove-item-${item.id}`}>{savingKey === `remove-item-${item.id}` ? 'Çıkarılıyor…' : 'Çıkar'}</button>
                  </div>
                </div>)}
              </div>
            )}
            <small className='listSessionNote'>Listeler ve içlerindeki öğeler SQLite üzerinde kalıcı saklanır.</small>
          </div>
        </div>
      )}
    </>
  );
}


function technicalPercent(value:number) {
  return `%${(value * 100).toLocaleString('tr-TR', {maximumFractionDigits:1})}`;
}

function technicalDuration(value:number) {
  if (value >= 1000) return formatDuration(value);
  return `${value.toLocaleString('tr-TR', {maximumFractionDigits:value < 1 ? 2 : 1})} ms`;
}

function technicalCount(value:number | null) {
  return value === null ? 'Ölçülmedi' : value.toLocaleString('tr-TR');
}

function technicalLabelShort(label:string) {
  if (label === 'Destekleyen') return 'Destek';
  if (label === 'Karşı / Sınırlayıcı') return 'Sınır';
  if (label === 'Koşullu / Dengeli') return 'Koşul';
  if (label === 'Soru / Tarafsız') return 'Soru';
  return label;
}

function TechnicalWorkspace({
  status,
  result,
  scenarioResult,
  currentPost,
  currentAnalysis,
  loading,
  running,
  scenarioRunning,
  error,
  onRefresh,
  onRun,
  onRunScenarios,
}:{
  status:TechnicalStatus | null;
  result:TechnicalEvaluation | null;
  scenarioResult:TechnicalScenarioEvaluation | null;
  currentPost:Post | null;
  currentAnalysis:Analysis | null;
  loading:boolean;
  running:boolean;
  scenarioRunning:boolean;
  error:string;
  onRefresh:()=>Promise<void>;
  onRun:()=>Promise<void>;
  onRunScenarios:()=>Promise<void>;
}) {
  const model = result?.model_status ?? status?.model_status ?? null;
  const hardware = result?.hardware ?? status?.hardware ?? null;
  const liveAnalysis = currentPost && currentAnalysis?.post_id === currentPost.id ? currentAnalysis : null;
  const busy = running || scenarioRunning;
  return (
    <div className='navWorkspace technicalWorkspace'>
      <div className='workspaceHero technicalHero'>
        <div>
          <span className='eyebrow'>N-KÖPRÜ • GERÇEK TEKNİK KANIT</span>
          <h2>Teknik Doğrulama</h2>
          <p>Referans performansı ve farklı konulardaki görüş başarısını birbirine karıştırmadan gerçekten ölç.</p>
        </div>
        <span className='technicalLiveChip'>● Gerçek ölçüm</span>
      </div>

      {error && <div className='errorBox'>{error}</div>}

      <div className='technicalRunCard'>
        <div>
          <b>Çalıştırılabilir değerlendirme</b>
          <span>{status?.dataset.sample_count ?? 20} elle etiketli cümle • {status?.dataset.label_count ?? 4} görüş sınıfı • 5 gerçek analiz tekrarı</span>
        </div>
        <div className='technicalRunActions'>
          <button className='ghost compact' onClick={() => void onRefresh()} disabled={loading || busy}>↻ Yenile</button>
          <button className='primary compact noMargin' onClick={() => void onRun()} disabled={loading || busy}>
            {running ? 'Gerçek ölçüm çalışıyor…' : '▶ Gerçek Ölçümü Başlat'}
          </button>
        </div>
      </div>

      <div className='technicalScenarioCard'>
        <div className='technicalSectionHeading'>
          <div><span className='eyebrow'>GENİŞLETİLMİŞ PROJE İÇİ DOĞRULAMA</span><h3>Çok senaryolu görüş testi</h3></div>
          <span className='technicalScenarioCount'>{status?.scenario_dataset.scenario_count ?? 4} konu · {status?.scenario_dataset.sample_count ?? 80} örnek</span>
        </div>
        <p>Yapay zekâ, okulda telefon, kampüs ulaşımı ve uzaktan çalışma; her konuda dört görüş sınıfı dengeli değerlendirilir.</p>
        <div className='technicalScenarioTags'>
          {(status?.scenario_dataset.scenarios ?? []).map(scenario => <span key={scenario.key}>{scenario.topic}</span>)}
        </div>
        <button className='primary compact noMargin technicalScenarioButton' onClick={() => void onRunScenarios()} disabled={loading || busy}>
          {scenarioRunning ? '80 örnek gerçekten değerlendiriliyor…' : '▶ Çok Senaryolu Doğrulamayı Başlat'}
        </button>
        {scenarioResult ? <>
          <div className='technicalScenarioScoreGrid'>
            <div><strong>{technicalPercent(scenarioResult.accuracy)}</strong><span>Çok konu doğruluğu</span><small>{scenarioResult.correct_count}/{scenarioResult.sample_count} doğru</small></div>
            <div><strong>{technicalPercent(scenarioResult.macro_f1)}</strong><span>Çok konu Macro-F1</span><small>{scenarioResult.dataset.label_count} dengeli sınıf</small></div>
            <div><strong>{scenarioResult.error_count}</strong><span>Gerçek sınıflandırma hatası</span><small>Hatalar sağ panelde açıkça gösterilir</small></div>
            <div><strong>{scenarioResult.transformer_inference_count}</strong><span>Gerçek görüş çıkarımı</span><small>{scenarioResult.structural_decision_count} yapısal karar</small></div>
          </div>
          <div className='technicalTopicSummary'>
            {scenarioResult.scenarios.map(scenario => <div key={scenario.key}>
              <span>{scenario.topic}</span><strong>{technicalPercent(scenario.accuracy)}</strong><small>{scenario.correct_count}/{scenario.sample_count}</small>
            </div>)}
          </div>
          <small>{scenarioResult.engine_note}</small>
        </> : <small>Sonuçlar önceden yazılmaz; 80 cümle ancak düğmeye bastığında mevcut görüş motoruyla sınıflandırılır.</small>}
      </div>

      {currentPost && <div className='technicalLiveDiscussionCard'>
        <div className='technicalSectionHeading'>
          <div><span className='eyebrow'>REFERANS TESTTEN AYRI GERÇEK İÇERİK</span><h3>Aktif kullanıcı tartışması</h3></div>
          <span className='technicalLiveChip'>● Canlı içerik</span>
        </div>
        <p>{currentPost.text}</p>
        <div className='technicalLiveMetrics'>
          <span><b>{currentPost.comments.length}</b> gerçek yorum</span>
          {liveAnalysis && <span><b>{liveAnalysis.indicators.comment_count ?? liveAnalysis.stance_details.length}</b> benzersiz yorum</span>}
          {liveAnalysis && <span><b>{liveAnalysis.claims.length}</b> iddia adayı</span>}
          {liveAnalysis && <span><b>{liveAnalysis.unanswered_questions.length}</b> soru</span>}
        </div>
        <small>Kullanıcı yorumları elle etiketlenmediği için bunlara doğruluk veya F1 skoru uydurulmaz; 80 etiketli senaryoya dahil edilmez.</small>
      </div>}

      {loading && !status ? (
        <div className='technicalEmpty'>Teknik doğrulama durumu yükleniyor…</div>
      ) : !result ? (
        <div className='technicalEmpty'>
          <b>Henüz ölçüm yapılmadı.</b>
          <span>Değerler önceden yazılmaz. Başlat düğmesine bastığında mevcut analiz motoru gerçekten çalıştırılır.</span>
        </div>
      ) : (
        <>
          <div className='technicalMetricGrid'>
            <div><strong>{technicalPercent(result.accuracy)}</strong><span>İç set doğruluğu</span><small>{result.correct_count}/{result.sample_count} doğru</small></div>
            <div><strong>{technicalPercent(result.macro_f1)}</strong><span>İç set Macro-F1</span><small>{result.dataset.label_count} eşit sınıf</small></div>
            <div><strong>{formatDuration(result.latency.median_ms)}</strong><span>Medyan analiz</span><small>{result.latency.iterations} gerçek tekrar</small></div>
            <div><strong>{formatDuration(result.latency.p95_ms)}</strong><span>P95 gecikme</span><small>{result.latency.unique_comment_count} benzersiz yorum</small></div>
          </div>

          {result.cache_profile.available && <div className='technicalCacheCard'>
            <div className='technicalSectionHeading'>
              <div><span className='eyebrow'>DONANIMDAN BAĞIMSIZ İYİLEŞTİRME</span><h3>İlk analiz ve tekrar analizi</h3></div>
              {result.cache_profile.speedup_factor !== null && <span className='technicalCacheSpeedup'>
                {result.cache_profile.speedup_factor.toLocaleString('tr-TR', {maximumFractionDigits:1})}× tekrar hızı
              </span>}
            </div>
            <div className='technicalCacheComparison'>
              <div><span>İlk analiz · soğuk</span><strong>{result.cache_profile.cold_ms === null ? 'Ölçülmedi' : formatDuration(result.cache_profile.cold_ms)}</strong><small>{technicalCount(result.model_usage.demo.cold_claim_transformer_count)} yeni İddia Radarı çıkarımı</small></div>
              <div><span>Tekrar analiz · sıcak</span><strong>{result.cache_profile.warm_median_ms === null ? 'Ölçülmedi' : formatDuration(result.cache_profile.warm_median_ms)}</strong><small>{technicalCount(result.model_usage.demo.warm_claim_cache_hit_total)} yeniden kullanılan model kararı</small></div>
            </div>
            <p>Aynı model sonucu tekrar hesaplanmaz; yalnızca değişen yorum yeni çıkarım gerektirir.</p>
          </div>}

          <div className='technicalEngineCard'>
            <div className='technicalSectionHeading'>
              <div><span className='eyebrow'>MOTOR ŞEFFAFLIĞI</span><h3>Ölçüm gerçekten nasıl çalıştı?</h3></div>
              <span className={result.effective_ai ? 'technicalModeChip hybrid' : 'technicalModeChip fallback'}>
                {result.effective_ai ? 'Hibrit motor' : 'Heuristik yedek'}
              </span>
            </div>
            <div className='technicalEngineMetrics'>
              <span><b>{result.structural_decision_count}</b> yapısal karar</span>
              <span><b>{result.transformer_inference_count}</b> iç set görüş çıkarımı</span>
              <span>Model: <b>{model?.loaded ? 'Hazır' : 'Yüklenmedi'}</b></span>
              <span>Cihaz: <b>{model?.device ?? 'cpu'}</b></span>
            </div>
            <div className='technicalExecutionSplit'>
              <div>
                <span>İç doğrulama seti</span>
                <strong>{technicalCount(result.model_usage.internal_set.stance_transformer_count)} görüş çıkarımı</strong>
                <small>{technicalCount(result.model_usage.internal_set.claim_transformer_count)} İddia Radarı çıkarımı</small>
              </div>
              <div>
                <span>Demo · analiz başına</span>
                <strong>{technicalCount(result.model_usage.demo.stance_transformer_per_run)} görüş çıkarımı</strong>
                <small>{technicalCount(result.model_usage.demo.claim_transformer_per_run)} yeni İddia Radarı çıkarımı</small>
                {result.model_usage.demo.claim_cache_hit_total !== null && <small>{technicalCount(result.model_usage.demo.claim_cache_hit_total)} toplam önbellek isabeti</small>}
              </div>
            </div>
            {result.model_usage.demo.claim_transformer_comment_ids.length > 0 && <div className='technicalModelEvidence'>
              Demo İddia Radarı model yorumu: {result.model_usage.demo.claim_transformer_comment_ids.map(id => `#${id}`).join(', ')}
              {' '}• {technicalCount(result.model_usage.demo.claim_transformer_total)} çıkarım / {result.model_usage.demo.iterations} tekrar
              {result.model_usage.demo.claim_cache_comment_ids.length > 0 && <>{' '}• önbellekten: {result.model_usage.demo.claim_cache_comment_ids.map(id => `#${id}`).join(', ')}</>}
            </div>}
            {result.engine_note && <p>{result.engine_note}</p>}
            <small>{result.model_usage.note}</small>
            <small>{model?.model ?? 'Model bilgisi alınamadı'}</small>
          </div>

          {hardware && <div className='technicalHardwareCard'>
            <div className='technicalSectionHeading'>
              <div><span className='eyebrow'>ÇALIŞMA ORTAMI</span><h3>CPU / CUDA durumu</h3></div>
              <span className={hardware.acceleration_active ? 'technicalModeChip hybrid' : 'technicalModeChip fallback'}>
                {hardware.acceleration_active ? 'GPU etkin' : 'CPU kullanımı'}
              </span>
            </div>
            <div className='technicalHardwareGrid'>
              <div><span>PyTorch</span><strong>{hardware.torch_version ?? 'Kurulu değil'}</strong></div>
              <div><span>CUDA derlemesi</span><strong>{hardware.cuda_build_version ?? 'Bulunamadı'}</strong></div>
              <div><span>CUDA erişimi</span><strong>{hardware.cuda_available ? 'Kullanılabilir' : 'Kullanılamıyor'}</strong></div>
              <div><span>Aktif cihaz</span><strong>{hardware.active_device}</strong></div>
            </div>
            {hardware.cuda_device_name && <div className='technicalHardwareGpu'>Doğrulanan CUDA aygıtı: {hardware.cuda_device_name}</div>}
            <p>{hardware.diagnosis}</p>
          </div>}

          <div className='technicalInvariantCard'>
            <div className='technicalSectionHeading'>
              <div><span className='eyebrow'>ÜRÜN DAVRANIŞI</span><h3>Demo değişmezleri</h3></div>
              <span className='technicalPassed'>{result.passed_invariant_count}/{result.invariant_count} geçti</span>
            </div>
            <div className='technicalInvariantList'>
              {result.invariants.map(item => (
                <div className={item.passed ? 'technicalInvariantRow pass' : 'technicalInvariantRow fail'} key={item.key}>
                  <span>{item.passed ? '✓' : '!'}</span>
                  <div><b>{item.label}</b><small>Beklenen: {item.expected}</small></div>
                  <strong>{item.actual}</strong>
                </div>
              ))}
            </div>
          </div>

          <div className='technicalScopeNote'>
            <b>Ölçüm kapsamı ve dürüstlük sınırı</b>
            <p>{result.dataset.limitation}</p>
            <p>{result.isolation_note}</p>
            <small>Son ölçüm: {new Date(result.created_at).toLocaleString('tr-TR')} • SQLite üzerinde saklanır.</small>
          </div>
        </>
      )}
    </div>
  );
}

function TechnicalPanel({result, scenarioResult, loading, running}:{
  result:TechnicalEvaluation | null;
  scenarioResult:TechnicalScenarioEvaluation | null;
  loading:boolean;
  running:boolean;
}) {
  const labels = result?.class_metrics.map(item => item.label) ?? [];
  const additionalLabels = result ? Array.from(new Set(result.confusion_matrix.flatMap(item => Object.keys(item.predicted_counts)).filter(label => !labels.includes(label)))) : [];
  const predictedLabels = [...labels, ...additionalLabels];
  const scenarioLabels = scenarioResult?.class_metrics.map(item => item.label) ?? [];
  const additionalScenarioLabels = scenarioResult ? Array.from(new Set(scenarioResult.confusion_matrix.flatMap(item => Object.keys(item.predicted_counts)).filter(label => !scenarioLabels.includes(label)))) : [];
  const scenarioPredictedLabels = [...scenarioLabels, ...additionalScenarioLabels];

  return (
    <>
      <div className='panelHeader'>
        <div><span className='eyebrow'>ŞEFFAF YEREL DEĞERLENDİRME</span><h2>Ölçüm Ayrıntıları</h2></div>
        <span className={result || scenarioResult ? 'status good' : 'status'}>{running ? '● Ölçülüyor' : result || scenarioResult ? '● Ölçüldü' : 'Bekliyor'}</span>
      </div>

      {!result && !scenarioResult ? (
        <div className='emptyState'>
          <div className='bigIcon'>◫</div>
          <h3>{loading ? 'Ölçüm geçmişi okunuyor' : running ? 'Gerçek analiz çalıştırılıyor' : 'Henüz ölçüm sonucu yok'}</h3>
          <p>Gecikme örnekleri, sınıf bazlı skorlar ve hata matrisi ölçüm tamamlanınca burada görünür.</p>
        </div>
      ) : (
        <div className='technicalPanelStack'>
          {scenarioResult && <>
            <div className='moduleCard technicalScenarioDetailCard'>
              <div className='technicalSectionHeading'>
                <div><span className='eyebrow'>DÖRT KONU · PROJE İÇİ ELLE ETİKETLİ SET</span><h3>Çok senaryolu gerçek sonuç</h3></div>
                <span className='technicalScenarioCount'>{scenarioResult.correct_count}/{scenarioResult.sample_count} doğru</span>
              </div>
              <div className='technicalScenarioScoreGrid'>
                <div><strong>{technicalPercent(scenarioResult.accuracy)}</strong><span>Genel doğruluk</span></div>
                <div><strong>{technicalPercent(scenarioResult.macro_f1)}</strong><span>Macro-F1</span></div>
                {scenarioResult.difficulty_metrics.map(metric => <div key={metric.key}><strong>{technicalPercent(metric.accuracy)}</strong><span>{metric.label}</span><small>{metric.correct_count}/{metric.sample_count}</small></div>)}
              </div>
              <div className='technicalLiveMetrics'>
                <span><b>{scenarioResult.structural_decision_count}</b> yapısal karar</span>
                <span><b>{scenarioResult.transformer_inference_count}</b> gerçek Transformer çıkarımı</span>
                <span><b>{formatDuration(scenarioResult.elapsed_ms)}</b> toplam</span>
              </div>
              <small>{scenarioResult.dataset.limitation}</small>
            </div>

            <div className='moduleCard technicalScenarioTopicsCard'>
              <div className='technicalSectionHeading'><div><span className='eyebrow'>KONU BAZINDA AYRI ÖLÇÜM</span><h3>Her tartışma başlığında başarı</h3></div></div>
              <div className='technicalTopicCards'>
                {scenarioResult.scenarios.map(scenario => <details className='technicalTopicCard' key={scenario.key}>
                  <summary><div><b>{scenario.topic}</b><small>{scenario.title}</small></div><strong>{technicalPercent(scenario.accuracy)}</strong></summary>
                  <p>{scenario.correct_count}/{scenario.sample_count} doğru • Macro-F1 {technicalPercent(scenario.macro_f1)} • {scenario.error_count} gerçek hata</p>
                  <div className='technicalTopicClasses'>{scenario.class_metrics.map(item => <span key={item.label}>{technicalLabelShort(item.label)}: {technicalPercent(item.f1)}</span>)}</div>
                  <small>{scenario.transformer_inference_count} model çıkarımı • {scenario.structural_decision_count} yapısal karar • {formatDuration(scenario.elapsed_ms)}</small>
                </details>)}
              </div>
            </div>

            <div className='moduleCard technicalMatrixCard'>
              <div className='technicalSectionHeading'><div><span className='eyebrow'>80 ÖRNEK · DÖRT BAŞLIK</span><h3>Çok senaryolu karışıklık matrisi</h3></div></div>
              <div className='technicalMatrixScroll'>
                <table className='technicalMatrix'>
                  <thead><tr><th>Beklenen ↓ / Tahmin →</th>{scenarioPredictedLabels.map(label => <th key={label} title={label}>{technicalLabelShort(label)}</th>)}</tr></thead>
                  <tbody>{scenarioResult.confusion_matrix.map(row => <tr key={row.expected_label}><th>{technicalLabelShort(row.expected_label)}</th>{scenarioPredictedLabels.map(label => <td className={label === row.expected_label ? 'diagonal' : ''} key={label}>{row.predicted_counts[label] ?? 0}</td>)}</tr>)}</tbody>
                </table>
              </div>
              <small>Beklenen etiketler proje içi el ile belirlendi; her hücre gerçek tahminlerden hesaplanır.</small>
            </div>

            <div className='moduleCard technicalClassCard'>
              <div className='technicalSectionHeading'><div><span className='eyebrow'>GENİŞLETİLMİŞ DENGELİ SET</span><h3>80 örnekte sınıf başarısı</h3></div></div>
              <div className='technicalClassList'>{scenarioResult.class_metrics.map(item => <div className='technicalClassRow' key={item.label}><div><b>{item.label}</b><small>{item.support} etiketli örnek</small></div><div><span>P {technicalPercent(item.precision)}</span><span>R {technicalPercent(item.recall)}</span><strong>F1 {technicalPercent(item.f1)}</strong></div></div>)}</div>
            </div>

            <details className='moduleCard technicalPredictionCard technicalScenarioErrors' open={scenarioResult.error_count > 0}>
              <summary><span>Gerçek sınıflandırma hataları</span><small>{scenarioResult.error_count} hata · gizlenmez</small></summary>
              {scenarioResult.errors.length > 0 ? <div className='technicalPredictionList'>
                {scenarioResult.errors.map(item => <div className='technicalPrediction fail' key={item.id}>
                  <div><b>! {item.scenario_topic}</b><span>{item.challenge} · {item.difficulty}</span></div>
                  <p>{item.text}</p>
                  <small>Beklenen: <b>{item.expected_label}</b> • Gerçek tahmin: <b>{item.predicted_label}</b></small>
                  <small>{item.model_confidence === null ? 'Yapısal karar' : `%${Math.round(item.model_confidence * 100)} model güveni`}</small>
                </div>)}
              </div> : <p>Bu çalıştırmada 80 proje içi örnekte sınıflandırma hatası bulunmadı; bu sonuç bağımsız başarı iddiası değildir.</p>}
            </details>
          </>}

          {result && <>
          <div className='moduleCard technicalLatencyCard'>
            <div className='technicalSectionHeading'><div><span className='eyebrow'>GERÇEK ÇALIŞTIRMA SÜRESİ</span><h3>{result.latency.iterations} analiz tekrarı</h3></div></div>
            <div className='technicalLatencyGrid'>
              <div><b>{formatDuration(result.latency.minimum_ms)}</b><span>En hızlı</span></div>
              <div><b>{formatDuration(result.latency.mean_ms)}</b><span>Ortalama</span></div>
              <div><b>{formatDuration(result.latency.maximum_ms)}</b><span>En yavaş</span></div>
            </div>
            <div className='technicalSampleChips'>{result.latency.samples_ms.map((value, index) => <span className={index === 0 && result.cache_profile.available ? 'technicalColdSample' : ''} key={`${index}-${value}`}>#{index + 1} · {formatDuration(value)}{result.cache_profile.available ? index === 0 ? ' · soğuk' : ' · sıcak' : ''}</span>)}</div>
            <small>{result.latency.raw_comment_count} ham yorum → {result.latency.unique_comment_count} benzersiz yorum • Yaklaşık {result.latency.estimated_comments_per_second.toLocaleString('tr-TR')} yorum/sn</small>
          </div>

          {result.cache_profile.available && <div className='moduleCard technicalCacheDetailCard'>
            <div className='technicalSectionHeading'>
              <div><span className='eyebrow'>GERÇEK ÖNBELLEK DAVRANIŞI</span><h3>Ne kadar model işi önlendi?</h3></div>
              <span className='technicalCacheHits'>{technicalCount(result.cache_profile.avoided_model_inference_count)} çıkarım önlendi</span>
            </div>
            <div className='technicalCacheStats'>
              <div><b>{technicalCount(result.cache_profile.hit_total)}</b><span>Önbellek isabeti</span></div>
              <div><b>{technicalCount(result.cache_profile.miss_total)}</b><span>Yeni model çıkarımı</span></div>
              <div><b>{result.cache_profile.hit_rate_percent === null ? 'Ölçülmedi' : `%${result.cache_profile.hit_rate_percent.toLocaleString('tr-TR', {maximumFractionDigits:1})}`}</b><span>Yeniden kullanım</span></div>
            </div>
            <small>{result.cache_profile.note}</small>
          </div>}

          <div className='moduleCard technicalProfileCard'>
            <div className='technicalSectionHeading'>
              <div><span className='eyebrow'>GERÇEK KATMAN SÜRELERİ</span><h3>Analiz süresi nereye gidiyor?</h3></div>
              {result.stage_profile.bottleneck && <span className='technicalBottleneckChip'>Darboğaz: {result.stage_profile.bottleneck.label}</span>}
            </div>
            {result.stage_profile.available ? <>
              <div className='technicalStageList'>
                {result.stage_profile.stages.map(stage => <div className={stage.key === result.stage_profile.bottleneck?.key ? 'technicalStageRow bottleneck' : 'technicalStageRow'} key={stage.key}>
                  <div><b>{stage.label}</b><strong>{technicalDuration(stage.median_ms)}</strong></div>
                  {stage.cold_ms !== null && stage.warm_median_ms !== null && <div className='technicalStageThermal'><span>İlk: {technicalDuration(stage.cold_ms)}</span><span>Tekrar: {technicalDuration(stage.warm_median_ms)}</span></div>}
                  <div className='technicalStageTrack'><span style={{width:`${Math.min(100, stage.share_of_total_percent)}%`}} /></div>
                  <div><small>Toplamın %{stage.share_of_total_percent.toLocaleString('tr-TR', {maximumFractionDigits:1})}</small>{stage.transformer_inference_total > 0 && <small>{stage.transformer_inference_total} gerçek çıkarım / {result.stage_profile.iterations} tekrar</small>}</div>
                  {(stage.cache_hit_total ?? 0) > 0 && <small className='technicalStageCache'>{stage.cache_hit_total} model sonucu önbellekten kullanıldı</small>}
                </div>)}
              </div>
              {result.stage_profile.cold_bottleneck && <div className='technicalColdBottleneck'>İlk analiz darboğazı: <b>{result.stage_profile.cold_bottleneck.label}</b> · {technicalDuration(result.stage_profile.cold_bottleneck.cold_ms ?? 0)}</div>}
              <div className='technicalProfileOverhead'>Hazırlık ve diğer işlemler: <b>{technicalDuration(result.stage_profile.overhead_median_ms)}</b></div>
            </> : <div className='technicalProfileLegacy'>Eski ölçümde katman süreleri bulunmuyor. Gerçek ölçümü yeniden başlat.</div>}
            <small>{result.stage_profile.note}</small>
          </div>

          <div className='moduleCard technicalMatrixCard'>
            <div className='technicalSectionHeading'><div><span className='eyebrow'>ELLE ETİKETLENMİŞ İÇ SET</span><h3>Hata / karışıklık matrisi</h3></div></div>
            <div className='technicalMatrixScroll'>
              <table className='technicalMatrix'>
                <thead><tr><th>Beklenen ↓ / Tahmin →</th>{predictedLabels.map(label => <th key={label} title={label}>{technicalLabelShort(label)}</th>)}</tr></thead>
                <tbody>
                  {result.confusion_matrix.map(row => <tr key={row.expected_label}>
                    <th>{technicalLabelShort(row.expected_label)}</th>
                    {predictedLabels.map(label => <td className={label === row.expected_label ? 'diagonal' : ''} key={label}>{row.predicted_counts[label] ?? 0}</td>)}
                  </tr>)}
                </tbody>
              </table>
            </div>
            <small>Her satır gerçek etiketi, her sütun uygulamanın o anda ürettiği tahmini gösterir.</small>
          </div>

          <div className='moduleCard technicalClassCard'>
            <div className='technicalSectionHeading'><div><span className='eyebrow'>SINIF BAZINDA ÖLÇÜM</span><h3>Precision / Recall / F1</h3></div></div>
            <div className='technicalClassList'>
              {result.class_metrics.map(item => <div className='technicalClassRow' key={item.label}>
                <div><b>{item.label}</b><small>{item.support} etiketli örnek</small></div>
                <div><span>P {technicalPercent(item.precision)}</span><span>R {technicalPercent(item.recall)}</span><strong>F1 {technicalPercent(item.f1)}</strong></div>
              </div>)}
            </div>
          </div>

          <details className='moduleCard technicalPredictionCard'>
            <summary><span>{result.sample_count} etiketli cümle ve gerçek tahmin</span><small>Aç / kapat</small></summary>
            <div className='technicalPredictionList'>
              {result.predictions.map(item => <div className={item.correct ? 'technicalPrediction pass' : 'technicalPrediction fail'} key={item.id}>
                <div><b>{item.correct ? '✓' : '!'} Örnek #{item.id}</b><span>{item.model_confidence === null ? 'Yapısal karar' : `%${Math.round(item.model_confidence * 100)} model güveni`}</span></div>
                <p>{item.text}</p>
                <small>Beklenen: <b>{item.expected_label}</b> • Tahmin: <b>{item.predicted_label}</b></small>
              </div>)}
            </div>
          </details>

          <div className='technicalPanelDisclaimer'>Bu ekran dış veri seti sonucu, bilimsel genelleme veya bağımsız model başarısı iddiası değildir.</div>
          </>}
        </div>
      )}
    </>
  );
}

function ProfileWorkspace({
  profile,
  loading,
  saving,
  error,
  selectedHistoryId,
  opening,
  onRefresh,
  onSelectHistory,
  onOpenHistory,
  onSave,
}:{
  profile:ProfileResponse | null;
  loading:boolean;
  saving:boolean;
  error:string;
  selectedHistoryId:number | null;
  opening:boolean;
  onRefresh:()=>Promise<void>;
  onSelectHistory:(historyId:number)=>Promise<void>;
  onOpenHistory:(item:AnalysisHistoryItem)=>Promise<void>;
  onSave:(payload:{display_name:string;handle:string;bio:string})=>Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [handle, setHandle] = useState('');
  const [bio, setBio] = useState('');

  useEffect(() => {
    if (!profile) return;
    setDisplayName(profile.user.display_name);
    setHandle(profile.user.handle);
    setBio(profile.user.bio);
  }, [profile]);

  const stats = profile?.stats;
  return (
    <div className='navWorkspace profileWorkspace'>
      <div className='workspaceHero profileHero'>
        <div>
          <span className='eyebrow'>N-KÖPRÜ • KALICI PROFİL</span>
          <h2>Profil</h2>
          <p>Analiz geçmişin, kayıtların ve çalışma istatistiklerin artık SQLite üzerinde kalıcı olarak tutulur.</p>
        </div>
        <span className='profileStorageChip'>● SQLite • Kalıcı</span>
      </div>

      {error && <div className='errorBox'>{error}</div>}
      {!profile && loading ? (
        <div className='profileLoading'>Profil ve analiz geçmişi yükleniyor…</div>
      ) : !profile ? (
        <div className='profileLoading'><b>Profil yüklenemedi.</b><button className='ghost compact' onClick={() => void onRefresh()}>↻ Tekrar Dene</button></div>
      ) : (
        <>
          <div className='profileIdentityCard'>
            <div className='profileAvatar'>{profile.user.display_name.slice(0,2).toUpperCase()}</div>
            {!editing ? (
              <div className='profileIdentityBody'>
                <div className='profileNameRow'><div><h3>{profile.user.display_name}</h3><span>{profile.user.handle}</span></div><button className='ghost compact' onClick={() => setEditing(true)}>Profili Düzenle</button></div>
                <p>{profile.user.bio || 'Profil açıklaması eklenmemiş.'}</p>
              </div>
            ) : (
              <div className='profileEditForm'>
                <div className='profileEditGrid'>
                  <label><span>Görünen ad</span><input className='textInput' value={displayName} onChange={e => setDisplayName(e.target.value)} /></label>
                  <label><span>Kullanıcı adı</span><input className='textInput' value={handle} onChange={e => setHandle(e.target.value)} /></label>
                </div>
                <label><span>Kısa açıklama</span><textarea value={bio} onChange={e => setBio(e.target.value)} /></label>
                <div className='profileEditActions'>
                  <button className='primary compact' disabled={saving || !displayName.trim()} onClick={async () => { await onSave({display_name:displayName,handle,bio}); setEditing(false); }}>{saving ? 'Kaydediliyor…' : 'Kaydet'}</button>
                  <button className='ghost compact' disabled={saving} onClick={() => { setDisplayName(profile.user.display_name); setHandle(profile.user.handle); setBio(profile.user.bio); setEditing(false); }}>Vazgeç</button>
                </div>
              </div>
            )}
          </div>

          <div className='profileStatsGrid'>
            <div><strong>{stats?.analysis_count ?? 0}</strong><span>Toplam analiz</span></div>
            <div><strong>{stats?.unique_discussions ?? 0}</strong><span>Farklı tartışma</span></div>
            <div><strong>{stats?.bookmark_count ?? 0}</strong><span>Yer imi</span></div>
            <div><strong>{stats?.saved_bridge_count ?? 0}</strong><span>Kayıtlı Köprü</span></div>
            <div><strong>{stats?.list_count ?? 0}</strong><span>Liste</span></div>
            <div><strong>{stats?.list_item_count ?? 0}</strong><span>Liste öğesi</span></div>
            <div><strong>{stats?.sent_message_count ?? 0}</strong><span>Gönderilen mesaj</span></div>
            <div><strong>{stats?.notification_count ?? 0}</strong><span>Aktif bildirim</span></div>
          </div>

          <div className='profileHistoryCard'>
            <div className='profileSectionTop'>
              <div><span className='eyebrow'>ANALİZ GEÇMİŞİ</span><h3>Son analizler</h3><p>Her analiz bağımsız bir anlık görüntü olarak saklanır. Geçmiş kaydı açmak yeni analiz çalıştırmaz.</p></div>
              <button className='ghost compact' onClick={() => void onRefresh()} disabled={loading}>↻ Yenile</button>
            </div>
            {profile.recent_analyses.length === 0 ? (
              <div className='profileHistoryEmpty'><b>Henüz analiz geçmişi yok.</b><span>Ana sayfada ilk tartışmayı analiz ettiğinde burada görünecek.</span></div>
            ) : (
              <div className='profileHistoryList'>
                {profile.recent_analyses.map(item => (
                  <div className={`profileHistoryRow ${selectedHistoryId === item.id ? 'profileHistorySelected' : ''}`} key={item.id} role='button' tabIndex={0} onClick={() => void onSelectHistory(item.id)} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); void onSelectHistory(item.id); } }}>
                    <div className='profileHistoryMain'>
                      <div><span className='historyId'>#{item.id}</span><b>{item.title}</b></div>
                      <p>{item.comment_count} yorum • {item.viewpoint_count} görüş • {item.claim_count} iddia • {item.question_count} soru</p>
                      <small>{item.relative_time} • {item.engine_mode || 'analiz motoru'}</small>
                    </div>
                    <div className='profileHistoryActions'>
                      <span className='historyChanges'>{item.changed_count} değişim notu</span>
                      <button className='ghost compact' onClick={e => { e.stopPropagation(); void onOpenHistory(item); }} disabled={opening}>{opening ? 'Açılıyor…' : 'Anlık Görüntüyü Aç'}</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className='profilePersistenceNote'>
            <b>Kalıcı veri katmanı aktif</b>
            <p>Bildirimler, mesajlar, yer imleri, listeler, özel tartışmalar ve analiz geçmişi backend yeniden başlatıldığında korunur. Yerel SQLite dosyası <code>backend/data/nkopru.db</code> altında oluşturulur.</p>
          </div>
        </>
      )}
    </div>
  );
}

function ProfilePanel({detail, loading, opening, onOpen}:{
  detail:AnalysisHistoryDetail | null;
  loading:boolean;
  opening:boolean;
  onOpen:(item:AnalysisHistoryItem)=>Promise<void>;
}) {
  return (
    <>
      <div className='panelHeader'>
        <div><span className='eyebrow'>ANALİZ GEÇMİŞİ</span><h2>{detail ? `Anlık Görüntü #${detail.item.id}` : 'Geçmiş ayrıntısı'}</h2></div>
        <span className='status good'>● Kalıcı</span>
      </div>
      {loading ? (
        <div className='emptyState'><div className='bigIcon'>⟳</div><h3>Geçmiş kayıt yükleniyor</h3></div>
      ) : !detail ? (
        <div className='emptyState'><div className='bigIcon'>◷</div><h3>Bir analiz seç</h3><p>Profildeki geçmiş kayıtlarından birini seçtiğinde kaydedilmiş analiz anlık görüntüsü burada açılır.</p></div>
      ) : (
        <div className='profileDetailStack'>
          <div className='moduleCard profileSnapshotCard'>
            <span className='eyebrow'>{detail.item.relative_time} • POST #{detail.item.post_id}</span>
            <h3>{detail.item.title}</h3>
            <p>{detail.analysis.short_summary}</p>
            <div className='profileSnapshotMetrics'>
              <div><strong>{detail.item.comment_count}</strong><span>Yorum</span></div>
              <div><strong>{detail.item.viewpoint_count}</strong><span>Görüş</span></div>
              <div><strong>{detail.item.claim_count}</strong><span>İddia</span></div>
              <div><strong>{detail.item.question_count}</strong><span>Soru</span></div>
            </div>
            <button className='primary' onClick={() => void onOpen(detail.item)} disabled={opening}>{opening ? 'Açılıyor…' : 'Bu Analiz Anlık Görüntüsünü Aç'}</button>
          </div>

          <div className='moduleCard profileChangesCard'>
            <span className='eyebrow'>BEN YOKKEN NE DEĞİŞTİ?</span>
            <h3>Snapshot karşılaştırması</h3>
            <div className='profileChangeList'>
              {detail.analysis.changes_since_last_visit.map((change,index) => <div key={`${index}-${change}`}><span>✓</span><p>{change}</p></div>)}
            </div>
          </div>

          <div className='moduleCard profileBridgePreview'>
            <span className='eyebrow'>KÖPRÜ KAYDI</span>
            <h3>Bu analizdeki Köprü sorusu</h3>
            <p>{detail.analysis.bridge.bridge_question || 'Bu anlık görüntüde Köprü sorusu bulunmuyor.'}</p>
            <small>Geçmiş kayıt açıldığında bu sorunun üretildiği analiz sonucu aynen geri yüklenir.</small>
          </div>
        </div>
      )}
    </>
  );
}

function NavWorkspace({page, onOpenHome}:{page:NavPage; onOpenHome:()=>void}) {
  const content: Record<Exclude<NavPage,'Ana Sayfa'>, {title:string; subtitle:string; cards:{title:string; text:string; badge:string}[]}> = {
    'Keşfet': {
      title: 'Keşfet',
      subtitle: 'N-KÖPRÜ için örnek gündem ve tartışma kümeleri.',
      cards: [
        {title:'Yapay zekâ ve eğitim', text:'Üniversitelerde kullanım sınırları, etik ve öğrenme etkisi.', badge:'Trend'},
        {title:'Dijital mahremiyet', text:'Kişisel veri, platform sorumluluğu ve kullanıcı hakları.', badge:'Yeni'},
        {title:'Sosyal medya ve gençler', text:'Ekran süresi, içerik önerileri ve çevrim içi etkileşim.', badge:'Tartışılıyor'},
        {title:'İklim teknolojileri', text:'Teknoloji yatırımları ve toplumsal fayda tartışmaları.', badge:'Öneri'},
      ],
    },
    'Bildirimler': {
      title: 'Bildirimler',
      subtitle: 'Analizlerinden gelen yeni gelişmeleri tek yerde takip et.',
      cards: [
        {title:'Tartışma haritası hazır', text:'Son analizde 4 görüş kümesi görünür hâle geldi.', badge:'Şimdi'},
        {title:'Yeni cevapsız soru', text:'Bir katılımcı tartışmaya yeni bir kaynak sorusu ekledi.', badge:'5 dk'},
        {title:'Köprü sorusu güncellendi', text:'Yeni yorumlar sonrasında ortak zemin kartı yenilendi.', badge:'12 dk'},
      ],
    },
    'Mesajlar': {
      title: 'Mesajlar',
      subtitle: 'Köprü kartlarını ve tartışma özetlerini ekip içinde paylaş.',
      cards: [
        {title:'N-KÖPRÜ Sistem', text:'Analiz sonuçlarını paylaşmadan önce kaynak uyarılarını kontrol et.', badge:'Sistem'},
        {title:'Ekip görüşmesi', text:'Köprü kartını ekip içinde paylaşmak için mesaj akışı burada gösterilecek.', badge:'Taslak'},
      ],
    },
    'Yer İmleri': {
      title: 'Yer İmleri',
      subtitle: 'Daha sonra dönmek istediğin tartışma, iddia ve Köprü kartları.',
      cards: [
        {title:'Üniversitelerde yapay zekâ', text:'Görüş haritası ve Köprü sorusu kaydedildi.', badge:'Kayıtlı'},
        {title:'Kaynak gerektiren iddialar', text:'İddia Radarı’ndan seçilmiş doğrulama adayları.', badge:'3 öğe'},
      ],
    },
    'Listeler': {
      title: 'Listeler',
      subtitle: 'Tartışmaları konu ve ilgi alanlarına göre düzenle.',
      cards: [
        {title:'AI & Eğitim', text:'Yapay zekâ, öğrenme, etik ve akademik güvenilirlik.', badge:'8 konu'},
        {title:'Dijital Etik', text:'Mahremiyet, güvenlik ve platform sorumluluğu.', badge:'5 konu'},
        {title:'Gençlik & Sosyal Medya', text:'Genç kullanıcı deneyimi ve çevrim içi davranış.', badge:'6 konu'},
      ],
    },
    'Profil': {
      title: 'Profil',
      subtitle: 'Yerel kullanıcı • analiz ve Köprü geçmişi',
      cards: [
        {title:'Analiz geçmişi', text:'Kalıcı analiz snapshotları ve değişim kayıtları.', badge:'Kalıcı'},
        {title:'Köprü kartları', text:'Kaydedilen ve geçmiş analizlerde üretilen Köprü soruları.', badge:'Köprü'},
        {title:'Konu listeleri', text:'SQLite üzerinde tutulan kullanıcı listeleri ve öğeleri.', badge:'Liste'},
      ],
    },
    'Teknik Doğrulama': {
      title: 'Teknik Doğrulama',
      subtitle: 'Çalıştırılabilir iç doğrulama ve gerçek analiz gecikmesi.',
      cards: [
        {title:'Elle etiketli iç set', text:'Dört görüş sınıfında 20 gerçek sınıflandırma kontrolü.', badge:'20 örnek'},
        {title:'Analiz gecikmesi', text:'Tekrarlı çalışma, medyan ve P95 süreleri.', badge:'Ölçüm'},
        {title:'Demo değişmezleri', text:'Kaynak farkındalığı, Köprü ve tekilleştirme kontrolleri.', badge:'Doğrulama'},
      ],
    },
  };

  if (page === 'Ana Sayfa') return null;
  const data = content[page];

  return (
    <div className='navWorkspace'>
      <div className='workspaceHero'>
        <span className='eyebrow'>N-KÖPRÜ</span>
        <h2>{data.title}</h2>
        <p>{data.subtitle}</p>
      </div>
      <div className='workspaceGrid'>
        {data.cards.map(card => (
          <div className='workspaceCard' key={card.title}>
            <div><b>{card.title}</b><span>{card.badge}</span></div>
            <p>{card.text}</p>
          </div>
        ))}
      </div>
      <div className='workspaceNote'>
        <b>N-KÖPRÜ akışına dön</b>
        <p>Yeni bir tartışmayı analiz etmek veya mevcut tartışmanın görüş haritasını açmak için ana akışa geçebilirsin.</p>
        <button className='primary noMargin' onClick={onOpenHome}>Ana tartışmaya dön</button>
      </div>
    </div>
  );
}

function NavContext({page}:{page:NavPage}) {
  const notes: Record<Exclude<NavPage,'Ana Sayfa'>, {title:string; items:string[]}> = {
    'Keşfet': {title:'Keşfet modülü', items:['Anlık arama ve Türkçe duyarlı eşleşme', 'Konu ve etiket filtreleri', 'Tartışmayı aç / hızlı analiz']},
    'Bildirimler': {title:'Bildirim merkezi', items:['Yeni görüş kümesi', 'Kaynak talebi', 'Köprü güncellemesi']},
    'Mesajlar': {title:'Mesajlaşma katmanı', items:['Köprü kartı paylaşımı', 'Ekip içi iletişim', 'Kalıcı çalışma alanı']},
    'Yer İmleri': {title:'Kaydedilenler', items:['Tartışmalar', 'İddia kartları', 'Köprü soruları']},
    'Listeler': {title:'Konu listeleri', items:['AI & Eğitim', 'Dijital Etik', 'Gençlik & Sosyal Medya']},
    'Profil': {title:'Kullanıcı profili', items:['Analiz geçmişi', 'Köprü kartları', 'Takip edilen listeler']},
    'Teknik Doğrulama': {title:'Teknik doğrulama', items:['Elle etiketli iç senaryolar', 'Gerçek analiz gecikmesi', 'Şeffaf model kullanımı']},
  };
  if (page === 'Ana Sayfa') return null;
  const note = notes[page];
  return (
    <>
      <div className='panelHeader'>
        <div><span className='eyebrow'>N-KÖPRÜ</span><h2>{note.title}</h2></div>
        <span className='status'>Hazır</span>
      </div>
      <div className='contextCard'>
        <div className='contextIcon'>N</div>
        <h3>{page}</h3>
        <p>{page === 'Keşfet' ? 'Yerel gündem kataloğu backend üzerinden aranır ve seçilen tartışma doğrudan analiz akışına taşınır.' : 'Bu bölüm, tartışma analizini tamamlayan kişisel çalışma alanını gösterir.'}</p>
        <div className='contextList'>
          {note.items.map(item => <span key={item}>✓ {item}</span>)}
        </div>
        <small>{page === 'Keşfet' ? 'Keşfet arama, filtreleme, önizleme, tartışma açma ve hızlı analiz işlevleri aktiftir.' : 'Bu alan yerel çalışma verileriyle hazırlanmıştır.'}</small>
      </div>
    </>
  );
}

function Metric({label,value}:{label:string;value:string|number}) { return <div className='metric'><strong>{value}</strong><span>{label}</span></div>; }
function Bridge({label,text,strong=false}:{label:string;text:string;strong?:boolean}) { return <div className={`bridgeRow ${strong?'bridgeStrong':''}`}><b>{label}</b><p>{text}</p></div>; }
