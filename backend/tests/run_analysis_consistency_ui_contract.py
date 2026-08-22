from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
TYPES = (ROOT / 'frontend' / 'lib' / 'types.ts').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')


class AnalysisConsistencyUIContract(unittest.TestCase):
    def test_01_summary_renders_backend_truthful_execution_text(self):
        self.assertIn("<p className='lead'>{analysis.short_summary}</p>", PAGE)

    def test_02_prototype_note_checks_real_transformer_count(self):
        self.assertIn('transformerCount > 0 ?', PAGE)

    def test_03_prototype_note_distinguishes_model_ready_from_model_used(self):
        self.assertIn('yapısal Türkçe sinyaller (Transformer hazır)', PAGE)

    def test_04_real_model_calls_are_counted_when_present(self):
        self.assertIn('mDeBERTa-XNLI (${transformerCount} çıkarım)', PAGE)

    def test_05_bridge_exposes_compared_positions(self):
        self.assertIn('Karşılaştırılan yaklaşımlar', PAGE)

    def test_06_bridge_uses_contextual_not_canonical_position_labels(self):
        self.assertIn('analysis.bridge.contrast_viewpoint_labels.map', PAGE)

    def test_07_contrast_section_supports_old_snapshots(self):
        self.assertIn('analysis.bridge.contrast_viewpoint_labels?.length', PAGE)

    def test_08_types_allow_optional_legacy_compatible_contrast_fields(self):
        self.assertIn('contrast_viewpoint_names?: string[]', TYPES)
        self.assertIn('contrast_viewpoint_labels?: string[]', TYPES)

    def test_09_contrast_positions_use_compact_chips(self):
        self.assertIn('.bridgeContrastRow', CSS)
        self.assertIn('.bridgeContrastRow>div>span', CSS)

    def test_10_question_impact_is_rendered_from_localized_backend_value(self):
        self.assertIn("<span>{q.impact}</span>", PAGE)

    def test_11_question_cards_continue_using_shared_display_name_map(self):
        self.assertIn('q.affected_viewpoints.map(name => viewpointLabelMap[name] || name)', PAGE)

    def test_12_bridge_evidence_and_actions_remain_available(self):
        for token in ('Dayanak yorumlar', 'Köprüyü Mesajlarda Paylaş', 'Köprüyü Kaydet'):
            self.assertIn(token, PAGE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
