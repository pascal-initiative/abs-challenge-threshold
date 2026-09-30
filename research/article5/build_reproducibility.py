"""Run the ABS-05 Gate G10 paired clean-build audit."""
from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT_DEFAULT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from reproducibility_core import (  # noqa: E402
    accepted_gate_statuses,
    compare_inventories,
    file_inventory,
    sha256,
)

VERSION = "abs_article5_reproducibility_v1"
EXPECTED_PREREGISTRATION_SHA256 = "73e70c487e20358a5a7a312a5fb3e4b47426ff7a06fc57a7aa98db85db60f977"
EXPECTED_INPUT_AUDIT_SHA256 = "75da568af916b44dc3656ca7443798c75bfd20f2cd7012dc112ad45334a34ff3"
EXPECTED_INPUT_REPORT_SHA256 = "f8f7cb6917fd74af0be2f54443a609e1e77e8b8922550f44473fde758257373c"
GATES = ["g5", "g6", "g7", "g8", "g8_wp", "g9"]


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def command_specs(root: Path, run: Path) -> list[tuple[str, list[str]]]:
    python = sys.executable
    article = root / "research/article5"
    return [
        ("g5", [python, str(article / "build_correction_values.py"), "--root", str(root), "--output", str(run / "g5")]),
        ("g6", [python, str(article / "validate_probability.py"), "--root", str(root), "--output", str(run / "g6")]),
        ("g7", [python, str(article / "build_dynamic_engine.py"), "--root", str(root), "--output", str(run / "g7")]),
        ("g8", [python, str(article / "build_stability.py"), "--root", str(root), "--output", str(run / "g8"), "--cache", str(run / "cache")]),
        ("g8_wp", [python, str(article / "build_win_probability_sensitivity.py"), "--root", str(root), "--output", str(run / "g8_wp")]),
        ("g9", [python, str(article / "build_effect_size.py"), "--root", str(root), "--output", str(run / "g9")]),
    ]


def normalized_command(gate: str) -> str:
    cache = " --cache {run}/cache" if gate == "g8" else ""
    scripts = {
        "g5": "build_correction_values.py",
        "g6": "validate_probability.py",
        "g7": "build_dynamic_engine.py",
        "g8": "build_stability.py",
        "g8_wp": "build_win_probability_sensitivity.py",
        "g9": "build_effect_size.py",
    }
    return f"{{python}} research/article5/{scripts[gate]} --root {{root}} --output {{run}}/{gate}{cache}"


def protected_paths(root: Path, input_audit: dict) -> list[Path]:
    paths = {root / row["path"] for row in input_audit["provenance"]["checks"]}
    relative = [
        "research/article4/output/article4_re288_table.csv",
        "research/article4/output/article4_all_incorrect_calls.csv",
        "research/article4/output/article4_spot_checks.csv",
        "research/article4/output/manifest.json",
        "research/article4/decision_value/output/article4_inventory_option_value.csv",
        "research/article5/PREREGISTRATION.md",
        "research/article5/AMENDMENT_001_G5.md",
        "research/article5/AMENDMENT_002_G8_OBJECTIVE.md",
        "research/article5/CORRECTION_VALUE_SPEC.md",
        "research/article5/PROBABILITY_SPEC.md",
        "research/article5/DYNAMIC_ENGINE_SPEC.md",
        "research/article5/STABILITY_SPEC.md",
        "research/article5/EFFECT_SIZE_SPEC.md",
        "research/article5/REPRODUCIBILITY_SPEC.md",
    ]
    paths.update(root / value for value in relative)
    return sorted(paths)


def hashes(paths: list[Path], root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): sha256(path) for path in paths}


def run_build(label: str, root: Path, run: Path) -> list[dict]:
    run.mkdir(parents=True, exist_ok=False)
    records = []
    for gate, command in command_specs(root, run):
        result = subprocess.run(command, cwd=root, text=True, capture_output=True)
        stdout_lines = [line for line in result.stdout.splitlines() if line.strip()]
        records.append({
            "run": label,
            "gate": gate,
            "command": normalized_command(gate),
            "returncode": result.returncode,
            "status_line": stdout_lines[-1] if stdout_lines else "",
        })
        if result.returncode:
            message = result.stderr[-4000:] or result.stdout[-4000:]
            raise RuntimeError(f"{label} {gate} failed ({result.returncode}): {message}")
    return records


def load_validations(run: Path) -> dict[str, dict]:
    return {
        gate: json.loads((run / gate / "validation.json").read_text())
        for gate in GATES
    }


def run_tests(root: Path) -> dict:
    command = [
        sys.executable, "-m", "unittest", "discover", "-s", "tests",
        "-p", "test_article5*.py",
    ]
    result = subprocess.run(command, cwd=root, text=True, capture_output=True)
    combined = result.stdout + "\n" + result.stderr
    match = re.search(r"Ran (\d+) tests?", combined)
    return {
        "command": "{python} -m unittest discover -s tests -p 'test_article5*.py'",
        "returncode": result.returncode,
        "tests_run": int(match.group(1)) if match else None,
    }


