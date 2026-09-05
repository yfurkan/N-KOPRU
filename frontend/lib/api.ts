import type { AIStatus, Analysis, AnalysisHistoryDetail, AnalysisHistoryResponse, BookmarkActionResponse, BookmarkKind, BookmarkResponse, CommentAppendResult, ConversationDetail, ConversationListResponse, ExploreResponse, MessageItem, NotificationActionResponse, NotificationResponse, PilotOverview, PilotSession, PilotPhaseResult, Post, ProfileResponse, SystemReadiness, TechnicalEvaluation, TechnicalScenarioEvaluation, TechnicalStatus, TopicListActionResponse, TopicListDetail, TopicListResponse } from './types';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000';

export async function getDemoPost(): Promise<Post> {
  const res = await fetch(`${API}/api/posts/demo`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Gönderi yüklenemedi');
  return res.json();
}

export async function getPostById(postId: number): Promise<Post> {
  const res = await fetch(`${API}/api/posts/${postId}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Gönderi yüklenemedi');
  return res.json();
}

export async function getAIStatus(): Promise<AIStatus> {
  const res = await fetch(`${API}/api/ai/status`, { cache: 'no-store' });
  if (!res.ok) throw new Error('AI durumu okunamadı');
  return res.json();
}

export async function loadAIModel(): Promise<AIStatus> {
  const res = await fetch(`${API}/api/ai/load`, { method: 'POST' });
  if (!res.ok) throw new Error('AI modeli yüklenemedi');
  return res.json();
}

export async function getTechnicalStatus(): Promise<TechnicalStatus> {
  const res = await fetch(`${API}/api/evaluation`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Teknik doğrulama durumu yüklenemedi');
  return res.json();
}

export async function runTechnicalEvaluation(iterations = 5, useAI = true): Promise<TechnicalEvaluation> {
  const res = await fetch(`${API}/api/evaluation/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ iterations, use_ai: useAI }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? 'Teknik doğrulama çalıştırılamadı');
  }
  return res.json();
}

export async function runScenarioEvaluation(useAI = true): Promise<TechnicalScenarioEvaluation> {
  const res = await fetch(`${API}/api/evaluation/scenarios/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ use_ai: useAI }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? 'Çok senaryolu doğrulama çalıştırılamadı');
  }
  return res.json();
}

export async function runHoldoutEvaluation(useAI = true): Promise<TechnicalScenarioEvaluation> {
  const res = await fetch(`${API}/api/evaluation/holdout/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ use_ai: useAI }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? 'Ayrılmış yeni iç kontrol çalıştırılamadı');
  }
  return res.json();
}

export async function analyzePost(postId: number, useAI = true): Promise<Analysis> {
  const res = await fetch(`${API}/api/analyze/${postId}?use_ai=${useAI ? 'true' : 'false'}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Analiz yapılamadı');
  return res.json();
}

export async function analyzeDiscussion(title: string, comments: string[], useAI = true): Promise<{ post: Post; analysis: Analysis }> {
  const res = await fetch(`${API}/api/analyze-discussion`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, comments, use_ai: useAI }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? 'Yeni tartışma analiz edilemedi');
  }
  return res.json();
}

export async function appendComment(postId: number, text: string, useAI = true): Promise<CommentAppendResult> {
  const res = await fetch(`${API}/api/posts/${postId}/comments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, use_ai: useAI }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? 'Yorum eklenemedi');
  }
  return res.json();
}

export async function getCoachStatus(): Promise<AIStatus> {
  const res = await fetch(`${API}/api/coach/status`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Yanıt Koçu durumu okunamadı');
  return res.json();
}

export async function loadCoachModel(): Promise<AIStatus> {
  const res = await fetch(`${API}/api/coach/load`, { method: 'POST' });
  if (!res.ok) throw new Error('Yanıt Koçu modeli yüklenemedi');
  return res.json();
}

export async function rewriteComment(text: string, context = '', useAI = true) {
  const res = await fetch(`${API}/api/rewrite`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, context, use_ai: useAI }),
  });
  if (!res.ok) throw new Error('Yanıt koçu çalıştırılamadı');
  return res.json();
}


