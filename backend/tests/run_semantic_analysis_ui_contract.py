from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
TYPES = (ROOT / 'frontend' / 'lib' / 'types.ts').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')


class SemanticAnalysisUIContract(unittest.TestCase):
    def test_01_common_ground_shows_cross_stance_engine(self):
        self.assertIn('Görüş kümeleri arası ortaklık analizi', PAGE)
        self.assertIn('common_ground_details', PAGE)

    def test_02_common_ground_shows_evidence_counts(self):
        self.assertIn('görüş kümesi', PAGE)
        self.assertIn('yorum sinyali', PAGE)
        self.assertIn('Kanıt:', PAGE)

    def test_03_claim_radar_shows_hybrid_engine(self):
        self.assertIn('Hibrit doğrulanabilirlik analizi', PAGE)
        self.assertIn('claimTransformerCount', PAGE)

    def test_04_claim_cards_show_type_priority_and_verification(self):
        self.assertIn('c.claim_type', PAGE)
        self.assertIn('c.priority', PAGE)
        self.assertIn('Doğrulama için:', PAGE)
        self.assertIn('c.verification_need', PAGE)

    def test_05_bridge_shows_evidence_grounding(self):
        self.assertIn('KANITA DAYALI KÖPRÜ SENTEZİ', PAGE)
        self.assertIn('analysis.bridge.evidence_comment_ids', PAGE)
        self.assertIn('Dayanak yorumlar', PAGE)

    def test_06_types_include_semantic_fields(self):
        self.assertIn('export type CommonGroundItem', TYPES)
        self.assertIn('verification_need: string', TYPES)
        self.assertIn('evidence_comment_ids?: number[]', TYPES)

    def test_07_old_heuristic_claim_warning_removed(self):
        self.assertNotIn('İddia Radarı ile kaynak göstergeleri şu anda yapısal/heuristik kurallarla üretilir.', PAGE)

    def test_08_semantic_styles_exist(self):
        for cls in ['.semanticEngineBanner', '.claimVerification', '.bridgeEngineSummary', '.bridgeEvidenceRow']:
            self.assertIn(cls, CSS)


    def test_09_source_awareness_definition_is_visible(self):
        self.assertIn('Kaynak farkındalığı; kaynak, araştırma, veri, kanıt, istatistik veya ölçüm ihtiyacını', PAGE)
        self.assertIn('evidenceRequestCount', PAGE)
        self.assertIn('sourceAwarenessCommentCount', PAGE)

    def test_10_bridge_compactness_does_not_add_debug_clutter(self):
        self.assertNotIn('bridgeQuestionWordCount', PAGE)
        self.assertNotIn('{bridgeQuestionWordCount} kelime', PAGE)
        self.assertIn('.metricDefinition', CSS)



if __name__ == '__main__':
    unittest.main(verbosity=2)
