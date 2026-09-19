from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'backend'
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.coach_engine import analyze_message, rewrite_with_ai, _numbers  # noqa: E402

CTX = 'Üniversitelerde yapay zekâ kullanımı yasaklanmalı mı?'
ATTACK_SIGNALS = {'hakaret/küfür', 'kişiye yönelik saldırı', 'tehdit/şiddet'}

PURE_ATTACKS = [
    'senin gibi bir mal görmedim hayatımda',
    'hayatımda senin kadar aptal birini görmedim',
    'sizin gibi salakları ilk kez görüyorum',
    'ömrümde senin kadar beyinsiz birini görmedim',
    'senin gibi bir gerizekalı görmedim',
    'senin kadar dangalak birini görmedim',
    'sizin gibi vasıfsız birini görmedim',
]

MIXED = [
    ('senin gibi bir mal görmedim hayatımda, bu öneri çok pahalı ve uygulanabilir değil', ('pahalı', 'uygulanabilir')),
    ('senin gibi bir salak görmedim, bu bilgi hangi araştırmaya dayanıyor?', ('araştırma',)),
    ("hayatımda senin kadar aptal birini görmedim; öğrencilerin %70'i bunu kullanıyor", ('%70',)),
]

FALSE_POSITIVES = [
    'Mal varlığı beyanını doldurdum.',
    'Senin gibi bir mal sahibi de sözleşmeyi imzalayabilir.',
    'Bu depodaki mal miktarı geçen aya göre arttı.',
    'Mal alım sözleşmesini bugün teslim edeceğiz.',
    'Malzeme listesi eksik.',
]


class CoachTargetedComparisonRegression(unittest.TestCase):
    def rewrite(self, text: str):
        return rewrite_with_ai(text, context=CTX, use_ai=True)

    def test_01_targeted_comparison_insults_are_detected(self):
        for original in PURE_ATTACKS:
            with self.subTest(original=original):
                signals = set(analyze_message(original))
                self.assertTrue(signals & ATTACK_SIGNALS, (original, signals))
                self.assertIn('kişiye yönelik saldırı', signals, (original, signals))

    def test_02_pure_attacks_are_never_echoed(self):
        for original in PURE_ATTACKS:
            with self.subTest(original=original):
                result = self.rewrite(original)
                suggestion = result['suggestion'].strip()
                self.assertNotEqual(suggestion.casefold(), original.strip().casefold(), (original, result))
                self.assertFalse(set(analyze_message(suggestion)) & ATTACK_SIGNALS, (original, result))
                self.assertNotIn('senin gibi', suggestion.casefold(), (original, result))
                self.assertNotIn('sizin gibi', suggestion.casefold(), (original, result))

    def test_03_mixed_messages_keep_real_content(self):
        for original, expected_terms in MIXED:
            with self.subTest(original=original):
                result = self.rewrite(original)
                suggestion = result['suggestion']
                self.assertFalse(set(analyze_message(suggestion)) & ATTACK_SIGNALS, (original, result))
                for term in expected_terms:
                    self.assertIn(term.casefold(), suggestion.casefold(), (original, result))
                for number in _numbers(original):
                    self.assertIn(number.replace(' ', ''), suggestion.replace(' ', ''), (original, result))

    def test_04_false_positive_mal_contexts_stay_clean(self):
        for original in FALSE_POSITIVES:
            with self.subTest(original=original):
                signals = set(analyze_message(original))
                self.assertFalse(signals & ATTACK_SIGNALS, (original, signals))
                result = self.rewrite(original)
                self.assertEqual(result['suggestion'], original, (original, result))

    def test_05_reported_user_example_is_fixed_exactly(self):
        original = 'senin gibi bir mal görmedim hayatımda'
        result = self.rewrite(original)
        self.assertNotEqual(result['suggestion'].casefold(), original.casefold())
        self.assertIn('kişiye yönelik saldırı', result['signals'])
        self.assertFalse(set(analyze_message(result['suggestion'])) & ATTACK_SIGNALS)


if __name__ == '__main__':
    unittest.main(verbosity=2)
