"""Build the ABS-05 Gate G8 assumption-conditional stability audit."""
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
sys.path.insert(0, str(HERE.parent / "article4"))
sys.path.insert(0, str(HERE.parent / "article4/decision_value"))
from build_correction_values import (  # noqa: E402
    build_constrained_table,
    lookup_from_table,
    value_incorrect_calls,
)
from build_dynamic_engine import prepare_stream, scenario_probability  # noqa: E402
from dv_core import flip_value  # noqa: E402
from stability_core import dynamic_values, flip_rate, threshold_band  # noqa: E402

import build as article4_build  # noqa: E402

VERSION = "abs_article5_stability_v1"
TOLERANCE = 1e-9
REFERENCE = "reference_fixed_0.60"

VARIANTS = [
    {"name": REFERENCE, "kind": "reference", "value": "value_constrained", "probability": "fixed_0.60", "grant_extras": True, "primary": False},
    {"name": "re_unconstrained_smoothed", "kind": "correction_value", "value": "value_smoothed", "probability": "fixed_0.60", "grant_extras": True, "primary": True},
    {"name": "re_pooled_count", "kind": "correction_value", "value": "value_pooled", "probability": "fixed_0.60", "grant_extras": True, "primary": True},
    {"name": "re_raw", "kind": "correction_value", "value": "value_raw", "probability": "fixed_0.60", "grant_extras": True, "primary": True},
    {"name": "re_leave_one_month_out", "kind": "correction_value", "value": "value_lomo", "probability": "fixed_0.60", "grant_extras": True, "primary": True},
    {"name": "probability_fixed_0.50", "kind": "probability", "value": "value_constrained", "probability": "fixed_0.50", "grant_extras": True, "primary": True},
    {"name": "probability_fixed_0.70", "kind": "probability", "value": "value_constrained", "probability": "fixed_0.70", "grant_extras": True, "primary": True},
    {"name": "probability_public_tracking", "kind": "probability", "value": "value_constrained", "probability": "public_tracking", "grant_extras": True, "primary": True},
    {"name": "probability_selected_transport", "kind": "probability", "value": "value_constrained", "probability": "selected_transport", "grant_extras": True, "primary": True},
    {"name": "no_extra_inning_restoration", "kind": "extra_inning", "value": "value_constrained", "probability": "fixed_0.60", "grant_extras": False, "primary": True},
    {"name": "ambiguous_lower_bound", "kind": "ambiguous_bound", "value": "value_ambiguous_lower", "probability": "fixed_0.60", "grant_extras": True, "primary": False},
    {"name": "ambiguous_upper_bound", "kind": "ambiguous_bound", "value": "value_ambiguous_upper", "probability": "fixed_0.60", "grant_extras": True, "primary": False},
]


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


def lookup(table: pd.DataFrame, column: str) -> dict:
    return {
        (int(row.balls), int(row.strikes), int(row.outs), str(row.base_state)): float(getattr(row, column))
        for row in table.itertuples(index=False)
    }


def values_from_lookup(stream: pd.DataFrame, table: dict) -> np.ndarray:
    keys = stream[["balls", "strikes", "outs", "base_state", "original_call"]].drop_duplicates()
    mapping = {}
    for row in keys.itertuples(index=False):
        key = (int(row.balls), int(row.strikes), int(row.outs), str(row.base_state), row.original_call)
        mapping[key] = flip_value(*key, table)
    return np.asarray([
        mapping[(int(b), int(s), int(o), str(base), call)]
        for b, s, o, base, call in zip(
            stream.balls, stream.strikes, stream.outs, stream.base_state, stream.original_call
        )
    ])


def build_lomo_lookups(root: Path, cache: Path) -> dict[str, dict]:
    pitch_path = root / "data/full_season/processed/pitches.csv"
    pitches = pd.read_csv(
        pitch_path,
        usecols=["game_pk", "game_date", "pitch_key", "source_game_feed"],
        low_memory=False,
    )
    article4_build.ROOT = root
    feed, _ = article4_build.feed_states(root, pitches, cache)
    feed["bases"] = (
        feed.feed_pre_on_1b.astype(str)
        + feed.feed_pre_on_2b.astype(str)
        + feed.feed_pre_on_3b.astype(str)
    )
    dates = pitches.drop_duplicates("game_pk").set_index("game_pk").game_date.astype(str)
    feed["game_date"] = feed.game_pk.map(dates)
    feed = feed[feed.pitch_key.isin(set(pitches.pitch_key))].copy()
    months = sorted(feed.game_date.str[:7].unique())
    return {
        month: article4_build.re_lookup(
            article4_build.fit_re(feed[feed.game_date.str[:7] != month])
        )
        for month in months
    }


