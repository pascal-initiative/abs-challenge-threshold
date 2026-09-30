import hashlib, json
from pathlib import Path

import numpy as np
import pandas as pd

from src.publication_validation import THRESHOLDS, outside_boundary

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/publication_validation"


def test_publication_funnel_exact_reconciliation():
    f = pd.read_csv(ART / "publication_funnel.csv").set_index("stage")
    assert f.loc["physical_pitches", "count"] == 645793
    assert f.loc["called_pitches", "count"] == 336095
    assert f.loc["called_strikes", "count"] == 103768
    assert f.loc["estimated_incorrect_called_strikes", "count"] == 11704
    assert f.loc["legal_estimated_incorrect_called_strikes", "count"] == 10755
    assert f.loc["challenged_legal_estimated_incorrect_called_strikes", "count"] == 2112
    assert f.loc["not_challenged_legal_estimated_incorrect_called_strikes", "count"] == 8643
    assert 2112 + 8643 == 10755


def test_recognition_denominator_and_outcome_independence():
    m = pd.read_csv(ART / "metric_definitions.csv").set_index("metric")
    r = m.loc["recognition_rate"]
    assert (r.numerator, r.denominator) == (2112, 10755)
    assert np.isclose(r.value, 2112 / 10755)
    # The official-success metric is separately defined even though this snapshot's
    # aggregate numerator happens to equal the recognition numerator.
    assert m.loc["challenge_success_rate", "denominator"] == 4335
    assert m.loc["correction_rate", "numerator"] == 2111


def test_boundary_threshold_is_inclusive():
    values = np.array([0.049999, 0.05, 0.050001])
    assert outside_boundary(values, 0.05).tolist() == [False, False, True]
    assert THRESHOLDS == [0.0, 0.05, 0.10, 0.25, 0.50]


def test_all_three_disagreements_are_preserved():
    d = pd.read_csv(ART / "boundary_disagreement_audit.csv")
    assert len(d) == 3
    assert set(d.pitch_key) == {"823451:7:2", "823610:68:1", "823701:65:4"}
    assert (d.interpretation == "MICROSCOPIC_BOUNDARY_PRECISION_DISAGREEMENT").sum() == 2
    assert d.interpretation.str.contains("MATERIAL_SOURCE_ZONE_HEIGHT").sum() == 1


def test_frozen_numbers_match_authoritative_outputs():
    n = json.loads((ART / "article1_numbers.json").read_text())
    assert n["official_challenges"] == 9485
    assert n["geometry_agreements"] == 9482
    assert n["geometry_disagreements"] == 3
    assert np.isclose(n["geometry_agreement_rate"], 9482 / 9485)
    assert n["legal_recognition_opportunities"] == 10755
    assert np.isclose(n["recognition_rate"], 2112 / 10755)
    b = pd.read_csv(ART / "boundary_sensitivity.csv")
    assert [x["legal_recognition_opportunities"] for x in n["boundary_sensitivity_results"]] == b.legal_recognition_opportunities.tolist()


def test_upstream_artifacts_were_not_mutated():
    m = json.loads((ART / "run_manifest.json").read_text())
    assert m["upstream_unchanged"]
    assert m["upstream_hashes_before"] == m["upstream_hashes_after"]
    for rel, expected in m["upstream_hashes_after"].items():
        if any(part.startswith(".") for part in Path(rel).parts):
            continue  # OS metadata is outside the research artifact inventory.
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == expected


def test_output_hashes_make_the_run_deterministically_auditable():
    m = json.loads((ART / "run_manifest.json").read_text())
    revision_path = ART / "positioning_revision_manifest.json"
    revision = json.loads(revision_path.read_text()) if revision_path.exists() else None
    for rel, expected in m["output_hashes"].items():
        if revision and rel in revision["replaced_file_prior_hashes"]:
            # The original manifest remains an immutable record of PV-1. The
            # revision manifest proves which two positioning files superseded it.
            assert revision["replaced_file_prior_hashes"][rel] == expected
        else:
            assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == expected


def test_positioning_revision_changes_no_quantitative_research():
    r = json.loads((ART / "positioning_revision_manifest.json").read_text())
    assert r["no_quantitative_research_changed"]
    assert r["quantitative_research_hashes_before"] == r["quantitative_research_hashes_after"]
    assert r["revised_gates"] == {
        "methodology": "PASS", "boundary_robustness": "PASS", "claim_accuracy": "PASS",
        "novelty_differentiation": "PASS", "article1": "READY_TO_DRAFT"}
    assert hashlib.sha256((ROOT / "docs/publication_validation/source_inventory.md").read_bytes()).hexdigest() == r["source_inventory_hash"]
    assert hashlib.sha256((ROOT / "docs/publication_validation/article1_claims_matrix.md").read_bytes()).hexdigest() == r["claims_matrix_hash"]
    assert hashlib.sha256((ART / "novelty_matrix.csv").read_bytes()).hexdigest() == r["novelty_matrix_hash"]


def test_revised_positioning_is_explicit_and_complete():
    positioning = (ROOT / "docs/publication_validation/article1_positioning.md").read_text()
    prior = (ROOT / "docs/publication_validation/article1_prior_work.md").read_text()
    titles = (ROOT / "docs/publication_validation/article1_title_options.md").read_text()
    claims = (ROOT / "docs/publication_validation/article1_claims_matrix.md").read_text()
    for phrase in ["What the article is", "Existing work we are building on", "Pascal's specific contribution",
                   "Claims to avoid", "READY_TO_DRAFT"]:
        assert phrase in positioning
    for source in ["Baseball Savant", "FanGraphs", "SABR", "ABS Charts", "open-source"]:
        assert source in prior
    assert "Prior-work context" in claims and "Pascal contribution" in claims
    assert "One in Five: Inside the ABS Recognition Gap" in titles
