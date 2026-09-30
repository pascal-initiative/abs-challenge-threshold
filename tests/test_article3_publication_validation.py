import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts/publication_validation/article3"
S4 = ROOT / "artifacts/sprint4"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_accepted_sprint4_is_verified_immutable():
    integrity = json.loads((ART / "upstream_integrity.json").read_text())
    assert integrity["status"] == "VERIFIED_UNCHANGED"
    assert sha(S4 / "run_manifest.json") == integrity["accepted_sprint4_manifest_sha256"]
    assert integrity["verified_sprint4_outputs"] >= 60


def test_frozen_figure_data_are_byte_identical():
    rows = json.loads((ART / "frozen_figure_source_map.json").read_text())
    assert len(rows) == 8
    for row in rows:
        assert (ROOT / row["publication_artifact"]).read_bytes() == (ROOT / row["sprint4_source"]).read_bytes()
        assert sha(ROOT / row["publication_artifact"]) == row["sha256"]


def test_claims_reject_causal_and_multiseason_language():
    rows = json.loads((ART / "final_publication_claims_matrix.json").read_text())
    statuses = {row["claim"]: row["status"] for row in rows}
    assert statuses["Recognition is persistent across seasons."] == "NOT_SUPPORTED"
    causal = next(row for row in rows if row["claim"].startswith("Batter vision"))
    assert causal["status"] == "NOT_SUPPORTED"


def test_publication_gates_and_bottom_policy():
    manifest = json.loads((ART / "run_manifest.json").read_text())
    assert manifest["gates"]["Article 3"] == "READY_TO_DRAFT"
    assert manifest["gates"]["Leaderboard Publication"] == "PASS"
    assert manifest["publication_decisions"]["bottom_rankings"] == "OMIT"


def test_manifest_hashes_reconcile():
    manifest = json.loads((ART / "run_manifest.json").read_text())
    for rel, expected in manifest["output_artifact_hashes"].items():
        assert sha(ROOT / rel) == expected
    listed = {}
    for line in (ART / "artifact_hashes.sha256").read_text().splitlines():
        digest, rel = line.split("  ", 1)
        listed[rel] = digest
    assert listed[str((ART / "run_manifest.json").relative_to(ROOT))] == sha(ART / "run_manifest.json")
