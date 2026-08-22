import json
import os
import unittest
from concurrent.futures import ThreadPoolExecutor

os.environ.setdefault('N_KOPRU_DB_PATH', '/tmp/nkopru_v130_live_persistence.db')

from fastapi.testclient import TestClient

from app.database import connection, db_path, initialize_schema, reset_database_for_tests
from app.demo import DEMO_POST
from app.history import append_post_comment, get_custom_post
from app.main import app


QUESTION = 'Bu yasak öğrencilerin ruh sağlığını nasıl etkiler?'


class LiveDiscussionPersistenceTests(unittest.TestCase):
    def setUp(self):
        reset_database_for_tests()
        self.client = TestClient(app)

    def append_demo(self, text=QUESTION):
        response = self.client.post('/api/posts/1/comments', json={'text': text, 'use_ai': False})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_01_sqlite_database_file_exists(self):
        self.append_demo()
        self.assertTrue(db_path().exists())

    def test_02_demo_override_is_stored_as_json(self):
        self.append_demo()
        with connection() as conn:
            row = conn.execute('SELECT post_json FROM custom_posts WHERE post_id = 1').fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(len(json.loads(row['post_json'])['comments']), 81)

    def test_03_persisted_post_can_be_reloaded_from_fresh_connection(self):
        self.append_demo()
        restored = get_custom_post(1)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.comments[-1].text, QUESTION)

    def test_04_schema_reinitialization_preserves_live_comment(self):
        self.append_demo()
        initialize_schema()
        self.assertEqual(get_custom_post(1).comments[-1].text, QUESTION)

    def test_05_both_demo_routes_return_same_persisted_copy(self):
        self.append_demo()
        demo = self.client.get('/api/posts/demo').json()
        by_id = self.client.get('/api/posts/1').json()
        self.assertEqual(demo, by_id)

    def test_06_multiple_comments_survive_separate_requests(self):
        self.append_demo('Kalıcı yorum bir.')
        self.append_demo('Kalıcı yorum iki.')
        restored = get_custom_post(1)
        self.assertEqual([item.text for item in restored.comments[-2:]], ['Kalıcı yorum bir.', 'Kalıcı yorum iki.'])

    def test_07_snapshot_persists_updated_post_and_analysis(self):
        body = self.append_demo()
        with connection() as conn:
            row = conn.execute('SELECT post_json, analysis_json FROM analysis_history WHERE id = ?', (body['history_id'],)).fetchone()
        stored_post = json.loads(row['post_json'])
        stored_analysis = json.loads(row['analysis_json'])
        self.assertEqual(stored_post['comments'][-1]['text'], QUESTION)
        self.assertEqual(stored_analysis['post_id'], 1)

    def test_08_custom_discussion_update_stays_in_same_record(self):
        created = self.client.post('/api/analyze-discussion', json={
            'title': 'Kalıcı özel tartışma',
            'comments': ['Kontrollü kullanım gerekli.', 'Tam yasak gerekli.', 'Yasak doğru değil.'],
            'use_ai': False,
        }).json()
        post_id = created['post']['id']
        response = self.client.post(f'/api/posts/{post_id}/comments', json={'text': QUESTION, 'use_ai': False})
        self.assertEqual(response.status_code, 200)
        with connection() as conn:
            count = conn.execute('SELECT COUNT(*) AS c FROM custom_posts WHERE post_id = ?', (post_id,)).fetchone()['c']
        self.assertEqual(int(count), 1)
        self.assertEqual(len(get_custom_post(post_id).comments), 4)

    def test_09_explore_override_survives_normal_post_route(self):
        original = self.client.get('/api/explore/102').json()
        self.client.post('/api/posts/102/comments', json={'text': QUESTION, 'use_ai': False})
        restored = self.client.get('/api/posts/102').json()
        self.assertEqual(len(restored['comments']), len(original['comments']) + 1)
        self.assertEqual(restored['comments'][-1]['text'], QUESTION)

    def test_10_deleted_live_event_remains_soft_deleted(self):
        self.client.get('/api/analyze/1?use_ai=false')
        body = self.append_demo()
        self.assertEqual(body['notifications_created'], 1)
        rows = self.client.get('/api/notifications').json()['notifications']
        target = next(item for item in rows if item['kind'] == 'source_request' and item['title'].startswith('Yeni'))
        self.client.delete(f"/api/notifications/{target['id']}")
        self.append_demo()
        visible = self.client.get('/api/notifications').json()['notifications']
        self.assertFalse(any(item['id'] == target['id'] for item in visible))
        with connection() as conn:
            deleted = conn.execute('SELECT deleted FROM notifications WHERE id = ?', (target['id'],)).fetchone()['deleted']
        self.assertEqual(int(deleted), 1)

    def test_11_concurrent_append_ids_are_serialized(self):
        def add(index):
            updated, comment = append_post_comment(DEMO_POST, f'Eş zamanlı yorum {index}.', 'Test Kullanıcısı')
            return comment.id, len(updated.comments)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(add, (1, 2)))
        self.assertEqual(sorted(item[0] for item in results), [81, 82])
        self.assertEqual(len(get_custom_post(1).comments), 82)

    def test_12_existing_database_tables_remain_available(self):
        self.append_demo()
        with connection() as conn:
            tables = {row['name'] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        for name in ('notifications', 'messages', 'bookmarks', 'topic_lists', 'analysis_history', 'profiles'):
            self.assertIn(name, tables)

    def test_13_unrelated_modules_remain_operational_after_append(self):
        self.append_demo()
        for path in ('/api/messages', '/api/bookmarks', '/api/lists', '/api/profile'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)
