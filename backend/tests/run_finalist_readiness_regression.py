"""v1.5.0: yan etkisiz jüri sunumu hazırlık denetimi."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

TEST_DB = Path(tempfile.gettempdir()) / 'nkopru_v150_readiness_regression.db'
os.environ['N_KOPRU_DB_PATH'] = str(TEST_DB)

from fastapi.testclient import TestClient

from app.database import connection, reset_database_for_tests
from app.main import app


class ReadinessRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for suffix in ('', '-wal', '-shm'):
            try:
                Path(str(TEST_DB) + suffix).unlink()
            except FileNotFoundError:
                pass
        reset_database_for_tests()
        cls.client = TestClient(app)

    def test_01_readiness_endpoint_is_available(self):
        response = self.client.get('/api/system/readiness')
        self.assertEqual(response.status_code, 200)

    def test_02_all_required_checks_are_ready(self):
        data = self.client.get('/api/system/readiness').json()
        self.assertTrue(data['presentation_ready'])
        self.assertEqual(data['required_ready_count'], data['required_check_count'])

    def test_03_required_contract_has_five_checks(self):
        data = self.client.get('/api/system/readiness').json()
        required = [item for item in data['checks'] if item['required']]
        self.assertEqual({item['key'] for item in required}, {'database', 'schema', 'demo', 'analysis', 'bridge'})

    def test_04_database_integrity_is_checked(self):
        data = self.client.get('/api/system/readiness').json()
        check = next(item for item in data['checks'] if item['key'] == 'database')
        self.assertEqual(check['status'], 'ready')
        self.assertIn('bütünlük', check['detail'].casefold())

    def test_05_pilot_schema_is_part_of_readiness(self):
        with connection() as conn:
            tables = {row['name'] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertIn('pilot_sessions', tables)
        self.assertIn('pilot_phase_results', tables)

    def test_06_demo_contract_uses_twenty_unique_comments(self):
        data = self.client.get('/api/system/readiness').json()
        check = next(item for item in data['checks'] if item['key'] == 'demo')
        self.assertIn('20 benzersiz yorum', check['detail'])

    def test_07_bridge_word_limit_is_verified(self):
        data = self.client.get('/api/system/readiness').json()
        check = next(item for item in data['checks'] if item['key'] == 'bridge')
        self.assertEqual(check['status'], 'ready')
        self.assertIn('28 kelimelik sınır', check['detail'])

    def test_08_optional_models_do_not_block_presentation(self):
        data = self.client.get('/api/system/readiness').json()
        optional = [item for item in data['checks'] if not item['required']]
        self.assertEqual({item['key'] for item in optional}, {'stance_model', 'coach_model'})
        self.assertTrue(all(item['status'] in {'ready', 'optional'} for item in optional))
        self.assertTrue(data['presentation_ready'])

    def test_09_readiness_is_side_effect_free_for_history(self):
        with connection() as conn:
            before = int(conn.execute('SELECT COUNT(*) AS count FROM analysis_history').fetchone()['count'])
        self.client.get('/api/system/readiness')
        with connection() as conn:
            after = int(conn.execute('SELECT COUNT(*) AS count FROM analysis_history').fetchone()['count'])
        self.assertEqual(before, after)

    def test_10_status_payload_is_timestamped(self):
        data = self.client.get('/api/system/readiness').json()
        self.assertIn('T', data['checked_at'])
        self.assertEqual(data['status'], 'ready')


if __name__ == '__main__':
    unittest.main(verbosity=2)