export async function getExploreTopics(category = 'Tümü', q = ''): Promise<ExploreResponse> {
  const params = new URLSearchParams();
  if (category && category !== 'Tümü') params.set('category', category);
  if (q.trim()) params.set('q', q.trim());
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const res = await fetch(`${API}/api/explore${suffix}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Keşfet gündemi yüklenemedi');
  return res.json();
}

export async function getExplorePost(topicId: number): Promise<Post> {
  const res = await fetch(`${API}/api/explore/${topicId}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Keşfet tartışması yüklenemedi');
  return res.json();
}


export type NotificationFilter = 'all' | 'unread' | 'read';

export async function getNotifications(status: NotificationFilter = 'all'): Promise<NotificationResponse> {
  const suffix = status === 'all' ? '' : `?status=${status}`;
  const res = await fetch(`${API}/api/notifications${suffix}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Bildirimler yüklenemedi');
  return res.json();
}

export async function markNotificationRead(notificationId: number): Promise<NotificationActionResponse> {
  const res = await fetch(`${API}/api/notifications/${notificationId}/read`, { method: 'POST' });
  if (!res.ok) throw new Error('Bildirim okunmuş olarak işaretlenemedi');
  return res.json();
}

export async function markNotificationUnread(notificationId: number): Promise<NotificationActionResponse> {
  const res = await fetch(`${API}/api/notifications/${notificationId}/unread`, { method: 'POST' });
  if (!res.ok) throw new Error('Bildirim okunmamış olarak işaretlenemedi');
  return res.json();
}

export async function markAllNotificationsRead(): Promise<NotificationActionResponse> {
  const res = await fetch(`${API}/api/notifications/read-all`, { method: 'POST' });
  if (!res.ok) throw new Error('Bildirimler güncellenemedi');
  return res.json();
}

export async function deleteNotification(notificationId: number): Promise<NotificationActionResponse> {
  const res = await fetch(`${API}/api/notifications/${notificationId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Bildirim silinemedi');
  return res.json();
}

export async function clearReadNotifications(): Promise<NotificationActionResponse> {
  const res = await fetch(`${API}/api/notifications/read`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Okunan bildirimler temizlenemedi');
  return res.json();
}

export async function restoreNotifications(ids: number[]): Promise<NotificationActionResponse> {
  const res = await fetch(`${API}/api/notifications/restore`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids }),
  });
  if (!res.ok) throw new Error('Bildirim geri alınamadı');
  return res.json();
}


export async function getConversations(): Promise<ConversationListResponse> {
  const res = await fetch(`${API}/api/messages`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Konuşmalar yüklenemedi');
  return res.json();
}

export async function getConversation(conversationId: number): Promise<ConversationDetail> {
  const res = await fetch(`${API}/api/messages/${conversationId}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Konuşma yüklenemedi');
  return res.json();
}

export async function sendConversationMessage(conversationId: number, text: string): Promise<MessageItem> {
  const res = await fetch(`${API}/api/messages/${conversationId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error('Mesaj gönderilemedi');
  return res.json();
}

export async function shareBridgeToConversation(payload: {
  conversation_id: number;
  post_id: number;
  title: string;
  summary: string;
  common_acceptance: string;
  main_divergence: string;
  missing_information: string;
  bridge_question: string;
}): Promise<MessageItem> {
  const res = await fetch(`${API}/api/messages/bridge/share`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Köprü kartı Mesajlar bölümüne aktarılamadı');
  return res.json();
}


export async function getBookmarks(kind: BookmarkKind | 'all' = 'all'): Promise<BookmarkResponse> {
  const suffix = kind === 'all' ? '' : `?kind=${encodeURIComponent(kind)}`;
  const res = await fetch(`${API}/api/bookmarks${suffix}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Yer imleri yüklenemedi');
  return res.json();
}

export async function createBookmark(payload: {
  kind: BookmarkKind;
  post_id: number;
  title: string;
  text: string;
  tab_index?: number | null;
  comment_id?: number | null;
}): Promise<BookmarkActionResponse> {
  const res = await fetch(`${API}/api/bookmarks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? 'Yer imi kaydedilemedi');
  }
  return res.json();
}

export async function deleteBookmark(bookmarkId: number): Promise<BookmarkActionResponse> {
  const res = await fetch(`${API}/api/bookmarks/${bookmarkId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Yer imi kaldırılamadı');
  return res.json();
}


export async function getTopicLists(): Promise<TopicListResponse> {
  const res = await fetch(`${API}/api/lists`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Listeler yüklenemedi');
  return res.json();
}

export async function getTopicList(listId: number): Promise<TopicListDetail> {
  const res = await fetch(`${API}/api/lists/${listId}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Liste ayrıntısı yüklenemedi');
  return res.json();
}

export async function createTopicList(payload: { name: string; description?: string }): Promise<TopicListActionResponse> {
  const res = await fetch(`${API}/api/lists`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? 'Liste oluşturulamadı');
  }
  return res.json();
}

export async function deleteTopicList(listId: number): Promise<TopicListActionResponse> {
  const res = await fetch(`${API}/api/lists/${listId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Liste silinemedi');
  return res.json();
}

export async function addTopicListItem(listId: number, payload: {
  kind: BookmarkKind;
  post_id: number;
  title: string;
  text: string;
  tab_index?: number | null;
  comment_id?: number | null;
}): Promise<TopicListActionResponse> {
  const res = await fetch(`${API}/api/lists/${listId}/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? 'İçerik listeye eklenemedi');
  }
  return res.json();
}

export async function deleteTopicListItem(listId: number, itemId: number): Promise<TopicListActionResponse> {
  const res = await fetch(`${API}/api/lists/${listId}/items/${itemId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Liste öğesi çıkarılamadı');
  return res.json();
}


export async function getAnalysisHistory(limit = 30, postId?: number | null): Promise<AnalysisHistoryResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (typeof postId === 'number') params.set('post_id', String(postId));
  const res = await fetch(`${API}/api/history?${params.toString()}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Analiz geçmişi yüklenemedi');
  return res.json();
}

export async function getAnalysisHistoryDetail(historyId: number): Promise<AnalysisHistoryDetail> {
  const res = await fetch(`${API}/api/history/${historyId}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Analiz geçmişi kaydı yüklenemedi');
  return res.json();
}

export async function getProfile(): Promise<ProfileResponse> {
  const res = await fetch(`${API}/api/profile`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Profil yüklenemedi');
  return res.json();
}

export async function updateProfile(payload: { display_name: string; handle: string; bio: string }): Promise<ProfileResponse> {
  const res = await fetch(`${API}/api/profile`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? 'Profil güncellenemedi');
  }
  return res.json();
}

export async function getSystemReadiness(): Promise<SystemReadiness> {
  const res = await fetch(`${API}/api/system/readiness`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Sunum hazırlık denetimi çalıştırılamadı');
  return res.json();
}

export async function getPilotOverview(): Promise<PilotOverview> {
  const res = await fetch(`${API}/api/pilot`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Etki pilotu sonuçları yüklenemedi');
  return res.json();
}

export async function startPilotSession(consent: boolean, practice: boolean): Promise<PilotSession> {
  const res = await fetch(`${API}/api/pilot/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ consent, practice }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? 'Pilot oturumu başlatılamadı');
  }
  return res.json();
}

export async function submitPilotPhase(sessionId: number, payload: {
  phase_index: number;
  selected_answer: number;
  duration_ms: number;
  clarity_rating: number;
  confidence_rating: number;
}): Promise<{ result: PilotPhaseResult; session: PilotSession }> {
  const res = await fetch(`${API}/api/pilot/sessions/${sessionId}/phases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? 'Pilot görevi kaydedilemedi');
  }
  return res.json();
}

export async function downloadPilotResults(): Promise<Blob> {
  const res = await fetch(`${API}/api/pilot/results.csv`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Pilot sonuçları dışa aktarılamadı');
  return res.blob();
}
