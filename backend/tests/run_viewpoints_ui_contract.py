from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
TYPES = (ROOT / 'frontend' / 'lib' / 'types.ts').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')


class ViewpointUIContract(unittest.TestCase):
    def test_01_contextual_name_preserves_legacy_name_fallback(self):
        self.assertIn('v.display_name || v.name', PAGE)

    def test_02_cluster_comment_count_and_percentage_are_visible(self):
        self.assertIn('{representedCount} yorum', PAGE)
        self.assertIn('%{v.percentage}', PAGE)

    def test_03_main_argument_is_explicit(self):
        self.assertIn('Bu görüş neyi savunuyor?', PAGE)
        self.assertIn('v.main_argument || v.summary', PAGE)

    def test_04_representative_comments_show_identity_and_source_text(self):
        self.assertIn('Temsilci yorumlar', PAGE)
        self.assertIn('v.representative_comments.map', PAGE)
        self.assertIn('item.comment_id', PAGE)
        self.assertIn('item.author', PAGE)

    def test_05_relationships_show_opposition_and_common_ground(self):
        self.assertIn('Diğer görüşlerle ilişkisi', PAGE)
        self.assertIn('Ayrıştığı yaklaşım:', PAGE)
        self.assertIn('Ortak zemin:', PAGE)

    def test_06_claim_and_question_links_are_visible(self):
        self.assertIn('İddia bağlantısı:', PAGE)
        self.assertIn('Soru bağlantısı:', PAGE)

    def test_07_model_confidence_is_not_presented_as_truth(self):
        self.assertIn('yalnızca Transformer ile değerlendirilen', PAGE)
        self.assertIn('görüşün haklılığını göstermez', PAGE)

    def test_08_structural_and_model_counts_are_separated(self):
        self.assertIn('yapısal değerlendirme', PAGE)
        self.assertIn('v.model_comment_count', PAGE)
        self.assertIn('v.average_model_confidence', PAGE)

    def test_09_question_cards_use_the_same_contextual_labels(self):
        self.assertIn('viewpointLabelMap[name] || name', PAGE)
        self.assertIn('q.affected_viewpoints.map', PAGE)

    def test_10_stance_examples_use_the_same_contextual_labels(self):
        self.assertIn('viewpointLabelMap[s.label] || s.label', PAGE)

    def test_11_types_include_representative_evidence(self):
        self.assertIn('export type ViewpointEvidence', TYPES)
        self.assertIn('representative_comments: ViewpointEvidence[]', TYPES)

    def test_12_types_include_full_viewpoint_contract(self):
        for field in (
            'display_name: string', 'comment_count: number', 'main_argument: string',
            'dominant_themes: string[]', 'shared_themes: string[]',
            'opposing_viewpoint_names: string[]', 'related_claim_comment_ids: number[]',
            'related_question_comment_ids: number[]', 'structural_comment_count: number',
            'model_comment_count: number', 'average_model_confidence: number',
        ):
            self.assertIn(field, TYPES)

    def test_13_semantic_viewpoint_styles_exist(self):
        for selector in (
            '.semanticViewpointCard', '.viewpointArgument', '.viewpointRelationship',
            '.viewpointRepresentatives', '.viewpointRepresentative', '.viewpointConfidenceNote',
        ):
            self.assertIn(selector, CSS)

    def test_14_mobile_viewpoint_style_exists(self):
        self.assertIn('.viewpointRepresentative>div{align-items:flex-start;flex-direction:column}', CSS)


if __name__ == '__main__':
    unittest.main(verbosity=2)
