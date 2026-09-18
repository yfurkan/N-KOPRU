"""v1.5.0: ayrılmış iç kontrolün ve konu bağlamının arayüz sözleşmesi."""
from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
API = (ROOT / 'frontend' / 'lib' / 'api.ts').read_text(encoding='utf-8')
TYPES = (ROOT / 'frontend' / 'lib' / 'types.ts').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')
EVALUATION = (ROOT / 'backend' / 'app' / 'evaluation.py').read_text(encoding='utf-8')
MAIN = (ROOT / 'backend' / 'app' / 'main.py').read_text(encoding='utf-8')
ANALYZER = (ROOT / 'backend' / 'app' / 'analyzer.py').read_text(encoding='utf-8')
ARGUMENT = (ROOT / 'backend' / 'app' / 'argument_engine.py').read_text(encoding='utf-8')
TOPIC = (ROOT / 'backend' / 'app' / 'topic_context.py').read_text(encoding='utf-8')
VERSION = (ROOT / 'backend' / 'app' / 'version.py').read_text(encoding='utf-8')
PACKAGE = json.loads((ROOT / 'frontend' / 'package.json').read_text(encoding='utf-8'))
LOCK = json.loads((ROOT / 'frontend' / 'package-lock.json').read_text(encoding='utf-8'))


