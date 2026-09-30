"""Validate Article 5 probability benchmarks without claiming player knowledge."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import statsmodels
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

START_DATE = "2026-03-25"
END_DATE = "2026-09-09"
EXPECTED_LEGAL = 312_228
EXPECTED_CHALLENGES = 9_485
DISTANCE_MAX = 6.0
MIN_GROUP_N = 500
MIN_GROUP_CLASS = 100
VERSION = "abs_article5_probability_validation_v1"

MODEL_FEATURES = {"absd", "side", "edge", "terminal"}
BENCHMARK_ONLY_FEATURES = {"absd"}
LEAKAGE_BLACKLIST = {
    "signed_boundary_distance", "distance_from_abs_boundary", "plate_x",
    "plate_z", "abs_zone_top", "abs_zone_bot", "derived_abs_call",
    "official_abs_call", "challenge_outcome", "challenged", "incorrect",
    "success", "outcome",
}
FORMULA = (
    "target ~ bs(absd, df=4, lower_bound=0, upper_bound=6.0) * C(side) "
    "+ C(edge) + terminal"
)


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


def validate_feature_set(features: set[str], benchmark: bool) -> None:
    leaked = features & LEAKAGE_BLACKLIST
    if leaked:
        raise ValueError(f"leakage features rejected: {sorted(leaked)}")
    allowed = MODEL_FEATURES if benchmark else MODEL_FEATURES - BENCHMARK_ONLY_FEATURES
    unexpected = features - allowed
    if unexpected:
        raise ValueError(f"features outside allowlist: {sorted(unexpected)}")


def rolling_origin_splits(frame: pd.DataFrame):
    months = sorted(frame.month.unique())
    for month in months[1:]:
        train = frame.index[frame.month < month]
        test = frame.index[frame.month == month]
        if len(train) and len(test):
            yield month, train, test


def _bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().map({"true": True, "false": False})


def load_populations(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    sys.path.insert(0, str(root / "research/article4/decision_value"))
    from dv_core import edge_class

    pitch_path = root / "data/full_season/processed/pitches.csv"
    challenge_path = root / "data/full_season/processed/challenges.csv"
    columns = [
        "pitch_key", "game_pk", "game_date", "inning", "balls", "strikes",
        "original_call", "derived_abs_call", "distance_from_abs_boundary",
        "plate_x", "plate_z", "abs_zone_top", "abs_zone_bot", "bat_side",
        "challenged", "challenge_outcome", "position_player_pitching",
        "affected_team_challenges_remaining",
    ]
    pitches = pd.read_csv(pitch_path, usecols=columns, low_memory=False)
    challenges = pd.read_csv(
        challenge_path,
        usecols=["pitch_key", "outcome", "challenger_role"],
    )
    called = pitches.original_call.isin(["BALL", "STRIKE"])
    position_player = _bool(pitches.position_player_pitching).fillna(False)
    inventory = pd.to_numeric(
        pitches.affected_team_challenges_remaining, errors="coerce"
    ).fillna(0)
    legal = pitches[called & ~position_player & inventory.gt(0)].copy()
    legal["target"] = legal.original_call.ne(legal.derived_abs_call).astype(int)
    legal["absd"] = (
        pd.to_numeric(legal.distance_from_abs_boundary, errors="coerce").abs() * 12
    ).clip(upper=DISTANCE_MAX)
    legal["side"] = np.where(
        legal.original_call.eq("STRIKE"), "OFFENSE", "DEFENSE"
    )
    legal["edge"] = edge_class(
        legal.plate_x, legal.plate_z, legal.abs_zone_top, legal.abs_zone_bot,
        legal.bat_side,
    )
    legal["edge"] = pd.Series(legal.edge, index=legal.index).fillna("UNKNOWN")
    legal["terminal"] = ((legal.balls == 3) | (legal.strikes == 2)).astype(int)
    legal["count"] = legal.balls.astype(int).astype(str) + "-" + legal.strikes.astype(int).astype(str)
    legal["inning_bucket"] = pd.cut(
        legal.inning,
        bins=[0, 3, 6, 9, np.inf],
        labels=["1-3", "4-6", "7-9", "10+"],
    ).astype(str)
    legal["month"] = legal.game_date.astype(str).str[:7]
    legal["challenged_bool"] = _bool(legal.challenged).fillna(False)

    valid = legal[["absd", "edge", "side", "terminal"]].notna().all(axis=1)
    public = legal[valid].copy()
    selected = public[public.challenged_bool].merge(
        challenges, on="pitch_key", how="left", validate="one_to_one"
    )
    selected["target"] = selected.outcome.eq("OVERTURNED").astype(int)
    selected["role"] = selected.challenger_role.fillna("UNKNOWN")
    audit = {
        "pitch_rows": len(pitches),
        "legal_called_pitches": len(legal),
        "public_geometry_rows": len(public),
        "public_geometry_exclusions": len(legal) - len(public),
        "official_challenge_rows": len(challenges),
        "selected_challenge_rows": len(selected),
        "selected_missing_official_outcome": int(selected.outcome.isna().sum()),
        "selected_missing_role": int(selected.challenger_role.isna().sum()),
        "public_start": str(public.game_date.min()),
        "public_end": str(public.game_date.max()),
    }
    return public, selected, audit


def fit_glm(train: pd.DataFrame):
    return smf.glm(FORMULA, data=train, family=sm.families.Binomial()).fit()


def rolling_predictions(frame: pd.DataFrame, benchmark_name: str) -> pd.DataFrame:
    validate_feature_set(set(MODEL_FEATURES), benchmark=True)
    pieces = []
    for month, train_index, test_index in rolling_origin_splits(frame):
        train = frame.loc[train_index]
        test = frame.loc[test_index]
        model = fit_glm(train)
        prediction = np.clip(model.predict(test).to_numpy(), 1e-6, 1 - 1e-6)
        baseline = np.repeat(float(train.target.mean()), len(test))
        columns = [
            "pitch_key", "game_pk", "game_date", "month", "side", "count",
            "inning_bucket", "target",
        ]
        out = test[columns].copy()
        if "role" in test:
            out["role"] = test.role.to_numpy()
        out["prediction"] = prediction
        out["baseline_prediction"] = baseline
        out["train_end"] = str(train.game_date.max())
        out["benchmark"] = benchmark_name
        pieces.append(out)
    return pd.concat(pieces, ignore_index=True)


def metric_row(y, prediction) -> dict:
    y = np.asarray(y, dtype=int)
    prediction = np.clip(np.asarray(prediction, dtype=float), 1e-6, 1 - 1e-6)
    result = {
        "n": len(y),
        "positives": int(y.sum()),
        "negatives": int(len(y) - y.sum()),
        "base_rate": float(y.mean()),
        "mean_prediction": float(prediction.mean()),
        "brier": float(brier_score_loss(y, prediction)),
        "log_loss": float(log_loss(y, prediction, labels=[0, 1])),
        "roc_auc": float(roc_auc_score(y, prediction)) if len(set(y)) > 1 else np.nan,
    }
    logits = np.log(prediction / (1 - prediction))
    try:
        calibration = sm.GLM(
            y, sm.add_constant(logits), family=sm.families.Binomial()
        ).fit()
        intercept_only = sm.GLM(
            y, np.ones_like(logits), offset=logits, family=sm.families.Binomial()
        ).fit()
        result["calibration_intercept"] = float(intercept_only.params[0])
        result["calibration_slope"] = float(calibration.params[1])
    except Exception:
        result["calibration_intercept"] = np.nan
        result["calibration_slope"] = np.nan
    bins = np.minimum((prediction * 10).astype(int), 9)
    ece = 0.0
    for value in range(10):
        mask = bins == value
        if mask.any():
            ece += float(mask.mean()) * abs(float(y[mask].mean() - prediction[mask].mean()))
    result["ece_10bin"] = ece
    return result


def support_status(metrics: dict) -> str:
    return (
        "SUPPORTED" if metrics["n"] >= MIN_GROUP_N
        and metrics["positives"] >= MIN_GROUP_CLASS
        and metrics["negatives"] >= MIN_GROUP_CLASS
        else "UNSUPPORTED_LOW_SAMPLE"
    )


def calibration_report(predictions: pd.DataFrame, dimensions: list[str]) -> pd.DataFrame:
    rows = []

    def add(dimension, level, group):
        metrics = metric_row(group.target, group.prediction)
        baseline = metric_row(group.target, group.baseline_prediction)
        rows.append({
            "benchmark": group.benchmark.iloc[0],
            "dimension": dimension,
            "level": str(level),
            **metrics,
            "baseline_brier": baseline["brier"],
            "baseline_log_loss": baseline["log_loss"],
            "delta_brier_vs_expanding_base_rate": metrics["brier"] - baseline["brier"],
            "delta_log_loss_vs_expanding_base_rate": metrics["log_loss"] - baseline["log_loss"],
            "support_status": support_status(metrics),
            "calibration_alert": bool(
                metrics["ece_10bin"] > (0.03 if dimension == "OVERALL" else 0.05)
                or (dimension == "OVERALL" and (
                    abs(metrics["calibration_intercept"]) > 0.10
                    or not 0.70 <= metrics["calibration_slope"] <= 1.30
                ))
            ),
        })

    add("OVERALL", "ALL", predictions)
    for dimension in dimensions:
        for level, group in predictions.groupby(dimension, sort=True, observed=True):
            add(dimension, level, group)
    return pd.DataFrame(rows)


def calibration_curve(predictions: pd.DataFrame) -> pd.DataFrame:
    ranked = predictions.prediction.rank(method="first")
    bins = pd.qcut(ranked, 10, labels=False)
    return (
        predictions.assign(decile=bins)
        .groupby(["benchmark", "decile"], observed=True)
        .agg(n=("target", "size"), observed=("target", "mean"), predicted=("prediction", "mean"))
        .reset_index()
    )


def build_validation(
    public: pd.DataFrame,
    selected: pd.DataFrame,
    public_predictions: pd.DataFrame,
    selected_predictions: pd.DataFrame,
    calibration: pd.DataFrame,
    audit: dict,
) -> dict:
    public_overall = calibration[
        calibration.benchmark.eq("PUBLIC_TRACKING_BENCHMARK")
        & calibration.dimension.eq("OVERALL")
    ].iloc[0]
    selected_overall = calibration[
        calibration.benchmark.eq("CHALLENGER_SELECTED_BENCHMARK")
        & calibration.dimension.eq("OVERALL")
    ].iloc[0]
    challenge_public = selected_predictions[["pitch_key", "target", "prediction"]].merge(
        public_predictions[["pitch_key", "prediction"]].rename(
            columns={"prediction": "public_prediction"}
        ),
        on="pitch_key",
        how="inner",
        validate="one_to_one",
    )
    canary_rejected = False
    try:
        validate_feature_set(MODEL_FEATURES | {"signed_boundary_distance"}, benchmark=True)
    except ValueError:
        canary_rejected = True
    temporal_ok = all(
        predictions.train_end.lt(predictions.game_date).all()
        for predictions in [public_predictions, selected_predictions]
    )
    required = {
        "public": {"OVERALL", "side", "count", "inning_bucket"},
        "selected": {"OVERALL", "side", "role", "count", "inning_bucket"},
    }
    present_public = set(calibration[calibration.benchmark.eq("PUBLIC_TRACKING_BENCHMARK")].dimension)
    present_selected = set(calibration[calibration.benchmark.eq("CHALLENGER_SELECTED_BENCHMARK")].dimension)
    conditions = {
        "legal_population_reconciles": audit["legal_called_pitches"] == EXPECTED_LEGAL,
        "official_challenges_reconcile": audit["selected_challenge_rows"] == EXPECTED_CHALLENGES,
        "official_challenge_labels_complete": audit["selected_missing_official_outcome"] == 0,
        "rolling_origin_strictly_prior": temporal_ok,
        "feature_allowlist_passes": True,
        "leaky_canary_rejected": canary_rejected,
        "required_calibration_dimensions_present": (
            required["public"] <= present_public and required["selected"] <= present_selected
        ),
        "public_aggregate_calibration_no_alert": not bool(public_overall.calibration_alert),
        "selected_aggregate_calibration_no_alert": not bool(selected_overall.calibration_alert),
    }
    return {
        "gate": "G6_PROBABILITY",
        "build_status": "PASS" if all(conditions.values()) else "FAIL",
        "scientific_status": "RESTRICTED_PLAYER_PROBABILITY_NOT_IDENTIFIED",
        "conditions": conditions,
        "population": audit,
        "rolling_evaluation_rows": {
            "public": len(public_predictions),
            "selected": len(selected_predictions),
        },
        "aggregate_calibration": {
            "public": public_overall.to_dict(),
            "selected": selected_overall.to_dict(),
        },
        "selection_evidence": {
            "matched_challenges": len(challenge_public),
            "observed_success_rate": float(challenge_public.target.mean()),
            "mean_public_tracking_probability": float(challenge_public.public_prediction.mean()),
            "mean_selected_benchmark_probability": float(challenge_public.prediction.mean()),
            "observed_minus_public_probability": float(
                challenge_public.target.mean() - challenge_public.public_prediction.mean()
            ),
            "interpretation": (
                "Challengers select on private information not represented by public features; "
                "the gap is descriptive and not a causal effect."
            ),
        },
        "identification": {
            "public_exact_distance_is_player_observed": False,
            "selected_sample_transports_to_unchallenged_decisions": False,
            "article3_target_equals_success_probability": False,
            "defense_player_perception_model_validated": False,
            "empirical_evidence_to_action_guidance_allowed": False,
            "model_free_thresholds_allowed": True,
        },
        "feature_audit": {
            "model_features": sorted(MODEL_FEATURES),
            "benchmark_only_features": sorted(BENCHMARK_ONLY_FEATURES),
            "leakage_blacklist": sorted(LEAKAGE_BLACKLIST),
            "canary_rejected": canary_rejected,
        },
    }


def render_report(validation: dict, calibration: pd.DataFrame) -> str:
    public = validation["aggregate_calibration"]["public"]
    selected = validation["aggregate_calibration"]["selected"]
    supported = calibration.groupby(["benchmark", "dimension"]).support_status.apply(
        lambda values: int((values == "SUPPORTED").sum())
    )
    lines = [
        "# ABS-05 Gate G6 Probability Validation",
        "",
        "Generated by `validate_probability.py`; do not hand-edit.",
        "",
        f"**Build status: {validation['build_status']}**",
        f"**Scientific status: {validation['scientific_status']}**",
        "",
        "## Benchmark calibration",
        "",
        f"- Public tracking: n={int(public['n']):,}, AUC={public['roc_auc']:.4f}, Brier={public['brier']:.4f}, slope={public['calibration_slope']:.3f}, intercept={public['calibration_intercept']:.3f}, ECE={public['ece_10bin']:.4f}.",
        f"- Challenger-selected: n={int(selected['n']):,}, AUC={selected['roc_auc']:.4f}, Brier={selected['brier']:.4f}, slope={selected['calibration_slope']:.3f}, intercept={selected['calibration_intercept']:.3f}, ECE={selected['ece_10bin']:.4f}.",
        "",
        "## Identification decision",
        "",
        "Both benchmark models are evaluated strictly out of time. Neither is a validated model of the player's subjective confidence. Exact tracking proximity is not directly observed by the player, while actual challengers are selected using private information. Article 3 predicts recognition conditional on a known wrong call and is not silently redefined as success probability.",
        "",
        "Therefore empirical evidence-to-action guidance remains prohibited. Model-free Challenge Threshold tables may proceed, and later policy work may use these probabilities only as explicitly named benchmark sensitivities.",
        "",
        "## Selection evidence",
        "",
        f"Among {validation['selection_evidence']['matched_challenges']:,} out-of-time challenged pitches, observed success was {validation['selection_evidence']['observed_success_rate']:.4f}, versus mean public-tracking probability {validation['selection_evidence']['mean_public_tracking_probability']:.4f}. This gap is descriptive evidence of selection/private information, not a causal effect.",
        "",
        "## Supported calibration groups",
        "",
    ]
    for (benchmark, dimension), count in supported.items():
        lines.append(f"- {benchmark} / {dimension}: {count} supported rows.")
    lines.extend(["", "Unsupported subgroup rows remain in `calibration.csv` and cannot support guidance.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve() if args.output else root / "research/article5/output/g6"
    output.mkdir(parents=True, exist_ok=True)

    public, selected, audit = load_populations(root)
    public_predictions = rolling_predictions(public, "PUBLIC_TRACKING_BENCHMARK")
    selected_predictions = rolling_predictions(selected, "CHALLENGER_SELECTED_BENCHMARK")
    public_calibration = calibration_report(
        public_predictions, ["side", "count", "inning_bucket"]
    )
    selected_calibration = calibration_report(
        selected_predictions, ["side", "role", "count", "inning_bucket"]
    )
    calibration = pd.concat([public_calibration, selected_calibration], ignore_index=True)
    curves = pd.concat(
        [calibration_curve(public_predictions), calibration_curve(selected_predictions)],
        ignore_index=True,
    )
    validation = build_validation(
        public, selected, public_predictions, selected_predictions, calibration, audit
    )

    public_path = output / "public_rolling_predictions.csv"
    selected_path = output / "selected_rolling_predictions.csv"
    calibration_path = output / "calibration.csv"
    curves_path = output / "calibration_curves.csv"
    validation_path = output / "validation.json"
    report_path = output / "VALIDATION.md"
    for frame, path in [
        (public_predictions, public_path),
        (selected_predictions, selected_path),
        (calibration, calibration_path),
        (curves, curves_path),
    ]:
        frame.to_csv(path, index=False, float_format="%.10g", lineterminator="\n")
    write_json(validation_path, validation)
    report_path.write_text(render_report(validation, calibration))

    inputs = [
        root / "data/full_season/processed/pitches.csv",
        root / "data/full_season/processed/challenges.csv",
        root / "research/article5/PREREGISTRATION.md",
        root / "research/article5/PROBABILITY_SPEC.md",
    ]
    outputs = [
        public_path, selected_path, calibration_path, curves_path,
        validation_path, report_path,
    ]
    manifest = {
        "version": VERSION,
        "build_status": validation["build_status"],
        "scientific_status": validation["scientific_status"],
        "code_sha256": sha256(Path(__file__)),
        "inputs": {str(path.relative_to(root)): sha256(path) for path in inputs},
        "outputs": {
            path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
            for path in outputs
        },
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "statsmodels": statsmodels.__version__,
        },
    }
    write_json(output / "manifest.json", manifest)
    print(json.dumps({
        "build_status": validation["build_status"],
        "scientific_status": validation["scientific_status"],
    }, sort_keys=True))
    return 0 if validation["build_status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
