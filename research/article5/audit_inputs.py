"""Article 5 pre-model provenance, population, and label-fidelity audit."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd

START_DATE = "2026-03-25"
END_DATE = "2026-09-09"
EXPECTED_PITCHES = 645_793
EXPECTED_GAMES = 2_195
EXPECTED_CHALLENGES = 9_485
EXPECTED_LEGAL_DECISIONS = 312_228
LABEL_FIDELITY_GATE = 0.99

PITCH_COLUMNS = [
    "affected_team_challenges_remaining",
    "challenge_outcome",
    "challenged",
    "derived_abs_call",
    "game_date",
    "game_pk",
    "official_abs_call",
    "original_call",
    "pitch_key",
    "position_player_pitching",
]

DECISION_FEATURE_ALLOWLIST = {
    "affected_team_challenges_remaining", "away_score", "balls", "bat_side",
    "batter_id", "catcher_id", "defense_challenges_remaining", "game_date",
    "game_pk", "half_inning", "home_score", "inning", "on_1b", "on_2b",
    "on_3b", "offense_challenges_remaining", "original_call", "outs",
    "pitch_hand", "pitch_type", "pitcher_id", "umpire_id",
}

LEAKAGE_BLACKLIST = {
    "challenge_outcome", "challenged", "derived_abs_call",
    "distance_from_abs_boundary", "feed_plate_x", "feed_plate_z",
    "official_abs_call", "opportunity_population", "plate_x", "plate_z",
    "survival_class", "survival_detail", "wrong_way_margin_inches",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def legal_decision_mask(frame: pd.DataFrame) -> pd.Series:
    called = frame["original_call"].isin(["BALL", "STRIKE"])
    position_player = frame["position_player_pitching"].fillna(False).astype(bool)
    inventory = pd.to_numeric(
        frame["affected_team_challenges_remaining"], errors="coerce"
    ).fillna(0)
    return called & ~position_player & inventory.gt(0)


def challenge_label_audit(frame: pd.DataFrame) -> dict:
    challenged = frame.loc[frame["challenged"].fillna(False).astype(bool)].copy()
    geometry_overturn = challenged["original_call"].ne(challenged["derived_abs_call"])
    official_overturn = challenged["challenge_outcome"].eq("OVERTURNED")
    agree = geometry_overturn.eq(official_overturn)
    mismatches = challenged.loc[
        ~agree,
        [
            "pitch_key", "game_pk", "game_date", "original_call",
            "derived_abs_call", "official_abs_call", "challenge_outcome",
        ],
    ].sort_values("pitch_key")
    return {
        "challenges": int(len(challenged)),
        "geometry_overturns": int(geometry_overturn.sum()),
        "official_overturns": int(official_overturn.sum()),
        "agreements": int(agree.sum()),
        "disagreements": int((~agree).sum()),
        "agreement_rate": float(agree.mean()),
        "official_label_coverage": float(challenged["challenge_outcome"].notna().mean()),
        "mismatches": mismatches.to_dict("records"),
    }


def verify_hashes(root: Path, manifest: dict) -> dict:
    checks = []
    for relative, expected in sorted(manifest["input_sha256"].items()):
        path = root / relative
        actual = sha256(path) if path.exists() else None
        checks.append({
            "path": relative,
            "expected_sha256": expected,
            "actual_sha256": actual,
            "verified": actual == expected,
        })
    for name, expected in sorted(manifest["code_sha256"].items()):
        path = root / "research/article4" / name
        actual = sha256(path) if path.exists() else None
        checks.append({
            "path": f"research/article4/{name}",
            "expected_sha256": expected,
            "actual_sha256": actual,
            "verified": actual == expected,
        })
    for name, metadata in sorted(manifest["outputs"].items()):
        path = root / "research/article4/output" / name
        actual = sha256(path) if path.exists() else None
        checks.append({
            "path": f"research/article4/output/{name}",
            "expected_sha256": metadata["sha256"],
            "actual_sha256": actual,
            "verified": actual == metadata["sha256"],
        })
    return {
        "checks": checks,
        "checked_files": len(checks),
        "failed_files": [row["path"] for row in checks if not row["verified"]],
        "all_verified": all(row["verified"] for row in checks),
    }


def build_audit(root: Path) -> dict:
    manifest_path = root / "research/article4/output/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    provenance = verify_hashes(root, manifest)

    pitches = pd.read_csv(
        root / "data/full_season/processed/pitches.csv",
        usecols=PITCH_COLUMNS,
        low_memory=False,
    )
    challenge_table = pd.read_csv(
        root / "data/full_season/processed/challenges.csv",
        usecols=["pitch_key"],
    )
    legal = legal_decision_mask(pitches)
    challenged_keys = set(pitches.loc[pitches["challenged"], "pitch_key"])
    official_keys = set(challenge_table["pitch_key"])
    labels = challenge_label_audit(pitches)

    population = {
        "rows": int(len(pitches)),
        "games": int(pitches["game_pk"].nunique()),
        "start_date": str(pitches["game_date"].min()),
        "end_date": str(pitches["game_date"].max()),
        "duplicate_pitch_keys": int(pitches["pitch_key"].duplicated().sum()),
        "legal_called_pitch_decisions": int(legal.sum()),
        "legal_challenges": int(pitches.loc[legal, "challenged"].sum()),
        "official_challenge_rows": int(len(challenge_table)),
        "duplicate_official_challenge_keys": int(challenge_table["pitch_key"].duplicated().sum()),
        "challenge_keys_missing_from_pitches": sorted(official_keys - challenged_keys),
        "challenged_pitch_keys_missing_from_official": sorted(challenged_keys - official_keys),
    }

    g1 = provenance["all_verified"]
    g2 = all([
        population["rows"] == EXPECTED_PITCHES,
        population["games"] == EXPECTED_GAMES,
        population["start_date"] == START_DATE,
        population["end_date"] == END_DATE,
        population["duplicate_pitch_keys"] == 0,
        population["legal_called_pitch_decisions"] == EXPECTED_LEGAL_DECISIONS,
        population["legal_challenges"] == EXPECTED_CHALLENGES,
        population["official_challenge_rows"] == EXPECTED_CHALLENGES,
        population["duplicate_official_challenge_keys"] == 0,
        not population["challenge_keys_missing_from_pitches"],
        not population["challenged_pitch_keys_missing_from_official"],
    ])
    g4 = (
        labels["challenges"] == EXPECTED_CHALLENGES
        and labels["official_label_coverage"] == 1.0
        and labels["agreement_rate"] >= LABEL_FIDELITY_GATE
    )
    schema = {
        "allowed_features": sorted(DECISION_FEATURE_ALLOWLIST),
        "blacklisted_features": sorted(LEAKAGE_BLACKLIST),
        "allowlist_blacklist_overlap": sorted(
            DECISION_FEATURE_ALLOWLIST & LEAKAGE_BLACKLIST
        ),
    }
    return {
        "audit_version": "abs_article5_input_audit_v1",
        "snapshot": [START_DATE, END_DATE],
        "preregistration_sha256": sha256(root / "research/article5/PREREGISTRATION.md"),
        "article4_manifest_sha256": sha256(manifest_path),
        "audit_code_sha256": sha256(Path(__file__)),
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "provenance": provenance,
        "population": population,
        "label_fidelity": labels,
        "feature_schema": schema,
        "gates": {
            "G1_PROVENANCE": "PASS" if g1 else "FAIL",
            "G2_POPULATION": "PASS" if g2 else "FAIL",
            "G3_SCHEMA_DEFINITION": "PASS" if not schema["allowlist_blacklist_overlap"] else "FAIL",
            "G4_LABEL_FIDELITY": "PASS" if g4 else "FAIL",
        },
    }


def render_markdown(audit: dict) -> str:
    p = audit["population"]
    label = audit["label_fidelity"]
    mismatch_lines = [
        f"- `{row['pitch_key']}`: {row['original_call']} -> geometry "
        f"{row['derived_abs_call']}, official {row['official_abs_call']} "
        f"({row['challenge_outcome']})"
        for row in label["mismatches"]
    ] or ["- None"]
    return "\n".join([
        "# ABS-05 Input Audit",
        "",
        "Generated by `audit_inputs.py`; do not hand-edit.",
        "",
        "## Gates",
        "",
        *[f"- **{name}: {status}**" for name, status in audit["gates"].items()],
        "",
        "## Population",
        "",
        f"- {p['rows']:,} pitches in {p['games']:,} games, {p['start_date']} through {p['end_date']}.",
        f"- {p['legal_called_pitch_decisions']:,} legal called-pitch decisions.",
        f"- {p['official_challenge_rows']:,} official challenges; duplicate keys: {p['duplicate_official_challenge_keys']}.",
        f"- Duplicate pitch keys: {p['duplicate_pitch_keys']}.",
        "",
        "## Label fidelity",
        "",
        f"Public geometry and official result agree on {label['agreements']:,} of "
        f"{label['challenges']:,} challenges ({label['agreement_rate']:.4%}).",
        f"The {label['disagreements']} disagreements are retained and audited:",
        "",
        *mismatch_lines,
        "",
        "## Provenance",
        "",
        f"- Protected files checked: {audit['provenance']['checked_files']}.",
        f"- Failed hashes: {len(audit['provenance']['failed_files'])}.",
        f"- Preregistration SHA-256: `{audit['preregistration_sha256']}`.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    audit = build_audit(args.root)
    output = args.root / "research/article5/output"
    output.mkdir(parents=True, exist_ok=True)
    (output / "input_audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n"
    )
    (output / "INPUT_AUDIT.md").write_text(render_markdown(audit))
    print(json.dumps(audit["gates"], sort_keys=True))
    return 0 if all(value == "PASS" for value in audit["gates"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())

