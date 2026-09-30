"""Run two isolated CT-2026 builds and require byte-identical artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inventory(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hash_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.root.resolve()
    python = root / ".venv-article5/bin/python"
    builder = root / "research/article5/build_ct2026.py"
    environment = os.environ.copy()
    environment["PYTHONPYCACHEPREFIX"] = "/tmp/pascal-pycache"

    with tempfile.TemporaryDirectory(prefix="ct2026-repro-") as temp:
        base = Path(temp)
        results = []
        for run in ("run_a", "run_b"):
            output = base / run
            completed = subprocess.run(
                [str(python), str(builder), "--root", str(root), "--output", str(output)],
                cwd=root,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            results.append({
                "run": run,
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
                "inventory": inventory(output),
            })

        tests = subprocess.run(
            [
                str(python), "-m", "unittest", "discover", "-s", "tests",
                "-p", "test_article5*.py",
            ],
            cwd=root,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        identical = results[0]["inventory"] == results[1]["inventory"]
        expected_failure = all(result["returncode"] == 2 for result in results)
        report = {
            "byte_identical": identical,
            "expected_ct6_failure_reproduced": expected_failure,
            "file_count": len(results[0]["inventory"]),
            "focused_tests_passed": tests.returncode == 0,
            "focused_test_summary": (tests.stderr or tests.stdout).strip().splitlines()[-1],
            "build_stdout": [result["stdout"] for result in results],
        }
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if identical and expected_failure and tests.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
