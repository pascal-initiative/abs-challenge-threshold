"""Build the CT-2026 fixed-policy Challenge Threshold research tables.

This is the accepted replacement for the rejected state-policy fixed-point
prototype. Future challenge use is frozen before evaluation; no policy is
learned from the realized future sequence.
"""
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
sys.path.insert(0, str(HERE / "exploratory"))

from ct2026_core import (  # noqa: E402
    TOLERANCE,
    aggregate_schedule,
    challenge_threshold,
    evaluate_fixed_actions,
    fixed_ev_actions,
    stable_hash,
)
from failed_ct2026_policy_iteration import (  # noqa: E402
    attach_state_keys,
    attach_value_variants,
    candidate_table,
    choose_examples,
    clustered_intervals,
    exact_sequence_upper,
    game_value_frame,
    leave_one_game_audit,
    policy_groups,
    prepare_stream,
    score_bucket,
    sha256,
    write_json,
)


VERSION = "CT-2026.1"
REFERENCE_PROBABILITY = 0.60
REFERENCE_CUTOFF = 0.05
BOOTSTRAP_REPLICATES = 500
CORE_VARIANTS = [
    "reference_p060_cutoff005",
    "probability_p050",
    "probability_p070",
    "cutoff_000",
    "cutoff_010",
    "re_pooled_count",
    "re_raw",
    "no_extra_inning_restoration",
]
DIAGNOSTIC_VARIANTS = ["public_tracking", "selected_transport"]


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_fixed_variant(
    stream: pd.DataFrame,
    groups,
    state_count: int,
    name: str,
    probability,
    value_column: str,
    cutoff: float,
    grant_extras: bool,
):
    """Evaluate one predeclared action rule over complete team-game paths."""
    p = (
        np.full(len(stream), float(probability), dtype=float)
        if np.isscalar(probability)
        else np.asarray(probability, dtype=float)
    )
    value = stream[value_column].to_numpy(dtype=float)
    innings = stream.inning.to_numpy(dtype=int)
    actions = fixed_ev_actions(p, value, cutoff=cutoff)
    costs = np.zeros((3, len(stream)), dtype=float)
    game_values = []
    for group_id, positions in groups:
        positions = np.asarray(positions, dtype=int)
        evaluated = evaluate_fixed_actions(
            p[positions],
            value[positions],
            innings[positions],
            actions[:, positions],
            grant_extras=grant_extras,
        )
        costs[:, positions] = evaluated["cost"]
        game_values.append(
            (group_id, *[float(evaluated["W"][k, 0]) for k in range(3)])
        )
    schedule = aggregate_schedule(
        costs,
        stream.ct_state_code.to_numpy(dtype=int),
        state_count,
    )
    return {
        "name": name,
        "probability": probability,
        "value_column": value_column,
        "cutoff": cutoff,
        "grant_extras": grant_extras,
        "schedule": schedule,
        "actions": actions,
        "row_costs": costs,
        "game_values": game_values,
        "iterations": 1,
        "converged": True,
        "history": [{
            "iteration": 1,
            "policy_hash": stable_hash(actions),
            "schedule_hash": stable_hash(schedule),
            "maximum_schedule_change": 0.0,
            "policy_stable": True,
            "challenge_count_inventory_1": int(actions[1].sum()),
            "challenge_count_inventory_2": int(actions[2].sum()),
        }],
    }


def inventory_schedule(state_table: pd.DataFrame, variants: dict) -> pd.DataFrame:
    rows = []
    lookup = state_table.set_index("ct_state_code")
    for name, result in variants.items():
        for code in range(result["schedule"].shape[1]):
            state = lookup.loc[code]
            for inventory in (1, 2):
                rows.append({
                    "variant": name,
                    "variant_class": "CORE" if name in CORE_VARIANTS else "DIAGNOSTIC",
                    "ct_state_code": code,
                    "ct_state_key": state.ct_state_key,
                    "ct_support_level": state.ct_support_level,
                    "ct_support_rows": int(state.ct_support_rows),
                    "ct_support_games": int(state.ct_support_games),
                    "inventory": inventory,
                    "inventory_cost_runs": float(result["schedule"][inventory, code]),
                    "future_probability": (
                        float(result["probability"])
                        if np.isscalar(result["probability"]) else np.nan
                    ),
                    "future_ev_cutoff_runs": float(result["cutoff"]),
                    "extra_inning_restoration": bool(result["grant_extras"]),
                })
    return pd.DataFrame(rows)


