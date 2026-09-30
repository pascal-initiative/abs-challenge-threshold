import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "research/article5/stability_core.py"
SPEC = importlib.util.spec_from_file_location("article5_stability_core", MODULE_PATH)
core = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = core
SPEC.loader.exec_module(core)

DYNAMIC_PATH = ROOT / "research/article5/dynamic_core.py"
DYNAMIC_SPEC = importlib.util.spec_from_file_location("article5_dynamic_core_for_stability", DYNAMIC_PATH)
dynamic_core = importlib.util.module_from_spec(DYNAMIC_SPEC)
sys.modules[DYNAMIC_SPEC.name] = dynamic_core
DYNAMIC_SPEC.loader.exec_module(dynamic_core)


class Article5StabilityTests(unittest.TestCase):
    def test_standard_variant_matches_g7_toy_result(self):
        solution = core.dynamic_values([0.4, 0.8], [0.2, 0.5], [1, 2])
        self.assertAlmostEqual(solution["W"][1, 0], 0.4)

    def test_standard_variant_matches_g7_engine(self):
        p = np.array([0.31, 0.72, 0.55, 0.91])
        value = np.array([0.12, 0.41, 0.07, 0.63])
        innings = np.array([8, 9, 10, 11])
        expected = dynamic_core.backward_values(p, value, innings, "dynamic")
        actual = core.dynamic_values(p, value, innings)
        np.testing.assert_allclose(actual["W"], expected["W"], rtol=0, atol=1e-12)
        np.testing.assert_array_equal(actual["action"], expected["action"])
        np.testing.assert_allclose(actual["threshold"], expected["threshold"], rtol=0, atol=1e-12)

    def test_disabling_extra_grant_changes_zero_inventory(self):
        enabled = core.dynamic_values([0.0, 1.0], [0.1, 0.4], [9, 10], True)
        disabled = core.dynamic_values([0.0, 1.0], [0.1, 0.4], [9, 10], False)
        self.assertAlmostEqual(enabled["W"][0, 0], 0.4)
        self.assertAlmostEqual(disabled["W"][0, 0], 0.0)

    def test_threshold_bands_have_declared_boundaries(self):
        self.assertEqual(core.threshold_band(0.50), "LOW_REQUIRED_CONFIDENCE")
        self.assertEqual(core.threshold_band(0.500001), "INTERMEDIATE_REQUIRED_CONFIDENCE")
        self.assertEqual(core.threshold_band(0.70), "INTERMEDIATE_REQUIRED_CONFIDENCE")
        self.assertEqual(core.threshold_band(0.700001), "HIGH_REQUIRED_CONFIDENCE")

    def test_flip_rate(self):
        denominator, flips, rate = core.flip_rate([True, False, True], [True, True, False])
        self.assertEqual((denominator, flips), (3, 2))
        self.assertAlmostEqual(rate, 2 / 3)

    def test_invalid_probability_is_rejected(self):
        with self.assertRaises(ValueError):
            core.dynamic_values([1.1], [0.2], [1])


if __name__ == "__main__":
    unittest.main()
