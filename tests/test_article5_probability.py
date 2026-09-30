import importlib.util
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "research/article5/validate_probability.py"
SPEC = importlib.util.spec_from_file_location("article5_probability", MODULE_PATH)
probability = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = probability
SPEC.loader.exec_module(probability)


class Article5ProbabilityTests(unittest.TestCase):
    def test_leaky_canary_is_rejected(self):
        with self.assertRaises(ValueError):
            probability.validate_feature_set(
                probability.MODEL_FEATURES | {"signed_boundary_distance"},
                benchmark=True,
            )

    def test_unsigned_distance_is_benchmark_only(self):
        with self.assertRaises(ValueError):
            probability.validate_feature_set(probability.MODEL_FEATURES, benchmark=False)
        probability.validate_feature_set(probability.MODEL_FEATURES, benchmark=True)

    def test_rolling_origin_is_strictly_prior(self):
        frame = pd.DataFrame({
            "month": ["2026-03", "2026-03", "2026-04", "2026-05"],
        })
        splits = list(probability.rolling_origin_splits(frame))
        self.assertEqual([month for month, _, _ in splits], ["2026-04", "2026-05"])
        for month, train, test in splits:
            self.assertTrue((frame.loc[train, "month"] < month).all())
            self.assertTrue((frame.loc[test, "month"] == month).all())

    def test_support_requires_both_classes(self):
        supported = {"n": 500, "positives": 100, "negatives": 400}
        unsupported = {"n": 500, "positives": 99, "negatives": 401}
        self.assertEqual(probability.support_status(supported), "SUPPORTED")
        self.assertEqual(
            probability.support_status(unsupported), "UNSUPPORTED_LOW_SAMPLE"
        )


if __name__ == "__main__":
    unittest.main()
