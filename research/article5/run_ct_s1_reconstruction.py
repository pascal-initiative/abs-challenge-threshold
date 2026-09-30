"""Run and gate isolated CT-S1 reconstruction after raw preflight passes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT_DEFAULT = HERE.parents[1]
sys.path.insert(0, str(ROOT_DEFAULT))

from research.article5.acquire_ct_s1 import END, START, stable_json  # noqa: E402
from research.article5.validate_ct_s1_raw import validate_snapshot  # noqa: E402
from src.pipeline import run as pipeline_run  # noqa: E402


GEOMETRY_METHOD = "abs_2026_circle_rectangle_r1.45in_v1"


class ReconstructionError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_fingerprint(root: Path) -> str:
    inventory = {
        str(path.relative_to(root)): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
    return hashlib.sha256(stable_json(inventory).encode("utf-8")).hexdigest()


def protected_inputs(root: Path) -> list[Path]:
    return [
        root / "data/full_season/processed/pitches.csv",
        root / "data/full_season/processed/challenges.csv",
        root / "research/article4/output/article4_re288_table.csv",
        root / "research/article5/PREREGISTRATION.md",
        root / "research/article5/PREREGISTRATION.sha256",
        root / "research/article5/CT2026_SPEC.md",
        root / "research/article5/CT2026_SPEC.sha256",
        root / "research/article5/AMENDMENT_005_CT_SUCCESSOR_STANDARD.md",
        root / "research/article5/CT_SUCCESSOR_VALIDATION_PLAN.md",
    ]


def _hash_paths(paths: list[Path]) -> dict[str, str]:
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise ReconstructionError(f"protected inputs missing: {missing}")
    return {str(path): sha256(path) for path in paths}


def _csv_rows(path: Path) -> list[dict]:
    if not path.is_file():
        raise ReconstructionError(f"required reconstruction output missing: {path}")
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def run_reconstruction(
    root: Path,
    raw: Path,
    preflight_path: Path,
    output: Path,
    runner=pipeline_run,
    preflight_validator=validate_snapshot,
    protected: list[Path] | None = None,
) -> dict:
    root = root.resolve()
    raw = raw.resolve()
    preflight_path = preflight_path.resolve()
    output = output.resolve()
    allowed = (root / "data/ct_s1").resolve()
    try:
        output.relative_to(allowed)
    except ValueError as error:
        raise ReconstructionError("output must remain under data/ct_s1") from error
    if output.exists() and any(output.iterdir()):
        raise ReconstructionError("reconstruction output directory must be empty")
    if not preflight_path.is_file():
        raise ReconstructionError("preflight validation record is missing")
    saved_preflight = json.loads(preflight_path.read_text())
    if saved_preflight.get("status") != "PASS_CTS1_READY_FOR_CTS2_PROCESSING":
        raise ReconstructionError("saved preflight is not passing")
    current_preflight = preflight_validator(raw)
    keys = {
        "status", "window", "final_games", "unique_urls",
        "stored_unique_object_bytes", "official_daily_challenges",
        "deduplicated_team_abs_challenges", "raw_snapshot_sha256",
        "source_sha256s",
    }
    if {key: saved_preflight.get(key) for key in keys} != {
        key: current_preflight.get(key) for key in keys
    }:
        raise ReconstructionError("raw snapshot no longer matches saved preflight")

    raw_before = tree_fingerprint(raw)
    protected_paths = protected if protected is not None else protected_inputs(root)
    protected_before = _hash_paths(protected_paths)
    validation, quality = runner(
        root,
        START.isoformat(),
        END.isoformat(),
        output,
        raw,
    )
    raw_after = tree_fingerprint(raw)
    protected_after = _hash_paths(protected_paths)

    run_manifest_path = output / "processed/run_manifest.json"
    validation_path = output / "processed/validation_report.json"
    if not run_manifest_path.is_file() or not validation_path.is_file():
        raise ReconstructionError("pipeline did not emit required validation manifests")
    run_manifest = json.loads(run_manifest_path.read_text())
    emitted_validation = json.loads(validation_path.read_text())
    pitches = _csv_rows(output / "processed/pitches.csv") if validation.get("gate_passed") else []
    challenges = _csv_rows(output / "processed/challenges.csv")
    pitch_dates = [row["game_date"] for row in pitches]
    challenge_dates = [row["game_date"] for row in challenges]
    expected_games = int(current_preflight["final_games"])
    expected_challenges = int(current_preflight["official_daily_challenges"])

    checks = {
        "preflight_revalidated": True,
        "pipeline_gate_passed": bool(validation.get("gate_passed")),
        "emitted_validation_matches": emitted_validation == validation,
        "window_matches": (
            run_manifest.get("start") == START.isoformat()
            and run_manifest.get("end") == END.isoformat()
        ),
        "game_counts_reconcile": (
            int(quality.get("expected_games", -1)) == expected_games
            and int(quality.get("successfully_processed_games", -1)) == expected_games
            and int(run_manifest.get("expected_games", -1)) == expected_games
            and int(run_manifest.get("processed_games", -1)) == expected_games
        ),
        "pipeline_sources_match_preflight": (
            sorted(run_manifest.get("source_sha256s", []))
            == sorted(current_preflight["source_sha256s"])
        ),
        "challenge_count_reconciles": len(challenges) == expected_challenges,
        "pitch_dates_isolated": bool(pitch_dates) and (
            min(pitch_dates) >= START.isoformat() and max(pitch_dates) <= END.isoformat()
        ),
        "challenge_dates_isolated": bool(challenge_dates) and (
            min(challenge_dates) >= START.isoformat()
            and max(challenge_dates) <= END.isoformat()
        ),
        "geometry_method_matches": validation.get("geometry_method") == GEOMETRY_METHOD,
        "daily_totals_reconcile": bool(validation.get("daily_reconciliation")) and all(
            int(row["expected"]) == int(row["observed"])
            for row in validation.get("daily_reconciliation", [])
        ),
        "raw_snapshot_unchanged": raw_before == raw_after,
        "development_inputs_unchanged": protected_before == protected_after,
    }
    status = "PASS_CTS2_READY_FOR_CTS3" if all(checks.values()) else "FAIL_CTS2"
    result = {
        "research_identity": "CT-S1",
        "status": status,
        "window": {"start": START.isoformat(), "end": END.isoformat()},
        "checks": checks,
        "counts": {
            "games": expected_games,
            "physical_pitches": len(pitches),
            "official_challenges": len(challenges),
        },
        "raw_snapshot_sha256": current_preflight["raw_snapshot_sha256"],
        "protected_input_sha256": protected_after,
        "pipeline_stop_reasons": validation.get("stop_reasons", []),
        "next_gate": "CTS3_FROZEN_IMPLEMENTATION" if status.startswith("PASS") else None,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "CTS2_VALIDATION.json").write_text(stable_json(result))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--raw-dir", type=Path)
    parser.add_argument("--preflight", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    raw = (args.raw_dir or root / "data/ct_s1/raw").resolve()
    preflight = (
        args.preflight or root / "data/ct_s1/preflight/validation.json"
    ).resolve()
    output = (args.output or root / "data/ct_s1/reconstructed").resolve()
    try:
        result = run_reconstruction(root, raw, preflight, output)
    except ReconstructionError as error:
        print(stable_json({"status": "FAIL_CTS2", "error": str(error)}), end="")
        return 2
    print(stable_json(result), end="")
    return 0 if result["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
