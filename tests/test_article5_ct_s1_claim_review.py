import json
from pathlib import Path

from research.article5.build_ct_s1_claim_review import run


ROOT = Path(__file__).resolve().parents[1]


def test_cts11_registry_passes_against_accepted_artifacts(tmp_path):
    result = run(
        ROOT / "research/article5/CT_S1_PUBLIC_CLAIMS.json",
        tmp_path / "cts11",
    )

    assert result["gate_status"]["CTS11"] == "PASS"
    assert result["claims"] == {
        "total": 9,
        "approved_restricted": 8,
        "prohibited": 1,
        "failed": 0,
    }
    assert result["decision"]["numerical_drafting_allowed"] is True
    assert result["decision"]["playbook_allowed"] is False
    assert result["conditions"]["convention_grid_publicly_defined"] is True


def test_cts11_fails_closed_on_unmapped_number(tmp_path):
    source = json.loads(
        (ROOT / "research/article5/CT_S1_PUBLIC_CLAIMS.json").read_text()
    )
    source["claims"][1]["sources"][0]["json_values"][
        "candidate_states.confirmation"
    ] = 24881
    claims = tmp_path / "claims.json"
    claims.write_text(json.dumps(source))

    result = run(claims, tmp_path / "cts11")

    assert result["gate_status"]["CTS11"] == "FAIL"
    assert result["decision"]["numerical_drafting_allowed"] is False
    assert any("candidate_states.confirmation" in item for item in result["failures"])


def test_cts11_requires_playbook_prohibition(tmp_path):
    source = json.loads(
        (ROOT / "research/article5/CT_S1_PUBLIC_CLAIMS.json").read_text()
    )
    playbook_claim = next(
        claim for claim in source["claims"] if claim["claim_id"] == "CTS11-C08"
    )
    playbook_claim["status"] = "APPROVED_RESTRICTED"
    claims = tmp_path / "claims.json"
    claims.write_text(json.dumps(source))

    result = run(claims, tmp_path / "cts11")

    assert result["gate_status"]["CTS11"] == "FAIL"
    assert result["conditions"]["playbook_prohibited"] is False
    assert result["decision"]["playbook_allowed"] is False


def test_cts11_requires_complete_public_convention_grid(tmp_path):
    source = json.loads(
        (ROOT / "research/article5/CT_S1_PUBLIC_CLAIMS.json").read_text()
    )
    convention_claim = next(
        claim for claim in source["claims"] if claim["claim_id"] == "CTS11-C09"
    )
    convention_claim["statement"] = convention_claim["statement"].replace(
        "re_raw", "omitted_raw_variant"
    )
    claims = tmp_path / "claims.json"
    claims.write_text(json.dumps(source))

    result = run(claims, tmp_path / "cts11")

    assert result["gate_status"]["CTS11"] == "FAIL"
    assert result["conditions"]["convention_grid_publicly_defined"] is False
    assert result["decision"]["numerical_drafting_allowed"] is False
