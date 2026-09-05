"""v1.5.0: konuya özgü ortak zemin ve tekrarsız Köprü dili."""
from __future__ import annotations

import unittest

from app.analyzer import analyze_post, build_custom_post
from app.topic_context import resolve_topic_context


CASES = [
    (
        'Şirketlerde uzaktan çalışma sürmeli mi?',
        [
            'Çalışanların mekân seçimini korumasından yanayım.',
            'Kritik ekip toplantıları yalnızca ofiste yapılmalı.',
            'Uzaktan çalışma açık kurallarla uygulanmalı.',
            'Verimlilik konusunda araştırma var mı?',
        ],
        ('verimlilik', 'ekip koordinasyonu', 'çalışan esnekliği'),
    ),
    (
        'Mahalle parkları akşam açık kalmalı mı?',
        [
            'Park erişimi sürmeli.',
            'Gece park kapatılmalı.',
            'Güvenlik sağlanırsa saatler uzatılabilir.',
            'Şikâyet verileri var mı?',
        ],
        ('erişim hakkı', 'çevre huzuru', 'güvenlik'),
    ),
    (
        'Kampüste gece ulaşımı sürmeli mi?',
        [
            'Gece servisi devam etmeli.',
            'Düşük talepte hizmet kaldırılmalı.',
            'Ana hatlar talebe göre çalışabilir.',
            'Yolcu sayısı açıklandı mı?',
        ],
        ('erişim', 'güvenlik', 'hizmet verimliliği'),
    ),
]


class FinalistTopicLanguageTests(unittest.TestCase):
    def test_01_remote_work_criteria_are_concrete(self):
        context = resolve_topic_context(CASES[0][0])
        self.assertEqual(context.decision_criteria, CASES[0][2])

    def test_02_remote_bridge_has_no_old_repetition(self):
        title, comments, _ = CASES[0]
        result = analyze_post(build_custom_post(title, comments), use_ai=False)
        bridge = result.bridge['bridge_question'].casefold()
        self.assertNotIn('uzaktan çalışma etkileri', bridge)
        self.assertEqual(bridge.count('uzaktan çalışma'), 1)

    def test_03_remote_bridge_names_three_decision_dimensions(self):
        title, comments, criteria = CASES[0]
        bridge = analyze_post(build_custom_post(title, comments), use_ai=False).bridge['bridge_question'].casefold()
        for criterion in criteria:
            self.assertIn(criterion, bridge)

    def test_04_specific_common_ground_is_not_generic(self):
        for title, comments, criteria in CASES:
            result = analyze_post(build_custom_post(title, comments), use_ai=False)
            ground = result.common_ground[0].casefold()
            self.assertTrue(any(criterion in ground for criterion in criteria))
            self.assertNotIn('belirgin bir içerik uzlaşısı henüz oluşmasa', ground)

    def test_05_specific_ground_uses_multiple_stances(self):
        for title, comments, _ in CASES:
            result = analyze_post(build_custom_post(title, comments), use_ai=False)
            detail = result.common_ground_details[0]
            self.assertGreaterEqual(detail.stance_count, 2)
            self.assertGreaterEqual(len(detail.evidence_comment_ids), 2)

    def test_06_all_contextual_bridge_questions_are_compact(self):
        for title, comments, _ in CASES:
            question = analyze_post(build_custom_post(title, comments), use_ai=False).bridge['bridge_question']
            self.assertLessEqual(len(question.split()), 28)

    def test_07_contextual_evidence_focus_matches_topic(self):
        self.assertIn('verimlilik', resolve_topic_context(CASES[0][0]).evidence_focus)
        self.assertIn('şikâyet', resolve_topic_context(CASES[1][0]).evidence_focus)
        self.assertIn('yolcu', resolve_topic_context(CASES[2][0]).evidence_focus)

    def test_08_generic_topic_retains_honest_fallback(self):
        result = analyze_post(build_custom_post(
            'Yeni öneri uygulanmalı mı?',
            ['Bence uygulanmalı.', 'Bence uygulanmamalı.', 'Belirli koşullarda olabilir.'],
        ), use_ai=False)
        self.assertIn('açık ölçütler', result.common_ground[0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
