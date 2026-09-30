import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "research/article5/win_probability_core.py"
SPEC = importlib.util.spec_from_file_location("article5_win_probability_core", MODULE_PATH)
core = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = core
SPEC.loader.exec_module(core)


class Article5WinProbabilityTests(unittest.TestCase):
    def test_extra_innings_share_phase(self):
        index = core.phase_index([10, 11, 14], ["top", "top", "bottom"])
        self.assertEqual(index[0], index[1])
        self.assertNotEqual(index[1], index[2])

    def test_advantage_slopes_are_nonnegative(self):
        inning = np.repeat([1, 9], 8)
        half = np.repeat(["top", "bottom"], 8)
        advantage = np.tile(np.linspace(-2, 2, 8), 2)
        target = (advantage > 0).astype(int)
        weights = np.ones(len(target))
        model = core.fit_bounded_logistic(core.design_matrix(inning, half, advantage), target, weights)
        self.assertGreaterEqual(model["minimum_advantage_slope"], 0.0)

    def test_probability_increases_with_advantage_within_phase(self):
        inning = [7, 7]
        half = ["bottom", "bottom"]
        advantage = [-1.0, 1.0]
        target = [0, 1]
        model = core.fit_bounded_logistic(core.design_matrix(inning, half, advantage), target, [1, 1])
        prediction = core.predict(model, core.design_matrix(inning, half, advantage))
        self.assertLessEqual(prediction[0], prediction[1])

    def test_sparse_phase_fit_matches_monotonic_direction(self):
        inning = np.repeat([2, 8], 10)
        half = np.repeat(["top", "bottom"], 10)
        advantage = np.tile(np.linspace(-3, 3, 10), 2)
        target = (advantage > 0).astype(int)
        model = core.fit_phase_logistic(inning, half, advantage, target, np.ones(len(target)))
        prediction = core.predict_phase(model, inning, half, advantage)
        self.assertTrue(np.all(np.diff(prediction[:10]) >= 0))
        self.assertTrue(np.all(np.diff(prediction[10:]) >= 0))

    def test_opponent_value_cancels(self):
        for opponent in (-0.2, 0.0, 0.7):
            self.assertAlmostEqual(
                core.opponent_adjusted_delta(0.42, 0.31, opponent),
                0.42 - 0.31,
            )

    def test_invalid_weights_rejected(self):
        with self.assertRaises(ValueError):
            core.fit_bounded_logistic(np.ones((2, 40)), [0, 1], [1, 0])


if __name__ == "__main__":
    unittest.main()
