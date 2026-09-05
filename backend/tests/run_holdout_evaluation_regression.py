"""v1.5.0: önceki kalibrasyondan ayrılmış dürüst iç kontrol."""
from __future__ import annotations

from collections import Counter
from statistics import mean
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('N_KOPRU_DB_PATH', '/tmp/nkopru_v142_holdout_regression.db')

from fastapi.testclient import TestClient

from app.database import reset_database_for_tests
from app.evaluation_holdout import HOLDOUT_SCENARIOS, holdout_dataset_info
from app.evaluation_scenarios import SCENARIOS, scenario_dataset_info
from app.main import app
from app.version import APP_VERSION


class HoldoutDatasetContractTests(unittest.TestCase):
    def setUp(self):
        self.info = holdout_dataset_info()

    def test_01_holdout_contains_eighty_new_cases(self):
        self.assertEqual(self.info['sample_count'], 80)

    def test_02_holdout_covers_five_new_topics(self):
        self.assertEqual(self.info['scenario_count'], 5)

    def test_03_holdout_preserves_four_canonical_labels(self):
        self.assertEqual(self.info['label_count'], 4)

    def test_04_global_labels_are_balanced(self):
        self.assertEqual(set(self.info['label_distribution'].values()), {20})

    def test_05_every_new_topic_has_sixteen_cases(self):
        self.assertTrue(all(len(item.cases) == 16 for item in HOLDOUT_SCENARIOS))

    def test_06_every_topic_has_four_examples_per_label(self):
        for scenario in HOLDOUT_SCENARIOS:
            self.assertEqual(set(Counter(item.expected_label for item in scenario.cases).values()), {4})

    def test_07_easy_and_challenging_cases_are_balanced(self):
        self.assertEqual(self.info['difficulty_distribution'], {'temel': 40, 'zor': 40})

    def test_08_case_overlap_counter_is_zero(self):
        self.assertEqual(self.info['calibration_sample_overlap_count'], 0)

    def test_09_topic_overlap_counter_is_zero(self):
        self.assertEqual(self.info['calibration_topic_overlap_count'], 0)

    def test_10_disjoint_status_is_explicit(self):
        self.assertTrue(self.info['is_disjoint_from_calibration'])

    def test_11_case_texts_do_not_overlap_after_normalization(self):
        old = {' '.join(case.text.casefold().split()) for item in SCENARIOS for case in item.cases}
        new = {' '.join(case.text.casefold().split()) for item in HOLDOUT_SCENARIOS for case in item.cases}
        self.assertEqual(old & new, set())

    def test_12_topic_names_do_not_overlap(self):
        self.assertFalse({item.topic for item in HOLDOUT_SCENARIOS} & {item.topic for item in SCENARIOS})

    def test_13_all_new_case_texts_are_unique(self):
        values = [case.text for item in HOLDOUT_SCENARIOS for case in item.cases]
        self.assertEqual(len(values), len(set(values)))

    def test_14_frozen_fingerprint_has_sha256_length(self):
        self.assertEqual(len(self.info['frozen_sha256']), 64)

    def test_15_frozen_fingerprint_is_stable(self):
        self.assertEqual(self.info['frozen_sha256'], holdout_dataset_info()['frozen_sha256'])

    def test_16_dataset_explicitly_is_not_external(self):
        self.assertFalse(self.info['is_external_benchmark'])

    def test_17_dataset_does_not_include_user_content(self):
        self.assertFalse(self.info['contains_user_content'])

    def test_18_scope_rejects_scientific_generalization(self):
        self.assertIn('bilimsel genelleme değildir', self.info['limitation'])

    def test_19_scope_rejects_academic_benchmark_claim(self):
        self.assertIn('akademik benchmark', self.info['limitation'])

    def test_20_calibration_note_discloses_internal_scope(self):
        self.assertIn('projeye içkindir', self.info['calibration_note'])

    def test_21_dataset_records_calibrated_source_version(self):
        self.assertEqual(self.info['calibration_dataset_version'], scenario_dataset_info()['version'])

    def test_22_dataset_role_distinguishes_internal_control(self):
        self.assertEqual(self.info['dataset_role'], 'separate-project-internal-control')

    def test_23_each_case_documents_a_real_challenge(self):
        self.assertTrue(all(case.challenge for item in HOLDOUT_SCENARIOS for case in item.cases))

    def test_24_existing_calibrated_dataset_remains_unchanged(self):
        old = scenario_dataset_info()
        self.assertEqual((old['sample_count'], old['scenario_count']), (80, 4))


