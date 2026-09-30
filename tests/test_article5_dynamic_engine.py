import importlib.util
import itertools
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "research/article5/dynamic_core.py"
SPEC = importlib.util.spec_from_file_location("article5_dynamic_core", MODULE_PATH)
core = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = core
SPEC.loader.exec_module(core)


def enumerate_fixed_policy(p, value, use, inventory):
    total = 0.0
    for outcomes in itertools.product([0, 1], repeat=len(p)):
        probability = 1.0
        held = inventory
        reward = 0.0
        for i, success in enumerate(outcomes):
            if held == 0 or not use[i]:
                if success:
                    probability = 0.0
                continue
            probability *= p[i] if success else 1 - p[i]
            if success:
                reward += value[i]
            else:
                held -= 1
        total += probability * reward
    return total


class Article5DynamicEngineTests(unittest.TestCase):
    def test_fixed_policy_matches_enumeration(self):
        p = np.array([0.4, 0.8, 0.5])
        value = np.array([0.2, 0.5, 0.1])
        innings = np.array([1, 2, 3])
        solution = core.backward_values(p, value, innings, "confidence_0.5")
        use = p >= 0.5
        for inventory in (1, 2):
            self.assertAlmostEqual(
                solution["W"][inventory, 0],
                enumerate_fixed_policy(p, value, use, inventory),
                places=12,
            )

    def test_dynamic_dominates_fixed_policies(self):
        p = [0.3, 0.8, 0.6]
        value = [0.4, 0.2, 0.7]
        innings = [1, 5, 9]
        dynamic = core.backward_values(p, value, innings, "dynamic")["W"][1, 0]
        for policy in ["never", "confidence_0.5", "confidence_0.6", "ev_0.05"]:
            fixed = core.backward_values(p, value, innings, policy)["W"][1, 0]
            self.assertGreaterEqual(dynamic + 1e-12, fixed)

    def test_success_retains_and_failure_consumes(self):
        success = core.backward_values([1, 1], [0.2, 0.3], [1, 1], "dynamic")
        failure = core.backward_values([0, 1], [0.2, 0.3], [1, 1], "dynamic")
        self.assertAlmostEqual(success["W"][1, 0], 0.5)
        self.assertAlmostEqual(failure["W"][1, 0], 0.3)

    def test_extra_inning_grant_only_when_empty(self):
        p = [0.0, 1.0]
        value = [0.1, 0.4]
        innings = [9, 10]
        solution = core.backward_values(p, value, innings, "dynamic")
        self.assertAlmostEqual(solution["W"][0, 0], 0.4)
        self.assertAlmostEqual(solution["W"][1, 0], 0.4)

    def test_game_end_truncates_value(self):
        solution = core.backward_values([0.5], [0.4], [9], "dynamic")
        self.assertAlmostEqual(solution["W"][1, 0], 0.2)
        self.assertEqual(solution["W"][1, 1], 0.0)


if __name__ == "__main__":
    unittest.main()
