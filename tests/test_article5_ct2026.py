import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "research/article5/ct2026_core.py"
SPEC = importlib.util.spec_from_file_location("article5_ct2026_core", MODULE_PATH)
core = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = core
SPEC.loader.exec_module(core)


def enumerate_policy(p, value, actions, inventory):
    def recurse(index, held):
        if index == len(p):
            return 0.0
        if held <= 0 or not actions[held, index]:
            return recurse(index + 1, held)
        return (
            p[index] * (value[index] + recurse(index + 1, held))
            + (1 - p[index]) * recurse(index + 1, held - 1)
        )

    return recurse(0, inventory)


class CT2026CoreTests(unittest.TestCase):
    def test_fixed_ev_policy_challenges_at_cutoff_and_holds_below(self):
        actions = core.fixed_ev_actions(
            np.array([0.5, 0.5, 1.0]),
            np.array([0.099, 0.100, 0.050]),
            cutoff=0.05,
        )
        np.testing.assert_array_equal(actions[0], [False, False, False])
        np.testing.assert_array_equal(actions[1], [False, True, True])
        np.testing.assert_array_equal(actions[2], [False, True, True])

    def test_fixed_ev_policy_is_independent_of_inventory_and_future(self):
        first = core.fixed_ev_actions(
            np.array([0.6, 0.6]), np.array([0.2, 0.01]), cutoff=0.05
        )
        second = core.fixed_ev_actions(
            np.array([0.6, 0.6]), np.array([0.2, 99.0]), cutoff=0.05
        )
        self.assertEqual(first[1, 0], second[1, 0])
        self.assertEqual(first[2, 0], second[2, 0])
        np.testing.assert_array_equal(first[1], first[2])

    def test_fixed_ev_policy_holds_negative_sensitivity_value(self):
        actions = core.fixed_ev_actions(
            np.array([1.0, 1.0]), np.array([-0.1, 0.0]), cutoff=0.0
        )
        np.testing.assert_array_equal(actions[1], [False, True])

    def test_threshold_boundaries_and_monotonicity(self):
        values = np.array([1.0, 2.0, 0.0, 0.0])
        costs = np.array([1.0, 1.0, 1.0, 0.0])
        result = core.challenge_threshold(values, costs)
        self.assertAlmostEqual(result[0], 0.5)
        self.assertLess(result[1], result[0])
        self.assertEqual(result[2], 1.0)
        self.assertTrue(np.isnan(result[3]))
        increasing_cost = core.challenge_threshold(1.0, [0.1, 0.2, 0.3])
        self.assertTrue(np.all(np.diff(increasing_cost) > 0))

    def test_fixed_actions_match_enumeration(self):
        p = np.array([0.4, 0.8, 0.5])
        value = np.array([0.2, 0.5, 0.1])
        innings = np.array([1, 2, 3])
        actions = np.zeros((3, 3), dtype=bool)
        actions[1] = [False, True, True]
        actions[2] = [True, True, True]
        evaluated = core.evaluate_fixed_actions(p, value, innings, actions)
        for inventory in (1, 2):
            self.assertAlmostEqual(
                evaluated["W"][inventory, 0],
                enumerate_policy(p, value, actions, inventory),
                places=12,
            )

    def test_action_does_not_change_when_future_changes(self):
        p = np.array([0.6, 0.6])
        state_codes = np.array([0, 1])
        schedule = np.array([[0.0, 0.0], [0.2, 0.1], [0.1, 0.05]])
        first = core.select_actions(p, np.array([0.3, 0.1]), state_codes, schedule)
        second = core.select_actions(p, np.array([0.3, 99.0]), state_codes, schedule)
        self.assertEqual(first[1, 0], second[1, 0])
        self.assertEqual(first[2, 0], second[2, 0])

    def test_extra_inning_restores_zero_only(self):
        p = np.array([0.0, 1.0])
        value = np.array([0.1, 0.4])
        innings = np.array([9, 10])
        actions = np.ones((3, 2), dtype=bool)
        actions[0] = False
        with_grant = core.evaluate_fixed_actions(p, value, innings, actions)
        without_grant = core.evaluate_fixed_actions(
            p, value, innings, actions, grant_extras=False
        )
        self.assertAlmostEqual(with_grant["W"][0, 0], 0.4)
        self.assertAlmostEqual(with_grant["W"][1, 0], 0.4)
        self.assertAlmostEqual(without_grant["W"][0, 0], 0.0)

    def test_state_policy_converges_without_future_access(self):
        p = np.array([0.6, 0.6, 0.6, 0.6])
        value = np.array([0.2, 0.5, 0.1, 0.4])
        innings = np.array([1, 1, 1, 1])
        state_codes = np.array([0, 1, 0, 1])
        groups = [("a", np.array([0, 1])), ("b", np.array([2, 3]))]
        result = core.fit_state_policy(
            p, value, innings, state_codes, groups, state_count=2
        )
        self.assertTrue(result["converged"])
        self.assertFalse(result["cycle_detected"])
        self.assertLessEqual(result["iterations"], 200)
        self.assertTrue(np.isfinite(result["schedule"]).all())


if __name__ == "__main__":
    unittest.main()
