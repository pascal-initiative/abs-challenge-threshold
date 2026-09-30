"""Build and validate the ABS-05 constrained correction-value estimator."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy.optimize import Bounds, LinearConstraint, minimize

PRIOR_MASS = 40.0
TOLERANCE = 1e-9
VERSION = "abs_article5_correction_value_v1"


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
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=_json_default) + "\n"
    )


def count_states() -> list[tuple[int, int]]:
    return [(balls, strikes) for balls in range(4) for strikes in range(3)]


def walk_successor(base_state: str) -> tuple[str, int]:
    first, second, third = (int(value) for value in str(base_state))
    runs = int(first and second and third)
    successor = f"1{int(first or second)}{int(third or (first and second))}"
    return successor, runs


def state_keys(base_states: list[str]) -> list[tuple[int, int, int, str]]:
    return [
        (balls, strikes, outs, bases)
        for outs in range(3)
        for bases in sorted(base_states)
        for balls, strikes in count_states()
    ]


def global_constraints(base_states: list[str]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    keys = state_keys(base_states)
    index = {state: i for i, state in enumerate(keys)}
    rows, lower, kinds = [], [], []

    def add(positive, negative=None, offset=0.0, kind=""):
        row = np.zeros(len(keys))
        row[index[positive]] += 1.0
        if negative is not None:
            row[index[negative]] -= 1.0
        rows.append(row)
        lower.append(float(offset))
        kinds.append(kind)

    for outs in range(3):
        for bases in sorted(base_states):
            for balls in range(3):
                for strikes in range(3):
                    add(
                        (balls + 1, strikes, outs, bases),
                        (balls, strikes, outs, bases),
                        kind="WITHIN_EXTRA_BALL",
                    )
            for balls in range(4):
                for strikes in range(2):
                    add(
                        (balls, strikes, outs, bases),
                        (balls, strikes + 1, outs, bases),
                        kind="WITHIN_EXTRA_STRIKE",
                    )

            walk_bases, walk_runs = walk_successor(bases)
            walk_state = (0, 0, outs, walk_bases)
            strikeout_state = None if outs == 2 else (0, 0, outs + 1, bases)
            for strikes in range(2):
                add(
                    walk_state,
                    (3, strikes + 1, outs, bases),
                    offset=-walk_runs,
                    kind="TERMINAL_WALK_VS_STRIKE",
                )
            for balls in range(3):
                add(
                    (balls + 1, 2, outs, bases),
                    strikeout_state,
                    kind="TERMINAL_BALL_VS_STRIKEOUT",
                )
            add(
                walk_state,
                strikeout_state,
                offset=-walk_runs,
                kind="TERMINAL_FULL_COUNT",
            )
    return np.vstack(rows), np.asarray(lower), kinds


def build_constrained_table(
    table: pd.DataFrame, prior_mass: float = PRIOR_MASS, uniform_weights: bool = False
) -> tuple[pd.DataFrame, dict]:
    required = {"balls", "strikes", "outs", "base_state", "re_smoothed", "n_pitches"}
    if required - set(table.columns):
        raise RuntimeError(f"RE table missing columns: {sorted(required - set(table.columns))}")
    if len(table) != 288 or table.duplicated(["balls", "strikes", "outs", "base_state"]).any():
        raise RuntimeError("RE table must contain exactly 288 unique states")
    base_states = sorted(table.base_state.astype(str).unique())
    keys = state_keys(base_states)
    ordered = table.set_index(["balls", "strikes", "outs", "base_state"]).loc[keys].reset_index()
    y = ordered.re_smoothed.to_numpy(dtype=float)
    weights = np.ones(len(ordered)) if uniform_weights else ordered.n_pitches.to_numpy(dtype=float) + prior_mass
    if not np.isfinite(y).all() or not np.isfinite(weights).all():
        raise RuntimeError("nonfinite input to global count projection")
    scaled_weights = weights / weights.mean()
    matrix, lower, kinds = global_constraints(base_states)

    def objective(values):
        return float(np.sum(scaled_weights * np.square(values - y)))

    def gradient(values):
        return 2.0 * scaled_weights * (values - y)

    solved = minimize(
        objective,
        y.copy(),
        jac=gradient,
        method="SLSQP",
        bounds=Bounds(np.zeros(len(y)), np.full(len(y), np.inf)),
        constraints=[LinearConstraint(matrix, lower, np.full(len(lower), np.inf))],
        options={"ftol": 1e-12, "maxiter": 2000, "disp": False},
    )
    if not solved.success:
        raise RuntimeError(f"global count projection failed: {solved.message}")
    margins = matrix @ solved.x - lower
    if float(margins.min()) < -TOLERANCE:
        raise RuntimeError(f"global projection violates constraint: {margins.min()}")
    ordered["re_constrained"] = solved.x
    ordered["projection_delta"] = solved.x - y
    ordered["effective_weight"] = weights
    ordered["solver_objective"] = objective(solved.x)
    result = ordered
    columns = [
        "balls", "strikes", "outs", "base_state", "raw_mean", "n_pitches",
        "base_out_mean", "re_smoothed", "effective_weight", "re_constrained",
        "projection_delta", "solver_objective",
    ]
    diagnostics = {
        "solver_success": bool(solved.success),
        "solver_status": int(solved.status),
        "solver_message": str(solved.message),
        "solver_iterations": int(solved.nit),
        "objective": objective(solved.x),
        "constraints": len(lower),
        "minimum_margin": float(margins.min()),
        "binding_by_type": {
            kind: int(sum(margin <= TOLERANCE for margin, label in zip(margins, kinds) if label == kind))
            for kind in sorted(set(kinds))
        },
        "constraints_by_type": {kind: kinds.count(kind) for kind in sorted(set(kinds))},
    }
    result = result[columns].sort_values(["outs", "base_state", "balls", "strikes"]).reset_index(drop=True)
    return result, diagnostics


def lookup_from_table(table: pd.DataFrame) -> dict[tuple[int, int, int, str], float]:
    return {
        (int(row.balls), int(row.strikes), int(row.outs), str(row.base_state)): float(row.re_constrained)
        for row in table.itertuples(index=False)
    }


def state_value(record, prefix: str, lookup: dict) -> float:
    if not bool(getattr(record, f"{prefix}_state_valid")):
        return np.nan
    runs = float(getattr(record, f"{prefix}_runs"))
    if bool(getattr(record, f"{prefix}_inning_ended")) or bool(getattr(record, f"{prefix}_walkoff")):
        return runs
    key = (
        int(getattr(record, f"{prefix}_balls")),
        int(getattr(record, f"{prefix}_strikes")),
        int(getattr(record, f"{prefix}_outs")),
        str(getattr(record, f"{prefix}_base_state")),
    )
    return runs + lookup.get(key, np.nan)


def alternative_state_value(state: dict, lookup: dict) -> float:
    runs = float(state["runs"])
    if bool(state["inning_ended"]):
        return runs
    key = (int(state["balls"]), int(state["strikes"]), int(state["outs"]), str(state["bases"]))
    return runs + lookup.get(key, np.nan)


def _json_mapping(value) -> dict:
    if not isinstance(value, str) or not value.strip():
        return {}
    parsed = json.loads(value)
    return parsed if isinstance(parsed, dict) else {}


def correction_value(observed: float, corrected: float, side: str) -> float:
    return corrected - observed if side == "OFFENSE" else observed - corrected


def value_incorrect_calls(frame: pd.DataFrame, lookup: dict) -> pd.DataFrame:
    rows = []
    for record in frame.itertuples(index=False):
        observed = state_value(record, "obs", lookup)
        corrected = state_value(record, "cor", lookup)
        alternatives = _json_mapping(record.alternative_states)
        observed_old_alts = _json_mapping(record.RE_observed_alternatives)
        corrected_old_alts = _json_mapping(record.RE_corrected_alternatives)
        observed_values = [observed]
        corrected_values = [corrected]
        if alternatives and observed_old_alts:
            observed_values = [alternative_state_value(state, lookup) for state in alternatives.values()]
        if alternatives and corrected_old_alts:
            corrected_values = [alternative_state_value(state, lookup) for state in alternatives.values()]
        values = [
            correction_value(obs, cor, record.opportunity_side)
            for obs, cor in product(observed_values, corrected_values)
            if np.isfinite(obs) and np.isfinite(cor)
        ]
        ambiguous = record.cf_confidence == "AMBIGUOUS"
        value_status = (
            "AMBIGUOUS_STRUCTURALLY_UNVALUED" if ambiguous and not values
            else "AMBIGUOUS_BOUNDED" if ambiguous
            else "VALUED"
        )
        rows.append({
            "pitch_key": record.pitch_key,
            "game_date": record.game_date,
            "opportunity_side": record.opportunity_side,
            "eligibility_status": record.eligibility_status,
            "count": record.count,
            "outs": int(record.outs),
            "base_state": str(record.base_state),
            "cf_rule": record.cf_rule,
            "cf_confidence": record.cf_confidence,
            "value_status": value_status,
            "re_observed_constrained": np.nan if ambiguous else observed,
            "re_corrected_constrained": np.nan if ambiguous else corrected,
            "correction_value_runs_constrained": np.nan if ambiguous else correction_value(observed, corrected, record.opportunity_side),
            "correction_value_runs_lower_constrained": min(values) if values else np.nan,
            "correction_value_runs_upper_constrained": max(values) if values else np.nan,
            "correction_value_runs_article4": record.correction_value_runs,
            "correction_value_runs_pooled": record.correction_value_runs_pooled,
            "correction_value_runs_lomo": record.correction_value_runs_lomo,
        })
    return pd.DataFrame(rows).sort_values("pitch_key").reset_index(drop=True)


def ordering_diagnostics(table: pd.DataFrame, column: str) -> dict:
    lookup = {
        (int(row.balls), int(row.strikes), int(row.outs), str(row.base_state)): float(getattr(row, column))
        for row in table.itertuples(index=False)
    }
    deltas = []
    for outs in range(3):
        for bases in sorted(table.base_state.unique()):
            for balls in range(3):
                for strikes in range(3):
                    deltas.append(("ball", lookup[(balls + 1, strikes, outs, bases)] - lookup[(balls, strikes, outs, bases)]))
            for balls in range(4):
                for strikes in range(2):
                    deltas.append(("strike", lookup[(balls, strikes, outs, bases)] - lookup[(balls, strikes + 1, outs, bases)]))
    return {
        "comparisons": len(deltas),
        "violations": int(sum(delta < -TOLERANCE for _, delta in deltas)),
        "minimum_constraint_margin": float(min(delta for _, delta in deltas)),
    }


def full_constraint_diagnostics(table: pd.DataFrame, column: str) -> dict:
    base_states = sorted(table.base_state.astype(str).unique())
    keys = state_keys(base_states)
    values = (
        table.set_index(["balls", "strikes", "outs", "base_state"])
        .loc[keys, column]
        .to_numpy(dtype=float)
    )
    matrix, lower, kinds = global_constraints(base_states)
    margins = matrix @ values - lower
    return {
        "comparisons": len(margins),
        "violations": int((margins < -TOLERANCE).sum()),
        "minimum_constraint_margin": float(margins.min()),
        "violations_by_type": {
            kind: int(sum(margin < -TOLERANCE for margin, label in zip(margins, kinds) if label == kind))
            for kind in sorted(set(kinds))
        },
    }


def sensitivity_diagnostics(values: pd.DataFrame) -> dict:
    eligible = values[
        values.eligibility_status.eq("ELIGIBLE") & values.cf_confidence.ne("AMBIGUOUS")
    ].copy()
    primary = eligible.correction_value_runs_constrained
    result = {}
    for label, column in [
        ("article4_unconstrained", "correction_value_runs_article4"),
        ("article4_pooled_count", "correction_value_runs_pooled"),
        ("article4_leave_one_month_out", "correction_value_runs_lomo"),
    ]:
        other = eligible[column]
        finite = primary.notna() & other.notna()
        delta = primary[finite] - other[finite]
        result[label] = {
            "rows": int(finite.sum()),
            "mean_absolute_difference": float(delta.abs().mean()),
            "maximum_absolute_difference": float(delta.abs().max()),
            "correlation": float(primary[finite].corr(other[finite])),
            "sign_disagreements": int((np.sign(primary[finite]) != np.sign(other[finite])).sum()),
        }
    return result


def canonical_replay_diagnostics(calls: pd.DataFrame) -> dict:
    candidates = calls[
        calls.cf_rule.eq("R1_NO_RUNNER_ACTION") & calls.cf_confidence.eq("EXACT")
    ]
    mismatches = []
    for record in candidates.itertuples(index=False):
        if record.derived_abs_call == "BALL":
            if int(record.balls) < 3:
                expected = (
                    int(record.balls) + 1, int(record.strikes), int(record.outs),
                    str(record.base_state), 0, False,
                )
            else:
                bases, runs = walk_successor(str(record.base_state))
                expected = (0, 0, int(record.outs), bases, runs, False)
        elif int(record.strikes) < 2:
            expected = (
                int(record.balls), int(record.strikes) + 1, int(record.outs),
                str(record.base_state), 0, False,
            )
        elif int(record.outs) < 2:
            expected = (0, 0, int(record.outs) + 1, str(record.base_state), 0, False)
        else:
            expected = (0, 0, 3, "000", 0, True)
        actual = (
            int(record.cor_balls), int(record.cor_strikes), int(record.cor_outs),
            str(record.cor_base_state), int(record.cor_runs), bool(record.cor_inning_ended),
        )
        if actual != expected:
            mismatches.append({
                "pitch_key": record.pitch_key,
                "expected": expected,
                "actual": actual,
            })
    return {
        "canonical_r1_exact_rows": len(candidates),
        "mismatches": len(mismatches),
        "examples": mismatches[:20],
    }


def projection_uncertainty(re_input: pd.DataFrame, constrained: pd.DataFrame) -> dict:
    keys = ["balls", "strikes", "outs", "base_state"]
    merged = constrained.merge(re_input[keys + ["sd"]], on=keys, validate="one_to_one")
    merged["standard_error"] = merged.sd / np.sqrt(merged.n_pitches)
    merged["projection_in_standard_errors"] = (
        merged.projection_delta.abs() / merged.standard_error
    )
    ordered = merged.sort_values("projection_in_standard_errors", ascending=False)
    return {
        "maximum_projection_in_standard_errors": float(
            ordered.projection_in_standard_errors.iloc[0]
        ),
        "largest_standardized_projection_states": ordered[
            keys + [
                "n_pitches", "re_smoothed", "re_constrained", "projection_delta",
                "standard_error", "projection_in_standard_errors",
            ]
        ].head(10).to_dict("records"),
    }


def validate(
    re_input: pd.DataFrame,
    constrained: pd.DataFrame,
    values: pd.DataFrame,
    spots: pd.DataFrame,
    calls: pd.DataFrame,
    solver: dict,
    weight_sensitivities: dict,
) -> dict:
    eligible = values[values.eligibility_status.eq("ELIGIBLE")]
    nonambiguous = eligible[eligible.cf_confidence.ne("AMBIGUOUS")]
    ambiguous = eligible[eligible.cf_confidence.eq("AMBIGUOUS")]
    bounded = ambiguous[ambiguous.value_status.eq("AMBIGUOUS_BOUNDED")]
    unvalued = ambiguous[ambiguous.value_status.eq("AMBIGUOUS_STRUCTURALLY_UNVALUED")]
    ordering_before = ordering_diagnostics(
        re_input.assign(re_constrained=re_input.re_smoothed), "re_constrained"
    )
    ordering_after = ordering_diagnostics(constrained, "re_constrained")
    full_after = full_constraint_diagnostics(constrained, "re_constrained")
    finite_states = int(np.isfinite(constrained.re_constrained).sum())
    finite_values = nonambiguous[[
        "re_observed_constrained", "re_corrected_constrained",
        "correction_value_runs_constrained",
    ]].notna().all(axis=1)
    bounds_finite = bounded[[
        "correction_value_runs_lower_constrained",
        "correction_value_runs_upper_constrained",
    ]].notna().all(axis=1)
    bounds_ordered = (
        bounded.correction_value_runs_lower_constrained
        <= bounded.correction_value_runs_upper_constrained + TOLERANCE
    )
    unvalued_null = unvalued[[
        "correction_value_runs_constrained",
        "correction_value_runs_lower_constrained",
        "correction_value_runs_upper_constrained",
    ]].isna().all(axis=1)
    spot_pass = spots.automated_check_pass.astype(str).str.lower().eq("true")
    spot_keys_present = spots.pitch_key.isin(set(values.pitch_key))
    replay = canonical_replay_diagnostics(calls)
    conditions = {
        "states_288_finite": len(constrained) == 288 and finite_states == 288,
        "solver_succeeded": solver["solver_success"],
        "count_ordering_has_zero_violations": ordering_after["violations"] == 0,
        "all_terminal_constraints_hold": full_after["violations"] == 0,
        "nonambiguous_eligible_values_finite": bool(finite_values.all()),
        "nonambiguous_eligible_values_nonnegative": bool(
            (nonambiguous.correction_value_runs_constrained >= -TOLERANCE).all()
        ),
        "eligible_ambiguous_count_is_40": len(ambiguous) == 40,
        "eligible_bounded_ambiguous_count_is_38": len(bounded) == 38,
        "eligible_structurally_unvalued_count_is_2": len(unvalued) == 2,
        "eligible_bounded_ambiguous_bounds_finite": bool(bounds_finite.all()),
        "eligible_bounded_ambiguous_bounds_ordered": bool(bounds_ordered.all()),
        "structurally_unvalued_values_are_null": bool(unvalued_null.all()),
        "article4_spot_checks_pass": bool(spot_pass.all() and spot_keys_present.all()),
        "canonical_r1_replay_matches": replay["mismatches"] == 0,
    }
    return {
        "gate": "G5_CORRECTION_VALUE",
        "status": "PASS" if all(conditions.values()) else "FAIL",
        "conditions": conditions,
        "re_table": {
            "states": len(constrained),
            "finite_states": finite_states,
            "ordering_before": ordering_before,
            "ordering_after": ordering_after,
            "full_constraints_after": full_after,
            "solver": solver,
            "states_changed": int((constrained.projection_delta.abs() > TOLERANCE).sum()),
            "mean_absolute_projection": float(constrained.projection_delta.abs().mean()),
            "maximum_absolute_projection": float(constrained.projection_delta.abs().max()),
        },
        "eligible_values": {
            "rows": len(eligible),
            "nonambiguous_rows": len(nonambiguous),
            "ambiguous_rows": len(ambiguous),
            "bounded_ambiguous_rows": len(bounded),
            "structurally_unvalued_rows": len(unvalued),
            "structurally_unvalued_pitch_keys": sorted(unvalued.pitch_key.tolist()),
            "nonfinite_nonambiguous_rows": int((~finite_values).sum()),
            "negative_nonambiguous_rows": int((nonambiguous.correction_value_runs_constrained < -TOLERANCE).sum()),
            "median_correction_value": float(nonambiguous.correction_value_runs_constrained.median()),
            "mean_correction_value": float(nonambiguous.correction_value_runs_constrained.mean()),
            "maximum_correction_value": float(nonambiguous.correction_value_runs_constrained.max()),
        },
        "spot_checks": {
            "rows": len(spots),
            "automated_passes": int(spot_pass.sum()),
            "keys_present": int(spot_keys_present.sum()),
        },
        "canonical_replay": replay,
        "projection_uncertainty": projection_uncertainty(re_input, constrained),
        "sensitivities": sensitivity_diagnostics(values),
        "weight_sensitivities": weight_sensitivities,
    }


def render_report(validation: dict) -> str:
    re_diag = validation["re_table"]
    values = validation["eligible_values"]
    lines = [
        "# ABS-05 Gate G5 Correction-Value Validation",
        "",
        "Generated by `build_correction_values.py`; do not hand-edit.",
        "",
        f"**Gate status: {validation['status']}**",
        "",
        "## Conditions",
        "",
        *[f"- {name}: {'PASS' if passed else 'FAIL'}" for name, passed in validation["conditions"].items()],
        "",
        "## Constrained run expectancy",
        "",
        f"- States: {re_diag['states']}; changed by projection: {re_diag['states_changed']}.",
        f"- Within-stratum ordering violations before/after: {re_diag['ordering_before']['violations']} / {re_diag['ordering_after']['violations']}.",
        f"- Full constraint violations after: {re_diag['full_constraints_after']['violations']}.",
        f"- Mean/max absolute projection: {re_diag['mean_absolute_projection']:.6f} / {re_diag['maximum_absolute_projection']:.6f} runs.",
        "",
        "## Eligible incorrect calls",
        "",
        f"- Rows: {values['rows']:,}; non-ambiguous: {values['nonambiguous_rows']:,}; ambiguous: {values['ambiguous_rows']}.",
        f"- Ambiguous reconciliation: {values['bounded_ambiguous_rows']} bounded + {values['structurally_unvalued_rows']} structurally unvalued.",
        f"- Nonfinite or negative non-ambiguous values: {values['nonfinite_nonambiguous_rows']} / {values['negative_nonambiguous_rows']}.",
        f"- Median/mean/max correction value: {values['median_correction_value']:.6f} / {values['mean_correction_value']:.6f} / {values['maximum_correction_value']:.6f} runs.",
        "",
        "## Sensitivities",
        "",
    ]
    for name, diag in validation["sensitivities"].items():
        lines.append(
            f"- {name}: mean |difference| {diag['mean_absolute_difference']:.6f}, "
            f"max {diag['maximum_absolute_difference']:.6f}, correlation {diag['correlation']:.6f}, "
            f"sign disagreements {diag['sign_disagreements']}."
        )
    lines.extend(["", "### Projection-weight sensitivities", ""])
    for name, diag in validation["weight_sensitivities"].items():
        lines.append(
            f"- {name}: changed states {diag['states_changed']}, max projection "
            f"{diag['maximum_absolute_projection']:.6f}, minimum exact eligible value "
            f"{diag['minimum_nonambiguous_eligible_value']:.6f}."
        )
    lines.extend([
        "",
        f"Largest projection relative to its cell standard error: {validation['projection_uncertainty']['maximum_projection_in_standard_errors']:.3f}.",
    ])
    lines.extend(["", "Sensitivity disagreement is descriptive at G5 and is tested for policy stability at G8.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve() if args.output else root / "research/article5/output/g5"
    output.mkdir(parents=True, exist_ok=True)

    re_path = root / "research/article4/output/article4_re288_table.csv"
    calls_path = root / "research/article4/output/article4_all_incorrect_calls.csv"
    spots_path = root / "research/article4/output/article4_spot_checks.csv"
    spec_path = root / "research/article5/CORRECTION_VALUE_SPEC.md"
    re_input = pd.read_csv(re_path, dtype={"base_state": str})
    calls = pd.read_csv(
        calls_path,
        low_memory=False,
        dtype={"base_state": str, "obs_base_state": str, "cor_base_state": str},
    )
    spots = pd.read_csv(spots_path, dtype={"base_state": str})

    constrained, solver = build_constrained_table(re_input)
    lookup = lookup_from_table(constrained)
    values = value_incorrect_calls(calls, lookup)
    weight_sensitivities = {}
    for name, prior_mass, uniform in [
        ("prior_20", 20.0, False),
        ("prior_80", 80.0, False),
        ("uniform_weights", 0.0, True),
    ]:
        sensitivity_table, _ = build_constrained_table(
            re_input, prior_mass=prior_mass, uniform_weights=uniform
        )
        sensitivity_values = value_incorrect_calls(
            calls, lookup_from_table(sensitivity_table)
        )
        sensitivity_eligible = sensitivity_values[
            sensitivity_values.eligibility_status.eq("ELIGIBLE")
            & sensitivity_values.cf_confidence.ne("AMBIGUOUS")
        ]
        weight_sensitivities[name] = {
            "states_changed": int((sensitivity_table.projection_delta.abs() > TOLERANCE).sum()),
            "maximum_absolute_projection": float(sensitivity_table.projection_delta.abs().max()),
            "minimum_nonambiguous_eligible_value": float(
                sensitivity_eligible.correction_value_runs_constrained.min()
            ),
        }
    validation = validate(
        re_input, constrained, values, spots, calls, solver, weight_sensitivities
    )

    table_out = output / "re288_constrained.csv"
    values_out = output / "incorrect_call_correction_values.csv"
    validation_out = output / "validation.json"
    report_out = output / "VALIDATION.md"
    constrained.to_csv(table_out, index=False, float_format="%.10g", lineterminator="\n")
    values.to_csv(values_out, index=False, float_format="%.10g", lineterminator="\n")
    write_json(validation_out, validation)
    report_out.write_text(render_report(validation))

    manifest = {
        "version": VERSION,
        "status": validation["status"],
        "preregistration_sha256": sha256(root / "research/article5/PREREGISTRATION.md"),
        "specification_sha256": sha256(spec_path),
        "amendment_sha256": sha256(root / "research/article5/AMENDMENT_001_G5.md"),
        "code_sha256": sha256(Path(__file__)),
        "inputs": {str(path.relative_to(root)): sha256(path) for path in [re_path, calls_path, spots_path]},
        "outputs": {path.name: {"sha256": sha256(path), "bytes": path.stat().st_size} for path in [table_out, values_out, validation_out, report_out]},
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
        },
    }
    write_json(output / "manifest.json", manifest)
    print(json.dumps({"gate": validation["gate"], "status": validation["status"]}, sort_keys=True))
    return 0 if validation["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
