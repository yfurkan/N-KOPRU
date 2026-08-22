import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
API = (ROOT / 'frontend' / 'lib' / 'api.ts').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')


class BookmarksUIContract(unittest.TestCase):
    def test_01_real_module_badge(self):
        self.assertIn('N-KÖPRÜ • YER İMLERİ', PAGE)

    def test_02_sidebar_count(self):
        self.assertIn("x === 'Yer İmleri' && bookmarkCount > 0", PAGE)

    def test_03_discussion_save_button(self):
        self.assertIn('☆ Tartışmayı Kaydet', PAGE)
        self.assertIn('★ Kaydedildi', PAGE)

    def test_04_claim_save_button(self):
        self.assertIn("toggleClaimBookmark", PAGE)
        self.assertIn('☆ Kaydet', PAGE)

    def test_05_bridge_save_button(self):
        self.assertIn('☆ Köprüyü Kaydet', PAGE)
        self.assertIn('★ Köprü Kaydedildi', PAGE)

    def test_06_filters_exist(self):
        for text in ['Tartışmalar','İddialar','Köprü Soruları']:
            self.assertIn(text, PAGE)

    def test_07_direct_open_exists(self):
        self.assertIn('İlgili Analizi Aç', PAGE)
        self.assertIn('openBookmarkTarget', PAGE)

    def test_08_backend_api_contract(self):
        self.assertIn('/api/bookmarks', API)
        self.assertIn('createBookmark', API)
        self.assertIn('deleteBookmark', API)

    def test_09_bookmark_styles_exist(self):
        for cls in ['.bookmarkWorkspace','.bookmarkCardSelected','.bookmarkDetailCard','.bookmarkSaved']:
            self.assertIn(cls, CSS)

    def test_10_persistence_note_exists(self):
        self.assertIn('Yer İmleri SQLite üzerinde kalıcı saklanır', PAGE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
