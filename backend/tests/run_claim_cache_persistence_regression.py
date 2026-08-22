from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault('N_KOPRU_DB_PATH', '/tmp/nkopru_v133_cache_persistence.db')

from fastapi.testclient import TestClient

from app.claim_cache import claim_cache_size, clear_claim_cache
from app.database import connection, reset_database_for_tests
from app.main import app


class PersistenceModel:
    def __init__(self):
        self.calls = []

    def __call__(self, sequences, candidate_labels, **kwargs):
        rows = sequences if isinstance(sequences, list) else [sequences]
        self.calls.extend(rows)
        return [{'labels': [candidate_labels[0]], 'scores': [0.91]} for _ in rows]


class ClaimCachePersistenceRegressionTests(unittest.TestCase):
    def setUp(self):
        reset_database_for_tests()
        clear_claim_cache()
        self.client = TestClient(app)
        self.model = PersistenceModel()
        self.pipeline_patch = patch('app.stance_engine._PIPELINE', self.model)
        self.dependency_patch = patch('app.stance_engine.dependencies_installed', return_value=True)
        self.pipeline_patch.start()
        self.dependency_patch.start()
        self.addCleanup(self.pipeline_patch.stop)
        self.addCleanup(self.dependency_patch.stop)
        self.addCleanup(clear_claim_cache)

    def analyze(self):
        response = self.client.get('/api/analyze/1?use_ai=true')
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def append(self, text):
        response = self.client.post('/api/posts/1/comments', json={'text': text, 'use_ai': True})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def table_count(self, table):
        with connection() as conn:
            return int(conn.execute(f'SELECT COUNT(*) AS count FROM {table}').fetchone()['count'])

    def test_01_real_api_first_analysis_reports_fresh_claim_inference(self):
        self.assertEqual(self.analyze()['engine']['claim_transformer_count'], 1)

    def test_02_real_api_second_analysis_reports_cache_hit(self):
        self.analyze()
        second = self.analyze()['engine']
        self.assertEqual((second['claim_transformer_count'], second['claim_cache_hit_count']), (0, 1))

    def test_03_cold_and_warm_claims_are_identical(self):
        first = self.analyze()
        second = self.analyze()
        self.assertEqual(first['claims'], second['claims'])

    def test_04_cold_and_warm_question_results_are_identical(self):
        first = self.analyze()
        second = self.analyze()
        self.assertEqual(first['unanswered_questions'], second['unanswered_questions'])

    def test_05_cold_and_warm_viewpoint_results_are_identical(self):
        first = self.analyze()
        second = self.analyze()
        self.assertEqual(first['viewpoints'], second['viewpoints'])

    def test_06_cold_and_warm_bridge_results_are_identical(self):
        first = self.analyze()
        second = self.analyze()
        self.assertEqual(first['bridge'], second['bridge'])

    def test_07_cold_and_warm_common_ground_is_identical(self):
        first = self.analyze()
        second = self.analyze()
        self.assertEqual(first['common_ground_details'], second['common_ground_details'])

    def test_08_cached_analysis_keeps_source_awareness_at_twenty_five(self):
        self.analyze()
        self.assertEqual(self.analyze()['indicators']['source_awareness'], 25)

    def test_09_cached_analysis_does_not_duplicate_notifications(self):
        self.analyze()
        before = self.client.get('/api/notifications').json()['total_count']
        self.analyze()
        after = self.client.get('/api/notifications').json()['total_count']
        self.assertEqual(before, after)

    def test_10_deleted_notification_does_not_reappear_after_cache_hit(self):
        self.analyze()
        rows = self.client.get('/api/notifications').json()['notifications']
        removed = rows[0]['id']
        self.client.delete(f'/api/notifications/{removed}')
        self.analyze()
        ids = {row['id'] for row in self.client.get('/api/notifications').json()['notifications']}
        self.assertNotIn(removed, ids)

    def test_11_cached_user_analysis_still_creates_one_requested_snapshot(self):
        self.analyze()
        before = self.table_count('analysis_history')
        self.analyze()
        self.assertEqual(self.table_count('analysis_history'), before + 1)

    def test_12_snapshot_comparison_recognizes_cached_analysis_as_unchanged(self):
        self.analyze()
        second = self.analyze()
        self.assertIn('ölçülebilir bir değişiklik tespit edilmedi',
                      ' '.join(second['changes_since_last_visit']))

    def test_13_new_structural_comment_reuses_existing_claim_model_decision(self):
        self.analyze()
        added = self.append('Yapay zekâ kullanımında açık kurallar belirlenmeli.')
        engine = added['analysis']['engine']
        self.assertEqual((engine['claim_transformer_count'], engine['claim_cache_hit_count']), (0, 1))

    def test_14_new_ambiguous_comment_evaluates_only_new_claim(self):
        self.analyze()
        added = self.append('Bazı öğrenciler farklı araçlarla bütün projelerini hazırlatıyor.')
        engine = added['analysis']['engine']
        self.assertEqual((engine['claim_transformer_count'], engine['claim_cache_hit_count']), (1, 1))
        self.assertEqual(engine['claim_transformer_comment_ids'], [81])

    def test_15_new_live_comment_remains_persisted_in_sqlite(self):
        self.analyze()
        self.append('Bazı öğrenciler farklı araçlarla bütün projelerini hazırlatıyor.')
        self.assertEqual(len(self.client.get('/api/posts/demo').json()['comments']), 81)

    def test_16_cache_clear_does_not_remove_sqlite_snapshots(self):
        self.analyze()
        count = self.table_count('analysis_history')
        clear_claim_cache()
        self.assertEqual(self.table_count('analysis_history'), count)

    def test_17_cache_clear_forces_fresh_model_without_changing_claim_result(self):
        first = self.analyze()
        clear_claim_cache()
        fresh = self.analyze()
        self.assertEqual(fresh['engine']['claim_transformer_count'], 1)
        self.assertEqual(first['claims'], fresh['claims'])

    def test_18_cache_entries_are_not_a_new_sqlite_table(self):
        self.analyze()
        self.assertGreater(claim_cache_size(), 0)
        with connection() as conn:
            tables = {row['name'] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertFalse(any('cache' in name for name in tables))

    def test_19_cached_claim_engine_remains_hybrid(self):
        self.analyze()
        self.assertEqual(self.analyze()['engine']['claim_engine'], 'hybrid-semantic-claim')

    def test_20_heuristic_analysis_never_reuses_ai_decision(self):
        self.analyze()
        response = self.client.get('/api/analyze/1?use_ai=false').json()['engine']
        self.assertEqual((response['claim_transformer_count'], response['claim_cache_hit_count']), (0, 0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
