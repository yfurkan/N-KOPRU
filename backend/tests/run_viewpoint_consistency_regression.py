from __future__ import annotations

import unittest
from collections import Counter
from unittest.mock import Mock, patch

from app.analyzer import analyze_demo, classify_viewpoint_heuristic
from app.demo import BASE_COMMENTS, DEMO_POST
from app.stance_engine import _structural_label, classify_stances, semantic_guardrail_label
from app.viewpoint_engine import _main_argument


class ViewpointConsistencyRegression(unittest.TestCase):
    def test_01_personal_bounded_usage_is_conditional(self):
        label, reason = _structural_label(BASE_COMMENTS[6][1])
        self.assertEqual(label, 'Koşullu / Dengeli')
        self.assertIn('sınırlı kişisel kullanım', reason)

    def test_02_source_critique_is_evidence_neutral(self):
        label, reason = _structural_label(BASE_COMMENTS[10][1])
        self.assertEqual(label, 'Soru / Tarafsız')
        self.assertIn('kaynak/veri eleştirisi', reason)

    def test_03_limited_learning_purpose_is_not_a_ban(self):
        text = 'Sadece konuyu anlamak için kullanıyorum.'
        self.assertEqual(semantic_guardrail_label(text)[0], 'Koşullu / Dengeli')

    def test_04_negative_delegation_with_personal_use_is_conditional(self):
        text = 'Ödevimi ona yaptırmıyorum, yalnızca açıklama alıyorum.'
        self.assertEqual(semantic_guardrail_label(text)[0], 'Koşullu / Dengeli')

    def test_05_full_assignment_delegation_is_not_guarded(self):
        text = 'Yapay zekâyı kullanıyorum ve ödevimi ona yazdırıyorum.'
        self.assertEqual(semantic_guardrail_label(text), (None, None))

    def test_06_complaint_about_other_students_remains_restrictive(self):
        self.assertEqual(_structural_label(BASE_COMMENTS[7][1])[0], 'Karşı / Sınırlayıcı')

    def test_07_real_ban_advocacy_remains_restrictive(self):
        self.assertEqual(_structural_label(BASE_COMMENTS[0][1])[0], 'Karşı / Sınırlayıcı')

    def test_08_unsourced_usage_risk_remains_conditional(self):
        self.assertEqual(_structural_label(BASE_COMMENTS[3][1])[0], 'Koşullu / Dengeli')
        self.assertEqual(semantic_guardrail_label(BASE_COMMENTS[3][1]), (None, None))

    def test_09_source_free_percentage_is_neutral(self):
        text = 'Kaynak gösterilmediği sürece bu yüzdeye güvenilemez.'
        self.assertEqual(semantic_guardrail_label(text)[0], 'Soru / Tarafsız')

    def test_10_missing_data_for_a_claim_is_neutral(self):
        text = 'Veri olmadan bu istatistik anlamlı değil.'
        self.assertEqual(semantic_guardrail_label(text)[0], 'Soru / Tarafsız')

    def test_11_requested_evidence_for_a_claim_is_neutral(self):
        text = 'Bu iddia için kaynak paylaşılmalı.'
        self.assertEqual(semantic_guardrail_label(text)[0], 'Soru / Tarafsız')

    def test_12_general_source_mention_is_not_hijacked(self):
        text = 'Kaynak göstermek akademik çalışmalarda önemlidir.'
        self.assertEqual(semantic_guardrail_label(text), (None, None))

    def test_13_explicit_question_keeps_question_reason(self):
        label, reason = _structural_label('Veri olmadan bu istatistik açıklanabilir mi?')
        self.assertEqual(label, 'Soru / Tarafsız')
        self.assertEqual(reason, 'yapısal soru sinyali')

    def test_14_original_twenty_demo_comments_are_structurally_resolved(self):
        unresolved = [index for index, (_, text) in enumerate(BASE_COMMENTS, 1) if _structural_label(text)[0] is None]
        self.assertEqual(unresolved, [])

    def test_15_hybrid_demo_does_not_call_transformer_for_resolved_comments(self):
        model = Mock()
        with patch('app.stance_engine.load_model', return_value=model):
            details, info = classify_stances(DEMO_POST.text, DEMO_POST.comments[:20])
        model.assert_not_called()
        self.assertEqual(len(details), 20)
        self.assertEqual(info['rule_count'], 20)
        self.assertEqual(info['transformer_count'], 0)

    def test_16_hybrid_demo_has_expected_corrected_distribution(self):
        with patch('app.stance_engine.load_model', return_value=Mock()):
            details, _ = classify_stances(DEMO_POST.text, DEMO_POST.comments[:20])
        self.assertEqual(Counter(item['label'] for item in details), {
            'Koşullu / Dengeli': 10,
            'Karşı / Sınırlayıcı': 2,
            'Destekleyen': 4,
            'Soru / Tarafsız': 4,
        })

    def test_17_hybrid_guardrails_are_counted_truthfully(self):
        with patch('app.stance_engine.load_model', return_value=Mock()):
            _, info = classify_stances(DEMO_POST.text, DEMO_POST.comments[:20])
        self.assertEqual(info['semantic_guardrail_count'], 2)

    def test_18_hybrid_corrected_comment_ids_keep_expected_labels(self):
        with patch('app.stance_engine.load_model', return_value=Mock()):
            details, _ = classify_stances(DEMO_POST.text, DEMO_POST.comments[:20])
        labels = {item['comment_id']: item['label'] for item in details}
        self.assertEqual(labels[7], 'Koşullu / Dengeli')
        self.assertEqual(labels[11], 'Soru / Tarafsız')

    def test_19_heuristic_fallback_uses_same_personal_usage_guardrail(self):
        self.assertEqual(classify_viewpoint_heuristic(BASE_COMMENTS[6][1]), 'Koşullu / Dengeli')

    def test_20_heuristic_fallback_uses_same_evidence_guardrail(self):
        self.assertEqual(classify_viewpoint_heuristic(BASE_COMMENTS[10][1]), 'Soru / Tarafsız')

    def test_21_heuristic_metadata_counts_both_guardrails(self):
        result = analyze_demo(use_ai=False)
        self.assertEqual(result.engine['semantic_guardrail_count'], 2)

    def test_22_personal_use_comment_is_in_controlled_evidence(self):
        result = analyze_demo(use_ai=False)
        controlled = next(item for item in result.viewpoints if item.name == 'Koşullu / Dengeli')
        self.assertIn(7, controlled.evidence_comment_ids)

    def test_23_source_critique_comment_is_in_neutral_evidence(self):
        result = analyze_demo(use_ai=False)
        neutral = next(item for item in result.viewpoints if item.name == 'Soru / Tarafsız')
        self.assertIn(11, neutral.evidence_comment_ids)

    def test_24_restrictive_copy_does_not_repeat_risk(self):
        sentence = _main_argument('Karşı / Sınırlayıcı', ['Risk ve olumsuz etki'], True)
        self.assertNotIn('risk ve olumsuz etki üzerindeki riskler', sentence.casefold())
        self.assertIn('sakıncalar', sentence)

    def test_25_existing_source_awareness_remains_twenty_five_percent(self):
        self.assertEqual(analyze_demo(use_ai=False).indicators['source_awareness'], 25)

    def test_26_existing_questions_and_short_bridge_are_preserved(self):
        result = analyze_demo(use_ai=False)
        self.assertEqual({item.comment_id for item in result.unanswered_questions}, {6, 13})
        self.assertLessEqual(len(result.bridge['bridge_question'].split()), 28)


if __name__ == '__main__':
    unittest.main(verbosity=2)
