import json
import os
import unittest

os.environ.setdefault('N_KOPRU_DB_PATH', '/tmp/nkopru_v140_scenario_persistence.db')

from fastapi.testclient import TestClient

from app.database import connection, reset_database_for_tests
from app.evaluation import RESULT_META_KEY, SCENARIO_RESULT_META_KEY
from app.main import app


class ScenarioEvaluationPersistenceTests(unittest.TestCase):
    def setUp(self):
        reset_database_for_tests()
        self.client = TestClient(app)

    def run_scenarios(self):
        response = self.client.post('/api/evaluation/scenarios/run', json={'use_ai': False})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def run_reference(self):
        response = self.client.post('/api/evaluation/run', json={'iterations': 1, 'use_ai': False})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def table_counts(self):
        with connection() as conn:
            return {
                table: conn.execute(f'SELECT COUNT(*) AS c FROM {table}').fetchone()['c']
                for table in (
                    'notifications', 'messages', 'conversations', 'bookmarks',
                    'topic_lists', 'topic_list_entries', 'analysis_history',
                    'custom_posts', 'profiles',
                )
            }

    def test_01_scenario_result_is_saved_in_existing_meta_table(self):
        result = self.run_scenarios()
        with connection() as conn:
            saved = conn.execute('SELECT value FROM app_meta WHERE key = ?', (SCENARIO_RESULT_META_KEY,)).fetchone()
        self.assertEqual(json.loads(saved['value'])['run_id'], result['run_id'])

    def test_02_status_restores_saved_scenario_result(self):
        result = self.run_scenarios()
        self.assertEqual(self.client.get('/api/evaluation').json()['latest_scenario_result']['run_id'], result['run_id'])

    def test_03_another_client_reads_same_result(self):
        result = self.run_scenarios()
        self.assertEqual(TestClient(app).get('/api/evaluation').json()['latest_scenario_result']['run_id'], result['run_id'])

    def test_04_only_one_latest_scenario_result_is_kept(self):
        self.run_scenarios()
        second = self.run_scenarios()
        with connection() as conn:
            count = conn.execute('SELECT COUNT(*) AS c FROM app_meta WHERE key = ?', (SCENARIO_RESULT_META_KEY,)).fetchone()['c']
        self.assertEqual(count, 1)
        self.assertEqual(self.client.get('/api/evaluation').json()['latest_scenario_result']['run_id'], second['run_id'])

    def test_05_scenario_run_preserves_previous_reference_result(self):
        reference = self.run_reference()
        self.run_scenarios()
        self.assertEqual(self.client.get('/api/evaluation').json()['latest_result']['run_id'], reference['run_id'])

    def test_06_reference_run_preserves_previous_scenario_result(self):
        scenarios = self.run_scenarios()
        self.run_reference()
        self.assertEqual(self.client.get('/api/evaluation').json()['latest_scenario_result']['run_id'], scenarios['run_id'])

    def test_07_scenario_run_does_not_create_reference_result(self):
        self.run_scenarios()
        self.assertIsNone(self.client.get('/api/evaluation').json()['latest_result'])

    def test_08_reference_run_does_not_create_scenario_result(self):
        self.run_reference()
        self.assertIsNone(self.client.get('/api/evaluation').json()['latest_scenario_result'])

    def test_09_result_meta_keys_are_distinct(self):
        self.assertNotEqual(RESULT_META_KEY, SCENARIO_RESULT_META_KEY)

    def test_10_scenario_run_does_not_modify_product_tables(self):
        before = self.table_counts()
        self.run_scenarios()
        self.assertEqual(self.table_counts(), before)

    def test_11_scenario_run_does_not_create_history_snapshot(self):
        before = self.table_counts()['analysis_history']
        self.run_scenarios()
        self.assertEqual(self.table_counts()['analysis_history'], before)

    def test_12_scenario_run_does_not_create_notifications(self):
        before = self.table_counts()['notifications']
        self.run_scenarios()
        self.assertEqual(self.table_counts()['notifications'], before)

    def test_13_scenario_run_does_not_create_custom_posts(self):
        before = self.table_counts()['custom_posts']
        self.run_scenarios()
        self.assertEqual(self.table_counts()['custom_posts'], before)

    def test_14_status_reads_do_not_create_scenario_result(self):
        self.client.get('/api/evaluation')
        with connection() as conn:
            row = conn.execute('SELECT value FROM app_meta WHERE key = ?', (SCENARIO_RESULT_META_KEY,)).fetchone()
        self.assertIsNone(row)

    def test_15_status_reads_do_not_rewrite_scenario_payload(self):
        self.run_scenarios()
        with connection() as conn:
            before = conn.execute('SELECT value FROM app_meta WHERE key = ?', (SCENARIO_RESULT_META_KEY,)).fetchone()['value']
        self.client.get('/api/evaluation')
        with connection() as conn:
            after = conn.execute('SELECT value FROM app_meta WHERE key = ?', (SCENARIO_RESULT_META_KEY,)).fetchone()['value']
        self.assertEqual(after, before)

    def test_16_corrupt_scenario_payload_is_handled_safely(self):
        with connection() as conn:
            conn.execute('INSERT INTO app_meta(key, value) VALUES(?, ?)', (SCENARIO_RESULT_META_KEY, 'bozuk'))
        self.assertIsNone(self.client.get('/api/evaluation').json()['latest_scenario_result'])

    def test_17_scalar_scenario_payload_is_ignored(self):
        with connection() as conn:
            conn.execute('INSERT INTO app_meta(key, value) VALUES(?, ?)', (SCENARIO_RESULT_META_KEY, '12'))
        self.assertIsNone(self.client.get('/api/evaluation').json()['latest_scenario_result'])

    def test_18_corrupt_scenario_payload_does_not_hide_reference(self):
        result = self.run_reference()
        with connection() as conn:
            conn.execute('INSERT INTO app_meta(key, value) VALUES(?, ?)', (SCENARIO_RESULT_META_KEY, 'bozuk'))
        self.assertEqual(self.client.get('/api/evaluation').json()['latest_result']['run_id'], result['run_id'])

    def test_19_persisted_errors_retain_expected_and_actual_labels(self):
        self.run_scenarios()
        result = self.client.get('/api/evaluation').json()['latest_scenario_result']
        self.assertTrue(all(item['expected_label'] != item['predicted_label'] for item in result['errors']))

    def test_20_persisted_dataset_retains_honest_scope(self):
        self.run_scenarios()
        result = self.client.get('/api/evaluation').json()['latest_scenario_result']
        self.assertFalse(result['dataset']['is_external_benchmark'])
        self.assertFalse(result['dataset']['contains_user_content'])

    def test_21_saved_results_have_independent_identities(self):
        reference = self.run_reference()
        scenarios = self.run_scenarios()
        self.assertNotEqual(reference['run_id'], scenarios['run_id'])

    def test_22_user_comment_is_not_added_to_authored_dataset(self):
        self.client.post('/api/posts/1/comments', json={'text': 'Yeni kullanıcı yorumu gerçek içeriktir.', 'use_ai': False})
        result = self.run_scenarios()
        self.assertEqual(result['sample_count'], 80)
        self.assertTrue(all('Yeni kullanıcı yorumu' not in item['text'] for item in result['predictions']))

    def test_23_scenario_run_preserves_persisted_user_comments(self):
        self.client.post('/api/posts/1/comments', json={'text': 'Kalıcı yorum korunmalıdır.', 'use_ai': False})
        before = self.client.get('/api/posts/demo').json()['comments']
        self.run_scenarios()
        self.assertEqual(self.client.get('/api/posts/demo').json()['comments'], before)

    def test_24_scenario_and_reference_counts_remain_separate(self):
        self.run_reference()
        self.run_scenarios()
        status = self.client.get('/api/evaluation').json()
        self.assertEqual(status['latest_result']['sample_count'], 20)
        self.assertEqual(status['latest_scenario_result']['sample_count'], 80)


if __name__ == '__main__':
    unittest.main(verbosity=2)
