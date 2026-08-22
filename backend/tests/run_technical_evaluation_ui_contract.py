from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
API = (ROOT / 'frontend' / 'lib' / 'api.ts').read_text(encoding='utf-8')
TYPES = (ROOT / 'frontend' / 'lib' / 'types.ts').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')


class TechnicalEvaluationUIContractTests(unittest.TestCase):
    def test_01_sidebar_has_technical_verification(self):
        self.assertIn("'Teknik Doğrulama'", PAGE)

    def test_02_user_can_run_a_real_measurement(self):
        self.assertIn('Gerçek Ölçümü Başlat', PAGE)
        self.assertIn('runTechnicalEvaluation(5, useAI)', PAGE)

    def test_03_ui_identifies_dataset_as_internal(self):
        self.assertIn('İç set doğruluğu', PAGE)
        self.assertIn('İç set Macro-F1', PAGE)

    def test_04_ui_discloses_small_manually_labeled_dataset(self):
        self.assertIn('elle etiketli cümle', PAGE)
        self.assertIn('result.dataset.limitation', PAGE)

    def test_05_ui_does_not_claim_external_benchmark(self):
        self.assertIn('dış veri seti sonucu', PAGE)
        self.assertIn('bağımsız model başarısı iddiası değildir', PAGE)

    def test_06_real_latency_samples_are_shown(self):
        self.assertIn('result.latency.samples_ms.map', PAGE)
        self.assertIn('result.latency.p95_ms', PAGE)

    def test_07_transformer_use_is_not_fabricated(self):
        self.assertIn('result.transformer_inference_count', PAGE)
        self.assertIn('result.structural_decision_count', PAGE)

    def test_08_model_confidence_is_only_shown_when_real(self):
        self.assertIn("item.model_confidence === null ? 'Yapısal karar'", PAGE)

    def test_09_confusion_matrix_is_visible(self):
        self.assertIn('Hata / karışıklık matrisi', PAGE)
        self.assertIn('result.confusion_matrix.map', PAGE)

    def test_10_each_class_metrics_are_visible(self):
        self.assertIn('Precision / Recall / F1', PAGE)
        self.assertIn('result.class_metrics.map', PAGE)

    def test_11_demo_invariants_are_visible(self):
        self.assertIn('Demo değişmezleri', PAGE)
        self.assertIn('result.invariants.map', PAGE)

    def test_12_saved_result_is_loaded_on_open(self):
        self.assertIn('getTechnicalStatus()', PAGE)
        self.assertIn('setTechnicalResult(result.latest_result)', PAGE)

    def test_13_isolation_notice_is_visible(self):
        self.assertIn('result.isolation_note', PAGE)

    def test_14_api_uses_real_backend_routes(self):
        self.assertIn('/api/evaluation`', API)
        self.assertIn('/api/evaluation/run`', API)

    def test_15_api_passes_iterations_and_ai_mode(self):
        self.assertIn('JSON.stringify({ iterations, use_ai: useAI })', API)

    def test_16_types_define_complete_evaluation_contract(self):
        self.assertIn('export type TechnicalEvaluation', TYPES)
        self.assertIn('transformer_inference_count: number', TYPES)
        self.assertIn('is_external_benchmark: boolean', TYPES)

    def test_17_layout_supports_compact_screens(self):
        self.assertIn('@media(max-width:850px){.technicalHero', CSS)

    def test_18_prediction_details_are_expandable(self):
        self.assertIn("<details className='moduleCard technicalPredictionCard'>", PAGE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
