from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from app.analyzer import _stance_execution_description, analyze_demo, analyze_post
from app.argument_engine import _bridge_contrast, _divergence_text
from app.models import AnalysisResult, Comment, Post, StanceDetail


def make_post(title: str, comments: list[str], post_id: int = 8123) -> Post:
    return Post(
        id=post_id,
        author='Analiz Tutarlılığı Testi',
        handle='@tutarlilik',
        text=title,
        created_at='şimdi',
        comments=[
            Comment(id=index, author=f'K{index}', text=text, created_at='şimdi', likes=index)
            for index, text in enumerate(comments, 1)
        ],
    )


def hybrid_demo():
    with patch('app.stance_engine.load_model', return_value=Mock()):
        return analyze_demo(use_ai=True)


class AnalysisConsistencyRegression(unittest.TestCase):
    def test_01_structural_only_hybrid_summary_names_actual_method(self):
        summary = hybrid_demo().short_summary
        self.assertIn('hibrit analiz motorunun yapısal Türkçe sinyalleriyle', summary)
        self.assertIn('Transformer çıkarımı gerekmedi', summary)

    def test_02_structural_only_summary_does_not_claim_transformer_inference(self):
        self.assertNotIn('hibrit Transformer görüş analizi ile çıkarıldı', hybrid_demo().short_summary)

    def test_03_structural_only_engine_metadata_is_truthful(self):
        result = hybrid_demo()
        self.assertEqual(result.engine['stance_execution_mode'], 'structural-only')
        self.assertFalse(result.engine['stance_transformer_used'])

    def test_04_heuristic_summary_does_not_claim_hybrid_model(self):
        result = analyze_demo(use_ai=False)
        self.assertIn('yapısal heuristik yedekle', result.short_summary)
        self.assertEqual(result.engine['stance_execution_mode'], 'heuristic-fallback')

    def test_05_mixed_execution_reports_actual_model_and_rule_counts(self):
        details = [
            StanceDetail(comment_id=1, text='A', label='Destekleyen', confidence=0.73, engine='mDeBERTa-XNLI'),
            StanceDetail(comment_id=2, text='B', label='Koşullu / Dengeli', confidence=0.0, engine='yapısal'),
        ]
        description, mode = _stance_execution_description({'mode': 'hybrid-transformer'}, details)
        self.assertIn('1 yapısal kararı', description)
        self.assertIn('1 Transformer çıkarımıyla', description)
        self.assertEqual(mode, 'hybrid-structural-transformer')

    def test_06_model_only_execution_is_reported_separately(self):
        details = [StanceDetail(comment_id=1, text='A', label='Destekleyen', confidence=0.81, engine='mDeBERTa-XNLI')]
        description, mode = _stance_execution_description({'mode': 'hybrid-transformer'}, details)
        self.assertIn('1 Transformer çıkarımıyla', description)
        self.assertEqual(mode, 'transformer-only')

    def test_07_demo_summary_keeps_minority_ban_position(self):
        self.assertIn('Tam yasak veya güçlü sınırlama (%10)', hybrid_demo().short_summary)

    def test_08_demo_summary_keeps_majority_controlled_position(self):
        self.assertIn('Kontrollü ve kurallı kullanım (%50)', hybrid_demo().short_summary)

    def test_09_demo_summary_keeps_usage_protection_position(self):
        self.assertIn('Yasağa karşı / kullanım alanlarını koruma (%20)', hybrid_demo().short_summary)

    def test_10_neutral_questions_are_not_presented_as_a_policy_side(self):
        self.assertNotIn('Kanıt talebi / tarafsız değerlendirme (%20)', hybrid_demo().short_summary)

    def test_11_demo_bridge_preserves_three_real_positions(self):
        result = hybrid_demo()
        self.assertEqual(result.bridge['contrast_viewpoint_names'], [
            'Karşı / Sınırlayıcı', 'Koşullu / Dengeli', 'Destekleyen',
        ])

    def test_12_demo_divergence_mentions_ban_control_and_preservation(self):
        divergence = hybrid_demo().bridge['main_divergence'].casefold()
        self.assertIn('tam yasaklama', divergence)
        self.assertIn('kontrollü kullanım', divergence)
        self.assertIn('kullanım alanlarını koruma', divergence)

    def test_13_demo_bridge_question_compares_all_three_options(self):
        question = hybrid_demo().bridge['bridge_question'].casefold()
        self.assertIn('tam yasak', question)
        self.assertIn('kontrollü kullanım', question)
        self.assertIn('kullanım alanlarını koruma', question)

    def test_14_demo_bridge_question_stays_within_twenty_eight_words(self):
        self.assertLessEqual(len(hybrid_demo().bridge['bridge_question'].split()), 28)

    def test_15_bridge_evidence_includes_real_restrictive_comment(self):
        self.assertTrue({1, 8}.intersection(hybrid_demo().bridge['evidence_comment_ids']))

    def test_16_bridge_evidence_keeps_original_source_question(self):
        self.assertIn(6, hybrid_demo().bridge['evidence_comment_ids'])

    def test_17_contextual_contrast_labels_match_visible_viewpoint_cards(self):
        result = hybrid_demo()
        self.assertEqual(result.bridge['contrast_viewpoint_labels'], [
            'Tam yasak veya güçlü sınırlama',
            'Kontrollü ve kurallı kullanım',
            'Yasağa karşı / kullanım alanlarını koruma',
        ])

    def test_18_bridge_engine_reports_policy_spectrum_strategy(self):
        result = hybrid_demo()
        self.assertEqual(result.engine['bridge_contrast_strategy'], 'policy-spectrum')
        self.assertEqual(result.engine['bridge_contrast_viewpoint_count'], 3)

    def test_19_generic_three_way_discussion_does_not_invent_a_ban(self):
        result = analyze_post(make_post('Mahalle parkı büyütülmeli mi?', [
            'Bu öneriyi destekliyorum, faydalı olur.',
            'Projeye karşıyım, riskli olabilir.',
            'Bütçe ancak belirli şartlarla uygun olabilir.',
        ]), use_ai=False)
        self.assertNotIn('yasak', result.bridge['main_divergence'].casefold())
        self.assertNotIn('yasak', result.bridge['bridge_question'].casefold())
        self.assertEqual(result.engine['bridge_contrast_viewpoint_count'], 3)

    def test_20_two_policy_positions_keep_real_opposition(self):
        result = analyze_post(make_post('Yapay zekâ yasaklanmalı mı?', [
            'Yapay zekâ faydalı ve yararlı bir araçtır.',
            'Kesinlikle yasaklanmalı.',
        ]), use_ai=False)
        self.assertEqual(set(result.bridge['contrast_viewpoint_names']), {'Destekleyen', 'Karşı / Sınırlayıcı'})
        self.assertIn('yasaklama', result.bridge['main_divergence'].casefold())

    def test_21_neutral_cluster_is_never_invented_as_opposition(self):
        result = analyze_post(make_post('Yeni karar nasıl düzenlenmeli?', [
            'Kontrollü kullanım daha doğru.',
            'Bu kararın dayandığı veri nedir?',
        ]), use_ai=False)
        self.assertNotIn('Soru / Tarafsız', result.bridge['contrast_viewpoint_names'])

    def test_22_question_impact_uses_contextual_controlled_label(self):
        for question in hybrid_demo().unanswered_questions:
            self.assertIn('Kontrollü ve kurallı kullanım', question.impact)

    def test_23_question_impact_uses_contextual_restriction_label(self):
        for question in hybrid_demo().unanswered_questions:
            self.assertIn('Tam yasak veya güçlü sınırlama', question.impact)

    def test_24_question_impact_hides_old_technical_cluster_names(self):
        for question in hybrid_demo().unanswered_questions:
            self.assertNotIn('Koşullu / Dengeli', question.impact)
            self.assertNotIn('Karşı / Sınırlayıcı', question.impact)

    def test_25_question_affected_labels_keep_canonical_event_identity(self):
        for question in hybrid_demo().unanswered_questions:
            self.assertIn('Koşullu / Dengeli', question.affected_viewpoints)
            self.assertTrue(question.identity_key.startswith('q120|'))

    def test_26_old_bridge_snapshot_without_contrast_fields_still_loads(self):
        payload = hybrid_demo().model_dump()
        payload['bridge'].pop('contrast_viewpoint_names')
        payload['bridge'].pop('contrast_viewpoint_labels')
        restored = AnalysisResult.model_validate(payload)
        self.assertTrue(restored.bridge['bridge_question'])

    def test_27_existing_source_awareness_and_questions_remain_stable(self):
        result = hybrid_demo()
        self.assertEqual(result.indicators['source_awareness'], 25)
        self.assertEqual({item.comment_id for item in result.unanswered_questions}, {6, 13})

    def test_28_existing_corrected_comments_keep_their_positions(self):
        labels = {item.comment_id: item.label for item in hybrid_demo().stance_details}
        self.assertEqual(labels[7], 'Koşullu / Dengeli')
        self.assertEqual(labels[11], 'Soru / Tarafsız')

    def test_29_generic_contrast_wording_is_topic_safe(self):
        labels = ['Destekleyen', 'Koşullu / Dengeli', 'Karşı / Sınırlayıcı']
        self.assertNotIn('yasak', _divergence_text(labels, False))
        self.assertNotIn('yasak', _bridge_contrast(labels, False))

    def test_30_model_confidence_is_not_fabricated_for_structural_demo(self):
        result = hybrid_demo()
        self.assertEqual(result.indicators['ai_average_confidence'], 0)
        self.assertEqual(result.engine['transformer_count'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
