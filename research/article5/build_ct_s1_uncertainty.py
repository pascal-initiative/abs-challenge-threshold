"""Build deterministic game-clustered CTS9 intervals for CT-S1."""
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

from ct2026_core import challenge_threshold  # noqa: E402
from ct_s1_assurance import (  # noqa: E402
    BOOTSTRAP_REPLICATES,
    BOOTSTRAP_SEED,
    clustered_reference_intervals,
)
from ct_s1_core import (  # noqa: E402
    REFERENCE_VARIANT,
    VERSION,
    attach_state_dimensions,
    state_key,
)


BUILD_VERSION = "ct-s1.0-cts9"
SEED = BOOTSTRAP_SEED
REPLICATES = BOOTSTRAP_REPLICATES
LOWER_QUANTILE = 0.025
UPPER_QUANTILE = 0.975
COST_COLUMNS = {
    1: f"cost_inventory_1__{REFERENCE_VARIANT}",
    2: f"cost_inventory_2__{REFERENCE_VARIANT}",
}


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


def bootstrap_support_costs(
    prepared: pd.DataFrame,
    *,
    period: str,
    required_keys: dict[str, set[str]],
) -> pd.DataFrame:
    """Adapt prepared rows to the pre-confirmation frozen CTS9 primitive."""
    frame = attach_state_dimensions(prepared)
    source_pieces = []
    target_records = []
    for level in sorted(required_keys):
        keys = sorted(required_keys[level])
        keyed = frame.assign(_state_key=state_key(frame, level))
        keyed = keyed.loc[keyed._state_key.isin(keys)].copy()
        keyed["state_key"] = level + "::" + keyed._state_key.astype(str)
        source_pieces.append(keyed.loc[:, ["game_pk", "state_key", *COST_COLUMNS.values()]].rename(
            columns={
                COST_COLUMNS[1]: "cost_inventory_1",
                COST_COLUMNS[2]: "cost_inventory_2",
            }
        ))
        for key in keys:
            for inventory in (1, 2):
                target_records.append({
                    "scenario_id": f"{level}::{key}::inventory={inventory}",
                    "state_key": f"{level}::{key}",
                    "inventory": inventory,
                    # Cost quantiles are independent of correction value.  A
                    # positive dummy value lets the frozen primitive complete
                    # its threshold transform, which this adapter discards.
                    "correction_value": 1.0,
                })
    source = pd.concat(source_pieces, ignore_index=True)
    targets = pd.DataFrame.from_records(target_records)
    intervals = clustered_reference_intervals(
        source,
        targets,
        replicates=REPLICATES,
        seed=SEED,
    )
    point_rows = []
    for inventory in (1, 2):
        point_rows.append(
            source.groupby("state_key", sort=True)[f"cost_inventory_{inventory}"]
            .mean()
            .rename("sampling_cost_point_recomputed")
            .reset_index()
            .assign(inventory=inventory)
        )
    points = pd.concat(point_rows, ignore_index=True)
    result = intervals.merge(
        points, on=["state_key", "inventory"], how="left", validate="one_to_one"
    )
    split = result.state_key.str.split("::", n=1, expand=True)
    result["harmonized_level"] = split[0]
    result["state_key"] = split[1]
    result.insert(0, "period", period)
    return result.rename(columns={
        "finite_replicates": "sampling_finite_replicates",
        "sampling_interval_complete": "sampling_complete",
        "sampling_cost_low_95": "sampling_cost_lower",
        "sampling_cost_high_95": "sampling_cost_upper",
    }).loc[:, [
        "period", "harmonized_level", "state_key", "inventory",
        "sampling_finite_replicates", "sampling_complete",
        "sampling_cost_point_recomputed", "sampling_cost_lower",
        "sampling_cost_upper",
    ]]


