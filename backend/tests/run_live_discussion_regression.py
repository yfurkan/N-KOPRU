import os
import unittest

os.environ.setdefault('N_KOPRU_DB_PATH', '/tmp/nkopru_v130_live_regression.db')

from fastapi.testclient import TestClient

from app.database import connection, reset_database_for_tests
from app.demo import DEMO_POST
from app.main import app


QUESTION = 'Bu yasak öğrencilerin ruh sağlığını nasıl etkiler?'
CLAIM = 'Yapay zekâ kullanımı mezunların iş bulma oranını yüzde 35 artırıyor.'


class LiveDiscussionRegressionTests(unittest.TestCase):
    def setUp(self):
        reset_database_for_tests()
        self.client = TestClient(app)

    def analyze_demo(self):
        response = self.client.get('/api/analyze/1?use_ai=false')
        self.assertEqual(response.status_code, 200)
        return response.json()

    def append_demo(self, text, **extra):
        payload = {'text': text, 'use_ai': False, **extra}
        return self.client.post('/api/posts/1/comments', json=payload)

    def new_custom(self):
        response = self.client.post('/api/analyze-discussion', json={
            'title': 'Canlı tartışma testi',
            'comments': [
                'Kontrollü kullanım ve açık kurallar gerekli.',
                'Tam yasak öğrencileri koruyabilir.',
                'Yararlı kullanım alanları korunmalı.',
            ],
            'use_ai': False,
        })
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_01_health_reports_v130(self):
        self.assertEqual(self.client.get('/health').json()['version'], '1.5.0')

    def test_02_append_response_contains_live_analysis_contract(self):
        self.analyze_demo()
        body = self.append_demo(QUESTION).json()
        self.assertEqual(set(body), {'post', 'comment', 'analysis', 'history_id', 'notifications_created'})
        self.assertGreater(body['history_id'], 0)

    def test_03_demo_comment_is_persisted(self):
        self.analyze_demo()
        self.append_demo(QUESTION)
        post = self.client.get('/api/posts/demo').json()
        self.assertEqual(len(post['comments']), 81)
        self.assertEqual(post['comments'][-1]['text'], QUESTION)

    def test_04_append_automatically_creates_snapshot(self):
        self.analyze_demo()
        self.append_demo(QUESTION)
        with connection() as conn:
            count = conn.execute('SELECT COUNT(*) AS c FROM analysis_history WHERE post_id = 1').fetchone()['c']
        self.assertEqual(int(count), 2)

    def test_05_new_unique_comment_is_visible_in_change_timeline(self):
        self.analyze_demo()
        body = self.append_demo(QUESTION).json()
        self.assertTrue(any('1 yeni benzersiz yorum' in item for item in body['analysis']['changes_since_last_visit']))

    def test_06_new_question_creates_only_related_question_notification(self):
        self.analyze_demo()
        before = {item['id'] for item in self.client.get('/api/notifications').json()['notifications']}
        body = self.append_demo(QUESTION).json()
        after = self.client.get('/api/notifications').json()['notifications']
        created = [item for item in after if item['id'] not in before]
        self.assertEqual(body['notifications_created'], 1)
        self.assertEqual([item['kind'] for item in created], ['source_request'])

    def test_07_same_question_second_time_creates_no_notification(self):
        self.analyze_demo()
        self.append_demo(QUESTION)
        second = self.append_demo(QUESTION).json()
        self.assertEqual(second['notifications_created'], 0)
        self.assertEqual(second['analysis']['changes_since_last_visit'], ['Önceki analizden bu yana ölçülebilir bir değişiklik tespit edilmedi.'])

    def test_08_duplicate_social_comment_remains_in_raw_post_but_not_unique_analysis(self):
        self.analyze_demo()
        first = self.append_demo(QUESTION).json()
        second = self.append_demo(QUESTION).json()
        self.assertEqual(len(second['post']['comments']), 82)
        self.assertEqual(first['analysis']['indicators']['comment_count'], 21)
        self.assertEqual(second['analysis']['indicators']['comment_count'], 21)

    def test_09_new_high_priority_claim_creates_one_claim_alert(self):
        self.analyze_demo()
        body = self.append_demo(CLAIM).json()
        self.assertEqual(body['notifications_created'], 1)
        self.assertTrue(any(item['text'] == CLAIM and item['priority'] == 'Yüksek' for item in body['analysis']['claims']))

    def test_10_same_high_priority_claim_is_not_alerted_twice(self):
        self.analyze_demo()
        self.append_demo(CLAIM)
        second = self.append_demo(CLAIM).json()
        self.assertEqual(second['notifications_created'], 0)

    def test_11_append_never_repeats_analysis_ready_notification(self):
        self.analyze_demo()
        before = sum(item['kind'] == 'analysis_ready' for item in self.client.get('/api/notifications').json()['notifications'])
        self.append_demo(QUESTION)
        after = sum(item['kind'] == 'analysis_ready' for item in self.client.get('/api/notifications').json()['notifications'])
        self.assertEqual(after, before)

    def test_12_whitespace_only_comment_is_rejected(self):
        response = self.append_demo('   ')
        self.assertEqual(response.status_code, 400)

    def test_13_comment_above_limit_is_rejected(self):
        response = self.append_demo('a' * 1201)
        self.assertEqual(response.status_code, 422)

    def test_14_unknown_post_is_rejected(self):
        response = self.client.post('/api/posts/999999/comments', json={'text': QUESTION, 'use_ai': False})
        self.assertEqual(response.status_code, 404)

    def test_15_default_author_comes_from_local_profile(self):
        body = self.append_demo(QUESTION).json()
        self.assertEqual(body['comment']['author'], 'Yerel Kullanıcı')

    def test_16_explicit_author_is_preserved(self):
        body = self.append_demo(QUESTION, author='Utku Kara').json()
        self.assertEqual(body['comment']['author'], 'Utku Kara')

    def test_17_comment_whitespace_is_normalized(self):
        body = self.append_demo('  Yeni   bir\n yorum.  ').json()
        self.assertEqual(body['comment']['text'], 'Yeni bir yorum.')

    def test_18_comment_ids_advance_without_collision(self):
        first = self.append_demo('Birinci yeni yorum.').json()['comment']['id']
        second = self.append_demo('İkinci yeni yorum.').json()['comment']['id']
        self.assertEqual((first, second), (81, 82))

    def test_19_static_demo_source_is_not_mutated(self):
        self.append_demo(QUESTION)
        self.assertEqual(len(DEMO_POST.comments), 80)

    def test_20_custom_discussion_accepts_live_comment(self):
        created = self.new_custom()
        post_id = created['post']['id']
        response = self.client.post(f'/api/posts/{post_id}/comments', json={'text': QUESTION, 'use_ai': False})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['post']['comments']), 4)

    def test_21_explore_discussion_accepts_live_comment(self):
        before = self.client.get('/api/explore/101').json()
        response = self.client.post('/api/posts/101/comments', json={'text': QUESTION, 'use_ai': False})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['post']['comments']), len(before['comments']) + 1)
        self.assertEqual(len(self.client.get('/api/explore/101').json()['comments']), len(before['comments']) + 1)

    def test_22_analysis_and_post_ids_remain_aligned(self):
        body = self.append_demo(QUESTION).json()
        self.assertEqual(body['post']['id'], 1)
        self.assertEqual(body['analysis']['post_id'], 1)

    def test_23_history_detail_contains_appended_comment(self):
        body = self.append_demo(QUESTION).json()
        detail = self.client.get(f"/api/history/{body['history_id']}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()['post']['comments'][-1]['text'], QUESTION)

    def test_24_unchanged_manual_reanalysis_after_append_stays_quiet(self):
        self.analyze_demo()
        self.append_demo(QUESTION)
        before = self.client.get('/api/notifications').json()['total_count']
        repeat = self.client.get('/api/analyze/1?use_ai=false').json()
        after = self.client.get('/api/notifications').json()['total_count']
        self.assertEqual(after, before)
        self.assertEqual(repeat['changes_since_last_visit'], ['Önceki analizden bu yana ölçülebilir bir değişiklik tespit edilmedi.'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
