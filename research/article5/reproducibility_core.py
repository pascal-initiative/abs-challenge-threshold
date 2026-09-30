"""Pure helpers for the ABS-05 Gate G10 reproducibility audit."""
from __future__ import annotations

import hashlib
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_inventory(root: Path) -> dict[str, dict]:
    return {
        str(path.relative_to(root)): {
            "size": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def compare_inventories(first: dict, second: dict) -> list[dict]:
    rows = []
    for relative_path in sorted(set(first) | set(second)):
        a = first.get(relative_path)
        b = second.get(relative_path)
        rows.append({
            "relative_path": relative_path,
            "present_run_a": a is not None,
            "present_run_b": b is not None,
            "bytes_run_a": a["size"] if a else None,
            "bytes_run_b": b["size"] if b else None,
            "sha256_run_a": a["sha256"] if a else None,
            "sha256_run_b": b["sha256"] if b else None,
            "byte_identical": bool(a and b and a == b),
        })
    return rows


def accepted_gate_statuses(validation_by_gate: dict[str, dict]) -> dict[str, bool]:
    g5 = validation_by_gate["g5"]
    g6 = validation_by_gate["g6"]
    g7 = validation_by_gate["g7"]
    g8 = validation_by_gate["g8"]
    g8_wp = validation_by_gate["g8_wp"]
    g9 = validation_by_gate["g9"]
    return {
        "g5_pass_preserved": g5.get("status") == "PASS",
        "g6_computation_pass_preserved": (
            g6.get("build_status") == "PASS"
            and g6.get("scientific_status") == "RESTRICTED_PLAYER_PROBABILITY_NOT_IDENTIFIED"
        ),
        "g7_computation_pass_preserved": (
            g7.get("build_status") == "PASS"
            and g7.get("scientific_status") == "RESTRICTED_DELTAW_ZERO_BY_CONSTRUCTION"
        ),
        "g8_failure_preserved": (
            g8.get("computational_status") == "PASS"
            and str(g8.get("gate_status", "")).startswith("FAIL_STABILITY")
            and g8.get("playbook_allowed") is False
        ),
        "g8_win_model_rejection_preserved": (
            g8_wp.get("computational_status") == "PASS"
            and g8_wp.get("win_probability_status") == "FAIL_VALIDATION"
            and g8_wp.get("original_g8_status") == "FAILED_UNCHANGED"
            and g8_wp.get("playbook_allowed") is False
        ),
        "g9_upper_benchmark_status_preserved": (
            g9.get("build_status") == "PASS"
            and g9.get("numerical_benchmark_condition") == "PASS"
            and g9.get("scientific_status")
            == "NOT_DEMONSTRATED_NONDEPLOYABLE_UPPER_BENCHMARK"
            and g9.get("restrictions", {}).get("playbook_allowed") is False
        ),
    }
