import os
import unittest
from statistics import mean
from unittest.mock import patch

os.environ.setdefault('N_KOPRU_DB_PATH', '/tmp/nkopru_v131_evaluation_regression.db')

from fastapi.testclient import TestClient

from app.database import connection, reset_database_for_tests
from app.evaluation import LABELED_CASES, LABELS, RESULT_META_KEY, _percentile
from app.main import app


class TechnicalEvaluationRegressionTests(unittest.TestCase):
    def setUp(self):
        reset_database_for_tests()
        self.client = TestClient(app)

    def measure(self, iterations=2, use_ai=False):
        response = self.client.post('/api/evaluation/run', json={
            'iterations': iterations,
            'use_ai': use_ai,
        })
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_01_health_reports_new_version(self):
        self.assertEqual(self.client.get('/health').json()['version'], '1.4.0')

    def test_02_status_exists_before_first_run(self):
        data = self.client.get('/api/evaluation').json()
        self.assertEqual(data['version'], '1.4.0')
        self.assertIsNone(data['latest_result'])

    def test_03_dataset_scope_is_honest(self):
        dataset = self.client.get('/api/evaluation').json()['dataset']
        self.assertEqual(dataset['sample_count'], 20)
        self.assertEqual(dataset['label_count'], 4)
        self.assertFalse(dataset['is_external_benchmark'])
        self.assertIn('Bağımsız veri seti', dataset['limitation'])

    def test_04_dataset_is_balanced(self):
        dataset = self.client.get('/api/evaluation').json()['dataset']
        self.assertEqual(set(dataset['label_distribution'].values()), {5})
        self.assertEqual(set(dataset['label_distribution']), set(LABELS))

    def test_05_run_returns_twenty_real_predictions(self):
        data = self.measure()
        self.assertEqual(data['sample_count'], len(LABELED_CASES))
        self.assertEqual(len(data['predictions']), len(LABELED_CASES))

    def test_06_predictions_retain_expected_texts_and_labels(self):
        data = self.measure()
        self.assertEqual(
            [(item['text'], item['expected_label']) for item in data['predictions']],
            list(LABELED_CASES),
        )

    def test_07_accuracy_is_calculated_from_predictions(self):
        data = self.measure()
        actual = sum(item['correct'] for item in data['predictions']) / len(data['predictions'])
        self.assertEqual(data['accuracy'], round(actual, 4))

    def test_08_correct_count_is_calculated(self):
        data = self.measure()
        self.assertEqual(data['correct_count'], sum(item['correct'] for item in data['predictions']))

    def test_09_macro_f1_is_calculated_from_class_f1(self):
        data = self.measure()
        expected = round(mean(item['f1'] for item in data['class_metrics']), 4)
        self.assertEqual(data['macro_f1'], expected)

    def test_10_each_class_has_metrics(self):
        data = self.measure()
        self.assertEqual({item['label'] for item in data['class_metrics']}, set(LABELS))
        self.assertTrue(all(item['support'] == 5 for item in data['class_metrics']))

    def test_11_confusion_matrix_counts_real_predictions(self):
        data = self.measure()
        for row in data['confusion_matrix']:
            self.assertEqual(sum(row['predicted_counts'].values()), 5)

    def test_12_latency_contains_requested_real_runs(self):
        data = self.measure(iterations=3)
        self.assertEqual(data['latency']['iterations'], 3)
        self.assertEqual(len(data['latency']['samples_ms']), 3)
        self.assertTrue(all(value > 0 for value in data['latency']['samples_ms']))

    def test_13_latency_percentiles_are_ordered(self):
        latency = self.measure(iterations=4)['latency']
        self.assertLessEqual(latency['minimum_ms'], latency['median_ms'])
        self.assertLessEqual(latency['median_ms'], latency['p95_ms'])
        self.assertLessEqual(latency['p95_ms'], latency['maximum_ms'])

    def test_14_percentile_interpolates_instead_of_inventing_sample(self):
        self.assertEqual(_percentile([10.0, 20.0, 30.0], 0.95), 29.0)

    def test_15_demo_has_eighty_raw_twenty_unique_comments(self):
        latency = self.measure()['latency']
        self.assertEqual(latency['raw_comment_count'], 80)
        self.assertEqual(latency['unique_comment_count'], 20)

    def test_16_all_product_invariants_are_measured(self):
        data = self.measure()
        self.assertEqual(data['invariant_count'], 9)
        self.assertEqual(data['passed_invariant_count'], sum(item['passed'] for item in data['invariants']))

    def test_17_source_awareness_is_checked(self):
        source = next(item for item in self.measure()['invariants'] if item['key'] == 'source_awareness')
        self.assertEqual(source['actual'], '%25')
        self.assertTrue(source['passed'])

    def test_18_bridge_limit_is_checked(self):
        bridge = next(item for item in self.measure()['invariants'] if item['key'] == 'bridge_length')
        self.assertLessEqual(int(bridge['actual']), 28)
        self.assertTrue(bridge['passed'])

    def test_19_semantic_guardrails_are_checked(self):
        rows = {item['key']: item for item in self.measure()['invariants']}
        self.assertTrue(rows['bounded_use_guardrail']['passed'])
        self.assertTrue(rows['evidence_guardrail']['passed'])

    def test_20_heuristic_run_does_not_fabricate_model_confidence(self):
        data = self.measure(use_ai=False)
        self.assertFalse(data['effective_ai'])
        self.assertEqual(data['transformer_inference_count'], 0)
        self.assertTrue(all(item['model_confidence'] is None for item in data['predictions']))

    def test_21_unavailable_model_is_not_automatically_loaded(self):
        with patch('app.stance_engine.load_model') as load_model:
            data = self.measure(use_ai=True)
        load_model.assert_not_called()
        self.assertFalse(data['effective_ai'])
        self.assertIn('otomatik', data['engine_note'])

    def test_22_run_contains_honest_isolation_note(self):
        data = self.measure()
        self.assertIn('analiz geçmişini', data['isolation_note'])
        self.assertIn('bildirimleri', data['isolation_note'])

    def test_23_latest_result_is_persisted(self):
        first = self.measure()
        status = self.client.get('/api/evaluation').json()
        self.assertEqual(status['latest_result']['run_id'], first['run_id'])

    def test_24_result_is_saved_in_existing_sqlite_meta_table(self):
        self.measure()
        with connection() as conn:
            row = conn.execute('SELECT value FROM app_meta WHERE key = ?', (RESULT_META_KEY,)).fetchone()
        self.assertIsNotNone(row)

    def test_25_iteration_bounds_are_enforced(self):
        for value in (0, 11, -1):
            response = self.client.post('/api/evaluation/run', json={'iterations': value, 'use_ai': False})
            self.assertEqual(response.status_code, 422)

    def test_26_every_run_gets_a_new_measured_identity(self):
        first = self.measure(iterations=1)
        second = self.measure(iterations=1)
        self.assertNotEqual(first['run_id'], second['run_id'])

    def test_27_stored_invalid_payload_is_handled_safely(self):
        with connection() as conn:
            conn.execute('INSERT INTO app_meta(key, value) VALUES(?, ?)', (RESULT_META_KEY, 'bozuk'))
        self.assertIsNone(self.client.get('/api/evaluation').json()['latest_result'])

    def test_28_hybrid_accounting_matches_prediction_count(self):
        data = self.measure()
        self.assertEqual(
            data['structural_decision_count'] + data['transformer_inference_count'],
            data['sample_count'],
        )

    def test_29_ready_model_uses_real_hybrid_decision_path(self):
        def simulated_model(sequences, candidate_labels, **kwargs):
            rows = sequences if isinstance(sequences, list) else [sequences]
            return [{'labels': [candidate_labels[0]], 'scores': [0.91]} for _ in rows]

        with patch('app.stance_engine._PIPELINE', simulated_model), patch(
            'app.stance_engine.dependencies_installed', return_value=True
        ):
            data = self.measure(use_ai=True)

        self.assertTrue(data['effective_ai'])
        self.assertEqual(data['engine_mode'], 'hybrid-transformer')
        self.assertEqual(data['correct_count'], 20)

    def test_30_ready_model_without_inference_is_reported_honestly(self):
        with patch('app.stance_engine._PIPELINE', lambda *args, **kwargs: []), patch(
            'app.stance_engine.dependencies_installed', return_value=True
        ):
            data = self.measure(use_ai=True)

        self.assertEqual(data['transformer_inference_count'], 0)
        self.assertEqual(data['structural_decision_count'], 20)
        self.assertIn('Transformer çıkarımı yapılmadı', data['engine_note'])

    def test_31_fallback_score_is_not_rounded_up_or_replaced(self):
        data = self.measure(use_ai=False)
        self.assertLess(data['correct_count'], data['sample_count'])
        self.assertEqual(data['accuracy'], data['correct_count'] / data['sample_count'])

    def test_32_wrong_predictions_remain_visible(self):
        data = self.measure(use_ai=False)
        mistakes = [item for item in data['predictions'] if not item['correct']]
        self.assertTrue(mistakes)
        self.assertTrue(all(item['expected_label'] != item['predicted_label'] for item in mistakes))

if __name__ == '__main__':
    unittest.main(verbosity=2)
