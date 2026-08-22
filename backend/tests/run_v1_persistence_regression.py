from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

# Bu test tek başına çalıştırılırken uygulama importundan önce test DB'sini sabitle.
TEST_DB = Path(tempfile.gettempdir()) / 'nkopru_v1_persistence_regression.db'
os.environ['N_KOPRU_DB_PATH'] = str(TEST_DB)
for suffix in ('', '-wal', '-shm'):
    try:
        Path(str(TEST_DB) + suffix).unlink()
    except FileNotFoundError:
        pass

from fastapi.testclient import TestClient

from app.database import reset_database_for_tests
from app.main import app


class V1PersistenceRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_database_for_tests()
        cls.client = TestClient(app)

    def test_01_health_declares_sqlite(self):
        data = self.client.get('/health').json()
        self.assertEqual(data['version'], '1.4.0')
        self.assertEqual(data['storage'], 'sqlite')

    def test_02_profile_is_real_and_starts_from_data(self):
        data = self.client.get('/api/profile').json()
        self.assertEqual(data['user']['display_name'], 'Yerel Kullanıcı')
        self.assertEqual(data['stats']['analysis_count'], 0)
        self.assertEqual(data['recent_analyses'], [])

    def test_03_profile_update_persists(self):
        payload = {'display_name':'N Köprü Test','handle':'testci','bio':'Kalıcı profil testi'}
        updated = self.client.put('/api/profile', json=payload)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()['user']['handle'], '@testci')
        reopened = self.client.get('/api/profile').json()
        self.assertEqual(reopened['user']['display_name'], payload['display_name'])
        self.assertEqual(reopened['user']['bio'], payload['bio'])

    def test_04_analysis_creates_history_snapshot(self):
        analyzed = self.client.get('/api/analyze/1', params={'use_ai':'false'})
        self.assertEqual(analyzed.status_code, 200)
        history = self.client.get('/api/history').json()
        self.assertEqual(history['count'], 1)
        self.assertEqual(len(history['analyses']), 1)
        row = history['analyses'][0]
        self.assertEqual(row['post_id'], 1)
        self.assertGreater(row['comment_count'], 0)
        detail = self.client.get(f"/api/history/{row['id']}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()['analysis']['post_id'], 1)

    def test_05_second_snapshot_compares_with_previous(self):
        second = self.client.get('/api/analyze/1', params={'use_ai':'false'}).json()
        self.assertTrue(second['changes_since_last_visit'])
        self.assertTrue(any('Önceki analizden bu yana' in x for x in second['changes_since_last_visit']))
        history = self.client.get('/api/history', params={'post_id':1}).json()
        self.assertEqual(len(history['analyses']), 2)

    def test_06_custom_post_survives_outside_process_memory(self):
        payload = {
            'title':'Kalıcı özel tartışma',
            'comments':['Bir görüş.', 'Başka bir görüş.', 'Üçüncü görüş.', 'Kaynak var mı?'],
            'use_ai':False,
        }
        created = self.client.post('/api/analyze-discussion', json=payload)
        self.assertEqual(created.status_code, 200)
        post_id = created.json()['post']['id']
        reopened = self.client.get(f'/api/posts/{post_id}')
        self.assertEqual(reopened.status_code, 200)
        self.assertEqual(reopened.json()['text'], payload['title'])
        history = self.client.get('/api/history', params={'post_id':post_id}).json()
        self.assertEqual(len(history['analyses']), 1)

    def test_07_bookmark_list_message_and_notification_are_database_backed(self):
        bookmark = self.client.post('/api/bookmarks', json={
            'kind':'discussion','post_id':1,'title':'Kalıcı tartışma','text':'Kayıt','tab_index':0,
        })
        self.assertTrue(bookmark.json()['created'])
        made_list = self.client.post('/api/lists', json={'name':'Kalıcı Liste','description':'SQLite'}).json()['list']
        self.client.post(f"/api/lists/{made_list['id']}/items", json={
            'kind':'discussion','post_id':1,'title':'Kalıcı tartışma','text':'Kayıt','tab_index':0,
        })
        sent = self.client.post('/api/messages/2', json={'text':'SQLite kalıcılık mesajı'})
        self.assertEqual(sent.status_code, 200)
        notifs = self.client.get('/api/notifications').json()['notifications']
        self.assertTrue(notifs)
        target = notifs[0]
        self.client.post(f"/api/notifications/{target['id']}/read")

        self.assertTrue(any(x['title']=='Kalıcı tartışma' for x in self.client.get('/api/bookmarks').json()['bookmarks']))
        self.assertEqual(self.client.get(f"/api/lists/{made_list['id']}").json()['list']['item_count'], 1)
        self.assertTrue(any(x['text']=='SQLite kalıcılık mesajı' for x in self.client.get('/api/messages/2').json()['messages']))
        current = next(x for x in self.client.get('/api/notifications').json()['notifications'] if x['id']==target['id'])
        self.assertTrue(current['is_read'])

    def test_08_profile_stats_follow_real_records(self):
        data = self.client.get('/api/profile').json()
        stats = data['stats']
        self.assertGreaterEqual(stats['analysis_count'], 3)
        self.assertGreaterEqual(stats['unique_discussions'], 2)
        self.assertGreaterEqual(stats['bookmark_count'], 1)
        self.assertGreaterEqual(stats['list_count'], 4)
        self.assertGreaterEqual(stats['list_item_count'], 1)
        self.assertGreaterEqual(stats['sent_message_count'], 1)
        self.assertIsNotNone(stats['last_analyzed_at'])

    def test_09_unknown_history_is_404(self):
        self.assertEqual(self.client.get('/api/history/999999').status_code, 404)

    def test_10_history_limit_validation(self):
        self.assertEqual(self.client.get('/api/history', params={'limit':0}).status_code, 422)
        self.assertEqual(self.client.get('/api/history', params={'limit':201}).status_code, 422)

    def test_11_snapshot_comparator_detects_real_post_change(self):
        from app.analyzer import analyze_post
        from app.history import record_analysis_snapshot
        from app.models import Comment, Post

        base_comments = [
            Comment(id=1, author='A', text='Kontrollü kullanım yararlı olabilir.', created_at='1 dk', likes=0),
            Comment(id=2, author='B', text='Tam yasak daha güvenli olabilir.', created_at='1 dk', likes=0),
            Comment(id=3, author='C', text='Ortak bir yönerge gerekli.', created_at='1 dk', likes=0),
        ]
        base = Post(id=4242, author='Test', handle='@test', text='Değişim testi', created_at='şimdi', comments=base_comments)
        first = analyze_post(base, demo_mode=False, use_ai=False)
        record_analysis_snapshot(base, first)

        changed = base.model_copy(deep=True)
        changed.comments.append(Comment(id=4, author='D', text='Yeni ölçümde katılım %73 oldu; bunun kaynağı nedir?', created_at='şimdi', likes=0))
        second = analyze_post(changed, demo_mode=False, use_ai=False)
        compared, _ = record_analysis_snapshot(changed, second)

        self.assertTrue(any('benzersiz yorum' in note for note in compared.changes_since_last_visit))
        self.assertFalse(any('ölçülebilir bir değişiklik tespit edilmedi' in note for note in compared.changes_since_last_visit))


if __name__ == '__main__':
    unittest.main(verbosity=2)
