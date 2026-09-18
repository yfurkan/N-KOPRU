
export type NotificationItem = {
  id: number;
  kind: string;
  title: string;
  text: string;
  created_at: string;
  relative_time: string;
  is_read: boolean;
  post_id: number | null;
  tab_index: number | null;
  badge: string;
  priority: string;
};

export type NotificationResponse = {
  total_count: number;
  read_count: number;
  unread_count: number;
  notifications: NotificationItem[];
};

export type NotificationActionResponse = {
  ok: boolean;
  total_count: number;
  read_count: number;
  unread_count: number;
  notification?: NotificationItem | null;
  changed: number;
  deleted_ids: number[];
};


export type ExploreTopic = {
  id: number;
  category: string;
  title: string;
  summary: string;
  badge: string;
  tags: string[];
  comment_count: number;
};

export type ExploreResponse = {
  categories: string[];
  topics: ExploreTopic[];
};

export type Comment = {
  id: number;
  author: string;
  text: string;
  created_at: string;
  likes: number;
};

export type Post = {
  id: number;
  author: string;
  handle: string;
  text: string;
  created_at: string;
  comments: Comment[];
};

export type CommentAppendResult = {
  post: Post;
  comment: Comment;
  analysis: Analysis;
  history_id: number;
  notifications_created: number;
};

export type ViewpointEvidence = {
  comment_id: number;
  author: string;
  text: string;
  confidence: number;
  engine: string;
};

export type Viewpoint = {
  name: string;
  percentage: number;
  summary: string;
  display_name: string;
  comment_count: number;
  main_argument: string;
  evidence_comment_ids: number[];
  representative_comments: ViewpointEvidence[];
  dominant_themes: string[];
  shared_themes: string[];
  opposing_viewpoint_names: string[];
  relationship_note: string;
  related_claim_comment_ids: number[];
  related_question_comment_ids: number[];
  structural_comment_count: number;
  model_comment_count: number;
  average_model_confidence: number;
};

export type StanceDetail = {
  comment_id: number;
  text: string;
  label: string;
  confidence: number;
  engine: string;
};

export type ClaimItem = {
  comment_id: number;
  text: string;
  source_status: string;
  claim_type: string;
  verification_need: string;
  priority: string;
  confidence: number;
  engine: string;
  detection_reason: string;
};

export type CommonGroundItem = {
  theme: string;
  text: string;
  support_count: number;
  stance_count: number;
  evidence_comment_ids: number[];
  confidence: number;
  engine: string;
};

export type QuestionItem = {
  comment_id: number;
  text: string;
  question_type: string;
  answer_status: string;
  priority: string;
  confidence: number;
  evidence_comment_ids: number[];
  repeated_comment_ids: number[];
  answer_comment_ids: number[];
  affected_viewpoints: string[];
  impact: string;
  engine: string;
  detection_reason: string;
  identity_key: string;
};

export type AIStatus = {
  installed: boolean;
  loaded: boolean;
  model: string;
  device: string;
  mode: string;
  message: string;
  error?: string | null;
};

export type TechnicalDataset = {
  name: string;
  version: string;
  sample_count: number;
  label_count: number;
  label_distribution: Record<string, number>;
  is_external_benchmark: boolean;
  limitation: string;
};

export type TechnicalClassMetric = {
  label: string;
  support: number;
  precision: number;
  recall: number;
  f1: number;
};

export type TechnicalPrediction = {
  id: number;
  text: string;
  expected_label: string;
  predicted_label: string;
  correct: boolean;
  decision_engine: string;
  model_confidence: number | null;
};

export type TechnicalLatency = {
  iterations: number;
  samples_ms: number[];
  minimum_ms: number;
  median_ms: number;
  p95_ms: number;
  maximum_ms: number;
  mean_ms: number;
  unique_comment_count: number;
  raw_comment_count: number;
  estimated_comments_per_second: number;
  cold_ms: number | null;
  warm_samples_ms: number[];
  warm_median_ms: number | null;
  warm_p95_ms: number | null;
  speedup_factor: number | null;
};

export type TechnicalInvariant = {
  key: string;
  label: string;
  expected: string;
  actual: string;
  passed: boolean;
};

