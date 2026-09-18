"""v1.4.1 anlam korumasının arayüz, sürüm ve geriye uyumluluk sözleşmesi."""
from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')
TYPES = (ROOT / 'frontend' / 'lib' / 'types.ts').read_text(encoding='utf-8')
API = (ROOT / 'frontend' / 'lib' / 'api.ts').read_text(encoding='utf-8')
DATASET = (ROOT / 'backend' / 'app' / 'evaluation_scenarios.py').read_text(encoding='utf-8')
EVALUATION = (ROOT / 'backend' / 'app' / 'evaluation.py').read_text(encoding='utf-8')
MAIN = (ROOT / 'backend' / 'app' / 'main.py').read_text(encoding='utf-8')
VERSION = (ROOT / 'backend' / 'app' / 'version.py').read_text(encoding='utf-8')
PACKAGE = json.loads((ROOT / 'frontend' / 'package.json').read_text(encoding='utf-8'))
LOCK = json.loads((ROOT / 'frontend' / 'package-lock.json').read_text(encoding='utf-8'))


class StanceSemanticsUiContract(unittest.TestCase):
    def test_01_technical_workspace_names_contextual_semantic_protection(self):
        self.assertIn('Bağlama duyarlı anlam koruması', PAGE)

    def test_02_technical_workspace_describes_continuity_evidence_and_context(self):
        self.assertIn('erişim/süreklilik, kanıt ihtiyacı veya konuya bağlı kısıtlama', PAGE)

    def test_03_semantic_summary_uses_real_api_count(self):
        self.assertIn('{scenarioResult.semantic_guardrail_count}', PAGE)

    def test_04_semantic_summary_is_hidden_for_old_sqlite_results(self):
        self.assertIn(
            "typeof scenarioResult.semantic_guardrail_count === 'number' && <div className='technicalSemanticSummary'>",
            PAGE,
        )

    def test_05_panel_uses_the_same_guard_for_old_results(self):
        self.assertIn(
            "typeof scenarioResult.semantic_guardrail_count === 'number' && <span>",
            PAGE,
        )

    def test_06_panel_names_semantic_protection(self):
        self.assertIn('anlamsal koruma</span>', PAGE)

    def test_07_calibration_disclaimer_uses_actual_dataset_note(self):
        self.assertIn('scenarioResult.dataset.calibration_note', PAGE)

    def test_08_calibration_disclaimer_is_optional_for_old_results(self):
        self.assertIn(
            "scenarioResult.dataset.calibration_note && <small className='technicalCalibrationNote'>",
            PAGE,
        )

    def test_09_existing_independent_scope_disclaimer_is_preserved(self):
        self.assertIn('scenarioResult.dataset.limitation', PAGE)

    def test_10_global_semantic_count_type_is_optional(self):
        self.assertGreaterEqual(TYPES.count('semantic_guardrail_count?: number;'), 2)

    def test_11_calibration_note_type_is_optional(self):
        self.assertIn('calibration_note?: string;', TYPES)

    def test_12_semantic_summary_has_dedicated_visual_style(self):
        self.assertIn('.technicalSemanticSummary{', CSS)

    def test_13_calibration_note_has_separate_visible_style(self):
        self.assertIn('.technicalCalibrationNote{', CSS)

    def test_14_dataset_discloses_that_prior_errors_informed_rules(self):
        self.assertIn('Önceki proje içi sınıflandırma hataları', DATASET)

    def test_15_dataset_rejects_independent_holdout_interpretation(self):
        self.assertIn('bağımsız tutma testi veya dış benchmark', DATASET)

    def test_16_counts_are_derived_from_decision_engine(self):
        self.assertIn(
            "item['decision_engine'].startswith('anlamsal tutarlılık:')",
            EVALUATION,
        )

    def test_17_backend_version_is_centralized(self):
        self.assertIn("APP_VERSION = '1.5.0'", VERSION)
        self.assertIn('from .version import APP_VERSION', MAIN)
        self.assertIn('from .version import APP_VERSION', EVALUATION)

    def test_18_frontend_package_version_is_updated(self):
        self.assertEqual(PACKAGE['version'], '1.5.0')

    def test_19_package_lock_root_version_is_updated(self):
        self.assertEqual(LOCK['version'], '1.5.0')
        self.assertEqual(LOCK['packages']['']['version'], '1.5.0')

    def test_20_source_package_version_file_is_updated(self):
        self.assertEqual((ROOT / 'VERSION.txt').read_text(encoding='utf-8').strip(), '1.5.0')

    def test_21_existing_scenario_endpoint_is_preserved(self):
        self.assertIn('/api/evaluation/scenarios/run', API)
        self.assertIn('/api/evaluation/scenarios/run', MAIN)

    def test_22_existing_user_content_boundary_is_preserved(self):
        self.assertIn('Kullanıcı yorumları elle etiketlenmediği için', PAGE)

    def test_23_existing_error_disclosure_remains_visible(self):
        self.assertIn('Gerçek sınıflandırma hataları', PAGE)
        self.assertIn('hata · gizlenmez', PAGE)

    def test_24_semantic_feature_has_no_device_specific_dependency(self):
        semantic_fragment = PAGE.split("className='technicalSemanticSummary'", 1)[1].split(
            '<small>{scenarioResult.engine_note}</small>',
            1,
        )[0]
        self.assertNotIn('GTX', semantic_fragment)
        self.assertNotIn('RTX', semantic_fragment)
        self.assertNotIn('CUDA', semantic_fragment)

    def test_25_main_analysis_already_exposes_honest_semantic_count(self):
        self.assertIn('semanticGuardrailCount > 0', PAGE)
        self.assertIn('anlam tutarlılığı kontrolüyle doğru kümeye bağlandı', PAGE)

    def test_26_reference_and_scenario_results_remain_separate(self):
        self.assertIn('latest_scenario_result', TYPES)
        self.assertIn('latest_result', TYPES)


if __name__ == '__main__':
    unittest.main(verbosity=2)
