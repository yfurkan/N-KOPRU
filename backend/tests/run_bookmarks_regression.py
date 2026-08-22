import unittest

from fastapi.testclient import TestClient

from app.bookmarks import reset_bookmarks
from app.main import app


class BookmarksRegression(unittest.TestCase):
    def setUp(self):
        reset_bookmarks()
        self.client = TestClient(app)

    def test_01_health_version(self):
        r = self.client.get('/health')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['version'], '1.4.0')

    def test_02_empty_list(self):
        r = self.client.get('/api/bookmarks')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['count'], 0)
        self.assertEqual(r.json()['bookmarks'], [])

    def test_03_create_discussion(self):
        payload = {
            'kind': 'discussion', 'post_id': 1,
            'title': 'Üniversitelerde yapay zekâ kullanımı yasaklanmalı mı?',
            'text': '20 yorum içeren tartışma', 'tab_index': 0,
        }
        r = self.client.post('/api/bookmarks', json=payload)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['created'])
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['bookmark']['kind'], 'discussion')

    def test_04_duplicate_is_idempotent(self):
        payload = {'kind':'claim','post_id':1,'title':'İddia #4','text':'Geçen dönem %70 kullandı.','tab_index':3,'comment_id':4}
        first = self.client.post('/api/bookmarks', json=payload).json()
        second = self.client.post('/api/bookmarks', json=payload).json()
        self.assertTrue(first['created'])
        self.assertFalse(second['created'])
        self.assertEqual(first['bookmark']['id'], second['bookmark']['id'])
        self.assertEqual(second['count'], 1)

    def test_05_filters(self):
        rows = [
            {'kind':'discussion','post_id':1,'title':'A','text':'Tartışma','tab_index':0},
            {'kind':'claim','post_id':1,'title':'B','text':'İddia','tab_index':3,'comment_id':4},
            {'kind':'bridge','post_id':1,'title':'C','text':'Köprü sorusu','tab_index':7},
        ]
        for row in rows:
            self.client.post('/api/bookmarks', json=row)
        r = self.client.get('/api/bookmarks?kind=claim')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['count'], 3)  # toplam kayıt sayısı korunur
        self.assertEqual(len(r.json()['bookmarks']), 1)
        self.assertEqual(r.json()['bookmarks'][0]['kind'], 'claim')

    def test_06_invalid_filter_rejected(self):
        r = self.client.get('/api/bookmarks?kind=banana')
        self.assertEqual(r.status_code, 400)

    def test_07_invalid_kind_rejected(self):
        r = self.client.post('/api/bookmarks', json={'kind':'banana','post_id':1,'title':'X','text':'Y'})
        self.assertEqual(r.status_code, 400)

    def test_08_delete(self):
        created = self.client.post('/api/bookmarks', json={'kind':'bridge','post_id':1,'title':'Köprü','text':'Bir soru?','tab_index':7}).json()
        bid = created['bookmark']['id']
        r = self.client.delete(f'/api/bookmarks/{bid}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['count'], 0)
        self.assertEqual(self.client.get('/api/bookmarks').json()['bookmarks'], [])

    def test_09_delete_unknown_is_404(self):
        r = self.client.delete('/api/bookmarks/99999')
        self.assertEqual(r.status_code, 404)

    def test_10_detail(self):
        created = self.client.post('/api/bookmarks', json={'kind':'claim','post_id':1,'title':'İddia','text':'Kaynak gerekir','tab_index':3,'comment_id':9}).json()
        bid = created['bookmark']['id']
        r = self.client.get(f'/api/bookmarks/{bid}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['bookmark']['comment_id'], 9)

    def test_11_three_kinds_keep_target_steps(self):
        cases = [('discussion',0),('claim',3),('bridge',7)]
        for idx,(kind,tab) in enumerate(cases, start=1):
            payload={'kind':kind,'post_id':1,'title':f'T{idx}','text':f'X{idx}','tab_index':tab}
            if kind == 'claim': payload['comment_id'] = 4
            self.client.post('/api/bookmarks', json=payload)
        data = self.client.get('/api/bookmarks').json()['bookmarks']
        target = {row['kind']: row['tab_index'] for row in data}
        self.assertEqual(target, {'bridge':7,'claim':3,'discussion':0})


if __name__ == '__main__':
    unittest.main(verbosity=2)