export type TechnicalStage = {
  key: string;
  label: string;
  samples_ms: number[];
  minimum_ms: number;
  median_ms: number;
  p95_ms: number;
  maximum_ms: number;
  mean_ms: number;
  share_of_total_percent: number;
  transformer_inference_counts: number[];
  transformer_inference_total: number;
  cold_ms: number | null;
  warm_median_ms: number | null;
  cache_hit_counts: number[];
  cache_hit_total: number | null;
};

export type TechnicalStageProfile = {
  available: boolean;
  iterations: number;
  stages: TechnicalStage[];
  overhead_samples_ms: number[];
  overhead_median_ms: number;
  bottleneck: {
    key: string;
    label: string;
    median_ms: number;
    share_of_total_percent: number;
  } | null;
  cold_bottleneck: {
    key: string;
    label: string;
    cold_ms: number | null;
  } | null;
  note: string;
};

export type TechnicalModelUsage = {
  internal_set: {
    sample_count: number;
    structural_decision_count: number;
    stance_transformer_count: number;
    claim_transformer_count: number | null;
    total_transformer_count: number | null;
    claim_transformer_comment_ids: number[];
  };
  demo: {
    available: boolean;
    iterations: number;
    stance_transformer_counts: number[];
    claim_transformer_counts: number[];
    stance_transformer_total: number | null;
    claim_transformer_total: number | null;
    transformer_total: number | null;
    stance_transformer_per_run: number | null;
    claim_transformer_per_run: number | null;
    claim_transformer_comment_ids: number[];
    claim_model_comment_ids: number[];
    claim_cache_comment_ids: number[];
    claim_cache_hit_counts: number[];
    claim_cache_miss_counts: number[];
    claim_cache_hit_total: number | null;
    claim_cache_miss_total: number | null;
    cold_claim_transformer_count: number | null;
    warm_claim_transformer_counts: number[];
    warm_claim_cache_hit_total: number | null;
  };
  note: string;
};

export type TechnicalCacheProfile = {
  available: boolean;
  storage: string;
  persistent: boolean;
  max_entries: number;
  cold_ms: number | null;
  warm_median_ms: number | null;
  warm_sample_count: number;
  speedup_factor: number | null;
  hit_counts: number[];
  miss_counts: number[];
  hit_total: number | null;
  miss_total: number | null;
  hit_rate_percent: number | null;
  avoided_model_inference_count: number | null;
  note: string;
};

export type TechnicalHardware = {
  torch_available: boolean;
  torch_version: string | null;
  cuda_build_version: string | null;
  cuda_available: boolean;
  cuda_device_count: number;
  cuda_device_name: string | null;
  probe_error: string | null;
  active_device: string;
  model_loaded: boolean;
  acceleration_active: boolean;
  cpu_core_count: number;
  diagnosis_key: string;
  diagnosis: string;
};

export type TechnicalEvaluation = {
  run_id: string;
  created_at: string;
  version: string;
  dataset: TechnicalDataset;
  accuracy: number;
  macro_f1: number;
  correct_count: number;
  sample_count: number;
  class_metrics: TechnicalClassMetric[];
  confusion_matrix: Array<{
    expected_label: string;
    predicted_counts: Record<string, number>;
  }>;
  predictions: TechnicalPrediction[];
  latency: TechnicalLatency;
  stage_profile: TechnicalStageProfile;
  model_usage: TechnicalModelUsage;
  cache_profile: TechnicalCacheProfile;
  hardware: TechnicalHardware;
  invariants: TechnicalInvariant[];
  passed_invariant_count: number;
  invariant_count: number;
  requested_ai: boolean;
  effective_ai: boolean;
  engine_mode: string;
  structural_decision_count: number;
  transformer_inference_count: number;
  model_status: AIStatus;
  engine_note: string;
  isolation_note: string;
  label_distribution: Record<string, number>;
};

export type TechnicalScenarioDataset = {
  name: string;
  version: string;
  sample_count: number;
  scenario_count: number;
  label_count: number;
  label_distribution: Record<string, number>;
  difficulty_distribution: Record<string, number>;
  scenarios: Array<{
    key: string;
    title: string;
    topic: string;
    description: string;
    sample_count: number;
  }>;
  is_external_benchmark: boolean;
  contains_user_content: boolean;
  limitation: string;
  calibration_note?: string;
  dataset_role?: string;
  calibration_dataset_version?: string;
  calibration_sample_overlap_count?: number;
  calibration_topic_overlap_count?: number;
  is_disjoint_from_calibration?: boolean;
  frozen_sha256?: string;
};

