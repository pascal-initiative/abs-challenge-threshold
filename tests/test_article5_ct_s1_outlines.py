import json
from pathlib import Path

from research.article5.validate_ct_s1_outlines import numeric_tokens, validate


ROOT = Path(__file__).resolve().parents[1]


def test_ct_s1_outline_package_passes():
    result = validate(ROOT / "research/article5/CT_S1_OUTLINE_CLAIM_MAP.json")

    assert result["status"] == "PASS_OUTLINES_READY_FOR_FACT_REVIEW"
    assert result["failures"] == []
    assert result["policy_prohibition_mapped"] is True
    assert result["approved_claims_covered"] == [
        *[f"CTS11-C{i:02d}" for i in range(1, 8)],
        "CTS11-C09",
    ]


def test_ct_s1_outline_validator_rejects_registry_hash_change(tmp_path):
    plan = json.loads(
        (ROOT / "research/article5/CT_S1_OUTLINE_CLAIM_MAP.json").read_text()
    )
    plan["source_registry_sha256"] = "0" * 64
    map_path = tmp_path / "claim-map.json"
    map_path.write_text(json.dumps(plan))

    result = validate(map_path)

    assert result["status"] == "FAIL_OUTLINES"
    assert any("registry hash" in failure for failure in result["failures"])


def test_numeric_tokens_preserve_line_initial_thousands_values():
    assert numeric_tokens("22,584 rows\n2,000 replicates") == {"22584", "2000"}
