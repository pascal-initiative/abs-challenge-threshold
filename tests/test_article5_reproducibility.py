import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "research/article5/reproducibility_core.py"
SPEC = importlib.util.spec_from_file_location("article5_reproducibility_core", MODULE_PATH)
core = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = core
SPEC.loader.exec_module(core)


class Article5ReproducibilityTests(unittest.TestCase):
    def test_identical_trees(self):
        with tempfile.TemporaryDirectory() as left, tempfile.TemporaryDirectory() as right:
            Path(left, "a.txt").write_text("same\n")
            Path(right, "a.txt").write_text("same\n")
            rows = core.compare_inventories(
                core.file_inventory(Path(left)), core.file_inventory(Path(right))
            )
            self.assertEqual(len(rows), 1)
            self.assertTrue(rows[0]["byte_identical"])

    def test_missing_and_changed_files_fail(self):
        first = {
            "a": {"size": 1, "sha256": "x"},
            "only_a": {"size": 2, "sha256": "y"},
        }
        second = {
            "a": {"size": 1, "sha256": "z"},
            "only_b": {"size": 2, "sha256": "y"},
        }
        rows = core.compare_inventories(first, second)
        self.assertFalse(any(row["byte_identical"] for row in rows))

    def test_expected_scientific_failures_are_accepted_outputs(self):
        statuses = core.accepted_gate_statuses({
            "g5": {"status": "PASS"},
            "g6": {
                "build_status": "PASS",
                "scientific_status": "RESTRICTED_PLAYER_PROBABILITY_NOT_IDENTIFIED",
            },
            "g7": {
                "build_status": "PASS",
                "scientific_status": "RESTRICTED_DELTAW_ZERO_BY_CONSTRUCTION",
            },
            "g8": {
                "computational_status": "PASS",
                "gate_status": "FAIL_STABILITY_AND_INCOMPLETE_MANDATORY_SENSITIVITIES",
                "playbook_allowed": False,
            },
            "g8_wp": {
                "computational_status": "PASS",
                "win_probability_status": "FAIL_VALIDATION",
                "original_g8_status": "FAILED_UNCHANGED",
                "playbook_allowed": False,
            },
            "g9": {
                "build_status": "PASS",
                "numerical_benchmark_condition": "PASS",
                "scientific_status": "NOT_DEMONSTRATED_NONDEPLOYABLE_UPPER_BENCHMARK",
                "restrictions": {"playbook_allowed": False},
            },
        })
        self.assertTrue(all(statuses.values()))


if __name__ == "__main__":
    unittest.main()
