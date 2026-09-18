"""v1.5.0: konuya duyarlı görüş, özet ve Köprü davranışı."""
from __future__ import annotations

import unittest

from app.analyzer import analyze_demo, analyze_post, build_custom_post
from app.argument_engine import _bridge_contrast, _divergence_text
from app.topic_context import CONDITIONAL, NEUTRAL, RESTRICT, SUPPORT, resolve_topic_context
from app.viewpoint_engine import _display_name, _main_argument


REMOTE_TITLE = 'Şirketlerde uzaktan çalışma sürmeli mi?'
REMOTE_COMMENTS = [
    'Çalışanların mekân seçimini korumasından yanayım.',
    'Kritik ekip toplantıları yalnızca ofiste yapılmalı.',
    'Uzaktan çalışma açık kurallarla uygulanmalı.',
    'Uzaktan çalışmanın verimliliğine ilişkin araştırma var mı?',
]


def analyze(title: str = REMOTE_TITLE, comments: list[str] | None = None):
    return analyze_post(build_custom_post(title, comments or REMOTE_COMMENTS), use_ai=False)


class TopicContextResolutionTests(unittest.TestCase):
    def test_01_remote_work_title_resolves(self):
        self.assertEqual(resolve_topic_context(REMOTE_TITLE).key, 'remote-work')

    def test_02_remote_work_title_is_case_insensitive(self):
        self.assertEqual(resolve_topic_context('UZAKTAN ÇALIŞMA sürmeli mi?').key, 'remote-work')

    def test_03_phone_title_resolves(self):
        self.assertEqual(resolve_topic_context('Okulda telefon kullanımı nasıl düzenlenmeli?').key, 'phone-use')

    def test_04_canteen_title_resolves(self):
        self.assertEqual(resolve_topic_context('Okul kantininde hangi ürünler satılmalı?').key, 'school-canteen')

    def test_05_recycling_title_resolves(self):
        self.assertEqual(resolve_topic_context('Kentte geri dönüşüm nasıl yaygınlaşmalı?').key, 'recycling')

    def test_06_library_title_resolves(self):
        self.assertEqual(resolve_topic_context('Halk kütüphaneleri hafta sonu açık kalmalı mı?').key, 'library-access')

    def test_07_digital_play_title_resolves(self):
        self.assertEqual(resolve_topic_context('Çocukların dijital oyun süresi nasıl belirlenmeli?').key, 'digital-play')

    def test_08_neighborhood_park_title_resolves(self):
        self.assertEqual(resolve_topic_context('Mahalle parkları akşam açık kalmalı mı?').key, 'neighborhood-park')

    def test_09_bicycle_title_resolves(self):
        self.assertEqual(resolve_topic_context('Bisiklet yolu genişletilmeli mi?').key, 'bicycle-access')

    def test_10_public_transport_title_resolves(self):
        self.assertEqual(resolve_topic_context('Belediye otobüs hizmeti sürmeli mi?').key, 'public-transport')

    def test_11_unknown_title_preserves_generic_behavior(self):
        context = resolve_topic_context('Yeni öneri uygulanmalı mı?')
        self.assertEqual(context.key, 'generic')
        self.assertFalse(context.is_specific)

    def test_12_academic_ai_demo_is_explicitly_frozen(self):
        context = resolve_topic_context('Üniversitelerde yapay zekâ kullanımı yasaklanmalı mı?')
        self.assertEqual(context.key, 'academic-ai')
        self.assertFalse(context.is_specific)

    def test_13_unknown_canonical_label_is_not_rewritten(self):
        self.assertIsNone(resolve_topic_context(REMOTE_TITLE).display_name('Yeni deneysel etiket'))

    def test_14_context_has_deterministic_positions(self):
        context = resolve_topic_context(REMOTE_TITLE)
        self.assertEqual(context.position(SUPPORT), 'uzaktan çalışmanın sürmesi')
        self.assertEqual(context.position(RESTRICT), 'ofis zorunluluğu')
        self.assertEqual(context.position(CONDITIONAL), 'kurallı veya hibrit çalışma')

    def test_15_context_does_not_invent_single_position_contrast(self):
        self.assertIsNone(resolve_topic_context(REMOTE_TITLE).contrast([SUPPORT]))


class TopicAwareAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.result = analyze()
        self.views = {view.name: view for view in self.result.viewpoints}

    def test_16_canonical_names_remain_unchanged(self):
        self.assertEqual(set(self.views), {SUPPORT, RESTRICT, CONDITIONAL, NEUTRAL})

    def test_17_remote_support_name_is_topic_specific(self):
        self.assertEqual(self.views[SUPPORT].display_name, 'Uzaktan çalışmanın devamını savunanlar')

    def test_18_remote_restriction_name_is_topic_specific(self):
        self.assertEqual(self.views[RESTRICT].display_name, 'Ofis zorunluluğu veya daha güçlü sınırlama')

    def test_19_remote_conditional_name_is_topic_specific(self):
        self.assertEqual(self.views[CONDITIONAL].display_name, 'Kurallı veya hibrit çalışma')

    def test_20_remote_neutral_name_mentions_topic(self):
        self.assertIn('Uzaktan çalışma', self.views[NEUTRAL].display_name)

    def test_21_support_argument_mentions_remote_work(self):
        self.assertIn('uzaktan çalışma', self.views[SUPPORT].main_argument.casefold())

    def test_22_restriction_argument_mentions_office_requirement(self):
        self.assertIn('ofis zorunluluğu', self.views[RESTRICT].main_argument.casefold())

    def test_23_conditional_argument_mentions_hybrid(self):
        self.assertIn('hibrit çalışma', self.views[CONDITIONAL].main_argument.casefold())

    def test_24_relationship_note_explains_real_remote_positions(self):
        self.assertIn('ofis zorunluluğu', self.views[SUPPORT].relationship_note.casefold())

    def test_25_neutral_group_is_not_falsely_opposing(self):
        self.assertEqual(self.views[NEUTRAL].opposing_viewpoint_names, [])

    def test_26_summary_includes_topic_aware_support_label(self):
        self.assertIn('Uzaktan çalışmanın devamını savunanlar', self.result.short_summary)

    def test_27_summary_includes_topic_aware_office_label(self):
        self.assertIn('Ofis zorunluluğu veya daha güçlü sınırlama', self.result.short_summary)

    def test_28_summary_includes_topic_aware_conditional_label(self):
        self.assertIn('Kurallı veya hibrit çalışma', self.result.short_summary)

    def test_29_summary_does_not_treat_question_as_a_decision_side(self):
        self.assertNotIn('Uzaktan çalışma için kanıt / tarafsız değerlendirme (%', self.result.short_summary)

    def test_30_bridge_divergence_mentions_remote_work(self):
        self.assertIn('uzaktan çalışmanın sürmesi', self.result.bridge['main_divergence'].casefold())

    def test_31_bridge_divergence_mentions_office_requirement(self):
        self.assertIn('ofis zorunluluğu', self.result.bridge['main_divergence'].casefold())

    def test_32_bridge_divergence_mentions_hybrid_work(self):
        self.assertIn('hibrit çalışma', self.result.bridge['main_divergence'].casefold())

    def test_33_bridge_question_is_limited_to_twenty_eight_words(self):
        self.assertLessEqual(len(self.result.bridge['bridge_question'].split()), 28)

    def test_34_bridge_question_preserves_topic(self):
        self.assertIn('uzaktan çalışma', self.result.bridge['bridge_question'].casefold())

    def test_35_bridge_keeps_canonical_identity_names(self):
        self.assertEqual(set(self.result.bridge['contrast_viewpoint_names']), {SUPPORT, RESTRICT, CONDITIONAL})

    def test_36_bridge_exposes_topic_aware_visible_labels(self):
        self.assertIn('Ofis zorunluluğu veya daha güçlü sınırlama', self.result.bridge['contrast_viewpoint_labels'])

    def test_37_question_impact_uses_visible_cluster_names(self):
        self.assertIn('Kurallı veya hibrit çalışma', self.result.unanswered_questions[0].impact)

    def test_38_question_identity_retains_canonical_names(self):
        self.assertIn(CONDITIONAL, self.result.unanswered_questions[0].affected_viewpoints)

    def test_39_engine_exposes_context_key(self):
        self.assertEqual(self.result.engine['viewpoint_topic_key'], 'remote-work')

    def test_40_engine_exposes_context_subject(self):
        self.assertEqual(self.result.engine['viewpoint_topic_subject'], 'uzaktan çalışma')

    def test_41_engine_marks_actual_specific_context(self):
        self.assertTrue(self.result.engine['viewpoint_topic_specific'])

    def test_42_old_display_name_helper_signature_is_preserved(self):
        self.assertEqual(_display_name(CONDITIONAL, True), 'Kontrollü ve kurallı kullanım')

    def test_43_old_argument_helper_signature_is_preserved(self):
        self.assertIn('Tam yasak yerine', _main_argument(CONDITIONAL, [], True))

    def test_44_old_bridge_helper_signatures_are_preserved(self):
        self.assertIn('öneriyi', _bridge_contrast([SUPPORT, RESTRICT], False))
        self.assertIn('Öneriyi', _divergence_text([SUPPORT, RESTRICT], False))


class FrozenAcademicDemoTests(unittest.TestCase):
    def setUp(self):
        self.result = analyze_demo(use_ai=False)

    def test_45_demo_source_awareness_stays_twenty_five_percent(self):
        self.assertEqual(self.result.indicators['source_awareness'], 25)

    def test_46_demo_retains_twenty_unique_comments(self):
        self.assertEqual(self.result.indicators['comment_count'], 20)

    def test_47_demo_retains_two_open_questions(self):
        self.assertEqual(self.result.indicators['unanswered_question_count'], 2)

    def test_48_demo_restriction_label_stays_frozen(self):
        views = {item.name: item.display_name for item in self.result.viewpoints}
        self.assertEqual(views[RESTRICT], 'Tam yasak veya güçlü sınırlama')

    def test_49_demo_conditional_label_stays_frozen(self):
        views = {item.name: item.display_name for item in self.result.viewpoints}
        self.assertEqual(views[CONDITIONAL], 'Kontrollü ve kurallı kullanım')

    def test_50_demo_bridge_remains_under_existing_word_limit(self):
        self.assertLessEqual(len(self.result.bridge['bridge_question'].split()), 28)

    def test_51_demo_context_is_not_misrepresented_as_new_specific_profile(self):
        self.assertEqual(self.result.engine['viewpoint_topic_key'], 'academic-ai')
        self.assertFalse(self.result.engine['viewpoint_topic_specific'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
