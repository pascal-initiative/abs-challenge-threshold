"""Validate the frozen CT-S1 CTS11 public-claim registry."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CLAIMS = ROOT / "research/article5/CT_S1_PUBLIC_CLAIMS.json"
DEFAULT_OUTPUT = ROOT / "data/ct_s1/cts11"
FORBIDDEN_APPROVED_PHRASES = (
    "should challenge",
    "always challenge",
    "optimal policy",
    "player made a mistake",
    "bad decision",
    "unused challenges were wasted",
)
CORE_CONVENTION_NAMES = (
    "reference_fixed_0.60",
    "fixed_0.50",
    "fixed_0.70",
    "cutoff_0.00",
    "cutoff_0.10",
    "re_pooled_count",
    "re_raw",
    "no_extra_inning_restoration",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def json_path(document: dict[str, Any], dotted: str) -> Any:
    value: Any = document
    for part in dotted.split("."):
        value = value[part]
    return value


def matching_rows(path: Path, filters: dict[str, str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            row
            for row in csv.DictReader(handle)
            if all(row.get(key) == expected for key, expected in filters.items())
        ]


def validate_source(source: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    relative = source["artifact"]
    path = ROOT / relative
    if not path.is_file():
        return [f"missing artifact: {relative}"]
    actual_sha = sha256(path)
    if actual_sha != source["sha256"]:
        failures.append(
            f"hash mismatch for {relative}: {actual_sha} != {source['sha256']}"
        )
        return failures

    if "json_values" in source:
        document = json.loads(path.read_text(encoding="utf-8"))
        for dotted, expected in source["json_values"].items():
            actual = json_path(document, dotted)
            if actual != expected:
                failures.append(f"{relative}:{dotted} was {actual!r}, expected {expected!r}")

    for check in source.get("csv_counts", []):
        actual = len(matching_rows(path, check["filters"]))
        if actual != check["expected"]:
            failures.append(
                f"{relative} count {check['filters']} was {actual}, expected {check['expected']}"
            )

    for check in source.get("csv_rows", []):
        rows = matching_rows(path, check["filters"])
        if len(rows) != 1:
            failures.append(
                f"{relative} row {check['filters']} matched {len(rows)} rows, expected 1"
            )
            continue
        for field, expected in check["values"].items():
            actual = rows[0].get(field)
            if actual != expected:
                failures.append(
                    f"{relative} row {check['filters']} field {field} was {actual!r}, "
                    f"expected {expected!r}"
                )
    return failures


def run(claims_path: Path, output_dir: Path) -> dict[str, Any]:
    registry = json.loads(claims_path.read_text(encoding="utf-8"))
    claims = registry["claims"]
    failures: list[str] = []
    audit_rows: list[dict[str, str]] = []
    ids = [claim["claim_id"] for claim in claims]
    if len(ids) != len(set(ids)):
        failures.append("claim IDs are not unique")

    for claim in claims:
        claim_failures: list[str] = []
        if claim["status"] not in {"APPROVED_RESTRICTED", "PROHIBITED"}:
            claim_failures.append(f"unsupported status {claim['status']}")
        if not claim.get("denominator") or not claim.get("required_context"):
            claim_failures.append("denominator and required context are mandatory")
        if not claim.get("prohibited_extension"):
            claim_failures.append("prohibited extension is mandatory")
        if not claim.get("sources"):
            claim_failures.append("at least one content-addressed source is mandatory")
        if claim["status"] == "APPROVED_RESTRICTED":
            lowered = claim["statement"].lower()
            for phrase in FORBIDDEN_APPROVED_PHRASES:
                if phrase in lowered:
                    claim_failures.append(f"approved statement contains forbidden phrase: {phrase}")
        for source in claim.get("sources", []):
            claim_failures.extend(validate_source(source))
        failures.extend(f"{claim['claim_id']}: {failure}" for failure in claim_failures)
        audit_rows.append(
            {
                "claim_id": claim["claim_id"],
                "claim_status": claim["status"],
                "claim_type": claim["type"],
                "source_count": str(len(claim.get("sources", []))),
                "validation_status": "PASS" if not claim_failures else "FAIL",
                "failure_count": str(len(claim_failures)),
            }
        )

    approved = sum(c["status"] == "APPROVED_RESTRICTED" for c in claims)
    prohibited = sum(c["status"] == "PROHIBITED" for c in claims)
    required_ids = {f"CTS11-C{i:02d}" for i in range(1, 10)}
    if set(ids) != required_ids:
        failures.append(f"required claim set mismatch: {sorted(set(ids) ^ required_ids)}")
    if registry.get("metric_version") != "ct-s1.0":
        failures.append("public metric version must be ct-s1.0")
    interpretation_contract_present = bool(registry.get("interpretation_contract"))
    if not interpretation_contract_present:
        failures.append("interpretation contract is mandatory")
    playbook_prohibited = any(
        c["claim_id"] == "CTS11-C08" and c["status"] == "PROHIBITED"
        for c in claims
    )
    if not playbook_prohibited:
        failures.append("CTS11-C08 must prohibit playbook and policy translation")
    convention_claim = next(
        (claim for claim in claims if claim["claim_id"] == "CTS11-C09"), None
    )
    convention_grid_publicly_defined = bool(
        convention_claim
        and convention_claim["status"] == "APPROVED_RESTRICTED"
        and all(
            name in convention_claim["statement"] for name in CORE_CONVENTION_NAMES
        )
        and "public_tracking" in convention_claim["required_context"]
        and "selected_transport" in convention_claim["required_context"]
    )
    if not convention_grid_publicly_defined:
        failures.append(
            "CTS11-C09 must define all eight core conventions and exclude diagnostics"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    audit_path = output_dir / "claim_audit.csv"
    with audit_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit_rows[0]))
        writer.writeheader()
        writer.writerows(audit_rows)

    passed = not failures
    validation = {
        "research_identity": "CT-S1",
        "metric_version": "ct-s1.0",
        "status": (
            "PASS_CTS11_NUMERICAL_DRAFTING_ALLOWED"
            if passed
            else "FAIL_CTS11_RETURN_TO_EDITORIAL_REVIEW"
        ),
        "gate_status": {"CTS11": "PASS" if passed else "FAIL"},
        "claims": {
            "total": len(claims),
            "approved_restricted": approved,
            "prohibited": prohibited,
            "failed": len(failures),
        },
        "conditions": {
            "all_public_numbers_map_to_accepted_artifacts": passed,
            "interpretation_contract_present": interpretation_contract_present,
            "no_prescriptive_approved_claim": passed,
            "playbook_prohibited": playbook_prohibited,
            "convention_grid_publicly_defined": convention_grid_publicly_defined,
        },
        "decision": {
            "numerical_drafting_allowed": passed,
            "reference_evaluator_allowed": passed,
            "representative_contrast_allowed": passed,
            "playbook_allowed": False,
            "optimal_policy_claim_allowed": False,
            "player_grading_allowed": False,
        },
        "failures": failures,
    }
    validation_path = output_dir / "validation.json"
    validation_path.write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "research_identity": "CT-S1",
        "version": "ct-s1.0-cts11",
        "inputs": {
            display_path(claims_path): sha256(claims_path),
        },
        "outputs": {
            display_path(audit_path): sha256(audit_path),
            display_path(validation_path): sha256(validation_path),
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return validation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claims", type=Path, default=DEFAULT_CLAIMS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.claims.resolve(), args.output_dir.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["gate_status"]["CTS11"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
