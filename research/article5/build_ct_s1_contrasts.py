"""Generate and audit the frozen CT-S1 CTS7 contrast families."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT_DEFAULT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from ct_s1_core import (  # noqa: E402
    CORE_VARIANTS,
    REFERENCE_VARIANT,
    VERSION,
    audit_contrasts,
    cts7_passes,
)


BUILD_VERSION = "ct-s1.0-cts7"
PAIR_FIELDS = (
    "original_call", "side", "balls", "strikes", "outs", "base_state",
    "inning_exact", "half_inning", "score_bucket", "team_role", "inventory",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def expected_hashes(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text().splitlines():
        digest, relative = line.split(maxsplit=1)
        result[relative] = digest
    return result


def _pairs(
    merged: pd.DataFrame,
    *,
    contrast_class: str,
    selection_rule: str,
) -> pd.DataFrame:
    result = pd.DataFrame({
        "contrast_class": contrast_class,
        "source_contrast_class": contrast_class,
        "member_a_scenario_id": merged["scenario_id_a"],
        "member_b_scenario_id": merged["scenario_id_b"],
        "outs": merged["outs_a"],
        "base_state": merged["base_state_a"],
        "selection_rule": selection_rule,
    })
    result["contrast_id"] = (
        contrast_class
        + "|A=" + result.member_a_scenario_id.astype(str)
        + "|B=" + result.member_b_scenario_id.astype(str)
    )
    return result


def early_late_pairs(states: pd.DataFrame) -> pd.DataFrame:
    work = states.copy()
    work["inning_number"] = pd.to_numeric(work.inning_exact, errors="coerce")
    early = work.loc[work.inning_number.between(1, 3)].copy()
    late = work.loc[work.inning_number.between(7, 9)].copy()
    early["late_inning"] = early.inning_number + 6
    keys = [
        "original_call", "side", "balls", "strikes", "outs", "base_state",
        "half_inning", "score_bucket", "team_role", "inventory",
    ]
    merged = early.merge(
        late,
        left_on=[*keys, "late_inning"],
        right_on=[*keys, "inning_number"],
        suffixes=("_a", "_b"),
        validate="one_to_one",
    )
    # Join keys are unsuffixed; expose the shared fields needed downstream.
    merged["outs_a"] = merged.outs
    merged["base_state_a"] = merged.base_state
    return _pairs(
        merged,
        contrast_class="early_late",
        selection_rule="same public state; innings 1:7, 2:8, or 3:9",
    )


def inventory_pairs(states: pd.DataFrame) -> pd.DataFrame:
    one = states.loc[states.inventory.eq(1)]
    two = states.loc[states.inventory.eq(2)]
    keys = [field for field in PAIR_FIELDS if field != "inventory"]
    merged = one.merge(two, on=keys, suffixes=("_a", "_b"), validate="one_to_one")
    merged["outs_a"] = merged.outs
    merged["base_state_a"] = merged.base_state
    return _pairs(
        merged,
        contrast_class="inventory",
        selection_rule="same public state; one unit versus two units",
    )


def count_pairs(states: pd.DataFrame) -> pd.DataFrame:
    pieces = []
    balls = states.loc[states.original_call.eq("BALL")]
    ordinary_ball = balls.loc[balls.balls.lt(3)]
    terminal_ball = balls.loc[balls.balls.eq(3)]
    ball_keys = [
        "original_call", "side", "strikes", "outs", "base_state",
        "inning_exact", "half_inning", "score_bucket", "team_role", "inventory",
    ]
    pieces.append(ordinary_ball.merge(
        terminal_ball, on=ball_keys, suffixes=("_a", "_b"), validate="many_to_one"
    ))

    strikes = states.loc[states.original_call.eq("STRIKE")]
    ordinary_strike = strikes.loc[strikes.strikes.lt(2)]
    terminal_strike = strikes.loc[strikes.strikes.eq(2)]
    strike_keys = [
        "original_call", "side", "balls", "outs", "base_state",
        "inning_exact", "half_inning", "score_bucket", "team_role", "inventory",
    ]
    pieces.append(ordinary_strike.merge(
        terminal_strike, on=strike_keys, suffixes=("_a", "_b"), validate="many_to_one"
    ))
    normalized = []
    for merged in pieces:
        if merged.empty:
            continue
        merged["outs_a"] = merged.outs
        merged["base_state_a"] = merged.base_state
        normalized.append(_pairs(
            merged,
            contrast_class="count_terminal",
            selection_rule="same non-count state; ordinary count versus call-terminal count",
        ))
    return pd.concat(normalized, ignore_index=True) if normalized else pd.DataFrame()


def select_ordinary_representatives(
    candidates: pd.DataFrame,
    development_reference: pd.Series,
) -> pd.DataFrame:
    median = float(development_reference.dropna().median())
    work = candidates.loc[
        pd.to_numeric(candidates.base_state, errors="coerce").eq(0)
        & pd.to_numeric(candidates.outs, errors="coerce").eq(0)
    ].copy()
    work["member_a_development_reference_ct"] = work.member_a_scenario_id.map(development_reference)
    work["member_b_development_reference_ct"] = work.member_b_scenario_id.map(development_reference)
    work["development_midpoint"] = (
        work.member_a_development_reference_ct + work.member_b_development_reference_ct
    ) / 2
    work["development_median_distance"] = (work.development_midpoint - median).abs()
    work = work.loc[np.isfinite(work.development_median_distance)].copy()
    selected = []
    for source_class, group in work.groupby("source_contrast_class", sort=True):
        winner = group.sort_values(
            ["development_median_distance", "contrast_id"], kind="stable"
        ).iloc[[0]].copy()
        winner["contrast_class"] = "ordinary"
        winner["selection_rule"] = (
            "bases empty/no outs; development midpoint nearest development reference median; "
            "lexicographic tie-break"
        )
        winner["contrast_id"] = "ordinary|source=" + source_class + "|" + winner.contrast_id
        selected.append(winner)
    return pd.concat(selected, ignore_index=True) if selected else pd.DataFrame()


def contrast_cells(pairs: pd.DataFrame, matched: pd.DataFrame) -> pd.DataFrame:
    lookup = pd.concat([
        matched.loc[:, ["scenario_id", "variant", "development_ct"]]
        .rename(columns={"development_ct": "ct"}).assign(period="development"),
        matched.loc[:, ["scenario_id", "variant", "confirmation_ct"]]
        .rename(columns={"confirmation_ct": "ct"}).assign(period="confirmation"),
    ], ignore_index=True)
    lookup = lookup.loc[lookup.variant.isin(CORE_VARIANTS)]
    if lookup.duplicated(["scenario_id", "variant", "period"]).any():
        raise ValueError("threshold lookup is not unique")
    members = pd.concat([
        pairs.loc[:, ["contrast_id", "contrast_class", "member_a_scenario_id"]]
        .rename(columns={"member_a_scenario_id": "scenario_id"}).assign(member="A"),
        pairs.loc[:, ["contrast_id", "contrast_class", "member_b_scenario_id"]]
        .rename(columns={"member_b_scenario_id": "scenario_id"}).assign(member="B"),
    ], ignore_index=True)
    cells = members.merge(
        lookup, on="scenario_id", how="left", validate="many_to_many"
    )
    expected = len(pairs) * 2 * 2 * len(CORE_VARIANTS)
    if len(cells) != expected:
        raise ValueError(f"contrast cell grid has {len(cells)} rows; expected {expected}")
    return cells.sort_values(
        ["contrast_class", "contrast_id", "period", "variant", "member"], kind="stable"
    ).reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    source = (args.input or root / "data/ct_s1/temporal").resolve()
    output = (args.output or root / "data/ct_s1/cts7").resolve()
    if output.exists():
        raise SystemExit(f"output must not already exist: {output}")
    output.mkdir(parents=True)

    required_inputs = [
        source / "confirmation_candidate_states.csv",
        source / "matched_all_variants.csv",
        source / "validation.json",
        source / "manifest.json",
    ]
    protected_specs = [
        root / "research/article5/CT_S1_CTS4_CTS8_OUTPUTS.sha256",
        root / "research/article5/CT_SUCCESSOR_VALIDATION_PLAN.md",
        root / "research/article5/CT_S1_MODEL_SCHEMA.md",
        root / "research/article5/CT_S1_CTS7_SELECTION_RULES.md",
    ]
    protected = [*required_inputs, *protected_specs]
    before = {str(path.relative_to(root)): sha256(path) for path in protected}
    expected = expected_hashes(root / "research/article5/CT_S1_CTS4_CTS8_OUTPUTS.sha256")
    prior_hashes_reconcile = all(
        (root / relative).is_file() and sha256(root / relative) == digest
        for relative, digest in expected.items()
    )
    prior = json.loads((source / "validation.json").read_text())
    required_prior_gates = ("CTS4", "CTS5", "CTS6", "CTS8")
    if not all(prior["gate_status"].get(gate) == "PASS" for gate in required_prior_gates):
        raise SystemExit("required predecessor gates did not pass")

    states = pd.read_csv(source / "confirmation_candidate_states.csv")
    matched = pd.read_csv(source / "matched_all_variants.csv")
    reference = matched.loc[matched.variant.eq(REFERENCE_VARIANT)].copy()
    supported_ids = set(reference.loc[reference.supported.astype(bool), "scenario_id"])
    states = states.loc[states.scenario_id.isin(supported_ids)].copy()
    development_reference = reference.set_index("scenario_id").development_ct

    enumerated = pd.concat([
        early_late_pairs(states),
        inventory_pairs(states),
        count_pairs(states),
    ], ignore_index=True)
    if enumerated.contrast_id.duplicated().any():
        raise ValueError("enumerated contrast identifiers are not unique")
    ordinary = select_ordinary_representatives(enumerated, development_reference)
    pairs = pd.concat([enumerated, ordinary], ignore_index=True)
    cells = contrast_cells(pairs, matched)
    audit = audit_contrasts(cells)
    audit = audit.merge(
        pairs,
        on=["contrast_id", "contrast_class"],
        how="left",
        validate="one_to_one",
    )

    after = {str(path.relative_to(root)): sha256(path) for path in protected}
    class_counts = pairs.contrast_class.value_counts().sort_index().to_dict()
    eligible_counts = (
        audit.groupby("contrast_class").article_eligible.sum().astype(int).to_dict()
    )
    failure_counts = audit.failure_reason.fillna("PASS").value_counts().to_dict()
    ordinary_count_ok = int(class_counts.get("ordinary", 0)) == 3
    conditions = {
        "prior_output_hashes_reconcile": prior_hashes_reconcile,
        "protected_inputs_unchanged": before == after,
        "all_pairs_have_distinct_members": bool(
            pairs.member_a_scenario_id.ne(pairs.member_b_scenario_id).all()
        ),
        "complete_cell_count": int(len(cells)) == int(len(pairs) * 32),
        "three_development_only_ordinary_representatives": ordinary_count_ok,
        "at_least_one_ordinary_contrast_eligible": cts7_passes(audit),
    }
    passed = all(conditions.values())
    status = "PASS_CTS7_READY_FOR_CTS9" if passed else "FAIL_CTS7_STOP_ARTICLE_EXAMPLES"

    pairs.to_csv(output / "contrast_pairs.csv", index=False, float_format="%.12g", lineterminator="\n")
    cells.to_csv(output / "contrast_cells.csv", index=False, float_format="%.12g", lineterminator="\n")
    audit.to_csv(output / "contrast_audit.csv", index=False, float_format="%.12g", lineterminator="\n")
    validation = {
        "research_identity": "CT-S1",
        "version": BUILD_VERSION,
        "metric_version": VERSION,
        "status": status,
        "conditions": conditions,
        "contrast_counts": {str(key): int(value) for key, value in class_counts.items()},
        "eligible_counts": {str(key): int(value) for key, value in eligible_counts.items()},
        "failure_counts": {str(key): int(value) for key, value in failure_counts.items()},
        "ordinary_contrasts": audit.loc[
            audit.contrast_class.eq("ordinary"),
            [
                "contrast_id", "source_contrast_class", "article_eligible",
                "failure_reason", "development_reference_separation",
                "confirmation_reference_separation",
            ],
        ].to_dict(orient="records"),
        "restrictions": {
            "confirmation_results_used_for_selection": False,
            "failed_contrasts_replaced": False,
            "cts9_sampling_intervals": "not evaluated",
            "article_claims": False,
            "playbook_allowed": False,
        },
        "next_gate": "CTS9_SAMPLING_UNCERTAINTY" if passed else "STOP_ARTICLE_EXAMPLES",
    }
    write_json(output / "validation.json", validation)
    artifacts = sorted(path for path in output.iterdir() if path.is_file())
    manifest = {
        "version": BUILD_VERSION,
        "status": status,
        "code_sha256": {
            "build_ct_s1_contrasts.py": sha256(Path(__file__)),
            "ct_s1_core.py": sha256(HERE / "ct_s1_core.py"),
            "selection_rules": sha256(HERE / "CT_S1_CTS7_SELECTION_RULES.md"),
        },
        "inputs": before,
        "outputs": {
            path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
            for path in artifacts
        },
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }
    write_json(output / "manifest.json", manifest)
    print(json.dumps({
        "status": status,
        "contrast_counts": validation["contrast_counts"],
        "eligible_counts": validation["eligible_counts"],
        "failure_counts": validation["failure_counts"],
    }, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