class HoldoutRealExecutionTests(unittest.TestCase):
    def setUp(self):
        reset_database_for_tests()
        self.client = TestClient(app)

    def run_holdout(self, use_ai: bool = False) -> dict:
        response = self.client.post('/api/evaluation/holdout/run', json={'use_ai': use_ai})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_25_health_reports_current_release(self):
        self.assertEqual(self.client.get('/health').json()['version'], APP_VERSION)

    def test_26_openapi_documents_new_endpoint(self):
        self.assertIn('/api/evaluation/holdout/run', self.client.get('/openapi.json').json()['paths'])

    def test_27_status_exposes_new_dataset_before_execution(self):
        self.assertEqual(self.client.get('/api/evaluation').json()['holdout_dataset']['sample_count'], 80)

    def test_28_status_has_no_premade_result(self):
        self.assertIsNone(self.client.get('/api/evaluation').json()['latest_holdout_result'])

    def test_29_execution_returns_eighty_real_predictions(self):
        result = self.run_holdout()
        self.assertEqual(result['sample_count'], len(result['predictions']))
        self.assertEqual(result['sample_count'], 80)

    def test_30_execution_returns_five_real_topics(self):
        result = self.run_holdout()
        self.assertEqual(result['scenario_count'], len(result['scenarios']))
        self.assertEqual(result['scenario_count'], 5)

    def test_31_every_original_text_and_label_is_preserved(self):
        result = self.run_holdout()
        expected = [(item.key, case.text, case.expected_label) for item in HOLDOUT_SCENARIOS for case in item.cases]
        actual = [(item['scenario_key'], item['text'], item['expected_label']) for item in result['predictions']]
        self.assertEqual(actual, expected)

    def test_32_accuracy_is_derived_from_actual_predictions(self):
        result = self.run_holdout()
        self.assertEqual(result['accuracy'], round(sum(item['correct'] for item in result['predictions']) / 80, 4))

    def test_33_correct_count_is_derived_from_actual_predictions(self):
        result = self.run_holdout()
        self.assertEqual(result['correct_count'], sum(item['correct'] for item in result['predictions']))

    def test_34_error_count_is_derived_from_actual_predictions(self):
        result = self.run_holdout()
        self.assertEqual(result['error_count'], sum(not item['correct'] for item in result['predictions']))

    def test_35_actual_errors_are_never_hidden(self):
        result = self.run_holdout()
        self.assertEqual(len(result['errors']), result['error_count'])
        self.assertTrue(all(item['expected_label'] != item['predicted_label'] for item in result['errors']))

    def test_36_heuristic_errors_are_not_artificially_corrected(self):
        result = self.run_holdout()
        self.assertGreater(result['error_count'], 0)
        self.assertLess(result['accuracy'], 1)

    def test_37_macro_f1_is_mean_of_actual_class_scores(self):
        result = self.run_holdout()
        self.assertEqual(result['macro_f1'], round(mean(row['f1'] for row in result['class_metrics']), 4))

    def test_38_class_supports_remain_twenty_each(self):
        self.assertEqual({row['support'] for row in self.run_holdout()['class_metrics']}, {20})

    def test_39_confusion_matrix_counts_all_predictions(self):
        result = self.run_holdout()
        total = sum(sum(row['predicted_counts'].values()) for row in result['confusion_matrix'])
        self.assertEqual(total, 80)

    def test_40_each_topic_score_uses_its_own_sixteen_cases(self):
        result = self.run_holdout()
        for scenario in result['scenarios']:
            actual = [item for item in result['predictions'] if item['scenario_key'] == scenario['key']]
            self.assertEqual(len(actual), 16)
            self.assertEqual(scenario['correct_count'], sum(item['correct'] for item in actual))

    def test_41_easy_and_challenging_scores_are_separate(self):
        self.assertEqual({row['key']: row['sample_count'] for row in self.run_holdout()['difficulty_metrics']}, {'temel': 40, 'zor': 40})

    def test_42_heuristic_execution_does_not_invent_transformer_usage(self):
        result = self.run_holdout()
        self.assertEqual(result['transformer_inference_count'], 0)
        self.assertEqual(result['structural_decision_count'], 80)

    def test_43_heuristic_execution_is_labeled_honestly(self):
        result = self.run_holdout()
        self.assertFalse(result['effective_ai'])
        self.assertEqual(result['engine_mode'], 'heuristic-fallback')

    def test_44_requested_ai_is_preserved(self):
        self.assertFalse(self.run_holdout(False)['requested_ai'])

    def test_45_result_contains_current_version(self):
        self.assertEqual(self.run_holdout()['version'], APP_VERSION)

    def test_46_each_execution_has_a_new_identity(self):
        self.assertNotEqual(self.run_holdout()['run_id'], self.run_holdout()['run_id'])

    def test_47_result_preserves_frozen_dataset_hash(self):
        self.assertEqual(self.run_holdout()['dataset']['frozen_sha256'], holdout_dataset_info()['frozen_sha256'])

    def test_48_result_explains_that_product_data_is_untouched(self):
        self.assertIn('bildirimleri', self.run_holdout()['isolation_note'])
        self.assertIn('kalibrasyon sonucunu değiştirmez', self.run_holdout()['isolation_note'])

    def test_49_overlap_is_rejected_before_any_result_is_saved(self):
        invalid = {**holdout_dataset_info(), 'is_disjoint_from_calibration': False}
        with patch('app.evaluation.holdout_dataset_info', return_value=invalid):
            response = self.client.post('/api/evaluation/holdout/run', json={'use_ai': False})
        self.assertEqual(response.status_code, 400)
        self.assertIn('çakışıyor', response.json()['detail'])

    def test_50_old_scenario_route_remains_available(self):
        response = self.client.post('/api/evaluation/scenarios/run', json={'use_ai': False})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['scenario_count'], 4)

    def test_51_reference_route_remains_twenty_cases(self):
        response = self.client.post('/api/evaluation/run', json={'use_ai': False, 'iterations': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['sample_count'], 20)


if __name__ == '__main__':
    unittest.main(verbosity=2)
