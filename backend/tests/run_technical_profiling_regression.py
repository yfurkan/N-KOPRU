import json
import os
import unittest
from statistics import mean, median
from unittest.mock import patch

os.environ.setdefault('N_KOPRU_DB_PATH', '/tmp/nkopru_v132_profiling_regression.db')

from fastapi.testclient import TestClient

from app.analyzer import analyze_post
from app.database import connection, reset_database_for_tests
from app.demo import DEMO_POST
from app.evaluation import PROFILE_STAGES, RESULT_META_KEY, _percentile
from app.main import app


class TechnicalProfilingRegressionTests(unittest.TestCase):
    def setUp(self):
        reset_database_for_tests()
        self.client = TestClient(app)

    def measure(self, *, iterations=2, use_ai=False):
        response = self.client.post('/api/evaluation/run', json={
            'iterations': iterations,
            'use_ai': use_ai,
        })
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def model_measure(self, *, iterations=2):
        def model(sequences, candidate_labels, **kwargs):
            rows = sequences if isinstance(sequences, list) else [sequences]
            return [{'labels': [candidate_labels[0]], 'scores': [0.91]} for _ in rows]

        with patch('app.stance_engine._PIPELINE', model), patch(
            'app.stance_engine.dependencies_installed', return_value=True
        ):
            return self.measure(iterations=iterations, use_ai=True)

    def store_legacy(self):
        measured = self.measure(iterations=1)
        legacy = {
            key: value for key, value in measured.items()
            if key not in {'stage_profile', 'model_usage', 'hardware'}
        }
        legacy['version'] = '1.3.1'
        with connection() as conn:
            conn.execute(
                'UPDATE app_meta SET value = ? WHERE key = ?',
                (json.dumps(legacy, ensure_ascii=False), RESULT_META_KEY),
            )
        return legacy

    def test_01_new_version_is_consistent(self):
        self.assertEqual(self.client.get('/health').json()['version'], '1.5.0')
        self.assertEqual(self.client.get('/api/evaluation').json()['version'], '1.5.0')
        self.assertEqual(self.measure()['version'], '1.5.0')

    def test_02_six_real_stages_have_stable_order(self):
        stages = self.measure()['stage_profile']['stages']
        self.assertEqual([(item['key'], item['label']) for item in stages], list(PROFILE_STAGES))

    def test_03_profile_reports_requested_iteration_count(self):
        profile = self.measure(iterations=3)['stage_profile']
        self.assertTrue(profile['available'])
        self.assertEqual(profile['iterations'], 3)

    def test_04_every_stage_has_one_sample_per_analysis(self):
        for stage in self.measure(iterations=4)['stage_profile']['stages']:
            self.assertEqual(len(stage['samples_ms']), 4)

    def test_05_stage_samples_are_not_negative(self):
        for stage in self.measure()['stage_profile']['stages']:
            self.assertTrue(all(value >= 0 for value in stage['samples_ms']))

    def test_06_stage_median_comes_from_real_samples(self):
        for stage in self.measure(iterations=3)['stage_profile']['stages']:
            self.assertEqual(stage['median_ms'], round(median(stage['samples_ms']), 3))

    def test_07_stage_mean_comes_from_real_samples(self):
        for stage in self.measure(iterations=3)['stage_profile']['stages']:
            self.assertAlmostEqual(stage['mean_ms'], mean(stage['samples_ms']), places=3)

    def test_08_stage_minimum_and_maximum_are_real(self):
        for stage in self.measure(iterations=3)['stage_profile']['stages']:
            self.assertEqual(stage['minimum_ms'], min(stage['samples_ms']))
            self.assertEqual(stage['maximum_ms'], max(stage['samples_ms']))

    def test_09_stage_p95_is_computed_from_samples(self):
        for stage in self.measure(iterations=4)['stage_profile']['stages']:
            self.assertEqual(stage['p95_ms'], _percentile(stage['samples_ms'], 0.95))

    def test_10_share_is_based_on_measured_total_median(self):
        data = self.measure(iterations=3)
        total = data['latency']['median_ms']
        for stage in data['stage_profile']['stages']:
            self.assertEqual(
                stage['share_of_total_percent'],
                round(stage['median_ms'] * 100 / total, 1),
            )

    def test_11_bottleneck_is_slowest_measured_stage(self):
        profile = self.measure(iterations=3)['stage_profile']
        expected = max(profile['stages'], key=lambda item: (item['median_ms'], item['mean_ms']))
        self.assertIsNotNone(profile['bottleneck'])
        self.assertEqual(profile['bottleneck']['key'], expected['key'])

    def test_12_overhead_has_one_measured_remainder_per_run(self):
        profile = self.measure(iterations=3)['stage_profile']
        self.assertEqual(len(profile['overhead_samples_ms']), 3)
        self.assertTrue(all(value >= 0 for value in profile['overhead_samples_ms']))

    def test_13_overhead_median_comes_from_remainders(self):
        profile = self.measure(iterations=3)['stage_profile']
        self.assertEqual(
            profile['overhead_median_ms'],
            round(median(profile['overhead_samples_ms']), 3),
        )

    def test_14_profile_note_discloses_untracked_work(self):
        note = self.measure()['stage_profile']['note']
        self.assertIn('Kalan süre', note)
        self.assertIn('sonuç nesnesi', note)

    def test_15_normal_analysis_also_exposes_real_stage_timers(self):
        result = analyze_post(DEMO_POST, demo_mode=True, use_ai=False)
        self.assertEqual(set(result.engine['stage_profile_ms']), {key for key, _ in PROFILE_STAGES})

    def test_16_heuristic_demo_has_no_fake_model_usage(self):
        usage = self.measure()['model_usage']['demo']
        self.assertEqual(usage['stance_transformer_total'], 0)
        self.assertEqual(usage['claim_transformer_total'], 0)
        self.assertEqual(usage['transformer_total'], 0)

    def test_17_ready_model_still_has_no_internal_stance_inference(self):
        usage = self.model_measure()['model_usage']['internal_set']
        self.assertEqual(usage['stance_transformer_count'], 0)
        self.assertEqual(usage['structural_decision_count'], 20)

    def test_18_ready_model_runs_demo_claim_inference(self):
        usage = self.model_measure()['model_usage']['demo']
        self.assertEqual(usage['stance_transformer_per_run'], 0)
        self.assertEqual(usage['cold_claim_transformer_count'], 1)
        self.assertEqual(usage['claim_transformer_per_run'], 0)

    def test_19_claim_inference_identifies_actual_demo_comment(self):
        usage = self.model_measure()['model_usage']['demo']
        self.assertEqual(usage['claim_transformer_comment_ids'], [8])

    def test_20_claim_inference_total_scales_with_real_runs(self):
        usage = self.model_measure(iterations=4)['model_usage']['demo']
        self.assertEqual(usage['claim_transformer_counts'], [1, 0, 0, 0])
        self.assertEqual(usage['claim_transformer_total'], 1)
        self.assertEqual(usage['claim_cache_hit_counts'], [0, 1, 1, 1])

    def test_21_demo_transformer_total_is_sum_of_layers(self):
        usage = self.model_measure(iterations=3)['model_usage']['demo']
        self.assertEqual(
            usage['transformer_total'],
            usage['stance_transformer_total'] + usage['claim_transformer_total'],
        )

    def test_22_claim_stage_uses_actual_model_count(self):
        stage = next(item for item in self.model_measure(iterations=3)['stage_profile']['stages'] if item['key'] == 'claims')
        self.assertEqual(stage['transformer_inference_counts'], [1, 0, 0])
        self.assertEqual(stage['transformer_inference_total'], 1)
        self.assertEqual(stage['cache_hit_counts'], [0, 1, 1])

    def test_23_stance_stage_does_not_borrow_claim_model_count(self):
        stage = next(item for item in self.model_measure()['stage_profile']['stages'] if item['key'] == 'stance')
        self.assertEqual(stage['transformer_inference_total'], 0)

    def test_24_non_model_stages_do_not_invent_inference(self):
        for stage in self.model_measure()['stage_profile']['stages']:
            if stage['key'] not in {'stance', 'claims'}:
                self.assertEqual(stage['transformer_inference_total'], 0)

    def test_25_internal_and_demo_model_scopes_are_distinct(self):
        usage = self.model_measure()['model_usage']
        self.assertEqual(usage['internal_set']['total_transformer_count'], 0)
        self.assertGreater(usage['demo']['transformer_total'], 0)

    def test_26_model_note_explains_zero_stance_does_not_mean_zero_pipeline(self):
        self.assertIn('tüm analiz hattında Transformer kullanılmadığı anlamına gelmez', self.model_measure()['model_usage']['note'])

    def test_27_model_comment_ids_are_not_invented_in_heuristic_mode(self):
        self.assertEqual(self.measure()['model_usage']['demo']['claim_transformer_comment_ids'], [])

    def test_28_saved_result_preserves_profile(self):
        measured = self.measure()
        saved = self.client.get('/api/evaluation').json()['latest_result']
        self.assertEqual(saved['stage_profile'], measured['stage_profile'])

    def test_29_saved_result_preserves_model_usage(self):
        measured = self.model_measure()
        saved = self.client.get('/api/evaluation').json()['latest_result']
        self.assertEqual(saved['model_usage'], measured['model_usage'])

    def test_30_legacy_result_is_read_without_crashing(self):
        original = self.store_legacy()
        restored = self.client.get('/api/evaluation').json()['latest_result']
        self.assertEqual(restored['run_id'], original['run_id'])
        self.assertEqual(restored['version'], '1.3.1')

    def test_31_legacy_profile_is_marked_unmeasured(self):
        self.store_legacy()
        profile = self.client.get('/api/evaluation').json()['latest_result']['stage_profile']
        self.assertFalse(profile['available'])
        self.assertEqual(profile['stages'], [])
        self.assertIsNone(profile['bottleneck'])

    def test_32_legacy_demo_model_counts_are_unknown_not_zero(self):
        self.store_legacy()
        usage = self.client.get('/api/evaluation').json()['latest_result']['model_usage']
        self.assertIsNone(usage['demo']['claim_transformer_per_run'])
        self.assertIsNone(usage['demo']['transformer_total'])
        self.assertIsNone(usage['internal_set']['claim_transformer_count'])

    def test_33_legacy_normalization_does_not_rewrite_sqlite(self):
        self.store_legacy()
        with connection() as conn:
            before = conn.execute('SELECT value FROM app_meta WHERE key = ?', (RESULT_META_KEY,)).fetchone()['value']
        self.client.get('/api/evaluation')
        with connection() as conn:
            after = conn.execute('SELECT value FROM app_meta WHERE key = ?', (RESULT_META_KEY,)).fetchone()['value']
        self.assertEqual(before, after)

    def test_34_hardware_diagnostics_are_visible_before_first_measurement(self):
        status = self.client.get('/api/evaluation').json()
        self.assertIn('hardware', status)
        self.assertIn('diagnosis', status['hardware'])

    def test_35_hardware_snapshot_is_stored_with_actual_measurement(self):
        measured = self.measure()
        saved = self.client.get('/api/evaluation').json()['latest_result']
        self.assertEqual(saved['hardware'], measured['hardware'])

    def test_36_profile_preserves_nine_existing_demo_invariants(self):
        result = self.model_measure()
        self.assertEqual(result['invariant_count'], 9)
        self.assertEqual(result['passed_invariant_count'], 9)


if __name__ == '__main__':
    unittest.main(verbosity=2)
