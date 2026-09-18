from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

TEST_DB = Path(tempfile.gettempdir()) / 'nkopru_v122_viewpoint_consistency.db'
os.environ['N_KOPRU_DB_PATH'] = str(TEST_DB)

from fastapi.testclient import TestClient

from app.database import reset_database_for_tests
from app.main import app


class ViewpointConsistencyPersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        reset_database_for_tests()

    def test_01_health_reports_v123_and_sqlite(self):
        self.assertEqual(self.client.get('/health').json(), {
            'status': 'ok', 'project': 'N-KÖPRÜ', 'version': '1.5.0', 'storage': 'sqlite',
        })

    def test_02_demo_api_places_personal_usage_in_controlled_cluster(self):
        data = self.client.get('/api/analyze/1', params={'use_ai': 'false'}).json()
        controlled = next(item for item in data['viewpoints'] if item['name'] == 'Koşullu / Dengeli')
        self.assertIn(7, controlled['evidence_comment_ids'])

    def test_03_demo_api_places_source_critique_in_neutral_cluster(self):
        data = self.client.get('/api/analyze/1', params={'use_ai': 'false'}).json()
        neutral = next(item for item in data['viewpoints'] if item['name'] == 'Soru / Tarafsız')
        self.assertIn(11, neutral['evidence_comment_ids'])

    def test_04_guardrail_metadata_survives_snapshot_reopen(self):
        created = self.client.get('/api/analyze/1', params={'use_ai': 'false'}).json()
        history_id = self.client.get('/api/history', params={'post_id': 1}).json()['analyses'][0]['id']
        restored = self.client.get(f'/api/history/{history_id}').json()['analysis']
        self.assertEqual(restored['engine']['semantic_guardrail_count'], 2)
        self.assertEqual(restored['viewpoints'], created['viewpoints'])

    def test_05_unchanged_reanalysis_does_not_create_notifications(self):
        self.client.get('/api/analyze/1', params={'use_ai': 'false'})
        before = self.client.get('/api/notifications').json()['total_count']
        self.client.get('/api/analyze/1', params={'use_ai': 'false'})
        self.assertEqual(self.client.get('/api/notifications').json()['total_count'], before)

    def test_06_deleted_viewpoint_notification_is_not_resurrected(self):
        self.client.get('/api/analyze/1', params={'use_ai': 'false'})
        target = next(item for item in self.client.get('/api/notifications').json()['notifications'] if item['kind'] == 'viewpoint_change' and item['post_id'] == 1)
        self.client.delete(f"/api/notifications/{target['id']}")
        self.client.get('/api/analyze/1', params={'use_ai': 'false'})
        remaining = self.client.get('/api/notifications').json()['notifications']
        self.assertFalse(any(item['id'] == target['id'] for item in remaining))

    def test_07_hybrid_api_corrects_both_comments_without_model_calls(self):
        model = Mock()
        with patch('app.stance_engine.load_model', return_value=model):
            data = self.client.get('/api/analyze/1', params={'use_ai': 'true'}).json()
        model.assert_not_called()
        self.assertEqual(data['engine']['transformer_count'], 0)
        self.assertEqual(data['engine']['semantic_guardrail_count'], 2)
        counts = {item['name']: item['comment_count'] for item in data['viewpoints']}
        self.assertEqual(counts, {
            'Koşullu / Dengeli': 10,
            'Karşı / Sınırlayıcı': 2,
            'Destekleyen': 4,
            'Soru / Tarafsız': 4,
        })

    def test_08_other_persistent_modules_remain_available(self):
        for path in ('/api/notifications', '/api/messages', '/api/bookmarks', '/api/lists', '/api/profile'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)
