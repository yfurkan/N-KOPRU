from __future__ import annotations

import math
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from app.argument_engine import (
    CLAIM_AI_LABELS,
    CLAIM_FACTUAL_THRESHOLD,
    CLAIM_HYPOTHESIS_TEMPLATE,
    analyze_claims,
    invalidate_claim_cache_for,
)
from app.claim_cache import (
    CACHE_MAX_ENTRIES,
    claim_cache_get,
    claim_cache_key,
    claim_cache_size,
    clear_claim_cache,
)
from app.models import Comment


class RecordingModel:
    def __init__(self, *, factual=True, score=0.93, delay=0.0):
        self.factual = factual
        self.score = score
        self.delay = delay
        self.calls = []

    def __call__(self, sequences, candidate_labels, **kwargs):
        rows = sequences if isinstance(sequences, list) else [sequences]
        self.calls.append(list(rows))
        if self.delay:
            time.sleep(self.delay)
        label = candidate_labels[0 if self.factual else 1]
        return [{'labels': [label], 'scores': [self.score]} for _ in rows]


class ClaimCacheRegressionTests(unittest.TestCase):
    def setUp(self):
        clear_claim_cache()
        self.model = RecordingModel()
        self.pipeline_patch = patch('app.stance_engine._PIPELINE', self.model)
        self.dependency_patch = patch('app.stance_engine.dependencies_installed', return_value=True)
        self.pipeline_patch.start()
        self.dependency_patch.start()
        self.addCleanup(self.pipeline_patch.stop)
        self.addCleanup(self.dependency_patch.stop)
        self.addCleanup(clear_claim_cache)
        self.title = 'Yapay zekâ kullanımı nasıl düzenlenmeli?'
        self.first = self.comment(8, 'Bazı öğrenciler bütün ödevi yapay zekâya yaptırıyor.')

    @staticmethod
    def comment(comment_id, text):
        return Comment(id=comment_id, author='Katılımcı', text=text, created_at='şimdi')

    def analyze(self, comments=None, *, title=None, use_ai=True):
        return analyze_claims(title or self.title, comments or [self.first], use_ai=use_ai)

    def key(self, *, title=None, text=None, model_name='örnek-model', device='cpu',
            model_identity=11, labels=None, template=None, threshold=None):
        return claim_cache_key(
            title or self.title,
            text or self.first.text,
            model_name=model_name,
            device=device,
            model_identity=model_identity,
            candidate_labels=labels or CLAIM_AI_LABELS,
            hypothesis_template=template or CLAIM_HYPOTHESIS_TEMPLATE,
            threshold=CLAIM_FACTUAL_THRESHOLD if threshold is None else threshold,
        )

    def test_01_first_ambiguous_comment_runs_real_model(self):
        _, info = self.analyze()
        self.assertEqual(info['transformer_count'], 1)

    def test_02_first_run_reports_real_cache_miss(self):
        _, info = self.analyze()
        self.assertEqual((info['cache_hit_count'], info['cache_miss_count']), (0, 1))

    def test_03_identical_second_run_reuses_model_result(self):
        self.analyze()
        _, info = self.analyze()
        self.assertEqual((info['transformer_count'], info['cache_hit_count']), (0, 1))

    def test_04_identical_comment_calls_model_only_once(self):
        self.analyze()
        self.analyze()
        self.assertEqual(len(self.model.calls), 1)

    def test_05_cached_claim_output_matches_cold_output(self):
        first, _ = self.analyze()
        second, _ = self.analyze()
        self.assertEqual([item.model_dump() for item in first], [item.model_dump() for item in second])

    def test_06_cached_model_decision_keeps_hybrid_engine(self):
        self.analyze()
        _, info = self.analyze()
        self.assertEqual(info['mode'], 'hybrid-semantic-claim')

    def test_07_cached_model_comment_id_is_still_visible(self):
        self.analyze()
        _, info = self.analyze()
        self.assertEqual(info['model_comment_ids'], [8])

    def test_08_cached_result_is_not_reported_as_new_inference(self):
        self.analyze()
        _, info = self.analyze()
        self.assertEqual(info['transformer_comment_ids'], [])

    def test_09_cached_comment_id_is_reported_separately(self):
        self.analyze()
        _, info = self.analyze()
        self.assertEqual(info['cache_comment_ids'], [8])

    def test_10_new_ambiguous_comment_alone_requires_new_inference(self):
        second = self.comment(9, 'Bazı öğrenciler araçları her derste kullanıyor.')
        self.analyze()
        _, info = self.analyze([self.first, second])
        self.assertEqual((info['transformer_count'], info['cache_hit_count']), (1, 1))
        self.assertEqual(info['transformer_comment_ids'], [9])

    def test_11_new_comment_model_call_contains_only_changed_content(self):
        second = self.comment(9, 'Bazı öğrenciler araçları her derste kullanıyor.')
        self.analyze()
        self.analyze([self.first, second])
        self.assertEqual(len(self.model.calls[1]), 1)
        self.assertIn(second.text, self.model.calls[1][0])

    def test_12_changed_discussion_title_invalidates_decision(self):
        self.analyze()
        _, info = self.analyze(title='Üniversitede farklı bir karar nasıl alınmalı?')
        self.assertEqual(info['transformer_count'], 1)

    def test_13_changed_comment_content_invalidates_decision(self):
        self.analyze()
        modified = self.comment(8, 'Bazı öğrenciler bütün projeyi yapay zekâya hazırlatıyor.')
        _, info = self.analyze([modified])
        self.assertEqual(info['transformer_count'], 1)

    def test_14_model_name_is_part_of_cache_identity(self):
        self.analyze()
        with patch('app.stance_engine.MODEL_NAME', 'başka-model'):
            _, info = self.analyze()
        self.assertEqual(info['transformer_count'], 1)

    def test_15_device_is_part_of_cache_identity(self):
        self.analyze()
        with patch('app.stance_engine._DEVICE', 'cuda'):
            _, info = self.analyze()
        self.assertEqual(info['transformer_count'], 1)

    def test_16_reloaded_model_object_invalidates_cached_decision(self):
        self.analyze()
        another = RecordingModel()
        with patch('app.stance_engine._PIPELINE', another):
            _, info = self.analyze()
        self.assertEqual((info['transformer_count'], len(another.calls)), (1, 1))

    def test_17_cache_key_is_sha256_digest(self):
        key = self.key()
        self.assertEqual(len(key), 64)
        int(key, 16)

    def test_18_raw_comment_text_is_not_exposed_in_key(self):
        self.assertNotIn('öğrenciler', self.key())

    def test_19_exact_title_changes_digest(self):
        self.assertNotEqual(self.key(), self.key(title=f'{self.title} '))

    def test_20_exact_comment_whitespace_changes_digest(self):
        self.assertNotEqual(self.key(), self.key(text=f'{self.first.text} '))

    def test_21_case_changes_digest_instead_of_assuming_equivalence(self):
        self.assertNotEqual(self.key(), self.key(text=self.first.text.upper()))

    def test_22_candidate_label_changes_digest(self):
        self.assertNotEqual(self.key(), self.key(labels=[*CLAIM_AI_LABELS, 'ek etiket']))

    def test_23_hypothesis_template_changes_digest(self):
        self.assertNotEqual(self.key(), self.key(template='Bu cümle {}.'))

    def test_24_decision_threshold_changes_digest(self):
        self.assertNotEqual(self.key(), self.key(threshold=0.75))

    def test_25_model_identity_changes_digest(self):
        self.assertNotEqual(self.key(), self.key(model_identity=99))

    def test_26_negative_model_decision_is_also_cached(self):
        self.model.factual = False
        first, _ = self.analyze()
        second, info = self.analyze()
        self.assertEqual((first, second, info['cache_hit_count'], len(self.model.calls)), ([], [], 1, 1))

    def test_27_score_below_threshold_is_cached_without_creating_claim(self):
        self.model.score = 0.35
        first, _ = self.analyze()
        second, info = self.analyze()
        self.assertEqual((first, second, info['cache_hit_count']), ([], [], 1))

    def test_28_non_finite_score_is_never_cached(self):
        self.model.score = math.nan
        _, info = self.analyze()
        self.assertEqual((info['transformer_count'], claim_cache_size()), (0, 0))

    def test_29_score_outside_probability_range_is_never_cached(self):
        self.model.score = 1.5
        _, info = self.analyze()
        self.assertEqual((info['transformer_count'], claim_cache_size()), (0, 0))

    def test_30_malformed_batch_is_not_partially_cached(self):
        second = self.comment(9, 'Bazı öğrenciler araçları her derste kullanıyor.')
        with patch.object(self.model, '__call__', return_value=[]):
            # __call__ spécial dispatch is resolved on the class; replace pipeline directly.
            with patch('app.stance_engine._PIPELINE', lambda *args, **kwargs: []):
                _, info = self.analyze([self.first, second])
        self.assertEqual((info['transformer_count'], claim_cache_size()), (0, 0))

    def test_31_model_exception_falls_back_without_cache_write(self):
        def broken(*args, **kwargs):
            raise RuntimeError('model unavailable')

        with patch('app.stance_engine._PIPELINE', broken):
            _, info = self.analyze()
        self.assertEqual((info['transformer_count'], claim_cache_size()), (0, 0))

    def test_32_heuristic_mode_does_not_read_or_write_cache(self):
        self.analyze()
        _, info = self.analyze(use_ai=False)
        self.assertEqual((info['transformer_count'], info['cache_hit_count']), (0, 0))

    def test_33_structural_claim_does_not_run_or_cache_model(self):
        comment = self.comment(12, 'Geçen yıl öğrencilerin %70 oranında katıldığı açıklandı.')
        _, info = self.analyze([comment])
        self.assertEqual((info['transformer_count'], info['cache_miss_count']), (0, 0))

    def test_34_question_does_not_run_model(self):
        question = self.comment(12, 'Bazı öğrenciler hangi araştırmada incelendi?')
        _, info = self.analyze([question])
        self.assertEqual(info['transformer_count'], 0)

    def test_35_identical_text_in_same_batch_runs_only_once(self):
        repeated = self.comment(15, self.first.text)
        _, info = self.analyze([self.first, repeated])
        self.assertEqual((info['transformer_count'], info['cache_hit_count']), (1, 1))

    def test_36_same_batch_reuse_keeps_both_comment_ids(self):
        repeated = self.comment(15, self.first.text)
        _, info = self.analyze([self.first, repeated])
        self.assertEqual(info['model_comment_ids'], [8, 15])

    def test_37_cache_has_fixed_safe_default_bound(self):
        self.assertEqual(CACHE_MAX_ENTRIES, 512)

    def test_38_lru_cache_evicts_oldest_entry(self):
        with patch('app.claim_cache.CACHE_MAX_ENTRIES', 2):
            self.analyze(title='A')
            self.analyze(title='B')
            self.analyze(title='C')
            self.assertEqual(claim_cache_size(), 2)
            _, info = self.analyze(title='A')
            self.assertEqual(info['transformer_count'], 1)

    def test_39_recent_access_preserves_entry_during_lru_eviction(self):
        with patch('app.claim_cache.CACHE_MAX_ENTRIES', 2):
            self.analyze(title='A')
            self.analyze(title='B')
            self.analyze(title='A')
            self.analyze(title='C')
            _, info = self.analyze(title='A')
            self.assertEqual(info['cache_hit_count'], 1)

    def test_40_targeted_invalidation_removes_only_matching_discussion(self):
        self.analyze(title='A')
        self.analyze(title='B')
        self.assertEqual(invalidate_claim_cache_for('A', [self.first]), 1)
        _, preserved = self.analyze(title='B')
        _, removed = self.analyze(title='A')
        self.assertEqual((preserved['cache_hit_count'], removed['transformer_count']), (1, 1))

    def test_41_clear_cache_reports_removed_entries(self):
        self.analyze()
        self.assertEqual((clear_claim_cache(), claim_cache_size()), (1, 0))

    def test_42_concurrent_identical_requests_share_one_model_call(self):
        self.model.delay = 0.015
        with ThreadPoolExecutor(max_workers=6) as executor:
            responses = list(executor.map(lambda _: self.analyze()[1], range(6)))
        self.assertEqual(len(self.model.calls), 1)
        self.assertEqual(sum(item['transformer_count'] for item in responses), 1)
        self.assertEqual(sum(item['cache_hit_count'] for item in responses), 5)

    def test_43_cache_size_is_reported_in_analysis_info(self):
        _, info = self.analyze()
        self.assertEqual(info['cache_size'], 1)

    def test_44_model_unavailable_does_not_invent_cache_hit(self):
        with patch('app.stance_engine._PIPELINE', None):
            _, info = self.analyze()
        self.assertEqual((info['cache_hit_count'], info['cache_miss_count']), (0, 0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
