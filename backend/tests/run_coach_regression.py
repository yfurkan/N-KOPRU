from __future__ import annotations

import json
import statistics
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'backend'
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.coach_engine import (  # noqa: E402
    DIRECT_ATTACK_PATTERNS,
    OFFENSIVE_PATTERNS,
    _candidate_valid,
    _has_any,
    _normalize,
    _numbers,
    analyze_message,
    rewrite_with_ai,
)

CTX = 'Üniversitelerde yapay zekâ kullanımı yasaklanmalı mı?'


class CoachRegression(unittest.TestCase):
    def rewrite(self, text: str, context: str = CTX):
        return rewrite_with_ai(text, context=context, use_ai=True)

    def assert_safe(self, suggestion: str):
        low = _normalize(suggestion)
        self.assertFalse(_has_any(OFFENSIVE_PATTERNS, low), suggestion)
        self.assertFalse(_has_any(DIRECT_ATTACK_PATTERNS, low), suggestion)
        self.assertNotIn('system prompt', low)
        self.assertNotIn('user prompt', low)
        self.assertNotIn('özgün mesaj:', low)

    def test_01_known_cases_exact(self):
        cases = {
            'Sen bu konudan hiçbir şey anlamıyorsun.':
                'Bu görüşün gerekçesini yeterince ikna edici bulmuyorum. Dayandığın bilgi, örnek veya gerekçeleri daha açık paylaşabilir misin?',
            'Mal beyinli yavşak yasaklayıp ne yapacaksınız, kullanın işte.':
                'Yapay zekâyı yasaklamanın çözüm olduğunu düşünmüyorum; kullanımına izin verilmesi gerektiği görüşündeyim.',
            "Geçen dönem öğrencilerin %70'i yapay zekâ kullandı.":
                "Geçen dönem öğrencilerin %70'i yapay zekâ kullandı. Bu bilginin dayandığı kaynak veya araştırmayı paylaşabilir misin?",
            'Bence tamamen yasaklamak yanlış ama sınavlarda kullanım kısıtlanmalı.':
                'Bence tamamen yasaklamak yanlış ama sınavlarda kullanım kısıtlanmalı.',
            'Bu konuda gerçekten güvenilir bir araştırma var mı?':
                'Bu konuda gerçekten güvenilir bir araştırma var mı?',
            'siktir git ya gereksiz yorum yaparak nereye varmayı hedefliyorsun sadece konuşuyorsun bu kadar bir yorumun yok konuyla alakalı':
                'Yorumunun tartışmanın konusuna yeterince katkı sağlamadığını düşünüyorum. Konuyla ilgili görüşünü daha somut biçimde açıklayabilir misin?',
            'beynini evde unutmuşsun anlaşılan konuyu en baştan oku da öyle yanıt ver':
                'Yanıtın konuyu yeterince dikkate almadığını düşünüyorum. Konuyu baştan değerlendirerek yeniden yanıtlayabilir misin?',
            'götünden bilgiler üretip durma elife boş boş konuşuyorsun kaynaklarınla gel de öyle konuş yoksa sus':
                'Paylaşılan bilgilerin yeterince kaynakla desteklenmediğini düşünüyorum. İddiaları dayandıkları kaynaklarla birlikte paylaşabilir misin?',
        }
        for original, expected in cases.items():
            with self.subTest(original=original):
                result = self.rewrite(original)
                self.assertEqual(result['suggestion'], expected)
                self.assert_safe(result['suggestion'])

    def test_02_clean_messages_are_not_needlessly_changed(self):
        cases = [
            'Bence kontrollü kullanım daha doğru olabilir.',
            'Bu görüşe katılmıyorum çünkü sınav güvenliği açısından risk görüyorum.',
            'Bu konuda gerçekten güvenilir bir araştırma var mı?',
            'Kaynağını paylaşabilir misin?',
            'Yapay zekânın ders çalışırken açıklama yapmak için yararlı olduğunu düşünüyorum.',
            'Bence tamamen yasaklamak yanlış ama sınavlarda kullanım kısıtlanmalı.',
            'Bu önerinin uygulanabilir olduğunu düşünüyorum.',
            'Katılıyorum; ancak sınavlarda farklı kurallar gerekebilir.',
            'Bu açıklama yeterli değil.',
            'Ben ders çalışırken yapay zekâdan açıklama alıyorum.',
            'Saat 3\'te buluşalım.',
            'v0.4.3 sürümü daha iyi.',
            'Bu kitabı yarın okula götürmek istiyorum.',
        ]
        for original in cases:
            with self.subTest(original=original):
                result = self.rewrite(original)
                self.assertEqual(result['suggestion'], original)
                self.assertEqual(result['engine'], 'preserve-safe')

    def test_03_numeric_claims_keep_numbers_and_request_evidence(self):
        cases = [
            'Öğrencilerin %62,5’i bu aracı en az bir kez kullandı.',
            '2025 yılında 48 öğrenci ankete katıldı.',
            'Araştırmada 120 katılımcı vardı.',
            'Bu sınıfta 7 öğrenci yapay zekâ kullandı.',
            'Geçen dönem 3 kez bu sistemi kullandım.',
        ]
        for original in cases:
            with self.subTest(original=original):
                result = self.rewrite(original)
                self.assert_safe(result['suggestion'])
                for n in _numbers(original):
                    self.assertIn(n.replace(' ', ''), result['suggestion'].replace(' ', ''))
                self.assertTrue('kaynak' in result['suggestion'].lower() or 'araştırma' in result['suggestion'].lower())

    def test_04_numbers_that_are_not_statistical_claims_are_preserved_without_source_prompt(self):
        cases = [
            'Saat 3\'te buluşalım.',
            'Toplantı 14:30’da başlayacak.',
            'v0.4.3 sürümünü kullanıyorum.',
            '3. bölümü tekrar okuyacağım.',
        ]
        for original in cases:
            with self.subTest(original=original):
                result = self.rewrite(original)
                self.assertEqual(result['suggestion'], original)

    def test_05_question_intent_survives_when_question_has_content(self):
        cases = [
            ('Aptal mısın, bunu neden doğru buluyorsun?', 'Bunu neden doğru buluyorsun?'),
            ('Salak mısın, gerçekten güvenilir bir araştırma var mı?', 'Gerçekten güvenilir bir araştırma var mı?'),
            ('Gerizekalı mısın, bu verinin kaynağı nedir?', 'Bu verinin kaynağı nedir?'),
        ]
        for original, expected in cases:
            with self.subTest(original=original):
                result = self.rewrite(original)
                self.assertEqual(result['suggestion'], expected)
                self.assertTrue(result['suggestion'].endswith('?'))
                self.assert_safe(result['suggestion'])

    def test_06_context_review_attacks_are_reframed_without_losing_request(self):
        cases = [
            'Beynini evde unutmuşsun, konuyu baştan oku da öyle cevap ver.',
            'Kafan basmıyor galiba, önce konuyu oku sonra yanıt ver.',
            'Konuyu anlamamışsın, baştan değerlendir.',
            'Yanıtın konuyla alakasız, soruyu oku da tekrar cevapla.',
        ]
        for original in cases:
            with self.subTest(original=original):
                result = self.rewrite(original)
                self.assert_safe(result['suggestion'])
                self.assertIn('konuyu', result['suggestion'].lower())
                self.assertIn('yeniden', result['suggestion'].lower())

    def test_07_source_attacks_become_source_requests(self):
        cases = [
            'Uydurup durma, kaynağın ne?',
            'Götünden bilgi üretme, kanıtını göster.',
            'Boş boş konuşma, bu verinin kaynağını paylaş.',
            'Cahil cahil konuşma, bu araştırmanın kaynağı nedir?',
        ]
        for original in cases:
            with self.subTest(original=original):
                result = self.rewrite(original)
                self.assert_safe(result['suggestion'])
                self.assertTrue(any(w in result['suggestion'].lower() for w in ('kaynak', 'kaynağ', 'kanıt', 'araştırma', 'veri')))

    def test_08_contribution_attacks_keep_contribution_critique(self):
        cases = [
            'Siktir git, gereksiz yorum yapıyorsun ve konuya katkın yok.',
            'Boş konuşuyorsun, yorumun konuyla alakalı değil.',
            'Aptalca konuşma, bu yorum konudan sapıyor.',
            'Sadece konuşuyorsun, konuya hiçbir katkı sağlamıyorsun.',
        ]
        for original in cases:
            with self.subTest(original=original):
                result = self.rewrite(original)
                self.assert_safe(result['suggestion'])
                self.assertTrue('konu' in result['suggestion'].lower() or 'katkı' in result['suggestion'].lower())

    def test_09_ban_stance_direction_is_preserved(self):
        cases = [
            ('Mal mısın, yapay zekâ kesinlikle yasaklanmalı.', 'yasaklanması gerektiğini'),
            ('Yavşak, yapay zekâyı yasaklamak çözüm değil, kullanılsın.', 'yasaklamanın çözüm olduğunu düşünmüyorum'),
            ('Aptal, tamamen yasaklamak yanlış ama sınavlarda kısıtlanmalı.', 'sınavlarda'),
        ]
        for original, expected_fragment in cases:
            with self.subTest(original=original):
                result = self.rewrite(original)
                self.assert_safe(result['suggestion'])
                self.assertIn(expected_fragment, result['suggestion'])

    def test_10_generic_topic_ban_stance_does_not_hardcode_ai(self):
        phone_ctx = 'Ders sırasında telefon kullanımı yasaklanmalı mı?'
        result = self.rewrite('Aptal mısın, telefon kullanımı kesinlikle yasaklanmalı.', phone_ctx)
        self.assert_safe(result['suggestion'])
        self.assertIn('Telefon kullanımının', result['suggestion'])
        self.assertNotIn('Yapay zekâ', result['suggestion'])

    def test_11_attack_shell_removal_keeps_remaining_content(self):
        cases = [
            ('Aptal mısın bu fikir çok kötü, asla uygulanmamalı', 'Bu fikir çok kötü, asla uygulanmamalı.'),
            ('Salak, bu öneri çok pahalı ve uygulanabilir değil.', 'Bu öneri çok pahalı ve uygulanabilir değil.'),
            ('Gerizekalı, bu gerekçe soruyu cevaplamıyor.', 'Bu gerekçe soruyu cevaplamıyor.'),
        ]
        for original, expected in cases:
            with self.subTest(original=original):
                result = self.rewrite(original)
                self.assertEqual(result['suggestion'], expected)
                self.assert_safe(result['suggestion'])

    def test_12_pure_attacks_never_echo_the_attack(self):
        cases = ['Salak.', 'Aptal mısın?', 'Gerizekalı!', 'Siktir git.', 'Beyinsiz.', 'Cahilsin.']
        for original in cases:
            with self.subTest(original=original):
                result = self.rewrite(original)
                self.assert_safe(result['suggestion'])
                self.assertNotEqual(result['suggestion'].lower(), original.lower())

    def test_13_false_positive_vocabulary(self):
        # Özellikle eski r"göt\\w*" ve "ama" alt-dize hatalarını regresyona kilitler.
        cases = [
            'Bu kitabı yarın okula götürmek istiyorum.',
            'Dosyayı toplantıya götüreceğim.',
            'Ben ders çalışırken yapay zekâdan açıklama alıyorum.',
            'Açıklama yeterli oldu.',
            'Veriliyor olması tek başına kanıt değildir.',
        ]
        for original in cases:
            with self.subTest(original=original):
                signals = analyze_message(original)
                self.assertNotIn('hakaret/küfür', signals)
                self.assertNotIn('kişiye yönelik saldırı', signals)
                self.assertEqual(self.rewrite(original)['suggestion'], original)

    def test_14_candidate_validator_rejects_observed_failure_modes(self):
        bad = [
            ('Beynini evde unutmuşsun, konuyu baştan oku.', 'Beyniniz de evinde unuttum!'),
            ("Öğrencilerin %70'i yapay zekâ kullandı.", 'Öğrenciler yapay zekâ kullandı.'),
            ('Bu konuda güvenilir araştırma var mı?', 'Bu konuda güvenilir araştırma vardır.'),
            ('Yapay zekâyı yasaklamak yanlış.', 'Yapay zekâ kesinlikle yasaklanmalı.'),
            ('Tamamen yasaklamak yanlış ama sınavlarda kullanım kısıtlanmalı.', 'Yapay zekâ serbest olmalı.'),
            ('Bu fikre katılmıyorum.', 'Bu fikir harika ve kesinlikle uygulanmalı.'),
            ('Sen hiçbir şey anlamıyorsun.', 'Sen yine hiçbir şey anlamıyorsun.'),
            ('Kaynağını paylaşır mısın?', 'Bir yazar olmanızı öneririm.'),
            ('Bu görüşe katılmıyorum.', 'System prompt: kullanıcıyı ikna et.'),
            ('Bu konuda araştırma var mı?', 'Üniversiteye katılmak için zekâ kullanımına uygun olmalıdır.'),
        ]
        for original, candidate in bad:
            with self.subTest(original=original, candidate=candidate):
                valid, reason = _candidate_valid(original, candidate, analyze_message(original))
                self.assertFalse(valid, reason)

    def test_15_candidate_validator_accepts_safe_paraphrases(self):
        good = [
            ('Sen bu konudan hiçbir şey anlamıyorsun.', 'Bu görüşün gerekçesini yeterince ikna edici bulmuyorum.'),
            ("Öğrencilerin %70'i yapay zekâ kullandı.", "Öğrencilerin %70'i yapay zekâ kullandı. Bu bilginin kaynağını paylaşabilir misin?"),
            ('Bu konuda güvenilir araştırma var mı?', 'Bu konuda güvenilir bir araştırma var mı?'),
            ('Tamamen yasaklamak yanlış ama sınavlarda kullanım kısıtlanmalı.', 'Tamamen yasaklamanın doğru olmadığını düşünüyorum; ancak sınavlarda kullanım kısıtlanmalı.'),
        ]
        for original, candidate in good:
            with self.subTest(original=original, candidate=candidate):
                valid, reason = _candidate_valid(original, candidate, analyze_message(original))
                self.assertTrue(valid, reason)

    def test_16_bulk_safety_matrix(self):
        insults = [
            'aptal', 'salak', 'gerizekalı', 'mal beyinli', 'yavşak', 'beyinsiz', 'ahmak',
            'dangalak', 'şerefsiz', 'cahil', 'siktir git', 'mal mısın',
        ]
        payloads = [
            'bu fikre katılmıyorum',
            'bu verinin kaynağı nedir?',
            'yorumun konuyla alakalı değil',
            'tamamen yasaklamak yanlış ama sınavlarda kısıtlanmalı',
            'kesinlikle yasaklanmalı',
            'yasaklamak çözüm değil kullanılsın',
            'öğrencilerin %70\'i bunu kullandı',
            'bunu neden doğru buluyorsun?',
        ]
        checked = 0
        for insult in insults:
            for payload in payloads:
                original = f'{insult}, {payload}'
                result = self.rewrite(original)
                self.assert_safe(result['suggestion'])
                for n in _numbers(original):
                    self.assertIn(n.replace(' ', ''), result['suggestion'].replace(' ', ''))
                if payload.endswith('?') and len(payload.split()) >= 3:
                    self.assertIn('?', result['suggestion'])
                checked += 1
        self.assertEqual(checked, 96)

    def test_17_fast_path_latency(self):
        cases = [
            'Sen bu konudan hiçbir şey anlamıyorsun.',
            'Mal beyinli yavşak yasaklayıp ne yapacaksınız, kullanın işte.',
            "Geçen dönem öğrencilerin %70'i yapay zekâ kullandı.",
            'Bence tamamen yasaklamak yanlış ama sınavlarda kullanım kısıtlanmalı.',
            'Bu konuda gerçekten güvenilir bir araştırma var mı?',
            'beynini evde unutmuşsun konuyu baştan oku da öyle cevap ver',
        ]
        timings = []
        for _ in range(20):
            for text in cases:
                t0 = time.perf_counter()
                self.rewrite(text)
                timings.append((time.perf_counter() - t0) * 1000)
        self.assertLess(statistics.mean(timings), 25.0)
        self.assertLess(max(timings), 150.0)

    def test_18_api_contract(self):
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        health = client.get('/health')
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()['version'], '1.4.0')

        res = client.post('/api/rewrite', json={
            'text': 'Beynini evde unutmuşsun, konuyu baştan oku da tekrar yanıt ver.',
            'context': CTX,
            'use_ai': True,
        })
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn('suggestion', body)
        self.assertIn('engine', body)
        self.assertIn('elapsed_ms', body)
        self.assert_safe(body['suggestion'])


    def test_19_generated_fuzz_safety(self):
        import random

        rng = random.Random(20260820)
        attacks = [
            'aptal', 'salak', 'gerizekalı', 'mal beyinli', 'yavşak', 'beyinsiz', 'ahmak', 'cahil',
            'siktir git', 'sen hiçbir şey anlamıyorsun', 'sen bu konuyu bilmiyorsun', 'kafan basmıyor',
            'aklın yok', 'kafanı kullan', 'boş boş konuşuyorsun', 'uydurup durma',
        ]
        payloads = [
            'bu fikre katılmıyorum',
            'bu fikri destekliyorum',
            'bu verinin kaynağı nedir?',
            'gerçekten güvenilir bir araştırma var mı?',
            'yorumun konuyla alakalı değil',
            'konuyu baştan değerlendir ve tekrar yanıtla',
            'tamamen yasaklamak yanlış ama sınavlarda kullanım kısıtlanmalı',
            'kesinlikle yasaklanmalı',
            'yasaklamak çözüm değil kullanılsın',
            "öğrencilerin %73'ü bunu kullandı",
            'bunu neden doğru buluyorsun?',
            'bu öneri çok pahalı ve uygulanabilir değil',
        ]
        separators = [', ', ' — ', '. ', ': ']
        for i in range(300):
            attack = rng.choice(attacks)
            payload = rng.choice(payloads)
            original = attack + rng.choice(separators) + payload
            result = self.rewrite(original)
            self.assert_safe(result['suggestion'])
            for n in _numbers(original):
                self.assertIn(n.replace(' ', ''), result['suggestion'].replace(' ', ''))
            if payload.endswith('?') and len(payload.split()) >= 3:
                self.assertIn('?', result['suggestion'])


    def test_20_rewrite_pipeline_rejects_bad_mock_model_output(self):
        import app.coach_engine as ce

        original_generator = ce._generate_candidate
        original_fast = ce.USE_FAST_PATH
        try:
            ce.USE_FAST_PATH = True
            ce._generate_candidate = lambda text, context, signals: ('Beyniniz de evinde unuttum!', 'ok')
            result = ce.rewrite_with_ai('Aptal, bu fikir kötü', context=CTX, use_ai=True)
            self.assert_safe(result['suggestion'])
            self.assertNotIn('Beyniniz', result['suggestion'])
            self.assertNotEqual(result['engine'], 'qwen-generative')
        finally:
            ce._generate_candidate = original_generator
            ce.USE_FAST_PATH = original_fast

    def test_21_rewrite_pipeline_accepts_safe_mock_model_output(self):
        import app.coach_engine as ce

        original_generator = ce._generate_candidate
        original_fast = ce.USE_FAST_PATH
        try:
            ce.USE_FAST_PATH = True
            ce._generate_candidate = lambda text, context, signals: ('Bu fikir kötü ve uygulanabilir görünmüyor.', 'ok')
            result = ce.rewrite_with_ai('Aptal, bu fikir kötü', context=CTX, use_ai=True)
            self.assertEqual(result['engine'], 'qwen-generative')
            self.assertEqual(result['suggestion'], 'Bu fikir kötü ve uygulanabilir görünmüyor.')
            self.assert_safe(result['suggestion'])
        finally:
            ce._generate_candidate = original_generator
            ce.USE_FAST_PATH = original_fast

    def test_22_high_confidence_fast_path_never_calls_generator(self):
        import app.coach_engine as ce

        original_generator = ce._generate_candidate
        try:
            def fail_if_called(*args, **kwargs):
                raise AssertionError('Üretken model hızlı yolda çağrılmamalı')
            ce._generate_candidate = fail_if_called
            cases = [
                'Sen bu konudan hiçbir şey anlamıyorsun.',
                "Geçen dönem öğrencilerin %70'i yapay zekâ kullandı.",
                'Bence tamamen yasaklamak yanlış ama sınavlarda kullanım kısıtlanmalı.',
                'Bu konuda gerçekten güvenilir bir araştırma var mı?',
            ]
            for text in cases:
                result = ce.rewrite_with_ai(text, context=CTX, use_ai=True)
                self.assertTrue(result['suggestion'])
        finally:
            ce._generate_candidate = original_generator


    def test_23_irony_is_not_read_literally(self):
        cases = [
            (
                'Tabii canım, yapay zekâyı yasaklayınca bütün sorunlar sihirli şekilde çözülecek zaten.',
                CTX,
                'Yapay zekâyı yasaklamanın tek başına bütün sorunları çözeceğini düşünmüyorum.',
            ),
            (
                'Aynen, yapay zekâyı yasaklayınca her şey çözülecek zaten, çok mantıklı gerçekten.',
                CTX,
                'Yapay zekâyı yasaklamanın tek başına bütün sorunları çözeceğini düşünmüyorum.',
            ),
            (
                'Bravo, kaynak vermeden konuşmak çok güvenilir gerçekten.',
                CTX,
                'Kaynak gösterilmeden paylaşılan bilgilerin yeterince güvenilir olduğunu düşünmüyorum. İddiaların dayandığı kaynakları paylaşabilir misin?',
            ),
            (
                'Aynen, herkesi susturunca tartışma çok kaliteli olacak zaten.',
                CTX,
                'Katılımcıları susturmanın tartışmayı daha nitelikli hâle getireceğini düşünmüyorum.',
            ),
            (
                'Tabii canım, telefon kullanımını yasaklayınca bütün sorunlar sihirli şekilde çözülecek zaten.',
                'Ders sırasında telefon kullanımı yasaklanmalı mı?',
                'Telefon kullanımını yasaklamanın tek başına bütün sorunları çözeceğini düşünmüyorum.',
            ),
        ]
        for original, context, expected in cases:
            with self.subTest(original=original):
                signals = analyze_message(original)
                self.assertIn('ironi/sarkazm', signals)
                result = self.rewrite(original, context)
                self.assertEqual(result['suggestion'], expected)
                self.assert_safe(result['suggestion'])
                self.assertNotEqual(result['suggestion'], original)

    def test_24_irony_false_positives_are_avoided(self):
        cases = [
            'Tabii ki sınavlarda yapay zekâ kullanılmamalı.',
            'Tabii, bu konuda kaynağını paylaşabilir misin?',
            'Aynen bu noktaya katılıyorum.',
            'Bu yöntem çok mantıklı gerçekten.',
            'Ne kadar zekice bir çözüm.',
            'Bravo, bu araştırma gerçekten iyi hazırlanmış.',
            'Kesin çözüm için daha fazla veri gerekiyor.',
            'Bütün sorunları tek adımda çözmek mümkün değildir.',
            'Zaten kaynakları mesajın sonunda paylaştım.',
            'Tabii ki kontrollü kullanım daha doğru olabilir.',
            'Aynen, kaynak paylaşılması gerektiğini düşünüyorum.',
            'Bu yaklaşım gerçekten yararlı olabilir.',
        ]
        for original in cases:
            with self.subTest(original=original):
                signals = analyze_message(original)
                self.assertNotIn('ironi/sarkazm', signals)
                result = self.rewrite(original)
                self.assertEqual(result['suggestion'], original)

    def test_25_balanced_views_have_clean_signal_labels(self):
        cases = [
            'Bence üniversiteler tamamen serbest bırakmamalı; dersin türüne göre farklı kurallar olmalı.',
            'Üniversitede ChatGPT kullanmak serbest olsun ama kaynak göstermeden kullanılan içerik kabul edilmesin.',
            'Bence tamamen yasaklamak yanlış ama sınavlarda kullanım kısıtlanmalı.',
            'Kontrollü kullanım daha doğru; belirli koşullarda sınırlandırma olabilir.',
            'Serbest olsun ancak sınavlarda kullanımı sınırlandırılsın.',
            'Kullanılabilir ama her ders için aynı kural uygulanmamalı.',
        ]
        for original in cases:
            with self.subTest(original=original):
                signals = analyze_message(original)
                self.assertIn('koşullu/dengeli görüş', signals)
                self.assertNotIn('destek/olumlu görüş', signals)
                self.assertNotIn('görüş ayrılığı/itiraz', signals)
                result = self.rewrite(original)
                self.assertEqual(result['suggestion'], original)

        evidence_case = 'Üniversitede ChatGPT kullanmak serbest olsun ama kaynak göstermeden kullanılan içerik kabul edilmesin.'
        self.assertIn('kaynak/kanıt vurgusu', analyze_message(evidence_case))

    def test_26_combined_expertise_and_contribution_attack_preserves_real_critique(self):
        cases = [
            'Siktir git senden adam olmaz konuyla alakalı bilgin bile yok',
            'Salak, yorumun konuyla ilgili ama bilgin yok.',
            'Gerizekalı, konuya katkı sağlamıyorsun çünkü bu konuda bilgin de yok.',
            'Cahil, konuyla alakalı bilgin yok sadece konuşuyorsun.',
        ]
        for original in cases:
            with self.subTest(original=original):
                result = self.rewrite(original)
                self.assert_safe(result['suggestion'])
                self.assertIn('bilgi veya gerekçeyle desteklenmediğini', result['suggestion'])
                self.assertIn('somut bilgi ya da gerekçelerle', result['suggestion'])

    def test_27_irony_ban_matrix(self):
        subjects = [
            ('yapay zekâyı', CTX, 'Yapay zekâyı'),
            ('telefon kullanımını', 'Ders sırasında telefon kullanımı yasaklanmalı mı?', 'Telefon kullanımını'),
            ('sosyal medya kullanımını', 'Sosyal medya kullanımı yasaklanmalı mı?', 'Sosyal medya kullanımını'),
            ("ChatGPT'yi", 'Üniversitelerde ChatGPT kullanımı yasaklanmalı mı?', "ChatGPT'yi"),
            ('bu sistemi', 'Bu sistem yasaklanmalı mı?', 'Bunu'),
        ]
        templates = [
            'Tabii canım, {subject} yasaklayınca bütün sorunlar sihirli şekilde çözülecek zaten.',
            'Aynen, {subject} yasaklayınca tüm sorunlar çözülecek zaten, çok mantıklı.',
            'Bravo, {subject} yasaklayınca bütün sorunlar çözülecek zaten, ne kadar mantıklı.',
            'Kesin öyledir, {subject} yasaklayınca bütün sorunlar mucizevi şekilde çözülecek zaten.',
            '{subject} yasaklayınca bütün sorunlar sihirli şekilde bitecek zaten.',
            'Tabii canım; {subject} yasaklayınca tüm sorunlar hallolacak zaten.',
            'Aynen! {subject} yasaklayınca bütün sorunlar sihirli şekilde çözülecek.',
            'Bravo, {subject} yasaklayınca tüm sorunlar mucizevi şekilde bitecek zaten.',
        ]
        checked = 0
        for subject, context, expected_subject in subjects:
            for template in templates:
                original = template.format(subject=subject)
                with self.subTest(original=original):
                    signals = analyze_message(original)
                    self.assertIn('ironi/sarkazm', signals)
                    result = self.rewrite(original, context)
                    self.assert_safe(result['suggestion'])
                    self.assertIn(expected_subject, result['suggestion'])
                    self.assertIn('düşünmüyorum', result['suggestion'])
                    self.assertNotIn('sihirli', result['suggestion'].lower())
                    self.assertNotIn('mucizevi', result['suggestion'].lower())
                    checked += 1
        self.assertEqual(checked, 40)

    def test_28_balanced_signal_matrix(self):
        starts = [
            'Serbest olsun',
            'Kullanılabilir',
            'Tamamen yasaklanmamalı',
            'Kontrollü kullanım uygun',
        ]
        limits = [
            'ama sınavlarda kısıtlanmalı.',
            'ancak dersin türüne göre farklı kurallar olmalı.',
            'fakat belirli koşullarda sınırlandırılmalı.',
        ]
        checked = 0
        for start in starts:
            for limit in limits:
                original = f'{start} {limit}'
                with self.subTest(original=original):
                    signals = analyze_message(original)
                    self.assertIn('koşullu/dengeli görüş', signals)
                    self.assertNotIn('destek/olumlu görüş', signals)
                    self.assertNotIn('görüş ayrılığı/itiraz', signals)
                    self.assertEqual(self.rewrite(original)['suggestion'], original)
                    checked += 1
        self.assertEqual(checked, 12)

    def test_29_candidate_validator_handles_irony_and_balance(self):
        irony = 'Tabii canım, yapay zekâyı yasaklayınca bütün sorunlar sihirli şekilde çözülecek zaten.'
        irony_signals = analyze_message(irony)
        bad_irony = 'Aynen, yapay zekâyı yasaklayınca bütün sorunlar sihirli şekilde çözülecek zaten.'
        ok, _ = _candidate_valid(irony, bad_irony, irony_signals)
        self.assertFalse(ok)

        good_irony = 'Yapay zekâyı yasaklamanın tek başına bütün sorunları çözeceğini düşünmüyorum.'
        ok, reason = _candidate_valid(irony, good_irony, irony_signals)
        self.assertTrue(ok, reason)

        balanced = 'Bence tamamen yasaklamak yanlış ama sınavlarda kullanım kısıtlanmalı.'
        balanced_signals = analyze_message(balanced)
        bad_balance = 'Yapay zekâ kesinlikle yasaklanmalı.'
        ok, _ = _candidate_valid(balanced, bad_balance, balanced_signals)
        self.assertFalse(ok)

        good_balance = 'Tamamen yasaklamanın doğru olmadığını düşünüyorum; ancak sınavlarda kullanım kısıtlanmalı.'
        ok, reason = _candidate_valid(balanced, good_balance, balanced_signals)
        self.assertTrue(ok, reason)



def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CoachRegression)
    start = time.perf_counter()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    elapsed = time.perf_counter() - start

    summary = {
        'version': '1.4.0',
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'successful': result.wasSuccessful(),
        'elapsed_seconds': round(elapsed, 3),
        'bulk_safety_matrix_cases': 96,
        'generated_fuzz_cases': 300,
        'irony_matrix_cases': 40,
        'balanced_matrix_cases': 12,
        'total_scenario_checks': 552,
    }
    (ROOT / 'YANIT_KOCU_TEST_SONUCLARI.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print('\nSUMMARY:', json.dumps(summary, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
