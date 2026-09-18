from __future__ import annotations

import json
import os
import unittest
from statistics import median
from unittest.mock import patch

os.environ.setdefault('N_KOPRU_DB_PATH', '/tmp/nkopru_v133_cache_evaluation.db')

from fastapi.testclient import TestClient

from app.analyzer import analyze_post
from app.claim_cache import CACHE_MAX_ENTRIES, claim_cache_size, clear_claim_cache
from app.database import connection, reset_database_for_tests
from app.demo import DEMO_POST
from app.evaluation import RESULT_META_KEY, _percentile
from app.main import app


class EvaluationModel:
    def __init__(self):
        self.calls = []

    def __call__(self, sequences, candidate_labels, **kwargs):
        rows = sequences if isinstance(sequences, list) else [sequences]
        self.calls.extend(rows)
        return [{'labels': [candidate_labels[0]], 'scores': [0.94]} for _ in rows]


class ClaimCacheEvaluationRegressionTests(unittest.TestCase):
    def setUp(self):
        reset_database_for_tests()
        clear_claim_cache()
        self.client = TestClient(app)
        self.model = EvaluationModel()
        self.pipeline_patch = patch('app.stance_engine._PIPELINE', self.model)
        self.dependency_patch = patch('app.stance_engine.dependencies_installed', return_value=True)
        self.pipeline_patch.start()
        self.dependency_patch.start()
        self.addCleanup(self.pipeline_patch.stop)
        self.addCleanup(self.dependency_patch.stop)
        self.addCleanup(clear_claim_cache)

    def measure(self, iterations=5, use_ai=True):
        response = self.client.post('/api/evaluation/run', json={
            'iterations': iterations,
            'use_ai': use_ai,
        })
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_01_health_reports_v133(self):
        self.assertEqual(self.client.get('/health').json()['version'], '1.5.0')

    def test_02_first_demo_analysis_is_real_cold_model_run(self):
        usage = self.measure()['model_usage']['demo']
        self.assertEqual(usage['cold_claim_transformer_count'], 1)

    def test_03_remaining_analyses_use_cached_decision(self):
        self.assertEqual(self.measure()['model_usage']['demo']['claim_transformer_counts'], [1, 0, 0, 0, 0])

    def test_04_cache_hits_are_real_per_run_counts(self):
        self.assertEqual(self.measure()['cache_profile']['hit_counts'], [0, 1, 1, 1, 1])

    def test_05_cache_misses_are_real_per_run_counts(self):
        self.assertEqual(self.measure()['cache_profile']['miss_counts'], [1, 0, 0, 0, 0])

    def test_06_only_one_model_inference_occurs_across_five_runs(self):
        self.assertEqual(self.measure()['model_usage']['demo']['claim_transformer_total'], 1)

    def test_07_four_model_inferences_are_avoided(self):
        self.assertEqual(self.measure()['cache_profile']['avoided_model_inference_count'], 4)

    def test_08_hit_rate_comes_from_measured_hits_and_misses(self):
        self.assertEqual(self.measure()['cache_profile']['hit_rate_percent'], 80.0)

    def test_09_cold_latency_equals_first_actual_sample(self):
        latency = self.measure()['latency']
        self.assertEqual(latency['cold_ms'], latency['samples_ms'][0])

    def test_10_warm_samples_are_actual_remaining_samples(self):
        latency = self.measure()['latency']
        self.assertEqual(latency['warm_samples_ms'], latency['samples_ms'][1:])

    def test_11_warm_median_is_computed_from_real_samples(self):
        latency = self.measure()['latency']
        self.assertEqual(latency['warm_median_ms'], round(median(latency['warm_samples_ms']), 2))

    def test_12_warm_p95_is_computed_from_real_samples(self):
        latency = self.measure()['latency']
        self.assertEqual(latency['warm_p95_ms'], _percentile(latency['warm_samples_ms'], 0.95))

    def test_13_speedup_uses_actual_cold_and_unrounded_warm_values(self):
        latency = self.measure()['latency']
        self.assertIsNotNone(latency['speedup_factor'])
        self.assertGreater(latency['speedup_factor'], 0)

    def test_14_single_iteration_does_not_invent_warm_measurement(self):
        latency = self.measure(iterations=1)['latency']
        self.assertIsNone(latency['warm_median_ms'])
        self.assertIsNone(latency['warm_p95_ms'])
        self.assertIsNone(latency['speedup_factor'])

    def test_15_single_iteration_has_no_warm_samples(self):
        self.assertEqual(self.measure(iterations=1)['latency']['warm_samples_ms'], [])

    def test_16_cache_profile_declares_process_memory_only(self):
        cache = self.measure()['cache_profile']
        self.assertEqual(cache['storage'], 'process-memory')
        self.assertFalse(cache['persistent'])

    def test_17_cache_profile_declares_actual_bound(self):
        self.assertEqual(self.measure()['cache_profile']['max_entries'], CACHE_MAX_ENTRIES)

    def test_18_cache_profile_note_discloses_key_scope(self):
        note = self.measure()['cache_profile']['note']
        self.assertIn('aynı model', note)
        self.assertIn('tartışma başlığı', note)
        self.assertIn('SQLite', note)

    def test_19_claim_stage_exposes_cold_sample(self):
        stage = next(x for x in self.measure()['stage_profile']['stages'] if x['key'] == 'claims')
        self.assertEqual(stage['cold_ms'], stage['samples_ms'][0])

    def test_20_claim_stage_exposes_warm_median(self):
        stage = next(x for x in self.measure()['stage_profile']['stages'] if x['key'] == 'claims')
        self.assertEqual(stage['warm_median_ms'], round(median(stage['samples_ms'][1:]), 3))

    def test_21_claim_stage_counts_actual_cache_hits(self):
        stage = next(x for x in self.measure()['stage_profile']['stages'] if x['key'] == 'claims')
        self.assertEqual((stage['cache_hit_counts'], stage['cache_hit_total']), ([0, 1, 1, 1, 1], 4))

    def test_22_unrelated_stages_do_not_invent_cache_hits(self):
        for stage in self.measure()['stage_profile']['stages']:
            if stage['key'] != 'claims':
                self.assertEqual(stage['cache_hit_total'], 0)

    def test_23_cold_bottleneck_is_measured_not_hardcoded(self):
        profile = self.measure()['stage_profile']
        expected = max(profile['stages'], key=lambda item: (item['cold_ms'], item['mean_ms']))
        self.assertEqual(profile['cold_bottleneck']['key'], expected['key'])

    def test_24_model_comment_is_tracked_across_cold_and_warm_runs(self):
        demo = self.measure()['model_usage']['demo']
        self.assertEqual(demo['claim_model_comment_ids'], [8])
        self.assertEqual(demo['claim_cache_comment_ids'], [8])

    def test_25_last_run_does_not_claim_fresh_model_inference(self):
        self.assertEqual(self.measure()['model_usage']['demo']['claim_transformer_per_run'], 0)

    def test_26_warm_counts_remain_distinct_from_actual_inference(self):
        demo = self.measure()['model_usage']['demo']
        self.assertEqual(demo['warm_claim_transformer_counts'], [0, 0, 0, 0])
        self.assertEqual(demo['warm_claim_cache_hit_total'], 4)

    def test_27_existing_hot_demo_cache_is_reset_only_for_cold_measurement(self):
        analyze_post(DEMO_POST, demo_mode=True, use_ai=True)
        self.model.calls.clear()
        measured = self.measure()
        self.assertEqual(measured['model_usage']['demo']['claim_transformer_counts'], [1, 0, 0, 0, 0])

    def test_28_repeated_measurement_always_starts_with_true_cold_sample(self):
        self.measure()
        second = self.measure()
        self.assertEqual(second['model_usage']['demo']['claim_transformer_counts'][0], 1)

    def test_29_heuristic_mode_never_fabricates_cache_hits(self):
        cache = self.measure(use_ai=False)['cache_profile']
        self.assertEqual((cache['hit_total'], cache['miss_total']), (0, 0))

    def test_30_cache_profile_is_preserved_in_sqlite_result(self):
        measured = self.measure()
        saved = self.client.get('/api/evaluation').json()['latest_result']
        self.assertEqual(saved['cache_profile'], measured['cache_profile'])

    def test_31_cache_entries_themselves_are_not_saved_in_sqlite(self):
        self.measure()
        with connection() as conn:
            tables = [row['name'] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        self.assertFalse(any('cache' in name for name in tables))
        self.assertGreater(claim_cache_size(), 0)

    def test_32_legacy_v132_result_remains_readable(self):
        measured = self.measure()
        legacy = dict(measured)
        legacy.pop('cache_profile')
        legacy['version'] = '1.3.2'
        with connection() as conn:
            conn.execute('UPDATE app_meta SET value = ? WHERE key = ?',
                         (json.dumps(legacy, ensure_ascii=False), RESULT_META_KEY))
        restored = self.client.get('/api/evaluation').json()['latest_result']
        self.assertEqual(restored['version'], '1.3.2')
        self.assertFalse(restored['cache_profile']['available'])

    def test_33_legacy_cache_numbers_are_unknown_not_zero(self):
        measured = self.measure()
        legacy = dict(measured)
        legacy.pop('cache_profile')
        with connection() as conn:
            conn.execute('UPDATE app_meta SET value = ? WHERE key = ?',
                         (json.dumps(legacy, ensure_ascii=False), RESULT_META_KEY))
        cache = self.client.get('/api/evaluation').json()['latest_result']['cache_profile']
        self.assertIsNone(cache['hit_total'])
        self.assertIsNone(cache['cold_ms'])

    def test_34_all_nine_existing_invariants_are_still_valid(self):
        measured = self.measure()
        self.assertEqual((measured['passed_invariant_count'], measured['invariant_count']), (9, 9))

    def test_35_cold_and_warm_decisions_do_not_change_accuracy(self):
        measured = self.measure()
        self.assertEqual((measured['accuracy'], measured['macro_f1']), (1.0, 1.0))

    def test_36_model_usage_note_does_not_count_cache_as_inference(self):
        self.assertIn('yeni çıkarım sayılmaz', self.measure()['model_usage']['note'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
