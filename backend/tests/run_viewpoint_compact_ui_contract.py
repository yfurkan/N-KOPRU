from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / 'frontend' / 'app' / 'page.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend' / 'app' / 'globals.css').read_text(encoding='utf-8')


class ViewpointCompactUIContract(unittest.TestCase):
    def test_01_viewpoint_details_use_native_accessible_disclosure(self):
        self.assertIn("<details className='viewpointDetails'>", PAGE)

    def test_02_viewpoint_details_are_closed_by_default(self):
        self.assertNotRegex(PAGE, r"<details\s+className='viewpointDetails'\s+open")

    def test_03_summary_explains_what_will_open(self):
        self.assertIn('Görüş ayrıntıları ve temsilci yorumlar', PAGE)

    def test_04_summary_shows_representative_comment_count(self):
        self.assertIn('{v.representative_comments?.length || 0} yorum', PAGE)

    def test_05_position_and_percentage_are_visible_before_disclosure(self):
        card = PAGE.split("className={`viewpoint semanticViewpointCard", 1)[1]
        self.assertLess(card.index('v.display_name || v.name'), card.index("<details className='viewpointDetails'>"))
        self.assertLess(card.index('%{v.percentage}'), card.index("<details className='viewpointDetails'>"))

    def test_06_main_argument_is_visible_before_disclosure(self):
        card = PAGE.split("className={`viewpoint semanticViewpointCard", 1)[1]
        self.assertLess(card.index('v.main_argument || v.summary'), card.index("<details className='viewpointDetails'>"))

    def test_07_representative_comments_are_inside_disclosure(self):
        details = PAGE.split("<details className='viewpointDetails'>", 1)[1].split('</details>', 1)[0]
        self.assertIn('Temsilci yorumlar', details)
        self.assertIn('v.representative_comments.map', details)
        self.assertIn('Anlam tutarlılığıyla doğrulanan yorumlar', details)
        self.assertIn('guardrailComments.map', details)

    def test_08_relationships_and_evidence_are_inside_disclosure(self):
        details = PAGE.split("<details className='viewpointDetails'>", 1)[1].split('</details>', 1)[0]
        for label in ('Diğer görüşlerle ilişkisi', 'İddia bağlantısı:', 'Soru bağlantısı:', 'Kümedeki tüm yorumlar'):
            self.assertIn(label, details)

    def test_09_duplicate_ai_examples_are_collapsed(self):
        self.assertIn("<details className='stanceExamplesDetails'>", PAGE)
        self.assertIn('AI sınıflandırma ayrıntılarını göster', PAGE)
        self.assertNotRegex(PAGE, r"<details\s+className='stanceExamplesDetails'\s+open")

    def test_10_original_ai_examples_are_still_available(self):
        details = PAGE.split("<details className='stanceExamplesDetails'>", 1)[1].split('</details>', 1)[0]
        self.assertIn('AI sınıflandırma örnekleri', details)
        self.assertIn('analysis.stance_details.slice(0,6)', details)

    def test_11_guardrail_count_is_reported_without_claiming_model_confidence(self):
        self.assertIn('semanticGuardrailCount', PAGE)
        self.assertIn('anlam tutarlılığı kontrolüyle doğru kümeye bağlandı', PAGE)

    def test_12_disclosure_styles_cover_open_and_closed_states(self):
        for selector in ('.viewpointDetails>summary', '.viewpointDetails[open]>summary::before', '.viewpointDetailsContent'):
            self.assertIn(selector, CSS)
        self.assertIn('.viewpointGuardrailComment', CSS)

    def test_13_ai_examples_disclosure_has_its_own_styles(self):
        self.assertIn('.stanceExamplesDetails>summary', CSS)
        self.assertIn('.stanceExamplesDetails[open]>summary::before', CSS)

    def test_14_compact_card_spacing_is_smaller_than_previous_release(self):
        match = re.search(r'\.semanticViewpointCard\{[^}]+\}', CSS)
        self.assertIsNotNone(match)
        self.assertIn('gap:8px', match.group(0))
        self.assertIn('padding:11px 13px', match.group(0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
