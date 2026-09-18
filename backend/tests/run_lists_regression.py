import unittest

from fastapi.testclient import TestClient

from app.lists import reset_lists
from app.main import app


class ListsRegression(unittest.TestCase):
    def setUp(self):
        reset_lists(seed=True)
        self.client = TestClient(app)

    def test_01_health_version(self):
        r = self.client.get('/health')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['version'], '1.5.0')

    def test_02_seed_lists_exist(self):
        data = self.client.get('/api/lists').json()
        self.assertEqual(data['count'], 3)
        self.assertEqual([row['name'] for row in data['lists']], ['AI & Eğitim', 'Dijital Etik', 'Gençlik & Sosyal Medya'])
        self.assertTrue(all(row['item_count'] == 0 for row in data['lists']))

    def test_03_create_list(self):
        r = self.client.post('/api/lists', json={'name':'Kaynak Kontrolü','description':'Doğrulanabilir iddialar'})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body['created'])
        self.assertEqual(body['count'], 4)
        self.assertEqual(body['list']['name'], 'Kaynak Kontrolü')

    def test_04_duplicate_name_is_idempotent(self):
        first = self.client.post('/api/lists', json={'name':'Yeni Liste','description':'A'}).json()
        second = self.client.post('/api/lists', json={'name':'  yeni   liste  ','description':'B'}).json()
        self.assertTrue(first['created'])
        self.assertFalse(second['created'])
        self.assertEqual(first['list']['id'], second['list']['id'])
        self.assertEqual(second['count'], 4)

    def test_05_add_discussion_and_detail(self):
        payload = {'kind':'discussion','post_id':1,'title':'Tartışma','text':'20 yorum','tab_index':0}
        r = self.client.post('/api/lists/1/items', json=payload)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body['created'])
        self.assertEqual(body['count'], 1)
        detail = self.client.get('/api/lists/1').json()
        self.assertEqual(detail['list']['discussion_count'], 1)
        self.assertEqual(detail['items'][0]['tab_index'], 0)

    def test_06_duplicate_item_same_list_is_idempotent(self):
        payload = {'kind':'claim','post_id':1,'title':'İddia #4','text':'%70 kullandı','tab_index':3,'comment_id':4}
        first = self.client.post('/api/lists/1/items', json=payload).json()
        second = self.client.post('/api/lists/1/items', json=payload).json()
        self.assertTrue(first['created'])
        self.assertFalse(second['created'])
        self.assertEqual(first['item']['id'], second['item']['id'])
        self.assertEqual(second['count'], 1)

    def test_07_same_item_can_live_in_different_lists(self):
        payload = {'kind':'discussion','post_id':1,'title':'Tartışma','text':'20 yorum','tab_index':0}
        a = self.client.post('/api/lists/1/items', json=payload).json()
        b = self.client.post('/api/lists/2/items', json=payload).json()
        self.assertTrue(a['created'])
        self.assertTrue(b['created'])
        self.assertNotEqual(a['item']['id'], b['item']['id'])

    def test_08_counts_for_three_kinds(self):
        rows = [
            {'kind':'discussion','post_id':1,'title':'T','text':'Tartışma','tab_index':0},
            {'kind':'claim','post_id':1,'title':'İ','text':'İddia','tab_index':3,'comment_id':4},
            {'kind':'bridge','post_id':1,'title':'K','text':'Köprü sorusu?','tab_index':7},
        ]
        for row in rows:
            self.client.post('/api/lists/1/items', json=row)
        detail = self.client.get('/api/lists/1').json()['list']
        self.assertEqual(detail['item_count'], 3)
        self.assertEqual(detail['discussion_count'], 1)
        self.assertEqual(detail['claim_count'], 1)
        self.assertEqual(detail['bridge_count'], 1)

    def test_09_invalid_kind_rejected(self):
        r = self.client.post('/api/lists/1/items', json={'kind':'banana','post_id':1,'title':'X','text':'Y'})
        self.assertEqual(r.status_code, 400)

    def test_10_missing_list_rejected(self):
        r = self.client.post('/api/lists/999/items', json={'kind':'discussion','post_id':1,'title':'X','text':'Y'})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(self.client.get('/api/lists/999').status_code, 404)

    def test_11_remove_item(self):
        made = self.client.post('/api/lists/1/items', json={'kind':'bridge','post_id':1,'title':'K','text':'Soru?','tab_index':7}).json()
        item_id = made['item']['id']
        r = self.client.delete(f'/api/lists/1/items/{item_id}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['count'], 0)
        self.assertEqual(self.client.get('/api/lists/1').json()['items'], [])

    def test_12_delete_list_and_entries(self):
        made = self.client.post('/api/lists', json={'name':'Silinecek','description':'Test'}).json()['list']
        list_id = made['id']
        self.client.post(f'/api/lists/{list_id}/items', json={'kind':'discussion','post_id':1,'title':'X','text':'Y','tab_index':0})
        r = self.client.delete(f'/api/lists/{list_id}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['count'], 3)
        self.assertEqual(self.client.get(f'/api/lists/{list_id}').status_code, 404)

    def test_13_target_steps_survive(self):
        rows = [
            {'kind':'discussion','post_id':1,'title':'T','text':'T','tab_index':0},
            {'kind':'claim','post_id':1,'title':'I','text':'I','tab_index':3,'comment_id':7},
            {'kind':'bridge','post_id':1,'title':'K','text':'K','tab_index':7},
        ]
        for row in rows:
            self.client.post('/api/lists/1/items', json=row)
        target = {row['kind']:row['tab_index'] for row in self.client.get('/api/lists/1').json()['items']}
        self.assertEqual(target, {'bridge':7,'claim':3,'discussion':0})

    def test_14_current_analysis_can_fill_all_quick_add_kinds(self):
        analysis = self.client.get('/api/analyze/1?use_ai=false').json()
        self.assertGreaterEqual(len(analysis['claims']), 1)
        self.assertTrue(analysis['bridge']['bridge_question'])
        self.client.post('/api/lists/1/items', json={'kind':'discussion','post_id':1,'title':'Demo tartışma','text':'80 yorum','tab_index':0})
        for claim in analysis['claims']:
            self.client.post('/api/lists/1/items', json={'kind':'claim','post_id':1,'title':f"İddia #{claim['comment_id']}",'text':claim['text'],'tab_index':3,'comment_id':claim['comment_id']})
        self.client.post('/api/lists/1/items', json={'kind':'bridge','post_id':1,'title':'Köprü Sorusu','text':analysis['bridge']['bridge_question'],'tab_index':7})
        detail = self.client.get('/api/lists/1').json()
        self.assertEqual(detail['list']['discussion_count'], 1)
        self.assertEqual(detail['list']['claim_count'], len(analysis['claims']))
        self.assertEqual(detail['list']['bridge_count'], 1)
        self.assertEqual(detail['list']['item_count'], len(analysis['claims']) + 2)

    def test_15_deleting_all_lists_does_not_reseed_defaults(self):
        rows = self.client.get('/api/lists').json()['lists']
        for item in rows:
            self.client.delete(f"/api/lists/{item['id']}")
        data = self.client.get('/api/lists').json()
        self.assertEqual(data['count'], 0)
        self.assertEqual(data['lists'], [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
