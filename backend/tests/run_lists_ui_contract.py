import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
API = (ROOT / 'frontend' / 'lib' / 'api.ts').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')


class ListsUIContract(unittest.TestCase):
    def test_01_real_module_badge(self):
        self.assertIn('N-KÖPRÜ • LİSTELER', PAGE)

    def test_02_sidebar_count(self):
        self.assertIn("x === 'Listeler' && topicListCount > 0", PAGE)

    def test_03_create_list_exists(self):
        self.assertIn('＋ Yeni Liste', PAGE)
        self.assertIn('Listeyi Oluştur', PAGE)
        self.assertIn('createUserTopicList', PAGE)

    def test_04_three_content_kinds_can_be_added(self):
        for text in ['💬 Tartışma','◇ İddia #','🌉 Köprü Sorusu']:
            self.assertIn(text, PAGE)
        self.assertIn('addCurrentToTopicList', PAGE)

    def test_05_remove_and_open_exist(self):
        self.assertIn('İlgili Analizi Aç', PAGE)
        self.assertIn('removeTopicListEntry', PAGE)
        self.assertIn('openTopicListEntry', PAGE)

    def test_06_filters_exist(self):
        for text in ['Tartışmalar','İddialar','Köprüler']:
            self.assertIn(text, PAGE)

    def test_07_api_contract(self):
        for text in ['/api/lists','getTopicLists','createTopicList','addTopicListItem','deleteTopicListItem']:
            self.assertIn(text, API)

    def test_08_styles_exist(self):
        for cls in ['.listWorkspace','.topicListCardSelected','.listQuickAddCard','.listEntryRow']:
            self.assertIn(cls, CSS)

    def test_09_persistence_note(self):
        self.assertIn('Listeler ve içlerindeki öğeler SQLite üzerinde kalıcı saklanır', PAGE)

    def test_10_list_page_prepares_missing_analysis_source(self):
        self.assertIn('ensureTopicListSourceAnalysis', PAGE)
        self.assertIn('topicListSourceBusyRef', PAGE)
        self.assertIn("if (x === 'Listeler') { refreshTopicLists", PAGE)
        self.assertIn('ensureTopicListSourceAnalysis().catch(() => null)', PAGE)

    def test_11_source_loading_error_and_retry_states_exist(self):
        for text in ['İddia ve Köprü verileri hazırlanıyor','Analiz verileri hazırlanamadı','↻ Tekrar Dene','✦ Analizi Hazırla']:
            self.assertIn(text, PAGE)

    def test_12_claim_and_bridge_empty_states_are_explicit(self):
        self.assertIn('Bu analizde doğrulanabilir iddia adayı bulunamadı.', PAGE)
        self.assertIn('Bu analiz için Köprü sorusu üretilemedi.', PAGE)
        self.assertIn('analysisMatchesPost', PAGE)
        self.assertIn('sourceClaims', PAGE)
        self.assertIn('sourceBridgeQuestion', PAGE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
