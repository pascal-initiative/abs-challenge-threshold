"""Build the frozen CT-S1 period adapters and evaluated row-cost schedules.

CTS3 prepares development and confirmation with the same reviewed code.  It
does not calculate temporal drift, select contrasts, or make article claims.
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

from build_dynamic_engine import prepare_stream  # noqa: E402
from ct2026_core import TOLERANCE, evaluate_fixed_actions, fixed_ev_actions  # noqa: E402
from ct_s1_core import (  # noqa: E402
    CONFIRMATION_MIN_GAMES,
    CONFIRMATION_MIN_ROWS,
    CORE_VARIANTS,
    DEVELOPMENT_MIN_GAMES,
    DEVELOPMENT_MIN_ROWS,
    DIAGNOSTIC_VARIANTS,
    VERSION,
    summarize_support_schedule,
    validate_information_fields,
    validate_team_game_order,
)
from failed_ct2026_policy_iteration import attach_value_variants, policy_groups  # noqa: E402


BUILD_VERSION = "ct-s1.0-cts3"
REFERENCE_PROBABILITY = 0.60
REFERENCE_CUTOFF = 0.05

VARIANT_SPECS = (
    ("reference_fixed_0.60", 0.60, "value_constrained", 0.05, True),
    ("fixed_0.50", 0.50, "value_constrained", 0.05, True),
    ("fixed_0.70", 0.70, "value_constrained", 0.05, True),
    ("cutoff_0.00", 0.60, "value_constrained", 0.00, True),
    ("cutoff_0.10", 0.60, "value_constrained", 0.10, True),
    ("re_pooled_count", 0.60, "value_pooled", 0.05, True),
    ("re_raw", 0.60, "value_raw", 0.05, True),
    ("no_extra_inning_restoration", 0.60, "value_constrained", 0.05, False),
    ("public_tracking", "p_public", "value_constrained", 0.05, True),
    ("selected_transport", "p_selected", "value_constrained", 0.05, True),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def expected_accepted_hashes(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text().splitlines():
        digest, relative = line.split(maxsplit=1)
        result[relative] = digest
    return result


def probability_values(stream: pd.DataFrame, specification) -> np.ndarray:
    if isinstance(specification, str):
        return stream[specification].to_numpy(dtype=float)
    return np.full(len(stream), float(specification), dtype=float)


def evaluate_variant_rows(
    stream: pd.DataFrame,
    *,
    probability,
    value_column: str,
    cutoff: float,
    grant_extras: bool,
) -> dict:
    p = probability_values(stream, probability)
    values = stream[value_column].to_numpy(dtype=float)
    actions = fixed_ev_actions(p, values, cutoff=cutoff)
    costs = np.zeros((3, len(stream)), dtype=float)
    game_values = []
    for group_id, positions in policy_groups(stream):
        positions = np.asarray(positions, dtype=int)
        evaluated = evaluate_fixed_actions(
            p[positions],
            values[positions],
            stream.inning.to_numpy(dtype=int)[positions],
            actions[:, positions],
            grant_extras=grant_extras,
        )
        costs[:, positions] = evaluated["cost"]
        game_values.append({
            "game_pk": int(group_id[0]),
            "team_id": int(group_id[1]),
            "W0": float(evaluated["W"][0, 0]),
            "W1": float(evaluated["W"][1, 0]),
            "W2": float(evaluated["W"][2, 0]),
        })
    return {
        "probability": probability,
        "value_column": value_column,
        "cutoff": cutoff,
        "grant_extras": grant_extras,
        "actions": actions,
        "costs": costs,
        "game_values": game_values,
    }


def prepare_period(
    root: Path,
    pitches_path: Path,
    *,
    period: str,
    min_rows: int,
    min_games: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    stream, population = prepare_stream(root, pitches_path=pitches_path)
    stream = attach_value_variants(stream, root)
    stream["decision_sequence"] = stream.groupby(
        ["game_pk", "team_id"], sort=False
    ).cumcount()
    validate_team_game_order(stream)

    evaluated = {}
    schedules = []
    game_values = []
    for name, probability, value_column, cutoff, grant_extras in VARIANT_SPECS:
        result = evaluate_variant_rows(
            stream,
            probability=probability,
            value_column=value_column,
            cutoff=cutoff,
            grant_extras=grant_extras,
        )
        evaluated[name] = result
        stream[f"cost_inventory_1__{name}"] = result["costs"][1]
        stream[f"cost_inventory_2__{name}"] = result["costs"][2]
        support_rows = stream.assign(
            cost_inventory_1=result["costs"][1],
            cost_inventory_2=result["costs"][2],
        )
        summary = summarize_support_schedule(
            support_rows,
            period=period,
            min_rows=min_rows,
            min_games=min_games,
        )
        summary.insert(1, "variant", name)
        summary.insert(
            2, "variant_class", "CORE" if name in CORE_VARIANTS else "DIAGNOSTIC"
        )
        schedules.append(summary)
        game_values.extend(
            {**row, "period": period, "variant": name}
            for row in result["game_values"]
        )

    reference = evaluated["reference_fixed_0.60"]
    action_canary = stream[["value_constrained"]].copy()
    p = np.full(len(stream), REFERENCE_PROBABILITY)
    before = fixed_ev_actions(p, action_canary.value_constrained, REFERENCE_CUTOFF)
    if len(action_canary) > 1:
        action_canary.iloc[-1, 0] = action_canary.iloc[-1, 0] + 100.0
    after = fixed_ev_actions(p, action_canary.value_constrained, REFERENCE_CUTOFF)
    current_action_unchanged = bool(np.array_equal(before[:, 0], after[:, 0]))
    population.update({
        "period": period,
        "date_min": str(stream.game_date.min()),
        "date_max": str(stream.game_date.max()),
        "legal_candidate_rows": int(stream.observed_legal_decision.sum()),
        "reference_action_count": int(reference["actions"][1].sum()),
        "reference_actions_inventory_invariant": bool(
            np.array_equal(reference["actions"][1], reference["actions"][2])
        ),
        "reference_current_action_canary": current_action_unchanged,
        "reference_costs_finite": bool(np.isfinite(reference["costs"]).all()),
        "reference_costs_nonnegative": bool((reference["costs"] >= -TOLERANCE).all()),
    })
    return (
        stream,
        pd.concat(schedules, ignore_index=True),
        pd.DataFrame(game_values),
        population,
    )


def output_columns() -> list[str]:
    base = [
        "pitch_key", "game_pk", "game_date", "team_id", "decision_sequence",
        "inning", "half_inning", "outs", "balls", "strikes", "base_state",
        "original_call", "side", "team_role", "team_score_diff",
        "observed_legal_decision", "value_constrained", "value_pooled", "value_raw",
        "p_public", "p_selected",
    ]
    costs = [
        f"cost_inventory_{inventory}__{name}"
        for name, *_ in VARIANT_SPECS
        for inventory in (1, 2)
    ]
    return base + costs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output or root / "data/ct_s1/cts3").resolve()
    if output.exists():
        raise SystemExit(f"output must not already exist: {output}")
    output.mkdir(parents=True)

    dev_pitches = root / "data/full_season/processed/pitches.csv"
    conf_pitches = root / "data/ct_s1/reconstructed/processed/pitches.csv"
    protected_paths = [
        dev_pitches,
        root / "data/full_season/processed/challenges.csv",
        conf_pitches,
        root / "data/ct_s1/reconstructed/processed/challenges.csv",
        root / "data/ct_s1/preflight/validation.json",
        root / "data/ct_s1/reconstructed/CTS2_VALIDATION.json",
        root / "research/article4/output/article4_re288_table.csv",
        root / "research/article5/AMENDMENT_005_CT_SUCCESSOR_STANDARD.md",
        root / "research/article5/CT_SUCCESSOR_VALIDATION_PLAN.md",
        root / "research/article5/CT_S1_MODEL_SCHEMA.md",
        root / "research/article5/CT_S1_ACCEPTED_INPUTS.sha256",
    ]
    before = {str(path.relative_to(root)): sha256(path) for path in protected_paths}
    accepted = expected_accepted_hashes(root / "research/article5/CT_S1_ACCEPTED_INPUTS.sha256")
    accepted_reconciles = all(
        relative == "RAW_SNAPSHOT_INVENTORY"
        or (root / relative).is_file() and sha256(root / relative) == digest
        for relative, digest in accepted.items()
    )

    validate_information_fields(
        ["fixed_probability", "correction_value", "fixed_ev_cutoff"]
    )
    validate_information_fields(
        ["inning_exact", "inning_bucket", "half_inning", "outs", "team_role", "score_bucket"]
    )
    development = prepare_period(
        root,
        dev_pitches,
        period="development",
        min_rows=DEVELOPMENT_MIN_ROWS,
        min_games=DEVELOPMENT_MIN_GAMES,
    )
    confirmation = prepare_period(
        root,
        conf_pitches,
        period="confirmation",
        min_rows=CONFIRMATION_MIN_ROWS,
        min_games=CONFIRMATION_MIN_GAMES,
    )
    dev_stream, dev_schedule, dev_games, dev_population = development
    conf_stream, conf_schedule, conf_games, conf_population = confirmation
    after = {str(path.relative_to(root)): sha256(path) for path in protected_paths}

    expected_variants = set(CORE_VARIANTS) | set(DIAGNOSTIC_VARIANTS)
    actual_variants = {row[0] for row in VARIANT_SPECS}
    conditions = {
        "accepted_input_hashes_reconcile": accepted_reconciles,
        "protected_inputs_unchanged": before == after,
        "period_schemas_match": list(pd.read_csv(dev_pitches, nrows=0).columns)
        == list(pd.read_csv(conf_pitches, nrows=0).columns),
        "periods_do_not_overlap": pd.to_datetime(dev_stream.game_date).max()
        < pd.to_datetime(conf_stream.game_date).min(),
        "confirmation_window_exact": conf_population["date_min"] == "2026-09-11"
        and conf_population["date_max"] == "2026-09-27",
        "complete_variant_grid": actual_variants == expected_variants,
        "reference_actions_inventory_invariant": bool(
            dev_population["reference_actions_inventory_invariant"]
            and conf_population["reference_actions_inventory_invariant"]
        ),
        "current_action_canary_passes": bool(
            dev_population["reference_current_action_canary"]
            and conf_population["reference_current_action_canary"]
        ),
        "reference_costs_valid": bool(
            dev_population["reference_costs_finite"]
            and conf_population["reference_costs_finite"]
            and dev_population["reference_costs_nonnegative"]
            and conf_population["reference_costs_nonnegative"]
        ),
        "support_schedules_present": bool(len(dev_schedule) and len(conf_schedule)),
    }
    status = "PASS_CTS3_READY_FOR_CTS4_CTS8" if all(conditions.values()) else "FAIL_CTS3"

    dev_stream[output_columns()].to_csv(
        output / "development_prepared.csv", index=False, float_format="%.12g", lineterminator="\n"
    )
    conf_stream[output_columns()].to_csv(
        output / "confirmation_prepared.csv", index=False, float_format="%.12g", lineterminator="\n"
    )
    pd.concat([dev_schedule, conf_schedule], ignore_index=True).to_csv(
        output / "support_schedules.csv", index=False, float_format="%.12g", lineterminator="\n"
    )
    pd.concat([dev_games, conf_games], ignore_index=True).to_csv(
        output / "game_values.csv", index=False, float_format="%.12g", lineterminator="\n"
    )
    validation = {
        "research_identity": "CT-S1",
        "version": BUILD_VERSION,
        "metric_version": VERSION,
        "status": status,
        "conditions": conditions,
        "variant_specs": [
            {
                "name": name,
                "probability": probability,
                "value_column": value_column,
                "cutoff": cutoff,
                "extra_inning_restoration": grant,
                "variant_class": "CORE" if name in CORE_VARIANTS else "DIAGNOSTIC",
            }
            for name, probability, value_column, cutoff, grant in VARIANT_SPECS
        ],
        "development": dev_population,
        "confirmation": conf_population,
        "restrictions": {
            "temporal_stability": "not evaluated in CTS3",
            "model_spread": "not evaluated in CTS3",
            "article_claims": False,
            "playbook_allowed": False,
        },
        "next_gate": "CTS4_INFORMATION_TIMING_AND_CTS5_SUPPORT",
    }
    write_json(output / "validation.json", validation)
    artifacts = sorted(path for path in output.iterdir() if path.is_file())
    manifest = {
        "version": BUILD_VERSION,
        "status": status,
        "code_sha256": {
            "build_ct_s1_prepared.py": sha256(Path(__file__)),
            "build_dynamic_engine.py": sha256(HERE / "build_dynamic_engine.py"),
            "ct2026_core.py": sha256(HERE / "ct2026_core.py"),
            "ct_s1_core.py": sha256(HERE / "ct_s1_core.py"),
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
        "failed_conditions": [key for key, passed in conditions.items() if not passed],
        "development_rows": len(dev_stream),
        "confirmation_rows": len(conf_stream),
    }, sort_keys=True))
    return 0 if status.startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
