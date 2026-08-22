from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
TYPES = (ROOT / 'frontend' / 'lib' / 'types.ts').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')


class TechnicalProfilingUIContractTests(unittest.TestCase):
    def test_01_technical_cards_override_inherited_minimum_height(self):
        self.assertIn('.technicalPanelStack>.moduleCard{min-height:auto', CSS)

    def test_02_other_analysis_cards_keep_existing_height(self):
        self.assertIn('.moduleCard { padding: 20px; min-height: 560px; }', CSS)

    def test_03_stage_profile_has_its_own_compact_card(self):
        self.assertIn("className='moduleCard technicalProfileCard'", PAGE)

    def test_04_each_measured_stage_is_rendered(self):
        self.assertIn('result.stage_profile.stages.map', PAGE)

    def test_05_stage_medians_are_rendered(self):
        self.assertIn('technicalDuration(stage.median_ms)', PAGE)

    def test_06_stage_shares_are_rendered(self):
        self.assertIn('stage.share_of_total_percent', PAGE)

    def test_07_bottleneck_is_not_hard_coded(self):
        self.assertIn('result.stage_profile.bottleneck.label', PAGE)

    def test_08_bottleneck_highlighting_uses_real_key(self):
        self.assertIn("stage.key === result.stage_profile.bottleneck?.key", PAGE)

    def test_09_stage_transformer_count_is_shown_only_when_real(self):
        self.assertIn('stage.transformer_inference_total > 0', PAGE)

    def test_10_stage_profile_discloses_remaining_work(self):
        self.assertIn('result.stage_profile.overhead_median_ms', PAGE)
        self.assertIn('result.stage_profile.note', PAGE)

    def test_11_legacy_saved_result_has_explicit_rerun_message(self):
        self.assertIn('Eski ölçümde katman süreleri bulunmuyor', PAGE)

    def test_12_internal_and_demo_model_usage_are_separate(self):
        self.assertIn('result.model_usage.internal_set.stance_transformer_count', PAGE)
        self.assertIn('result.model_usage.demo.stance_transformer_per_run', PAGE)

    def test_13_claim_usage_is_not_hidden_by_stance_counter(self):
        self.assertIn('result.model_usage.demo.claim_transformer_per_run', PAGE)

    def test_14_claim_model_comment_ids_are_exposed(self):
        self.assertIn('result.model_usage.demo.claim_transformer_comment_ids', PAGE)

    def test_15_unknown_legacy_counts_are_not_displayed_as_zero(self):
        self.assertIn("value === null ? 'Ölçülmedi'", PAGE)

    def test_16_hardware_diagnostics_are_visible(self):
        self.assertIn('CPU / CUDA durumu', PAGE)
        self.assertIn('hardware.diagnosis', PAGE)

    def test_17_cuda_build_and_availability_are_separate(self):
        self.assertIn('hardware.cuda_build_version', PAGE)
        self.assertIn('hardware.cuda_available', PAGE)

    def test_18_gpu_name_is_shown_only_when_verified(self):
        self.assertIn('hardware.cuda_device_name &&', PAGE)

    def test_19_gpu_active_label_uses_real_acceleration_state(self):
        self.assertIn("hardware.acceleration_active ? 'GPU etkin' : 'CPU kullanımı'", PAGE)

    def test_20_types_define_stage_profile_contract(self):
        self.assertIn('export type TechnicalStageProfile', TYPES)
        self.assertIn('stage_profile: TechnicalStageProfile', TYPES)

    def test_21_types_define_separate_model_usage_contract(self):
        self.assertIn('export type TechnicalModelUsage', TYPES)
        self.assertIn('claim_transformer_per_run: number | null', TYPES)

    def test_22_types_define_hardware_contract(self):
        self.assertIn('export type TechnicalHardware', TYPES)
        self.assertIn('cuda_build_version: string | null', TYPES)

    def test_23_stage_bar_and_bottleneck_have_scoped_styles(self):
        self.assertIn('.technicalStageTrack>span', CSS)
        self.assertIn('.technicalStageRow.bottleneck', CSS)

    def test_24_hardware_grid_collapses_on_small_screens(self):
        self.assertIn('.technicalLatencyGrid,.technicalExecutionSplit,.technicalHardwareGrid{grid-template-columns:1fr}', CSS)


if __name__ == '__main__':
    unittest.main(verbosity=2)
