import csv
from pathlib import Path

from research.article5.build_ct_s1_figures import build, sha256


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "research/article5/CT_S1_FIGURE_SPEC.json"
REGISTRY = ROOT / "research/article5/CT_S1_PUBLIC_CLAIMS.json"


def rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_ct_s1_figure_package_builds_from_approved_claims(tmp_path):
    output = tmp_path / "figures"
    result = build(SPEC, REGISTRY, output)

    assert result["status"] == "PASS_FIGURES_READY_FOR_EDITORIAL_REVIEW"
    assert result["restrictions"] == {
        "site_deployment_authorized": False,
        "playbook_authorized": False,
        "player_grading_authorized": False,
    }
    assert len(list((output / "rendered").glob("*.svg"))) == 4
    assert len(list((output / "rendered").glob("*.png"))) == 4
    assert len(list((output / "source").glob("*.csv"))) == 4

    count_rows = rows(output / "source/figure2_one_state_two_counts.csv")
    assert {(row["period"], row["count"]) for row in count_rows} == {
        ("development", "1-1"),
        ("development", "1-2"),
        ("confirmation", "1-1"),
        ("confirmation", "1-2"),
    }
    assert all(row["claim_id"] == "CTS11-C05" for row in count_rows)


def test_ct_s1_figure_build_is_byte_deterministic(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    result_a = build(SPEC, REGISTRY, first)
    result_b = build(SPEC, REGISTRY, second)

    assert result_a["outputs"] == result_b["outputs"]
    for relative in result_a["outputs"]:
        assert sha256(first / relative) == sha256(second / relative)
