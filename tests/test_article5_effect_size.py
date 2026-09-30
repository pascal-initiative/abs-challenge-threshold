import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "research/article5/effect_size_core.py"
SPEC = importlib.util.spec_from_file_location("article5_effect_size_core", MODULE_PATH)
core = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = core
SPEC.loader.exec_module(core)


class Article5EffectSizeTests(unittest.TestCase):
    def test_fixed_policy_evaluation(self):
        p = np.array([0.5, 1.0])
        value = np.array([0.2, 0.4])
        innings = np.array([1, 1])
        actions = np.zeros((3, 2), dtype=bool)
        actions[1:, :] = True
        result = core.evaluate_inventory_policy(p, value, innings, actions)
        self.assertAlmostEqual(result[1, 0], 0.3)

    def test_extra_inning_grant(self):
        actions = np.zeros((3, 2), dtype=bool)
        actions[1:, 1] = True
        result = core.evaluate_inventory_policy([0, 1], [0.1, 0.4], [9, 10], actions)
        self.assertAlmostEqual(result[0, 0], 0.4)

    def test_static_cost_rule(self):
        actions = core.static_cost_actions(
            [0.5, 0.5], [0.2, 0.04], [0.1, 0.1], [0.3, 0.01]
        )
        self.assertEqual(actions[1].tolist(), [True, False])
        self.assertEqual(actions[2].tolist(), [False, True])

    def test_bootstrap_keeps_best_simple_inside_replicate(self):
        dynamic = [1.0, 1.0, 1.0, 1.0]
        simple = np.array([[0.5, 0.8], [0.5, 0.8], [0.5, 0.8], [0.5, 0.8]])
        result = core.cluster_bootstrap_effect(dynamic, simple, 100, 7)
        self.assertAlmostEqual(result["point"], 0.2)
        self.assertAlmostEqual(result["lower_95"], 0.2)
        self.assertAlmostEqual(result["upper_95"], 0.2)

    def test_bootstrap_is_deterministic(self):
        dynamic = np.linspace(0, 1, 20)
        simple = np.column_stack([dynamic * 0.5, dynamic * 0.8])
        first = core.cluster_bootstrap_effect(dynamic, simple, 200, 11)
        second = core.cluster_bootstrap_effect(dynamic, simple, 200, 11)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
