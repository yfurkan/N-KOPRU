"""v1.4.1 doğrulama sayaçları, kalıcılık ve ölçüm dürüstlüğü."""
from __future__ import annotations

import json
import os
import unittest
from collections import Counter
from unittest.mock import patch

os.environ.setdefault('N_KOPRU_DB_PATH', '/tmp/nkopru_v141_semantic_evaluation.db')

from fastapi.testclient import TestClient

from app.analyzer import analyze_demo
from app.database import connection, reset_database_for_tests
from app.evaluation import SCENARIO_RESULT_META_KEY
from app.evaluation_scenarios import SCENARIO_DATASET_VERSION, SCENARIOS, scenario_dataset_info
from app.main import app
from app.version import APP_VERSION


FIXED_CASES = (
    (
        'akademik-yapay-zeka',
        'Bu araçlara erişimin devam etmesinden yanayım.',
        'Destekleyen',
        'erişim ve süreklilik desteği',
    ),
    (
        'okulda-telefon',
        'Ders aralarında iletişim hakkının sürmesini istiyorum.',
        'Destekleyen',
        'erişim ve süreklilik desteği',
    ),
    (
        'okulda-telefon',
        'Araştırma paylaşılmalı; aksi halde verilen oran doğrulanamaz.',
        'Soru / Tarafsız',
        'kaynak/veri eleştirisi',
    ),
    (
        'kampus-ulasimi',
        'Denetimsiz sürücü kullanılması ciddi sorun oluşturuyor.',
        'Karşı / Sınırlayıcı',
        'kısıtlama sinyali',
    ),
    (
        'uzaktan-calisma',
        'Çalışanların mekân seçimini korumasından yanayım.',
        'Destekleyen',
        'erişim ve süreklilik desteği',
    ),
    (
        'uzaktan-calisma',
        'Kritik ekip toplantıları yalnızca ofiste yapılmalı.',
        'Karşı / Sınırlayıcı',
        'zorunlu fiziksel çalışma',
    ),
)


def controlled_restrict_model(sequences, candidate_labels, **kwargs):
    """Sadece gerçekten çözümsüz üç yoruma deterministik test modeli uygular."""
    return [
        {'labels': [candidate_labels[1]], 'scores': [0.89]}
        for _ in sequences
    ]


