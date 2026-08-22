from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
API = (ROOT / 'frontend' / 'lib' / 'api.ts').read_text(encoding='utf-8')
TYPES = (ROOT / 'frontend' / 'lib' / 'types.ts').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')


class NotificationsUIContract(unittest.TestCase):
    def test_01_notifications_are_real_module(self):
        self.assertIn('N-KÖPRÜ • BİLDİRİM MERKEZİ', PAGE)
        self.assertIn('function NotificationWorkspace', PAGE)
        self.assertIn('function NotificationPanel', PAGE)

    def test_02_api_contract_is_wired(self):
        for fn in ('getNotifications', 'markNotificationRead', 'markNotificationUnread', 'markAllNotificationsRead', 'deleteNotification', 'clearReadNotifications', 'restoreNotifications', 'getPostById'):
            self.assertIn(f'function {fn}', API)
        self.assertIn('read_count: number', TYPES)
        self.assertIn('total_count: number', TYPES)
        self.assertIn('deleted_ids: number[]', TYPES)

    def test_03_nav_has_unread_badge(self):
        self.assertIn("x === 'Bildirimler' && notificationUnreadCount > 0", PAGE)
        self.assertIn("className='navCount'", PAGE)
        self.assertIn('.navCount', CSS)

    def test_04_three_filters_and_bulk_actions_exist(self):
        self.assertIn("'Tümü'|'Okunmamış'|'Okunanlar'", PAGE)
        self.assertIn('Tümünü okundu yap', PAGE)
        self.assertIn('Okunanları temizle', PAGE)
        self.assertIn('↻ Yenile', PAGE)

    def test_05_per_notification_menu_and_delete_exist(self):
        self.assertIn('Bildirim seçenekleri', PAGE)
        self.assertIn('Okunmadı yap', PAGE)
        self.assertIn('Okundu yap', PAGE)
        self.assertIn('Bildirimi sil', PAGE)
        self.assertIn('.notificationMenu', CSS)

    def test_06_undo_exists(self):
        self.assertIn('notificationUndo', PAGE)
        self.assertIn('Geri Al', PAGE)
        self.assertIn('restoreNotifications', PAGE)
        self.assertIn('.notificationUndoToast', CSS)

    def test_07_notification_opens_exact_analysis_tab(self):
        self.assertIn('setActive(Math.max(0, Math.min(7, item.tab_index)))', PAGE)
        self.assertIn('const alreadyOpen = post?.id === item.post_id', PAGE)
        self.assertIn('Promise.all([', PAGE)
        self.assertIn('getPostById(item.post_id)', PAGE)
        self.assertIn('analyzePost(item.post_id, useAI)', PAGE)

    def test_08_right_panel_is_dynamic_and_manageable(self):
        self.assertIn("navPage === 'Bildirimler' ? (\n          <NotificationPanel", PAGE)
        self.assertIn('Bildirim detayı', PAGE)
        self.assertIn('notification.tab_index + 1', PAGE)
        self.assertIn('onToggleRead={toggleNotificationReadState}', PAGE)
        self.assertIn('onDelete={removeNotification}', PAGE)

    def test_09_notification_styles_exist(self):
        for selector in ('.notificationItem', '.notificationUnread', '.notificationSelected', '.notificationDetailCard', '.notificationMenuButton', '.notificationSummaryRow'):
            self.assertIn(selector, CSS)

    def test_10_wording_is_not_live_network_claim(self):
        self.assertIn('Kontrollü demo verisi', PAGE)
        self.assertNotIn('Yerel kontrollü demo verisi', PAGE)

    def test_11_ui_explains_meaningful_change_dedup(self):
        self.assertIn('Aynı tartışmayı değişiklik olmadan yeniden analiz etmek yeni bildirim üretmez.', PAGE)
        self.assertIn('Yalnızca anlamlı analiz değişikliklerini', PAGE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
