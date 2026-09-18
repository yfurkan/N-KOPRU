from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TEST_DB = Path(tempfile.gettempdir()) / 'nkopru_v121_viewpoints_persistence.db'
os.environ['N_KOPRU_DB_PATH'] = str(TEST_DB)

from fastapi.testclient import TestClient

from app.analyzer import analyze_demo
from app.database import connection, reset_database_for_tests
from app.demo import DEMO_POST
from app.history import record_analysis_snapshot
from app.main import app
from app.notifications import list_notifications, record_analysis


class ViewpointPersistenceRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        reset_database_for_tests()

    def test_01_health_reports_v123_and_sqlite(self):
        data = self.client.get('/health').json()
        self.assertEqual(data['version'], '1.5.0')
        self.assertEqual(data['storage'], 'sqlite')

    def test_02_demo_api_exposes_contextual_cluster_contract(self):
        data = self.client.get('/api/analyze/1', params={'use_ai': 'false'}).json()
        conditional = next(item for item in data['viewpoints'] if item['name'] == 'Koşullu / Dengeli')
        self.assertEqual(conditional['display_name'], 'Kontrollü ve kurallı kullanım')
        self.assertGreater(conditional['comment_count'], 0)
        self.assertTrue(conditional['representative_comments'])
        self.assertTrue(conditional['main_argument'])

    def test_03_enriched_cluster_survives_snapshot_reopen(self):
        created = self.client.get('/api/analyze/1', params={'use_ai': 'false'}).json()
        history_id = self.client.get('/api/history', params={'post_id': 1}).json()['analyses'][0]['id']
        restored = self.client.get(f'/api/history/{history_id}').json()['analysis']
        self.assertEqual(restored['viewpoints'], created['viewpoints'])
        self.assertEqual(restored['engine']['viewpoint_engine'], 'contextual-evidence-grounded-viewpoints')

    def test_04_legacy_snapshot_without_new_fields_reopens(self):
        self.client.get('/api/analyze/1', params={'use_ai': 'false'})
        history_id = self.client.get('/api/history').json()['analyses'][0]['id']
        with connection() as conn:
            raw = conn.execute('SELECT analysis_json FROM analysis_history WHERE id = ?', (history_id,)).fetchone()
            data = json.loads(raw['analysis_json'])
            data['viewpoints'] = [
                {key: item[key] for key in ('name', 'percentage', 'summary')}
                for item in data['viewpoints']
            ]
            conn.execute('UPDATE analysis_history SET analysis_json = ? WHERE id = ?', (json.dumps(data), history_id))
            conn.commit()
        restored = self.client.get(f'/api/history/{history_id}')
        self.assertEqual(restored.status_code, 200)
        viewpoint = restored.json()['analysis']['viewpoints'][0]
        self.assertEqual(viewpoint['display_name'], '')
        self.assertEqual(viewpoint['representative_comments'], [])

    def test_05_old_snapshot_followed_by_new_analysis_has_no_fake_change(self):
        self.client.get('/api/analyze/1', params={'use_ai': 'false'})
        history_id = self.client.get('/api/history').json()['analyses'][0]['id']
        with connection() as conn:
            raw = conn.execute('SELECT analysis_json FROM analysis_history WHERE id = ?', (history_id,)).fetchone()
            data = json.loads(raw['analysis_json'])
            data['viewpoints'] = [
                {key: item[key] for key in ('name', 'percentage', 'summary')}
                for item in data['viewpoints']
            ]
            conn.execute('UPDATE analysis_history SET analysis_json = ? WHERE id = ?', (json.dumps(data), history_id))
            conn.commit()
        count_before = self.client.get('/api/notifications').json()['total_count']
        updated = self.client.get('/api/analyze/1', params={'use_ai': 'false'}).json()
        self.assertEqual(updated['changes_since_last_visit'], ['Önceki analizden bu yana ölçülebilir bir değişiklik tespit edilmedi.'])
        self.assertEqual(self.client.get('/api/notifications').json()['total_count'], count_before)

    def test_06_unchanged_reanalysis_preserves_notification_dedup(self):
        self.client.get('/api/analyze/1', params={'use_ai': 'false'})
        before = self.client.get('/api/notifications').json()['total_count']
        self.client.get('/api/analyze/1', params={'use_ai': 'false'})
        after = self.client.get('/api/notifications').json()['total_count']
        self.assertEqual(before, after)
        self.assertEqual(self.client.get('/api/history', params={'post_id': 1}).json()['count'], 2)

    def test_07_display_label_only_change_is_not_an_event(self):
        first = analyze_demo(use_ai=False)
        first, first_id = record_analysis_snapshot(DEMO_POST, first)
        record_analysis(DEMO_POST, first, history_id=first_id)
        initial = len(list_notifications())

        changed = first.model_copy(deep=True)
        changed.viewpoints[0].display_name = 'Sunum başlığı güncellendi'
        changed.viewpoints[0].main_argument = 'Görüşün yalnızca sunum açıklaması güncellendi.'
        changed, changed_id = record_analysis_snapshot(DEMO_POST, changed)
        self.assertEqual(record_analysis(DEMO_POST, changed, history_id=changed_id), 0)
        self.assertEqual(len(list_notifications()), initial)

    def test_08_deleted_viewpoint_notification_is_not_recreated(self):
        self.client.get('/api/analyze/1', params={'use_ai': 'false'})
        rows = self.client.get('/api/notifications').json()['notifications']
        target = next(item for item in rows if item['post_id'] == 1 and item['kind'] == 'viewpoint_change')
        removed = self.client.delete(f"/api/notifications/{target['id']}")
        self.assertEqual(removed.status_code, 200)
        self.client.get('/api/analyze/1', params={'use_ai': 'false'})
        after = self.client.get('/api/notifications').json()['notifications']
        self.assertFalse(any(item['id'] == target['id'] for item in after))

    def test_09_custom_discussion_preserves_unique_post_and_labels(self):
        payload = {
            'title': 'Mahalle parkı büyütülmeli mi?',
            'comments': [
                'Bu öneriyi destekliyorum, faydalı olur.',
                'Projeye karşıyım, riskli olabilir.',
                'Bütçe ancak belirli şartlarla uygun olabilir.',
                'Bu maliyetin kaynağı nedir?',
            ],
            'use_ai': False,
        }
        created = self.client.post('/api/analyze-discussion', json=payload).json()
        self.assertGreaterEqual(created['post']['id'], 9001)
        self.assertEqual(created['analysis']['engine']['viewpoint_context'], 'general-discussion')
        self.assertFalse(any('yasak' in item['display_name'].casefold() for item in created['analysis']['viewpoints']))

    def test_10_viewpoint_fields_survive_real_process_restart(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix='nkopru_v121_restart_') as temp_dir:
            db_path = Path(temp_dir) / 'restart.db'
            env = os.environ.copy()
            env['N_KOPRU_DB_PATH'] = str(db_path)
            env['PYTHONPATH'] = str(root)
            create_code = """
import json
from fastapi.testclient import TestClient
from app.database import reset_database_for_tests
from app.main import app
reset_database_for_tests()
client = TestClient(app)
result = client.get('/api/analyze/1', params={'use_ai': 'false'}).json()
history = client.get('/api/history').json()['analyses'][0]
cluster = next(item for item in result['viewpoints'] if item['name'] == 'Koşullu / Dengeli')
print(json.dumps({'history_id': history['id'], 'display_name': cluster['display_name']}))
"""
            first = subprocess.run([sys.executable, '-c', create_code], cwd=root, env=env, text=True, capture_output=True, check=True)
            created = json.loads(first.stdout.strip().splitlines()[-1])
            read_code = f"""
import json
from fastapi.testclient import TestClient
from app.main import app
result = TestClient(app).get('/api/history/{created['history_id']}').json()['analysis']
cluster = next(item for item in result['viewpoints'] if item['name'] == 'Koşullu / Dengeli')
print(json.dumps(cluster))
"""
            second = subprocess.run([sys.executable, '-c', read_code], cwd=root, env=env, text=True, capture_output=True, check=True)
            restored = json.loads(second.stdout.strip().splitlines()[-1])
            self.assertEqual(restored['display_name'], created['display_name'])
            self.assertTrue(restored['representative_comments'])
            self.assertGreater(restored['comment_count'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
