import hashlib
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.sprint5 import (INDIFFERENCE_WP, PitchState, bellman_tables,
                         classify_decision, inventory_after,
                         transition_called_pitch)

ROOT = Path(__file__).resolve().parents[1]


class StateTransitionTests(unittest.TestCase):
    def state(self, **kw):
        base = dict(inning=5, half_inning="top", balls=1, strikes=1, outs=1,
                    on_1b=0, on_2b=0, on_3b=0, home_score=2, away_score=1)
        base.update(kw); return PitchState(**base)

    def test_ordinary_ball_and_strike(self):
        self.assertEqual(transition_called_pitch(self.state(), "BALL")["balls"], 2)
        self.assertEqual(transition_called_pitch(self.state(), "STRIKE")["strikes"], 2)

    def test_strike_three_and_inning_end(self):
        out = transition_called_pitch(self.state(strikes=2), "STRIKE")
        self.assertEqual((out["outs"], out["plate_appearance_status"]), (2, "STRIKEOUT"))
        end = transition_called_pitch(self.state(strikes=2, outs=2, on_1b=1), "STRIKE")
        self.assertEqual((end["half_inning"], end["outs"], end["base_state"]), ("bottom", 0, "000"))

    def test_ball_four_and_forced_run(self):
        walk = transition_called_pitch(self.state(balls=3, on_2b=1), "BALL")
        self.assertEqual((walk["base_state"], walk["runs_scored"]), ("110", 0))
        loaded = transition_called_pitch(self.state(balls=3, on_1b=1, on_2b=1, on_3b=1), "BALL")
        self.assertEqual((loaded["base_state"], loaded["away_score"], loaded["runs_scored"]), ("111", 2, 1))


class InventoryAndPolicyTests(unittest.TestCase):
    def test_inventory_retention_loss_and_exhaustion(self):
        self.assertEqual(inventory_after(1, "OVERTURNED"), 1)
        self.assertEqual(inventory_after(2, "CONFIRMED"), 1)
        self.assertEqual(inventory_after(1, "CONFIRMED"), 0)

    def test_decision_categories_and_hindsight_separation(self):
        self.assertEqual(classify_decision(.01, "CHALLENGE")[1], "STRONGLY_OPTIMAL")
        self.assertEqual(classify_decision(.001, "HOLD")[1], "SUBOPTIMAL")
        self.assertEqual(classify_decision(-.01, "CHALLENGE")[1], "STRONGLY_SUBOPTIMAL")
        before = classify_decision(.001, "CHALLENGE")
        future_realized_cost = 99.0
        self.assertEqual(before, classify_decision(.001, "CHALLENGE"))
        self.assertGreater(future_realized_cost, 0)

    def test_policy_determinism(self):
        p = np.array([.2, .5, .8]); gain = np.array([.001, .005, .02])
        a = bellman_tables(p, gain); b = bellman_tables(p, gain)
        for key in a: np.testing.assert_array_equal(a[key], b[key])


class Sprint5OutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = ROOT / "data/analysis/sprint5"; cls.art = ROOT / "artifacts/sprint5"
        if not cls.data.exists(): raise unittest.SkipTest("Sprint 5 has not run")

    def test_required_outputs(self):
        data = "challenge_opportunities.csv challenge_decision_states.csv challenge_value_estimates.csv decision_quality.csv challenge_inventory_history.csv exhaustion_events.csv post_exhaustion_opportunities.csv resource_cost_summary.csv".split()
        art = "overturn_model_metrics.csv run_expectancy_model_metrics.csv win_probability_model_metrics.csv policy_validation.csv calibration_metrics.csv decision_matrix.csv decision_margin_distribution.csv successful_bad_decisions.csv unsuccessful_good_decisions.csv valuable_holds.csv low_value_challenges.csv timing_analysis.csv count_analysis.csv inventory_analysis.csv offense_defense_comparison.csv exhaustion_sequences.csv counterfactual_preservation.csv benchmark_comparison.csv sensitivity_analysis.csv run_manifest.json".split()
        self.assertTrue(all((self.data / x).is_file() for x in data))
        self.assertTrue(all((self.art / x).is_file() for x in art))
        self.assertEqual(len(list(self.art.glob("*.png"))), 10)

    def test_population_and_probabilities(self):
        o = pd.read_csv(self.data / "challenge_opportunities.csv", low_memory=False)
        self.assertEqual(len(o), 312228); self.assertEqual(o.pitch_key.nunique(), len(o))
        self.assertEqual(set(o.decision_side), {"OFFENSE", "DEFENSE"})
        v = pd.read_csv(self.data / "challenge_value_estimates.csv")
        self.assertTrue(v.P_overturn.between(0, 1).all())
        self.assertTrue(v.required_confidence.between(0, 1).all())

    def test_temporal_integrity_and_hindsight_labels(self):
        for name in ["overturn_model_metrics.csv", "run_expectancy_model_metrics.csv", "win_probability_model_metrics.csv"]:
            f = pd.read_csv(self.art / name); f = f[f.fold.ne("POOLED")]
            self.assertTrue((pd.to_datetime(f.train_end) < pd.to_datetime(f.test_start)).all())
        d = pd.read_csv(self.data / "decision_quality.csv")
        self.assertTrue(d.analysis_perspective.eq("EX_ANTE").all())
        p = pd.read_csv(self.data / "post_exhaustion_opportunities.csv")
        self.assertTrue(p.empty or p.analysis_perspective.eq("HINDSIGHT_DESCRIPTIVE").all())


if __name__ == "__main__": unittest.main()
