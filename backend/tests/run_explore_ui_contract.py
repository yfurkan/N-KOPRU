from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')


class ExploreUIContract(unittest.TestCase):
    def test_01_version_and_demo_label(self):
        self.assertIn('N-KÖPRÜ • KEŞFET', PAGE)
        self.assertIn('● Demo gündem aktif', PAGE)
        self.assertNotIn('● Yerel gündem aktif', PAGE)

    def test_02_dynamic_preview_panel_is_wired_to_right_column(self):
        self.assertIn("navPage === 'Keşfet' ? (\n          <ExplorePreviewPanel", PAGE)
        self.assertIn('Tartışma önizlemesi', PAGE)
        self.assertIn('post.comments.slice(0,4)', PAGE)

    def test_03_preview_has_both_open_and_analyze_actions(self):
        self.assertIn("void run('open')", PAGE)
        self.assertIn("void run('analyze')", PAGE)
        self.assertIn('✨ N-KÖPRÜ ile Analiz Et', PAGE)

    def test_04_filter_reset_and_empty_state_exist(self):
        self.assertIn('Filtreleri temizle', PAGE)
        self.assertIn('Eşleşen tartışma bulunamadı.', PAGE)
        self.assertIn("const hasFilters = category !== 'Tümü' || query.trim().length > 0", PAGE)

    def test_05_result_counters_are_derived_from_filtered_topics(self):
        self.assertIn('{topics.length}', PAGE)
        self.assertIn('topics.reduce((sum,t) => sum + t.comment_count, 0)', PAGE)

    def test_06_card_preview_is_keyboard_accessible(self):
        self.assertIn("role='button'", PAGE)
        self.assertIn('tabIndex={0}', PAGE)
        self.assertIn("e.key === 'Enter' || e.key === ' '", PAGE)

    def test_07_preview_race_guard_exists(self):
        self.assertIn('explorePreviewRequestId = useRef(0)', PAGE)
        self.assertIn('requestId === explorePreviewRequestId.current', PAGE)

    def test_08_selected_and_preview_styles_exist(self):
        for selector in ('.exploreCardSelected', '.explorePreviewCard', '.previewActions', '.filterReset'):
            self.assertIn(selector, CSS)


if __name__ == '__main__':
    unittest.main(verbosity=2)
