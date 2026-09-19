from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'backend'
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.coach_engine import (  # noqa: E402
    DIRECT_ATTACK_PATTERNS,
    OFFENSIVE_PATTERNS,
    THREAT_PATTERNS,
    _has_any,
    _normalize,
    _numbers,
    analyze_message,
    rewrite_with_ai,
)

CTX = 'Üniversitelerde yapay zekâ kullanımı yasaklanmalı mı?'
ATTACK_SIGNALS = {'hakaret/küfür', 'kişiye yönelik saldırı', 'tehdit/şiddet'}

# Açık kaynaklı Türkçe YouTube yorumlarında görülen dil biçimlerinden ve
# sosyal medya saldırgan dil korpuslarının PROF/IND ayrımından türetilmiş
# gerçek-dünya tarzı örnekler. Kaynak cümleler yalnız test amacıyla kısa
# örnekler olarak tutulur; kullanıcı verisi/pilot verisi değildir.
REAL_WORLD_STYLE = [
    'hahahah kudur aptal apple fanboyu',
    'ilk yazanları skm',
    'sen de ne boş adamsın ya',
    'okumayı öğren de gel',
    'kafan basmıyor galiba',
    'beynini kullan biraz',
    'anlama kapasiten yok',
    'ilkokul çocuğu senden iyi anlar',
    'zeka seviyen buna yetmiyor',
    "IQ'n kaç senin 20 mi?",
    'sana laf anlatılmaz',
    'seninle tartışmak zaman kaybı',
    'kendini rezil ediyorsun',
    'acınası birisin',
    'şaka mısın sen',
    'ergen misin nesin',
    'fanboyluk yapma da düzgün konuş',
    'kudurmuşsun yine',
    'boş yapma',
    'saçmalayıp duruyorsun',
    'zırvalama artık',
    'hadi ordan',
    'yürü git',
    'adam değilsin',
    'insan içine çıkma',
    'hangi mağaradan çıktın',
    'beynin almıyor işte',
    'kafanı çalıştır da yaz',
    'okuduğunu anlamıyorsun',
    'bu kadar cahillik fazla',
    'sen ciddi ciddi bunu mu yazdın aptal',
    'palyaço gibi konuşuyorsun',
    'tam bir eziksin',
    'çapsızın tekisin',
    'vasıfsız herif',
    'dangalak mısın',
    'embesil gibi cevap verme',
    'manyak mısın sen',
    'salak salak konuşma',
    'gerizekalı gibi davranma',
]

THREAT_STYLE = [
    'seni bulurum',
    'adresini bulurum görürsün',
    'görürsün sen gününü',
    'ağzını burnunu kırarım',
    'dayak yersin böyle konuşursan',
    'seni gebertirim',
    'seni öldürürüm',
    'karşıma çıkma pişman olursun',
    'bir daha yazarsan seni mahvederim',
    'nerede olduğunu bulurum',
]

MIXED_INTENT = [
    ('aptal mısın bu verinin kaynağı ne?', 'question'),
    ('kafan basmıyor galiba, neden bunun doğru olduğunu düşünüyorsun?', 'question'),
    ('boş yapma bu iddianın kaynağını paylaş', 'source'),
    ('fanboyluk yapma, bu bilgi hangi araştırmaya dayanıyor?', 'source'),
    ('salak, öğrencilerin %63,5\'i bunu kullanmış', 'number'),
    ('gerizekalı, 2026 yılında 184 kişi ankete katılmış', 'number'),
    ('aptal, bu öneri çok pahalı ve uygulanabilir değil', 'content'),
    ('beyinsiz, tamamen yasaklamak yanlış ama sınavda kısıtlanmalı', 'content'),
    ('kudur fanboy, bu özellik bataryayı gerçekten daha hızlı tüketiyor', 'content'),
    ('cahil cahil konuşma, bu yöntem veri kaybına yol açabilir', 'content'),
]

# Nesne/konu eleştirisi veya saldırı sözcüğüne benzeyen masum dizgiler.
# Bunlar kişisel saldırı diye bozulmamalı.
FALSE_POSITIVES = [
    'Bu firmaya verilen para gerçekten çöp.',
    'Çöp kutusunu dışarı çıkaralım.',
    'Bok böceği üzerine araştırma yapıyorum.',
    'Mal varlığı beyanını doldurdum.',
    'Malzeme listesi eksik.',
    'Sikorsky helikopteri bugün iniş yaptı.',
    'Sıkışık trafikte kaldım.',
    'Sikke koleksiyonunu müzeye bağışladı.',
    'Bu kitabı yarın okula götürmek istiyorum.',
    'Hayvan davranışlarını gözlemliyoruz.',
    'Eşek arıları hakkında belgesel izledim.',
    'Sürüngen türlerini sınıflandırıyoruz.',
    'Bu yöntem işe yaramaz.',
    'Bu fikir bana aptalca geliyor.',
    'Bu tasarım berbat görünüyor.',
    'Bu uygulama çok kötü.',
    'Fanboy kelimesinin anlamını soruyorum.',
    'Kudurmak fiilinin kökü nedir?',
    'Çocuk gelişimi dersinde ergen davranışlarını konuşuyoruz.',
    'Palyaço kostümü aldım.',
]

