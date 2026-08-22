from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.evaluation import _hardware_diagnostics, _read_torch_capabilities


class TechnicalHardwareRegressionTests(unittest.TestCase):
    def capabilities(self, **overrides):
        values = {
            'torch_available': True,
            'torch_version': '2.8.0',
            'cuda_build_version': '12.8',
            'cuda_available': False,
            'cuda_device_count': 0,
            'cuda_device_name': None,
            'probe_error': None,
        }
        values.update(overrides)
        return values

    def diagnose(self, *, loaded=True, device='cpu', **capabilities):
        with patch('app.evaluation._read_torch_capabilities', return_value=self.capabilities(**capabilities)):
            return _hardware_diagnostics({'loaded': loaded, 'device': device})

    def test_01_missing_torch_is_reported_honestly(self):
        result = self.diagnose(torch_available=False, torch_version=None, cuda_build_version=None)
        self.assertEqual(result['diagnosis_key'], 'torch-missing')
        self.assertIn('PyTorch bulunamadı', result['diagnosis'])

    def test_02_cpu_only_torch_is_distinguished_from_driver_problem(self):
        result = self.diagnose(cuda_build_version=None)
        self.assertEqual(result['diagnosis_key'], 'cpu-only-torch')
        self.assertIn('CUDA desteği yok', result['diagnosis'])

    def test_03_cpu_only_torch_does_not_claim_gpu_absence(self):
        result = self.diagnose(cuda_build_version=None)
        self.assertIn('Fiziksel ekran kartı varlığı', result['diagnosis'])

    def test_04_cuda_build_without_device_is_diagnosed(self):
        result = self.diagnose(cuda_available=False)
        self.assertEqual(result['diagnosis_key'], 'cuda-unavailable')
        self.assertIn('kullanılabilir CUDA aygıtı algılanmadı', result['diagnosis'])

    def test_05_cuda_ready_with_cpu_loaded_model_is_distinguished(self):
        result = self.diagnose(cuda_available=True, cuda_device_count=1, cuda_device_name='GPU')
        self.assertEqual(result['diagnosis_key'], 'cuda-ready-model-on-cpu')
        self.assertFalse(result['acceleration_active'])

    def test_06_cuda_ready_without_model_is_not_claimed_active(self):
        result = self.diagnose(loaded=False, cuda_available=True, cuda_device_count=1)
        self.assertEqual(result['diagnosis_key'], 'cuda-ready-model-unloaded')
        self.assertFalse(result['acceleration_active'])

    def test_07_loaded_cuda_model_is_reported_as_gpu_active(self):
        result = self.diagnose(
            device='cuda', cuda_available=True, cuda_device_count=1,
            cuda_device_name='NVIDIA GeForce RTX 3060',
        )
        self.assertEqual(result['diagnosis_key'], 'cuda-active')
        self.assertTrue(result['acceleration_active'])

    def test_08_verified_gpu_name_is_preserved(self):
        result = self.diagnose(
            device='cuda:0', cuda_available=True, cuda_device_count=1,
            cuda_device_name='NVIDIA GeForce RTX 3060',
        )
        self.assertIn('NVIDIA GeForce RTX 3060', result['diagnosis'])

    def test_09_hardware_probe_failure_has_explicit_state(self):
        result = self.diagnose(probe_error='RuntimeError: CUDA okunamadı')
        self.assertEqual(result['diagnosis_key'], 'probe-error')
        self.assertIn('güvenli biçimde okunamadı', result['diagnosis'])

    def test_10_report_preserves_actual_model_device(self):
        result = self.diagnose(device='cpu')
        self.assertEqual(result['active_device'], 'cpu')

    def test_11_report_exposes_positive_cpu_core_count(self):
        self.assertGreaterEqual(self.diagnose()['cpu_core_count'], 1)

    def test_12_torch_versions_are_not_invented(self):
        result = self.diagnose(torch_version='2.8.0+cu128')
        self.assertEqual(result['torch_version'], '2.8.0+cu128')

    def test_13_missing_torch_does_not_import_model(self):
        with patch('app.evaluation.importlib.util.find_spec', return_value=None), patch(
            'app.evaluation.importlib.import_module'
        ) as imported:
            values = _read_torch_capabilities()
        imported.assert_not_called()
        self.assertFalse(values['torch_available'])

    def test_14_torch_cuda_details_are_read_without_loading_model(self):
        cuda = SimpleNamespace(
            is_available=lambda: True,
            device_count=lambda: 1,
            get_device_name=lambda index: 'Measured GPU',
        )
        torch = SimpleNamespace(
            __version__='2.8.0+cu128',
            version=SimpleNamespace(cuda='12.8'),
            cuda=cuda,
        )
        with patch('app.evaluation.importlib.util.find_spec', return_value=object()), patch(
            'app.evaluation.importlib.import_module', return_value=torch
        ):
            values = _read_torch_capabilities()
        self.assertTrue(values['torch_available'])
        self.assertTrue(values['cuda_available'])
        self.assertEqual(values['cuda_device_name'], 'Measured GPU')

    def test_15_probe_exception_is_captured_instead_of_crashing(self):
        with patch('app.evaluation.importlib.util.find_spec', side_effect=RuntimeError('bozuk kurulum')):
            values = _read_torch_capabilities()
        self.assertIn('bozuk kurulum', values['probe_error'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