def attach_intervals(
    reference: pd.DataFrame,
    candidates: pd.DataFrame,
    support_costs: pd.DataFrame,
    disclosure: pd.DataFrame,
    *,
    period: str,
) -> pd.DataFrame:
    state_column = f"{period}_state_key"
    cost_column = f"{period}_cost"
    ct_column = f"{period}_ct"
    result = reference.loc[:, [
        "scenario_id", "inventory", "supported", "harmonized_level",
        state_column, cost_column, ct_column, "exclusion_reason",
    ]].rename(columns={
        state_column: "state_key",
        cost_column: "reference_cost",
        ct_column: "reference_ct",
    })
    result.insert(0, "period", period)
    result = result.merge(
        candidates.loc[:, ["scenario_id", "value_constrained"]]
        .rename(columns={"value_constrained": "correction_value"}),
        on="scenario_id",
        how="left",
        validate="one_to_one",
    )
    result = result.merge(
        support_costs,
        on=["period", "harmonized_level", "state_key", "inventory"],
        how="left",
        validate="many_to_one",
    )
    complete = result.sampling_complete.eq(True)
    finite_value = np.isfinite(pd.to_numeric(result.correction_value, errors="coerce"))
    valid = complete & finite_value & result.correction_value.ge(0)
    result["sampling_ct_lower"] = np.nan
    result["sampling_ct_upper"] = np.nan
    if valid.any():
        result.loc[valid, "sampling_ct_lower"] = challenge_threshold(
            result.loc[valid, "correction_value"],
            result.loc[valid, "sampling_cost_lower"],
        )
        result.loc[valid, "sampling_ct_upper"] = challenge_threshold(
            result.loc[valid, "correction_value"],
            result.loc[valid, "sampling_cost_upper"],
        )
    result["sampling_interval_width"] = (
        result.sampling_ct_upper - result.sampling_ct_lower
    )
    result["sampling_point_inside_interval"] = (
        result.reference_ct.ge(result.sampling_ct_lower)
        & result.reference_ct.le(result.sampling_ct_upper)
    )
    result["sampling_interval_status"] = np.select(
        [
            ~result.supported.astype(bool),
            result.supported.astype(bool) & ~complete,
            valid,
        ],
        [
            "SUPPRESSED_UNSUPPORTED",
            "SUPPRESSED_INCOMPLETE_REPLICATES",
            "COMPLETE_2000_REPLICATES",
        ],
        default="SUPPRESSED_INVALID_CORRECTION_VALUE",
    )
    model_columns = [
        "period", "scenario_id", "inventory", "model_spread_complete",
        "model_spread_low", "model_spread_high", "model_spread_width",
        "model_spread_label", "permitted_use",
    ]
    result = result.merge(
        disclosure.loc[:, model_columns],
        on=["period", "scenario_id", "inventory"],
        how="left",
        validate="one_to_one",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--cts3", type=Path)
    parser.add_argument("--temporal", type=Path)
    parser.add_argument("--cts7", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    cts3 = (args.cts3 or root / "data/ct_s1/cts3").resolve()
    temporal = (args.temporal or root / "data/ct_s1/temporal").resolve()
    cts7 = (args.cts7 or root / "data/ct_s1/cts7").resolve()
    output = (args.output or root / "data/ct_s1/cts9").resolve()
    if output.exists():
        raise SystemExit(f"output must not already exist: {output}")
    output.mkdir(parents=True)

    required_inputs = [
        cts3 / "development_prepared.csv",
        cts3 / "confirmation_prepared.csv",
        temporal / "development_candidate_states.csv",
        temporal / "confirmation_candidate_states.csv",
        temporal / "matched_reference.csv",
        temporal / "reference_disclosure.csv",
        temporal / "validation.json",
        cts7 / "validation.json",
    ]
    protected_specs = [
        root / "research/article5/CT_S1_CTS4_CTS8_OUTPUTS.sha256",
        root / "research/article5/CT_S1_CTS7_OUTPUTS.sha256",
        root / "research/article5/CT_S1_ASSURANCE_SPEC.md",
        root / "research/article5/CT_SUCCESSOR_VALIDATION_PLAN.md",
    ]
    protected = [*required_inputs, *protected_specs]
    before = {str(path.relative_to(root)): sha256(path) for path in protected}
    accepted_hashes = {}
    for hash_file in protected_specs[:2]:
        accepted_hashes.update(expected_hashes(hash_file))
    prior_hashes_reconcile = all(
        (root / relative).is_file() and sha256(root / relative) == digest
        for relative, digest in accepted_hashes.items()
    )
    temporal_validation = json.loads((temporal / "validation.json").read_text())
    cts7_validation = json.loads((cts7 / "validation.json").read_text())
    if temporal_validation["status"] != "PASS_CTS4_CTS5_CTS6_CTS8":
        raise SystemExit("CTS4--CTS8 predecessor status did not pass")
    if cts7_validation["status"] != "PASS_CTS7_READY_FOR_CTS9":
        raise SystemExit("CTS7 predecessor status did not pass")

    reference = pd.read_csv(temporal / "matched_reference.csv")
    disclosure = pd.read_csv(temporal / "reference_disclosure.csv")
    supported = reference.loc[reference.supported.astype(bool)]
    required_keys = {
        period: {
            level: set(
                supported.loc[supported.harmonized_level.eq(level), f"{period}_state_key"]
            )
            for level in sorted(supported.harmonized_level.dropna().unique())
        }
        for period in ("development", "confirmation")
    }
    prepared = {
        "development": pd.read_csv(cts3 / "development_prepared.csv"),
        "confirmation": pd.read_csv(cts3 / "confirmation_prepared.csv"),
    }
    candidates = {
        "development": pd.read_csv(temporal / "development_candidate_states.csv"),
        "confirmation": pd.read_csv(temporal / "confirmation_candidate_states.csv"),
    }

    support_pieces = []
    period_games = {}
    for period in ("development", "confirmation"):
        games = np.sort(prepared[period].game_pk.unique())
        period_games[period] = int(len(games))
        support_pieces.append(bootstrap_support_costs(
            prepared[period],
            period=period,
            required_keys=required_keys[period],
        ))
    support_costs = pd.concat(support_pieces, ignore_index=True)
    interval_table = pd.concat([
        attach_intervals(
            reference,
            candidates[period],
            support_costs,
            disclosure,
            period=period,
        )
        for period in ("development", "confirmation")
    ], ignore_index=True).sort_values(
        ["period", "scenario_id"], kind="stable"
    ).reset_index(drop=True)

    supported_intervals = interval_table.loc[interval_table.supported.astype(bool)]
    published = interval_table.loc[
        interval_table.sampling_interval_status.eq("COMPLETE_2000_REPLICATES")
    ]
    point_cost_delta = (
        published.sampling_cost_point_recomputed - published.reference_cost
    ).abs()
    partial_interval = (
        interval_table.sampling_ct_lower.notna()
        ^ interval_table.sampling_ct_upper.notna()
    )
    prefix_separation = not any(
        column.startswith("model_spread_") and "sampling" in column
        or column.startswith("sampling_") and "model_spread" in column
        for column in interval_table.columns
    )
    after = {str(path.relative_to(root)): sha256(path) for path in protected}
    conditions = {
        "prior_output_hashes_reconcile": prior_hashes_reconcile,
        "protected_inputs_unchanged": before == after,
        "frozen_seed_used": SEED == 20260926,
        "frozen_replicate_count_used": REPLICATES == 2000,
        "game_cluster_resampling_used": True,
        "reference_point_costs_reconcile": bool(
            len(point_cost_delta) and point_cost_delta.max() <= 1e-10
        ),
        "no_partial_intervals": not bool(partial_interval.any()),
        "all_published_intervals_have_2000_finite_replicates": bool(
            len(published)
            and published.sampling_finite_replicates.eq(REPLICATES).all()
        ),
        "all_supported_rows_receive_complete_interval": bool(
            len(published) == len(supported_intervals)
        ),
        "interval_endpoints_ordered": bool(
            published.sampling_ct_lower.le(published.sampling_ct_upper).all()
        ),
        "sampling_and_model_spread_columns_separate": prefix_separation,
    }
    passed = all(conditions.values())
    status = "PASS_CTS9_READY_FOR_CTS10" if passed else "FAIL_CTS9_NO_PUBLISHED_INTERVALS"

    completeness = (
        interval_table.groupby(
            ["period", "harmonized_level", "inventory", "sampling_interval_status"],
            dropna=False,
        )
        .agg(
            rows=("scenario_id", "size"),
            minimum_finite_replicates=("sampling_finite_replicates", "min"),
            maximum_finite_replicates=("sampling_finite_replicates", "max"),
            median_interval_width=("sampling_interval_width", "median"),
            maximum_interval_width=("sampling_interval_width", "max"),
        )
        .reset_index()
    )
    interval_table.to_csv(
        output / "reference_sampling_intervals.csv",
        index=False,
        float_format="%.12g",
        lineterminator="\n",
    )
    support_costs.to_csv(
        output / "bootstrap_support_costs.csv",
        index=False,
        float_format="%.12g",
        lineterminator="\n",
    )
    completeness.to_csv(
        output / "completeness_audit.csv",
        index=False,
        float_format="%.12g",
        lineterminator="\n",
    )
    validation = {
        "research_identity": "CT-S1",
        "version": BUILD_VERSION,
        "metric_version": VERSION,
        "status": status,
        "conditions": conditions,
        "bootstrap": {
            "cluster_unit": "game_pk",
            "seed": SEED,
            "replicates": REPLICATES,
            "quantiles": [LOWER_QUANTILE, UPPER_QUANTILE],
            "quantile_method": "linear",
            "games": period_games,
            "resampling_implementation": "ct_s1_assurance.clustered_reference_intervals",
        },
        "intervals": {
            "candidate_period_state_rows": int(len(interval_table)),
            "supported_period_state_rows": int(len(supported_intervals)),
            "published_complete_rows": int(len(published)),
            "suppressed_rows": int(len(interval_table) - len(published)),
            "median_width": float(published.sampling_interval_width.median()),
            "p90_width": float(published.sampling_interval_width.quantile(0.90)),
            "maximum_width": float(published.sampling_interval_width.max()),
            "point_inside_interval_rows": int(published.sampling_point_inside_interval.sum()),
            "maximum_point_cost_reconciliation_delta": float(point_cost_delta.max()),
        },
        "restrictions": {
            "conditional_finite_game_sample_interval": True,
            "probability_refit": False,
            "correction_value_refit": False,
            "state_hierarchy_refit": False,
            "future_use_policy_refit": False,
            "model_spread_combined_with_sampling": False,
            "article_claims": False,
            "playbook_allowed": False,
        },
        "next_gate": "CTS10_PAIRED_ISOLATED_BUILDS" if passed else "STOP_INTERVAL_PUBLICATION",
    }
    write_json(output / "validation.json", validation)
    artifacts = sorted(path for path in output.iterdir() if path.is_file())
    manifest = {
        "version": BUILD_VERSION,
        "status": status,
        "code_sha256": {
            "build_ct_s1_uncertainty.py": sha256(Path(__file__)),
            "ct_s1_assurance.py": sha256(HERE / "ct_s1_assurance.py"),
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
        "published_complete_rows": len(published),
        "median_interval_width": validation["intervals"]["median_width"],
        "p90_interval_width": validation["intervals"]["p90_width"],
        "maximum_interval_width": validation["intervals"]["maximum_width"],
    }, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
