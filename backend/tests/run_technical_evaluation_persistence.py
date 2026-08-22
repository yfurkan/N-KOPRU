import os
import unittest

os.environ.setdefault('N_KOPRU_DB_PATH', '/tmp/nkopru_v131_evaluation_persistence.db')

from fastapi.testclient import TestClient

from app.database import connection, reset_database_for_tests
from app.evaluation import RESULT_META_KEY
from app.main import app


class TechnicalEvaluationPersistenceTests(unittest.TestCase):
    def setUp(self):
        reset_database_for_tests()
        self.client = TestClient(app)

    def measure(self):
        response = self.client.post('/api/evaluation/run', json={'iterations': 1, 'use_ai': False})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def seed_user_state(self):
        self.client.get('/api/analyze/1?use_ai=false')
        self.client.get('/api/notifications')
        self.client.get('/api/messages')
        self.client.get('/api/bookmarks')
        self.client.get('/api/lists')
        self.client.get('/api/profile')

    def table_counts(self):
        tables = (
            'analysis_history', 'notifications', 'messages', 'conversations',
            'bookmarks', 'topic_lists', 'topic_list_entries', 'custom_posts', 'profiles',
        )
        with connection() as conn:
            return {
                table: int(conn.execute(f'SELECT COUNT(*) AS c FROM {table}').fetchone()['c'])
                for table in tables
            }

    def test_01_evaluation_does_not_create_analysis_snapshot(self):
        self.seed_user_state()
        before = self.table_counts()
        self.measure()
        self.assertEqual(before['analysis_history'], self.table_counts()['analysis_history'])

    def test_02_evaluation_does_not_create_notifications(self):
        self.seed_user_state()
        before = self.table_counts()
        self.measure()
        self.assertEqual(before['notifications'], self.table_counts()['notifications'])

    def test_03_evaluation_preserves_all_application_tables(self):
        self.seed_user_state()
        before = self.table_counts()
        self.measure()
        self.assertEqual(before, self.table_counts())

    def test_04_profile_counts_do_not_change(self):
        self.seed_user_state()
        before = self.client.get('/api/profile').json()['stats']
        self.measure()
        self.assertEqual(before, self.client.get('/api/profile').json()['stats'])

    def test_05_latest_result_survives_new_client(self):
        measured = self.measure()
        another_client = TestClient(app)
        saved = another_client.get('/api/evaluation').json()['latest_result']
        self.assertEqual(saved['run_id'], measured['run_id'])

    def test_06_second_run_replaces_only_last_result(self):
        first = self.measure()
        second = self.measure()
        with connection() as conn:
            count = conn.execute('SELECT COUNT(*) AS c FROM app_meta WHERE key = ?', (RESULT_META_KEY,)).fetchone()['c']
        self.assertEqual(count, 1)
        self.assertNotEqual(first['run_id'], second['run_id'])
        self.assertEqual(self.client.get('/api/evaluation').json()['latest_result']['run_id'], second['run_id'])

    def test_07_custom_discussion_is_preserved(self):
        created = self.client.post('/api/analyze-discussion', json={
            'title': 'Kalıcı tartışma',
            'comments': ['Kontrollü kullanım gerekli.', 'Tam yasak yanlış.', 'Kaynağı nedir?'],
            'use_ai': False,
        }).json()['post']
        self.measure()
        self.assertEqual(self.client.get(f"/api/posts/{created['id']}").json()['text'], created['text'])

    def test_08_modified_demo_stays_modified(self):
        response = self.client.post('/api/posts/1/comments', json={
            'text': 'Bu karar öğrencilerin iyi oluşunu nasıl etkiler?', 'use_ai': False,
        })
        self.assertEqual(response.status_code, 200)
        self.measure()
        self.assertEqual(len(self.client.get('/api/posts/demo').json()['comments']), 81)

    def test_09_deleted_notifications_are_not_restored(self):
        self.seed_user_state()
        notifications = self.client.get('/api/notifications').json()['notifications']
        removed = notifications[0]['id']
        self.client.delete(f'/api/notifications/{removed}')
        self.measure()
        active = {item['id'] for item in self.client.get('/api/notifications').json()['notifications']}
        self.assertNotIn(removed, active)

    def test_10_status_read_does_not_write_app_meta(self):
        with connection() as conn:
            before = int(conn.execute('SELECT COUNT(*) AS c FROM app_meta').fetchone()['c'])
        self.client.get('/api/evaluation')
        with connection() as conn:
            after = int(conn.execute('SELECT COUNT(*) AS c FROM app_meta').fetchone()['c'])
        self.assertEqual(before, after)

    def test_11_demo_invariants_use_canonical_not_mutated_demo(self):
        self.client.post('/api/posts/1/comments', json={'text': 'Yeni ve kalıcı bir kaynak sorusu nedir?', 'use_ai': False})
        result = self.measure()
        raw = next(item for item in result['invariants'] if item['key'] == 'raw_demo_comments')
        self.assertEqual(raw['actual'], '80')
        self.assertTrue(raw['passed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
