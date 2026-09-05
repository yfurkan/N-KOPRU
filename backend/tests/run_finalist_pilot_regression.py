"""v1.5.0: anonim, karşı dengelenmiş kullanıcı etki pilotu."""
from __future__ import annotations

import csv
import io
import os
import tempfile
import unittest
from pathlib import Path

TEST_DB = Path(tempfile.gettempdir()) / 'nkopru_v150_pilot_regression.db'
os.environ['N_KOPRU_DB_PATH'] = str(TEST_DB)

from fastapi.testclient import TestClient

from app.database import connection, reset_database_for_tests
from app.main import app
from app.pilot import MINIMUM_SAMPLE_SIZE, PROTOCOL_VERSION, SCENARIOS, _analysis_payload


def clear_test_database() -> None:
    for suffix in ('', '-wal', '-shm'):
        try:
            Path(str(TEST_DB) + suffix).unlink()
        except FileNotFoundError:
            pass
    reset_database_for_tests()


class PilotApiTests(unittest.TestCase):
    def setUp(self):
        clear_test_database()
        self.client = TestClient(app)

    def start(self, *, practice: bool = False):
        response = self.client.post('/api/pilot/sessions', json={'consent': True, 'practice': practice})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def submit_correct(self, session: dict, duration_ms: int = 5000):
        phase = session['current_phase']
        correct = int(SCENARIOS[phase['scenario_key']]['correct_answer'])
        response = self.client.post(
            f"/api/pilot/sessions/{session['session_id']}/phases",
            json={
                'phase_index': phase['phase_index'],
                'selected_answer': correct,
                'duration_ms': duration_ms,
                'clarity_rating': 4,
                'confidence_rating': 4,
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def complete(self, *, practice: bool = False, raw_ms: int = 9000, nkopru_ms: int = 5000):
        session = self.start(practice=practice)
        while not session['completed']:
            phase = session['current_phase']
            duration = nkopru_ms if phase['variant'] == 'nkopru' else raw_ms
            session = self.submit_correct(session, duration)['session']
        return session

    def test_01_consent_is_mandatory(self):
        response = self.client.post('/api/pilot/sessions', json={'consent': False, 'practice': True})
        self.assertEqual(response.status_code, 400)
        self.assertIn('onay', response.json()['detail'].casefold())

    def test_02_first_assignment_is_ab_and_counterbalanced(self):
        first = self.start(practice=True)
        second = self.start(practice=True)
        self.assertEqual(first['assignment'], 'AB')
        self.assertEqual(second['assignment'], 'BA')

    def test_03_raw_phase_contains_comments_but_no_analysis(self):
        phase = self.start(practice=True)['current_phase']
        self.assertEqual(phase['variant'], 'raw')
        self.assertEqual(len(phase['comments']), 8)
        self.assertIsNone(phase['analysis'])

    def test_04_nkopru_phase_contains_real_analysis_output(self):
        first = self.start(practice=True)
        second = self.start(practice=True)
        self.assertEqual(second['current_phase']['variant'], 'nkopru')
        analysis = second['current_phase']['analysis']
        self.assertTrue(analysis['short_summary'])
        self.assertTrue(analysis['main_divergence'])
        self.assertTrue(analysis['bridge_question'])
        self.assertGreaterEqual(len(analysis['viewpoints']), 2)

    def test_05_duration_and_ratings_are_server_validated(self):
        session = self.start(practice=True)
        response = self.client.post(
            f"/api/pilot/sessions/{session['session_id']}/phases",
            json={'phase_index': 0, 'selected_answer': 1, 'duration_ms': 10, 'clarity_rating': 6, 'confidence_rating': 0},
        )
        self.assertEqual(response.status_code, 422)

    def test_06_phases_cannot_be_submitted_out_of_order(self):
        session = self.start(practice=True)
        response = self.client.post(
            f"/api/pilot/sessions/{session['session_id']}/phases",
            json={'phase_index': 1, 'selected_answer': 2, 'duration_ms': 5000, 'clarity_rating': 4, 'confidence_rating': 4},
        )
        self.assertEqual(response.status_code, 400)

    def test_07_first_result_moves_to_other_variant(self):
        session = self.start(practice=True)
        response = self.submit_correct(session)
        self.assertTrue(response['result']['correct'])
        self.assertEqual(response['session']['completed_phase_count'], 1)
        self.assertEqual(response['session']['current_phase']['variant'], 'nkopru')

    def test_08_phase_submission_is_idempotent(self):
        session = self.start(practice=True)
        first = self.submit_correct(session)
        retry = self.client.post(
            f"/api/pilot/sessions/{session['session_id']}/phases",
            json={'phase_index': 0, 'selected_answer': 0, 'duration_ms': 7000, 'clarity_rating': 1, 'confidence_rating': 1},
        )
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(retry.json()['result'], first['result'])
        with connection() as conn:
            count = conn.execute('SELECT COUNT(*) AS count FROM pilot_phase_results').fetchone()['count']
        self.assertEqual(count, 1)

    def test_09_two_phases_complete_session(self):
        session = self.complete(practice=True)
        self.assertTrue(session['completed'])
        self.assertEqual(session['completed_phase_count'], 2)
        self.assertIsNone(session['current_phase'])

    def test_10_unknown_session_is_404(self):
        response = self.client.get('/api/pilot/sessions/999999')
        self.assertEqual(response.status_code, 404)

    def test_11_practice_session_never_changes_real_metrics(self):
        self.complete(practice=True)
        overview = self.client.get('/api/pilot').json()
        self.assertEqual(overview['practice_session_count'], 1)
        self.assertEqual(overview['completed_session_count'], 0)
        self.assertEqual(overview['raw']['completed_task_count'], 0)

    def test_12_only_completed_real_pairs_enter_metrics(self):
        self.start(practice=False)
        overview = self.client.get('/api/pilot').json()
        self.assertEqual(overview['active_session_count'], 1)
        self.assertEqual(overview['completed_session_count'], 0)

    def test_13_real_pair_produces_observed_metrics(self):
        self.complete(practice=False, raw_ms=10_000, nkopru_ms=5_000)
        overview = self.client.get('/api/pilot').json()
        self.assertEqual(overview['completed_session_count'], 1)
        self.assertEqual(overview['raw']['median_duration_ms'], 10_000)
        self.assertEqual(overview['nkopru']['median_duration_ms'], 5_000)
        self.assertEqual(overview['time_gain_percent'], 50.0)
        self.assertEqual(overview['raw']['accuracy_percent'], 100.0)

    def test_14_no_conclusion_before_minimum_sample(self):
        self.complete(practice=False)
        overview = self.client.get('/api/pilot').json()
        self.assertFalse(overview['minimum_sample_reached'])
        self.assertIn('Sonuç çıkarılmadı', overview['conclusion'])

    def test_15_minimum_sample_is_enforced(self):
        for _ in range(MINIMUM_SAMPLE_SIZE):
            self.complete(practice=False)
        overview = self.client.get('/api/pilot').json()
        self.assertTrue(overview['minimum_sample_reached'])
        self.assertEqual(overview['completed_session_count'], MINIMUM_SAMPLE_SIZE)
        self.assertIn('betimsel', overview['conclusion'])

    def test_16_csv_contains_only_complete_real_pairs(self):
        self.complete(practice=True)
        self.complete(practice=False)
        response = self.client.get('/api/pilot/results.csv')
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.headers['content-disposition'])
        rows = list(csv.DictReader(io.StringIO(response.text)))
        self.assertEqual(len(rows), 2)
        self.assertEqual({row['protocol_version'] for row in rows}, {PROTOCOL_VERSION})
        self.assertEqual({row['variant'] for row in rows}, {'raw', 'nkopru'})

    def test_17_storage_contains_no_name_or_email_columns(self):
        with connection() as conn:
            columns = {row['name'] for row in conn.execute('PRAGMA table_info(pilot_sessions)')}
        self.assertNotIn('name', columns)
        self.assertNotIn('email', columns)
        self.assertIn('participant_code', columns)


class PilotScenarioTests(unittest.TestCase):
    def test_18_protocol_has_two_parallel_scenarios(self):
        self.assertEqual(set(SCENARIOS), {'night-transport', 'park-hours'})

    def test_19_each_scenario_has_eight_comments(self):
        self.assertTrue(all(len(item['comments']) == 8 for item in SCENARIOS.values()))

    def test_20_each_scenario_has_four_choices(self):
        self.assertTrue(all(len(item['choices']) == 4 for item in SCENARIOS.values()))

    def test_21_transport_analysis_names_actual_topic(self):
        payload = _analysis_payload('night-transport')
        self.assertIn('ulaşım', payload['short_summary'].casefold())
        self.assertIn('ulaşım', payload['main_divergence'].casefold())

    def test_22_park_analysis_names_actual_topic(self):
        payload = _analysis_payload('park-hours')
        self.assertIn('park', payload['short_summary'].casefold())
        self.assertIn('park', payload['main_divergence'].casefold())

    def test_23_pilot_bridge_questions_remain_compact(self):
        for key in SCENARIOS:
            self.assertLessEqual(len(_analysis_payload(key)['bridge_question'].split()), 28)

    def test_24_analysis_payload_exposes_no_comment_author(self):
        for key in SCENARIOS:
            payload = _analysis_payload(key)
            self.assertNotIn('author', str(payload).casefold())


if __name__ == '__main__':
    unittest.main(verbosity=2)
