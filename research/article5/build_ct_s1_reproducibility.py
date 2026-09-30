"""Run the frozen CT-S1 successor chain twice and require identical bytes."""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT_DEFAULT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from ct_s1_assurance import (  # noqa: E402
    compare_clean_builds,
    protected_hashes,
    validate_json_files_have_no_runtime_metadata,
)
from reproducibility_core import compare_inventories, file_inventory, sha256  # noqa: E402


BUILD_VERSION = "ct-s1.0-cts10"
GATES = ("cts3", "temporal", "cts7", "cts9")


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def clone_path(source: Path, destination: Path) -> None:
    """Prefer APFS copy-on-write; fall back to ordinary copying."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = ["cp", "-cR" if source.is_dir() else "-c", str(source), str(destination)]
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode == 0:
        return
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)


def populate_isolated_root(source_root: Path, isolated_root: Path) -> None:
    """Copy only inputs and accepted artifacts required by the successor chain."""
    relative_paths = [
        "research/article5",
        "research/article4",
        "data/full_season/processed/pitches.csv",
        "data/full_season/processed/challenges.csv",
        "data/ct_s1/preflight/validation.json",
        "data/ct_s1/reconstructed/CTS2_VALIDATION.json",
        "data/ct_s1/reconstructed/processed/run_manifest.json",
        "data/ct_s1/reconstructed/processed/pitches.csv",
        "data/ct_s1/reconstructed/processed/challenges.csv",
        "data/ct_s1/cts3",
        "data/ct_s1/temporal",
        "data/ct_s1/cts7",
        "data/ct_s1/cts9",
    ]
    isolated_root.mkdir(parents=True, exist_ok=False)
    for relative in relative_paths:
        clone_path(source_root / relative, isolated_root / relative)


def protected_paths(root: Path) -> list[Path]:
    """Inventory raw, processed, accepted, specification, and source inputs."""
    paths = {
        root / "data/full_season/processed/pitches.csv",
        root / "data/full_season/processed/challenges.csv",
        root / "research/article4/output/article4_re288_table.csv",
    }
    for relative in (
        "data/ct_s1/raw",
        "data/ct_s1/preflight",
        "data/ct_s1/reconstructed",
        "data/ct_s1/cts3",
        "data/ct_s1/temporal",
        "data/ct_s1/cts7",
        "data/ct_s1/cts9",
    ):
        paths.update(path for path in (root / relative).rglob("*") if path.is_file())
    article = root / "research/article5"
    paths.update(path for path in article.iterdir() if path.is_file())
    paths.update(path for path in (article / "exploratory").glob("*.py") if path.is_file())
    paths.update(path for path in (root / "research/article4").rglob("*.py") if path.is_file())
    return sorted(paths)


def commands(root: Path, python: Path) -> list[tuple[str, list[str]]]:
    article = root / "research/article5"
    isolated = root / "data/ct_s1/isolated"
    return [
        (
            "cts3",
            [str(python), str(article / "build_ct_s1_prepared.py"), "--root", str(root), "--output", str(isolated / "cts3")],
        ),
        (
            "temporal",
            [str(python), str(article / "build_ct_s1_temporal.py"), "--root", str(root), "--input", str(isolated / "cts3"), "--output", str(isolated / "temporal")],
        ),
        (
            "cts7",
            [str(python), str(article / "build_ct_s1_contrasts.py"), "--root", str(root), "--input", str(isolated / "temporal"), "--output", str(isolated / "cts7")],
        ),
        (
            "cts9",
            [str(python), str(article / "build_ct_s1_uncertainty.py"), "--root", str(root), "--cts3", str(isolated / "cts3"), "--temporal", str(isolated / "temporal"), "--cts7", str(isolated / "cts7"), "--output", str(isolated / "cts9")],
        ),
    ]


def normalized_command(gate: str) -> str:
    values = {
        "cts3": "{python} research/article5/build_ct_s1_prepared.py --root {root} --output {root}/data/ct_s1/isolated/cts3",
        "temporal": "{python} research/article5/build_ct_s1_temporal.py --root {root} --input {root}/data/ct_s1/isolated/cts3 --output {root}/data/ct_s1/isolated/temporal",
        "cts7": "{python} research/article5/build_ct_s1_contrasts.py --root {root} --input {root}/data/ct_s1/isolated/temporal --output {root}/data/ct_s1/isolated/cts7",
        "cts9": "{python} research/article5/build_ct_s1_uncertainty.py --root {root} --cts3 {root}/data/ct_s1/isolated/cts3 --temporal {root}/data/ct_s1/isolated/temporal --cts7 {root}/data/ct_s1/isolated/cts7 --output {root}/data/ct_s1/isolated/cts9",
    }
    return values[gate]


def run_chain(label: str, root: Path, python: Path) -> list[dict]:
    environment = os.environ.copy()
    environment["PYTHONPYCACHEPREFIX"] = str(root / "cache/pycache")
    records = []
    for gate, command in commands(root, python):
        completed = subprocess.run(
            command,
            cwd=root,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        stdout = [line for line in completed.stdout.splitlines() if line.strip()]
        records.append({
            "run": label,
            "gate": gate,
            "command": normalized_command(gate),
            "returncode": completed.returncode,
            "status_line": stdout[-1] if stdout else "",
            "stderr": completed.stderr.strip(),
        })
        if completed.returncode:
            message = completed.stderr[-4000:] or completed.stdout[-4000:]
            raise RuntimeError(f"{label}/{gate} failed: {message}")
    return records


def load_statuses(output: Path) -> dict[str, str]:
    values = {
        gate: json.loads((output / gate / "validation.json").read_text())
        for gate in GATES
    }
    return {
        "CTS3": values["cts3"]["status"],
        "CTS4": values["temporal"]["gate_status"]["CTS4"],
        "CTS5": values["temporal"]["gate_status"]["CTS5"],
        "CTS6": values["temporal"]["gate_status"]["CTS6"],
        "CTS7": values["cts7"]["status"],
        "CTS8": values["temporal"]["gate_status"]["CTS8"],
        "CTS9": values["cts9"]["status"],
    }


def statuses_pass(statuses: dict[str, str]) -> bool:
    expected = {
        "CTS3": "PASS_CTS3_READY_FOR_CTS4_CTS8",
        "CTS4": "PASS",
        "CTS5": "PASS",
        "CTS6": "PASS",
        "CTS7": "PASS_CTS7_READY_FOR_CTS9",
        "CTS8": "PASS",
        "CTS9": "PASS_CTS9_READY_FOR_CTS10",
    }
    return statuses == expected


def run_tests(root: Path, python: Path) -> dict:
    test_files = sorted(str(path) for path in (root / "tests").glob("test_article5_*.py"))
    completed = subprocess.run(
        [str(python), "-m", "pytest", "-q", *test_files],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    combined = completed.stdout + "\n" + completed.stderr
    matches = re.findall(r"(\d+) passed", combined)
    return {
        "command": "{python} -m pytest -q tests/test_article5_*.py",
        "returncode": completed.returncode,
        "tests_passed": int(matches[-1]) if matches else None,
        "summary": next(
            (line for line in completed.stdout.splitlines() if " passed" in line),
            "",
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output or root / "data/ct_s1/cts10").resolve()
    if output.exists():
        raise SystemExit(f"output must not already exist: {output}")
    output.mkdir(parents=True)

    python = root / ".venv-article5/bin/python"
    protected = protected_paths(root)
    before = protected_hashes(protected, root)
    command_records = []
    with tempfile.TemporaryDirectory(prefix="ct-s1-cts10-") as temporary:
        temporary_root = Path(temporary)
        roots = {
            "run_a": temporary_root / "run_a/root",
            "run_b": temporary_root / "run_b/root",
        }
        for label, isolated_root in roots.items():
            populate_isolated_root(root, isolated_root)
            command_records.extend(run_chain(label, isolated_root, python))

        outputs = {
            label: isolated_root / "data/ct_s1/isolated"
            for label, isolated_root in roots.items()
        }
        comparison_result = compare_clean_builds(outputs["run_a"], outputs["run_b"])
        inventories = {label: file_inventory(path) for label, path in outputs.items()}
        comparison_rows = compare_inventories(inventories["run_a"], inventories["run_b"])
        runtime_json = {
            label: validate_json_files_have_no_runtime_metadata(path)
            for label, path in outputs.items()
        }
        statuses = {label: load_statuses(path) for label, path in outputs.items()}

    after = protected_hashes(protected, root)
    tests = run_tests(root, python)
    protected_unchanged = before == after
    runtime_file_sets_match = runtime_json["run_a"] == runtime_json["run_b"]
    conditions = {
        "protected_inputs_unchanged": protected_unchanged,
        "all_build_commands_succeeded": all(row["returncode"] == 0 for row in command_records),
        "run_a_prior_gate_statuses_reproduced": statuses_pass(statuses["run_a"]),
        "run_b_prior_gate_statuses_reproduced": statuses_pass(statuses["run_b"]),
        "relative_file_sets_match": comparison_result["relative_file_sets_match"],
        "all_generated_files_byte_identical": comparison_result["all_files_byte_identical"],
        "no_comparison_exclusions": True,
        "runtime_metadata_absent": bool(runtime_json["run_a"] and runtime_json["run_b"]),
        "runtime_json_file_sets_match": runtime_file_sets_match,
        "focused_article5_tests_pass": tests["returncode"] == 0,
    }
    passed = all(conditions.values())
    status = "PASS_CTS10_READY_FOR_CTS11" if passed else "FAIL_CTS10_STOP_DRAFTING"

    pd.DataFrame(comparison_rows).to_csv(
        output / "comparison.csv", index=False, lineterminator="\n"
    )
    write_json(output / "commands.json", command_records)
    write_json(output / "protected_inputs_before.json", before)
    write_json(output / "protected_inputs_after.json", after)
    validation = {
        "research_identity": "CT-S1",
        "version": BUILD_VERSION,
        "status": status,
        "conditions": conditions,
        "comparison": {
            "files_compared": comparison_result["files_compared"],
            "differences": len(comparison_result["differences"]),
            "timestamp_exclusions": [],
        },
        "gate_statuses": statuses,
        "runtime_metadata": {
            "json_files_checked_per_run": len(runtime_json["run_a"]),
            "forbidden_keys": [
                "created_at", "generated_at", "run_at", "runtime_timestamp", "timestamp"
            ],
        },
        "protected_inputs": {
            "files_hashed": len(before),
            "changed_files": sorted(
                path for path in set(before) | set(after)
                if before.get(path) != after.get(path)
            ),
        },
        "tests": tests,
        "restrictions": {
            "computational_reproducibility_only": True,
            "scientific_gates_overridden": False,
            "article_claims": False,
            "playbook_allowed": False,
        },
        "next_gate": "CTS11_CLAIM_REVIEW" if passed else "STOP_DRAFTING",
    }
    write_json(output / "validation.json", validation)
    summary_paths = sorted(path for path in output.iterdir() if path.is_file())
    manifest = {
        "version": BUILD_VERSION,
        "status": status,
        "code_sha256": {
            "build_ct_s1_reproducibility.py": sha256(Path(__file__)),
            "ct_s1_assurance.py": sha256(HERE / "ct_s1_assurance.py"),
            "reproducibility_core.py": sha256(HERE / "reproducibility_core.py"),
        },
        "summary_outputs": {
            path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
            for path in summary_paths
        },
        "software": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
        },
    }
    write_json(output / "manifest.json", manifest)
    print(json.dumps({
        "status": status,
        "files_compared": comparison_result["files_compared"],
        "differences": len(comparison_result["differences"]),
        "protected_files": len(before),
        "focused_tests_passed": tests["tests_passed"],
    }, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
