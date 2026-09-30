"""Build and validate the ABS-05 empirical-sequence inventory engine."""
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
sys.path.insert(0, str(HERE.parent / "article4/decision_value"))
from dynamic_core import backward_values, simulate_policy  # noqa: E402
from validate_probability import fit_glm, load_populations  # noqa: E402
from dv_core import edge_class, flip_value  # noqa: E402

SCENARIOS = ["fixed_0.50", "fixed_0.60", "fixed_0.70", "public_tracking", "selected_transport"]
POLICIES = ["never", "confidence_0.5", "confidence_0.6", "confidence_0.7", "ev_0.05", "dynamic"]
SEED = 20260925
TOLERANCE = 1e-9
VERSION = "abs_article5_dynamic_engine_v1"


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


def _bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().map({"true": True, "false": False})


def prepare_stream(
    root: Path,
    pitches_path: Path | None = None,
) -> tuple[pd.DataFrame, dict]:
    public, selected, probability_audit = load_populations(root)
    public_model = fit_glm(public)
    selected_model = fit_glm(selected)

    columns = [
        "pitch_key", "game_pk", "game_date", "at_bat_index", "play_event_index",
        "inning", "half_inning", "outs", "balls", "strikes", "on_1b", "on_2b",
        "on_3b", "home_score", "away_score", "home_team_id", "away_team_id",
        "original_call", "distance_from_abs_boundary", "plate_x", "plate_z",
        "abs_zone_top", "abs_zone_bot", "bat_side", "position_player_pitching",
        "affected_team_challenges_remaining", "challenge_available",
    ]
    source_path = pitches_path or root / "data/full_season/processed/pitches.csv"
    pitches = pd.read_csv(source_path, usecols=columns, low_memory=False)
    called = pitches.original_call.isin(["BALL", "STRIKE"])
    position_player = _bool(pitches.position_player_pitching).fillna(False)
    stream = pitches[called & ~position_player].copy()
    stream["observed_legal_decision"] = _bool(stream.challenge_available).fillna(False)
    stream["base_state"] = (
        stream.on_1b.notna().astype(int).astype(str)
        + stream.on_2b.notna().astype(int).astype(str)
        + stream.on_3b.notna().astype(int).astype(str)
    )
    stream["side"] = np.where(stream.original_call.eq("STRIKE"), "OFFENSE", "DEFENSE")
    batting = np.where(stream.half_inning.eq("top"), stream.away_team_id, stream.home_team_id)
    fielding = np.where(stream.half_inning.eq("top"), stream.home_team_id, stream.away_team_id)
    stream["team_id"] = np.where(stream.side.eq("OFFENSE"), batting, fielding).astype(int)
    stream["team_role"] = np.where(stream.team_id.eq(stream.home_team_id), "HOME", "AWAY")
    batting_score = np.where(stream.half_inning.eq("top"), stream.away_score, stream.home_score)
    fielding_score = np.where(stream.half_inning.eq("top"), stream.home_score, stream.away_score)
    stream["team_score_diff"] = np.where(
        stream.side.eq("OFFENSE"), batting_score - fielding_score, fielding_score - batting_score
    )
    stream["count"] = stream.balls.astype(int).astype(str) + "-" + stream.strikes.astype(int).astype(str)
    stream["order"] = stream.at_bat_index * 1000 + stream.play_event_index

    # Benchmark-only probability features. Invalid geometry rows receive the
    # corresponding training base rate and remain explicitly counted.
    stream["absd"] = (
        pd.to_numeric(stream.distance_from_abs_boundary, errors="coerce").abs() * 12
    ).clip(upper=6.0)
    stream["edge"] = edge_class(
        stream.plate_x, stream.plate_z, stream.abs_zone_top, stream.abs_zone_bot,
        stream.bat_side,
    )
    stream["edge"] = pd.Series(stream.edge, index=stream.index).fillna("UNKNOWN")
    stream["terminal"] = ((stream.balls == 3) | (stream.strikes == 2)).astype(int)
    valid_geometry = stream[["absd", "edge", "side", "terminal"]].notna().all(axis=1)
    stream["p_public"] = float(public.target.mean())
    stream["p_selected"] = float(selected.target.mean())
    stream.loc[valid_geometry, "p_public"] = np.clip(
        public_model.predict(stream.loc[valid_geometry]), 1e-6, 1 - 1e-6
    )
    stream.loc[valid_geometry, "p_selected"] = np.clip(
        selected_model.predict(stream.loc[valid_geometry]), 1e-6, 1 - 1e-6
    )

    from build_correction_values import build_constrained_table, lookup_from_table
    re_input = pd.read_csv(
        root / "research/article4/output/article4_re288_table.csv",
        dtype={"base_state": str},
    )
    constrained, _ = build_constrained_table(re_input)
    lookup = lookup_from_table(constrained)
    unique = stream[["balls", "strikes", "outs", "base_state", "original_call"]].drop_duplicates()
    value_map = {}
    for row in unique.itertuples(index=False):
        key = (int(row.balls), int(row.strikes), int(row.outs), str(row.base_state), row.original_call)
        value_map[key] = flip_value(*key, lookup)
    stream["correction_value"] = [
        value_map[(int(b), int(s), int(o), str(base), call)]
        for b, s, o, base, call in zip(
            stream.balls, stream.strikes, stream.outs, stream.base_state,
            stream.original_call,
        )
    ]
    stream.loc[stream.correction_value.abs() < TOLERANCE, "correction_value"] = 0.0
    stream = stream.sort_values(["game_pk", "team_id", "order"]).reset_index(drop=True)
    audit = {
        "probability_training": probability_audit,
        "future_stream_rows": len(stream),
        "observed_legal_decisions": int(stream.observed_legal_decision.sum()),
        "exhausted_future_opportunities": int((~stream.observed_legal_decision).sum()),
        "team_games": int(stream.groupby(["game_pk", "team_id"]).ngroups),
        "invalid_geometry_probability_fallbacks": int((~valid_geometry).sum()),
        "negative_canonical_values": int((stream.correction_value < -TOLERANCE).sum()),
        "nonfinite_canonical_values": int((~np.isfinite(stream.correction_value)).sum()),
        "pitch_source": str(source_path.resolve().relative_to(root.resolve())),
    }
    return stream, audit


