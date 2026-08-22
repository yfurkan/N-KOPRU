from __future__ import annotations

import unittest
from unittest.mock import patch

from app.analyzer import analyze_demo, analyze_post, build_custom_post
from app.models import AnalysisResult, Comment, Post


def make_post(title: str, texts: list[str], post_id: int = 8121) -> Post:
    return Post(
        id=post_id,
        author='Görüş Haritası Testi',
        handle='@gorus_testi',
        text=title,
        created_at='şimdi',
        comments=[
            Comment(id=index + 1, author=f'K{index + 1}', text=text, created_at='şimdi', likes=index)
            for index, text in enumerate(texts)
        ],
    )


class ViewpointAnalysisRegression(unittest.TestCase):
    def test_01_canonical_cluster_names_remain_backward_compatible(self):
        result = analyze_demo(use_ai=False)
        self.assertEqual(
            {item.name for item in result.viewpoints},
            {'Diğer / Nötr', 'Koşullu / Dengeli', 'Karşı / Sınırlayıcı', 'Soru / Tarafsız'},
        )

    def test_02_restriction_discussion_uses_contextual_labels(self):
        result = analyze_demo(use_ai=False)
        labels = {item.name: item.display_name for item in result.viewpoints}
        self.assertEqual(labels['Koşullu / Dengeli'], 'Kontrollü ve kurallı kullanım')
        self.assertEqual(labels['Karşı / Sınırlayıcı'], 'Tam yasak veya güçlü sınırlama')
        self.assertEqual(labels['Soru / Tarafsız'], 'Kanıt talebi / tarafsız değerlendirme')

    def test_03_support_label_does_not_confuse_ban_and_usage(self):
        result = analyze_post(make_post('Yapay zekâ kullanımı yasaklanmalı mı?', [
            'Yapay zekâ faydalı ve yararlı bir araçtır.',
            'Kesinlikle yasaklanmalı.',
            'Kontrollü kullanım daha doğru.',
        ]), use_ai=False)
        supported = next(item for item in result.viewpoints if item.name == 'Destekleyen')
        self.assertIn('Yasağa karşı', supported.display_name)
        self.assertIn('yararlı kullanım alanlarının korunması', supported.main_argument)

    def test_04_generic_topic_avoids_unrelated_ban_labels(self):
        result = analyze_post(make_post('Mahalle parkı büyütülmeli mi?', [
            'Bu öneriyi destekliyorum, faydalı olur.',
            'Projeye karşıyım, riskli olabilir.',
            'Bütçe ancak belirli şartlarla uygun olabilir.',
            'Bu maliyetin kaynağı nedir?',
        ]), use_ai=False)
        self.assertEqual(result.engine['viewpoint_context'], 'general-discussion')
        self.assertFalse(any('yasak' in item.display_name.casefold() for item in result.viewpoints))

    def test_05_group_counts_match_unique_comments(self):
        result = analyze_demo(use_ai=False)
        self.assertEqual(sum(item.comment_count for item in result.viewpoints), 20)
        self.assertEqual(sum(item.percentage for item in result.viewpoints), 100)

    def test_06_duplicate_comments_do_not_inflate_group_counts(self):
        result = analyze_post(make_post('Yeni karar nasıl düzenlenmeli?', [
            'Kontrollü kullanım daha doğru.',
            'Kontrollü kullanım daha doğru.',
            'Tam yasak gerekli olabilir.',
            'Bu kararın dayandığı veri nedir?',
        ]), use_ai=False)
        self.assertEqual(result.indicators['comment_count'], 3)
        self.assertEqual(sum(item.comment_count for item in result.viewpoints), 3)

    def test_07_representative_comments_belong_to_their_cluster(self):
        result = analyze_demo(use_ai=False)
        by_id = {item.comment_id: item.label for item in result.stance_details}
        for cluster in result.viewpoints:
            self.assertGreaterEqual(len(cluster.representative_comments), 1)
            self.assertLessEqual(len(cluster.representative_comments), 2)
            for item in cluster.representative_comments:
                self.assertEqual(by_id[item.comment_id], cluster.name)
                self.assertTrue(item.author)
                self.assertTrue(item.text)

    def test_08_all_evidence_ids_match_group_size(self):
        result = analyze_demo(use_ai=False)
        for item in result.viewpoints:
            self.assertEqual(len(item.evidence_comment_ids), item.comment_count)
            self.assertEqual(len(set(item.evidence_comment_ids)), item.comment_count)

    def test_09_main_argument_is_topic_and_position_specific(self):
        result = analyze_demo(use_ai=False)
        restrictive = next(item for item in result.viewpoints if item.name == 'Karşı / Sınırlayıcı')
        conditional = next(item for item in result.viewpoints if item.name == 'Koşullu / Dengeli')
        self.assertIn('yasaklama', restrictive.main_argument.casefold())
        self.assertIn('kurallar', conditional.main_argument.casefold())
        self.assertNotEqual(restrictive.main_argument, conditional.main_argument)

    def test_10_neutral_groups_are_not_described_as_opposing_sides(self):
        result = analyze_demo(use_ai=False)
        for item in result.viewpoints:
            if item.name in {'Diğer / Nötr', 'Soru / Tarafsız'}:
                self.assertEqual(item.opposing_viewpoint_names, [])
                self.assertIn('karşıt bir karar tarafı değildir', item.relationship_note)

    def test_11_substantive_positions_link_to_opposing_groups(self):
        result = analyze_demo(use_ai=False)
        conditional = next(item for item in result.viewpoints if item.name == 'Koşullu / Dengeli')
        restrictive = next(item for item in result.viewpoints if item.name == 'Karşı / Sınırlayıcı')
        self.assertIn('Karşı / Sınırlayıcı', conditional.opposing_viewpoint_names)
        self.assertIn('Koşullu / Dengeli', restrictive.opposing_viewpoint_names)

    def test_12_shared_themes_are_grounded_in_existing_common_ground(self):
        result = analyze_demo(use_ai=False)
        themes = {item.theme for item in result.common_ground_details}
        self.assertTrue(any(item.shared_themes for item in result.viewpoints))
        for item in result.viewpoints:
            self.assertTrue(set(item.shared_themes).issubset(themes))

    def test_13_claim_links_use_real_claim_comment_ids(self):
        result = analyze_demo(use_ai=False)
        known = {item.comment_id for item in result.claims}
        linked = {comment_id for cluster in result.viewpoints for comment_id in cluster.related_claim_comment_ids}
        self.assertEqual(linked, known)

    def test_14_question_links_are_consistent_with_question_cards(self):
        result = analyze_demo(use_ai=False)
        known = {item.comment_id for item in result.unanswered_questions}
        linked = {comment_id for cluster in result.viewpoints for comment_id in cluster.related_question_comment_ids}
        self.assertEqual(linked, known)

    def test_15_engine_metadata_describes_viewpoint_layer(self):
        result = analyze_demo(use_ai=False)
        self.assertEqual(result.engine['viewpoint_engine'], 'contextual-evidence-grounded-viewpoints')
        self.assertEqual(result.engine['viewpoint_context'], 'restriction-policy')
        self.assertEqual(result.engine['viewpoint_cluster_count'], len(result.viewpoints))
        self.assertEqual(result.engine['viewpoint_structural_comment_count'], 20)
        self.assertIn('viewpoint_elapsed_ms', result.engine)

    def test_16_fallback_mode_does_not_invent_model_confidence(self):
        result = analyze_demo(use_ai=False)
        self.assertEqual(result.engine['viewpoint_model_comment_count'], 0)
        for cluster in result.viewpoints:
            self.assertEqual(cluster.model_comment_count, 0)
            self.assertEqual(cluster.average_model_confidence, 0)
            self.assertEqual(cluster.structural_comment_count, cluster.comment_count)

    def test_17_model_confidence_excludes_structural_decisions(self):
        post = make_post('Yapay zekâ kullanımı yasaklanmalı mı?', [
            'Öğrencilerin düşünme becerileri korunmalı.',
            'Yararlı kullanım alanları korunabilir.',
            'Açık kurallarla kontrollü kullanım öneriyorum.',
            'Bu kararın dayandığı araştırma var mı?',
        ])
        details = [
            {'comment_id': 1, 'text': post.comments[0].text, 'label': 'Karşı / Sınırlayıcı', 'confidence': 0.78, 'engine': 'mDeBERTa-XNLI'},
            {'comment_id': 2, 'text': post.comments[1].text, 'label': 'Destekleyen', 'confidence': 0.64, 'engine': 'mDeBERTa-XNLI'},
            {'comment_id': 3, 'text': post.comments[2].text, 'label': 'Koşullu / Dengeli', 'confidence': 0.0, 'engine': 'yapısal sinyal'},
            {'comment_id': 4, 'text': post.comments[3].text, 'label': 'Soru / Tarafsız', 'confidence': 0.0, 'engine': 'yapısal soru'},
        ]
        info = {'mode': 'hybrid-transformer', 'message': 'test', 'transformer_count': 2, 'rule_count': 2, 'elapsed_ms': 3}
        with patch('app.analyzer.classify_stances', return_value=(details, info)):
            result = analyze_post(post, use_ai=True)
        self.assertEqual(result.indicators['ai_average_confidence'], 71)
        self.assertEqual(result.engine['viewpoint_model_comment_count'], 2)
        self.assertEqual(result.engine['viewpoint_structural_comment_count'], 2)
        conditional = next(item for item in result.viewpoints if item.name == 'Koşullu / Dengeli')
        self.assertEqual(conditional.average_model_confidence, 0)
        supported = next(item for item in result.viewpoints if item.name == 'Destekleyen')
        self.assertEqual(supported.average_model_confidence, 0.64)

    def test_18_summary_uses_contextual_display_names(self):
        result = analyze_demo(use_ai=False)
        self.assertIn('Kontrollü ve kurallı kullanım', result.short_summary)

    def test_19_old_snapshot_without_viewpoint_fields_still_opens(self):
        payload = analyze_demo(use_ai=False).model_dump()
        legacy_keys = {'name', 'percentage', 'summary'}
        payload['viewpoints'] = [
            {key: value for key, value in item.items() if key in legacy_keys}
            for item in payload['viewpoints']
        ]
        restored = AnalysisResult.model_validate(payload)
        self.assertEqual(restored.viewpoints[0].display_name, '')
        self.assertEqual(restored.viewpoints[0].representative_comments, [])
        self.assertEqual(restored.viewpoints[0].comment_count, 0)

    def test_20_original_source_metric_bridge_and_questions_are_preserved(self):
        result = analyze_demo(use_ai=False)
        self.assertEqual(result.indicators['source_awareness'], 25)
        self.assertEqual({item.comment_id for item in result.unanswered_questions}, {6, 13})
        self.assertLessEqual(len(result.bridge['bridge_question'].split()), 28)

    def test_21_comment_signals_can_reveal_restriction_context(self):
        result = analyze_post(make_post('Yeni uygulama nasıl değerlendirilmeli?', [
            'Tam yasak daha güvenli olabilir.',
            'Yasaklamak yanlış ve faydalı kullanım korunmalı.',
            'Kontrollü kullanım uygun.',
        ]), use_ai=False)
        self.assertEqual(result.engine['viewpoint_context'], 'restriction-policy')

    def test_22_cluster_method_counts_add_up(self):
        result = analyze_demo(use_ai=False)
        for item in result.viewpoints:
            self.assertEqual(item.structural_comment_count + item.model_comment_count, item.comment_count)


if __name__ == '__main__':
    unittest.main(verbosity=2)
