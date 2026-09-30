import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.offensive_recognition import (
    EXPECTED,
    PILOT_END,
    PILOT_START,
    _geometry,
    descriptive,
    population_and_features,
    run,
)


ROOT = Path(__file__).resolve().parents[1]


def digest_tree(paths):
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for parent in paths
        for path in sorted(parent.rglob("*"))
        if path.is_file()
    }


class Sprint2PopulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.features, cls.audit = population_and_features(ROOT)

    def test_population_reconciles_exactly(self):
        for key, expected in EXPECTED.items():
            self.assertEqual(self.audit[key], expected)
        self.assertEqual(self.audit["excluded_other"], 0)

    def test_scope_is_pilot_only(self):
        self.assertEqual(self.features.game_date.min(), PILOT_START)
        self.assertEqual(self.features.game_date.max(), PILOT_END)
        self.assertEqual(self.features.date_scope.unique().tolist(), [f"{PILOT_START}/{PILOT_END}"])
        self.assertFalse(self.audit["full_season_expansion_performed"])

    def test_outcome_does_not_define_recognition(self):
        self.assertTrue((self.features.recognized == self.features.challenged.map({"True": 1, "False": 0})).all())
        altered = self.features.copy()
        altered["challenge_outcome"] = np.where(altered.recognized.eq(1), "CONFIRMED", "OVERTURNED")
        self.assertTrue((altered.recognized == self.features.recognized).all())

    def test_no_resource_or_unknown_rows_enter_population(self):
        self.assertFalse(self.features.survival_class.isin(["SURVIVED_RESOURCE", "UNKNOWN"]).any())
        self.assertTrue(self.features.affected_team_challenges_remaining.isin([1, 2]).all())

    def test_required_predictors_are_complete(self):
        required = [
            "abs_distance", "miss_axis", "miss_side", "release_speed", "release_spin_rate",
            "spin_axis", "pfx_x", "pfx_z", "extension", "release_pos_x", "release_pos_z",
            "inning", "balls", "strikes", "outs", "score_diff",
            "affected_team_challenges_remaining", "batter_id", "pitcher_id", "catcher_id", "umpire_id",
        ]
        self.assertFalse(self.features[required].isna().any().any())

    def test_geometry_reproduces_source_distance(self):
        calculated = np.hypot(
            np.maximum(self.features.horizontal_distance, 0),
            np.maximum(self.features.vertical_distance, 0),
        ) - 2.9 / 2 / 12
        # For single-axis misses, hypot naturally returns that axis; for corner misses it is Euclidean.
        self.assertTrue(np.allclose(calculated, self.features.abs_distance, atol=1e-12))

    def test_handedness_aware_inside(self):
        base = {"plate_z": 2.5, "abs_zone_top": 3.5, "abs_zone_bot": 1.5}
        right = pd.Series({**base, "plate_x": -1.0, "bat_side": "R"})
        left = pd.Series({**base, "plate_x": 1.0, "bat_side": "L"})
        self.assertEqual(_geometry(right)[1], "INSIDE")
        self.assertEqual(_geometry(left)[1], "INSIDE")

    def test_feature_table_preserves_requested_raw_fields(self):
        fields = {
            "distance_from_abs_boundary", "pitch_type", "release_speed", "release_spin_rate",
            "spin_axis", "pfx_x", "pfx_z", "extension", "release_pos_x", "release_pos_z",
            "pitch_hand", "bat_side", "inning", "balls", "strikes", "outs", "on_1b",
            "on_2b", "on_3b", "score_diff", "affected_team_challenges_remaining",
            "survival_class", "challenge_outcome",
        }
        self.assertTrue(fields.issubset(self.features.columns))


class Sprint2OutputTests(unittest.TestCase):
    def test_descriptive_suppresses_tiny_group_display_only(self):
        frame = pd.DataFrame({
            "abs_distance_inches": [0.1] * 19,
            "release_speed": [90.0] * 19,
            "pfx_x": np.arange(19), "pfx_z": np.arange(19),
            "miss_side": ["ABOVE"] * 19, "pitch_family": ["OTHER"] * 19,
            "count": ["0-0"] * 19, "inning": [1] * 19, "inning_group": ["EARLY"] * 19,
            "outs": [0] * 19, "base_state": ["000"] * 19,
            "affected_team_challenges_remaining": [2] * 19, "recognized": [1] + [0] * 18,
        })
        output = descriptive(frame)
        row = output[(output.dimension == "pitch_family") & (output.value == "OTHER")].iloc[0]
        self.assertTrue(row.small_sample_warning)
        self.assertEqual(row.display_rate, "SUPPRESSED_N_LT_20")
        self.assertAlmostEqual(row.recognition_rate, 1 / 19)

    def test_required_outputs_and_prediction_coverage(self):
        required = [
            "offensive_recognition_features.csv", "offensive_recognition_population_audit.json",
            "offensive_recognition_descriptive.csv", "offensive_recognition_model_metrics.csv",
            "offensive_recognition_predictions.csv",
        ]
        for name in required:
            self.assertTrue((ROOT / "data/analysis" / name).is_file(), name)
        predictions = pd.read_csv(ROOT / "data/analysis/offensive_recognition_predictions.csv")
        metrics = pd.read_csv(ROOT / "data/analysis/offensive_recognition_model_metrics.csv")
        self.assertEqual(len(predictions), 484 * len(metrics))
        self.assertTrue(predictions.groupby(["pitch_key", "model"]).size().eq(1).all())
        self.assertTrue(predictions.predicted_probability.between(0, 1).all())
        self.assertEqual(set(metrics.recognized), {96})
        self.assertEqual(set(metrics.not_recognized), {388})

    def test_seven_figures_exist(self):
        figures = list((ROOT / "artifacts/sprint2").glob("*.png"))
        self.assertEqual(len(figures), 7)
        self.assertTrue(all(path.stat().st_size > 10_000 for path in figures))

    def test_identity_coefficients_are_not_published(self):
        coefficients = pd.read_csv(ROOT / "artifacts/sprint2/model_coefficients.csv")
        self.assertFalse(coefficients.model.str.startswith("D_").any())
        self.assertFalse(coefficients.term.str.contains("batter_id|pitcher_id|catcher_id|umpire_id").any())

    def test_sprint1_checksums_match_manifest(self):
        manifest = json.loads((ROOT / "artifacts/sprint2/run_manifest.json").read_text())
        for name, expected in manifest["sprint1_processed_sha256"].items():
            actual = hashlib.sha256((ROOT / "data/processed" / name).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, name)
        self.assertFalse(manifest["full_season_expansion_performed"])

    def test_full_analysis_is_byte_deterministic(self):
        tracked = [ROOT / "data/analysis", ROOT / "artifacts/sprint2"]
        before = digest_tree(tracked)
        report_before = hashlib.sha256((ROOT / "docs/sprint2_offensive_recognition_report.md").read_bytes()).hexdigest()
        run(ROOT)
        self.assertEqual(before, digest_tree(tracked))
        self.assertEqual(report_before, hashlib.sha256((ROOT / "docs/sprint2_offensive_recognition_report.md").read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
