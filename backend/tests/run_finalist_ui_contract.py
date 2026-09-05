"""v1.5.0: mobil, erişilebilir, sunum ve pilot arayüz sözleşmesi."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')
API = (ROOT / 'frontend' / 'lib' / 'api.ts').read_text(encoding='utf-8')
TYPES = (ROOT / 'frontend' / 'lib' / 'types.ts').read_text(encoding='utf-8')
MAIN = (ROOT / 'backend' / 'app' / 'main.py').read_text(encoding='utf-8')
PACKAGE = json.loads((ROOT / 'frontend' / 'package.json').read_text(encoding='utf-8'))


class FinalistUIContractTests(unittest.TestCase):
    def test_01_mobile_navigation_is_not_removed(self):
        self.assertIn('sidebarOpen', PAGE)
        self.assertIn('.sidebar.sidebarOpen', CSS)
        final_css = CSS.split('/* v1.5.0', 1)[1]
        self.assertNotIn('.sidebar { display:none', final_css.replace(' ', ''))

    def test_02_mobile_menu_has_expanded_state(self):
        self.assertIn("aria-controls='primary-navigation'", PAGE)
        self.assertIn('aria-expanded={mobileNavOpen}', PAGE)

    def test_03_mobile_analysis_is_a_real_drawer(self):
        self.assertIn('mobilePanelOpen', PAGE)
        self.assertIn('.analysisPanel.mobilePanelOpen', CSS)
        self.assertIn("aria-controls='analysis-panel'", PAGE)

    def test_04_escape_closes_mobile_layers(self):
        self.assertIn("event.key !== 'Escape'", PAGE)
        self.assertIn('setMobileNavOpen(false)', PAGE)
        self.assertIn('setMobilePanelOpen(false)', PAGE)

    def test_05_skip_link_targets_main_content(self):
        self.assertIn("href='#main-content'", PAGE)
        self.assertIn("id='main-content'", PAGE)
        self.assertIn('.skipLink', CSS)

    def test_06_live_region_announces_async_state(self):
        self.assertIn("aria-live='polite'", PAGE)
        self.assertIn('setAnnouncement', PAGE)

    def test_07_analysis_tabs_have_semantics(self):
        self.assertIn("role='tablist'", PAGE)
        self.assertIn("role='tab'", PAGE)
        self.assertIn("role='tabpanel'", PAGE)
        self.assertIn('aria-selected={active === i}', PAGE)

    def test_08_keyboard_focus_is_globally_visible(self):
        self.assertIn(':focus-visible', CSS)
        self.assertIn('outline:3px solid', CSS)

    def test_09_reduced_motion_is_respected(self):
        self.assertIn('@media (prefers-reduced-motion:reduce)', CSS)

    def test_10_native_blocking_alert_was_removed(self):
        self.assertNotIn('window.alert', PAGE)

    def test_11_privacy_mode_masks_comment_authors(self):
        self.assertIn('visibleAuthor(', PAGE)
        self.assertIn('Gizlilik Açık', PAGE)
        self.assertIn("localStorage.setItem('nkopru:privacy-mode'", PAGE)

    def test_12_presentation_mode_is_primary_navigation(self):
        self.assertIn("'Sunum Modu'", PAGE)
        self.assertIn('<PresentationWorkspace', PAGE)
        self.assertIn('<PresentationPanel', PAGE)

    def test_13_presentation_has_live_readiness(self):
        self.assertIn('getSystemReadiness()', PAGE)
        self.assertIn('/api/system/readiness', API)
        self.assertIn("@app.get('/api/system/readiness'", MAIN)

    def test_14_presentation_timer_is_user_controlled(self):
        self.assertIn('4:30 Sayacı Başlat', PAGE)
        self.assertIn('setTimerRunning', PAGE)
        self.assertIn('setSecondsLeft(270)', PAGE)

    def test_15_presentation_links_to_live_product_evidence(self):
        self.assertIn('Canlı Özeti Aç', PAGE)
        self.assertIn('Görüş Haritasını Aç', PAGE)
        self.assertIn('Teknik Doğrulamayı Aç', PAGE)
        self.assertIn('Etki Pilotunu Aç', PAGE)

    def test_16_pilot_is_primary_navigation(self):
        self.assertIn("'Etki Pilotu'", PAGE)
        self.assertIn('<PilotWorkspace', PAGE)
        self.assertIn('<PilotPanel', PAGE)

    def test_17_pilot_api_is_fully_connected(self):
        for path in ('/api/pilot`', '/api/pilot/sessions`', '/api/pilot/sessions/${sessionId}/phases', '/api/pilot/results.csv'):
            self.assertIn(path, API)

    def test_18_pilot_requires_consent(self):
        self.assertIn('bilgilendirilmiş onay', MAIN + (ROOT / 'backend' / 'app' / 'pilot.py').read_text(encoding='utf-8'))
        self.assertIn('setConsent', PAGE)

    def test_19_practice_mode_is_explicit(self):
        self.assertIn('Deneme oturumu — sonuç metriklerine katma', PAGE)
        self.assertIn('practice: boolean', TYPES)

    def test_20_pilot_collects_all_four_metrics(self):
        for term in ('duration_ms', 'correct', 'clarity_rating', 'confidence_rating'):
            self.assertIn(term, TYPES)

    def test_21_pilot_evidence_is_exportable(self):
        self.assertIn('CSV Kanıtını İndir', PAGE)
        self.assertIn('downloadPilotResults()', PAGE)

    def test_22_contextual_coach_receives_real_disagreement(self):
        self.assertIn('analysis?.bridge.main_divergence', PAGE)
        self.assertIn('firstOpenQuestion', PAGE)

    def test_23_patched_next_release_is_pinned(self):
        self.assertEqual(PACKAGE['dependencies']['next'], '15.5.25')

    def test_24_transitive_security_fixes_are_pinned(self):
        self.assertEqual(PACKAGE['overrides']['postcss'], '8.5.28')
        self.assertEqual(PACKAGE['overrides']['sharp'], '0.35.4')

    def test_25_tabs_support_roving_focus_and_arrow_keys(self):
        self.assertIn('tabIndex={active === i ? 0 : -1}', PAGE)
        self.assertIn("event.key === 'ArrowRight'", PAGE)
        self.assertIn("event.key === 'ArrowLeft'", PAGE)
        self.assertIn("document.getElementById(`analysis-tab-${next}`)?.focus()", PAGE)

    def test_26_initial_demo_failure_is_announced(self):
        self.assertIn('Backend bağlantısı kurulamadı:', PAGE)
        self.assertIn("setAnnouncement('Örnek tartışma yüklendi.')", PAGE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
