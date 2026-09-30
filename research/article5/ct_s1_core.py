"""Frozen, data-agnostic validation primitives for CT-S1.

This module deliberately accepts prepared tables.  It does not fetch data,
fit a probability model, or choose article examples.  That separation lets us
test and freeze the CTS3--CTS8 rules before opening the confirmation sample.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np
import pandas as pd

from ct2026_core import challenge_threshold


VERSION = "ct-s1.0-candidate"
REFERENCE_VARIANT = "reference_fixed_0.60"
CORE_VARIANTS = (
    REFERENCE_VARIANT,
    "fixed_0.50",
    "fixed_0.70",
    "cutoff_0.00",
    "cutoff_0.10",
    "re_pooled_count",
    "re_raw",
    "no_extra_inning_restoration",
)
DIAGNOSTIC_VARIANTS = ("public_tracking", "selected_transport")
DEVELOPMENT_MIN_ROWS = 200
DEVELOPMENT_MIN_GAMES = 100
CONFIRMATION_MIN_ROWS = 50
CONFIRMATION_MIN_GAMES = 25
MATERIAL_SPREAD = 0.10

STATE_LEVELS = (
    ("L0_EXACT", ("inning_exact", "half_inning", "outs", "team_role", "score_bucket")),
    ("L1_NO_SCORE", ("inning_exact", "half_inning", "outs", "team_role")),
    ("L2_NO_ROLE", ("inning_exact", "half_inning", "outs")),
    ("L3_INNING_BUCKET", ("inning_bucket", "half_inning", "outs")),
    ("L4_NO_HALF", ("inning_bucket", "outs")),
)

FORBIDDEN_EXACT_FIELDS = frozenset({
    "actual_correctness",
    "challenge_result",
    "decision_sequence",
    "is_overturned",
    "observed_success",
    "pitch_number",
    "realized_runs",
    "future_option_value",
})
FORBIDDEN_FIELD_FRAGMENTS = (
    "future_",
    "next_",
    "result",
    "overturn",
    "correctness",
    "realized_",
)


def _require_columns(frame: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")


def validate_information_fields(fields: Iterable[str]) -> tuple[str, ...]:
    """Reject hindsight and exact-future fields from actions/public state keys."""
    normalized = tuple(str(field) for field in fields)
    forbidden = sorted({
        field
        for field in normalized
        if field.lower() in FORBIDDEN_EXACT_FIELDS
        or any(fragment in field.lower() for fragment in FORBIDDEN_FIELD_FRAGMENTS)
    })
    if forbidden:
        raise ValueError(f"decision-time information violation: {forbidden}")
    return normalized


def validate_team_game_order(
    frame: pd.DataFrame,
    *,
    group_columns: Sequence[str] = ("game_pk", "team_id"),
    order_column: str = "decision_sequence",
) -> None:
    """Reject shuffled, duplicated, or gapped decision sequences."""
    _require_columns(frame, [*group_columns, order_column])
    for group_key, group in frame.groupby(list(group_columns), sort=False):
        observed = group[order_column].to_numpy()
        expected = np.arange(len(group), dtype=observed.dtype)
        if not np.array_equal(observed, expected):
            raise ValueError(f"non-canonical row order for team-game {group_key}")


def attach_state_dimensions(frame: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        frame,
        ["inning", "half_inning", "outs", "team_role", "team_score_diff"],
    )
    result = frame.copy()
    inning = pd.to_numeric(result["inning"], errors="raise")
    score = pd.to_numeric(result["team_score_diff"], errors="raise")
    result["inning_exact"] = np.where(inning.le(9), inning.astype(int).astype(str), "10+")
    result["inning_bucket"] = pd.cut(
        inning,
        bins=[0, 3, 6, 9, np.inf],
        labels=["1-3", "4-6", "7-9", "10+"],
    ).astype(str)
    result["score_bucket"] = np.select(
        [score.le(-2), score.eq(-1), score.eq(0), score.eq(1), score.ge(2)],
        ["TRAIL_2PLUS", "TRAIL_1", "TIED", "LEAD_1", "LEAD_2PLUS"],
        default="INVALID",
    )
    if result["score_bucket"].eq("INVALID").any():
        raise ValueError("invalid team score difference")
    return result


def state_key(frame: pd.DataFrame, level: str) -> pd.Series:
    definitions = dict(STATE_LEVELS)
    if level not in definitions:
        raise ValueError(f"unknown support level: {level}")
    _require_columns(frame, definitions[level])
    key = pd.Series(level, index=frame.index, dtype="object")
    for column in definitions[level]:
        key = key.str.cat(frame[column].astype(str), sep="|")
    return key


def summarize_support_schedule(
    rows: pd.DataFrame,
    *,
    period: str,
    min_rows: int,
    min_games: int,
    cost_columns: Sequence[str] = ("cost_inventory_1", "cost_inventory_2"),
) -> pd.DataFrame:
    """Summarize every eligible hierarchy level, not only the finest one.

    Keeping all eligible levels is necessary because cross-period comparison
    must map both periods to their finest *common* supported level.
    """
    if min_rows <= 0 or min_games <= 0:
        raise ValueError("support minima must be positive")
    frame = attach_state_dimensions(rows)
    _require_columns(frame, ["game_pk", *cost_columns])
    pieces = []
    for rank, (level, _) in enumerate(STATE_LEVELS):
        working = frame.assign(state_key=state_key(frame, level))
        aggregations = {
            "support_rows": ("game_pk", "size"),
            "support_games": ("game_pk", "nunique"),
        }
        aggregations.update({column: (column, "mean") for column in cost_columns})
        summary = working.groupby("state_key", sort=True).agg(**aggregations).reset_index()
        summary = summary.loc[
            summary.support_rows.ge(min_rows) & summary.support_games.ge(min_games)
        ].copy()
        summary.insert(0, "period", period)
        summary.insert(1, "support_level", level)
        summary.insert(2, "support_rank", rank)
        pieces.append(summary)
    if not pieces:
        return pd.DataFrame()
    return pd.concat(pieces, ignore_index=True).sort_values(
        ["support_rank", "state_key"], kind="stable"
    ).reset_index(drop=True)


def harmonize_scenarios(
    development: pd.DataFrame,
    confirmation: pd.DataFrame,
    development_schedule: pd.DataFrame,
    confirmation_schedule: pd.DataFrame,
) -> pd.DataFrame:
    """Map matched scenarios to the finest hierarchy level supported by both."""
    required = ["scenario_id", "inventory", "correction_value"]
    _require_columns(development, required)
    _require_columns(confirmation, required)
    development = attach_state_dimensions(development)
    confirmation = attach_state_dimensions(confirmation)
    if development["scenario_id"].duplicated().any() or confirmation["scenario_id"].duplicated().any():
        raise ValueError("scenario_id must be unique within each period")
    dev_keys = {
        level: dict(zip(development.scenario_id, state_key(development, level)))
        for level, _ in STATE_LEVELS
    }
    conf_keys = {
        level: dict(zip(confirmation.scenario_id, state_key(confirmation, level)))
        for level, _ in STATE_LEVELS
    }
    # Confirmation is the controlling CTS5 denominator.  A confirmation
    # scenario with no development match must survive as unsupported rather
    # than disappearing in an inner join.
    paired = confirmation.merge(
        development,
        on="scenario_id",
        how="left",
        suffixes=("_confirmation", "_development"),
        validate="one_to_one",
        indicator="merge_status",
    )
    dev_lookup = development_schedule.set_index(["support_level", "state_key"])
    conf_lookup = confirmation_schedule.set_index(["support_level", "state_key"])
    records = []

    def threshold_or_nan(value: float, cost: float) -> float:
        # Raw run-expectancy sensitivities can assign a negative correction
        # value.  Such a value has no nonnegative break-even Challenge
        # Threshold; retain the row for the exclusion/model-spread audit but
        # do not manufacture a point estimate from it.
        if value < -1e-12:
            return float("nan")
        return float(challenge_threshold([value], [cost])[0])

    for row in paired.itertuples(index=False):
        inventory_conf = int(row.inventory_confirmation)
        if row.merge_status != "both":
            records.append({
                "scenario_id": row.scenario_id,
                "inventory": inventory_conf,
                "supported": False,
                "development_original_level": None,
                "confirmation_original_level": None,
                "exclusion_reason": "NO_DEVELOPMENT_MATCH",
            })
            continue
        inventory_dev = int(row.inventory_development)
        if inventory_dev != inventory_conf or inventory_dev not in (1, 2):
            raise ValueError("matched scenarios must share inventory 1 or 2")
        record = {
            "scenario_id": row.scenario_id,
            "inventory": inventory_dev,
            "supported": False,
            "exclusion_reason": "NO_COMMON_SUPPORTED_LEVEL",
        }
        dev_levels = []
        conf_levels = []
        period_keys = []
        for rank, (level, _) in enumerate(STATE_LEVELS):
            dev_key = dev_keys[level][row.scenario_id]
            conf_key = conf_keys[level][row.scenario_id]
            dev_supported = (level, dev_key) in dev_lookup.index
            conf_supported = (level, conf_key) in conf_lookup.index
            if dev_supported:
                dev_levels.append((rank, level))
            if conf_supported:
                conf_levels.append((rank, level))
            period_keys.append((rank, level, dev_key, conf_key, dev_supported, conf_supported))
        record["development_original_level"] = dev_levels[0][1] if dev_levels else None
        record["confirmation_original_level"] = conf_levels[0][1] if conf_levels else None
        for rank, level, dev_key, conf_key, dev_supported, conf_supported in period_keys:
            if not dev_supported or not conf_supported:
                continue
            cost_column = f"cost_inventory_{inventory_dev}"
            dev_support = dev_lookup.loc[(level, dev_key)]
            conf_support = conf_lookup.loc[(level, conf_key)]
            dev_value = float(row.correction_value_development)
            conf_value = float(row.correction_value_confirmation)
            dev_cost = float(dev_support[cost_column])
            conf_cost = float(conf_support[cost_column])
            record.update({
                "supported": True,
                "harmonized_level": level,
                "harmonized_rank": rank,
                "development_state_key": dev_key,
                "confirmation_state_key": conf_key,
                "development_support_rows": int(dev_support.support_rows),
                "development_support_games": int(dev_support.support_games),
                "confirmation_support_rows": int(conf_support.support_rows),
                "confirmation_support_games": int(conf_support.support_games),
                "development_cost": dev_cost,
                "confirmation_cost": conf_cost,
                "development_ct": threshold_or_nan(dev_value, dev_cost),
                "confirmation_ct": threshold_or_nan(conf_value, conf_cost),
                "exclusion_reason": None,
            })
            break
        records.append(record)
    return pd.DataFrame.from_records(records).sort_values("scenario_id", kind="stable").reset_index(drop=True)


def _average_ranks(values: np.ndarray) -> np.ndarray:
    return pd.Series(values).rank(method="average").to_numpy(dtype=float)


def temporal_stability(matched: pd.DataFrame) -> dict:
    """Calculate the frozen, unweighted CTS6 statistics and decision."""
    _require_columns(matched, ["supported", "development_ct", "confirmation_ct"])
    supported = matched.loc[matched.supported].copy()
    finite = np.isfinite(supported.development_ct) & np.isfinite(supported.confirmation_ct)
    valid = supported.loc[finite]
    if len(valid) < 2:
        raise ValueError("at least two finite matched supported rows are required")
    drift = np.abs(valid.confirmation_ct.to_numpy() - valid.development_ct.to_numpy())
    dev_rank = _average_ranks(valid.development_ct.to_numpy())
    conf_rank = _average_ranks(valid.confirmation_ct.to_numpy())
    correlation = float(np.corrcoef(dev_rank, conf_rank)[0, 1])
    median = float(np.median(drift))
    percentile_90 = float(np.quantile(drift, 0.90))
    return {
        "candidate_rows": int(len(matched)),
        "supported_rows": int(matched.supported.sum()),
        "finite_matched_rows": int(len(valid)),
        "support_coverage": float(matched.supported.mean()) if len(matched) else 0.0,
        "median_absolute_drift": median,
        "p90_absolute_drift": percentile_90,
        "maximum_absolute_drift": float(np.max(drift)),
        "spearman_average_rank": correlation,
        "pass_support_coverage": bool(matched.supported.mean() >= 0.90),
        "pass_median_drift": bool(median <= 0.05),
        "pass_p90_drift": bool(percentile_90 <= 0.10),
        "pass_spearman": bool(correlation >= 0.80),
        "pass_cts6": bool(median <= 0.05 and percentile_90 <= 0.10 and correlation >= 0.80),
    }


def attach_model_spread(
    table: pd.DataFrame,
    *,
    core_variants: Sequence[str] = CORE_VARIANTS,
) -> pd.DataFrame:
    """Attach model spread; sampling intervals remain separate input columns."""
    _require_columns(table, core_variants)
    result = table.copy()
    values = result.loc[:, list(core_variants)].apply(pd.to_numeric, errors="coerce")
    complete = values.notna().all(axis=1) & np.isfinite(values).all(axis=1)
    result["model_spread_complete"] = complete
    result["model_spread_low"] = values.min(axis=1, skipna=False)
    result["model_spread_high"] = values.max(axis=1, skipna=False)
    result["model_spread_width"] = result.model_spread_high - result.model_spread_low
    result["model_spread_label"] = np.select(
        [~complete, result.model_spread_width.gt(MATERIAL_SPREAD)],
        ["INCOMPLETE_MODEL_SPREAD", "MATERIAL_MODEL_DISAGREEMENT"],
        default="MODEL_SPREAD_WITHIN_0.10",
    )
    result["unlabeled_point_permitted"] = complete & result.model_spread_width.le(
        MATERIAL_SPREAD
    )
    return result


def validate_public_presentation(table: pd.DataFrame) -> None:
    """Stop unlabeled material or incomplete CT point estimates."""
    required = [
        "reference_ct",
        "model_spread_complete",
        "model_spread_width",
        "model_spread_label",
    ]
    _require_columns(table, required)
    shown = pd.to_numeric(table.reference_ct, errors="coerce").notna()
    incomplete = shown & ~table.model_spread_complete.astype(bool)
    mislabeled_material = (
        shown
        & pd.to_numeric(table.model_spread_width, errors="coerce").gt(MATERIAL_SPREAD)
        & table.model_spread_label.ne("MATERIAL_MODEL_DISAGREEMENT")
    )
    if incomplete.any() or mislabeled_material.any():
        failing = table.index[incomplete | mislabeled_material].tolist()
        raise ValueError(f"unsafe public CT presentation at rows: {failing}")


def audit_contrasts(
    contrasts: pd.DataFrame,
    *,
    reference_variant: str = REFERENCE_VARIANT,
    core_variants: Sequence[str] = CORE_VARIANTS,
) -> pd.DataFrame:
    """Apply CTS7 without selecting or substituting article examples."""
    required = ["contrast_id", "contrast_class", "period", "variant", "member", "ct"]
    _require_columns(contrasts, required)
    if not set(contrasts.member.unique()).issubset({"A", "B"}):
        raise ValueError("contrast members must be A and B")
    expected = {(period, variant, member) for period in ("development", "confirmation") for variant in core_variants for member in ("A", "B")}
    records = []
    for (contrast_id, contrast_class), group in contrasts.groupby(
        ["contrast_id", "contrast_class"], sort=True
    ):
        observed = set(zip(group.period, group.variant, group.member))
        unique_grid = not group.duplicated(["period", "variant", "member"]).any()
        complete = unique_grid and expected.issubset(observed)
        differences = {}
        if complete:
            indexed = group.set_index(["period", "variant", "member"])["ct"]
            for period in ("development", "confirmation"):
                for variant in core_variants:
                    differences[(period, variant)] = float(
                        indexed.loc[(period, variant, "B")] - indexed.loc[(period, variant, "A")]
                    )
        finite = bool(complete and all(np.isfinite(value) for value in differences.values()))
        directions = {int(np.sign(value)) for value in differences.values()} if finite else set()
        direction_stable = finite and len(directions) == 1 and 0 not in directions
        dev_separation = abs(differences.get(("development", reference_variant), np.nan))
        conf_separation = abs(differences.get(("confirmation", reference_variant), np.nan))
        eligible = bool(
            complete
            and finite
            and direction_stable
            and dev_separation >= 0.05
            and conf_separation >= 0.05
        )
        if not complete:
            failure_reason = "INCOMPLETE_OR_DUPLICATE_CORE_GRID"
        elif not finite:
            failure_reason = "NONFINITE_CORE_VALUE"
        elif not direction_stable:
            failure_reason = "DIRECTION_NOT_STABLE"
        elif dev_separation < 0.05:
            failure_reason = "DEVELOPMENT_REFERENCE_SEPARATION_BELOW_0.05"
        elif conf_separation < 0.05:
            failure_reason = "CONFIRMATION_REFERENCE_SEPARATION_BELOW_0.05"
        else:
            failure_reason = None
        records.append({
            "contrast_id": contrast_id,
            "contrast_class": contrast_class,
            "complete_core_grid": complete,
            "finite_core_grid": finite,
            "direction_stable": direction_stable,
            "direction_sign": next(iter(directions)) if direction_stable else 0,
            "development_reference_separation": dev_separation,
            "confirmation_reference_separation": conf_separation,
            "article_eligible": eligible,
            "failure_reason": failure_reason,
        })
    return pd.DataFrame.from_records(records)


def cts7_passes(audit: pd.DataFrame) -> bool:
    """CTS7 requires at least one eligible ordinary contrast."""
    _require_columns(audit, ["contrast_class", "article_eligible"])
    return bool(
        audit.article_eligible.astype(bool)
        .loc[audit.contrast_class.eq("ordinary")]
        .any()
    )
