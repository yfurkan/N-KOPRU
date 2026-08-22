import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
API = (ROOT / 'frontend' / 'lib' / 'api.ts').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')


class MessagesUIContract(unittest.TestCase):
    def test_01_real_module_label(self):
        self.assertIn('N-KÖPRÜ • MESAJLAR', PAGE)

    def test_02_workspace_exists(self):
        self.assertIn('function MessageWorkspace', PAGE)
        self.assertIn('conversationList', PAGE)

    def test_03_panel_exists(self):
        self.assertIn('function MessagePanel', PAGE)
        self.assertIn('messageThread', PAGE)
        self.assertIn('messageComposer', PAGE)

    def test_04_send_api_exists(self):
        self.assertIn('sendConversationMessage', API)
        self.assertIn('/api/messages/${conversationId}', API)

    def test_05_bridge_share_api_exists(self):
        self.assertIn('shareBridgeToConversation', API)
        self.assertIn('/api/messages/bridge/share', API)

    def test_06_bridge_button_is_internal(self):
        self.assertIn('Köprüyü Mesajlarda Paylaş', PAGE)
        self.assertIn('shareCurrentBridgeToMessages', PAGE)

    def test_07_bridge_return_link_exists(self):
        self.assertIn('İlgili Köprü analizini aç', PAGE)
        self.assertIn('onOpenPost', PAGE)

    def test_08_message_badge_exists(self):
        self.assertIn("x === 'Mesajlar' && conversationUnreadCount > 0", PAGE)

    def test_09_notification_read_state_is_refreshed_from_backend(self):
        self.assertIn('await markNotificationRead(item.id)', PAGE)
        self.assertIn('await refreshNotifications(notificationFilter)', PAGE)
        self.assertIn('applyNotificationCounts', PAGE)

    def test_10_styles_exist(self):
        for token in ['.messageWorkspace', '.conversationItem', '.messageThread', '.messageBridgeCard', '.messageComposer']:
            self.assertIn(token, CSS)

    def test_11_bridge_open_is_single_click_guarded(self):
        self.assertIn('openBridgeFromMessages', PAGE)
        self.assertIn('if (messageBridgeOpening) return', PAGE)
        self.assertIn('post?.id === postId && analysis', PAGE)
        self.assertIn('disabled={openingPost}', PAGE)
        self.assertIn("openingPost ? '⏳ Köprü açılıyor…'", PAGE)

    def test_12_bridge_open_parallel_loads_when_needed(self):
        self.assertIn('Promise.all([', PAGE)
        self.assertIn('getPostById(postId)', PAGE)
        self.assertIn('analyzePost(postId, useAI)', PAGE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
