"""Fail-closed validation for the CT-S1 findings and methodology outlines."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MAP = ROOT / "research/article5/CT_S1_OUTLINE_CLAIM_MAP.json"
CLAIM_TAG = re.compile(r"CTS11-C\d{2}")
NUMBER = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?(?!\w)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def numeric_tokens(value: Any) -> set[str]:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return {token.replace(",", "") for token in NUMBER.findall(text)}


def validate(map_path: Path) -> dict[str, Any]:
    plan = json.loads(map_path.read_text(encoding="utf-8"))
    registry_path = ROOT / plan["source_registry"]
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    failures: list[str] = []

    if sha256(registry_path) != plan["source_registry_sha256"]:
        failures.append("public-claim registry hash does not match the drafting map")

    known = {claim["claim_id"]: claim for claim in registry["claims"]}
    approved = {
        claim_id
        for claim_id, claim in known.items()
        if claim["status"] == "APPROVED_RESTRICTED"
    }
    allowed_numbers = numeric_tokens(registry) | {
        token.replace(",", "")
        for token in plan.get("additional_allowed_numeric_tokens", [])
    }
    document_results: dict[str, Any] = {}

    for relative, required_claims in plan["documents"].items():
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"missing outline: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        normalized = " ".join(lowered.split())
        tags = set(CLAIM_TAG.findall(text))
        unknown = tags - set(known)
        missing = set(required_claims) - tags
        if unknown:
            failures.append(f"{relative}: unknown claim tags {sorted(unknown)}")
        if missing:
            failures.append(f"{relative}: missing claim tags {sorted(missing)}")

        for phrase in plan["required_phrases"].get(relative, []):
            if " ".join(phrase.lower().split()) not in normalized:
                failures.append(f"{relative}: missing required phrase {phrase!r}")
        for phrase in plan["forbidden_phrases"]:
            if phrase.lower() in lowered:
                failures.append(f"{relative}: forbidden phrase {phrase!r}")

        unexpected_numbers = numeric_tokens(text) - allowed_numbers
        if unexpected_numbers:
            failures.append(
                f"{relative}: numerical tokens absent from claim registry "
                f"{sorted(unexpected_numbers)}"
            )

        document_results[relative] = {
            "sha256": sha256(path),
            "claim_tags": sorted(tags),
            "required_claims_present": not missing,
            "unexpected_numbers": sorted(unexpected_numbers),
        }

    covered = set().union(
        *(set(result.get("claim_tags", [])) for result in document_results.values())
    )
    if not approved <= covered:
        failures.append(f"approved claims not covered: {sorted(approved - covered)}")
    if "CTS11-C08" not in covered:
        failures.append("policy prohibition CTS11-C08 is not mapped")

    return {
        "research_identity": "CT-S1",
        "metric_version": "ct-s1.0",
        "status": "PASS_OUTLINES_READY_FOR_FACT_REVIEW" if not failures else "FAIL_OUTLINES",
        "documents": document_results,
        "approved_claims_covered": sorted(approved & covered),
        "policy_prohibition_mapped": "CTS11-C08" in covered,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    args = parser.parse_args()
    result = validate(args.map.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not result["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
