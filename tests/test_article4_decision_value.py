import itertools
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research/article4/decision_value"))
from dv_core import classify_spend, edge_class, suffix_option_values, suffix_prophet  # noqa: E402


def brute_force(p, v, q, k):
    """Enumerate every use/success path explicitly."""
    total = 0.0
    n = len(p)
    for uses in itertools.product([0, 1], repeat=n):
        for succ in itertools.product([0, 1], repeat=n):
            prob, inv, val = 1.0, k, 0.0
            for i in range(n):
                if inv == 0:
                    if uses[i] or succ[i]:
                        prob = 0.0
                    continue
                prob *= q[i] if uses[i] else 1 - q[i]
                if uses[i]:
                    prob *= p[i] if succ[i] else 1 - p[i]
                    if succ[i]:
                        val += v[i]
                    else:
                        inv -= 1
                elif succ[i]:
                    prob = 0.0
            total += prob * val
    return total


class DecisionValueCore(unittest.TestCase):
    def test_recursion_matches_enumeration(self):
        rng = np.random.default_rng(1)
        for _ in range(20):
            n = rng.integers(1, 5)
            p, v, q = rng.uniform(size=n), rng.uniform(0, 1, size=n), rng.uniform(size=n)
            V = suffix_option_values(p, v, q, 2)
            for k in (1, 2):
                self.assertAlmostEqual(V[k, 0], brute_force(p, v, q, k), places=10)
                self.assertAlmostEqual(V[k, 1], brute_force(p[1:], v[1:], q[1:], k), places=10)

    def test_success_retains_challenge(self):
        V = suffix_option_values([1.0, 1.0], [0.3, 0.4], [1, 1], 1)
        self.assertAlmostEqual(V[1, 0], 0.7)
        V = suffix_option_values([0.0, 1.0], [0.3, 0.4], [1, 1], 1)
        self.assertAlmostEqual(V[1, 0], 0.0)

    def test_second_challenge_worth_less(self):
        V = suffix_option_values([.6, .5, .7], [.2, .1, .3], [1, 1, 1], 2)
        self.assertGreaterEqual(V[1, 0], V[2, 0] - V[1, 0])

    def test_prophet(self):
        t1, t2 = suffix_prophet([.1, .5, .2])
        self.assertEqual((t1[0], t2[0], t1[2], t1[3]), (.5, .7, .2, 0))

    def test_edge_symmetric_across_boundary(self):
        top = 3.4; bot = 1.6
        e = edge_class([0.0, 0.0, 0.8, 0.6, -0.8], [3.45, 3.35, 2.5, 2.5, 2.5], [top] * 5, [bot] * 5, ["R", "R", "R", "R", "R"])
        self.assertEqual(list(e), ["TOP", "TOP", "OUTSIDE", "OUTSIDE", "INSIDE"])

    def test_classify(self):
        self.assertEqual(list(classify_spend([.3, .01, .1], [.05, .05, .05], [.2, .2, .2])),
                         ["IMMEDIATE_EXCEEDS_PRESERVATION", "PRESERVATION_EXCEEDS_IMMEDIATE", "OVERLAPPING"])


if __name__ == "__main__":
    unittest.main()
