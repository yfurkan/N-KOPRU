import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
API = (ROOT / 'frontend' / 'lib' / 'api.ts').read_text(encoding='utf-8')
TYPES = (ROOT / 'frontend' / 'lib' / 'types.ts').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')
MODELS = (ROOT / 'backend' / 'app' / 'models.py').read_text(encoding='utf-8')
MAIN = (ROOT / 'backend' / 'app' / 'main.py').read_text(encoding='utf-8')


class LiveDiscussionUIContractTests(unittest.TestCase):
    def test_01_frontend_api_exports_append_comment(self):
        self.assertIn('export async function appendComment', API)

    def test_02_frontend_calls_post_scoped_comment_endpoint(self):
        self.assertIn('/api/posts/${postId}/comments', API)
        self.assertIn("method: 'POST'", API)

    def test_03_ai_preference_is_forwarded_to_backend(self):
        self.assertIn('JSON.stringify({ text, use_ai: useAI })', API)

    def test_04_response_contract_is_typed(self):
        self.assertIn('export type CommentAppendResult', TYPES)
        for field in ('post: Post', 'comment: Comment', 'analysis: Analysis', 'history_id: number', 'notifications_created: number'):
            self.assertIn(field, TYPES)

    def test_05_live_composer_state_exists(self):
        self.assertIn("const [liveComment, setLiveComment] = useState('')", PAGE)
        self.assertIn('commentSubmitting', PAGE)
        self.assertIn('commentFeedback', PAGE)

    def test_06_live_action_is_separately_guarded(self):
        self.assertIn('async function addLiveComment()', PAGE)
        self.assertIn('if (!post || !clean || commentSubmitting) return', PAGE)

    def test_07_success_updates_both_post_and_analysis(self):
        self.assertIn('setPost(result.post)', PAGE)
        self.assertIn('setAnalysis(result.analysis)', PAGE)

    def test_08_success_opens_real_change_tab(self):
        self.assertIn('setActive(6)', PAGE)

    def test_09_composer_explains_sqlite_and_snapshot_behavior(self):
        self.assertIn('Yorum SQLite’a kaydedilir; analiz ve değişim anlık görüntüsü otomatik güncellenir.', PAGE)

    def test_10_button_uses_clear_user_facing_action(self):
        self.assertIn('Yorumu Ekle ve Analizi Güncelle', PAGE)
        self.assertIn('Yorum ekleniyor ve analiz güncelleniyor…', PAGE)

    def test_11_character_limit_matches_backend(self):
        self.assertIn('maxLength={1200}', PAGE)
        self.assertIn('max_length=1200', MODELS)

    def test_12_success_and_failure_feedback_are_visually_distinct(self):
        self.assertIn('liveCommentFeedback', PAGE)
        self.assertIn('.liveCommentFeedback.success', CSS)
        self.assertIn('.liveCommentFeedback.failure', CSS)

    def test_13_mobile_button_remains_usable(self):
        self.assertIn('.liveCommentFooter button{width:100%}', CSS)

    def test_14_backend_endpoint_returns_snapshot_metadata(self):
        self.assertIn("@app.post('/api/posts/{post_id}/comments', response_model=CommentAppendResponse)", MAIN)
        self.assertIn('notifications_created=notifications_created', MAIN)

    def test_15_comment_composer_resets_when_discussion_changes(self):
        self.assertIn('}, [post?.id]);', PAGE)
        self.assertIn("setCommentFeedback('')", PAGE)
        self.assertIn('setLatestLiveComment(null)', PAGE)

    def test_16_last_added_comment_is_visible_without_opening_all_comments(self):
        self.assertIn('setLatestLiveComment(result.comment)', PAGE)
        self.assertIn('Son eklenen yorum · #{latestLiveComment.id}', PAGE)
        self.assertIn('.latestLiveComment', CSS)


if __name__ == '__main__':
    unittest.main(verbosity=2)