class SemanticEvaluationRegression(unittest.TestCase):
    def setUp(self):
        reset_database_for_tests()
        self.client = TestClient(app)

    def run_hybrid(self):
        with patch('app.stance_engine._PIPELINE', controlled_restrict_model), patch(
            'app.stance_engine.dependencies_installed',
            return_value=True,
        ):
            response = self.client.post(
                '/api/evaluation/scenarios/run',
                json={'use_ai': True},
            )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_01_controlled_hybrid_classifies_all_existing_cases(self):
        result = self.run_hybrid()
        self.assertEqual((result['correct_count'], result['error_count']), (80, 0))

    def test_02_accuracy_is_calculated_from_eighty_actual_predictions(self):
        result = self.run_hybrid()
        self.assertEqual(
            result['accuracy'],
            sum(item['correct'] for item in result['predictions']) / len(result['predictions']),
        )

    def test_03_macro_f1_follows_real_class_metrics(self):
        result = self.run_hybrid()
        self.assertEqual(
            result['macro_f1'],
            sum(item['f1'] for item in result['class_metrics']) / 4,
        )

    def test_04_seventy_seven_cases_are_structurally_resolved(self):
        self.assertEqual(self.run_hybrid()['structural_decision_count'], 77)

    def test_05_three_genuinely_implicit_restrictions_use_the_model(self):
        self.assertEqual(self.run_hybrid()['transformer_inference_count'], 3)

    def test_06_semantic_guardrail_count_is_thirteen(self):
        self.assertEqual(self.run_hybrid()['semantic_guardrail_count'], 13)

    def test_07_semantic_count_is_derived_from_decision_reasons(self):
        result = self.run_hybrid()
        actual = sum(
            row['decision_engine'].startswith('anlamsal tutarlılık:')
            for row in result['predictions']
        )
        self.assertEqual(result['semantic_guardrail_count'], actual)

    def test_08_topic_guardrail_counts_sum_to_total(self):
        result = self.run_hybrid()
        self.assertEqual(
            sum(row['semantic_guardrail_count'] for row in result['scenarios']),
            result['semantic_guardrail_count'],
        )

    def test_09_per_topic_semantic_counts_are_real(self):
        result = self.run_hybrid()
        self.assertEqual(
            {row['key']: row['semantic_guardrail_count'] for row in result['scenarios']},
            {
                'akademik-yapay-zeka': 3,
                'okulda-telefon': 3,
                'kampus-ulasimi': 3,
                'uzaktan-calisma': 4,
            },
        )

    def test_10_remote_topic_no_longer_needs_model_inference(self):
        remote = next(
            row for row in self.run_hybrid()['scenarios']
            if row['key'] == 'uzaktan-calisma'
        )
        self.assertEqual((remote['correct_count'], remote['transformer_inference_count']), (20, 0))

    def test_11_other_three_topics_each_keep_one_genuine_model_inference(self):
        result = self.run_hybrid()
        self.assertEqual(
            [row['transformer_inference_count'] for row in result['scenarios']],
            [1, 1, 1, 0],
        )

    def test_12_model_confidence_exists_only_for_three_real_test_inferences(self):
        result = self.run_hybrid()
        confidences = [
            row['model_confidence']
            for row in result['predictions']
            if row['model_confidence'] is not None
        ]
        self.assertEqual(confidences, [0.89, 0.89, 0.89])

    def test_13_structural_results_do_not_invent_model_confidence(self):
        result = self.run_hybrid()
        structural = [
            row for row in result['predictions']
            if row['decision_engine'].startswith('anlamsal tutarlılık:')
        ]
        self.assertTrue(all(row['model_confidence'] is None for row in structural))

    def test_14_existing_dataset_version_is_unchanged(self):
        self.assertEqual(SCENARIO_DATASET_VERSION, '2026.08.22-v1')

    def test_15_existing_eighty_labels_are_not_rewritten(self):
        expected = Counter(
            case.expected_label
            for scenario in SCENARIOS
            for case in scenario.cases
        )
        self.assertEqual(set(expected.values()), {20})
        self.assertEqual(sum(expected.values()), 80)

    def test_16_calibration_note_discloses_use_of_prior_errors(self):
        note = scenario_dataset_info()['calibration_note']
        self.assertIn('hataları', note)
        self.assertIn('iyileştirmek', note)

    def test_17_calibration_note_rejects_independent_holdout_claim(self):
        note = scenario_dataset_info()['calibration_note']
        self.assertIn('bağımsız tutma testi', note)
        self.assertIn('dış benchmark', note)

    def test_18_previous_honest_scope_limitation_is_preserved(self):
        dataset = self.run_hybrid()['dataset']
        self.assertFalse(dataset['is_external_benchmark'])
        self.assertFalse(dataset['contains_user_content'])
        self.assertIn('Bağımsız dış veri seti', dataset['limitation'])

    def test_19_calibration_note_is_saved_with_the_sqlite_result(self):
        result = self.run_hybrid()
        restored = self.client.get('/api/evaluation').json()['latest_scenario_result']
        self.assertEqual(restored['dataset']['calibration_note'], result['dataset']['calibration_note'])

    def test_20_semantic_counter_is_saved_with_the_sqlite_result(self):
        result = self.run_hybrid()
        restored = self.client.get('/api/evaluation').json()['latest_scenario_result']
        self.assertEqual(restored['semantic_guardrail_count'], result['semantic_guardrail_count'])

    def test_21_previous_version_result_without_new_fields_is_still_readable(self):
        old_result = self.run_hybrid()
        old_result['version'] = '1.4.0'
        old_result.pop('semantic_guardrail_count')
        old_result['dataset'].pop('calibration_note')
        for scenario in old_result['scenarios']:
            scenario.pop('semantic_guardrail_count')
        with connection() as conn:
            conn.execute(
                'UPDATE app_meta SET value = ? WHERE key = ?',
                (json.dumps(old_result, ensure_ascii=False), SCENARIO_RESULT_META_KEY),
            )
        restored = self.client.get('/api/evaluation').json()['latest_scenario_result']
        self.assertEqual(restored['version'], '1.4.0')
        self.assertNotIn('semantic_guardrail_count', restored)
        self.assertEqual(restored['sample_count'], 80)

    def test_22_health_uses_central_application_version(self):
        self.assertEqual(self.client.get('/health').json()['version'], APP_VERSION)

    def test_23_openapi_uses_central_application_version(self):
        self.assertEqual(self.client.get('/openapi.json').json()['info']['version'], APP_VERSION)

    def test_24_evaluation_result_uses_central_application_version(self):
        self.assertEqual(self.run_hybrid()['version'], APP_VERSION)

    def test_25_reference_evaluation_status_uses_central_application_version(self):
        self.assertEqual(self.client.get('/api/evaluation').json()['version'], APP_VERSION)

    def test_26_original_demo_source_awareness_is_preserved(self):
        self.assertEqual(analyze_demo(use_ai=False).indicators['source_awareness'], 25)

    def test_27_original_demo_open_questions_are_preserved(self):
        result = analyze_demo(use_ai=False)
        self.assertEqual({row.comment_id for row in result.unanswered_questions}, {6, 13})

    def test_28_original_demo_short_bridge_is_preserved(self):
        result = analyze_demo(use_ai=False)
        self.assertLessEqual(len(result.bridge['bridge_question'].split()), 28)

    def test_29_no_hardware_model_is_assumed(self):
        result = self.run_hybrid()
        self.assertIn(result['model_status']['device'], {'cpu', 'cuda'})

    def test_30_heuristic_only_mode_remains_honest_about_model_usage(self):
        response = self.client.post(
            '/api/evaluation/scenarios/run',
            json={'use_ai': False},
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertFalse(result['effective_ai'])
        self.assertEqual(result['transformer_inference_count'], 0)
        self.assertEqual(result['structural_decision_count'], 80)

    def test_31_no_errors_are_fabricated_after_all_predictions_are_correct(self):
        result = self.run_hybrid()
        self.assertEqual(result['errors'], [])
        self.assertTrue(all(row['correct'] for row in result['predictions']))

    def test_32_per_topic_totals_remain_balanced(self):
        result = self.run_hybrid()
        self.assertTrue(all(row['sample_count'] == 20 for row in result['scenarios']))
        self.assertTrue(all(row['correct_count'] == 20 for row in result['scenarios']))


def _make_fixed_prediction_test(
    scenario_key: str,
    text: str,
    expected: str,
    reason_fragment: str,
):
    def test(self):
        result = self.run_hybrid()
        prediction = next(row for row in result['predictions'] if row['text'] == text)
        self.assertEqual(prediction['scenario_key'], scenario_key)
        self.assertEqual(prediction['predicted_label'], expected)
        self.assertIn(reason_fragment, prediction['decision_engine'])
        self.assertIsNone(prediction['model_confidence'])

    return test


for index, case in enumerate(FIXED_CASES, start=33):
    setattr(
        SemanticEvaluationRegression,
        f'test_{index:02d}_original_error_is_fixed_with_explainable_reason',
        _make_fixed_prediction_test(*case),
    )


if __name__ == '__main__':
    unittest.main(verbosity=2)