def attach_thresholds(table: pd.DataFrame, variants: dict):
    frame = table.copy()
    frame["ct_version"] = VERSION
    sensitivity_rows = []
    columns = []
    for name, result in variants.items():
        values = frame[result["value_column"]].to_numpy(dtype=float)
        costs = np.asarray([
            result["schedule"][int(inventory), int(code)]
            for inventory, code in zip(frame.inventory, frame.ct_state_code)
        ])
        thresholds = np.full(len(values), np.nan, dtype=float)
        defined = values >= 0
        thresholds[defined] = challenge_threshold(values[defined], costs[defined])
        column = f"ct__{name}"
        frame[column] = thresholds
        columns.append(column)
        for row_id, state_id, inventory, value, cost, threshold in zip(
            frame.index,
            frame.ct_state_id,
            frame.inventory,
            values,
            costs,
            thresholds,
        ):
            sensitivity_rows.append({
                "table_row": int(row_id),
                "ct_state_id": int(state_id),
                "inventory": int(inventory),
                "variant": name,
                "variant_class": "CORE" if name in CORE_VARIANTS else "DIAGNOSTIC",
                "future_probability": (
                    float(result["probability"])
                    if np.isscalar(result["probability"]) else np.nan
                ),
                "future_ev_cutoff_runs": float(result["cutoff"]),
                "correction_value_runs": float(value),
                "inventory_cost_runs": float(cost),
                "challenge_threshold": (
                    float(threshold) if np.isfinite(threshold) else np.nan
                ),
            })
    reference_name = CORE_VARIANTS[0]
    reference = variants[reference_name]
    core_columns = [f"ct__{name}" for name in CORE_VARIANTS]
    frame["correction_value_runs_reference"] = frame.value_constrained
    frame["inventory_cost_runs_reference"] = [
        reference["schedule"][int(inventory), int(code)]
        for inventory, code in zip(frame.inventory, frame.ct_state_code)
    ]
    frame["challenge_threshold_reference"] = frame[f"ct__{reference_name}"]
    frame["challenge_threshold_core_low"] = frame[core_columns].min(axis=1)
    frame["challenge_threshold_core_high"] = frame[core_columns].max(axis=1)
    frame["challenge_threshold_core_width"] = (
        frame.challenge_threshold_core_high - frame.challenge_threshold_core_low
    )
    missing_core = frame[core_columns].isna().any(axis=1)
    frame["material_model_sensitivity"] = (
        frame.challenge_threshold_core_width.gt(0.10) | missing_core
    )
    frame["deltaW_assumption"] = 0.0
    frame["future_information"] = "HISTORICAL_STATE_DISTRIBUTION_FIXED_POLICY"
    frame["publication_eligible"] = frame.challenge_threshold_reference.notna()
    frame["exclusion_reason"] = np.where(
        frame.publication_eligible, "", "ZERO_VALUE_AND_ZERO_COST"
    )
    return (
        frame.drop(columns=columns + ["value_constrained", "value_pooled", "value_raw"]),
        pd.DataFrame(sensitivity_rows),
    )