class TopicHoldoutUIContractTests(unittest.TestCase):
    def test_01_new_control_has_its_own_start_button(self):
        self.assertIn('Ayrılmış Yeni Kontrolü Başlat', PAGE)

    def test_02_original_reference_button_is_preserved(self):
        self.assertIn('Gerçek Ölçümü Başlat', PAGE)

    def test_03_previous_calibration_button_is_preserved(self):
        self.assertIn('Çok Senaryolu Doğrulamayı Başlat', PAGE)

    def test_04_frontend_calls_real_holdout_endpoint(self):
        self.assertIn('/api/evaluation/holdout/run`', API)

    def test_05_backend_exposes_same_holdout_endpoint(self):
        self.assertIn("@app.post('/api/evaluation/holdout/run')", MAIN)

    def test_06_new_run_preserves_user_ai_preference(self):
        self.assertIn('runHoldoutEvaluation(useAI)', PAGE)

    def test_07_new_run_has_its_own_result_state(self):
        self.assertIn('technicalHoldoutResult, setTechnicalHoldoutResult', PAGE)

    def test_08_new_result_is_restored_without_rerunning(self):
        self.assertIn('setTechnicalHoldoutResult(result.latest_holdout_result ?? null)', PAGE)

    def test_09_all_three_result_payloads_are_independent(self):
        self.assertIn('latest_result: TechnicalEvaluation | null', TYPES)
        self.assertIn('latest_scenario_result: TechnicalScenarioEvaluation | null', TYPES)
        self.assertIn('latest_holdout_result?: TechnicalScenarioEvaluation | null', TYPES)

    def test_10_old_server_payloads_remain_type_compatible(self):
        self.assertIn('holdout_dataset?: TechnicalScenarioDataset', TYPES)

    def test_11_new_dataset_shows_five_separate_topics(self):
        self.assertIn('5} yeni konu', PAGE)

    def test_12_new_dataset_shows_eighty_new_sentences(self):
        self.assertIn('80} yeni örnek', PAGE)

    def test_13_sample_overlap_counter_is_visible(self):
        self.assertIn('calibration_sample_overlap_count ?? 0', PAGE)
        self.assertIn('ortak cümle', PAGE)

    def test_14_topic_overlap_counter_is_visible(self):
        self.assertIn('calibration_topic_overlap_count ?? 0', PAGE)
        self.assertIn('ortak konu', PAGE)

    def test_15_frozen_dataset_hash_is_visible(self):
        self.assertIn('SHA-256:', PAGE)
        self.assertIn('frozen_sha256.slice(0, 12)', PAGE)

    def test_16_full_fingerprint_remains_inspectable(self):
        self.assertIn('title={status.holdout_dataset.frozen_sha256}', PAGE)

    def test_17_hash_and_overlap_are_typed(self):
        self.assertIn('frozen_sha256?: string', TYPES)
        self.assertIn('is_disjoint_from_calibration?: boolean', TYPES)

    def test_18_overall_accuracy_uses_actual_backend_result(self):
        self.assertIn('technicalPercent(holdoutResult.accuracy)', PAGE)

    def test_19_macro_f1_uses_actual_backend_result(self):
        self.assertIn('technicalPercent(holdoutResult.macro_f1)', PAGE)

    def test_20_true_correct_count_is_displayed(self):
        self.assertIn('{holdoutResult.correct_count}/{holdoutResult.sample_count}', PAGE)

    def test_21_real_errors_are_never_hidden(self):
        self.assertIn('Ayrı kontroldeki gerçek sınıflandırma hataları', PAGE)
        self.assertIn('holdoutResult.errors.map', PAGE)

    def test_22_error_details_open_automatically_when_needed(self):
        self.assertIn('open={holdoutResult.error_count > 0}', PAGE)

    def test_23_error_items_show_expected_and_predicted_labels(self):
        self.assertIn('item.expected_label', PAGE)
        self.assertIn('item.predicted_label', PAGE)

    def test_24_each_new_topic_is_scored_separately(self):
        self.assertIn('holdoutResult.scenarios.map', PAGE)
        self.assertIn('Yeni tartışma konularında sonuç', PAGE)

    def test_25_new_confusion_matrix_is_separate(self):
        self.assertIn('Ayrı kontrol karışıklık matrisi', PAGE)
        self.assertIn('holdoutResult.confusion_matrix.map', PAGE)

    def test_26_new_class_metrics_are_separate(self):
        self.assertIn('Yeni örneklerde sınıf başarısı', PAGE)
        self.assertIn('holdoutResult.class_metrics.map', PAGE)

    def test_27_precision_recall_and_f1_are_shown(self):
        self.assertIn('technicalPercent(item.precision)', PAGE)
        self.assertIn('technicalPercent(item.recall)', PAGE)
        self.assertIn('technicalPercent(item.f1)', PAGE)

    def test_28_easy_and_difficult_cases_are_shown(self):
        self.assertIn('holdoutResult.difficulty_metrics.map', PAGE)

    def test_29_actual_model_and_structural_counts_are_shown(self):
        self.assertIn('holdoutResult.transformer_inference_count', PAGE)
        self.assertIn('holdoutResult.structural_decision_count', PAGE)

    def test_30_internal_scope_is_explicit(self):
        self.assertIn('AYRILMIŞ YENİ PROJE İÇİ KONTROL', PAGE)
        self.assertIn('bağımsız akademik benchmark değildir', PAGE)

    def test_31_previous_calibration_warning_is_preserved(self):
        self.assertIn('scenarioResult.dataset.calibration_note', PAGE)

    def test_32_all_three_run_types_are_mutually_exclusive(self):
        self.assertIn('technicalRunning || technicalScenarioRunning || technicalHoldoutRunning', PAGE)

    def test_33_new_cards_have_their_own_visual_style(self):
        self.assertIn('.technicalHoldoutCard{', CSS)
        self.assertIn('.technicalHoldoutEvidence{', CSS)

    def test_34_new_cards_are_responsive(self):
        self.assertIn('@media(max-width:850px){.technicalHoldoutCard', CSS)

    def test_35_analysis_exposes_shared_topic_identifier(self):
        self.assertIn("engine_info['viewpoint_topic_key']", ANALYZER)

    def test_36_analysis_exposes_shared_topic_subject(self):
        self.assertIn("engine_info['viewpoint_topic_subject']", ANALYZER)

    def test_37_bridge_uses_same_context_as_viewpoint_cards(self):
        self.assertIn('resolve_topic_context', ARGUMENT)

    def test_38_remote_labels_name_actual_positions(self):
        self.assertIn('Uzaktan çalışmanın devamını savunanlar', TOPIC)
        self.assertIn('Ofis zorunluluğu veya daha güçlü sınırlama', TOPIC)
        self.assertIn('Kurallı veya hibrit çalışma', TOPIC)

    def test_39_existing_academic_demo_is_explicitly_frozen(self):
        self.assertIn("key='academic-ai'", TOPIC)
        self.assertIn("self.key not in {'generic', 'academic-ai'}", TOPIC)

    def test_40_holdout_has_its_own_sqlite_metadata_key(self):
        self.assertIn("HOLDOUT_RESULT_META_KEY = 'technical_evaluation:last_holdout_result:v1'", EVALUATION)

    def test_41_overlap_is_rejected_before_prediction(self):
        self.assertIn("if not dataset['is_disjoint_from_calibration']", EVALUATION)

    def test_42_frontend_and_backend_versions_are_consistent(self):
        self.assertIn("APP_VERSION = '1.5.0'", VERSION)
        self.assertEqual(PACKAGE['version'], '1.5.0')
        self.assertEqual(LOCK['version'], '1.5.0')

    def test_43_existing_reference_and_calibration_routes_remain(self):
        self.assertIn("@app.post('/api/evaluation/run')", MAIN)
        self.assertIn("@app.post('/api/evaluation/scenarios/run')", MAIN)

    def test_44_holdout_ui_does_not_assume_a_specific_gpu(self):
        section = PAGE.split("className='technicalScenarioCard technicalHoldoutCard'", 1)[1]
        section = section.split("className='technicalLiveDiscussionCard'", 1)[0]
        self.assertNotIn('GTX', section)
        self.assertNotIn('RTX', section)


if __name__ == '__main__':
    unittest.main(verbosity=2)
