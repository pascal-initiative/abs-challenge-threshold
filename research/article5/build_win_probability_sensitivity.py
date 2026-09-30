"""Build the post-failure ABS-05 G8 objective-scale follow-up."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import log_loss, roc_auc_score

HERE = Path(__file__).resolve().parent
ROOT_DEFAULT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "article4"))
from build_correction_values import build_constrained_table, lookup_from_table  # noqa: E402
from build_dynamic_engine import prepare_stream  # noqa: E402
from counterfactual import apply_call  # noqa: E402
from stability_core import dynamic_values  # noqa: E402
from win_probability_core import (  # noqa: E402
    fit_phase_logistic,
    opponent_adjusted_delta,
    predict_phase,
)

VERSION = "abs_article5_g8_win_probability_v1"
PENALTY = 1e-4
TOLERANCE = 1e-9
ALLOWED_FEATURES = {"inning_phase", "home_state_advantage"}
BLACKLIST = {
    "derived_abs_call", "official_abs_call", "challenge_outcome", "challenged",
    "distance_from_abs_boundary", "plate_x", "plate_z", "realized_future_runs",
}


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
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(type(value))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=_json_default) + "\n")


def validate_features(features: set[str]) -> None:
    if features & BLACKLIST:
        raise ValueError(f"blacklisted features: {sorted(features & BLACKLIST)}")
    if features != ALLOWED_FEATURES:
        raise ValueError(f"feature set must equal {sorted(ALLOWED_FEATURES)}")


def final_home_wins(root: Path, pitches: pd.DataFrame) -> tuple[dict[int, int], dict]:
    objects = root / "data/full_season/raw/objects"
    games = pitches[["game_pk", "source_game_feed"]].drop_duplicates()
    if games.game_pk.duplicated().any() or games.source_game_feed.isna().any():
        raise RuntimeError("game-feed mapping is not one-to-one and complete")
    outcomes = {}
    ties, nonfinal = [], []
    for row in games.sort_values("game_pk").itertuples(index=False):
        payload = json.loads((objects / row.source_game_feed).read_text())
        status = payload["gameData"]["status"]["abstractGameState"]
        scores = payload["liveData"]["linescore"]["teams"]
        home, away = int(scores["home"]["runs"]), int(scores["away"]["runs"])
        if status != "Final":
            nonfinal.append(int(row.game_pk))
        elif home == away:
            ties.append(int(row.game_pk))
        else:
            outcomes[int(row.game_pk)] = int(home > away)
    return outcomes, {
        "games": len(games),
        "labeled_games": len(outcomes),
        "tied_games": ties,
        "nonfinal_games": nonfinal,
        "home_win_rate": float(np.mean(list(outcomes.values()))) if outcomes else np.nan,
    }


def training_population(root: Path, re_lookup: dict) -> tuple[pd.DataFrame, dict]:
    columns = [
        "pitch_key", "game_pk", "game_date", "source_game_feed", "inning",
        "half_inning", "home_score", "away_score", "balls", "strikes", "outs",
        "on_1b", "on_2b", "on_3b",
    ]
    pitches = pd.read_csv(
        root / "data/full_season/processed/pitches.csv",
        usecols=columns,
        low_memory=False,
    )
    outcomes, outcome_audit = final_home_wins(root, pitches)
    pitches["home_win"] = pitches.game_pk.map(outcomes)
    pitches["base_state"] = (
        pitches.on_1b.notna().astype(int).astype(str)
        + pitches.on_2b.notna().astype(int).astype(str)
        + pitches.on_3b.notna().astype(int).astype(str)
    )
    state_valid = (
        pitches.balls.between(0, 3)
        & pitches.strikes.between(0, 2)
        & pitches.outs.between(0, 2)
        & pitches.home_win.notna()
    )
    frame = pitches[state_valid].copy()
    keys = zip(frame.balls, frame.strikes, frame.outs, frame.base_state)
    frame["remaining_re"] = [
        re_lookup[(int(b), int(s), int(o), str(base))] for b, s, o, base in keys
    ]
    sign = np.where(frame.half_inning.eq("bottom"), 1.0, -1.0)
    frame["home_state_advantage"] = (
        frame.home_score - frame.away_score + sign * frame.remaining_re
    )
    frame["month"] = frame.game_date.astype(str).str[:7]
    frame["late_close"] = frame.inning.ge(7) & (frame.home_score - frame.away_score).abs().le(1)
    counts = frame.groupby("game_pk").pitch_key.transform("size")
    frame["game_weight"] = 1.0 / counts
    audit = {
        **outcome_audit,
        "pitch_rows": len(pitches),
        "model_rows": len(frame),
        "excluded_invalid_state_or_outcome": len(pitches) - len(frame),
        "start_date": str(frame.game_date.min()),
        "end_date": str(frame.game_date.max()),
    }
    return frame.reset_index(drop=True), audit


def weighted_metrics(target, prediction, weights) -> dict:
    target = np.asarray(target, dtype=int)
    prediction = np.clip(np.asarray(prediction, dtype=float), 1e-6, 1 - 1e-6)
    weights = np.asarray(weights, dtype=float)
    weights = weights / weights.sum()
    brier = float(np.sum(weights * np.square(target - prediction)))
    loss = float(log_loss(target, prediction, sample_weight=weights, labels=[0, 1]))
    auc = float(roc_auc_score(target, prediction, sample_weight=weights)) if len(set(target)) > 1 else np.nan
    logits = np.log(prediction / (1 - prediction))
    try:
        calibration = sm.GLM(
            target,
            sm.add_constant(logits),
            family=sm.families.Binomial(),
            freq_weights=weights * len(weights),
        ).fit()
        intercept_only = sm.GLM(
            target,
            np.ones_like(logits),
            offset=logits,
            family=sm.families.Binomial(),
            freq_weights=weights * len(weights),
        ).fit()
        intercept = float(intercept_only.params[0])
        slope = float(calibration.params[1])
    except Exception:
        intercept, slope = np.nan, np.nan
    bins = np.minimum((prediction * 10).astype(int), 9)
    ece = 0.0
    for value in range(10):
        mask = bins == value
        if mask.any():
            group_weight = float(weights[mask].sum())
            observed = float(np.average(target[mask], weights=weights[mask]))
            estimated = float(np.average(prediction[mask], weights=weights[mask]))
            ece += group_weight * abs(observed - estimated)
    return {
        "rows": len(target),
        "positives": int(target.sum()),
        "negatives": int(len(target) - target.sum()),
        "weighted_base_rate": float(np.average(target, weights=weights)),
        "weighted_mean_prediction": float(np.average(prediction, weights=weights)),
        "brier": brier,
        "log_loss": loss,
        "roc_auc": auc,
        "calibration_intercept": intercept,
        "calibration_slope": slope,
        "ece_10bin": ece,
    }


def rolling_predictions(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    validate_features(set(ALLOWED_FEATURES))
    pieces, fits = [], []
    months = sorted(frame.month.unique())
    for month in months[1:]:
        train_mask = frame.month.lt(month).to_numpy()
        test_mask = frame.month.eq(month).to_numpy()
        if not train_mask.any() or not test_mask.any():
            continue
        model = fit_phase_logistic(
            frame.loc[train_mask, "inning"],
            frame.loc[train_mask, "half_inning"],
            frame.loc[train_mask, "home_state_advantage"],
            frame.loc[train_mask, "home_win"],
            frame.loc[train_mask, "game_weight"],
            PENALTY,
        )
        prediction = np.clip(predict_phase(
            model,
            frame.loc[test_mask, "inning"],
            frame.loc[test_mask, "half_inning"],
            frame.loc[test_mask, "home_state_advantage"],
        ), 1e-6, 1 - 1e-6)
        train_base = float(np.average(
            frame.loc[train_mask, "home_win"],
            weights=frame.loc[train_mask, "game_weight"],
        ))
        out = frame.loc[test_mask, [
            "pitch_key", "game_pk", "game_date", "month", "inning", "half_inning",
            "home_score", "away_score", "late_close", "home_win", "game_weight",
        ]].copy()
        out["prediction"] = prediction
        out["baseline_prediction"] = train_base
        out["train_end"] = str(frame.loc[train_mask, "game_date"].max())
        pieces.append(out)
        fits.append({
            "test_month": month,
            "train_rows": int(train_mask.sum()),
            "test_rows": int(test_mask.sum()),
            "train_end": str(frame.loc[train_mask, "game_date"].max()),
            "objective": model["objective"],
            "iterations": model["iterations"],
            "minimum_advantage_slope": model["minimum_advantage_slope"],
        })
    return pd.concat(pieces, ignore_index=True), fits


def calibration_table(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dimension, level, group in [
        ("OVERALL", "ALL", predictions),
        ("late_close", "True", predictions[predictions.late_close]),
        ("late_close", "False", predictions[~predictions.late_close]),
    ]:
        metrics = weighted_metrics(group.home_win, group.prediction, group.game_weight)
        baseline = weighted_metrics(group.home_win, group.baseline_prediction, group.game_weight)
        rows.append({
            "dimension": dimension,
            "level": level,
            **metrics,
            "baseline_brier": baseline["brier"],
            "baseline_log_loss": baseline["log_loss"],
            "delta_brier_vs_expanding_base_rate": metrics["brier"] - baseline["brier"],
            "delta_log_loss_vs_expanding_base_rate": metrics["log_loss"] - baseline["log_loss"],
        })
    return pd.DataFrame(rows)


def successor_descriptor(row, call: str, re_lookup: dict) -> tuple[bool, float, int, str, float]:
    occupied = {base for base, flag in zip(("1B", "2B", "3B"), str(row.base_state)) if flag == "1"}
    state = apply_call(int(row.balls), int(row.strikes), int(row.outs), occupied, call)
    home_score, away_score = int(row.home_score), int(row.away_score)
    if row.half_inning == "top":
        away_score += int(state.runs)
    else:
        home_score += int(state.runs)

    if row.half_inning == "bottom" and int(row.inning) >= 9 and home_score > away_score:
        return True, 1.0, int(row.inning), "bottom", np.nan

    if state.inning_ended:
        if row.half_inning == "top":
            if int(row.inning) >= 9 and home_score > away_score:
                return True, 1.0, int(row.inning), "top", np.nan
            inning, half = int(row.inning), "bottom"
        else:
            if int(row.inning) >= 9 and home_score != away_score:
                return True, float(home_score > away_score), int(row.inning), "bottom", np.nan
            inning, half = int(row.inning) + 1, "top"
        remaining = re_lookup[(0, 0, 0, "000")]
    else:
        inning, half = int(row.inning), row.half_inning
        remaining = re_lookup[(state.balls, state.strikes, state.outs, state.base_state)]
    sign = 1.0 if half == "bottom" else -1.0
    advantage = home_score - away_score + sign * remaining
    return False, np.nan, inning, half, float(advantage)


def counterfactual_win_values(stream: pd.DataFrame, model: dict, re_lookup: dict) -> tuple[np.ndarray, pd.DataFrame]:
    descriptors = []
    for row in stream.itertuples(index=False):
        corrected_call = "STRIKE" if row.original_call == "BALL" else "BALL"
        descriptors.append((
            successor_descriptor(row, row.original_call, re_lookup),
            successor_descriptor(row, corrected_call, re_lookup),
        ))
    flat = [descriptor for pair in descriptors for descriptor in pair]
    nonterminal = np.asarray([not descriptor[0] for descriptor in flat])
    probabilities = np.asarray([descriptor[1] for descriptor in flat], dtype=float)
    if nonterminal.any():
        innings = [flat[i][2] for i in np.flatnonzero(nonterminal)]
        halves = [flat[i][3] for i in np.flatnonzero(nonterminal)]
        advantages = [flat[i][4] for i in np.flatnonzero(nonterminal)]
        probabilities[nonterminal] = predict_phase(model, innings, halves, advantages)
    observed = probabilities[0::2]
    corrected = probabilities[1::2]
    phase_crossing = np.asarray([
        pair[0][0] != pair[1][0]
        or pair[0][2] != pair[1][2]
        or pair[0][3] != pair[1][3]
        for pair in descriptors
    ])
    home_delta = corrected - observed
    oriented = np.where(stream.team_role.eq("HOME"), home_delta, -home_delta)
    diagnostics = pd.DataFrame({
        "pitch_key": stream.pitch_key,
        "game_pk": stream.game_pk,
        "observed_legal_decision": stream.observed_legal_decision,
        "run_correction_value": stream.correction_value,
        "wp_call_stands": observed,
        "wp_corrected": corrected,
        "wp_correction_value": oriented,
        "counterfactual_crosses_phase": phase_crossing,
    })
    return oriented, diagnostics


def action_comparison(stream: pd.DataFrame, wp_value: np.ndarray) -> tuple[pd.DataFrame, dict]:
    legal = stream.observed_legal_decision.to_numpy(dtype=bool)
    cutoff = float(stream.loc[legal, "correction_value"].quantile(0.90, interpolation="linear"))
    top = legal & stream.correction_value.ge(cutoff).to_numpy()
    reference = {inventory: np.zeros(len(stream), dtype=bool) for inventory in (1, 2)}
    win_scale = {inventory: np.zeros(len(stream), dtype=bool) for inventory in (1, 2)}
    for _, group in stream.groupby(["game_pk", "team_id"], sort=True):
        loc = group.index.to_numpy(dtype=int)
        p = np.repeat(0.60, len(group))
        run_solution = dynamic_values(p, group.correction_value, group.inning)
        wp_solution = dynamic_values(p, wp_value[loc], group.inning)
        for inventory in (1, 2):
            reference[inventory][loc] = run_solution["action"][inventory]
            win_scale[inventory][loc] = wp_solution["action"][inventory]
    rows = []
    detail = stream.loc[top, [
        "pitch_key", "game_pk", "game_date", "team_id", "inning", "half_inning",
        "team_score_diff", "count", "outs", "base_state", "side", "correction_value",
    ]].copy()
    detail["wp_correction_value"] = wp_value[top]
    for inventory in (1, 2):
        ref = reference[inventory][top]
        other = win_scale[inventory][top]
        detail[f"run_action_inventory_{inventory}"] = ref
        detail[f"win_action_inventory_{inventory}"] = other
        rows.append({
            "sensitivity": "win_probability_fixed_path",
            "inventory": inventory,
            "denominator": int(top.sum()),
            "reference_challenges": int(ref.sum()),
            "sensitivity_challenges": int(other.sum()),
            "flips": int((ref != other).sum()),
            "flip_rate": float((ref != other).mean()),
            "passes_10_percent": bool((ref != other).mean() <= 0.10 + TOLERANCE),
        })
    return detail, {"cutoff": cutoff, "rows": int(top.sum()), "summary": rows}


def opponent_invariance() -> dict:
    rng = np.random.default_rng(20260925)
    challenge = rng.normal(size=10_000)
    hold = rng.normal(size=10_000)
    typical = rng.normal(size=10_000)
    optimized = typical + np.abs(rng.normal(size=10_000))
    base = challenge - hold
    typical_delta = opponent_adjusted_delta(challenge, hold, typical)
    optimized_delta = opponent_adjusted_delta(challenge, hold, optimized)
    return {
        "comparisons": len(base),
        "league_typical_max_absolute_difference": float(np.max(np.abs(base - typical_delta))),
        "optimized_max_absolute_difference": float(np.max(np.abs(base - optimized_delta))),
        "league_typical_action_changes": int(((base > 0) != (typical_delta > 0)).sum()),
        "optimized_action_changes": int(((base > 0) != (optimized_delta > 0)).sum()),
        "scope": "G7 independent fixed-path additive model only",
    }


def render_report(validation: dict) -> str:
    overall = validation["rolling_calibration"]["overall"]
    late = validation["rolling_calibration"]["late_close"]
    flips = (
        validation["win_scale_action_flips"]
        or validation["diagnostic_action_flips_if_model_invalid"]
    )
    flip_label = (
        "accepted sensitivity" if validation["win_scale_action_flips"]
        else "diagnostic only; model failed validation"
    )
    return "\n".join([
        "# ABS-05 G8 Objective-Scale Follow-up",
        "",
        "Generated by `build_win_probability_sensitivity.py`; do not hand-edit.",
        "",
        f"**Computational status: {validation['computational_status']}**",
        f"**Win-probability sensitivity: {validation['win_probability_status']}**",
        f"**Opponent policy accounting: {validation['opponent_policy_status']}**",
        "**Original G8 stability gate: FAILED (unchanged)**",
        "**Playbook allowed: False**",
        "",
        "## Rolling-origin validation",
        "",
        f"- Overall Brier {overall['brier']:.6f} vs baseline {overall['baseline_brier']:.6f}; AUC {overall['roc_auc']:.4f}; ECE {overall['ece_10bin']:.4f}.",
        f"- Overall calibration intercept {overall['calibration_intercept']:.4f}; slope {overall['calibration_slope']:.4f}.",
        f"- Late/close rows {late['rows']:,}; Brier {late['brier']:.6f}; ECE {late['ece_10bin']:.4f}.",
        "",
        "## Objective-scale action sensitivity",
        "",
        f"These comparisons are {flip_label}.",
        "",
        *[
            f"- Inventory {row['inventory']}: {row['flips']:,}/{row['denominator']:,} flips ({row['flip_rate']:.2%}); 10% condition {'passes' if row['passes_10_percent'] else 'fails'}."
            for row in flips
        ],
        "",
        "## Opponent-policy accounting",
        "",
        "Within G7's independent fixed-path additive model, the opponent value is the same term under CHALLENGE and HOLD and cancels from the focal action difference. Executable checks cover league-typical and optimized opponent values. This is not a coupled opponent-response model and does not resolve deltaW.",
        "",
        "## Interpretation",
        "",
        "This follow-up cannot reverse the previously observed G8 instability. Win-probability results are a fixed-observed-path additive sensitivity, not situational player guidance. The Pascal ABS Challenge Playbook remains prohibited.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve() if args.output else root / "research/article5/output/g8_wp"
    output.mkdir(parents=True, exist_ok=True)

    input_paths = [
        root / "data/full_season/processed/pitches.csv",
        root / "data/full_season/processed/challenges.csv",
        root / "data/full_season/processed/run_manifest.json",
        root / "research/article4/output/article4_re288_table.csv",
        root / "research/article4/output/manifest.json",
        root / "research/article5/PREREGISTRATION.md",
        root / "research/article5/STABILITY_SPEC.md",
        root / "research/article5/AMENDMENT_002_G8_OBJECTIVE.md",
    ]
    before = {str(path.relative_to(root)): sha256(path) for path in input_paths}
    re_input = pd.read_csv(
        root / "research/article4/output/article4_re288_table.csv",
        dtype={"base_state": str},
    )
    constrained, _ = build_constrained_table(re_input)
    re_lookup = lookup_from_table(constrained)
    training, population = training_population(root, re_lookup)
    rolling, fits = rolling_predictions(training)
    calibration = calibration_table(rolling)
    overall = calibration[calibration.dimension.eq("OVERALL")].iloc[0]
    late = calibration[(calibration.dimension.eq("late_close")) & calibration.level.eq("True")].iloc[0]

    full_model = fit_phase_logistic(
        training.inning,
        training.half_inning,
        training.home_state_advantage,
        training.home_win,
        training.game_weight,
        PENALTY,
    )
    stream, stream_population = prepare_stream(root)
    wp_value, wp_rows = counterfactual_win_values(stream, full_model, re_lookup)
    legal = stream.observed_legal_decision.to_numpy(dtype=bool)
    cutoff = float(stream.loc[legal, "correction_value"].quantile(0.90, interpolation="linear"))
    top = legal & stream.correction_value.ge(cutoff).to_numpy()
    negative = wp_value < -TOLERANCE
    wp_conditions = {
        "all_games_have_unique_final_winner": population["labeled_games"] == 2_195 and not population["tied_games"] and not population["nonfinal_games"],
        "rolling_origin_strictly_prior": bool(rolling.train_end.lt(rolling.game_date.astype(str)).all()),
        "feature_allowlist_passes": True,
        "overall_brier_improves_baseline": bool(overall.brier < overall.baseline_brier),
        "overall_log_loss_improves_baseline": bool(overall.log_loss < overall.baseline_log_loss),
        "overall_ece_at_most_003": bool(overall.ece_10bin <= 0.03),
        "overall_calibration_intercept_bounded": bool(abs(overall.calibration_intercept) <= 0.10),
        "overall_calibration_slope_bounded": bool(0.70 <= overall.calibration_slope <= 1.30),
        "late_close_supported": bool(late.rows >= 500 and late.positives > 0 and late.negatives > 0),
        "late_close_ece_at_most_005": bool(late.ece_10bin <= 0.05),
        "wp_values_finite": bool(np.isfinite(wp_value).all()),
        "negative_wp_values_below_point_one_percent": bool(negative.mean() < 0.001),
        "no_negative_wp_values_in_top_population": not bool(negative[top].any()),
    }
    canary_rejected = False
    try:
        validate_features(ALLOWED_FEATURES | {"challenge_outcome"})
    except ValueError:
        canary_rejected = True
    wp_conditions["leaky_canary_rejected"] = canary_rejected
    wp_status = "PASS_FIXED_PATH_SENSITIVITY" if all(wp_conditions.values()) else "FAIL_VALIDATION"
    detail, action_audit = action_comparison(stream, wp_value)
    opponent = opponent_invariance()
    opponent_pass = (
        opponent["league_typical_max_absolute_difference"] <= TOLERANCE
        and opponent["optimized_max_absolute_difference"] <= TOLERANCE
        and opponent["league_typical_action_changes"] == 0
        and opponent["optimized_action_changes"] == 0
    )
    after = {str(path.relative_to(root)): sha256(path) for path in input_paths}
    computational_conditions = {
        "protected_inputs_unchanged": before == after,
        "training_games_reconcile": population["games"] == 2_195,
        "stream_legal_decisions_reconcile": stream_population["observed_legal_decisions"] == 312_228,
        "stream_team_games_reconcile": stream_population["team_games"] == 4_390,
        "rolling_predictions_nonempty": len(rolling) > 0,
        "opponent_invariance_passes": opponent_pass,
    }
    computational_status = "PASS" if all(computational_conditions.values()) else "FAIL"
    calibration_records = calibration.to_dict("records")
    validation = {
        "gate": "G8_OBJECTIVE_SCALE_FOLLOWUP",
        "computational_status": computational_status,
        "win_probability_status": wp_status,
        "opponent_policy_status": "PASS_SEPARABLE_MODEL_ONLY" if opponent_pass else "FAIL",
        "original_g8_status": "FAILED_UNCHANGED",
        "playbook_allowed": False,
        "computational_conditions": computational_conditions,
        "win_probability_conditions": wp_conditions,
        "population": population,
        "stream_population": stream_population,
        "rolling_fits": fits,
        "rolling_calibration": {
            "overall": next(row for row in calibration_records if row["dimension"] == "OVERALL"),
            "late_close": next(row for row in calibration_records if row["dimension"] == "late_close" and row["level"] == "True"),
        },
        "full_fit": {
            "objective": full_model["objective"],
            "iterations": full_model["iterations"],
            "minimum_advantage_slope": full_model["minimum_advantage_slope"],
            "future_stream_rows": len(stream),
            "negative_wp_values": int(negative.sum()),
            "negative_wp_value_rate": float(negative.mean()),
            "negative_top_value_rows": int(negative[top].sum()),
            "negative_phase_crossing_rows": int(
                (negative & wp_rows.counterfactual_crosses_phase.to_numpy(dtype=bool)).sum()
            ),
            "negative_within_phase_rows": int(
                (negative & ~wp_rows.counterfactual_crosses_phase.to_numpy(dtype=bool)).sum()
            ),
        },
        "win_scale_action_flips": action_audit["summary"] if wp_status.startswith("PASS") else [],
        "diagnostic_action_flips_if_model_invalid": action_audit["summary"] if not wp_status.startswith("PASS") else [],
        "opponent_invariance": opponent,
        "restrictions": {
            "win_probability": "fixed-observed-path additive sensitivity",
            "opponent_policy": "cancels only under separable G7 construction",
            "deltaW": "zero by construction remains unresolved",
            "player_probability": "fixed 0.60 assumption; not identified",
        },
    }

    outputs = {
        "rolling_predictions.csv": rolling,
        "calibration.csv": calibration,
        "wp_correction_values.csv": wp_rows,
        "top_value_wp_actions.csv": detail,
    }
    for name, frame in outputs.items():
        frame.to_csv(output / name, index=False, float_format="%.10g", lineterminator="\n")
    write_json(output / "opponent_invariance.json", opponent)
    write_json(output / "validation.json", validation)
    (output / "VALIDATION.md").write_text(render_report(validation))
    artifacts = [output / name for name in outputs] + [
        output / "opponent_invariance.json", output / "validation.json", output / "VALIDATION.md"
    ]
    manifest = {
        "version": VERSION,
        "computational_status": computational_status,
        "win_probability_status": wp_status,
        "original_g8_status": "FAILED_UNCHANGED",
        "code_sha256": {
            "build_win_probability_sensitivity.py": sha256(Path(__file__)),
            "win_probability_core.py": sha256(HERE / "win_probability_core.py"),
            "build_correction_values.py": sha256(HERE / "build_correction_values.py"),
            "build_dynamic_engine.py": sha256(HERE / "build_dynamic_engine.py"),
            "stability_core.py": sha256(HERE / "stability_core.py"),
            "article4/counterfactual.py": sha256(HERE.parent / "article4/counterfactual.py"),
        },
        "inputs": before,
        "outputs": {path.name: {"sha256": sha256(path), "bytes": path.stat().st_size} for path in artifacts},
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }
    write_json(output / "manifest.json", manifest)
    print(json.dumps({
        "computational_status": computational_status,
        "win_probability_status": wp_status,
        "original_g8_status": "FAILED_UNCHANGED",
    }, sort_keys=True))
    return 0 if computational_status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
