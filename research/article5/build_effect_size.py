"""Build the preregistered ABS-05 Gate G9 effect-size audit."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

HERE = Path(__file__).resolve().parent
ROOT_DEFAULT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from build_dynamic_engine import prepare_stream, scenario_probability  # noqa: E402
from dynamic_core import backward_values  # noqa: E402
from effect_size_core import (  # noqa: E402
    cluster_bootstrap_effect,
    evaluate_inventory_policy,
    static_cost_actions,
)
from validate_probability import fit_glm, load_populations  # noqa: E402

SEED = 20260925
BOOTSTRAP_REPETITIONS = 10_000
TOLERANCE = 1e-9
VERSION = "abs_article5_effect_size_v1"
SCENARIOS = [
    "fixed_0.50",
    "fixed_0.60",
    "fixed_0.70",
    "public_tracking",
    "selected_transport",
    "shuffled_public",
]
SIMPLE_POLICIES = [
    "never",
    "confidence_0.5",
    "confidence_0.6",
    "confidence_0.7",
    "ev_0.05",
    "static_article4",
]
ALL_POLICIES = SIMPLE_POLICIES + ["dynamic_exact_sequence"]


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


def shuffled_probability(root: Path, stream: pd.DataFrame) -> tuple[np.ndarray, dict]:
    public, _, _ = load_populations(root)
    rng = np.random.default_rng(SEED)
    shuffled = public.copy()
    shuffled["target"] = rng.permutation(shuffled.target.to_numpy())
    model = fit_glm(shuffled)
    training_prediction = np.clip(model.predict(shuffled).to_numpy(), 1e-6, 1 - 1e-6)
    auc = float(roc_auc_score(shuffled.target, training_prediction))
    valid = stream[["absd", "edge", "side", "terminal"]].notna().all(axis=1)
    prediction = np.repeat(float(shuffled.target.mean()), len(stream))
    prediction[valid.to_numpy()] = np.clip(
        model.predict(stream.loc[valid]).to_numpy(), 1e-6, 1 - 1e-6
    )
    return prediction, {
        "seed": SEED,
        "training_rows": len(shuffled),
        "shuffled_positive_rate": float(shuffled.target.mean()),
        "in_sample_auc_on_shuffled_labels": auc,
        "auc_required_range": [0.48, 0.52],
        "auc_condition_pass": 0.48 <= auc <= 0.52,
        "stream_probability_mean": float(prediction.mean()),
        "stream_probability_min": float(prediction.min()),
        "stream_probability_max": float(prediction.max()),
    }


def load_static_costs(root: Path) -> dict:
    table = pd.read_csv(
        root / "research/article4/decision_value/output/article4_inventory_option_value.csv"
    )
    costs = {}
    for row in table.itertuples(index=False):
        costs[(int(row.inning), str(row.half), str(row.role))] = (
            float(row.OV1_league_behavior),
            float(row.M2_league_behavior),
        )
    return costs


def static_cost_arrays(group: pd.DataFrame, costs: dict) -> tuple[np.ndarray, np.ndarray]:
    one, two = [], []
    for inning, half, role in zip(group.inning, group.half_inning, group.team_role):
        key = (min(int(inning), 10), str(half), str(role))
        if key not in costs:
            raise KeyError(f"missing Article 4 static cost: {key}")
        c1, c2 = costs[key]
        one.append(c1)
        two.append(c2)
    return np.asarray(one), np.asarray(two)


def run_policies(
    stream: pd.DataFrame,
    shuffled: np.ndarray,
    static_costs: dict,
) -> pd.DataFrame:
    rows = []
    groups = list(stream.groupby(["game_pk", "team_id"], sort=True))
    shuffled_series = pd.Series(shuffled, index=stream.index)
    for scenario in SCENARIOS:
        for (game_pk, team_id), group in groups:
            p = (
                shuffled_series.loc[group.index].to_numpy(dtype=float)
                if scenario == "shuffled_public"
                else scenario_probability(group, scenario)
            )
            value = group.correction_value.to_numpy(dtype=float)
            innings = group.inning.to_numpy(dtype=int)
            c1, c2 = static_cost_arrays(group, static_costs)
            for policy in SIMPLE_POLICIES:
                if policy == "static_article4":
                    actions = static_cost_actions(p, value, c1, c2)
                    W = evaluate_inventory_policy(p, value, innings, actions)
                else:
                    W = backward_values(p, value, innings, policy)["W"]
                rows.append({
                    "scenario": scenario,
                    "policy": policy,
                    "game_pk": int(game_pk),
                    "team_id": int(team_id),
                    "team_role": str(group.team_role.iloc[0]),
                    "opportunities": len(group),
                    "W1": float(W[1, 0]),
                    "W2": float(W[2, 0]),
                })
            dynamic = backward_values(p, value, innings, "dynamic")["W"]
            rows.append({
                "scenario": scenario,
                "policy": "dynamic_exact_sequence",
                "game_pk": int(game_pk),
                "team_id": int(team_id),
                "team_role": str(group.team_role.iloc[0]),
                "opportunities": len(group),
                "W1": float(dynamic[1, 0]),
                "W2": float(dynamic[2, 0]),
            })
    return pd.DataFrame(rows)


def summarize(team_values: pd.DataFrame) -> pd.DataFrame:
    return (
        team_values.groupby(["scenario", "policy"], sort=True)
        .agg(
            team_games=("game_pk", "size"),
            mean_W1=("W1", "mean"),
            mean_W2=("W2", "mean"),
            median_W1=("W1", "median"),
            median_W2=("W2", "median"),
        )
        .reset_index()
    )


def effect_table(team_values: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scenario_index, scenario in enumerate(SCENARIOS):
        frame = team_values[team_values.scenario.eq(scenario)]
        for inventory in (1, 2):
            column = f"W{inventory}"
            game_policy = (
                frame.groupby(["game_pk", "policy"], sort=True)[column]
                .mean()
                .unstack("policy")
            )
            dynamic = game_policy["dynamic_exact_sequence"].to_numpy()
            simple = game_policy[SIMPLE_POLICIES].to_numpy()
            result = cluster_bootstrap_effect(
                dynamic,
                simple,
                BOOTSTRAP_REPETITIONS,
                SEED + scenario_index * 10 + inventory,
            )
            simple_means = game_policy[SIMPLE_POLICIES].mean()
            best = str(simple_means.idxmax())
            rows.append({
                "scenario": scenario,
                "inventory": inventory,
                "games": len(game_policy),
                "team_games": len(frame[frame.policy.eq("dynamic_exact_sequence")]),
                "dynamic_mean": float(game_policy.dynamic_exact_sequence.mean()),
                "best_simple_policy": best,
                "best_simple_mean": float(simple_means.loc[best]),
                "effect_dynamic_minus_best_simple": result["point"],
                "lower_95": result["lower_95"],
                "upper_95": result["upper_95"],
                "bootstrap_repetitions": result["repetitions"],
                "numerical_condition_pass": bool(
                    result["point"] >= 0.01 and result["lower_95"] > 0
                ),
            })
    return pd.DataFrame(rows)


def descriptive_benchmarks(root: Path, stream: pd.DataFrame) -> pd.DataFrame:
    observed = pd.read_csv(
        root / "data/full_season/processed/pitches.csv",
        usecols=["pitch_key", "derived_abs_call", "challenged", "challenge_outcome"],
        low_memory=False,
    )
    merged = stream.merge(observed, on="pitch_key", how="left", validate="one_to_one")
    challenged = _bool(merged.challenged).fillna(False)
    corrected = challenged & merged.challenge_outcome.eq("OVERTURNED")
    incorrect = merged.derived_abs_call.notna() & merged.original_call.ne(merged.derived_abs_call)
    merged["observed_realized_corrected_value"] = np.where(
        corrected, merged.correction_value, 0.0
    )
    merged["hindsight_oracle_value"] = np.where(
        incorrect, merged.correction_value, 0.0
    )
    merged["incorrect_opportunity"] = incorrect.astype(int)
    merged["unknown_abs_call"] = merged.derived_abs_call.isna().astype(int)
    return (
        merged.groupby(["game_pk", "team_id"], sort=True)
        .agg(
            observed_realized_corrected_value=("observed_realized_corrected_value", "sum"),
            hindsight_oracle_value=("hindsight_oracle_value", "sum"),
            observed_challenges=("challenged", lambda x: int(_bool(x).fillna(False).sum())),
            incorrect_opportunities=("incorrect_opportunity", "sum"),
            unknown_abs_calls=("unknown_abs_call", "sum"),
        )
        .reset_index()
    )


def render_report(validation: dict, effects: pd.DataFrame) -> str:
    primary = effects[(effects.scenario == "fixed_0.60") & (effects.inventory == 2)].iloc[0]
    shuffled = effects[(effects.scenario == "shuffled_public") & (effects.inventory == 2)].iloc[0]
    return "\n".join([
        "# ABS-05 Gate G9 Effect-Size Validation",
        "",
        "Generated by `build_effect_size.py`; do not hand-edit.",
        "",
        f"**Build status: {validation['build_status']}**",
        f"**Numerical benchmark condition: {validation['numerical_benchmark_condition']}**",
        f"**Scientific G9 status: {validation['scientific_status']}**",
        "",
        "## Primary upper benchmark",
        "",
        f"At fixed p=0.60 with two units, exact-sequence dynamic value exceeded the best simple policy ({primary.best_simple_policy}) by {primary.effect_dynamic_minus_best_simple:.6f} expected runs per team-game (95% cluster-bootstrap interval {primary.lower_95:.6f} to {primary.upper_95:.6f}).",
        "",
        "## Falsification",
        "",
        f"The shuffled-label model had AUC {validation['shuffle']['in_sample_auc_on_shuffled_labels']:.6f}. Its exact-sequence advantage was {shuffled.effect_dynamic_minus_best_simple:.6f} ({shuffled.lower_95:.6f} to {shuffled.upper_95:.6f}).",
        "",
        "## Interpretation boundary",
        "",
        "The dynamic policy sees the complete remaining empirical opportunity sequence. G6 did not identify player confidence, G8 rejected the win-probability model, and corrected calls do not rewrite the observed future path. The numerical result is therefore a nondeployable upper benchmark and does not support a situational playbook.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve() if args.output else root / "research/article5/output/g9"
    output.mkdir(parents=True, exist_ok=True)

    stream, population = prepare_stream(root)
    shuffled, shuffle_audit = shuffled_probability(root, stream)
    static_costs = load_static_costs(root)
    team_values = run_policies(stream, shuffled, static_costs)
    policy_summary = summarize(team_values)
    effects = effect_table(team_values)
    descriptive = descriptive_benchmarks(root, stream)

    dynamic = team_values[team_values.policy.eq("dynamic_exact_sequence")][
        ["scenario", "game_pk", "team_id", "W1", "W2"]
    ].rename(columns={"W1": "dynamic_W1", "W2": "dynamic_W2"})
    dominance = team_values.merge(
        dynamic, on=["scenario", "game_pk", "team_id"], how="left", validate="many_to_one"
    )
    primary = effects[(effects.scenario == "fixed_0.60") & (effects.inventory == 2)].iloc[0]
    shuffled_effect = effects[(effects.scenario == "shuffled_public") & (effects.inventory == 2)].iloc[0]
    conditions = {
        "observed_legal_decisions_reconcile": population["observed_legal_decisions"] == 312_228,
        "team_games_reconcile": population["team_games"] == 4_390,
        "all_scenario_policy_team_games_present": len(team_values) == len(SCENARIOS) * len(ALL_POLICIES) * 4_390,
        "game_clusters_reconcile": team_values.game_pk.nunique() == 2_195,
        "static_lookup_complete": len(static_costs) == 40,
        "values_finite": bool(np.isfinite(team_values[["W1", "W2"]]).all().all()),
        "values_nonnegative": bool((team_values[["W1", "W2"]] >= -TOLERANCE).all().all()),
        "dynamic_dominates_simple": bool(
            (dominance.dynamic_W1 + TOLERANCE >= dominance.W1).all()
            and (dominance.dynamic_W2 + TOLERANCE >= dominance.W2).all()
        ),
        "shuffle_auc_in_falsification_range": shuffle_audit["auc_condition_pass"],
        "descriptive_team_games_reconcile": len(descriptive) == 4_390,
        "descriptive_unknown_abs_calls_retained_as_unknown": int(
            descriptive.unknown_abs_calls.sum()
        ) == 172,
        "bootstrap_rows_complete": len(effects) == len(SCENARIOS) * 2,
    }
    numerical = bool(primary.numerical_condition_pass)
    shuffle_persists = bool(shuffled_effect.numerical_condition_pass)
    validation = {
        "gate": "G9_EFFECT_SIZE",
        "build_status": "PASS" if all(conditions.values()) else "FAIL",
        "numerical_benchmark_condition": "PASS" if numerical else "FAIL",
        "scientific_status": "NOT_DEMONSTRATED_NONDEPLOYABLE_UPPER_BENCHMARK",
        "conditions": conditions,
        "population": population,
        "primary": primary.to_dict(),
        "shuffle": {**shuffle_audit, "numerical_advantage_persists": shuffle_persists},
        "restrictions": {
            "dynamic_information": "complete remaining empirical sequence; unavailable at decision time",
            "player_probability": "not identified by G6",
            "win_probability": "G8 model rejected and not reused",
            "game_path_after_correction": "held to observed empirical sequence",
            "observed_and_oracle": "descriptive only; excluded from comparator set",
            "playbook_allowed": False,
        },
    }

    outputs = {
        "team_game_values.csv": team_values,
        "policy_summary.csv": policy_summary,
        "effect_size.csv": effects,
        "descriptive_benchmarks.csv": descriptive,
    }
    for name, frame in outputs.items():
        frame.to_csv(output / name, index=False, float_format="%.10g", lineterminator="\n")
    write_json(output / "shuffle_diagnostic.json", validation["shuffle"])
    write_json(output / "validation.json", validation)
    (output / "VALIDATION.md").write_text(render_report(validation, effects))
    artifact_paths = [output / name for name in outputs] + [
        output / "shuffle_diagnostic.json",
        output / "validation.json",
        output / "VALIDATION.md",
    ]
    input_paths = [
        root / "data/full_season/processed/pitches.csv",
        root / "data/full_season/processed/challenges.csv",
        root / "research/article4/output/article4_re288_table.csv",
        root / "research/article4/decision_value/output/article4_inventory_option_value.csv",
        root / "research/article5/PREREGISTRATION.md",
        root / "research/article5/EFFECT_SIZE_SPEC.md",
    ]
    manifest = {
        "version": VERSION,
        "build_status": validation["build_status"],
        "numerical_benchmark_condition": validation["numerical_benchmark_condition"],
        "scientific_status": validation["scientific_status"],
        "code_sha256": {
            "build_effect_size.py": sha256(Path(__file__)),
            "effect_size_core.py": sha256(HERE / "effect_size_core.py"),
            "dynamic_core.py": sha256(HERE / "dynamic_core.py"),
        },
        "inputs": {str(path.relative_to(root)): sha256(path) for path in input_paths},
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
        "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
    }
    write_json(output / "manifest.json", manifest)
    print(json.dumps({
        "build_status": validation["build_status"],
        "numerical_benchmark_condition": validation["numerical_benchmark_condition"],
        "scientific_status": validation["scientific_status"],
    }, sort_keys=True))
    return 0 if validation["build_status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
