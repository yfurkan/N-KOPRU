from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
TYPES = (ROOT / 'frontend' / 'lib' / 'types.ts').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')


class ClaimCacheUIContractTests(unittest.TestCase):
    def test_01_ui_explicitly_states_hardware_independence(self):
        self.assertIn('DONANIMDAN BAĞIMSIZ İYİLEŞTİRME', PAGE)

    def test_02_first_analysis_is_labeled_cold(self):
        self.assertIn('İlk analiz · soğuk', PAGE)

    def test_03_repeat_analysis_is_labeled_warm(self):
        self.assertIn('Tekrar analiz · sıcak', PAGE)

    def test_04_cold_duration_uses_measured_result(self):
        self.assertIn('result.cache_profile.cold_ms', PAGE)

    def test_05_warm_duration_uses_measured_result(self):
        self.assertIn('result.cache_profile.warm_median_ms', PAGE)

    def test_06_speedup_is_only_shown_when_measured(self):
        self.assertIn('result.cache_profile.speedup_factor !== null', PAGE)

    def test_07_actual_cache_hits_are_shown(self):
        self.assertIn('result.cache_profile.hit_total', PAGE)

    def test_08_actual_model_misses_are_shown(self):
        self.assertIn('result.cache_profile.miss_total', PAGE)

    def test_09_avoided_inferences_are_shown(self):
        self.assertIn('result.cache_profile.avoided_model_inference_count', PAGE)

    def test_10_cache_hit_rate_is_measured_not_hardcoded(self):
        self.assertIn('result.cache_profile.hit_rate_percent', PAGE)

    def test_11_saved_old_results_do_not_show_fake_cache_card(self):
        self.assertIn('result.cache_profile.available &&', PAGE)

    def test_12_actual_model_comment_stays_visible(self):
        self.assertIn('result.model_usage.demo.claim_transformer_comment_ids', PAGE)

    def test_13_cached_model_comment_is_disclosed(self):
        self.assertIn('result.model_usage.demo.claim_cache_comment_ids', PAGE)

    def test_14_cold_inference_count_is_separate(self):
        self.assertIn('result.model_usage.demo.cold_claim_transformer_count', PAGE)

    def test_15_warm_cache_usage_is_separate(self):
        self.assertIn('result.model_usage.demo.warm_claim_cache_hit_total', PAGE)

    def test_16_run_samples_are_labeled_cold_and_warm(self):
        self.assertIn("' · soğuk' : ' · sıcak'", PAGE)

    def test_17_each_stage_shows_first_and_repeat_duration(self):
        self.assertIn('technicalDuration(stage.cold_ms)', PAGE)
        self.assertIn('technicalDuration(stage.warm_median_ms)', PAGE)

    def test_18_claim_stage_shows_real_cache_hits(self):
        self.assertIn('stage.cache_hit_total', PAGE)

    def test_19_first_run_bottleneck_is_measured(self):
        self.assertIn('result.stage_profile.cold_bottleneck.label', PAGE)

    def test_20_normal_claim_radar_shows_cache_reuse(self):
        self.assertIn('claimCacheHitCount', PAGE)
        self.assertIn('önbellek kararı', PAGE)

    def test_21_normal_claim_radar_keeps_ai_identification_when_cached(self):
        self.assertIn("'AI + Önbellek'", PAGE)

    def test_22_cache_scope_is_disclosed(self):
        self.assertIn('result.cache_profile.note', PAGE)

    def test_23_types_define_cache_contract(self):
        self.assertIn('export type TechnicalCacheProfile', TYPES)
        self.assertIn('cache_profile: TechnicalCacheProfile', TYPES)

    def test_24_types_allow_unknown_legacy_values(self):
        self.assertIn('warm_median_ms: number | null', TYPES)
        self.assertIn('hit_total: number | null', TYPES)

    def test_25_cache_cards_use_scoped_styles(self):
        self.assertIn('.technicalCacheCard{', CSS)
        self.assertIn('.technicalCacheDetailCard>small', CSS)

    def test_26_cache_layout_supports_small_screens(self):
        self.assertIn('.technicalCacheComparison,.technicalCacheStats{grid-template-columns:1fr}', CSS)

    def test_27_prior_metric_cards_are_preserved(self):
        self.assertIn('Medyan analiz', PAGE)
        self.assertIn('P95 gecikme', PAGE)

    def test_28_no_specific_gpu_model_is_required(self):
        self.assertNotIn('GTX 1650', PAGE)
        self.assertNotIn('RTX 3060', PAGE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