BROKEN_SHELL_PATTERNS = [
    r'^(?:birisin|birisiniz|birisi|biri|senden|sizden|senin|sizin|sana|seni)\b',
    r'\b(?:birisin|birisiniz)\b',
    r'\b(?:senden|sizden)\s+daha\s+(?:iyi|kötü|zeki|akıllı|başarılı|mantıklı|değerli)\b',
]


def obfuscated_cases() -> list[str]:
    cases: list[str] = []
    # Karakter ayırma ve görünmez karakter kaçakları.
    for token in ('siktir', 'sikim', 'amk', 'yarrak', 'aptal', 'salak'):
        for sep in ('.', ' ', '-', '_', '*', '\u200b'):
            variant = sep.join(token)
            cases.append(f'sen {variant} birisin')
    # Yaygın ASCII/leet ve uzatma biçimleri.
    cases.extend([
        's1kt1r g1t', 's!k!m senden olmaz', 'a*m*k ne yazmışsın',
        '0r0spu cocugu', 'g3r1z3k4l1', 'saaalaaaak', 'aptaaalll',
        'y4rr4k kafali', 'b3y1ns1z', 'ş e r e f s i z',
        's.i.k.t.i.r git', 'a.m.k ya', 'y a r r a k kafalı',
        'SİKTİR GİT', 'APTAL MISIN', 'SALAKSIN',
    ])
    return cases


class CoachRealWorldStressRegression(unittest.TestCase):
    maxDiff = None

    def rewrite(self, text: str):
        return rewrite_with_ai(text, context=CTX, use_ai=True)

    def assert_output_safe(self, original: str, suggestion: str):
        self.assertTrue(suggestion.strip(), original)
        low = _normalize(suggestion)
        self.assertFalse(_has_any(OFFENSIVE_PATTERNS, low), (original, suggestion))
        self.assertFalse(_has_any(DIRECT_ATTACK_PATTERNS, low), (original, suggestion))
        self.assertFalse(_has_any(THREAT_PATTERNS, low), (original, suggestion))
        for pattern in BROKEN_SHELL_PATTERNS:
            self.assertIsNone(re.search(pattern, low), (original, suggestion))

    def test_01_real_world_hurtful_language_is_coached(self):
        for original in REAL_WORLD_STYLE:
            with self.subTest(original=original):
                signals = set(analyze_message(original))
                self.assertTrue(signals & ATTACK_SIGNALS, (original, signals))
                result = self.rewrite(original)
                self.assertNotEqual(result['suggestion'].strip(), original.strip(), original)
                self.assert_output_safe(original, result['suggestion'])

    def test_02_threat_language_is_deescalated(self):
        for original in THREAT_STYLE:
            with self.subTest(original=original):
                signals = set(analyze_message(original))
                self.assertIn('tehdit/şiddet', signals, (original, signals))
                result = self.rewrite(original)
                self.assert_output_safe(original, result['suggestion'])

    def test_03_obfuscation_matrix_cannot_bypass_guard(self):
        for original in obfuscated_cases():
            with self.subTest(original=original):
                signals = set(analyze_message(original))
                self.assertTrue(signals & ATTACK_SIGNALS, (original, signals))
                result = self.rewrite(original)
                self.assert_output_safe(original, result['suggestion'])

    def test_04_mixed_attacks_keep_useful_intent(self):
        for original, kind in MIXED_INTENT:
            with self.subTest(original=original):
                result = self.rewrite(original)
                suggestion = result['suggestion']
                self.assert_output_safe(original, suggestion)
                if kind == 'question':
                    self.assertTrue(suggestion.rstrip().endswith('?'), (original, suggestion))
                elif kind == 'source':
                    self.assertTrue(any(k in suggestion.lower() for k in ('kaynak', 'kanıt', 'araştırma', 'veri')), (original, suggestion))
                elif kind == 'number':
                    for number in _numbers(original):
                        self.assertIn(number.replace(' ', ''), suggestion.replace(' ', ''), (original, suggestion))
                elif kind == 'content':
                    # Salt güvenli genel cümleye kaçmak yerine özgün tartışılabilir içeriğin
                    # en az bir çekirdek sözcüğü korunmalı.
                    core = [w for w in ('pahalı', 'uygulanabilir', 'yasaklamak', 'sınav', 'batarya', 'veri kaybı') if w in original.lower()]
                    self.assertTrue(any(w in suggestion.lower() for w in core), (original, suggestion, core))

    def test_05_false_positive_contexts_are_preserved(self):
        for original in FALSE_POSITIVES:
            with self.subTest(original=original):
                signals = set(analyze_message(original))
                self.assertFalse(signals & ATTACK_SIGNALS, (original, signals))
                result = self.rewrite(original)
                self.assertEqual(result['suggestion'], original, (original, result))

    def test_06_stress_inventory_is_large_enough(self):
        total = len(REAL_WORLD_STYLE) + len(THREAT_STYLE) + len(MIXED_INTENT) + len(FALSE_POSITIVES) + len(obfuscated_cases())
        self.assertGreaterEqual(total, 120)


if __name__ == '__main__':
    unittest.main(verbosity=2)