def scenario_probability(frame: pd.DataFrame, scenario: str) -> np.ndarray:
    if scenario.startswith("fixed_"):
        return np.repeat(float(scenario.split("_")[1]), len(frame))
    if scenario == "public_tracking":
        return frame.p_public.to_numpy(dtype=float)
    if scenario == "selected_transport":
        return frame.p_selected.to_numpy(dtype=float)
    raise ValueError(scenario)


def inning_bucket(inning: int) -> str:
    return "1-3" if inning <= 3 else "4-6" if inning <= 6 else "7-9" if inning <= 9 else "10+"


def run_engine(stream: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    game_rows, threshold_rows = [], []
    aggregates = {}
    representative = None
    groups = list(stream.groupby(["game_pk", "team_id"], sort=True))
    for scenario in SCENARIOS:
        for (game_pk, team_id), group in groups:
            p = scenario_probability(group, scenario)
            value = group.correction_value.to_numpy(dtype=float)
            innings = group.inning.to_numpy(dtype=int)
            solutions = {}
            for policy in POLICIES:
                solution = backward_values(p, value, innings, policy)
                solutions[policy] = solution
                game_rows.append({
                    "scenario": scenario,
                    "policy": policy,
                    "game_pk": int(game_pk),
                    "team_id": int(team_id),
                    "team_role": group.team_role.iloc[0],
                    "opportunities": len(group),
                    "max_inning": int(group.inning.max()),
                    "W0": float(solution["W"][0, 0]),
                    "W1": float(solution["W"][1, 0]),
                    "W2": float(solution["W"][2, 0]),
                    "C1": float(solution["W"][1, 0] - solution["W"][0, 0]),
                    "C2": float(solution["W"][2, 0] - solution["W"][1, 0]),
                })
            dynamic = solutions["dynamic"]
            legal_positions = np.flatnonzero(group.observed_legal_decision.to_numpy())
            for i in legal_positions:
                row = group.iloc[i]
                for inventory in (1, 2):
                    key = (scenario, inventory, inning_bucket(int(row.inning)))
                    record = aggregates.setdefault(key, {"n": 0, "cost": 0.0, "threshold": 0.0, "action": 0})
                    record["n"] += 1
                    record["cost"] += float(dynamic["cost"][inventory, i])
                    record["threshold"] += float(dynamic["threshold"][inventory, i])
                    record["action"] += int(dynamic["action"][inventory, i])
                if scenario == "fixed_0.50":
                    threshold_rows.append({
                        "scenario": scenario,
                        "pitch_key": row.pitch_key,
                        "game_pk": int(game_pk),
                        "team_id": int(team_id),
                        "inning": int(row.inning),
                        "half_inning": row.half_inning,
                        "team_role": row.team_role,
                        "team_score_diff": int(row.team_score_diff),
                        "count": row["count"],
                        "outs": int(row.outs),
                        "base_state": row.base_state,
                        "side": row.side,
                        "probability": float(p[i]),
                        "correction_value": float(value[i]),
                        "future_marginal_cost_C1": float(dynamic["cost"][1, i]),
                        "future_marginal_cost_C2": float(dynamic["cost"][2, i]),
                        "challenge_threshold_inventory_1": float(dynamic["threshold"][1, i]),
                        "challenge_threshold_inventory_2": float(dynamic["threshold"][2, i]),
                        "dynamic_action_inventory_1": bool(dynamic["action"][1, i]),
                        "dynamic_action_inventory_2": bool(dynamic["action"][2, i]),
                        "deltaW_assumption": 0.0,
                    })
            if representative is None and scenario == "fixed_0.60" and 60 <= len(group) <= 100:
                representative = (p, value, innings, solutions["dynamic"])

    if representative is None:
        raise RuntimeError("no representative sequence for simulation")
    p, value, innings, solution = representative
    draws = simulate_policy(p, value, innings, solution, 2, 50_000, SEED)
    expected = float(solution["W"][2, 0])
    se = float(draws.std(ddof=1) / np.sqrt(len(draws)))
    simulation = {
        "repetitions": len(draws),
        "dynamic_program_value": expected,
        "simulation_mean": float(draws.mean()),
        "simulation_standard_error": se,
        "absolute_difference": abs(float(draws.mean()) - expected),
        "within_four_standard_errors": abs(float(draws.mean()) - expected) <= 4 * se,
    }
    summary_rows = []
    for (scenario, inventory, bucket), record in sorted(aggregates.items()):
        summary_rows.append({
            "scenario": scenario,
            "inventory": inventory,
            "inning_bucket": bucket,
            "decisions": record["n"],
            "mean_cost": record["cost"] / record["n"],
            "mean_threshold": record["threshold"] / record["n"],
            "dynamic_challenge_rate": record["action"] / record["n"],
        })
    return pd.DataFrame(game_rows), pd.DataFrame(threshold_rows), pd.DataFrame(summary_rows), simulation


def summarize(game_values: pd.DataFrame) -> pd.DataFrame:
    game_summary = (
        game_values.groupby(["scenario", "policy"], sort=True)
        .agg(
            team_games=("game_pk", "size"),
            mean_W1=("W1", "mean"),
            mean_W2=("W2", "mean"),
            mean_C1=("C1", "mean"),
            mean_C2=("C2", "mean"),
            median_C1=("C1", "median"),
            median_C2=("C2", "median"),
        )
        .reset_index()
    )
    return game_summary


def render_report(validation: dict) -> str:
    sim = validation["simulation"]
    return "\n".join([
        "# ABS-05 Gate G7 Dynamic-Engine Validation",
        "",
        "Generated by `build_dynamic_engine.py`; do not hand-edit.",
        "",
        f"**Build status: {validation['build_status']}**",
        f"**Scientific status: {validation['scientific_status']}**",
        "",
        "## Population",
        "",
        f"- {validation['population']['observed_legal_decisions']:,} observed legal decisions.",
        f"- {validation['population']['future_stream_rows']:,} counterfactual future opportunities, including {validation['population']['exhausted_future_opportunities']:,} observed after exhaustion.",
        f"- {validation['population']['team_games']:,} team-games.",
        "",
        "## Computational validation",
        "",
        f"- Monte Carlo mean {sim['simulation_mean']:.6f} vs recursion {sim['dynamic_program_value']:.6f}; difference {sim['absolute_difference']:.6f}, SE {sim['simulation_standard_error']:.6f}.",
        f"- Agreement within four SE: {sim['within_four_standard_errors']}.",
        "- Success retains inventory; failure consumes one; extra-inning grants restore zero to one only.",
        "",
        "## Scientific restriction",
        "",
        "The engine integrates complete empirical opportunity sequences, but a corrected call does not rewrite the subsequent observed game path. Therefore deltaW is zero by construction, opponent response is not modeled, and C/(V+C) is an assumption-labeled sequence threshold rather than the final full-form threshold.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve() if args.output else root / "research/article5/output/g7"
    output.mkdir(parents=True, exist_ok=True)

    stream, population = prepare_stream(root)
    game_values, thresholds, threshold_summary, simulation = run_engine(stream)
    game_summary = summarize(game_values)
    dynamic_reference = game_values[game_values.policy.eq("dynamic")][
        ["scenario", "game_pk", "team_id", "W1", "W2"]
    ].rename(columns={"W1": "dynamic_W1", "W2": "dynamic_W2"})
    dominance = game_values.merge(
        dynamic_reference,
        on=["scenario", "game_pk", "team_id"],
        how="left",
        validate="many_to_one",
    )
    threshold_columns = [
        "challenge_threshold_inventory_1", "challenge_threshold_inventory_2"
    ]
    conditions = {
        "observed_legal_decisions_reconcile": population["observed_legal_decisions"] == 312_228,
        "team_games_reconcile": population["team_games"] == 4_390,
        "exhausted_opportunities_retained": population["exhausted_future_opportunities"] > 0,
        "canonical_values_finite": population["nonfinite_canonical_values"] == 0,
        "canonical_values_nonnegative": population["negative_canonical_values"] == 0,
        "simulation_matches_recursion": simulation["within_four_standard_errors"],
        "marginal_values_nonnegative": bool((game_values[["C1", "C2"]] >= -TOLERANCE).all().all()),
        "dynamic_policy_dominates_fixed": bool(
            (dominance.dynamic_W1 + TOLERANCE >= dominance.W1).all()
            and (dominance.dynamic_W2 + TOLERANCE >= dominance.W2).all()
        ),
        "threshold_rows_reconcile": len(thresholds) == 312_228,
        "thresholds_finite_and_bounded": bool(
            np.isfinite(thresholds[threshold_columns]).all().all()
            and (thresholds[threshold_columns] >= -TOLERANCE).all().all()
            and (thresholds[threshold_columns] <= 1 + TOLERANCE).all().all()
        ),
        "regulation_zero_inventory_has_zero_value": bool(
            (game_values.loc[game_values.max_inning <= 9, "W0"].abs() <= TOLERANCE).all()
        ),
    }
    dynamic_games = game_values[game_values.policy.eq("dynamic")]
    validation = {
        "gate": "G7_DYNAMIC_ENGINE",
        "build_status": "PASS" if all(conditions.values()) else "FAIL",
        "scientific_status": "RESTRICTED_DELTAW_ZERO_BY_CONSTRUCTION",
        "conditions": conditions,
        "population": population,
        "simulation": simulation,
        "dynamic_marginal_value": {
            "C2_le_C1_rate": float((dynamic_games.C2 <= dynamic_games.C1 + TOLERANCE).mean()),
            "C2_greater_than_C1_team_games": int((dynamic_games.C2 > dynamic_games.C1 + TOLERANCE).sum()),
        },
        "restrictions": {
            "deltaW": "zero by construction; not demonstrated negligible",
            "opponent_response": "not modeled",
            "game_path_after_correction": "held to observed empirical sequence",
            "player_probability": "assumption or G6 benchmark only",
            "playbook_allowed": False,
        },
    }

    outputs = {
        "game_values.csv": game_values,
        "threshold_rows.csv": thresholds,
        "game_summary.csv": game_summary,
        "threshold_summary.csv": threshold_summary,
    }
    for name, frame in outputs.items():
        frame.to_csv(output / name, index=False, float_format="%.10g", lineterminator="\n")
    write_json(output / "validation.json", validation)
    (output / "VALIDATION.md").write_text(render_report(validation))
    artifact_paths = [output / name for name in outputs] + [output / "validation.json", output / "VALIDATION.md"]
    input_paths = [
        root / "data/full_season/processed/pitches.csv",
        root / "data/full_season/processed/challenges.csv",
        root / "research/article4/output/article4_re288_table.csv",
        root / "research/article5/PREREGISTRATION.md",
        root / "research/article5/DYNAMIC_ENGINE_SPEC.md",
    ]
    manifest = {
        "version": VERSION,
        "build_status": validation["build_status"],
        "scientific_status": validation["scientific_status"],
        "code_sha256": {
            "build_dynamic_engine.py": sha256(Path(__file__)),
            "dynamic_core.py": sha256(HERE / "dynamic_core.py"),
        },
        "inputs": {str(path.relative_to(root)): sha256(path) for path in input_paths},
        "outputs": {path.name: {"sha256": sha256(path), "bytes": path.stat().st_size} for path in artifact_paths},
        "software": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
        "seed": SEED,
    }
    write_json(output / "manifest.json", manifest)
    print(json.dumps({"build_status": validation["build_status"], "scientific_status": validation["scientific_status"]}, sort_keys=True))
    return 0 if validation["build_status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