export type TechnicalScenarioPrediction = TechnicalPrediction & {
  scenario_key: string;
  scenario_title: string;
  scenario_topic: string;
  difficulty: string;
  challenge: string;
};

export type TechnicalDifficultyMetric = {
  key: string;
  label: string;
  sample_count: number;
  correct_count: number;
  accuracy: number;
};

export type TechnicalScenarioOutcome = {
  key: string;
  title: string;
  topic: string;
  description: string;
  sample_count: number;
  correct_count: number;
  accuracy: number;
  macro_f1: number;
  class_metrics: TechnicalClassMetric[];
  confusion_matrix: Array<{
    expected_label: string;
    predicted_counts: Record<string, number>;
  }>;
  difficulty_metrics: TechnicalDifficultyMetric[];
  error_count: number;
  errors: TechnicalScenarioPrediction[];
  structural_decision_count: number;
  transformer_inference_count: number;
  semantic_guardrail_count?: number;
  elapsed_ms: number;
  engine_mode: string;
};

export type TechnicalScenarioEvaluation = {
  run_id: string;
  created_at: string;
  version: string;
  dataset: TechnicalScenarioDataset;
  sample_count: number;
  scenario_count: number;
  correct_count: number;
  error_count: number;
  accuracy: number;
  macro_f1: number;
  class_metrics: TechnicalClassMetric[];
  confusion_matrix: Array<{
    expected_label: string;
    predicted_counts: Record<string, number>;
  }>;
  difficulty_metrics: TechnicalDifficultyMetric[];
  scenarios: TechnicalScenarioOutcome[];
  predictions: TechnicalScenarioPrediction[];
  errors: TechnicalScenarioPrediction[];
  label_distribution: Record<string, number>;
  structural_decision_count: number;
  transformer_inference_count: number;
  semantic_guardrail_count?: number;
  elapsed_ms: number;
  requested_ai: boolean;
  effective_ai: boolean;
  engine_mode: string;
  model_status: AIStatus;
  engine_note: string;
  isolation_note: string;
};

export type TechnicalStatus = {
  version: string;
  storage: string;
  dataset: TechnicalDataset;
  scenario_dataset: TechnicalScenarioDataset;
  holdout_dataset?: TechnicalScenarioDataset;
  model_status: AIStatus;
  hardware: TechnicalHardware;
  latest_result: TechnicalEvaluation | null;
  latest_scenario_result: TechnicalScenarioEvaluation | null;
  latest_holdout_result?: TechnicalScenarioEvaluation | null;
};

export type Analysis = {
  post_id: number;
  short_summary: string;
  common_ground: string[];
  common_ground_details: CommonGroundItem[];
  key_disagreements: string[];
  viewpoints: Viewpoint[];
  stance_details: StanceDetail[];
  claims: ClaimItem[];
  unanswered_questions: QuestionItem[];
  rhetorical_questions: QuestionItem[];
  indicators: Record<string, number>;
  bridge: {
    common_acceptance: string;
    main_divergence: string;
    missing_information: string;
    bridge_question: string;
    evidence_comment_ids?: number[];
    contrast_viewpoint_names?: string[];
    contrast_viewpoint_labels?: string[];
    confidence?: number;
    engine?: string;
  };
  changes_since_last_visit: string[];
  engine: AIStatus & Record<string, unknown>;
};


export type RewriteResult = {
  original: string;
  suggestion: string;
  reason: string;
  engine: string;
  elapsed_ms: number;
  signals: string[];
};

export type MessageAttachment = {
  kind: string;
  title: string;
  post_id: number | null;
  tab_index: number | null;
  summary: string;
  common_acceptance: string;
  main_divergence: string;
  missing_information: string;
  bridge_question: string;
};

export type MessageItem = {
  id: number;
  conversation_id: number;
  author: string;
  text: string;
  created_at: string;
  relative_time: string;
  is_mine: boolean;
  attachment: MessageAttachment | null;
};

export type ConversationSummary = {
  id: number;
  title: string;
  subtitle: string;
  badge: string;
  unread_count: number;
  last_message: string;
  last_time: string;
};

export type ConversationListResponse = {
  conversations: ConversationSummary[];
};

export type ConversationDetail = {
  conversation: ConversationSummary;
  messages: MessageItem[];
};

export type BookmarkKind = 'discussion' | 'claim' | 'bridge';

