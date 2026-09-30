"""Frozen CTS9 uncertainty and CTS10 reproducibility primitives for CT-S1."""
from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd

from ct2026_core import challenge_threshold
from reproducibility_core import compare_inventories, file_inventory, sha256


BOOTSTRAP_SEED = 20260926
BOOTSTRAP_REPLICATES = 2_000
INTERVAL_QUANTILES = (0.025, 0.975)
FORBIDDEN_RUNTIME_KEYS = frozenset({
    "created_at",
    "generated_at",
    "run_at",
    "runtime_timestamp",
    "timestamp",
})


def _require_columns(frame: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")


def clustered_reference_intervals(
    source: pd.DataFrame,
    targets: pd.DataFrame,
    *,
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
) -> pd.DataFrame:
    """Bootstrap games while holding the named reference convention fixed.

    ``source`` contains evaluated row costs.  The function does not refit or
    select a future-use policy inside a replicate.  This is therefore a
    conditional finite-game-sample interval, not model spread.
    """
    _require_columns(
        source,
        ["game_pk", "state_key", "cost_inventory_1", "cost_inventory_2"],
    )
    _require_columns(
        targets,
        ["scenario_id", "state_key", "inventory", "correction_value"],
    )
    if replicates <= 0:
        raise ValueError("replicates must be positive")
    if targets.scenario_id.duplicated().any():
        raise ValueError("scenario_id must be unique")
    if not targets.inventory.isin([1, 2]).all():
        raise ValueError("inventory must be 1 or 2")
    numeric_costs = source[["cost_inventory_1", "cost_inventory_2"]].apply(
        pd.to_numeric, errors="raise"
    )
    if not np.isfinite(numeric_costs.to_numpy()).all():
        raise ValueError("source costs must be finite")
    if (numeric_costs.to_numpy() < 0).any():
        raise ValueError("source costs must be nonnegative")
    values = pd.to_numeric(targets.correction_value, errors="raise").to_numpy()
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("correction values must be finite and nonnegative")

    target_states = sorted(targets.state_key.astype(str).unique())
    state_codes = {state: index for index, state in enumerate(target_states)}
    relevant = source.loc[source.state_key.astype(str).isin(target_states)].copy()
    relevant["state_code"] = relevant.state_key.astype(str).map(state_codes)
    games = np.sort(source.game_pk.unique())
    if len(games) == 0:
        raise ValueError("source must contain at least one game")
    game_codes = {game: index for index, game in enumerate(games)}

    grouped = relevant.groupby(["game_pk", "state_code"], sort=True).agg(
        rows=("state_key", "size"),
        sum_1=("cost_inventory_1", "sum"),
        sum_2=("cost_inventory_2", "sum"),
    ).reset_index()
    grouped_games = grouped.game_pk.map(game_codes).to_numpy(dtype=int)
    grouped_states = grouped.state_code.to_numpy(dtype=int)
    grouped_rows = grouped.rows.to_numpy(dtype=float)
    grouped_sums = {
        1: grouped.sum_1.to_numpy(dtype=float),
        2: grouped.sum_2.to_numpy(dtype=float),
    }

    rng = np.random.default_rng(seed)
    draws = np.full((2, replicates, len(target_states)), np.nan, dtype=float)
    for replicate in range(replicates):
        sampled_games = rng.integers(0, len(games), size=len(games))
        game_weights = np.bincount(sampled_games, minlength=len(games)).astype(float)
        group_weights = game_weights[grouped_games]
        denominators = np.bincount(
            grouped_states,
            weights=grouped_rows * group_weights,
            minlength=len(target_states),
        )
        for inventory in (1, 2):
            numerators = np.bincount(
                grouped_states,
                weights=grouped_sums[inventory] * group_weights,
                minlength=len(target_states),
            )
            np.divide(
                numerators,
                denominators,
                out=draws[inventory - 1, replicate],
                where=denominators > 0,
            )

    records = []
    for target in targets.sort_values("scenario_id", kind="stable").itertuples(index=False):
        code = state_codes[str(target.state_key)]
        inventory = int(target.inventory)
        sampled_costs = draws[inventory - 1, :, code]
        finite = sampled_costs[np.isfinite(sampled_costs)]
        interval_complete = len(finite) == replicates
        low_cost = (
            float(np.quantile(finite, INTERVAL_QUANTILES[0]))
            if interval_complete else np.nan
        )
        high_cost = (
            float(np.quantile(finite, INTERVAL_QUANTILES[1]))
            if interval_complete else np.nan
        )
        if interval_complete:
            threshold_bounds = challenge_threshold(
                [float(target.correction_value), float(target.correction_value)],
                [low_cost, high_cost],
            )
            low_ct, high_ct = map(float, threshold_bounds)
        else:
            low_ct = high_ct = np.nan
        records.append({
            "scenario_id": target.scenario_id,
            "state_key": target.state_key,
            "inventory": inventory,
            "bootstrap_seed": seed,
            "bootstrap_replicates": replicates,
            "finite_replicates": int(len(finite)),
            "sampling_cost_low_95": low_cost,
            "sampling_cost_high_95": high_cost,
            "sampling_ct_low_95": low_ct,
            "sampling_ct_high_95": high_ct,
            "sampling_interval_complete": bool(interval_complete),
        })
    return pd.DataFrame.from_records(records)


def validate_uncertainty_output(
    intervals: pd.DataFrame,
    *,
    expected_replicates: int = BOOTSTRAP_REPLICATES,
    expected_seed: int = BOOTSTRAP_SEED,
) -> dict:
    _require_columns(
        intervals,
        [
            "bootstrap_seed",
            "bootstrap_replicates",
            "finite_replicates",
            "sampling_ct_low_95",
            "sampling_ct_high_95",
            "sampling_interval_complete",
        ],
    )
    conditions = {
        "rows_present": bool(len(intervals)),
        "seed_frozen": bool(intervals.bootstrap_seed.eq(expected_seed).all()),
        "replicate_count_frozen": bool(
            intervals.bootstrap_replicates.eq(expected_replicates).all()
        ),
        "all_replicates_finite": bool(
            intervals.finite_replicates.eq(expected_replicates).all()
            and intervals.sampling_interval_complete.astype(bool).all()
        ),
        "ordered_bounds": bool(
            intervals.sampling_ct_low_95.le(intervals.sampling_ct_high_95).all()
        ),
        "sampling_names_separate_from_model_spread": not any(
            column.startswith("model_spread_") for column in intervals.columns
        ),
    }
    return {"conditions": conditions, "pass_cts9": bool(all(conditions.values()))}


def protected_hashes(paths: Iterable[Path], root: Path) -> dict[str, str]:
    root = root.resolve()
    inventory = {}
    for raw_path in paths:
        path = raw_path.resolve()
        if not path.is_file():
            raise ValueError(f"protected input missing: {path}")
        try:
            relative = path.relative_to(root)
        except ValueError as error:
            raise ValueError(f"protected input outside root: {path}") from error
        inventory[str(relative)] = sha256(path)
    return dict(sorted(inventory.items()))


def assert_protected_unchanged(before: dict[str, str], after: dict[str, str]) -> None:
    if before != after:
        changed = sorted(
            path for path in set(before) | set(after) if before.get(path) != after.get(path)
        )
        raise RuntimeError(f"protected inputs changed: {changed}")


def reject_runtime_metadata(value, path: str = "$") -> None:
    """Reject nondeterministic wall-clock fields from generated JSON objects."""
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_RUNTIME_KEYS:
                raise ValueError(f"runtime metadata is forbidden at {path}.{key}")
            reject_runtime_metadata(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_runtime_metadata(child, f"{path}[{index}]")


def validate_json_files_have_no_runtime_metadata(root: Path) -> list[str]:
    checked = []
    for path in sorted(root.rglob("*.json")):
        reject_runtime_metadata(json.loads(path.read_text()))
        checked.append(str(path.relative_to(root)))
    return checked


def compare_clean_builds(run_a: Path, run_b: Path) -> dict:
    """Require identical file sets and bytes, with no exclusions."""
    first = file_inventory(run_a)
    second = file_inventory(run_b)
    rows = compare_inventories(first, second)
    differences = [row for row in rows if not row["byte_identical"]]
    return {
        "files_compared": len(rows),
        "relative_file_sets_match": set(first) == set(second),
        "all_files_byte_identical": not differences,
        "differences": differences,
        "pass_cts10_pair_comparison": bool(set(first) == set(second) and not differences),
    }
