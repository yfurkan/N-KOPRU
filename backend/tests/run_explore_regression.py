from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from app.main import app


class ExploreRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_version(self):
        r = self.client.get('/health')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['version'], '1.4.0')

    def test_02_topic_catalog(self):
        r = self.client.get('/api/explore')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data['topics']), 6)
        self.assertEqual(set(data['categories']), {
            'AI & Eğitim', 'Dijital Etik', 'Gençlik & Sosyal Medya', 'İklim Teknolojileri'
        })
        self.assertTrue(all(item['comment_count'] >= 8 for item in data['topics']))

    def test_03_category_filter(self):
        r = self.client.get('/api/explore', params={'category': 'AI & Eğitim'})
        self.assertEqual(r.status_code, 200)
        topics = r.json()['topics']
        self.assertEqual(len(topics), 2)
        self.assertTrue(all(t['category'] == 'AI & Eğitim' for t in topics))

    def test_04_search_is_turkish_fold_tolerant(self):
        r = self.client.get('/api/explore', params={'q': 'yapay zeka'})
        self.assertEqual(r.status_code, 200)
        ids = {t['id'] for t in r.json()['topics']}
        self.assertTrue({101, 105, 106}.issubset(ids))

    def test_05_search_by_summary_and_tag(self):
        r = self.client.get('/api/explore', params={'q': 'mahremiyet'})
        self.assertIn(102, [t['id'] for t in r.json()['topics']])
        r = self.client.get('/api/explore', params={'q': 'uyku'})
        self.assertIn(103, [t['id'] for t in r.json()['topics']])

    def test_06_each_topic_can_be_opened(self):
        catalog = self.client.get('/api/explore').json()['topics']
        for item in catalog:
            with self.subTest(topic_id=item['id']):
                r = self.client.get(f"/api/explore/{item['id']}")
                self.assertEqual(r.status_code, 200)
                post = r.json()
                self.assertEqual(post['id'], item['id'])
                self.assertEqual(len(post['comments']), item['comment_count'])
                self.assertEqual(post['text'], item['title'])

    def test_07_each_topic_can_be_analyzed(self):
        catalog = self.client.get('/api/explore').json()['topics']
        for item in catalog:
            with self.subTest(topic_id=item['id']):
                r = self.client.get(f"/api/analyze/{item['id']}", params={'use_ai': 'false'})
                self.assertEqual(r.status_code, 200)
                analysis = r.json()
                self.assertEqual(analysis['post_id'], item['id'])
                self.assertEqual(analysis['indicators']['comment_count'], item['comment_count'])
                self.assertTrue(analysis['viewpoints'])
                self.assertTrue(analysis['bridge']['bridge_question'])

    def test_08_unknown_topic_is_404(self):
        self.assertEqual(self.client.get('/api/explore/9999').status_code, 404)
        self.assertEqual(self.client.get('/api/analyze/9999', params={'use_ai':'false'}).status_code, 404)

    def test_09_empty_search_returns_empty_list_not_error(self):
        r = self.client.get('/api/explore', params={'q':'zzzz-eslesmeyen-konu'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['topics'], [])

    def test_10_category_and_search_are_intersected(self):
        r = self.client.get('/api/explore', params={'category':'AI & Eğitim', 'q':'beyan'})
        self.assertEqual(r.status_code, 200)
        topics = r.json()['topics']
        self.assertEqual([t['id'] for t in topics], [105])

    def test_11_categories_remain_available_while_results_are_filtered(self):
        r = self.client.get('/api/explore', params={'category':'Dijital Etik'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(set(r.json()['categories']), {
            'AI & Eğitim', 'Dijital Etik', 'Gençlik & Sosyal Medya', 'İklim Teknolojileri'
        })

    def test_12_catalog_comment_counts_match_opened_posts(self):
        catalog = self.client.get('/api/explore').json()['topics']
        for item in catalog:
            with self.subTest(topic_id=item['id']):
                post = self.client.get(f"/api/explore/{item['id']}").json()
                self.assertEqual(item['comment_count'], len(post['comments']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
