from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.notifications import list_notifications, record_analysis, reset_for_tests
from app.history import record_analysis_snapshot, reset_history_for_tests
from app.analyzer import analyze_demo
from app.demo import DEMO_POST
from app.models import ClaimItem, QuestionItem
from app.database import transaction


class NotificationRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        reset_history_for_tests()
        reset_for_tests()

    def test_01_health_version(self):
        r = self.client.get('/health')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['version'], '1.5.0')

    def test_02_seed_notifications_are_available(self):
        data = self.client.get('/api/notifications').json()
        self.assertGreaterEqual(len(data['notifications']), 3)
        self.assertEqual(data['total_count'], len(data['notifications']))
        self.assertEqual(data['unread_count'], len([x for x in data['notifications'] if not x['is_read']]))
        self.assertEqual(data['read_count'] + data['unread_count'], data['total_count'])

    def test_03_unread_and_read_filters(self):
        first = self.client.get('/api/notifications').json()['notifications'][0]
        self.client.post(f"/api/notifications/{first['id']}/read")
        unread = self.client.get('/api/notifications', params={'status':'unread'}).json()
        read = self.client.get('/api/notifications', params={'status':'read'}).json()
        self.assertTrue(all(not x['is_read'] for x in unread['notifications']))
        self.assertTrue(all(x['is_read'] for x in read['notifications']))
        self.assertTrue(any(x['id'] == first['id'] for x in read['notifications']))

    def test_04_legacy_unread_filter_still_works(self):
        data = self.client.get('/api/notifications', params={'unread_only':'true'}).json()
        self.assertTrue(data['notifications'])
        self.assertTrue(all(not x['is_read'] for x in data['notifications']))

    def test_05_mark_one_read_and_unread(self):
        first = self.client.get('/api/notifications').json()['notifications'][0]
        before = self.client.get('/api/notifications').json()['unread_count']
        result = self.client.post(f"/api/notifications/{first['id']}/read")
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json()['notification']['is_read'])
        self.assertEqual(result.json()['unread_count'], before - 1)
        result = self.client.post(f"/api/notifications/{first['id']}/unread")
        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.json()['notification']['is_read'])
        self.assertEqual(result.json()['unread_count'], before)

    def test_06_mark_all_read(self):
        result = self.client.post('/api/notifications/read-all')
        self.assertEqual(result.status_code, 200)
        self.assertGreaterEqual(result.json()['changed'], 1)
        self.assertEqual(result.json()['unread_count'], 0)
        self.assertEqual(result.json()['read_count'], result.json()['total_count'])

    def test_07_delete_one_and_restore(self):
        first = self.client.get('/api/notifications').json()['notifications'][0]
        before = self.client.get('/api/notifications').json()['total_count']
        deleted = self.client.delete(f"/api/notifications/{first['id']}")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.json()['total_count'], before - 1)
        self.assertEqual(deleted.json()['deleted_ids'], [first['id']])
        self.assertFalse(any(x['id'] == first['id'] for x in self.client.get('/api/notifications').json()['notifications']))
        restored = self.client.post('/api/notifications/restore', json={'ids':[first['id']]})
        self.assertEqual(restored.status_code, 200)
        self.assertEqual(restored.json()['changed'], 1)
        self.assertTrue(any(x['id'] == first['id'] for x in self.client.get('/api/notifications').json()['notifications']))

    def test_08_clear_read_and_restore_batch(self):
        self.client.post('/api/notifications/read-all')
        before = self.client.get('/api/notifications').json()['total_count']
        cleared = self.client.delete('/api/notifications/read')
        self.assertEqual(cleared.status_code, 200)
        self.assertEqual(cleared.json()['changed'], before)
        self.assertEqual(cleared.json()['total_count'], 0)
        ids = cleared.json()['deleted_ids']
        self.assertEqual(len(ids), before)
        restored = self.client.post('/api/notifications/restore', json={'ids':ids})
        self.assertEqual(restored.json()['changed'], before)
        self.assertEqual(self.client.get('/api/notifications').json()['total_count'], before)

    def test_09_delete_all_does_not_reseed(self):
        rows = self.client.get('/api/notifications').json()['notifications']
        for item in rows:
            self.client.delete(f"/api/notifications/{item['id']}")
        data = self.client.get('/api/notifications').json()
        self.assertEqual(data['total_count'], 0)
        self.assertEqual(data['notifications'], [])

    def test_10_invalid_filter_rejected(self):
        self.assertEqual(self.client.get('/api/notifications', params={'status':'bogus'}).status_code, 400)

    def test_11_unknown_notification_is_404(self):
        self.assertEqual(self.client.post('/api/notifications/999999/read').status_code, 404)
        self.assertEqual(self.client.post('/api/notifications/999999/unread').status_code, 404)
        self.assertEqual(self.client.delete('/api/notifications/999999').status_code, 404)

    def test_12_analysis_creates_actionable_notifications(self):
        before_ids = {x['id'] for x in self.client.get('/api/notifications').json()['notifications']}
        r = self.client.get('/api/analyze/101', params={'use_ai':'false'})
        self.assertEqual(r.status_code, 200)
        rows = self.client.get('/api/notifications').json()['notifications']
        new_rows = [x for x in rows if x['id'] not in before_ids]
        self.assertGreaterEqual(len(new_rows), 3)
        self.assertTrue(all(x['post_id'] == 101 for x in new_rows))
        self.assertTrue({0, 2, 7}.issubset({x['tab_index'] for x in new_rows}))

    def test_13_same_analysis_does_not_duplicate_same_event(self):
        self.client.get('/api/analyze/101', params={'use_ai':'false'})
        count1 = len(self.client.get('/api/notifications').json()['notifications'])
        self.client.get('/api/analyze/101', params={'use_ai':'false'})
        count2 = len(self.client.get('/api/notifications').json()['notifications'])
        self.assertEqual(count1, count2)

    def test_14_deleted_event_does_not_immediately_reappear(self):
        self.client.get('/api/analyze/101', params={'use_ai':'false'})
        rows = [x for x in self.client.get('/api/notifications').json()['notifications'] if x['post_id'] == 101]
        target = rows[0]
        self.client.delete(f"/api/notifications/{target['id']}")
        self.client.get('/api/analyze/101', params={'use_ai':'false'})
        rows2 = self.client.get('/api/notifications').json()['notifications']
        self.assertFalse(any(x['id'] == target['id'] for x in rows2))
        self.assertFalse(any(x['kind'] == target['kind'] and x['post_id'] == 101 and x['title'] == target['title'] for x in rows2))

    def test_15_each_actionable_notification_has_destination(self):
        rows = self.client.get('/api/notifications').json()['notifications']
        self.assertTrue(all(x['post_id'] is not None and x['tab_index'] is not None for x in rows))

    def test_16_custom_discussion_notification_can_reopen_post(self):
        payload = {
            'title': 'Kampüslerde gece ulaşımı nasıl düzenlenmeli?',
            'comments': [
                'Gece servisleri artırılmalı.',
                'Bütçe sınırlıysa talebe göre planlama yapılmalı.',
                'Geçen yıl öğrencilerin %55i gece ulaşımında sorun yaşadı.',
                'Bu yüzde hangi ankete dayanıyor?',
            ],
            'use_ai': False,
        }
        analyzed = self.client.post('/api/analyze-discussion', json=payload)
        self.assertEqual(analyzed.status_code, 200)
        post_id = analyzed.json()['post']['id']
        reopened = self.client.get(f'/api/posts/{post_id}')
        self.assertEqual(reopened.status_code, 200)
        self.assertEqual(reopened.json()['text'], payload['title'])
        reanalysis = self.client.get(f'/api/analyze/{post_id}', params={'use_ai':'false'})
        self.assertEqual(reanalysis.status_code, 200)
        self.assertEqual(reanalysis.json()['post_id'], post_id)

    def test_17_multiple_custom_discussions_keep_distinct_targets(self):
        base = {
            'comments': ['Birinci görüş.', 'İkinci görüş.', 'Üçüncü görüş.'],
            'use_ai': False,
        }
        a = self.client.post('/api/analyze-discussion', json={**base, 'title':'Birinci özel tartışma'}).json()['post']
        b = self.client.post('/api/analyze-discussion', json={**base, 'title':'İkinci özel tartışma'}).json()['post']
        self.assertNotEqual(a['id'], b['id'])
        self.assertEqual(self.client.get(f"/api/posts/{a['id']}").json()['text'], 'Birinci özel tartışma')
        self.assertEqual(self.client.get(f"/api/posts/{b['id']}").json()['text'], 'İkinci özel tartışma')

    def test_18_notifications_are_newest_first(self):
        rows = self.client.get('/api/notifications').json()['notifications']
        timestamps = [x['created_at'] for x in rows]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))

    def test_19_identical_snapshot_creates_zero_new_notifications(self):
        first = analyze_demo(DEMO_POST.id, use_ai=False)
        first, first_id = record_analysis_snapshot(DEMO_POST, first)
        record_analysis(DEMO_POST, first, history_id=first_id)
        count1 = len(list_notifications())

        second = analyze_demo(DEMO_POST.id, use_ai=False)
        second, second_id = record_analysis_snapshot(DEMO_POST, second)
        created = record_analysis(DEMO_POST, second, history_id=second_id)
        self.assertEqual(created, 0)
        self.assertEqual(len(list_notifications()), count1)
        self.assertEqual(second.changes_since_last_visit, ['Önceki analizden bu yana ölçülebilir bir değişiklik tespit edilmedi.'])

    def test_20_only_new_claim_creates_claim_notification(self):
        first = analyze_demo(DEMO_POST.id, use_ai=False)
        first, first_id = record_analysis_snapshot(DEMO_POST, first)
        record_analysis(DEMO_POST, first, history_id=first_id)
        before_ids = {x.id for x in list_notifications()}

        extra = ClaimItem(
            comment_id=999, text='Yeni karşılaştırmada başarı oranı yüzde 12 arttı.',
            source_status='Kaynak gerekli', claim_type='Nicel / İstatistiksel',
            verification_need='Karşılaştırmalı veri', priority='Yüksek', confidence=0.95,
        )
        changed = first.model_copy(deep=True)
        changed.claims = [*first.claims, extra]
        changed, changed_id = record_analysis_snapshot(DEMO_POST, changed)
        created = record_analysis(DEMO_POST, changed, history_id=changed_id)
        new_rows = [x for x in list_notifications() if x.id not in before_ids]
        self.assertEqual(created, 1)
        self.assertEqual(len(new_rows), 1)
        self.assertEqual(new_rows[0].kind, 'claim_alert')
        self.assertEqual(new_rows[0].tab_index, 3)

    def test_21_same_meaningful_event_content_is_not_repeated(self):
        first = analyze_demo(DEMO_POST.id, use_ai=False)
        first, first_id = record_analysis_snapshot(DEMO_POST, first)
        record_analysis(DEMO_POST, first, history_id=first_id)
        extra = QuestionItem(comment_id=999, text='Bu yeni oran hangi veri setine dayanıyor?')

        changed = first.model_copy(deep=True)
        changed.unanswered_questions = [*first.unanswered_questions, extra]
        changed, changed_id = record_analysis_snapshot(DEMO_POST, changed)
        self.assertEqual(record_analysis(DEMO_POST, changed, history_id=changed_id), 1)
        count1 = len(list_notifications())

        repeated = changed.model_copy(deep=True)
        repeated, repeated_id = record_analysis_snapshot(DEMO_POST, repeated)
        self.assertEqual(record_analysis(DEMO_POST, repeated, history_id=repeated_id), 0)
        self.assertEqual(len(list_notifications()), count1)

    def test_22_one_time_legacy_family_cleanup(self):
        with transaction(immediate=True) as conn:
            conn.execute("DELETE FROM app_meta WHERE key = 'notifications_dedup_v112'")
            conn.execute(
                "INSERT INTO notifications(kind, title, text, created_at, is_read, post_id, tab_index, badge, priority, signature_key, deleted) "
                "VALUES('viewpoint_change', 'Eski sürüm görüş bildirimi', 'aynı olay', '2026-01-01T00:00:00+00:00', 0, 1, 2, 'Görüş', 'normal', 'legacy-duplicate-for-test', 0)"
            )
        rows = list_notifications()
        family = [x for x in rows if x.kind == 'viewpoint_change' and x.post_id == 1 and x.tab_index == 2]
        self.assertEqual(len(family), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
