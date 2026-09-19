from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'backend'
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.coach_engine import _has_attack_residue, _normalize, rewrite_with_ai  # noqa: E402

CTX = 'Üniversitelerde yapay zekâ kullanımı yasaklanmalı mı?'

SCREENSHOT_CASES = [
    'beyinsiz birisin sikim senden daha iyi düşünceler üretir',
    'beyinsiz birisin senden hiç bir bok olmaz',
]

PURE_ATTACKS = [
    'senden hiçbir şey olmaz',
    'beyinsiz birisin',
    'mal mısın',
    'aptal herif',
    'sen tam bir gerizekalısın',
    'sikim senden daha akıllı',
    'yarak kafalı',
    'siktir git',
    'bok kafalı birisin',
    'senin kafan basmıyor',
    'hiçbir şey bilmiyorsun',
    'beş para etmezsin',
    'işe yaramazsın',
    'bir gram aklın yok',
    'kendini bir şey sanıyorsun',
    'sen kimsin ya',
    'çeneni kapat',
    'defol buradan',
    'rezilsin',
    'karaktersizsin',
    'omurgasızsın',
    'beceriksizsin',
    'you are an idiot',
    'piece of shit',
    'fuck you',
]

MIXED_CASES = [
    'Aptal mısın, bu verinin kaynağı nedir?',
    'Salak mısın, bunu neden doğru buluyorsun?',
    'Siktir git, bu %70 oranı hangi rapora dayanıyor?',
    "Senden hiçbir bok olmaz ama öğrencilerin %62,5'i bunu kullandı.",
    'Yarrak kafalı, bu fikir kötü ve uygulanabilir değil.',
    'Gerizekalı, tamamen yasaklamak yanlış ama sınavlarda kullanım kısıtlanmalı.',
    'Beyinsiz, yapay zekâ kesinlikle yasaklanmalı.',
    'Uyduruyorsun, kaynaklarını paylaş.',
    'Götünden bilgi üretme, kanıtını göster.',
    'Boş konuşma, bu araştırmanın kaynağı var mı?',
    'Kafan basmıyor, konuyu baştan değerlendir.',
    'Siktir git, bu yorumun konuya katkısı yok.',
    'Sen hayvansın; yapay zekâ kullanımına izin verilmemeli.',
    'Aptal mısın, gerçekten güvenilir bir araştırma var mı?',
    'Mal herif, bu yöntemin maliyeti çok yüksek.',
]

FALSE_POSITIVES = [
    'Mal varlığı beyanı gerekiyor.',
    'Hayvan davranışlarını inceliyoruz.',
    'Sikorsky helikopteri hakkında bilgi ver.',
    'Bok böceği üzerine araştırma yapıyorum.',
    'Sıkışık bir programımız var.',
    'Bu yöntem işe yaramaz.',
    'Çöp kutusunu değiştirelim.',
    'Bu görüşe katılmıyorum çünkü sınav güvenliği açısından risk görüyorum.',
    'Bence kontrollü kullanım daha doğru olabilir.',
    'Bu konuda gerçekten güvenilir bir araştırma var mı?',
]


class CoachFinalGuardRegression(unittest.TestCase):
    def rewrite(self, text: str):
        return rewrite_with_ai(text, context=CTX, use_ai=False)

    def assert_safe_and_well_formed(self, text: str):
        low = _normalize(text)
        self.assertFalse(_has_attack_residue(text), text)
        self.assertFalse(low.startswith(('birisin ', 'birisi ', 'biri ', 'senden ', 'sizden ')), text)
        self.assertNotIn('senden daha iyi', low, text)
        self.assertNotIn('sizden daha iyi', low, text)
        self.assertNotIn('birisin', low, text)
        self.assertGreaterEqual(len(text.split()), 4, text)

    def test_01_reported_screenshots_do_not_leak_broken_shells(self):
        for original in SCREENSHOT_CASES:
            with self.subTest(original=original):
                result = self.rewrite(original)
                self.assert_safe_and_well_formed(result['suggestion'])
                low = _normalize(result['suggestion'])
                self.assertTrue(any(x in low for x in ('görüş', 'düşün', 'gerekçe', 'tartış', 'eleştiri')))

    def test_02_pure_attacks_become_constructive_not_personal(self):
        for original in PURE_ATTACKS:
            with self.subTest(original=original):
                result = self.rewrite(original)
                self.assert_safe_and_well_formed(result['suggestion'])
                low = _normalize(result['suggestion'])
                self.assertTrue(any(x in low for x in ('görüş', 'düşün', 'gerekçe', 'tartış', 'konu', 'eleştiri')))

    def test_03_mixed_attacks_preserve_useful_intent(self):
        for original in MIXED_CASES:
            with self.subTest(original=original):
                result = self.rewrite(original)
                self.assert_safe_and_well_formed(result['suggestion'])
                original_low = _normalize(original)
                out_low = _normalize(result['suggestion'])
                if '?' in original:
                    self.assertIn('?', result['suggestion'])
                if '%' in original:
                    number = original.split('%', 1)[1].split()[0].strip('.,?!')
                    self.assertIn(number, result['suggestion'])
                if any(x in original_low for x in ('kaynak', 'kanıt', 'rapor', 'araştırma')):
                    self.assertTrue(any(x in out_low for x in ('kaynak', 'kanıt', 'rapor', 'araştırma')))

    def test_04_clean_and_objective_messages_are_not_damaged(self):
        for original in FALSE_POSITIVES:
            with self.subTest(original=original):
                result = self.rewrite(original)
                self.assertEqual(result['suggestion'], original)

    def test_05_guard_engine_is_used_only_when_needed(self):
        bad = self.rewrite(SCREENSHOT_CASES[0])
        self.assertIn(bad['engine'], {'quality-guard-safe', 'hybrid-safe', 'contextual-fallback'})
        clean = self.rewrite('Bence kontrollü kullanım daha doğru olabilir.')
        self.assertEqual(clean['engine'], 'preserve-safe')


if __name__ == '__main__':
    unittest.main(verbosity=2)
