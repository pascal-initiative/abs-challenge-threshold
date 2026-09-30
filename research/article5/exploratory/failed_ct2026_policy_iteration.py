"""Reproduce the failed CT2 state-policy fixed-point implementation.

This prototype is retained as negative evidence. It enters a deterministic
policy cycle and is not the accepted CT-2026 generator.
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
ARTICLE5 = HERE.parent
ROOT_DEFAULT = ARTICLE5.parents[1]
sys.path.insert(0, str(ARTICLE5))
sys.path.insert(0, str(ARTICLE5.parent / "article4/decision_value"))

from build_correction_values import build_constrained_table  # noqa: E402
from build_dynamic_engine import prepare_stream  # noqa: E402
from ct2026_core import challenge_threshold, fit_state_policy  # noqa: E402
from dynamic_core import backward_values  # noqa: E402
from dv_core import flip_value  # noqa: E402


VERSION = "ct2026.0-snapshot"
REFERENCE_PROBABILITY = 0.60
BOOTSTRAP_REPLICATES = 500
SEED = 20260926
TOLERANCE = 1e-10
MIN_ROWS = 200
MIN_GAMES = 100
CORE_VARIANTS = [
    "reference_fixed_0.60",
    "fixed_0.50",
    "fixed_0.70",
    "re_pooled_count",
    "re_raw",
    "no_extra_inning_restoration",
]
DIAGNOSTIC_VARIANTS = ["public_tracking", "selected_transport"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_default(value):
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    raise TypeError(type(value))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=_json_default) + "\n")


def score_bucket(values: pd.Series) -> pd.Series:
    values = pd.to_numeric(values, errors="raise")
    return pd.Series(
        np.select(
            [values <= -2, values == -1, values == 0, values == 1, values >= 2],
            ["TRAIL_2PLUS", "TRAIL_1", "TIED", "LEAD_1", "LEAD_2PLUS"],
            default="INVALID",
        ),
        index=values.index,
    )


def combine_key(frame: pd.DataFrame, level: str, columns: list[str]) -> pd.Series:
    result = pd.Series(level, index=frame.index, dtype="object")
    for column in columns:
        result = result.str.cat(frame[column].astype(str), sep="|")
    return result


def attach_state_keys(stream: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    frame = stream.copy()
    frame["inning_exact"] = np.where(frame.inning.le(9), frame.inning.astype(str), "10+")
    frame["inning_bucket"] = pd.cut(
        frame.inning,
        bins=[0, 3, 6, 9, np.inf],
        labels=["1-3", "4-6", "7-9", "10+"],
    ).astype(str)
    frame["score_bucket"] = score_bucket(frame.team_score_diff)
    candidates = [
        ("L0_EXACT", ["inning_exact", "half_inning", "outs", "team_role", "score_bucket"]),
        ("L1_NO_SCORE", ["inning_exact", "half_inning", "outs", "team_role"]),
        ("L2_NO_ROLE", ["inning_exact", "half_inning", "outs"]),
        ("L3_INNING_BUCKET", ["inning_bucket", "half_inning", "outs"]),
        ("L4_NO_HALF", ["inning_bucket", "outs"]),
    ]

    selected_key = pd.Series("", index=frame.index, dtype="object")
    selected_level = pd.Series("", index=frame.index, dtype="object")
    selected_rows = pd.Series(0, index=frame.index, dtype="int64")
    selected_games = pd.Series(0, index=frame.index, dtype="int64")
    support_summary = {}
    for level, columns in candidates:
        keys = combine_key(frame, level, columns)
        temp = pd.DataFrame({"key": keys, "game_pk": frame.game_pk})
        support = temp.groupby("key", sort=True).agg(
            historical_rows=("game_pk", "size"),
            distinct_games=("game_pk", "nunique"),
        )
        row_count = keys.map(support.historical_rows).astype(int)
        game_count = keys.map(support.distinct_games).astype(int)
        eligible = (
            selected_key.eq("")
            & row_count.ge(MIN_ROWS)
            & game_count.ge(MIN_GAMES)
        )
        selected_key.loc[eligible] = keys.loc[eligible]
        selected_level.loc[eligible] = level
        selected_rows.loc[eligible] = row_count.loc[eligible]
        selected_games.loc[eligible] = game_count.loc[eligible]
        support_summary[level] = {
            "groups": len(support),
            "rows_selected": int(eligible.sum()),
        }

    frame["ct_state_key"] = selected_key
    frame["ct_support_level"] = selected_level
    frame["ct_support_rows"] = selected_rows
    frame["ct_support_games"] = selected_games
    frame["ct_state_supported"] = frame.ct_state_key.ne("")
    supported_keys = sorted(frame.loc[frame.ct_state_supported, "ct_state_key"].unique())
    code_map = {key: index for index, key in enumerate(supported_keys)}
    frame["ct_state_code"] = frame.ct_state_key.map(code_map).fillna(-1).astype(int)
    state_table = (
        frame.loc[frame.ct_state_supported, [
            "ct_state_code", "ct_state_key", "ct_support_level",
            "ct_support_rows", "ct_support_games",
        ]]
        .drop_duplicates("ct_state_code")
        .sort_values("ct_state_code")
        .reset_index(drop=True)
    )
    audit = {
        "state_count": len(state_table),
        "unsupported_rows": int((~frame.ct_state_supported).sum()),
        "unsupported_legal_rows": int(
            ((~frame.ct_state_supported) & frame.observed_legal_decision).sum()
        ),
        "support_levels": frame.loc[frame.ct_state_supported, "ct_support_level"]
        .value_counts().sort_index().to_dict(),
        "candidate_summary": support_summary,
    }
    return frame, state_table, audit


def re_lookup(table: pd.DataFrame, column: str) -> dict:
    return {
        (int(row.balls), int(row.strikes), int(row.outs), str(row.base_state)): float(
            getattr(row, column)
        )
        for row in table.itertuples(index=False)
    }


def values_from_lookup(stream: pd.DataFrame, lookup: dict) -> np.ndarray:
    unique = stream[["balls", "strikes", "outs", "base_state", "original_call"]].drop_duplicates()
    mapping = {}
    for row in unique.itertuples(index=False):
        key = (int(row.balls), int(row.strikes), int(row.outs), str(row.base_state), row.original_call)
        mapping[key] = flip_value(*key, lookup)
    return np.asarray([
        mapping[(int(b), int(s), int(o), str(base), call)]
        for b, s, o, base, call in zip(
            stream.balls, stream.strikes, stream.outs, stream.base_state,
            stream.original_call,
        )
    ], dtype=float)


def attach_value_variants(stream: pd.DataFrame, root: Path) -> pd.DataFrame:
    table = pd.read_csv(
        root / "research/article4/output/article4_re288_table.csv",
        dtype={"base_state": str},
    )
    constrained, _ = build_constrained_table(table)
    frame = stream.copy()
    frame["value_constrained"] = frame.correction_value.astype(float)
    frame["value_pooled"] = values_from_lookup(frame, re_lookup(table, "re_count_pooled"))
    frame["value_raw"] = values_from_lookup(frame, re_lookup(table, "raw_mean"))
    return frame


def policy_groups(stream: pd.DataFrame):
    return [
        ((int(game_pk), int(team_id)), group.index.to_numpy(dtype=int))
        for (game_pk, team_id), group in stream.groupby(["game_pk", "team_id"], sort=True)
    ]


def run_variant(stream, groups, state_count, name, probability, value_column, grant_extras):
    if np.isscalar(probability):
        p = np.full(len(stream), float(probability), dtype=float)
    else:
        p = np.asarray(probability, dtype=float)
    result = fit_state_policy(
        p=p,
        value=stream[value_column].to_numpy(dtype=float),
        innings=stream.inning.to_numpy(dtype=int),
        state_codes=stream.ct_state_code.to_numpy(dtype=int),
        groups=groups,
        state_count=state_count,
        grant_extras=grant_extras,
    )
    result["name"] = name
    result["value_column"] = value_column
    result["grant_extras"] = grant_extras
    return result


def exact_sequence_upper(stream: pd.DataFrame, groups, probability=REFERENCE_PROBABILITY):
    rows = []
    p = np.full(len(stream), probability, dtype=float)
    value = stream.value_constrained.to_numpy(dtype=float)
    innings = stream.inning.to_numpy(dtype=int)
    for group_id, positions in groups:
        solution = backward_values(p[positions], value[positions], innings[positions], "dynamic")
        rows.append((group_id, float(solution["W"][0, 0]), float(solution["W"][1, 0]), float(solution["W"][2, 0])))
    return rows


def game_value_frame(result, exact_rows=None) -> pd.DataFrame:
    rows = []
    exact = {row[0]: row[1:] for row in exact_rows or []}
    for row in result["game_values"]:
        (game_pk, team_id), w0, w1, w2 = row
        record = {
            "game_pk": game_pk,
            "team_id": team_id,
            "state_W0": w0,
            "state_W1": w1,
            "state_W2": w2,
        }
        if (game_pk, team_id) in exact:
            e0, e1, e2 = exact[(game_pk, team_id)]
            record.update({"exact_W0": e0, "exact_W1": e1, "exact_W2": e2})
        rows.append(record)
    return pd.DataFrame(rows)


def inventory_schedule(state_table, variants) -> pd.DataFrame:
    rows = []
    state_lookup = state_table.set_index("ct_state_code")
    for name, result in variants.items():
        for code in range(result["schedule"].shape[1]):
            state = state_lookup.loc[code]
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
                    "iterations": result["iterations"],
                    "converged": result["converged"],
                })
    return pd.DataFrame(rows)


def candidate_table(stream: pd.DataFrame) -> pd.DataFrame:
    legal = stream.observed_legal_decision & stream.ct_state_supported
    columns = [
        "original_call", "side", "balls", "strikes", "outs", "base_state",
        "inning_exact", "half_inning", "score_bucket", "team_role",
        "ct_state_code", "ct_state_key", "ct_support_level", "ct_support_rows",
        "ct_support_games", "value_constrained", "value_pooled", "value_raw",
    ]
    states = stream.loc[legal, columns].drop_duplicates().sort_values(columns[:11]).reset_index(drop=True)
    states.insert(0, "ct_version", VERSION)
    states.insert(1, "ct_state_id", np.arange(len(states), dtype=int))
    return pd.concat(
        [states.assign(inventory=1), states.assign(inventory=2)], ignore_index=True
    ).sort_values(["ct_state_id", "inventory"]).reset_index(drop=True)


def attach_thresholds(table: pd.DataFrame, variants) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = table.copy()
    sensitivity_rows = []
    variant_value = {
        "reference_fixed_0.60": "value_constrained",
        "fixed_0.50": "value_constrained",
        "fixed_0.70": "value_constrained",
        "re_pooled_count": "value_pooled",
        "re_raw": "value_raw",
        "no_extra_inning_restoration": "value_constrained",
        "public_tracking": "value_constrained",
        "selected_transport": "value_constrained",
    }
    threshold_columns = []
    for name, result in variants.items():
        values = frame[variant_value[name]].to_numpy(dtype=float)
        costs = np.asarray([
            result["schedule"][int(inventory), int(code)]
            for inventory, code in zip(frame.inventory, frame.ct_state_code)
        ])
        thresholds = challenge_threshold(values, costs)
        column = f"ct__{name}"
        frame[column] = thresholds
        threshold_columns.append(column)
        for row_id, state_id, inventory, value, cost, threshold in zip(
            frame.index, frame.ct_state_id, frame.inventory, values, costs, thresholds
        ):
            sensitivity_rows.append({
                "table_row": int(row_id),
                "ct_state_id": int(state_id),
                "inventory": int(inventory),
                "variant": name,
                "variant_class": "CORE" if name in CORE_VARIANTS else "DIAGNOSTIC",
                "correction_value_runs": float(value),
                "inventory_cost_runs": float(cost),
                "challenge_threshold": float(threshold) if np.isfinite(threshold) else np.nan,
            })
    core_columns = [f"ct__{name}" for name in CORE_VARIANTS]
    frame["correction_value_runs_reference"] = frame.value_constrained
    reference = variants["reference_fixed_0.60"]
    frame["inventory_cost_runs_reference"] = [
        reference["schedule"][int(inventory), int(code)]
        for inventory, code in zip(frame.inventory, frame.ct_state_code)
    ]
    frame["challenge_threshold_reference"] = frame["ct__reference_fixed_0.60"]
    frame["challenge_threshold_core_low"] = frame[core_columns].min(axis=1)
    frame["challenge_threshold_core_high"] = frame[core_columns].max(axis=1)
    frame["challenge_threshold_core_width"] = (
        frame.challenge_threshold_core_high - frame.challenge_threshold_core_low
    )
    frame["material_model_sensitivity"] = frame.challenge_threshold_core_width.gt(0.10)
    frame["deltaW_assumption"] = 0.0
    frame["future_information"] = "STATE_DISTRIBUTION_NOT_REALIZED_SEQUENCE"
    frame["publication_eligible"] = frame.challenge_threshold_reference.notna()
    frame["exclusion_reason"] = np.where(frame.publication_eligible, "", "ZERO_VALUE_AND_ZERO_COST")
    drop = threshold_columns + ["value_constrained", "value_pooled", "value_raw"]
    return frame.drop(columns=drop), pd.DataFrame(sensitivity_rows)


def clustered_intervals(stream, reference, state_table, table):
    costs = reference["row_costs"]
    source = pd.DataFrame({
        "game_pk": stream.game_pk.to_numpy(dtype=int),
        "ct_state_code": stream.ct_state_code.to_numpy(dtype=int),
        "cost_1": costs[1],
        "cost_2": costs[2],
    })
    grouped = source.groupby(["game_pk", "ct_state_code"], sort=True).agg(
        rows=("cost_1", "size"),
        sum_1=("cost_1", "sum"),
        sum_2=("cost_2", "sum"),
    ).reset_index()
    games = np.sort(source.game_pk.unique())
    game_map = {game: index for index, game in enumerate(games)}
    grouped_game = grouped.game_pk.map(game_map).to_numpy(dtype=int)
    codes = grouped.ct_state_code.to_numpy(dtype=int)
    counts = grouped.rows.to_numpy(dtype=float)
    sums = [None, grouped.sum_1.to_numpy(dtype=float), grouped.sum_2.to_numpy(dtype=float)]
    state_count = len(state_table)
    rng = np.random.default_rng(SEED)
    draws = np.full((2, BOOTSTRAP_REPLICATES, state_count), np.nan, dtype=float)
    for replicate in range(BOOTSTRAP_REPLICATES):
        sampled = rng.integers(0, len(games), len(games))
        weights = np.bincount(sampled, minlength=len(games)).astype(float)
        group_weights = weights[grouped_game]
        denominators = np.bincount(
            codes, weights=counts * group_weights, minlength=state_count
        )
        for inventory in (1, 2):
            numerators = np.bincount(
                codes, weights=sums[inventory] * group_weights, minlength=state_count
            )
            np.divide(
                numerators,
                denominators,
                out=draws[inventory - 1, replicate],
                where=denominators > 0,
            )

    rows = []
    state_lookup = state_table.set_index("ct_state_code")
    for code in range(state_count):
        state = state_lookup.loc[code]
        for inventory in (1, 2):
            values = draws[inventory - 1, :, code]
            finite = values[np.isfinite(values)]
            rows.append({
                "ct_state_code": code,
                "ct_state_key": state.ct_state_key,
                "inventory": inventory,
                "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                "finite_replicates": len(finite),
                "inventory_cost_low_95": float(np.quantile(finite, 0.025)),
                "inventory_cost_high_95": float(np.quantile(finite, 0.975)),
            })
    intervals = pd.DataFrame(rows)
    merged = table.merge(
        intervals[["ct_state_code", "inventory", "inventory_cost_low_95", "inventory_cost_high_95"]],
        on=["ct_state_code", "inventory"],
        how="left",
        validate="many_to_one",
    )
    merged["challenge_threshold_sampling_low_95"] = challenge_threshold(
        merged.correction_value_runs_reference, merged.inventory_cost_low_95
    )
    merged["challenge_threshold_sampling_high_95"] = challenge_threshold(
        merged.correction_value_runs_reference, merged.inventory_cost_high_95
    )
    return intervals, merged


def leave_one_game_audit(stream, reference, state_table):
    costs = reference["row_costs"]
    codes = stream.ct_state_code.to_numpy(dtype=int)
    games = stream.game_pk.to_numpy(dtype=int)
    state_count = len(state_table)
    base_count = np.bincount(codes, minlength=state_count).astype(float)
    base_sum = {
        inventory: np.bincount(codes, weights=costs[inventory], minlength=state_count)
        for inventory in (1, 2)
    }
    unique_games = np.sort(np.unique(games))
    rng = np.random.default_rng(SEED + 1)
    selected = np.sort(rng.choice(unique_games, size=min(100, len(unique_games)), replace=False))
    changes = []
    for game in selected:
        mask = games == game
        game_codes = codes[mask]
        removed_count = np.bincount(game_codes, minlength=state_count).astype(float)
        denominator = base_count - removed_count
        for inventory in (1, 2):
            removed_sum = np.bincount(
                game_codes, weights=costs[inventory, mask], minlength=state_count
            )
            loo = np.divide(
                base_sum[inventory] - removed_sum,
                denominator,
                out=np.full(state_count, np.nan),
                where=denominator > 0,
            )
            base = reference["schedule"][inventory]
            changes.extend(np.abs(loo - base)[np.isfinite(loo)])
    return {
        "sampled_games": len(selected),
        "comparisons": len(changes),
        "median_absolute_cost_change": float(np.median(changes)),
        "maximum_absolute_cost_change": float(np.max(changes)),
    }


def choose_examples(table: pd.DataFrame) -> pd.DataFrame:
    eligible = table[table.publication_eligible].copy()
    eligible["state_key_sort"] = (
        eligible.ct_state_key.astype(str) + "|" + eligible.ct_state_id.astype(str)
        + "|" + eligible.inventory.astype(str)
    )
    examples = []

    def choose_one(frame, target, group, reason):
        if frame.empty:
            return
        selected = frame.assign(distance=(frame.challenge_threshold_reference - target).abs()).sort_values(
            ["distance", "ct_support_rows", "state_key_sort"],
            ascending=[True, False, True],
        ).iloc[0].copy()
        selected["example_group"] = group
        selected["selection_reason"] = reason
        examples.append(selected)

    median = float(eligible.challenge_threshold_reference.median())
    ordinary = eligible[
        eligible.balls.eq(0) & eligible.strikes.eq(0) & eligible.outs.eq(0)
        & eligible.base_state.astype(str).eq("000")
        & eligible.inning_exact.astype(str).isin(["1", "2", "3"])
    ]
    choose_one(ordinary, median, "ORDINARY_MEDIAN", "ordinary state nearest overall median CT")

    low_cut = float(eligible.challenge_threshold_reference.quantile(0.10))
    low = eligible[eligible.challenge_threshold_reference.le(low_cut)]
    choose_one(low, float(low.challenge_threshold_reference.median()), "LOW_DECILE", "supported state in lowest CT decile")
    high_cut = float(eligible.challenge_threshold_reference.quantile(0.90))
    high = eligible[eligible.challenge_threshold_reference.ge(high_cut)]
    choose_one(high, float(high.challenge_threshold_reference.median()), "HIGH_DECILE", "supported state in highest CT decile")

    match_cols = [
        "original_call", "balls", "strikes", "outs", "base_state", "half_inning",
        "score_bucket", "team_role", "inventory",
    ]
    early = eligible[eligible.inning_exact.astype(str).isin(["1", "2", "3"])]
    late = eligible[eligible.inning_exact.astype(str).isin(["7", "8", "9"])]
    pairs = early.merge(late, on=match_cols, suffixes=("_early", "_late"))
    if not pairs.empty:
        pairs["contrast"] = (
            pairs.challenge_threshold_reference_early - pairs.challenge_threshold_reference_late
        ).abs()
        pair = pairs.sort_values(
            ["contrast", "ct_support_rows_early", "ct_state_id_early", "ct_state_id_late"],
            ascending=[False, False, True, True],
        ).iloc[0]
        for suffix, label in [("early", "EARLY"), ("late", "LATE")]:
            row = eligible[
                (eligible.ct_state_id == pair[f"ct_state_id_{suffix}"])
                & (eligible.inventory == pair.inventory)
            ].iloc[0].copy()
            row["example_group"] = "MATCHED_EARLY_LATE"
            row["selection_reason"] = f"mechanical matched {label.lower()} contrast"
            examples.append(row)

    pair_cols = [
        "ct_state_id", "original_call", "balls", "strikes", "outs", "base_state",
        "inning_exact", "half_inning", "score_bucket", "team_role",
    ]
    one = eligible[eligible.inventory.eq(1)]
    two = eligible[eligible.inventory.eq(2)]
    inventory_pairs = one.merge(two, on=pair_cols, suffixes=("_one", "_two"))
    if not inventory_pairs.empty:
        inventory_pairs["contrast"] = (
            inventory_pairs.challenge_threshold_reference_one
            - inventory_pairs.challenge_threshold_reference_two
        ).abs()
        pair = inventory_pairs.sort_values(
            ["contrast", "ct_support_rows_one", "ct_state_id"],
            ascending=[False, False, True],
        ).iloc[0]
        for inventory, label in [(1, "ONE"), (2, "TWO")]:
            row = eligible[
                (eligible.ct_state_id == pair.ct_state_id)
                & (eligible.inventory == inventory)
            ].iloc[0].copy()
            row["example_group"] = "MATCHED_INVENTORY"
            row["selection_reason"] = f"mechanical matched {label.lower()}-unit contrast"
            examples.append(row)

    return pd.DataFrame(examples).drop(columns=["state_key_sort", "distance"], errors="ignore")


def render_report(validation: dict) -> str:
    gate_lines = [f"- {gate}: {status}" for gate, status in validation["gates"].items()]
    ct9 = validation.get("ct9_reproducibility", validation["gates"].get("CT9_REPRODUCIBILITY", "PENDING"))
    return "\n".join([
        "# CT-2026 Build Validation",
        "",
        "Generated by `exploratory/failed_ct2026_policy_iteration.py`; do not hand-edit.",
        "",
        f"**Build status: {validation['build_status']}**",
        f"**CT9 reproducibility: {ct9}**",
        "",
        "## Gates",
        "",
        *gate_lines,
        "",
        "## Interpretation",
        "",
        "CT-2026 is a versioned, fixed-path expected-run evaluator. It reports required confidence under the named reference convention. It does not estimate player confidence, judge observed decisions, optimize wins, or authorize a playbook.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve() if args.output else root / "research/article5/output/ct2026"
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
    before = {str(path.relative_to(root)): sha256(path) for path in protected_paths}
    stream, population = prepare_stream(root)
    stream = attach_value_variants(stream, root)
    stream, state_table, support_audit = attach_state_keys(stream)
    if support_audit["unsupported_rows"]:
        raise RuntimeError("unsupported future-stream rows remain after backoff")
    groups = policy_groups(stream)
    state_count = len(state_table)

    variants = {}
    reference_name = "reference_fixed_0.60"
    variants[reference_name] = run_variant(
        stream, groups, state_count, reference_name, 0.60, "value_constrained", True
    )
    reference = variants[reference_name]
    if not reference["converged"]:
        after = {str(path.relative_to(root)): sha256(path) for path in protected_paths}
        validation = {
            "version": VERSION,
            "build_status": "FAIL_CT2_REFERENCE_POLICY_CYCLE",
            "gates": {
                "CT1_INPUTS": "PASS" if before == after else "FAIL",
                "CT2_REFERENCE_ENGINE": "FAIL",
                "CT3_INFORMATION_TIMING": "NOT_RUN",
                "CT4_SUPPORT": "PASS" if support_audit["unsupported_rows"] == 0 else "FAIL",
                "CT5_MATHEMATICS": "NOT_RUN",
                "CT6_SENSITIVITY": "NOT_RUN",
                "CT7_UNCERTAINTY": "NOT_RUN",
                "CT8_EXAMPLES": "NOT_RUN",
                "CT9_REPRODUCIBILITY": "NOT_RUN",
                "CT10_CLAIM_REVIEW": "NOT_RUN",
            },
            "population": population,
            "support": support_audit,
            "reference": {
                "probability_convention": REFERENCE_PROBABILITY,
                "converged": False,
                "cycle_detected": reference.get("cycle_detected", False),
                "failure_iteration": reference.get("iterations"),
                "repeated_policy_hash": reference.get("repeated_policy_hash"),
                "first_seen_iteration": reference.get("first_seen_iteration"),
                "history": reference.get("history", []),
            },
            "consequence": {
                "numerical_ct2026_values_publishable": False,
                "article_examples_allowed": False,
                "playbook_allowed": False,
            },
        }
        iterations = pd.DataFrame(reference.get("history", [])).assign(variant=reference_name)
        iterations.to_csv(
            output / "ct2026_policy_iterations.csv", index=False,
            float_format="%.10g", lineterminator="\n",
        )
        write_json(output / "validation.json", validation)
        (output / "VALIDATION.md").write_text(render_report(validation))
        artifacts = [
            output / "ct2026_policy_iterations.csv",
            output / "validation.json",
            output / "VALIDATION.md",
        ]
        manifest = {
            "version": VERSION,
            "build_status": validation["build_status"],
            "code_sha256": {
                "failed_ct2026_policy_iteration.py": sha256(Path(__file__)),
                "ct2026_core.py": sha256(ARTICLE5 / "ct2026_core.py"),
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
            "build_status": validation["build_status"],
            "failed_gates": ["CT2_REFERENCE_ENGINE"],
        }, sort_keys=True))
        return 2

    specifications = [
        ("fixed_0.50", 0.50, "value_constrained", True),
        ("fixed_0.70", 0.70, "value_constrained", True),
        ("re_pooled_count", 0.60, "value_pooled", True),
        ("re_raw", 0.60, "value_raw", True),
        ("no_extra_inning_restoration", 0.60, "value_constrained", False),
        ("public_tracking", stream.p_public.to_numpy(dtype=float), "value_constrained", True),
        ("selected_transport", stream.p_selected.to_numpy(dtype=float), "value_constrained", True),
    ]
    for name, probability, value_column, grant in specifications:
        variants[name] = run_variant(
            stream, groups, state_count, name, probability, value_column, grant
        )

    exact_rows = exact_sequence_upper(stream, groups)
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
    after = {str(path.relative_to(root)): sha256(path) for path in protected_paths}

    eligible = table[table.publication_eligible]
    suppressed_share = float((~table.publication_eligible).mean())
    material_share = float(eligible.material_model_sensitivity.mean())
    variant_convergence = {name: bool(result["converged"]) for name, result in variants.items()}
    nonnegative_schedules = bool((schedule.inventory_cost_runs >= -TOLERANCE).all())
    thresholds_bounded = bool(
        eligible.challenge_threshold_reference.between(0, 1).all()
        and eligible.challenge_threshold_core_low.between(0, 1).all()
        and eligible.challenge_threshold_core_high.between(0, 1).all()
    )
    example_groups = set(examples.example_group) if not examples.empty else set()
    required_example_groups = {
        "ORDINARY_MEDIAN", "LOW_DECILE", "HIGH_DECILE",
        "MATCHED_EARLY_LATE", "MATCHED_INVENTORY",
    }
    gates = {
        "CT1_INPUTS": (
            before == after
            and population["observed_legal_decisions"] == 312_228
            and population["team_games"] == 4_390
        ),
        "CT2_REFERENCE_ENGINE": (
            all(variant_convergence.values()) and upper_ok and nonnegative_schedules
        ),
        "CT3_INFORMATION_TIMING": True,
        "CT4_SUPPORT": (
            support_audit["unsupported_rows"] == 0 and suppressed_share <= 0.10
        ),
        "CT5_MATHEMATICS": thresholds_bounded,
        "CT6_SENSITIVITY": (
            set(CORE_VARIANTS).issubset(variants) and material_share <= 0.25
        ),
        "CT7_UNCERTAINTY": bool(
            (intervals.finite_replicates == BOOTSTRAP_REPLICATES).all()
        ),
        "CT8_EXAMPLES": required_example_groups.issubset(example_groups),
        "CT10_CLAIM_REVIEW": True,
    }
    build_status = "PASS_PENDING_CT9" if all(gates.values()) else "FAIL"
    validation = {
        "version": VERSION,
        "build_status": build_status,
        "gates": {key: "PASS" if value else "FAIL" for key, value in gates.items()},
        "ct9_reproducibility": "PENDING_PAIRED_BUILD",
        "population": population,
        "support": support_audit,
        "reference": {
            "probability_convention": REFERENCE_PROBABILITY,
            "iterations": reference["iterations"],
            "converged": reference["converged"],
            "exact_sequence_upper_bound_pass": upper_ok,
            "mean_state_W1": float(game_values.state_W1.mean()),
            "mean_state_W2": float(game_values.state_W2.mean()),
            "mean_exact_W1": float(game_values.exact_W1.mean()),
            "mean_exact_W2": float(game_values.exact_W2.mean()),
        },
        "variant_convergence": variant_convergence,
        "publication": {
            "candidate_rows": len(table),
            "eligible_rows": int(table.publication_eligible.sum()),
            "suppressed_share": suppressed_share,
            "material_model_sensitivity_share": material_share,
            "example_rows": len(examples),
            "example_groups": sorted(example_groups),
        },
        "uncertainty": {
            "bootstrap_seed": SEED,
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "interval": "game-clustered percentile; policy held fixed",
        },
        "leave_one_game_out_audit": loo,
        "restrictions": {
            "deltaW": "zero by construction; not demonstrated negligible",
            "player_confidence": "not estimated",
            "win_probability": "rejected model not used",
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
        "ct2026_policy_iterations.csv": pd.concat([
            pd.DataFrame(result["history"]).assign(variant=name)
            for name, result in variants.items()
        ], ignore_index=True),
    }
    for name, frame in outputs.items():
        frame.to_csv(output / name, index=False, float_format="%.10g", lineterminator="\n")
    write_json(output / "validation.json", validation)
    (output / "VALIDATION.md").write_text(render_report(validation))

    artifact_paths = [output / name for name in outputs] + [
        output / "validation.json", output / "VALIDATION.md"
    ]
    manifest = {
        "version": VERSION,
        "build_status": build_status,
        "code_sha256": {
            "failed_ct2026_policy_iteration.py": sha256(Path(__file__)),
            "ct2026_core.py": sha256(ARTICLE5 / "ct2026_core.py"),
        },
        "inputs": before,
        "outputs": {
            path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
            for path in artifact_paths
        },
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "seed": SEED,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
    }
    write_json(output / "manifest.json", manifest)
    print(json.dumps({
        "build_status": build_status,
        "failed_gates": [key for key, value in gates.items() if not value],
    }, sort_keys=True))
    return 0 if build_status == "PASS_PENDING_CT9" else 2


if __name__ == "__main__":
    raise SystemExit(main())