def render_report(validation: dict) -> str:
    return "\n".join([
        "# ABS-05 Gate G10 Reproducibility Validation",
        "",
        "Generated by `build_reproducibility.py`; do not hand-edit.",
        "",
        f"**Gate status: {validation['gate_status']}**",
        f"**Article readiness: {validation['article_readiness']}**",
        f"**Playbook allowed: {validation['playbook_allowed']}**",
        "",
        "## Paired clean builds",
        "",
        f"- Generated files compared: {validation['comparison']['files_compared']}.",
        f"- Byte-identical files: {validation['comparison']['byte_identical_files']}.",
        f"- Missing or changed files: {validation['comparison']['differences']}.",
        f"- Focused Article 5 tests: {validation['tests']['tests_run']} passed.",
        "",
        "## Interpretation",
        "",
        "The analytical package is reproducible and ready for a findings outline. Reproducibility does not repair the G8 stability failure or the rejected win-probability model. A situational challenge playbook and empirical evidence-to-action guidance remain prohibited.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)

    input_audit_path = root / "research/article5/output/input_audit.json"
    input_report_path = root / "research/article5/output/INPUT_AUDIT.md"
    preregistration_path = root / "research/article5/PREREGISTRATION.md"
    input_audit = json.loads(input_audit_path.read_text())
    protected = protected_paths(root, input_audit)
    before = hashes(protected, root)

    command_records = []
    command_records.extend(run_build("run_a", root, output / "run_a"))
    command_records.extend(run_build("run_b", root, output / "run_b"))
    after = hashes(protected, root)
    tests = run_tests(root)

    first = file_inventory(output / "run_a")
    second = file_inventory(output / "run_b")
    comparison_rows = compare_inventories(first, second)
    comparison = pd.DataFrame(comparison_rows)
    validation_a = load_validations(output / "run_a")
    validation_b = load_validations(output / "run_b")
    status_a = accepted_gate_statuses(validation_a)
    status_b = accepted_gate_statuses(validation_b)
    all_identical = bool(comparison.byte_identical.all())
    conditions = {
        "input_audit_json_hash_reconciles": sha256(input_audit_path) == EXPECTED_INPUT_AUDIT_SHA256,
        "input_audit_report_hash_reconciles": sha256(input_report_path) == EXPECTED_INPUT_REPORT_SHA256,
        "input_audit_gates_pass": all(value == "PASS" for value in input_audit["gates"].values()),
        "input_audit_provenance_pass": input_audit["provenance"]["all_verified"] is True,
        "preregistration_hash_reconciles": sha256(preregistration_path) == EXPECTED_PREREGISTRATION_SHA256,
        "protected_inputs_unchanged": before == after,
        "all_commands_succeeded": all(record["returncode"] == 0 for record in command_records),
        "run_a_statuses_preserved": all(status_a.values()),
        "run_b_statuses_preserved": all(status_b.values()),
        "relative_file_sets_match": set(first) == set(second),
        "all_generated_files_byte_identical": all_identical,
        "article5_tests_pass": tests["returncode"] == 0 and tests["tests_run"] == 40,
    }
    gate_status = "PASS" if all(conditions.values()) else "FAIL"
    validation = {
        "gate": "G10_REPRODUCIBILITY",
        "gate_status": gate_status,
        "article_readiness": "READY_FOR_FINDINGS_OUTLINE_WITH_RESTRICTIONS" if gate_status == "PASS" else "NOT_READY_TO_DRAFT",
        "playbook_allowed": False,
        "conditions": conditions,
        "accepted_gate_statuses_run_a": status_a,
        "accepted_gate_statuses_run_b": status_b,
        "comparison": {
            "files_compared": len(comparison),
            "byte_identical_files": int(comparison.byte_identical.sum()),
            "differences": int((~comparison.byte_identical).sum()),
            "timestamp_exclusions": [],
        },
        "tests": tests,
        "restrictions": {
            "g8_stability": "failed; situational guidance prohibited",
            "player_probability": "not identified",
            "win_probability": "model rejected",
            "dynamic_policy": "nondeployable exact-future-sequence upper benchmark",
            "article_scope": "model-free or explicitly assumption-labeled findings only",
        },
    }

    comparison.to_csv(output / "comparison.csv", index=False, lineterminator="\n")
    write_json(output / "commands.json", command_records)
    write_json(output / "validation.json", validation)
    (output / "VALIDATION.md").write_text(render_report(validation))
    summary_paths = [
        output / "comparison.csv",
        output / "commands.json",
        output / "validation.json",
        output / "VALIDATION.md",
    ]
    manifest = {
        "version": VERSION,
        "gate_status": gate_status,
        "code_sha256": {
            "build_reproducibility.py": sha256(Path(__file__)),
            "reproducibility_core.py": sha256(HERE / "reproducibility_core.py"),
        },
        "protected_inputs": before,
        "summary_outputs": {
            path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
            for path in summary_paths
        },
        "software": {"python": platform.python_version(), "pandas": pd.__version__},
    }
    write_json(output / "manifest.json", manifest)
    print(json.dumps({
        "gate_status": gate_status,
        "files_compared": len(comparison),
        "differences": int((~comparison.byte_identical).sum()),
    }, sort_keys=True))
    return 0 if gate_status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
