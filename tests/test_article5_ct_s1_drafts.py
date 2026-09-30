import json
from pathlib import Path

from research.article5.validate_ct_s1_drafts import validate_drafts


ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "research/article5/CT_S1_DRAFT_CLAIM_MAP.json"


def test_ct_s1_draft_package_passes():
    result = validate_drafts(MAP)

    assert result["status"] == "PASS_DRAFTS_READY_FOR_FACT_REVIEW"
    assert result["failures"] == []
    assert result["policy_prohibition_mapped"] is True
    assert result["approved_claims_covered"] == [
        *[f"CTS11-C{i:02d}" for i in range(1, 8)],
        "CTS11-C09",
    ]


def test_ct_s1_draft_validator_rejects_registry_hash_change(tmp_path):
    plan = json.loads(MAP.read_text())
    plan["source_registry_sha256"] = "0" * 64
    map_path = tmp_path / "claim-map.json"
    map_path.write_text(json.dumps(plan))

    result = validate_drafts(map_path)

    assert result["status"] == "FAIL_DRAFTS"
    assert any("registry hash" in failure for failure in result["failures"])


def test_ct_s1_draft_validator_rejects_unregistered_number(tmp_path):
    plan = json.loads(MAP.read_text())
    article = ROOT / "research/article5/CT_S1_ARTICLE_DRAFT.md"
    changed = tmp_path / "article.md"
    changed.write_text(article.read_text() + "\nUnregistered value: 123456789.\n")
    plan["documents"] = {str(changed): plan["documents"][str(article.relative_to(ROOT))]}
    plan["required_phrases"] = {str(changed): []}
    map_path = tmp_path / "claim-map.json"
    map_path.write_text(json.dumps(plan))

    result = validate_drafts(map_path)

    assert result["status"] == "FAIL_DRAFTS"
    assert any("numerical tokens" in failure for failure in result["failures"])


def test_ct_s1_draft_validator_requires_complete_public_convention_grid(tmp_path):
    plan = json.loads(MAP.read_text())
    article = ROOT / "research/article5/CT_S1_ARTICLE_DRAFT.md"
    changed = tmp_path / "article.md"
    changed.write_text(
        article.read_text().replace("`re_raw`", "`omitted_raw_variant`")
    )
    relative = str(article.relative_to(ROOT))
    plan["documents"] = {str(changed): plan["documents"][relative]}
    plan["required_phrases"] = {
        str(changed): plan["required_phrases"][relative]
    }
    map_path = tmp_path / "claim-map.json"
    map_path.write_text(json.dumps(plan))

    result = validate_drafts(map_path)

    assert result["status"] == "FAIL_DRAFTS"
    assert any("re_raw" in failure for failure in result["failures"])
