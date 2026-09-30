import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "research/article5/build_correction_values.py"
SPEC = importlib.util.spec_from_file_location("article5_correction_value", MODULE_PATH)
cv = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cv
SPEC.loader.exec_module(cv)


class Record:
    obs_state_valid = True
    obs_runs = 1
    obs_inning_ended = False
    obs_walkoff = False
    obs_balls = 2
    obs_strikes = 1
    obs_outs = 1
    obs_base_state = "010"


class Article5CorrectionValueTests(unittest.TestCase):
    def re_table(self, valid=False):
        rows = []
        for outs in range(3):
            for bases in [f"{value:03b}" for value in range(8)]:
                for balls, strikes in cv.count_states():
                    value = (0.8, 0.5, 0.2)[outs] if valid else 1.0 - balls * 0.2 + strikes * 0.3
                    rows.append({
                        "balls": balls,
                        "strikes": strikes,
                        "outs": outs,
                        "base_state": bases,
                        "raw_mean": value,
                        "n_pitches": 10,
                        "base_out_mean": value,
                        "re_smoothed": value,
                    })
        return pd.DataFrame(rows)

    def test_global_constraint_matrix_includes_terminal_edges(self):
        matrix, lower, kinds = cv.global_constraints([f"{value:03b}" for value in range(8)])
        self.assertEqual(matrix.shape, (552, 288))
        self.assertEqual(len(lower), 552)
        self.assertEqual(kinds.count("TERMINAL_FULL_COUNT"), 24)

    def test_projection_enforces_all_constraints(self):
        projected, solver = cv.build_constrained_table(self.re_table())
        diagnostics = cv.full_constraint_diagnostics(projected, "re_constrained")
        self.assertTrue(solver["solver_success"])
        self.assertEqual(diagnostics["violations"], 0)

    def test_projection_is_identity_for_valid_surface(self):
        table = self.re_table(valid=True)
        projected, _ = cv.build_constrained_table(table)
        expected = table.sort_values(["outs", "base_state", "balls", "strikes"]).re_smoothed
        np.testing.assert_allclose(projected.re_constrained, expected, atol=1e-8)

    def test_walk_successors_and_loaded_run(self):
        self.assertEqual(cv.walk_successor("001"), ("101", 0))
        self.assertEqual(cv.walk_successor("010"), ("110", 0))
        self.assertEqual(cv.walk_successor("111"), ("111", 1))

    def test_state_value_adds_runs_and_lookup(self):
        lookup = {(2, 1, 1, "010"): 0.75}
        self.assertEqual(cv.state_value(Record(), "obs", lookup), 1.75)

    def test_ended_state_excludes_future_expectancy(self):
        record = Record()
        record.obs_inning_ended = True
        lookup = {(2, 1, 1, "010"): 0.75}
        self.assertEqual(cv.state_value(record, "obs", lookup), 1.0)

    def test_side_orientation(self):
        self.assertAlmostEqual(cv.correction_value(0.2, 0.7, "OFFENSE"), 0.5)
        self.assertAlmostEqual(cv.correction_value(0.7, 0.2, "DEFENSE"), 0.5)


if __name__ == "__main__":
    unittest.main()
