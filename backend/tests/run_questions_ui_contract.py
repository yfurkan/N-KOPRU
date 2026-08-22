from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
TYPES = (ROOT / 'frontend' / 'lib' / 'types.ts').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')


class QuestionAnalysisUIContract(unittest.TestCase):
    def test_01_question_engine_explanation_is_visible(self):
        self.assertIn('Yapısal-semantik soru analizi', PAGE)
        self.assertIn('tekrarlar gruplanır', PAGE)

    def test_02_status_counts_are_visible(self):
        for token in ('questionUnansweredCount', 'questionPartialCount', 'questionAnsweredCount', 'questionRhetoricalCount'):
            self.assertIn(token, PAGE)

    def test_03_question_cards_show_type_status_and_priority(self):
        self.assertIn('q.question_type', PAGE)
        self.assertIn('q.answer_status', PAGE)
        self.assertIn('q.priority', PAGE)

    def test_04_question_cards_show_evidence_and_answer_links(self):
        self.assertIn('Dayanak yorumlar', PAGE)
        self.assertIn('Etkilediği görüşler', PAGE)
        self.assertIn('Yanıt bağlantıları', PAGE)

    def test_05_question_cards_explain_possible_impact(self):
        self.assertIn('Bu soru cevaplanırsa ne değişebilir?', PAGE)
        self.assertIn('q.impact', PAGE)

    def test_06_detection_confidence_is_not_presented_as_truth(self):
        self.assertIn('Soru tespit güveni', PAGE)
        self.assertIn('verilen yanıtın doğruluğunu göstermez', PAGE)

    def test_07_rhetorical_questions_are_separate(self):
        self.assertIn('Retorik ifadeler ayrı tutuldu', PAGE)
        self.assertIn('analysis.rhetorical_questions', PAGE)

    def test_08_types_include_full_question_contract(self):
        for field in (
            'question_type: string', 'answer_status: string', 'priority: string',
            'evidence_comment_ids: number[]', 'answer_comment_ids: number[]',
            'affected_viewpoints: string[]', 'impact: string', 'identity_key: string',
        ):
            self.assertIn(field, TYPES)
        self.assertIn('rhetorical_questions: QuestionItem[]', TYPES)

    def test_09_question_styles_exist(self):
        for cls in ('.semanticQuestionCard', '.questionEvidenceGrid', '.questionImpact', '.rhetoricalSection'):
            self.assertIn(cls, CSS)

    def test_10_open_question_badge_uses_status_counts(self):
        self.assertIn('{questionUnansweredCount + questionPartialCount} açık soru', PAGE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
