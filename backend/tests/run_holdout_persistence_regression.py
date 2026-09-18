"""v1.5.0 ayrı kontrol sonucunun SQLite izolasyonu ve kalıcılığı."""
from __future__ import annotations

import json
import os
import unittest

os.environ.setdefault('N_KOPRU_DB_PATH', '/tmp/nkopru_v142_holdout_persistence.db')

from fastapi.testclient import TestClient

from app.database import connection, reset_database_for_tests
from app.evaluation import HOLDOUT_RESULT_META_KEY, RESULT_META_KEY, SCENARIO_RESULT_META_KEY
from app.evaluation_holdout import holdout_dataset_info
from app.main import app


class HoldoutPersistenceRegressionTests(unittest.TestCase):
    def setUp(self):
        reset_database_for_tests()
        self.client = TestClient(app)

    def run_holdout(self):
        response = self.client.post('/api/evaluation/holdout/run', json={'use_ai': False})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def run_scenarios(self):
        response = self.client.post('/api/evaluation/scenarios/run', json={'use_ai': False})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def run_reference(self):
        response = self.client.post('/api/evaluation/run', json={'iterations': 1, 'use_ai': False})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def counts(self):
        with connection() as conn:
            return {
                table: conn.execute(f'SELECT COUNT(*) AS amount FROM {table}').fetchone()['amount']
                for table in (
                    'notifications', 'conversations', 'messages', 'bookmarks',
                    'topic_lists', 'topic_list_entries', 'custom_posts',
                    'analysis_history', 'profiles',
                )
            }

    def test_01_all_three_sqlite_metadata_keys_are_distinct(self):
        self.assertEqual(len({RESULT_META_KEY, SCENARIO_RESULT_META_KEY, HOLDOUT_RESULT_META_KEY}), 3)

    def test_02_holdout_uses_existing_app_meta_table(self):
        result = self.run_holdout()
        with connection() as conn:
            row = conn.execute('SELECT value FROM app_meta WHERE key = ?', (HOLDOUT_RESULT_META_KEY,)).fetchone()
        self.assertEqual(json.loads(row['value'])['run_id'], result['run_id'])

    def test_03_status_restores_saved_holdout_result(self):
        result = self.run_holdout()
        self.assertEqual(self.client.get('/api/evaluation').json()['latest_holdout_result']['run_id'], result['run_id'])

    def test_04_new_client_reads_same_saved_result(self):
        result = self.run_holdout()
        self.assertEqual(TestClient(app).get('/api/evaluation').json()['latest_holdout_result']['run_id'], result['run_id'])

    def test_05_only_latest_holdout_result_is_saved(self):
        self.run_holdout()
        second = self.run_holdout()
        with connection() as conn:
            count = conn.execute('SELECT COUNT(*) AS amount FROM app_meta WHERE key = ?', (HOLDOUT_RESULT_META_KEY,)).fetchone()['amount']
        self.assertEqual(count, 1)
        self.assertEqual(self.client.get('/api/evaluation').json()['latest_holdout_result']['run_id'], second['run_id'])

    def test_06_holdout_does_not_create_reference_result(self):
        self.run_holdout()
        self.assertIsNone(self.client.get('/api/evaluation').json()['latest_result'])

    def test_07_holdout_does_not_create_old_scenario_result(self):
        self.run_holdout()
        self.assertIsNone(self.client.get('/api/evaluation').json()['latest_scenario_result'])

    def test_08_old_scenario_run_does_not_create_holdout_result(self):
        self.run_scenarios()
        self.assertIsNone(self.client.get('/api/evaluation').json()['latest_holdout_result'])

    def test_09_reference_run_does_not_create_holdout_result(self):
        self.run_reference()
        self.assertIsNone(self.client.get('/api/evaluation').json()['latest_holdout_result'])

    def test_10_holdout_preserves_reference_result(self):
        reference = self.run_reference()
        self.run_holdout()
        self.assertEqual(self.client.get('/api/evaluation').json()['latest_result']['run_id'], reference['run_id'])

    def test_11_holdout_preserves_old_calibration_result(self):
        scenarios = self.run_scenarios()
        self.run_holdout()
        self.assertEqual(self.client.get('/api/evaluation').json()['latest_scenario_result']['run_id'], scenarios['run_id'])

    def test_12_reference_preserves_holdout_result(self):
        result = self.run_holdout()
        self.run_reference()
        self.assertEqual(self.client.get('/api/evaluation').json()['latest_holdout_result']['run_id'], result['run_id'])

    def test_13_old_scenario_run_preserves_holdout_result(self):
        result = self.run_holdout()
        self.run_scenarios()
        self.assertEqual(self.client.get('/api/evaluation').json()['latest_holdout_result']['run_id'], result['run_id'])

    def test_14_all_three_result_ids_remain_independent(self):
        reference = self.run_reference()
        old = self.run_scenarios()
        new = self.run_holdout()
        self.assertEqual(len({reference['run_id'], old['run_id'], new['run_id']}), 3)

    def test_15_all_three_result_counts_remain_separate(self):
        self.run_reference()
        self.run_scenarios()
        self.run_holdout()
        data = self.client.get('/api/evaluation').json()
        self.assertEqual(data['latest_result']['sample_count'], 20)
        self.assertEqual(data['latest_scenario_result']['scenario_count'], 4)
        self.assertEqual(data['latest_holdout_result']['scenario_count'], 5)

    def test_16_holdout_does_not_change_any_product_table(self):
        before = self.counts()
        self.run_holdout()
        self.assertEqual(self.counts(), before)

    def test_17_holdout_does_not_add_history_snapshot(self):
        before = self.counts()['analysis_history']
        self.run_holdout()
        self.assertEqual(self.counts()['analysis_history'], before)

    def test_18_holdout_does_not_add_notifications(self):
        before = self.counts()['notifications']
        self.run_holdout()
        self.assertEqual(self.counts()['notifications'], before)

    def test_19_holdout_does_not_add_messages(self):
        before = self.counts()['messages']
        self.run_holdout()
        self.assertEqual(self.counts()['messages'], before)

    def test_20_holdout_does_not_add_bookmarks(self):
        before = self.counts()['bookmarks']
        self.run_holdout()
        self.assertEqual(self.counts()['bookmarks'], before)

    def test_21_holdout_does_not_add_custom_discussions(self):
        before = self.counts()['custom_posts']
        self.run_holdout()
        self.assertEqual(self.counts()['custom_posts'], before)

    def test_22_read_only_status_does_not_create_holdout_payload(self):
        self.client.get('/api/evaluation')
        with connection() as conn:
            row = conn.execute('SELECT value FROM app_meta WHERE key = ?', (HOLDOUT_RESULT_META_KEY,)).fetchone()
        self.assertIsNone(row)

    def test_23_read_only_status_does_not_rewrite_saved_payload(self):
        self.run_holdout()
        with connection() as conn:
            original = conn.execute('SELECT value FROM app_meta WHERE key = ?', (HOLDOUT_RESULT_META_KEY,)).fetchone()['value']
        self.client.get('/api/evaluation')
        with connection() as conn:
            current = conn.execute('SELECT value FROM app_meta WHERE key = ?', (HOLDOUT_RESULT_META_KEY,)).fetchone()['value']
        self.assertEqual(current, original)

    def test_24_invalid_saved_json_is_ignored_safely(self):
        with connection() as conn:
            conn.execute('INSERT INTO app_meta(key, value) VALUES(?, ?)', (HOLDOUT_RESULT_META_KEY, 'geçersiz'))
        self.assertIsNone(self.client.get('/api/evaluation').json()['latest_holdout_result'])

    def test_25_scalar_saved_json_is_ignored_safely(self):
        with connection() as conn:
            conn.execute('INSERT INTO app_meta(key, value) VALUES(?, ?)', (HOLDOUT_RESULT_META_KEY, '42'))
        self.assertIsNone(self.client.get('/api/evaluation').json()['latest_holdout_result'])

    def test_26_corrupt_holdout_does_not_hide_reference(self):
        result = self.run_reference()
        with connection() as conn:
            conn.execute('INSERT INTO app_meta(key, value) VALUES(?, ?)', (HOLDOUT_RESULT_META_KEY, 'bozuk'))
        self.assertEqual(self.client.get('/api/evaluation').json()['latest_result']['run_id'], result['run_id'])

    def test_27_corrupt_holdout_does_not_hide_old_scenario(self):
        result = self.run_scenarios()
        with connection() as conn:
            conn.execute('INSERT INTO app_meta(key, value) VALUES(?, ?)', (HOLDOUT_RESULT_META_KEY, 'bozuk'))
        self.assertEqual(self.client.get('/api/evaluation').json()['latest_scenario_result']['run_id'], result['run_id'])

    def test_28_corrupt_old_scenario_does_not_hide_holdout(self):
        result = self.run_holdout()
        with connection() as conn:
            conn.execute('INSERT INTO app_meta(key, value) VALUES(?, ?)', (SCENARIO_RESULT_META_KEY, 'bozuk'))
        self.assertEqual(self.client.get('/api/evaluation').json()['latest_holdout_result']['run_id'], result['run_id'])

    def test_29_saved_fingerprint_matches_current_frozen_content(self):
        self.run_holdout()
        saved = self.client.get('/api/evaluation').json()['latest_holdout_result']
        self.assertEqual(saved['dataset']['frozen_sha256'], holdout_dataset_info()['frozen_sha256'])

    def test_30_saved_errors_preserve_expected_and_actual_labels(self):
        self.run_holdout()
        saved = self.client.get('/api/evaluation').json()['latest_holdout_result']
        self.assertTrue(all(item['expected_label'] != item['predicted_label'] for item in saved['errors']))

    def test_31_saved_overlap_metadata_remains_zero(self):
        self.run_holdout()
        dataset = self.client.get('/api/evaluation').json()['latest_holdout_result']['dataset']
        self.assertEqual(dataset['calibration_sample_overlap_count'], 0)
        self.assertEqual(dataset['calibration_topic_overlap_count'], 0)

    def test_32_saved_dataset_does_not_claim_external_validation(self):
        self.run_holdout()
        self.assertFalse(self.client.get('/api/evaluation').json()['latest_holdout_result']['dataset']['is_external_benchmark'])

    def test_33_live_user_comments_do_not_enter_holdout_cases(self):
        response = self.client.post('/api/posts/1/comments', json={'text': 'Bu gerçek kullanıcı yorumu ayrı sete girmemeli.', 'use_ai': False})
        self.assertEqual(response.status_code, 200, response.text)
        result = self.run_holdout()
        self.assertTrue(all('gerçek kullanıcı yorumu ayrı sete' not in row['text'] for row in result['predictions']))

    def test_34_holdout_preserves_persisted_user_comments(self):
        self.client.post('/api/posts/1/comments', json={'text': 'Kalıcı kullanıcı yorumu aynen korunmalı.', 'use_ai': False})
        before = self.client.get('/api/posts/demo').json()['comments']
        self.run_holdout()
        self.assertEqual(self.client.get('/api/posts/demo').json()['comments'], before)

    def test_35_deleted_notification_does_not_reappear_after_holdout(self):
        notifications = self.client.get('/api/notifications').json()['notifications']
        target = notifications[0]
        self.client.delete(f"/api/notifications/{target['id']}")
        self.run_holdout()
        remaining = self.client.get('/api/notifications').json()['notifications']
        self.assertFalse(any(item['id'] == target['id'] for item in remaining))

    def test_36_saved_payload_is_valid_utf8_json(self):
        self.run_holdout()
        with connection() as conn:
            raw = conn.execute('SELECT value FROM app_meta WHERE key = ?', (HOLDOUT_RESULT_META_KEY,)).fetchone()['value']
        self.assertEqual(len(json.loads(raw)['predictions']), 80)

    def test_37_holdout_preserves_original_demo_source_awareness(self):
        self.run_holdout()
        result = self.client.get('/api/analyze/1', params={'use_ai': 'false'}).json()
        self.assertEqual(result['indicators']['source_awareness'], 25)

    def test_38_results_remain_available_after_repeated_status_reads(self):
        result = self.run_holdout()
        for _ in range(3):
            self.assertEqual(self.client.get('/api/evaluation').json()['latest_holdout_result']['run_id'], result['run_id'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
