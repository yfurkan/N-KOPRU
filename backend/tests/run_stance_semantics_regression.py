"""v1.4.1: konu-bağımsız anlam koruması ve görülmemiş cümleler."""
from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.analyzer import classify_viewpoint_heuristic
from app.evaluation_scenarios import SCENARIOS
from app.stance_engine import (
    _positive_conditional_signal,
    _structural_label,
    classify_stances,
    semantic_guardrail_label,
)


SUPPORT = 'Destekleyen'
RESTRICT = 'Karşı / Sınırlayıcı'
CONDITIONAL = 'Koşullu / Dengeli'
NEUTRAL = 'Soru / Tarafsız'


# Bu cümlelerin hiçbiri mevcut 80 örnekli doğrulama setinde yer almaz.
# Ayrı testler yapısal karar ve modelsiz yedek için aynı sonucu doğrular.
HOLDOUT_CASES = (
    ('kutuphane_erisim', 'Kütüphane erişimi nasıl düzenlenmeli?',
     'Kütüphane erişiminin devam etmesinden yanayım.', SUPPORT),
    ('ogrenci_servisi', 'Öğrenci servisi sürmeli mi?',
     'Servis hattının sürmesini savunuyorum.', SUPPORT),
    ('iletisim_hakki', 'Okul telefonları nasıl düzenlenmeli?',
     'İletişim hakkının korunmasını istiyorum.', SUPPORT),
    ('esnek_calisma_secimi', 'Uzaktan çalışma sürmeli mi?',
     'Esnek çalışma seçiminin devam etmesini destekliyorum.', SUPPORT),
    ('hizmet_surekliligi', 'Kampüs hizmeti nasıl düzenlenmeli?',
     'Bu hizmetin sürmesini savunuyorum.', SUPPORT),
    ('ogrenci_erisimi', 'Kütüphane hizmeti devam etmeli mi?',
     'Öğrencilerin erişiminin korunmasından yanayım.', SUPPORT),
    ('secim_hakki', 'İşyeri politikası nasıl kurulmalı?',
     'Çalışanların seçim hakkının sürmesini istiyorum.', SUPPORT),
    ('gece_uygulamasi', 'Ulaşım uygulaması sürmeli mi?',
     'Gece uygulamasının devam etmesini savunuyorum.', SUPPORT),
    ('iletisim_savunusu', 'İletişim nasıl sürmeli?',
     'İletişim hakkının sürmesini destekliyorum.', SUPPORT),
    ('destek_hizmeti', 'Okul sonrası destek programı',
     'Destek hizmetinin devam etmesini istiyorum.', SUPPORT),
    ('arastirma_aciklama', 'Okul tartışması',
     'Araştırma açıklanmalı; verilen oran doğrulanamaz.', NEUTRAL),
    ('calisma_paylasma', 'Okul tartışması',
     'Çalışma paylaşılmalı, bu istatistik sınanamaz.', NEUTRAL),
    ('kanit_sunma', 'Okul tartışması',
     'Kanıt sunulmalı; açıklanan yüzde kanıtlanamaz.', NEUTRAL),
    ('orneklem_yayimlama', 'Okul tartışması',
     'Örneklem yayımlanmalı, bu sonuç doğrulanamaz.', NEUTRAL),
    ('veri_aciklama', 'Okul tartışması',
     'Veri açıklanmalı; iddia teyit edilemez.', NEUTRAL),
    ('kaynak_paylasma', 'Okul tartışması',
     'Kaynak paylaşılmalı; açıklanan rakam doğrulanamaz.', NEUTRAL),
    ('arastirma_sunma', 'Okul tartışması',
     'Araştırma sunulmalı; açıklanan sonuç kanıtlanamaz.', NEUTRAL),
    ('kanit_paylasma', 'Okul tartışması',
     'Kanıt paylaşılmalı; verilen istatistik sınanamaz.', NEUTRAL),
    ('veri_paylasma', 'Okul tartışması',
     'Veri paylaşılmalı; bu yüzde doğrulanamaz.', NEUTRAL),
    ('arastirma_yayimlama', 'Okul tartışması',
     'Araştırma yayımlanmalı; bu orana güvenilemez.', NEUTRAL),
    ('denetimsiz_servis', 'Ulaşım güvenliği',
     'Denetimsiz servis işletilmesi ciddi sorun oluşturuyor.', RESTRICT),
    ('kuralsiz_veri', 'Veri güvenliği',
     'Kuralsız veri paylaşımı ciddi problem yaratıyor.', RESTRICT),
    ('sartsiz_erisim', 'Kampüs erişimi',
     'Şartsız erişim ciddi sorun doğuruyor.', RESTRICT),
    ('denetimsiz_surucu', 'Ulaşım güvenliği',
     'Denetimsiz sürücü yönetimi ciddi problem.', RESTRICT),
    ('kuralsiz_ulasim', 'Kampüs erişimi',
     'Kuralsız gece ulaşımı ciddi sorun.', RESTRICT),
    ('sartsiz_ofis', 'İşyeri güvenliği',
     'Şartsız ofis erişimi ciddi problem.', RESTRICT),
    ('denetimli_servis', 'Servis düzenlemesi',
     'Servis güvenlik denetimi altında devam etmeli.', CONDITIONAL),
    ('kuralli_kullanim', 'Kullanım düzenlemesi',
     'Kullanım açık kurallarla sürdürülebilir.', CONDITIONAL),
    ('denetimli_arac', 'Araç güvenliği',
     'Araçlar denetim altında kullanılabilir.', CONDITIONAL),
    ('kaynak_sarti', 'Kaynak düzenlemesi',
     'Kaynak gösterme şartıyla erişime izin verilebilir.', CONDITIONAL),
    ('olumsuz_ve_olumlu_denetim', 'Hizmet güvenliği',
     'Denetimsiz hizmet ancak güvenlik denetimi sağlanırsa sürebilir.', CONDITIONAL),
    ('olumsuz_ve_olumlu_kural', 'Erişim politikası',
     'Kuralsız kullanım yerine açık kurallarla erişim düzenlenmeli.', CONDITIONAL),
    ('yalnizca_ofis', 'Uzaktan çalışma sürmeli mi?',
     'Toplantılar yalnızca ofiste yapılmalı.', RESTRICT),
    ('sadece_is_yeri', 'Uzaktan çalışma sürmeli mi?',
     'Ekip görüşmeleri sadece iş yerinde gerçekleştirilmeli.', RESTRICT),
    ('mutlaka_isyeri', 'Uzaktan çalışma sürmeli mi?',
     'Sunumlar mutlaka işyerinde yapılmalı.', RESTRICT),
    ('mecburi_yuz_yuze', 'Uzaktan çalışma sürmeli mi?',
     'Çalışanlar mecburen yüz yüze toplanmalı.', RESTRICT),
    ('ofiste_yurutme', 'Uzaktan çalışma sürmeli mi?',
     'Bu çalışma yalnızca ofiste yürütülmeli.', RESTRICT),
    ('fiziksel_zorunluluk', 'Uzaktan çalışma sürmeli mi?',
     'Ekip yalnızca fiziksel olarak bulunmalı.', RESTRICT),
    ('zorunlu_ofis', 'Uzaktan çalışma sürmeli mi?',
     'Kritik görüşmeler zorunlu olarak ofiste gerçekleştirilmeli.', RESTRICT),
    ('yuz_yuze_toplanti', 'Uzaktan çalışma sürmeli mi?',
     'Takım buluşmaları sadece yüz yüze yapılmalı.', RESTRICT),
    ('kanit_ve_acik_yasak', 'Öğrenme araçları',
     'Araştırma paylaşılmalı ve uygulama kesinlikle yasaklanmalı.', RESTRICT),
    ('kanit_ve_acik_serbesti', 'Öğrenme araçları',
     'Araştırma paylaşılmalı ve erişim serbest olmalı.', SUPPORT),
)