def attach_value_sensitivities(stream: pd.DataFrame, root: Path, cache: Path) -> tuple[pd.DataFrame, dict]:
    re_input = pd.read_csv(
        root / "research/article4/output/article4_re288_table.csv",
        dtype={"base_state": str},
    )
    constrained, _ = build_constrained_table(re_input)
    stream = stream.copy()
    stream["value_constrained"] = stream.correction_value.to_numpy(dtype=float)
    stream["value_smoothed"] = values_from_lookup(stream, lookup(re_input, "re_smoothed"))
    stream["value_pooled"] = values_from_lookup(stream, lookup(re_input, "re_count_pooled"))
    stream["value_raw"] = values_from_lookup(stream, lookup(re_input, "raw_mean"))

    lomo = build_lomo_lookups(root, cache)
    stream["month"] = stream.game_date.astype(str).str[:7]
    lomo_values = np.empty(len(stream))
    for month, positions in stream.groupby("month", sort=True).groups.items():
        if month not in lomo:
            raise RuntimeError(f"missing leave-one-month-out table for {month}")
        loc = np.asarray(list(positions), dtype=int)
        lomo_values[loc] = values_from_lookup(stream.loc[loc], lomo[month])
    stream["value_lomo"] = lomo_values

    calls = pd.read_csv(
        root / "research/article4/output/article4_all_incorrect_calls.csv",
        low_memory=False,
        dtype={"base_state": str, "obs_base_state": str, "cor_base_state": str},
    )
    bounded = value_incorrect_calls(calls, lookup_from_table(constrained))
    bounded = bounded[
        bounded.eligibility_status.eq("ELIGIBLE")
        & bounded.cf_confidence.eq("AMBIGUOUS")
        & bounded.value_status.eq("AMBIGUOUS_BOUNDED")
    ]
    lower = bounded.set_index("pitch_key").correction_value_runs_lower_constrained.to_dict()
    upper = bounded.set_index("pitch_key").correction_value_runs_upper_constrained.to_dict()
    stream["value_ambiguous_lower"] = stream.value_constrained
    stream["value_ambiguous_upper"] = stream.value_constrained
    stream["ambiguous_bounded"] = stream.pitch_key.isin(lower)
    stream.loc[stream.pitch_key.isin(lower), "value_ambiguous_lower"] = stream.pitch_key.map(lower)
    stream.loc[stream.pitch_key.isin(upper), "value_ambiguous_upper"] = stream.pitch_key.map(upper)

    value_columns = [variant["value"] for variant in VARIANTS]
    audit = {
        "lomo_months": sorted(lomo),
        "bounded_ambiguous_rows": len(bounded),
        "bounded_ambiguous_keys_in_stream": int(stream.pitch_key.isin(lower).sum()),
        "nonfinite_by_value": {column: int((~np.isfinite(stream[column])).sum()) for column in sorted(set(value_columns))},
        "negative_by_value": {column: int((stream[column] < -TOLERANCE).sum()) for column in sorted(set(value_columns))},
    }
    return stream, audit


def family_masks(stream: pd.DataFrame) -> dict[str, np.ndarray]:
    bases = stream.base_state.astype(str)
    risp = bases.str[1].eq("1") | bases.str[2].eq("1")
    return {
        "ordinary": (
            stream["count"].eq("0-0")
            & stream.outs.eq(0)
            & bases.eq("000")
            & stream.inning.between(1, 3)
        ).to_numpy(),
        "full_count": stream["count"].eq("3-2").to_numpy(),
        "two_out_risp": (stream.outs.eq(2) & risp).to_numpy(),
        "late_close": (
            stream.inning.between(7, 9) & stream.team_score_diff.abs().le(1)
        ).to_numpy(),
        "extra_innings": stream.inning.ge(10).to_numpy(),
    }


