import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "research/article5/run_ct_s1_reconstruction.py"
SPEC = importlib.util.spec_from_file_location("article5_ct_s1_reconstruction", MODULE_PATH)
reconstruction = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = reconstruction
SPEC.loader.exec_module(reconstruction)


PREFLIGHT = {
    "status": "PASS_CTS1_READY_FOR_CTS2_PROCESSING",
    "window": {"start": "2026-09-11", "end": "2026-09-27"},
    "final_games": 2,
    "unique_urls": 5,
    "stored_unique_object_bytes": 10,
    "official_daily_challenges": 2,
    "deduplicated_team_abs_challenges": 2,
    "raw_snapshot_sha256": "synthetic-raw",
    "source_sha256s": ["synthetic-source"],
}


def write_csv(path, rows):
    import csv
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def passing_runner(root, start, end, output, raw):
    validation = {
        "gate_passed": True,
        "stop_reasons": [],
        "geometry_method": reconstruction.GEOMETRY_METHOD,
        "daily_reconciliation": [
            {"game_date": "2026-09-11", "expected": 1, "observed": 1},
            {"game_date": "2026-09-27", "expected": 1, "observed": 1},
        ],
    }
    quality = {"expected_games": 2, "successfully_processed_games": 2}
    processed = output / "processed"
    processed.mkdir(parents=True)
    (processed / "run_manifest.json").write_text(json.dumps({
        "start": start, "end": end, "expected_games": 2,
        "processed_games": 2, "gate_passed": True,
        "source_sha256s": ["synthetic-source"],
    }))
    (processed / "validation_report.json").write_text(json.dumps(validation))
    write_csv(processed / "pitches.csv", [
        {"game_date": "2026-09-11", "pitch_key": "1"},
        {"game_date": "2026-09-27", "pitch_key": "2"},
    ])
    write_csv(processed / "challenges.csv", [
        {"game_date": "2026-09-11", "pitch_key": "1"},
        {"game_date": "2026-09-27", "pitch_key": "2"},
    ])
    return validation, quality


def failing_runner(root, start, end, output, raw):
    _, quality = passing_runner(root, start, end, output, raw)
    validation = {
        "gate_passed": False,
        "stop_reasons": ["SYNTHETIC_RECONCILIATION_FAILURE"],
        "geometry_method": reconstruction.GEOMETRY_METHOD,
        "daily_reconciliation": [],
    }
    (output / "processed/validation_report.json").write_text(json.dumps(validation))
    (output / "processed/run_manifest.json").write_text(json.dumps({
        "start": start, "end": end, "expected_games": 2,
        "processed_games": 2, "gate_passed": False,
        "source_sha256s": ["synthetic-source"],
    }))
    return validation, quality


class CTS1ReconstructionTests(unittest.TestCase):
    def test_passing_reconstruction_is_released_to_cts3(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = root / "data/ct_s1/raw"
            raw.mkdir(parents=True)
            (raw / "object").write_text("immutable")
            preflight = root / "data/ct_s1/preflight/validation.json"
            preflight.parent.mkdir(parents=True)
            preflight.write_text(json.dumps(PREFLIGHT))
            protected = root / "protected.txt"
            protected.write_text("locked")
            result = reconstruction.run_reconstruction(
                root, raw, preflight, root / "data/ct_s1/reconstructed",
                runner=passing_runner,
                preflight_validator=lambda _: dict(PREFLIGHT),
                protected=[protected],
            )
            self.assertEqual(result["status"], "PASS_CTS2_READY_FOR_CTS3")
            self.assertTrue(all(result["checks"].values()))

    def test_changed_raw_snapshot_is_rejected_before_runner(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = root / "data/ct_s1/raw"
            raw.mkdir(parents=True)
            (raw / "object").write_text("immutable")
            preflight = root / "data/ct_s1/preflight/validation.json"
            preflight.parent.mkdir(parents=True)
            preflight.write_text(json.dumps(PREFLIGHT))
            changed = dict(PREFLIGHT, raw_snapshot_sha256="changed")
            with self.assertRaises(reconstruction.ReconstructionError):
                reconstruction.run_reconstruction(
                    root, raw, preflight, root / "data/ct_s1/reconstructed",
                    runner=lambda *args: self.fail("runner must not execute"),
                    preflight_validator=lambda _: changed,
                    protected=[],
                )

    def test_failed_pipeline_gate_remains_quarantined(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = root / "data/ct_s1/raw"
            raw.mkdir(parents=True)
            (raw / "object").write_text("immutable")
            preflight = root / "data/ct_s1/preflight/validation.json"
            preflight.parent.mkdir(parents=True)
            preflight.write_text(json.dumps(PREFLIGHT))
            protected = root / "protected.txt"
            protected.write_text("locked")
            result = reconstruction.run_reconstruction(
                root, raw, preflight, root / "data/ct_s1/reconstructed",
                runner=failing_runner,
                preflight_validator=lambda _: dict(PREFLIGHT),
                protected=[protected],
            )
            self.assertEqual(result["status"], "FAIL_CTS2")
            self.assertEqual(
                result["pipeline_stop_reasons"],
                ["SYNTHETIC_RECONCILIATION_FAILURE"],
            )

    def test_nonempty_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "data/ct_s1/reconstructed"
            output.mkdir(parents=True)
            (output / "stale").write_text("do not mix runs")
            with self.assertRaises(reconstruction.ReconstructionError):
                reconstruction.run_reconstruction(
                    root, root / "raw", root / "preflight.json", output,
                    protected=[],
                )


if __name__ == "__main__":
    unittest.main()