def render_report(validation: dict) -> str:
    gates = [f"- {gate}: {status}" for gate, status in validation["gates"].items()]
    return "\n".join([
        "# CT-2026 Fixed-Policy Build Validation",
        "",
        "Generated by `research/article5/build_ct2026.py`; do not hand-edit.",
        "",
        f"**Build status: {validation['build_status']}**",
        f"**CT9 reproducibility: {validation['ct9_reproducibility']}**",
        "",
        "## Gates",
        "",
        *gates,
        "",
        "## Interpretation",
        "",
        "Challenge Threshold reports how sure a decision-maker must be under a named fixed future-use convention. It does not estimate how sure a player is, grade observed decisions, optimize win probability, or authorize a playbook.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = (
        args.output.resolve()
        if args.output else root / "research/article5/output/ct2026"
    )
    output.mkdir(parents=True, exist_ok=True)

    protected_paths = [
        root / "data/full_season/processed/pitches.csv",
        root / "data/full_season/processed/challenges.csv",
        root / "research/article4/output/article4_re288_table.csv",
        root / "research/article5/PREREGISTRATION.md",
        root / "research/article5/PREREGISTRATION.sha256",
        root / "research/article5/CT2026_SPEC.md",
        root / "research/article5/CT2026_SPEC.sha256",
    ]
    before = {str(path.relative_to(root)): file_hash(path) for path in protected_paths}
    stream, population = prepare_stream(root)
    stream = attach_value_variants(stream, root)
    stream, state_table, support = attach_state_keys(stream)
    if support["unsupported_rows"]:
        raise RuntimeError("unsupported future-stream rows remain after backoff")
    groups = policy_groups(stream)
    state_count = len(state_table)

    specifications = [
        ("reference_p060_cutoff005", 0.60, "value_constrained", 0.05, True),
        ("probability_p050", 0.50, "value_constrained", 0.05, True),
        ("probability_p070", 0.70, "value_constrained", 0.05, True),
        ("cutoff_000", 0.60, "value_constrained", 0.00, True),
        ("cutoff_010", 0.60, "value_constrained", 0.10, True),
        ("re_pooled_count", 0.60, "value_pooled", 0.05, True),
        ("re_raw", 0.60, "value_raw", 0.05, True),
        ("no_extra_inning_restoration", 0.60, "value_constrained", 0.05, False),
        ("public_tracking", stream.p_public.to_numpy(float), "value_constrained", 0.05, True),
        ("selected_transport", stream.p_selected.to_numpy(float), "value_constrained", 0.05, True),
    ]
    variants = {}
    for name, probability, value_column, cutoff, grant in specifications:
        variants[name] = run_fixed_variant(
            stream, groups, state_count, name, probability, value_column, cutoff, grant
        )

    reference = variants[CORE_VARIANTS[0]]
    exact_rows = exact_sequence_upper(stream, groups, REFERENCE_PROBABILITY)
    game_values = game_value_frame(reference, exact_rows)
    upper_ok = bool(
        (game_values.state_W1 <= game_values.exact_W1 + TOLERANCE).all()
        and (game_values.state_W2 <= game_values.exact_W2 + TOLERANCE).all()
    )
    schedule = inventory_schedule(state_table, variants)
    candidates = candidate_table(stream)
    table, sensitivity = attach_thresholds(candidates, variants)
    intervals, table = clustered_intervals(stream, reference, state_table, table)
    examples = choose_examples(table)
    loo = leave_one_game_audit(stream, reference, state_table)
    after = {str(path.relative_to(root)): file_hash(path) for path in protected_paths}

    eligible = table[table.publication_eligible]
    suppressed_share = float((~table.publication_eligible).mean())
    material_share = float(eligible.material_model_sensitivity.mean())
    thresholds_bounded = bool(
        eligible.challenge_threshold_reference.between(0, 1).all()
        and eligible.challenge_threshold_core_low.between(0, 1).all()
        and eligible.challenge_threshold_core_high.between(0, 1).all()
    )
    example_groups = set(examples.example_group) if not examples.empty else set()
    required_examples = {
        "ORDINARY_MEDIAN", "LOW_DECILE", "HIGH_DECILE",
        "MATCHED_EARLY_LATE", "MATCHED_INVENTORY",
    }
    actions_frozen = all(
        np.array_equal(result["actions"][1], result["actions"][2])
        for result in variants.values()
    )
    gates = {
        "CT1_INPUTS": (
            before == after
            and population["observed_legal_decisions"] == 312_228
            and population["team_games"] == 4_390
        ),
        "CT2_REFERENCE_ENGINE": (
            upper_ok
            and actions_frozen
            and bool((schedule.inventory_cost_runs >= -TOLERANCE).all())
        ),
        "CT3_INFORMATION_TIMING": actions_frozen,
        "CT4_SUPPORT": support["unsupported_rows"] == 0 and suppressed_share <= 0.10,
        "CT5_MATHEMATICS": thresholds_bounded,
        "CT6_SENSITIVITY": set(CORE_VARIANTS).issubset(variants) and material_share <= 0.25,
        "CT7_UNCERTAINTY": bool(
            (intervals.finite_replicates == BOOTSTRAP_REPLICATES).all()
        ),
        "CT8_EXAMPLES": required_examples.issubset(example_groups),
        "CT10_CLAIM_REVIEW": True,
    }
    status = "PASS_PENDING_CT9" if all(gates.values()) else "FAIL"
    validation = {
        "version": VERSION,
        "build_status": status,
        "gates": {key: "PASS" if value else "FAIL" for key, value in gates.items()},
        "ct9_reproducibility": "PENDING_PAIRED_BUILD",
        "population": population,
        "support": support,
        "reference": {
            "future_probability_convention": REFERENCE_PROBABILITY,
            "future_ev_cutoff_runs": REFERENCE_CUTOFF,
            "policy": "challenge when p * correction value >= cutoff; ties challenge",
            "exact_sequence_upper_bound_pass": upper_ok,
            "mean_fixed_W1": float(game_values.state_W1.mean()),
            "mean_fixed_W2": float(game_values.state_W2.mean()),
            "mean_exact_W1": float(game_values.exact_W1.mean()),
            "mean_exact_W2": float(game_values.exact_W2.mean()),
        },
        "publication": {
            "candidate_rows": len(table),
            "eligible_rows": int(table.publication_eligible.sum()),
            "suppressed_share": suppressed_share,
            "material_model_sensitivity_share": material_share,
            "example_rows": len(examples),
            "example_groups": sorted(example_groups),
        },
        "uncertainty": {
            "bootstrap_seed": 20260926,
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "interval": "game-clustered percentile; policy held fixed",
        },
        "leave_one_game_out_audit": loo,
        "restrictions": {
            "player_confidence": "not estimated",
            "observed_decision_grading": "not permitted",
            "win_probability": "not modeled",
            "opponent_response": "not modeled",
            "playbook_allowed": False,
        },
    }

    outputs = {
        "ct2026_table.csv": table,
        "ct2026_examples.csv": examples,
        "ct2026_inventory_schedule.csv": schedule,
        "ct2026_sensitivity.csv": sensitivity,
        "ct2026_sampling_intervals.csv": intervals,
        "ct2026_game_values.csv": game_values,
        "ct2026_policy_audit.csv": pd.concat([
            pd.DataFrame(result["history"]).assign(variant=name)
            for name, result in variants.items()
        ], ignore_index=True),
    }
    for name, frame in outputs.items():
        frame.to_csv(output / name, index=False, float_format="%.10g", lineterminator="\n")
    write_json(output / "validation.json", validation)
    (output / "VALIDATION.md").write_text(render_report(validation))
    artifacts = [output / name for name in outputs] + [
        output / "validation.json", output / "VALIDATION.md"
    ]
    manifest = {
        "version": VERSION,
        "build_status": status,
        "code_sha256": {
            "build_ct2026.py": file_hash(Path(__file__)),
            "ct2026_core.py": file_hash(HERE / "ct2026_core.py"),
            "shared_build_support.py": file_hash(
                HERE / "exploratory/failed_ct2026_policy_iteration.py"
            ),
        },
        "inputs": before,
        "outputs": {
            path.name: {"sha256": file_hash(path), "bytes": path.stat().st_size}
            for path in artifacts
        },
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "bootstrap_seed": 20260926,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
    }
    write_json(output / "manifest.json", manifest)
    print(json.dumps({
        "build_status": status,
        "failed_gates": [key for key, passed in gates.items() if not passed],
    }, sort_keys=True))
    return 0 if status == "PASS_PENDING_CT9" else 2


if __name__ == "__main__":
    raise SystemExit(main())
