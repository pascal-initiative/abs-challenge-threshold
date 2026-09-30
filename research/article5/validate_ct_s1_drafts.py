"""Fail-closed validation for the CT-S1 article and methodology drafts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.article5.validate_ct_s1_outlines import validate  # noqa: E402


DEFAULT_MAP = ROOT / "research/article5/CT_S1_DRAFT_CLAIM_MAP.json"


def validate_drafts(map_path: Path) -> dict[str, object]:
    result = validate(map_path)
    result["status"] = (
        "PASS_DRAFTS_READY_FOR_FACT_REVIEW"
        if not result["failures"]
        else "FAIL_DRAFTS"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    args = parser.parse_args()
    result = validate_drafts(args.map.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not result["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
