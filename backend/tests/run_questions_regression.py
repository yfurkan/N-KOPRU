from __future__ import annotations

import unittest

from app.analyzer import analyze_demo, analyze_post
from app.models import AnalysisResult, Comment, Post


def make_post(*texts: str, post_id: int = 8120) -> Post:
    return Post(
        id=post_id,
        author='Soru Testi',
        handle='@soru_testi',
        text='Tartışmadaki sorular nasıl değerlendirilmelidir?',
        created_at='şimdi',
        comments=[
            Comment(id=index + 1, author=f'K{index + 1}', text=text, created_at='şimdi', likes=0)
            for index, text in enumerate(texts)
        ],
    )


class QuestionAnalysisRegression(unittest.TestCase):
    def analyze(self, *texts: str):
        return analyze_post(make_post(*texts), use_ai=False)

    def test_01_demo_keeps_two_explicit_evidence_questions(self):
        result = analyze_demo(use_ai=False)
        self.assertEqual({item.comment_id for item in result.unanswered_questions}, {6, 13})
        self.assertTrue(all(item.question_type == 'Kaynak / Kanıt Talebi' for item in result.unanswered_questions))
        self.assertTrue(all(item.answer_status == 'Cevapsız' for item in result.unanswered_questions))

    def test_02_interrogative_words_inside_statements_are_not_questions(self):
        result = self.analyze(
            'Sorun yasaklamak değil, nasıl kullandığımız.',
            'Öğretmenler nasıl kullanılacağını öğretmeli.',
            'Hangi kullanım biçimlerinin öğrenmeyi güçlendirdiğini ölçmeliyiz.',
        )
        self.assertEqual(result.unanswered_questions, [])

    def test_03_evidence_request_without_question_mark_is_detected(self):
        result = self.analyze(
            'Bu yüzde için güvenilir kaynak paylaşılmalı.',
            'Kontrollü kullanım yararlı olabilir.',
            'Tam yasak daha güvenli olabilir.',
        )
        self.assertEqual(len(result.unanswered_questions), 1)
        item = result.unanswered_questions[0]
        self.assertEqual(item.question_type, 'Kaynak / Kanıt Talebi')
        self.assertEqual(item.answer_status, 'Cevapsız')

    def test_04_rhetorical_question_is_separated(self):
        result = self.analyze(
            'Bu nasıl saçmalık?',
            'Uygulama kurallarla sınırlandırılabilir.',
            'Tam yasak doğru değil.',
        )
        self.assertEqual(result.unanswered_questions, [])
        self.assertEqual(len(result.rhetorical_questions), 1)
        self.assertEqual(result.rhetorical_questions[0].answer_status, 'Retorik')
        self.assertEqual(result.engine['question_rhetorical_count'], 1)

    def test_05_information_question_is_classified(self):
        result = self.analyze(
            'Gece bildirimleri neden uyku düzenini bozuyor?',
            'Bildirimler sessize alınabilir.',
            'Kullanıcı kontrolü korunmalı.',
        )
        item = result.unanswered_questions[0]
        self.assertEqual(item.question_type, 'Bilgi / Açıklama Sorusu')
        self.assertGreaterEqual(item.confidence, 0.9)

    def test_06_decision_question_is_classified(self):
        result = self.analyze(
            'Gece bildirimleri varsayılan olarak kapatılmalı mı?',
            'Kullanıcı isterse açabilmeli.',
            'Gençler için daha sınırlı olmalı.',
        )
        self.assertEqual(result.unanswered_questions[0].question_type, 'Uygulama / Karar Sorusu')

    def test_07_semantic_repeats_are_grouped(self):
        result = self.analyze(
            'Yasaklamanın öğrenci başarısına etkisini gösteren güvenilir bir araştırma var mı?',
            'Yapay zekâ yasağının başarı üzerindeki etkisine dair bir çalışma bulunuyor mu?',
            'Kontrollü kullanım daha doğru olabilir.',
        )
        self.assertEqual(len(result.unanswered_questions), 1)
        item = result.unanswered_questions[0]
        self.assertEqual(item.evidence_comment_ids, [1, 2])
        self.assertEqual(item.repeated_comment_ids, [2])
        self.assertEqual(result.engine['question_grouped_repeat_count'], 1)

    def test_08_later_direct_explanation_marks_answered(self):
        result = self.analyze(
            'Gece bildirimleri neden uyku düzenini bozuyor?',
            'Çünkü gece bildirimleri uykuyu bölüyor ve yeniden uykuya geçişi geciktiriyor.',
            'Sessize alma seçeneği kullanıcıda kalmalı.',
        )
        item = result.unanswered_questions[0]
        self.assertEqual(item.answer_status, 'Cevaplandı')
        self.assertEqual(item.answer_comment_ids, [2])
        self.assertEqual(item.priority, 'Düşük')

    def test_09_weak_evidence_link_marks_partially_answered(self):
        result = self.analyze(
            'Yapay zekâ kullanımının başarıyı artırdığına dair güvenilir bir araştırma var mı?',
            'Bazı araştırmalarda başarı artışı bildirildi ancak örneklem ve yöntem açıklanmadı.',
            'Bu nedenle daha güçlü karşılaştırma gerekli.',
        )
        item = result.unanswered_questions[0]
        self.assertEqual(item.answer_status, 'Kısmen cevaplandı')
        self.assertEqual(item.answer_comment_ids, [2])

    def test_10_another_question_does_not_count_as_answer(self):
        result = self.analyze(
            'Bu oranın dayandığı veri nedir?',
            'Peki örneklem hangi öğrencilerden oluşuyor?',
            'Kaynak belirtilmeden kesin hüküm verilmemeli.',
        )
        item = result.unanswered_questions[0]
        self.assertEqual(item.answer_status, 'Cevapsız')
        self.assertEqual(item.answer_comment_ids, [])

    def test_11_question_links_to_relevant_viewpoint_clusters(self):
        result = analyze_demo(use_ai=False)
        item = next(q for q in result.unanswered_questions if q.comment_id == 6)
        self.assertGreaterEqual(len(item.affected_viewpoints), 2)
        self.assertNotIn('Soru / Tarafsız', item.affected_viewpoints)

    def test_12_cards_keep_evidence_and_impact_explanation(self):
        result = analyze_demo(use_ai=False)
        item = result.unanswered_questions[0]
        self.assertEqual(item.evidence_comment_ids, [item.comment_id])
        self.assertIn('Yanıtlanırsa', item.impact)
        self.assertTrue(item.identity_key.startswith('q120|'))

    def test_13_engine_metadata_reports_status_counts(self):
        result = self.analyze(
            'Gece bildirimleri neden uyku düzenini bozuyor?',
            'Çünkü gece bildirimleri uykuyu bölüyor.',
            'Bu nasıl saçmalık?',
            'Bu oran için kaynak paylaşılmalı.',
        )
        self.assertEqual(result.engine['question_engine'], 'structural-semantic-question')
        self.assertEqual(result.engine['question_answered_count'], 1)
        self.assertEqual(result.engine['question_unanswered_count'], 1)
        self.assertEqual(result.engine['question_rhetorical_count'], 1)
        self.assertIn('question_elapsed_ms', result.engine)

    def test_14_old_question_snapshot_remains_backward_compatible(self):
        current = analyze_demo(use_ai=False).model_dump()
        current.pop('rhetorical_questions', None)
        for question in current['unanswered_questions']:
            for key in (
                'question_type', 'answer_status', 'priority', 'confidence',
                'evidence_comment_ids', 'repeated_comment_ids', 'answer_comment_ids',
                'affected_viewpoints', 'impact', 'engine', 'detection_reason', 'identity_key',
            ):
                question.pop(key, None)
        restored = AnalysisResult.model_validate(current)
        self.assertEqual(restored.rhetorical_questions, [])
        self.assertEqual(restored.unanswered_questions[0].answer_status, 'Cevapsız')
        self.assertEqual(restored.unanswered_questions[0].priority, 'Orta')

    def test_15_answered_question_is_not_counted_as_open(self):
        result = self.analyze(
            'Gece bildirimleri neden uyku düzenini bozuyor?',
            'Çünkü gece bildirimleri uykuyu bölüyor ve uyanıklığı artırıyor.',
            'Sessize alma seçeneği bulunmalı.',
        )
        self.assertEqual(result.indicators['question_count'], 1)
        self.assertEqual(result.indicators['answered_question_count'], 1)
        self.assertEqual(result.indicators['unanswered_question_count'], 0)
        self.assertIn('0 açık soru', result.short_summary)


if __name__ == '__main__':
    unittest.main(verbosity=2)