class StructuralUnseenSentenceRegression(unittest.TestCase):
    """Her örnekte hibrit motorun yüksek kesinlikli yapısal yolunu ölçer."""


class HeuristicUnseenSentenceRegression(unittest.TestCase):
    """AI yüklenmediğinde de aynı dil anlamının korunmasını doğrular."""


def _make_structural_test(title: str, text: str, expected: str):
    def test(self):
        label, reason = _structural_label(text, title)
        self.assertEqual(label, expected, text)
        self.assertTrue(reason)

    return test


def _make_heuristic_test(title: str, text: str, expected: str):
    def test(self):
        self.assertEqual(classify_viewpoint_heuristic(text, title), expected, text)

    return test


for index, (name, title, text, expected) in enumerate(HOLDOUT_CASES, start=1):
    setattr(
        StructuralUnseenSentenceRegression,
        f'test_{index:02d}_{name}',
        _make_structural_test(title, text, expected),
    )
    setattr(
        HeuristicUnseenSentenceRegression,
        f'test_{index:02d}_{name}',
        _make_heuristic_test(title, text, expected),
    )


class SemanticPriorityAndGeneralizationRegression(unittest.TestCase):
    def test_01_holdout_sentences_do_not_overlap_existing_scenarios(self):
        existing = {case.text for scenario in SCENARIOS for case in scenario.cases}
        holdout = {row[2] for row in HOLDOUT_CASES}
        self.assertEqual(holdout & existing, set())

    def test_02_all_holdout_sentences_are_unique(self):
        self.assertEqual(len(HOLDOUT_CASES), len({row[2] for row in HOLDOUT_CASES}))

    def test_03_holdout_covers_all_four_product_classes(self):
        self.assertEqual({row[3] for row in HOLDOUT_CASES}, {
            SUPPORT, RESTRICT, CONDITIONAL, NEUTRAL,
        })

    def test_04_holdout_adds_topics_beyond_original_four(self):
        original = {scenario.title for scenario in SCENARIOS}
        self.assertTrue(any(row[1] not in original for row in HOLDOUT_CASES))

    def test_05_denetimsiz_is_not_positive_supervision(self):
        self.assertFalse(_positive_conditional_signal('denetimsiz'))

    def test_06_kuralsiz_is_not_a_positive_rule(self):
        self.assertFalse(_positive_conditional_signal('kuralsız'))

    def test_07_sartsiz_is_not_a_positive_condition(self):
        self.assertFalse(_positive_conditional_signal('şartsız'))

    def test_08_positive_supervision_is_still_recognized(self):
        self.assertTrue(_positive_conditional_signal('güvenlik denetimi'))

    def test_09_positive_rule_is_still_recognized(self):
        self.assertTrue(_positive_conditional_signal('açık kurallarla'))

    def test_10_positive_condition_is_still_recognized(self):
        self.assertTrue(_positive_conditional_signal('kaynak şartıyla'))

    def test_11_positive_supervision_can_follow_negative_supervision(self):
        self.assertTrue(_positive_conditional_signal(
            'denetimsiz hizmet yerine gerçek denetim gerekir'
        ))

    def test_12_conditional_continuation_is_not_relabelled_as_unlimited_support(self):
        text = 'Servis güvenlik denetimi altında devam etmeli.'
        self.assertEqual(semantic_guardrail_label(text), (None, None))
        self.assertEqual(_structural_label(text)[0], CONDITIONAL)

    def test_13_explicit_rejection_cannot_become_continuation_support(self):
        text = 'Bu hizmetin devam etmesine karşıyım.'
        self.assertEqual(semantic_guardrail_label(text), (None, None))

    def test_14_explicit_question_takes_priority_over_continuation(self):
        label, reason = _structural_label(
            'Erişimin devam etmesini istiyor musunuz?',
            'Kütüphane kullanımı',
        )
        self.assertEqual((label, reason), (NEUTRAL, 'yapısal soru sinyali'))

    def test_15_explicit_question_takes_priority_over_office_restriction(self):
        label, reason = _structural_label(
            'Toplantılar yalnızca ofiste yapılmalı mı?',
            'Uzaktan çalışma sürmeli mi?',
        )
        self.assertEqual((label, reason), (NEUTRAL, 'yapısal soru sinyali'))

    def test_16_office_rule_is_not_applied_to_unrelated_topics(self):
        text = 'Toplantılar yalnızca ofiste yapılmalı.'
        self.assertEqual(
            semantic_guardrail_label(text, 'Ofis toplantı kültürü nasıl olmalı?'),
            (None, None),
        )

    def test_17_office_rule_requires_an_actual_mandatory_action(self):
        self.assertEqual(
            semantic_guardrail_label(
                'Toplantılar yalnızca ofiste güzel geçiyor.',
                'Uzaktan çalışma sürmeli mi?',
            ),
            (None, None),
        )

    def test_18_hybrid_topic_also_receives_restriction_context(self):
        self.assertEqual(
            _structural_label(
                'Toplantılar sadece ofiste yapılmalı.',
                'Hibrit çalışma modeli sürmeli mi?',
            )[0],
            RESTRICT,
        )

    def test_19_evidence_request_cannot_hide_explicit_ban(self):
        text = 'Araştırma açıklanmalı ve uygulama yasaklanmalı.'
        self.assertEqual(_structural_label(text)[0], RESTRICT)

    def test_20_evidence_request_cannot_hide_explicit_permission(self):
        text = 'Veri açıklanmalı ama erişim serbest olmalı.'
        self.assertEqual(_structural_label(text)[0], SUPPORT)

    def test_21_ama_inside_uygulama_is_not_a_conditional_conjunction(self):
        text = 'Araştırma paylaşılmalı ve uygulama kesinlikle yasaklanmalı.'
        self.assertEqual(classify_viewpoint_heuristic(text), RESTRICT)

    def test_22_real_ama_conjunction_is_still_conditional(self):
        text = 'Kullanım faydalı ama riskli.'
        self.assertEqual(classify_viewpoint_heuristic(text), CONDITIONAL)

    def test_23_guarded_sentences_do_not_trigger_transformer(self):
        model = Mock()
        comments = [
            SimpleNamespace(id=index, text=row[2])
            for index, row in enumerate(HOLDOUT_CASES[:10], start=1)
        ]
        with patch('app.stance_engine.load_model', return_value=model):
            details, info = classify_stances('Kütüphane erişimi', comments)
        model.assert_not_called()
        self.assertEqual(len(details), 10)
        self.assertEqual(info['transformer_count'], 0)

    def test_24_guarded_structural_decisions_never_claim_model_confidence(self):
        model = Mock()
        comment = SimpleNamespace(id=1, text=HOLDOUT_CASES[0][2])
        with patch('app.stance_engine.load_model', return_value=model):
            details, _ = classify_stances('Kütüphane erişimi', [comment])
        self.assertEqual(details[0]['confidence'], 0.0)
        self.assertIn('anlamsal tutarlılık:', details[0]['engine'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
