from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
API = (ROOT / 'frontend' / 'lib' / 'api.ts').read_text(encoding='utf-8')
TYPES = (ROOT / 'frontend' / 'lib' / 'types.ts').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')


class ScenarioEvaluationUIContractTests(unittest.TestCase):
    def test_01_user_can_start_separate_scenario_evaluation(self):
        self.assertIn('Çok Senaryolu Doğrulamayı Başlat', PAGE)

    def test_02_reference_run_remains_separate(self):
        self.assertIn('Gerçek Ölçümü Başlat', PAGE)
        self.assertIn('runTechnicalEvaluation(5, useAI)', PAGE)

    def test_03_scenario_run_uses_real_backend_route(self):
        self.assertIn('/api/evaluation/scenarios/run`', API)

    def test_04_scenario_run_preserves_ai_selection(self):
        self.assertIn('JSON.stringify({ use_ai: useAI })', API)

    def test_05_scenario_status_is_restored(self):
        self.assertIn('setTechnicalScenarioResult(result.latest_scenario_result)', PAGE)

    def test_06_dataset_shows_eighty_real_examples(self):
        self.assertIn('80 örnek', PAGE)

    def test_07_dataset_shows_four_separate_topics(self):
        self.assertIn('4} konu', PAGE)

    def test_08_ui_does_not_call_scenarios_external(self):
        self.assertIn('PROJE İÇİ ELLE ETİKETLİ SET', PAGE)

    def test_09_dataset_limitation_is_shown(self):
        self.assertIn('scenarioResult.dataset.limitation', PAGE)

    def test_10_overall_accuracy_is_real(self):
        self.assertIn('technicalPercent(scenarioResult.accuracy)', PAGE)

    def test_11_macro_f1_is_real(self):
        self.assertIn('technicalPercent(scenarioResult.macro_f1)', PAGE)

    def test_12_each_topic_has_its_own_score(self):
        self.assertIn('scenarioResult.scenarios.map', PAGE)

    def test_13_difficult_cases_are_measured_separately(self):
        self.assertIn('scenarioResult.difficulty_metrics.map', PAGE)

    def test_14_real_errors_are_displayed(self):
        self.assertIn('Gerçek sınıflandırma hataları', PAGE)
        self.assertIn('scenarioResult.errors.map', PAGE)

    def test_15_error_records_show_actual_and_expected_labels(self):
        self.assertIn('Gerçek tahmin:', PAGE)
        self.assertIn('item.expected_label', PAGE)

    def test_16_error_records_show_challenge(self):
        self.assertIn('item.challenge', PAGE)
        self.assertIn('item.difficulty', PAGE)

    def test_17_scenario_confusion_matrix_is_distinct(self):
        self.assertIn('Çok senaryolu karışıklık matrisi', PAGE)
        self.assertIn('scenarioResult.confusion_matrix.map', PAGE)

    def test_18_scenario_class_metrics_are_distinct(self):
        self.assertIn('80 örnekte sınıf başarısı', PAGE)
        self.assertIn('scenarioResult.class_metrics.map', PAGE)

    def test_19_model_count_is_not_fabricated(self):
        self.assertIn('scenarioResult.transformer_inference_count', PAGE)
        self.assertIn('scenarioResult.structural_decision_count', PAGE)

    def test_20_live_discussion_is_shown_separately(self):
        self.assertIn('Aktif kullanıcı tartışması', PAGE)
        self.assertIn('REFERANS TESTTEN AYRI GERÇEK İÇERİK', PAGE)

    def test_21_live_discussion_shows_real_comments(self):
        self.assertIn('currentPost.comments.length', PAGE)

    def test_22_live_discussion_shows_real_unique_count(self):
        self.assertIn('liveAnalysis.indicators.comment_count', PAGE)

    def test_23_live_discussion_shows_real_claim_count(self):
        self.assertIn('liveAnalysis.claims.length', PAGE)

    def test_24_live_discussion_does_not_fabricate_accuracy(self):
        self.assertIn('doğruluk veya F1 skoru uydurulmaz', PAGE)

    def test_25_types_define_scenario_evaluation_contract(self):
        self.assertIn('export type TechnicalScenarioEvaluation', TYPES)

    def test_26_types_define_scenario_dataset_contract(self):
        self.assertIn('export type TechnicalScenarioDataset', TYPES)

    def test_27_types_define_real_error_records(self):
        self.assertIn('errors: TechnicalScenarioPrediction[]', TYPES)

    def test_28_status_keeps_both_saved_results(self):
        self.assertIn('latest_result: TechnicalEvaluation | null', TYPES)
        self.assertIn('latest_scenario_result: TechnicalScenarioEvaluation | null', TYPES)

    def test_29_logo_has_explicit_single_line_wrapper(self):
        self.assertIn("className='topBrand'", PAGE)
        self.assertIn('.topBrand h1 { white-space: nowrap; }', CSS)

    def test_30_scenario_cards_have_responsive_layout(self):
        self.assertIn('.technicalScenarioScoreGrid', CSS)
        self.assertIn('@media(max-width:850px){.technicalScenarioCard', CSS)

    def test_31_topic_cards_show_actual_class_results(self):
        self.assertIn('scenario.class_metrics.map', PAGE)

    def test_32_scenario_and_reference_runs_cannot_overlap(self):
        self.assertIn('technicalRunning || technicalScenarioRunning', PAGE)

    def test_33_each_topic_shows_model_vs_structural_counts(self):
        self.assertIn('scenario.transformer_inference_count', PAGE)
        self.assertIn('scenario.structural_decision_count', PAGE)

    def test_34_previous_reference_details_remain_visible(self):
        self.assertIn('result.confusion_matrix.map', PAGE)
        self.assertIn('result.latency.samples_ms.map', PAGE)

    def test_35_saved_scenario_results_are_read_without_rerun(self):
        self.assertIn('latest_scenario_result: result', PAGE)

    def test_36_error_details_are_open_when_errors_exist(self):
        self.assertIn('open={scenarioResult.error_count > 0}', PAGE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
