from __future__ import annotations

import unittest

from app.analyzer import analyze_demo, analyze_post
from app.models import Comment, Post


class SemanticAnalysisRegression(unittest.TestCase):
    def test_01_demo_claim_radar_keeps_only_verifiable_candidates(self):
        result = analyze_demo(use_ai=False)
        ids = {item.comment_id for item in result.claims}
        self.assertEqual(ids, {1, 4, 10})
        self.assertNotIn(5, ids)   # yönerge önerisi
        self.assertNotIn(7, ids)   # kişisel kullanım deneyimi
        self.assertNotIn(17, ids)  # normatif şeffaflık önerisi

    def test_02_numeric_claim_is_high_priority(self):
        result = analyze_demo(use_ai=False)
        claim = next(item for item in result.claims if item.comment_id == 10)
        self.assertEqual(claim.claim_type, 'Nicel / İstatistiksel')
        self.assertEqual(claim.priority, 'Yüksek')
        self.assertEqual(claim.source_status, 'Kaynak gerekli')
        self.assertGreaterEqual(claim.confidence, 0.9)
        self.assertIn('Örneklem', claim.verification_need)

    def test_03_causal_claim_gets_effect_verification_guidance(self):
        result = analyze_demo(use_ai=False)
        claim = next(item for item in result.claims if item.comment_id == 4)
        self.assertEqual(claim.claim_type, 'Etki / Nedensellik')
        self.assertIn('Kontrollü', claim.verification_need)

    def test_04_explicit_source_marker_is_recognized(self):
        post = Post(
            id=7001, author='T', handle='@t', text='Kaynak testi', created_at='şimdi',
            comments=[
                Comment(id=1, author='A', text='Araştırmaya göre kullanım başarıyı %12 artırıyor.', created_at='şimdi', likes=0),
                Comment(id=2, author='B', text='Bence yasaklanmalı.', created_at='şimdi', likes=0),
                Comment(id=3, author='C', text='Kaynak nedir?', created_at='şimdi', likes=0),
            ],
        )
        result = analyze_post(post, use_ai=False)
        self.assertEqual(len(result.claims), 1)
        self.assertEqual(result.claims[0].source_status, 'Kaynak işareti var')

    def test_05_common_ground_requires_cross_stance_evidence(self):
        result = analyze_demo(use_ai=False)
        self.assertTrue(result.common_ground_details)
        self.assertTrue(all(item.stance_count >= 2 for item in result.common_ground_details[:2]))
        self.assertTrue(all(item.evidence_comment_ids for item in result.common_ground_details))

    def test_06_demo_common_ground_finds_learning_theme(self):
        result = analyze_demo(use_ai=False)
        themes = {item.theme for item in result.common_ground_details}
        self.assertIn('Öğrenme etkisinin ölçülmesi', themes)

    def test_07_bridge_is_not_a_raw_unanswered_question(self):
        result = analyze_demo(use_ai=False)
        raw_questions = {item.text for item in result.unanswered_questions}
        self.assertNotIn(result.bridge['bridge_question'], raw_questions)
        self.assertIn('hangi ortak ölçütlerle', result.bridge['bridge_question'])

    def test_08_bridge_uses_evidence_comment_ids(self):
        result = analyze_demo(use_ai=False)
        ids = result.bridge.get('evidence_comment_ids', [])
        self.assertGreaterEqual(len(ids), 3)
        self.assertIn(6, ids)  # güvenilir araştırma sorusu

    def test_09_bridge_divergence_prefers_substantive_stances(self):
        result = analyze_demo(use_ai=False)
        divergence = result.bridge['main_divergence']
        self.assertNotIn('Diğer / Nötr', divergence)
        self.assertTrue('kısıtlama' in divergence.casefold() or 'serbest' in divergence.casefold())

    def test_10_engine_metadata_reports_all_three_layers(self):
        result = analyze_demo(use_ai=False)
        self.assertEqual(result.engine['claim_engine'], 'structural-semantic-claim')
        self.assertEqual(result.engine['common_ground_engine'], 'cross-stance-semantic-ground')
        self.assertEqual(result.engine['bridge_engine'], 'evidence-grounded-bridge')
        self.assertIn('bridge_evidence_count', result.engine)

    def test_11_question_with_percentage_is_not_misclassified_as_claim(self):
        post = Post(
            id=7002, author='T', handle='@t', text='Soru testi', created_at='şimdi',
            comments=[
                Comment(id=1, author='A', text='Bu %70 oranının kaynağı nedir?', created_at='şimdi', likes=0),
                Comment(id=2, author='B', text='Bence kontrollü olmalı.', created_at='şimdi', likes=0),
                Comment(id=3, author='C', text='Kullanım amacı önemli.', created_at='şimdi', likes=0),
            ],
        )
        result = analyze_post(post, use_ai=False)
        self.assertEqual(result.claims, [])
        self.assertEqual(result.unanswered_questions[0].comment_id, 1)

    def test_12_personal_experience_does_not_become_general_claim(self):
        post = Post(
            id=7003, author='T', handle='@t', text='Deneyim testi', created_at='şimdi',
            comments=[
                Comment(id=1, author='A', text='Ben ders çalışırken açıklama almak için kullanıyorum.', created_at='şimdi', likes=0),
                Comment(id=2, author='B', text='Bence yararlı olabilir.', created_at='şimdi', likes=0),
                Comment(id=3, author='C', text='Kurallı kullanmak daha iyi.', created_at='şimdi', likes=0),
            ],
        )
        result = analyze_post(post, use_ai=False)
        self.assertFalse(result.claims)

    def test_13_common_ground_has_safe_fallback_when_topics_do_not_overlap(self):
        post = Post(
            id=7004, author='T', handle='@t', text='Dağınık konu', created_at='şimdi',
            comments=[
                Comment(id=1, author='A', text='Tamamen karşıyım.', created_at='şimdi', likes=0),
                Comment(id=2, author='B', text='Bunu destekliyorum.', created_at='şimdi', likes=0),
                Comment(id=3, author='C', text='Kararsızım.', created_at='şimdi', likes=0),
            ],
        )
        result = analyze_post(post, use_ai=False)
        self.assertTrue(result.common_ground_details)
        self.assertEqual(result.common_ground_details[0].theme, 'Ortak değerlendirme ölçütleri')
        self.assertLessEqual(result.common_ground_details[0].confidence, 0.55)

    def test_14_bridge_exposes_confidence_and_engine(self):
        result = analyze_demo(use_ai=False)
        self.assertGreaterEqual(result.bridge['confidence'], 0.7)
        self.assertEqual(result.bridge['engine'], 'Kanıta dayalı Köprü sentezi')

    def test_15_analysis_serialization_keeps_semantic_fields(self):
        result = analyze_demo(use_ai=False)
        data = result.model_dump()
        self.assertIn('common_ground_details', data)
        self.assertIn('verification_need', data['claims'][0])
        self.assertIn('evidence_comment_ids', data['bridge'])


    def test_16_v1_snapshot_json_remains_backward_compatible(self):
        from app.models import AnalysisResult
        current = analyze_demo(use_ai=False).model_dump()
        current.pop('common_ground_details', None)
        for claim in current['claims']:
            for key in ('claim_type','verification_need','priority','confidence','engine','detection_reason'):
                claim.pop(key, None)
        current['bridge'] = {
            'common_acceptance': current['bridge']['common_acceptance'],
            'main_divergence': current['bridge']['main_divergence'],
            'missing_information': current['bridge']['missing_information'],
            'bridge_question': current['bridge']['bridge_question'],
        }
        restored = AnalysisResult.model_validate(current)
        self.assertEqual(restored.common_ground_details, [])
        self.assertTrue(restored.claims)
        self.assertEqual(restored.claims[0].priority, 'Orta')



    def test_17_source_awareness_counts_evidence_signals_not_only_citations(self):
        result = analyze_demo(use_ai=False)
        self.assertEqual(result.indicators['source_awareness'], 25)
        self.assertEqual(result.engine['source_awareness_engine'], 'comment-level-evidence-awareness')
        self.assertEqual(result.engine['source_awareness_comment_count'], 5)
        self.assertEqual(result.engine['evidence_request_count'], 2)

    def test_18_source_request_alone_contributes_to_awareness(self):
        post = Post(
            id=7005, author='T', handle='@t', text='Kaynak farkındalığı', created_at='şimdi',
            comments=[
                Comment(id=1, author='A', text='Bu konuda güvenilir bir araştırma var mı?', created_at='şimdi', likes=0),
                Comment(id=2, author='B', text='Bence kontrollü kullanılmalı.', created_at='şimdi', likes=0),
                Comment(id=3, author='C', text='Tamamen karşıyım.', created_at='şimdi', likes=0),
            ],
        )
        result = analyze_post(post, use_ai=False)
        self.assertEqual(result.indicators['source_awareness'], 33)
        self.assertEqual(result.engine['evidence_request_count'], 1)

    def test_19_bridge_question_obeys_compact_rule(self):
        result = analyze_demo(use_ai=False)
        question = result.bridge['bridge_question']
        self.assertLessEqual(len(question.split()), 28)
        self.assertNotIn('başlıklı tartışmada', question)
        self.assertIn('güvenilir verilerle', question)

    def test_20_bridge_engine_reports_compactness_metadata(self):
        result = analyze_demo(use_ai=False)
        self.assertEqual(result.engine['bridge_question_word_count'], len(result.bridge['bridge_question'].split()))
        self.assertEqual(result.engine['bridge_question_max_words'], 28)
        self.assertLessEqual(result.engine['bridge_question_word_count'], result.engine['bridge_question_max_words'])



if __name__ == '__main__':
    unittest.main(verbosity=2)
