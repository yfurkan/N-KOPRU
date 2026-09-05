from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

TEST_DB = Path(tempfile.gettempdir()) / 'nkopru_v123_analysis_consistency.db'
os.environ['N_KOPRU_DB_PATH'] = str(TEST_DB)

from fastapi.testclient import TestClient

from app.database import connection, reset_database_for_tests
from app.main import app


class AnalysisConsistencyPersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        reset_database_for_tests()

    def hybrid_analysis(self):
        with patch('app.stance_engine.load_model', return_value=Mock()):
            response = self.client.get('/api/analyze/1', params={'use_ai': 'true'})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def latest_history_id(self):
        return self.client.get('/api/history', params={'post_id': 1}).json()['analyses'][0]['id']

    def test_01_health_reports_v123_and_sqlite(self):
        data = self.client.get('/health').json()
        self.assertEqual(data['version'], '1.5.0')
        self.assertEqual(data['storage'], 'sqlite')

    def test_02_truthful_hybrid_summary_survives_snapshot_reopen(self):
        created = self.hybrid_analysis()
        restored = self.client.get(f'/api/history/{self.latest_history_id()}').json()['analysis']
        self.assertEqual(restored['short_summary'], created['short_summary'])
        self.assertIn('Transformer çıkarımı gerekmedi', restored['short_summary'])

    def test_03_three_contrast_labels_survive_sqlite_snapshot(self):
        created = self.hybrid_analysis()
        restored = self.client.get(f'/api/history/{self.latest_history_id()}').json()['analysis']
        self.assertEqual(restored['bridge']['contrast_viewpoint_labels'], created['bridge']['contrast_viewpoint_labels'])
        self.assertEqual(len(restored['bridge']['contrast_viewpoint_labels']), 3)

    def test_04_localized_question_impacts_survive_sqlite_snapshot(self):
        self.hybrid_analysis()
        restored = self.client.get(f'/api/history/{self.latest_history_id()}').json()['analysis']
        for question in restored['unanswered_questions']:
            self.assertIn('Kontrollü ve kurallı kullanım', question['impact'])
            self.assertNotIn('Koşullu / Dengeli', question['impact'])

    def test_05_unchanged_reanalysis_creates_no_extra_notification(self):
        self.hybrid_analysis()
        before = self.client.get('/api/notifications').json()['total_count']
        self.hybrid_analysis()
        self.assertEqual(self.client.get('/api/notifications').json()['total_count'], before)

    def test_06_legacy_snapshot_without_contrast_metadata_still_opens(self):
        self.hybrid_analysis()
        history_id = self.latest_history_id()
        with connection() as conn:
            row = conn.execute('SELECT analysis_json FROM analysis_history WHERE id = ?', (history_id,)).fetchone()
            payload = json.loads(row['analysis_json'])
            payload['bridge'].pop('contrast_viewpoint_names', None)
            payload['bridge'].pop('contrast_viewpoint_labels', None)
            conn.execute('UPDATE analysis_history SET analysis_json = ? WHERE id = ?', (json.dumps(payload), history_id))
            conn.commit()
        restored = self.client.get(f'/api/history/{history_id}')
        self.assertEqual(restored.status_code, 200)
        self.assertTrue(restored.json()['analysis']['bridge']['bridge_question'])

    def test_07_presentation_only_summary_and_impact_changes_create_no_events(self):
        self.hybrid_analysis()
        history_id = self.latest_history_id()
        with connection() as conn:
            row = conn.execute('SELECT analysis_json FROM analysis_history WHERE id = ?', (history_id,)).fetchone()
            payload = json.loads(row['analysis_json'])
            payload['short_summary'] = 'Eski sürümdeki farklı özet sunumu.'
            payload['unanswered_questions'][0]['impact'] = 'Koşullu / Dengeli ile Karşı / Sınırlayıcı karşılaştırması.'
            conn.execute('UPDATE analysis_history SET analysis_json = ? WHERE id = ?', (json.dumps(payload), history_id))
            conn.commit()
        before = self.client.get('/api/notifications').json()['total_count']
        self.hybrid_analysis()
        self.assertEqual(self.client.get('/api/notifications').json()['total_count'], before)

    def test_08_real_bridge_upgrade_emits_only_one_new_bridge_notification(self):
        self.hybrid_analysis()
        history_id = self.latest_history_id()
        with connection() as conn:
            row = conn.execute('SELECT analysis_json FROM analysis_history WHERE id = ?', (history_id,)).fetchone()
            payload = json.loads(row['analysis_json'])
            payload['bridge']['bridge_question'] = 'Geniş kullanım ile kurallı kullanım hangi ölçütlerle karşılaştırılmalı?'
            conn.execute('UPDATE analysis_history SET analysis_json = ? WHERE id = ?', (json.dumps(payload), history_id))
            conn.commit()
        before = self.client.get('/api/notifications').json()['total_count']
        self.hybrid_analysis()
        after_first = self.client.get('/api/notifications').json()['total_count']
        self.assertEqual(after_first, before + 1)
        self.hybrid_analysis()
        self.assertEqual(self.client.get('/api/notifications').json()['total_count'], after_first)

    def test_09_deleted_bridge_notification_does_not_reappear(self):
        self.hybrid_analysis()
        rows = self.client.get('/api/notifications').json()['notifications']
        target = next(item for item in rows if item['kind'] == 'bridge_update' and item['post_id'] == 1)
        self.client.delete(f"/api/notifications/{target['id']}")
        self.hybrid_analysis()
        after = self.client.get('/api/notifications').json()['notifications']
        self.assertFalse(any(item['id'] == target['id'] for item in after))

    def test_10_engine_execution_and_contrast_metadata_persist(self):
        self.hybrid_analysis()
        restored = self.client.get(f'/api/history/{self.latest_history_id()}').json()['analysis']
        self.assertEqual(restored['engine']['stance_execution_mode'], 'structural-only')
        self.assertFalse(restored['engine']['stance_transformer_used'])
        self.assertEqual(restored['engine']['bridge_contrast_strategy'], 'policy-spectrum')

    def test_11_other_modules_and_short_bridge_remain_available(self):
        result = self.hybrid_analysis()
        self.assertLessEqual(len(result['bridge']['bridge_question'].split()), 28)
        for path in ('/api/messages', '/api/bookmarks', '/api/lists', '/api/profile'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)