export type BookmarkItem = {
  id: number;
  kind: BookmarkKind;
  post_id: number;
  title: string;
  text: string;
  tab_index: number | null;
  comment_id: number | null;
  created_at: string;
  relative_time: string;
};

export type BookmarkResponse = {
  count: number;
  bookmarks: BookmarkItem[];
};

export type BookmarkActionResponse = {
  ok: boolean;
  created: boolean;
  count: number;
  bookmark: BookmarkItem | null;
};

export type TopicList = {
  id: number;
  name: string;
  description: string;
  created_at: string;
  relative_time: string;
  item_count: number;
  discussion_count: number;
  claim_count: number;
  bridge_count: number;
};

export type TopicListEntry = {
  id: number;
  list_id: number;
  kind: BookmarkKind;
  post_id: number;
  title: string;
  text: string;
  tab_index: number | null;
  comment_id: number | null;
  created_at: string;
  relative_time: string;
};

export type TopicListResponse = {
  count: number;
  lists: TopicList[];
};

export type TopicListDetail = {
  list: TopicList;
  items: TopicListEntry[];
};

export type TopicListActionResponse = {
  ok: boolean;
  created: boolean;
  count: number;
  list: TopicList | null;
  item: TopicListEntry | null;
};

export type AnalysisHistoryItem = {
  id: number;
  post_id: number;
  title: string;
  analyzed_at: string;
  relative_time: string;
  comment_count: number;
  viewpoint_count: number;
  claim_count: number;
  question_count: number;
  engine_mode: string;
  changed_count: number;
};

export type AnalysisHistoryResponse = {
  count: number;
  analyses: AnalysisHistoryItem[];
};

export type AnalysisHistoryDetail = {
  item: AnalysisHistoryItem;
  post: Post;
  analysis: Analysis;
};

export type ProfileUser = {
  display_name: string;
  handle: string;
  bio: string;
  created_at: string;
  updated_at: string;
};

export type ProfileStats = {
  analysis_count: number;
  unique_discussions: number;
  saved_bridge_count: number;
  bookmark_count: number;
  list_count: number;
  list_item_count: number;
  notification_count: number;
  sent_message_count: number;
  last_analyzed_at: string | null;
};

export type ProfileResponse = {
  user: ProfileUser;
  stats: ProfileStats;
  recent_analyses: AnalysisHistoryItem[];
};

export type ReadinessCheck = {
  key: string;
  label: string;
  status: 'ready' | 'optional' | 'warning' | 'failed';
  detail: string;
  required: boolean;
};

export type SystemReadiness = {
  version: string;
  checked_at: string;
  status: 'ready' | 'degraded' | 'failed';
  presentation_ready: boolean;
  required_ready_count: number;
  required_check_count: number;
  checks: ReadinessCheck[];
  note: string;
};

export type PilotAnalysis = {
  short_summary: string;
  common_ground: string;
  main_divergence: string;
  bridge_question: string;
  viewpoints: Array<{ name: string; percentage: number; comment_count: number }>;
  claim_count: number;
  open_question_count: number;
  engine: string;
};

export type PilotPhase = {
  phase_index: number;
  variant: 'raw' | 'nkopru';
  scenario_key: string;
  title: string;
  instructions: string;
  question: string;
  choices: string[];
  comments: string[];
  analysis: PilotAnalysis | null;
};

export type PilotSession = {
  session_id: number;
  participant_code: string;
  practice: boolean;
  assignment: string;
  completed_phase_count: number;
  completed: boolean;
  current_phase: PilotPhase | null;
};

export type PilotPhaseResult = {
  phase_index: number;
  variant: 'raw' | 'nkopru';
  scenario_key: string;
  correct: boolean;
  duration_ms: number;
  clarity_rating: number;
  confidence_rating: number;
};

export type PilotVariantMetrics = {
  variant: 'raw' | 'nkopru';
  completed_task_count: number;
  median_duration_ms: number | null;
  accuracy_percent: number | null;
  average_clarity: number | null;
  average_confidence: number | null;
};

export type PilotOverview = {
  protocol_version: string;
  recommended_participants: string;
  completed_session_count: number;
  active_session_count: number;
  practice_session_count: number;
  minimum_sample_reached: boolean;
  raw: PilotVariantMetrics;
  nkopru: PilotVariantMetrics;
  time_gain_percent: number | null;
  accuracy_gain_points: number | null;
  clarity_gain: number | null;
  conclusion: string;
  integrity_note: string;
};
