from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
API = (ROOT / 'frontend' / 'lib' / 'api.ts').read_text(encoding='utf-8')
TYPES = (ROOT / 'frontend' / 'lib' / 'types.ts').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')


class V1ProfileUIContract(unittest.TestCase):
    def test_01_profile_is_dedicated_workspace(self):
        self.assertIn('function ProfileWorkspace', PAGE)
        self.assertIn('function ProfilePanel', PAGE)
        self.assertIn("navPage === 'Profil'", PAGE)

    def test_02_profile_fetch_and_update_are_api_backed(self):
        self.assertIn('getProfile', API)
        self.assertIn('updateProfile', API)
        self.assertIn('/api/profile', API)
        self.assertIn('onSave={saveProfile}', PAGE)

    def test_03_history_is_api_backed(self):
        self.assertIn('getAnalysisHistoryDetail', API)
        self.assertIn('/api/history/', API)
        self.assertIn('loadHistoryDetail', PAGE)

    def test_04_profile_has_real_stats(self):
        for label in ['Toplam analiz','Farklı tartışma','Yer imi','Kayıtlı Köprü','Liste','Liste öğesi']:
            self.assertIn(label, PAGE)

    def test_05_snapshot_open_does_not_call_analyze(self):
        start = PAGE.index('async function openHistorySnapshot')
        end = PAGE.index('async function prepareAI', start)
        block = PAGE[start:end]
        self.assertIn('getAnalysisHistoryDetail', block)
        self.assertIn('setAnalysis(detail.analysis)', block)
        self.assertNotIn('analyzePost(', block)

    def test_06_persistence_is_visible_to_user(self):
        self.assertIn('SQLite • Kalıcı', PAGE)
        self.assertIn('backend/data/nkopru.db', PAGE)
        self.assertIn('SQLite üzerinde kalıcı', PAGE)

    def test_07_profile_types_exist(self):
        self.assertIn('export type ProfileResponse', TYPES)
        self.assertIn('export type AnalysisHistoryDetail', TYPES)

    def test_08_profile_styles_exist(self):
        self.assertIn('.profileWorkspace', CSS)
        self.assertIn('.profileHistoryRow', CSS)
        self.assertIn('.profileSnapshotMetrics', CSS)

    def test_09_snapshot_change_panel_exists(self):
        self.assertIn('Snapshot karşılaştırması', PAGE)
        self.assertIn('changes_since_last_visit', PAGE)

    def test_10_session_only_copy_is_removed_from_persistent_modules(self):
        self.assertNotIn('Kalıcı hesap ve veritabanı v1.0 ürün katmanında bağlanacaktır.', PAGE)
        self.assertNotIn('bu yerel çalışma oturumunda tutulur', PAGE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
