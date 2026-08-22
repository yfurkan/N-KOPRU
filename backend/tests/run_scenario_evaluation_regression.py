import os
import unittest
from collections import Counter
from statistics import mean
from unittest.mock import patch

os.environ.setdefault('N_KOPRU_DB_PATH', '/tmp/nkopru_v140_scenario_regression.db')

from fastapi.testclient import TestClient

from app.database import reset_database_for_tests
from app.evaluation import LABELS
from app.evaluation_scenarios import SCENARIOS, scenario_dataset_info
from app.main import app
from app.stance_engine import CANDIDATE_LABELS, GENERIC_LABEL_MAP, LABEL_MAP, candidate_labels_for_title


class ScenarioEvaluationRegressionTests(unittest.TestCase):
    def setUp(self):
        reset_database_for_tests()
        self.client = TestClient(app)

    def run_scenarios(self, use_ai=False):
        response = self.client.post('/api/evaluation/scenarios/run', json={'use_ai': use_ai})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_01_health_reports_version_140(self):
        self.assertEqual(self.client.get('/health').json()['version'], '1.4.0')

    def test_02_scenario_dataset_has_eighty_cases(self):
        self.assertEqual(scenario_dataset_info()['sample_count'], 80)

    def test_03_scenario_dataset_has_four_topics(self):
        self.assertEqual(scenario_dataset_info()['scenario_count'], 4)

    def test_04_scenario_dataset_has_four_stance_labels(self):
        self.assertEqual(scenario_dataset_info()['label_count'], 4)

    def test_05_scenario_dataset_is_globally_balanced(self):
        self.assertEqual(set(scenario_dataset_info()['label_distribution'].values()), {20})

    def test_06_each_topic_has_twenty_cases(self):
        self.assertTrue(all(len(scenario.cases) == 20 for scenario in SCENARIOS))

    def test_07_each_topic_is_balanced_across_four_classes(self):
        for scenario in SCENARIOS:
            self.assertEqual(set(Counter(item.expected_label for item in scenario.cases).values()), {5})

    def test_08_scenario_topics_have_distinct_keys(self):
        self.assertEqual(len({item.key for item in SCENARIOS}), 4)

    def test_09_scenario_titles_are_distinct(self):
        self.assertEqual(len({item.title for item in SCENARIOS}), 4)

    def test_10_scenario_texts_are_unique(self):
        texts = [case.text for scenario in SCENARIOS for case in scenario.cases]
        self.assertEqual(len(texts), len(set(texts)))

    def test_11_scenario_dataset_does_not_claim_external_status(self):
        self.assertFalse(scenario_dataset_info()['is_external_benchmark'])

    def test_12_scenario_dataset_excludes_user_content(self):
        self.assertFalse(scenario_dataset_info()['contains_user_content'])

    def test_13_scenario_dataset_discloses_limitations(self):
        limitation = scenario_dataset_info()['limitation']
        self.assertIn('proje ekibince', limitation)
        self.assertIn('Bağımsız dış veri seti', limitation)

    def test_14_scenario_dataset_contains_easy_and_difficult_cases(self):
        self.assertEqual(scenario_dataset_info()['difficulty_distribution'], {'temel': 32, 'zor': 48})

    def test_15_every_case_documents_its_challenge(self):
        self.assertTrue(all(case.challenge for scenario in SCENARIOS for case in scenario.cases))

    def test_16_standard_reference_dataset_remains_twenty_cases(self):
        status = self.client.get('/api/evaluation').json()
        self.assertEqual(status['dataset']['sample_count'], 20)
        self.assertEqual(status['scenario_dataset']['sample_count'], 80)

    def test_17_scenario_result_is_empty_before_first_run(self):
        self.assertIsNone(self.client.get('/api/evaluation').json()['latest_scenario_result'])

    def test_18_run_produces_eighty_real_predictions(self):
        result = self.run_scenarios()
        self.assertEqual(result['sample_count'], 80)
        self.assertEqual(len(result['predictions']), 80)

    def test_19_run_preserves_every_authored_case(self):
        result = self.run_scenarios()
        expected = [(scenario.key, case.text, case.expected_label) for scenario in SCENARIOS for case in scenario.cases]
        actual = [(item['scenario_key'], item['text'], item['expected_label']) for item in result['predictions']]
        self.assertEqual(actual, expected)

    def test_20_accuracy_is_calculated_from_actual_predictions(self):
        result = self.run_scenarios()
        accuracy = sum(item['correct'] for item in result['predictions']) / 80
        self.assertEqual(result['accuracy'], round(accuracy, 4))

    def test_21_correct_count_is_calculated(self):
        result = self.run_scenarios()
        self.assertEqual(result['correct_count'], sum(item['correct'] for item in result['predictions']))

    def test_22_error_count_is_calculated(self):
        result = self.run_scenarios()
        self.assertEqual(result['error_count'], sum(not item['correct'] for item in result['predictions']))

    def test_23_errors_are_not_hidden(self):
        result = self.run_scenarios()
        self.assertGreater(result['error_count'], 0)
        self.assertEqual(len(result['errors']), result['error_count'])
        self.assertTrue(all(not item['correct'] for item in result['errors']))

    def test_24_macro_f1_is_mean_of_real_class_f1(self):
        result = self.run_scenarios()
        self.assertEqual(result['macro_f1'], round(mean(row['f1'] for row in result['class_metrics']), 4))

    def test_25_all_class_metrics_have_twenty_labels(self):
        result = self.run_scenarios()
        self.assertEqual({row['label'] for row in result['class_metrics']}, set(LABELS))
        self.assertTrue(all(row['support'] == 20 for row in result['class_metrics']))

    def test_26_confusion_matrix_counts_every_real_prediction(self):
        result = self.run_scenarios()
        self.assertEqual(sum(sum(row['predicted_counts'].values()) for row in result['confusion_matrix']), 80)

    def test_27_extra_fallback_label_is_not_hidden_from_matrix(self):
        result = self.run_scenarios()
        self.assertTrue(any('Diğer / Nötr' in row['predicted_counts'] for row in result['confusion_matrix']))

    def test_28_each_topic_has_its_own_real_result(self):
        result = self.run_scenarios()
        self.assertEqual(len(result['scenarios']), 4)
        self.assertTrue(all(row['sample_count'] == 20 for row in result['scenarios']))

    def test_29_each_topic_accuracy_is_calculated(self):
        for row in self.run_scenarios()['scenarios']:
            self.assertEqual(row['accuracy'], round(row['correct_count'] / row['sample_count'], 4))

    def test_30_topic_errors_match_own_predictions(self):
        for row in self.run_scenarios()['scenarios']:
            self.assertEqual(row['error_count'], len(row['errors']))
            self.assertTrue(all(item['scenario_key'] == row['key'] for item in row['errors']))

    def test_31_difficulty_metrics_cover_every_prediction(self):
        result = self.run_scenarios()
        self.assertEqual(sum(item['sample_count'] for item in result['difficulty_metrics']), 80)
        self.assertEqual({item['key'] for item in result['difficulty_metrics']}, {'temel', 'zor'})

    def test_32_each_difficulty_score_is_real(self):
        for row in self.run_scenarios()['difficulty_metrics']:
            self.assertEqual(row['accuracy'], round(row['correct_count'] / row['sample_count'], 4))

    def test_33_heuristic_run_reports_no_model_inference(self):
        result = self.run_scenarios(use_ai=False)
        self.assertEqual(result['transformer_inference_count'], 0)
        self.assertEqual(result['structural_decision_count'], 80)
        self.assertFalse(result['effective_ai'])

    def test_34_unloaded_model_is_not_automatically_loaded(self):
        with patch('app.stance_engine.load_model') as load:
            result = self.run_scenarios(use_ai=True)
        load.assert_not_called()
        self.assertFalse(result['effective_ai'])
        self.assertIn('otomatik', result['engine_note'])

    def test_35_loaded_model_uses_actual_hybrid_path(self):
        def fake_model(sequences, candidate_labels, **kwargs):
            return [{'labels': [candidate_labels[0]], 'scores': [0.92]} for _ in sequences]

        with patch('app.stance_engine._PIPELINE', fake_model), patch(
            'app.stance_engine.dependencies_installed', return_value=True
        ):
            result = self.run_scenarios(use_ai=True)

        self.assertTrue(result['effective_ai'])
        self.assertGreater(result['transformer_inference_count'], 0)
        self.assertEqual(result['engine_mode'], 'hybrid-transformer')

    def test_36_model_confidence_is_only_reported_for_real_inference(self):
        def fake_model(sequences, candidate_labels, **kwargs):
            return [{'labels': [candidate_labels[0]], 'scores': [0.93]} for _ in sequences]

        with patch('app.stance_engine._PIPELINE', fake_model), patch(
            'app.stance_engine.dependencies_installed', return_value=True
        ):
            result = self.run_scenarios(use_ai=True)

        actual = sum(row['model_confidence'] is not None for row in result['predictions'])
        self.assertEqual(actual, result['transformer_inference_count'])
        self.assertTrue(all(row['model_confidence'] == 0.93 for row in result['predictions'] if row['model_confidence'] is not None))

    def test_37_structural_and_model_counts_sum_to_eighty(self):
        result = self.run_scenarios()
        self.assertEqual(result['structural_decision_count'] + result['transformer_inference_count'], 80)

    def test_38_each_topic_has_elapsed_measurement(self):
        self.assertTrue(all(row['elapsed_ms'] > 0 for row in self.run_scenarios()['scenarios']))

    def test_39_overall_elapsed_measurement_is_real(self):
        self.assertGreater(self.run_scenarios()['elapsed_ms'], 0)

    def test_40_error_records_keep_difficulty_and_challenge(self):
        for row in self.run_scenarios()['errors']:
            self.assertIn(row['difficulty'], {'temel', 'zor'})
            self.assertTrue(row['challenge'])

    def test_41_result_reports_project_scope_honestly(self):
        self.assertIn('Bağımsız dış veri seti', self.run_scenarios()['dataset']['limitation'])

    def test_42_result_reports_isolated_behavior(self):
        result = self.run_scenarios()
        self.assertIn('bildirimleri', result['isolation_note'])
        self.assertIn('referans ölçümünü', result['isolation_note'])

    def test_43_every_run_has_new_identity(self):
        self.assertNotEqual(self.run_scenarios()['run_id'], self.run_scenarios()['run_id'])

    def test_44_result_version_is_current(self):
        self.assertEqual(self.run_scenarios()['version'], '1.4.0')

    def test_45_ai_topic_retains_original_candidate_labels(self):
        self.assertEqual(candidate_labels_for_title('Üniversitede yapay zekâ'), LABEL_MAP)
        self.assertEqual(list(candidate_labels_for_title('Üniversitede yapay zekâ')), CANDIDATE_LABELS)

    def test_46_other_topics_receive_subject_neutral_labels(self):
        labels = candidate_labels_for_title('Okullarda telefon kullanımı')
        self.assertEqual(labels, GENERIC_LABEL_MAP)
        self.assertTrue(all('yapay zekâ' not in label for label in labels))

    def test_47_subject_neutral_labels_preserve_four_product_classes(self):
        self.assertEqual(set(GENERIC_LABEL_MAP.values()), set(LABELS))

    def test_48_model_receives_subject_appropriate_labels(self):
        seen = []

        def fake_model(sequences, candidate_labels, **kwargs):
            seen.append(candidate_labels)
            return [{'labels': [candidate_labels[0]], 'scores': [0.9]} for _ in sequences]

        with patch('app.stance_engine._PIPELINE', fake_model), patch(
            'app.stance_engine.dependencies_installed', return_value=True
        ):
            self.run_scenarios(use_ai=True)

        self.assertEqual(seen[0], CANDIDATE_LABELS)
        self.assertTrue(all(labels == list(GENERIC_LABEL_MAP) for labels in seen[1:]))


if __name__ == '__main__':
    unittest.main(verbosity=2)