def run_variants(stream: pd.DataFrame) -> tuple[dict, dict, dict]:
    n = len(stream)
    results = {
        variant["name"]: {
            "action_1": np.zeros(n, dtype=bool),
            "action_2": np.zeros(n, dtype=bool),
            "threshold_1": np.full(n, np.nan),
            "threshold_2": np.full(n, np.nan),
        }
        for variant in VARIANTS
    }
    game_counts = {variant["name"]: 0 for variant in VARIANTS}
    groups = list(stream.groupby(["game_pk", "team_id"], sort=True))
    for variant in VARIANTS:
        name = variant["name"]
        for _, group in groups:
            loc = group.index.to_numpy(dtype=int)
            p = scenario_probability(group, variant["probability"])
            value = group[variant["value"]].to_numpy(dtype=float)
            solution = dynamic_values(p, value, group.inning, variant["grant_extras"])
            for inventory in (1, 2):
                results[name][f"action_{inventory}"][loc] = solution["action"][inventory]
                results[name][f"threshold_{inventory}"][loc] = solution["threshold"][inventory]
            game_counts[name] += 1
    return results, game_counts, {variant["name"]: variant for variant in VARIANTS}


def build_outputs(stream: pd.DataFrame, results: dict, metadata: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    legal = stream.observed_legal_decision.to_numpy(dtype=bool)
    legal_values = stream.loc[legal, "value_constrained"]
    cutoff = float(legal_values.quantile(0.90, interpolation="linear"))
    top = legal & stream.value_constrained.ge(cutoff).to_numpy()
    top_positions = np.flatnonzero(top)

    top_actions = stream.loc[top_positions, [
        "pitch_key", "game_pk", "game_date", "team_id", "inning", "half_inning",
        "team_score_diff", "count", "outs", "base_state", "side", "value_constrained",
    ]].copy()
    for inventory in (1, 2):
        top_actions[f"reference_action_inventory_{inventory}"] = results[REFERENCE][f"action_{inventory}"][top]
        top_actions[f"reference_threshold_inventory_{inventory}"] = results[REFERENCE][f"threshold_{inventory}"][top]
    for variant in VARIANTS[1:]:
        name = variant["name"]
        for inventory in (1, 2):
            top_actions[f"{name}_action_inventory_{inventory}"] = results[name][f"action_{inventory}"][top]

    flip_rows = []
    for variant in VARIANTS[1:10]:
        name = variant["name"]
        for inventory in (1, 2):
            denominator, flips, rate = flip_rate(
                results[REFERENCE][f"action_{inventory}"][top],
                results[name][f"action_{inventory}"][top],
            )
            flip_rows.append({
                "sensitivity": name,
                "sensitivity_type": variant["kind"],
                "inventory": inventory,
                "available": True,
                "denominator": denominator,
                "reference_challenges": int(results[REFERENCE][f"action_{inventory}"][top].sum()),
                "sensitivity_challenges": int(results[name][f"action_{inventory}"][top].sum()),
                "flips": flips,
                "flip_rate": rate,
                "passes_10_percent": bool(rate <= 0.10 + TOLERANCE),
            })
    for name, kind in [
        ("win_probability_objective", "objective_scale"),
        ("league_typical_opponent", "opponent_policy"),
        ("optimized_opponent", "opponent_policy"),
    ]:
        for inventory in (1, 2):
            flip_rows.append({
                "sensitivity": name,
                "sensitivity_type": kind,
                "inventory": inventory,
                "available": False,
                "denominator": len(top_positions),
                "reference_challenges": int(results[REFERENCE][f"action_{inventory}"][top].sum()),
                "sensitivity_challenges": np.nan,
                "flips": np.nan,
                "flip_rate": np.nan,
                "passes_10_percent": False,
            })
    flips = pd.DataFrame(flip_rows)

    masks = family_masks(stream)
    scenario_rows = []
    for variant in VARIANTS[:10]:
        name = variant["name"]
        for inventory in (1, 2):
            for family, mask in masks.items():
                selected = legal & mask
                values = results[name][f"threshold_{inventory}"][selected]
                median = float(np.median(values)) if len(values) else np.nan
                reference_values = results[REFERENCE][f"threshold_{inventory}"][selected]
                reference_median = float(np.median(reference_values)) if len(reference_values) else np.nan
                band = threshold_band(median)
                reference_band = threshold_band(reference_median)
                scenario_rows.append({
                    "sensitivity": name,
                    "sensitivity_type": variant["kind"],
                    "inventory": inventory,
                    "scenario_family": family,
                    "rows": int(selected.sum()),
                    "median_threshold": median,
                    "threshold_band": band,
                    "reference_median_threshold": reference_median,
                    "reference_threshold_band": reference_band,
                    "band_crossing": bool(name != REFERENCE and band != reference_band),
                })
    scenarios = pd.DataFrame(scenario_rows)

    unique_dates = sorted(stream.loc[legal, "game_date"].astype(str).unique())
    split = len(unique_dates) // 2
    early_dates = set(unique_dates[:split])
    late_dates = set(unique_dates[split:])
    period = np.where(stream.game_date.astype(str).isin(early_dates), "EARLY", "LATE")
    distribution_rows = []
    for label in ("EARLY", "LATE"):
        selected = legal & (period == label)
        for inventory in (1, 2):
            distribution_rows.append({
                "period": label,
                "first_date": min(stream.loc[selected, "game_date"].astype(str)),
                "last_date": max(stream.loc[selected, "game_date"].astype(str)),
                "inventory": inventory,
                "rows": int(selected.sum()),
                "mean_correction_value": float(stream.loc[selected, "value_constrained"].mean()),
                "median_correction_value": float(stream.loc[selected, "value_constrained"].median()),
                "mean_threshold": float(np.mean(results[REFERENCE][f"threshold_{inventory}"][selected])),
                "median_threshold": float(np.median(results[REFERENCE][f"threshold_{inventory}"][selected])),
                "action_rate": float(np.mean(results[REFERENCE][f"action_{inventory}"][selected])),
            })
    distribution = pd.DataFrame(distribution_rows)

    ambiguous = stream.ambiguous_bounded.to_numpy(dtype=bool) & legal
    ambiguous_rows = []
    for name in ("ambiguous_lower_bound", "ambiguous_upper_bound"):
        for inventory in (1, 2):
            denominator, count, rate = flip_rate(
                results[REFERENCE][f"action_{inventory}"][ambiguous],
                results[name][f"action_{inventory}"][ambiguous],
            )
            ambiguous_rows.append({
                "sensitivity": name,
                "inventory": inventory,
                "denominator": denominator,
                "flips": count,
                "flip_rate": rate,
            })
    ambiguous_audit = pd.DataFrame(ambiguous_rows)

    audit = {
        "top_value_cutoff": cutoff,
        "top_value_rows": len(top_positions),
        "top_value_share": float(len(top_positions) / legal.sum()),
        "first_late_date": unique_dates[split],
        "scenario_band_crossings": int(scenarios.band_crossing.sum()),
        "ambiguous_rows_audited": int(ambiguous.sum()),
    }
    return flips, top_actions, scenarios, distribution, ambiguous_audit, audit


def render_report(validation: dict, flips: pd.DataFrame) -> str:
    available = flips[flips.available]
    failed = available[~available.passes_10_percent]
    unavailable = sorted(flips.loc[~flips.available, "sensitivity"].unique())
    return "\n".join([
        "# ABS-05 Gate G8 Stability Validation",
        "",
        "Generated by `build_stability.py`; do not hand-edit.",
        "",
        f"**Computational status: {validation['computational_status']}**",
        f"**Gate status: {validation['gate_status']}**",
        f"**Playbook allowed: {validation['playbook_allowed']}**",
        "",
        "## Fixed top-value population",
        "",
        f"- Cutoff: {validation['audit']['top_value_cutoff']:.6f} runs.",
        f"- Rows: {validation['audit']['top_value_rows']:,} ({validation['audit']['top_value_share']:.3%} of legal decisions).",
        "",
        "## Stability result",
        "",
        f"- Available sensitivity/inventory comparisons above 10% flips: {len(failed)}.",
        f"- Maximum available flip rate: {available.flip_rate.max():.3%}.",
        f"- Disclosed threshold-band crossings: {validation['audit']['scenario_band_crossings']}.",
        "",
        "## Mandatory unavailable sensitivities",
        "",
        *[f"- {name}" for name in unavailable],
        "",
        "Win probability is not replaced with realized wins or an unvalidated conversion. Opponent response is not identified by independent fixed empirical sequences. These omissions keep G8 incomplete even if the available comparisons were stable.",
        "",
        "## Interpretation",
        "",
        "All actions are conditional on named assumptions. G6 did not identify player confidence, G7 fixes the subsequent game path, and this gate does not authorize player advice, an optimal-policy claim, or a Pascal ABS Challenge Playbook.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve() if args.output else root / "research/article5/output/g8"
    cache = args.cache.resolve() if args.cache else root / "research/article5/output/cache"
    output.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)

    protected = [
        root / "data/full_season/processed/pitches.csv",
        root / "data/full_season/processed/challenges.csv",
        root / "research/article4/output/article4_re288_table.csv",
        root / "research/article4/output/article4_all_incorrect_calls.csv",
        root / "research/article4/output/manifest.json",
        root / "research/article5/PREREGISTRATION.md",
        root / "research/article5/STABILITY_SPEC.md",
    ]
    before = {str(path.relative_to(root)): sha256(path) for path in protected}
    stream, population = prepare_stream(root)
    stream, value_audit = attach_value_sensitivities(stream, root, cache)
    results, game_counts, metadata = run_variants(stream)
    flips, top_actions, scenarios, distribution, ambiguous, audit = build_outputs(stream, results, metadata)
    after = {str(path.relative_to(root)): sha256(path) for path in protected}

    available_primary = flips[flips.available & flips.sensitivity_type.isin([
        "correction_value", "probability", "extra_inning"
    ])]
    unavailable_mandatory = sorted(flips.loc[~flips.available, "sensitivity"].unique())
    conditions = {
        "protected_inputs_unchanged": before == after,
        "legal_decisions_reconcile": population["observed_legal_decisions"] == 312_228,
        "team_games_reconcile": population["team_games"] == 4_390,
        "all_variants_cover_team_games": all(count == 4_390 for count in game_counts.values()),
        "all_value_inputs_finite": all(count == 0 for count in value_audit["nonfinite_by_value"].values()),
        "top_population_nonempty": audit["top_value_rows"] > 0,
        "top_actions_unique": not top_actions.duplicated(["pitch_key"]).any(),
        "scenario_crossings_disclosed": "band_crossing" in scenarios and scenarios.band_crossing.notna().all(),
        "ambiguous_bounds_reconcile": value_audit["bounded_ambiguous_rows"] == 38 and audit["ambiguous_rows_audited"] == 38,
    }
    computational_status = "PASS" if all(conditions.values()) else "FAIL"
    flip_gate = bool(available_primary.passes_10_percent.all())
    if computational_status != "PASS":
        gate_status = "FAIL_COMPUTATION"
    elif not flip_gate and unavailable_mandatory:
        gate_status = "FAIL_STABILITY_AND_INCOMPLETE_MANDATORY_SENSITIVITIES"
    elif not flip_gate:
        gate_status = "FAIL_STABILITY"
    elif unavailable_mandatory:
        gate_status = "INCOMPLETE_MANDATORY_SENSITIVITIES"
    else:
        gate_status = "PASS"
    validation = {
        "gate": "G8_STABILITY",
        "computational_status": computational_status,
        "gate_status": gate_status,
        "playbook_allowed": False,
        "conditions": conditions,
        "population": population,
        "value_audit": value_audit,
        "audit": audit,
        "available_primary_flip_gate_pass": flip_gate,
        "available_primary_max_flip_rate": float(available_primary.flip_rate.max()),
        "unavailable_mandatory_sensitivities": unavailable_mandatory,
        "restrictions": {
            "player_probability": "not identified by G6",
            "deltaW": "zero by construction in the G7 empirical-sequence engine",
            "win_probability": "unavailable; no validated decision-time estimator",
            "opponent_response": "unavailable; independent fixed sequences do not identify it",
        },
    }

    outputs = {
        "flip_summary.csv": flips,
        "top_value_actions.csv": top_actions,
        "scenario_stability.csv": scenarios,
        "distribution_shift.csv": distribution,
        "ambiguous_bounds.csv": ambiguous,
    }
    for name, frame in outputs.items():
        frame.to_csv(output / name, index=False, float_format="%.10g", lineterminator="\n")
    write_json(output / "validation.json", validation)
    (output / "VALIDATION.md").write_text(render_report(validation, flips))
    artifacts = [output / name for name in outputs] + [output / "validation.json", output / "VALIDATION.md"]
    manifest = {
        "version": VERSION,
        "computational_status": computational_status,
        "gate_status": gate_status,
        "code_sha256": {
            "build_stability.py": sha256(Path(__file__)),
            "stability_core.py": sha256(HERE / "stability_core.py"),
        },
        "inputs": before,
        "outputs": {path.name: {"sha256": sha256(path), "bytes": path.stat().st_size} for path in artifacts},
        "software": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
    }
    write_json(output / "manifest.json", manifest)
    print(json.dumps({"computational_status": computational_status, "gate_status": gate_status}, sort_keys=True))
    return 0 if computational_status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
