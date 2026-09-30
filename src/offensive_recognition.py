"""Sprint 2 offensive recognition analysis for the fixed 2026 pilot week."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings(
    "ignore",
    message="Found unknown categories",
    category=UserWarning,
)

PILOT_START = "2026-08-24"
PILOT_END = "2026-08-30"
EXPECTED = {
    "incorrect_called_strikes": 509,
    "challenge_available": 484,
    "recognized": 96,
    "not_recognized": 388,
    "excluded_resource": 15,
    "excluded_unknown": 10,
}
BALL_RADIUS_FT = 2.9 / 2 / 12
HALF_PLATE_FT = 17 / 2 / 12
MIN_DISPLAY_N = 20
CV_REPEATS = 10
CV_FOLDS = 5
SEED = 20260824

PITCH_FAMILY = {
    "FF": "FOUR_SEAM", "SI": "SINKER", "FC": "CUTTER", "SL": "SLIDER",
    "ST": "SWEEPER", "CU": "CURVEBALL", "KC": "CURVEBALL",
    "CH": "CHANGEUP", "FS": "SPLITTER", "FO": "SPLITTER",
}

MODEL_SPECS = {
    "DISTANCE": (["abs_distance_inches"], []),
    "A_GEOMETRY": (["abs_distance", "horizontal_distance", "vertical_distance", "corner_proximity"], ["miss_axis", "miss_side"]),
    "B_PITCH_TYPE": (["abs_distance", "horizontal_distance", "vertical_distance", "corner_proximity"], ["miss_axis", "miss_side", "pitch_family"]),
    "B_MOVEMENT": (["abs_distance", "horizontal_distance", "vertical_distance", "corner_proximity", "release_speed", "release_spin_rate", "spin_axis_sin", "spin_axis_cos", "pfx_x", "pfx_z", "extension", "release_pos_x", "release_pos_z"], ["miss_axis", "miss_side", "pitch_hand", "bat_side"]),
    "B_PITCH": (["abs_distance", "horizontal_distance", "vertical_distance", "corner_proximity", "release_speed", "release_spin_rate", "spin_axis_sin", "spin_axis_cos", "pfx_x", "pfx_z", "extension", "release_pos_x", "release_pos_z"], ["miss_axis", "miss_side", "pitch_family", "pitch_hand", "bat_side"]),
    "C_SITUATION": (["abs_distance", "horizontal_distance", "vertical_distance", "corner_proximity", "release_speed", "release_spin_rate", "spin_axis_sin", "spin_axis_cos", "pfx_x", "pfx_z", "extension", "release_pos_x", "release_pos_z", "inning", "offense_score_diff"], ["miss_axis", "miss_side", "pitch_family", "pitch_hand", "bat_side", "count", "outs", "base_state", "affected_team_challenges_remaining"]),
}


def _stable_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_stable_json(value))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().map({"true": True, "false": False})


def _numeric(frame: pd.DataFrame, fields: list[str]) -> None:
    for field in fields:
        frame[field] = pd.to_numeric(frame[field], errors="coerce")


def _inside_outside(x: float, stand: str) -> str:
    # Statcast x is catcher's perspective: negative is the RHB side of the plate.
    inside = (stand == "R" and x < 0) or (stand == "L" and x > 0)
    return "INSIDE" if inside else "OUTSIDE"


def _geometry(row: pd.Series) -> tuple:
    x, z, top, bot = row["plate_x"], row["plate_z"], row["abs_zone_top"], row["abs_zone_bot"]
    hx = max(abs(x) - HALF_PLATE_FT, 0.0)
    vz_above = max(z - top, 0.0)
    vz_below = max(bot - z, 0.0)
    vz = max(vz_above, vz_below)
    if hx > 0 and vz > 0:
        axis = "CORNER"
        vertical = "ABOVE" if vz_above else "BELOW"
        side = f"{vertical}_{_inside_outside(x, row['bat_side'])}"
    elif hx > 0:
        axis, side = "HORIZONTAL", _inside_outside(x, row["bat_side"])
    else:
        axis, side = "VERTICAL", "ABOVE" if vz_above else "BELOW"
    corner = math.hypot(hx, vz) if hx and vz else 0.0
    return axis, side, hx, vz, corner


def population_and_features(root: Path) -> tuple[pd.DataFrame, dict]:
    source = root / "data/processed/pitches.csv"
    challenges_path = root / "data/processed/challenges.csv"
    validation_path = root / "data/processed/validation_report.json"
    if not source.exists() or not challenges_path.exists():
        raise RuntimeError("Sprint 1 processed pitch and challenge tables are required")
    validation = json.loads(validation_path.read_text())
    if not validation.get("gate_passed"):
        raise RuntimeError("Sprint 1 validation gate is not passing")

    pitches = pd.read_csv(source, dtype=str, keep_default_na=False)
    if pitches["game_date"].min() != PILOT_START or pitches["game_date"].max() != PILOT_END:
        raise RuntimeError("Sprint 2 is locked to the August 24–30, 2026 pilot")
    if not pitches["game_date"].between(PILOT_START, PILOT_END).all():
        raise RuntimeError("A non-pilot row was detected")
    pitches["challenge_available_bool"] = _bool(pitches["challenge_available"])
    pitches["challenged_bool"] = _bool(pitches["challenged"])
    incorrect = pitches[(pitches.original_call == "STRIKE") & (pitches.derived_abs_call == "BALL")].copy()

    resource = incorrect.survival_class.eq("SURVIVED_RESOURCE")
    unknown = incorrect.survival_class.eq("UNKNOWN")
    available = incorrect.challenge_available_bool.eq(True) & ~resource & ~unknown
    other = ~(available | resource | unknown)
    eligible = incorrect[available].copy()

    challenges = pd.read_csv(challenges_path, dtype=str, keep_default_na=False)
    roles = challenges.set_index("pitch_key")["challenger_role"].to_dict()
    challenged_roles = eligible.loc[eligible.challenged_bool, "pitch_key"].map(roles)
    if challenged_roles.isna().any() or not challenged_roles.eq("BATTER").all():
        raise RuntimeError("Offensive challenged opportunities do not reconcile to batter challenges")
    eligible["recognized"] = eligible.challenged_bool.astype(int)

    audit = {
        "pilot_start": PILOT_START,
        "pilot_end": PILOT_END,
        "full_season_expansion_performed": False,
        "sprint1_pitches_sha256": _sha256(source),
        "incorrect_called_strikes": int(len(incorrect)),
        "challenge_available": int(len(eligible)),
        "recognized": int(eligible.recognized.sum()),
        "not_recognized": int((1 - eligible.recognized).sum()),
        "excluded_resource": int(resource.sum()),
        "excluded_unknown": int(unknown.sum()),
        "excluded_other": int(other.sum()),
        "excluded_unknown_reasons": incorrect.loc[unknown, "challenge_unavailable_reason"].replace("", "UNSPECIFIED").value_counts().sort_index().to_dict(),
        "outcome_definition": "1 when the eligible incorrect called strike was challenged by its batter; 0 otherwise. Challenge result is not used.",
    }
    for key, value in EXPECTED.items():
        if audit[key] != value:
            raise RuntimeError(f"Population failed reconciliation: {key}={audit[key]}, expected {value}")
    if audit["excluded_other"] != 0:
        raise RuntimeError("Unexpected excluded population is nonzero")

    runner_fields = ["on_1b", "on_2b", "on_3b"]
    numeric = ["plate_x", "plate_z", "abs_zone_top", "abs_zone_bot", "distance_from_abs_boundary", "release_speed", "release_spin_rate", "spin_axis", "pfx_x", "pfx_z", "extension", "release_pos_x", "release_pos_z", "inning", "balls", "strikes", "outs", "score_diff", "affected_team_challenges_remaining"] + runner_fields
    _numeric(eligible, numeric)
    required_numeric = [field for field in numeric if field not in runner_fields]
    if eligible[required_numeric].isna().any().any():
        missing = eligible[required_numeric].isna().sum()
        raise RuntimeError("Unexplained model-feature missingness: " + str(missing[missing > 0].to_dict()))
    geometry = eligible.apply(_geometry, axis=1, result_type="expand")
    geometry.columns = ["miss_axis", "miss_side", "horizontal_distance", "vertical_distance", "corner_proximity"]
    eligible = pd.concat([eligible, geometry], axis=1)
    eligible["abs_distance"] = eligible.distance_from_abs_boundary.abs()
    eligible["pitch_family"] = eligible.pitch_type.map(PITCH_FAMILY).fillna("OTHER")
    eligible["spin_axis_sin"] = np.sin(np.deg2rad(eligible.spin_axis))
    eligible["spin_axis_cos"] = np.cos(np.deg2rad(eligible.spin_axis))
    eligible["count"] = eligible.balls.astype(int).astype(str) + "-" + eligible.strikes.astype(int).astype(str)
    eligible["base_state"] = eligible[["on_1b", "on_2b", "on_3b"]].notna().replace({True: "1", False: "0"}).agg("".join, axis=1)
    # CSV empty runner cells became NaN during numeric conversion, so notna is exact here.
    eligible["two_strike_count"] = np.where(eligible.strikes.eq(2), "YES", "NO")
    eligible["strike_three_call"] = np.where(eligible.strikes.eq(2), "YES", "NO")
    eligible["inning_group"] = pd.cut(eligible.inning, [0, 3, 6, np.inf], labels=["EARLY", "MIDDLE", "LATE"]).astype(str)
    eligible["offense_score_diff"] = np.where(eligible.half_inning.eq("top"), -eligible.score_diff, eligible.score_diff)
    eligible["score_state"] = np.select([eligible.offense_score_diff > 0, eligible.offense_score_diff < 0], ["AHEAD", "BEHIND"], default="TIED")
    eligible["abs_distance_inches"] = eligible.abs_distance * 12
    eligible["horizontal_distance_inches"] = eligible.horizontal_distance * 12
    eligible["vertical_distance_inches"] = eligible.vertical_distance * 12
    eligible["corner_proximity_inches"] = eligible.corner_proximity * 12
    eligible["date_scope"] = f"{PILOT_START}/{PILOT_END}"
    eligible["feature_version"] = "offensive_recognition_v1"
    eligible = eligible.sort_values(["game_date", "game_pk", "at_bat_index", "play_event_index"]).reset_index(drop=True)
    return eligible, audit


def _model(numeric: list[str], categorical: list[str], regularized: bool) -> Pipeline:
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric))
    if categorical:
        transformers.append(("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), categorical))
    classifier = LogisticRegression(C=1.0, penalty="l2" if regularized else None, max_iter=5000, solver="liblinear" if regularized else "lbfgs", random_state=SEED)
    return Pipeline([("features", ColumnTransformer(transformers)), ("logit", classifier)])


def _ece(y: np.ndarray, p: np.ndarray, bins: int = 5) -> float:
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for low, high in zip(edges[:-1], edges[1:]):
        mask = (p >= low) & (p < high if high < 1 else p <= high)
        if mask.any():
            total += mask.mean() * abs(y[mask].mean() - p[mask].mean())
    return float(total)


def _calibration(y: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    clipped = np.clip(p, 1e-6, 1 - 1e-6)
    frame = pd.DataFrame({"y": y, "logit_p": np.log(clipped / (1 - clipped))})
    fit = smf.logit("y ~ logit_p", frame).fit(disp=0)
    return float(fit.params["Intercept"]), float(fit.params["logit_p"])


def _formula_fit(frame: pd.DataFrame, numeric: list[str], categorical: list[str], name: str):
    terms = numeric + [f"C({field})" for field in categorical]
    formula = "recognized ~ " + " + ".join(terms)
    fit = smf.logit(formula, frame).fit(disp=0, maxiter=1000)
    coefficients = []
    ci = fit.conf_int()
    for term in fit.params.index:
        coefficients.append({
            "model": name, "term": term, "coefficient_log_odds": fit.params[term],
            "odds_ratio": math.exp(fit.params[term]), "std_error": fit.bse[term],
            "ci95_low_log_odds": ci.loc[term, 0], "ci95_high_log_odds": ci.loc[term, 1],
            "p_value_exploratory": fit.pvalues[term], "coefficient_basis": "UNPENALIZED_RAW_SCALE",
        })
    return fit, coefficients


def fit_models(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    specs = dict(MODEL_SPECS)
    c_num, c_cat = MODEL_SPECS["C_SITUATION"]
    for label, field in [("D_BATTER", "batter_id"), ("D_PITCHER", "pitcher_id"), ("D_CATCHER", "catcher_id"), ("D_UMPIRE", "umpire_id")]:
        specs[label] = (c_num, c_cat + [field])
    specs["D_ALL_IDENTITY"] = (c_num, c_cat + ["batter_id", "pitcher_id", "catcher_id", "umpire_id"])

    y = frame.recognized.to_numpy()
    groups = frame.game_pk.to_numpy()
    prediction_rows, metric_rows, coefficient_rows = [], [], []
    for name, (numeric, categorical) in specs.items():
        # Fixed L2 regularization is used for every predictive model. The pilot's
        # sparse categorical cells make expanded unpenalized fits singular.
        regularized = True
        sums = np.zeros(len(frame)); counts = np.zeros(len(frame))
        fold_values = {key: [] for key in ("roc_auc", "pr_auc", "log_loss", "brier")}
        for repeat in range(CV_REPEATS):
            splitter = StratifiedGroupKFold(n_splits=CV_FOLDS, shuffle=True, random_state=SEED + repeat)
            for train, test in splitter.split(frame, y, groups):
                model = _model(numeric, categorical, regularized)
                model.fit(frame.iloc[train], y[train])
                probabilities = model.predict_proba(frame.iloc[test])[:, 1]
                sums[test] += probabilities; counts[test] += 1
                yt = y[test]
                if len(np.unique(yt)) == 2:
                    fold_values["roc_auc"].append(roc_auc_score(yt, probabilities))
                    fold_values["pr_auc"].append(average_precision_score(yt, probabilities))
                fold_values["log_loss"].append(log_loss(yt, probabilities, labels=[0, 1]))
                fold_values["brier"].append(brier_score_loss(yt, probabilities))
        if not np.all(counts == CV_REPEATS):
            raise RuntimeError(f"Incomplete repeated out-of-fold predictions for {name}")
        probabilities = sums / counts
        # Identity coefficients are deliberately withheld: the identity tests are
        # aggregate model comparisons, not one-week player/umpire rankings.
        if not name.startswith("D_"):
            full_model = _model(numeric, categorical, True)
            full_model.fit(frame, y)
            names = full_model.named_steps["features"].get_feature_names_out()
            for term, coefficient in zip(names, full_model.named_steps["logit"].coef_[0]):
                coefficient_rows.append({
                    "model": name, "term": term, "coefficient_log_odds": coefficient,
                    "odds_ratio": math.exp(coefficient), "std_error": np.nan,
                    "ci95_low_log_odds": np.nan, "ci95_high_log_odds": np.nan,
                    "p_value_exploratory": np.nan, "coefficient_basis": "L2_C_1_STANDARDIZED_FULL_SAMPLE",
                })
        intercept, slope = _calibration(y, probabilities)
        row = {
            "model": name, "sample_size": len(frame), "recognized": int(y.sum()),
            "not_recognized": int((1-y).sum()), "regularization": "L2_C_1_FIXED_NO_TUNING",
            "cv_strategy": f"{CV_REPEATS}x{CV_FOLDS}-fold stratified group-by-game",
            "roc_auc": roc_auc_score(y, probabilities), "pr_auc": average_precision_score(y, probabilities),
            "log_loss": log_loss(y, probabilities), "brier_score": brier_score_loss(y, probabilities),
            "calibration_intercept": intercept, "calibration_slope": slope,
            "expected_calibration_error_5bin": _ece(y, probabilities),
            "aic": np.nan, "bic": np.nan, "parameter_count": np.nan,
        }
        for metric, values in fold_values.items():
            row[f"cv_{metric}_mean"] = np.mean(values)
            row[f"cv_{metric}_std"] = np.std(values, ddof=1)
        if name == "DISTANCE":
            try:
                fit, coefficients = _formula_fit(frame, numeric, categorical, name)
                row.update(aic=fit.aic, bic=fit.bic, parameter_count=len(fit.params))
                coefficient_rows.extend(coefficients)
            except Exception as error:
                raise RuntimeError(f"Unpenalized inferential model failed for {name}: {error}") from error
        metric_rows.append(row)
        for index, probability in enumerate(probabilities):
            prediction_rows.append({
                "pitch_key": frame.loc[index, "pitch_key"], "game_pk": frame.loc[index, "game_pk"],
                "game_date": frame.loc[index, "game_date"], "model": name,
                "recognized": int(y[index]), "predicted_probability": probability,
                "prediction_method": "mean repeated out-of-fold probability",
            })

    metrics = pd.DataFrame(metric_rows)
    comparisons = []
    transitions = [("DISTANCE", "A_GEOMETRY"), ("A_GEOMETRY", "B_PITCH_TYPE"),
                   ("A_GEOMETRY", "B_MOVEMENT"), ("A_GEOMETRY", "B_PITCH"), ("B_PITCH", "C_SITUATION"),
                   ("C_SITUATION", "D_BATTER"), ("C_SITUATION", "D_PITCHER"),
                   ("C_SITUATION", "D_CATCHER"), ("C_SITUATION", "D_UMPIRE"),
                   ("C_SITUATION", "D_ALL_IDENTITY")]
    by_name = metrics.set_index("model")
    for before, after in transitions:
        comparisons.append({
            "transition": f"{before} -> {after}", "baseline_model": before, "expanded_model": after,
            "delta_roc_auc": by_name.loc[after, "roc_auc"] - by_name.loc[before, "roc_auc"],
            "delta_pr_auc": by_name.loc[after, "pr_auc"] - by_name.loc[before, "pr_auc"],
            "delta_log_loss": by_name.loc[after, "log_loss"] - by_name.loc[before, "log_loss"],
            "delta_brier_score": by_name.loc[after, "brier_score"] - by_name.loc[before, "brier_score"],
            "interpretation_rule": "Positive AUC/PR and negative log-loss/Brier changes favor expanded model",
        })
    return metrics, pd.DataFrame(prediction_rows), pd.DataFrame(comparisons), pd.DataFrame(coefficient_rows)


def _wilson(successes: int, total: int) -> tuple[float, float]:
    if total == 0:
        return np.nan, np.nan
    z = 1.96; p = successes / total; denominator = 1 + z*z/total
    center = (p + z*z/(2*total))/denominator
    half = z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))/denominator
    return center-half, center+half


def descriptive(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["distance_bin_inches"] = pd.cut(work.abs_distance_inches, [-1e-9, .25, .5, 1, 2, np.inf], labels=["0–0.25", "0.25–0.5", "0.5–1", "1–2", "2+"])
    work["velocity_bin_mph"] = pd.cut(work.release_speed, [-np.inf, 85, 90, 95, np.inf], right=False, labels=["<85", "85–<90", "90–<95", "95+"])
    for field in ("pfx_x", "pfx_z"):
        work[field + "_quartile"] = pd.qcut(work[field], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    dimensions = ["distance_bin_inches", "miss_side", "pitch_family", "velocity_bin_mph", "pfx_x_quartile", "pfx_z_quartile", "count", "inning", "inning_group", "outs", "base_state", "affected_team_challenges_remaining"]
    rows = []
    for dimension in dimensions:
        for value, group in work.groupby(dimension, observed=True, dropna=False, sort=True):
            n, successes = len(group), int(group.recognized.sum())
            low, high = _wilson(successes, n)
            rows.append({
                "dimension": dimension, "value": str(value), "opportunities": n,
                "recognized": successes, "not_recognized": n-successes,
                "recognition_rate": successes/n, "ci95_low_wilson": low,
                "ci95_high_wilson": high, "small_sample_warning": n < MIN_DISPLAY_N,
                "display_rate": f"{successes/n:.1%}" if n >= MIN_DISPLAY_N else "SUPPRESSED_N_LT_20",
            })
    return pd.DataFrame(rows)


def _rate_plot(desc: pd.DataFrame, dimension: str, title: str, path: Path) -> None:
    data = desc[desc.dimension.eq(dimension)].copy()
    x = np.arange(len(data)); y = data.recognition_rate.to_numpy()
    lower = y - data.ci95_low_wilson.to_numpy(); upper = data.ci95_high_wilson.to_numpy() - y
    fig, ax = plt.subplots(figsize=(max(7, len(data)*.65), 5))
    for i, row in enumerate(data.itertuples()):
        color = "#9CA3AF" if row.small_sample_warning else "#125A78"
        ax.errorbar(i, y[i], yerr=[[lower[i]], [upper[i]]], fmt="o", color=color, capsize=3)
        warning = "\nsmall n" if row.small_sample_warning else ""
        ax.annotate(f"n={row.opportunities}{warning}", (i, y[i]), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8)
    ax.set_xticks(x, data.value, rotation=35, ha="right"); ax.set_ylim(0, 1)
    ax.set_ylabel("Recognition rate (95% Wilson CI)"); ax.set_title(title)
    ax.grid(axis="y", alpha=.25); fig.tight_layout(); fig.savefig(path, dpi=180); plt.close(fig)


def figures(frame: pd.DataFrame, desc: pd.DataFrame, artifacts: Path) -> None:
    artifacts.mkdir(parents=True, exist_ok=True)
    # Distance: raw bins plus fixed distance-only logistic curve and model uncertainty.
    fit = smf.logit("recognized ~ abs_distance_inches", frame).fit(disp=0)
    grid = np.linspace(0, frame.abs_distance_inches.max(), 200)
    design = np.column_stack([np.ones_like(grid), grid])
    eta = design @ fit.params.to_numpy(); se = np.sqrt(np.einsum("ij,jk,ik->i", design, fit.cov_params().to_numpy(), design))
    logistic = lambda value: 1/(1+np.exp(-value))
    fig, ax = plt.subplots(figsize=(8,5))
    rng=np.random.default_rng(SEED)
    ax.scatter(frame.abs_distance_inches, frame.recognized + rng.uniform(-.025,.025,len(frame)), alpha=.14, s=12, color="#555555")
    ax.plot(grid, logistic(eta), color="#9A3412", label="distance-only logistic fit")
    ax.fill_between(grid, logistic(eta-1.96*se), logistic(eta+1.96*se), color="#FDBA74", alpha=.4, label="95% model CI")
    ax.set(xlabel="Distance beyond ABS boundary (inches)", ylabel="Recognized (jittered) / probability", ylim=(-.08,1.08), title="Recognition versus ABS boundary distance")
    ax.legend(); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(artifacts/"01_recognition_vs_distance.png",dpi=180); plt.close(fig)
    for dim,title,name in [
        ("miss_side","Recognition by miss location","02_recognition_by_miss_location.png"),
        ("pitch_family","Recognition by pitch family","03_recognition_by_pitch_type.png"),
        ("count","Recognition by pre-pitch count","05_recognition_by_count.png"),
        ("inning","Recognition by inning","06_recognition_by_inning.png"),
        ("affected_team_challenges_remaining","Recognition by challenges remaining","07_recognition_by_challenges_remaining.png")]:
        _rate_plot(desc,dim,title,artifacts/name)
    fig, axes = plt.subplots(1,2,figsize=(11,4.8),sharey=True)
    for ax, field, label in [(axes[0],"pfx_x","Horizontal movement (feet)"),(axes[1],"pfx_z","Vertical movement (feet)")]:
        ax.scatter(frame[field],frame.recognized+rng.uniform(-.025,.025,len(frame)),alpha=.18,s=13,color="#125A78")
        bins=pd.qcut(frame[field],4,duplicates="drop")
        grouped=frame.assign(bin=bins).groupby("bin",observed=True).agg(x=(field,"mean"),rate=("recognized","mean"),n=("recognized","size"))
        ax.plot(grouped.x,grouped.rate,"o-",color="#9A3412")
        for row in grouped.itertuples(): ax.annotate(f"n={row.n}",(row.x,row.rate),xytext=(0,7),textcoords="offset points",ha="center",fontsize=8)
        ax.set(xlabel=label,ylim=(-.08,1.08));ax.grid(alpha=.2)
    axes[0].set_ylabel("Recognized (jittered) / quartile rate");fig.suptitle("Recognition versus pitch movement")
    fig.tight_layout();fig.savefig(artifacts/"04_recognition_vs_movement.png",dpi=180);plt.close(fig)


def secondary_analyses(frame: pd.DataFrame, metrics: pd.DataFrame, comparisons: pd.DataFrame) -> dict:
    pitch = frame.groupby("pitch_family", sort=True).agg(opportunities=("recognized","size"), mean_boundary_distance_inches=("abs_distance_inches","mean"), recognized=("recognized","sum"), recognition_rate=("recognized","mean")).reset_index()
    pitch["supported_n_ge_20"] = pitch.opportunities.ge(MIN_DISPLAY_N)
    support = {}
    for field in ("batter_id", "pitcher_id", "catcher_id", "umpire_id"):
        counts=frame.groupby(field).size()
        support[field]={"groups":int(len(counts)),"minimum":int(counts.min()),"p25":float(counts.quantile(.25)),"median":float(counts.median()),"p75":float(counts.quantile(.75)),"maximum":int(counts.max()),"groups_n_ge_5":int((counts>=5).sum()),"groups_n_ge_10":int((counts>=10).sum())}
    changes=comparisons.set_index("transition").to_dict("index")
    def signal(identity: str) -> str:
        row=changes[f"C_SITUATION -> D_{identity.upper()}"]
        supported=support[identity+"_id"]
        if supported["median"] < 5 or supported["groups_n_ge_5"] < 10: return "insufficient sample"
        if row["delta_log_loss"] < -.005 and row["delta_roc_auc"] > .01: return "meaningful pilot signal requiring full-season validation"
        if row["delta_log_loss"] < 0 or row["delta_roc_auc"] > 0: return "weak pilot signal"
        return "no detectable pilot signal"
    adjusted = {}
    for model_name, field, values in [
        ("B_PITCH", "pitch_family", sorted(frame.pitch_family.unique())),
        ("C_SITUATION", "inning", [2, 5, 8]),
        ("C_SITUATION", "affected_team_challenges_remaining", [1, 2]),
    ]:
        numeric,categorical=MODEL_SPECS[model_name]
        fitted=_model(numeric,categorical,True).fit(frame,frame.recognized)
        estimates=[]
        for value in values:
            scenario=frame.copy();scenario[field]=value
            estimates.append({"value":value,"average_adjusted_probability":float(fitted.predict_proba(scenario)[:,1].mean())})
        adjusted[field]=estimates
    pitch_adjusted={row["value"]:row["average_adjusted_probability"] for row in adjusted["pitch_family"]}
    pitch_records=pitch.to_dict("records")
    for row in pitch_records:
        row["model_adjusted_recognition_estimate"] = pitch_adjusted[row["pitch_family"]]
    return {"pitch_type":pitch_records,"identity_support":support,"identity_signal":{x:signal(x) for x in ("batter","pitcher","catcher","umpire")},"controlled_marginal_estimates":adjusted}


def report(root: Path, audit: dict, metrics: pd.DataFrame, comparisons: pd.DataFrame, coefficients: pd.DataFrame, secondary: dict) -> None:
    by=metrics.set_index("model"); comp=comparisons.set_index("transition")
    distance=coefficients[(coefficients.model=="DISTANCE") & (coefficients.term=="abs_distance_inches") & (coefficients.coefficient_basis=="UNPENALIZED_RAW_SCALE")].iloc[0]
    base=audit["recognized"]/audit["challenge_available"]
    lines=[
        "# Sprint 2 — Offensive recognition analysis", "",
        f"This analysis is restricted to **{PILOT_START} through {PILOT_END}**. It did not acquire or analyze full-season data. Sprint 1 accepted outputs were read-only inputs.", "",
        "## 1. Population", "",
        f"The population reconciles exactly: {audit['incorrect_called_strikes']} incorrect called strikes, comprising {audit['challenge_available']} legal opportunities, {audit['excluded_resource']} exhausted-resource exclusions, and {audit['excluded_unknown']} position-player-pitching exclusions. The analytical population has {audit['recognized']} recognized and {audit['not_recognized']} not recognized opportunities. No other rows were excluded.", "",
        "## 2. Baseline recognition", "",
        f"Batters challenged {audit['recognized']} of {audit['challenge_available']} eligible incorrect strikes ({base:.1%}). Recognition means the batter challenged; challenge outcome never defines the label.", "",
        "## 3. Geometry", "",
        f"Boundary distance had a {('positive' if distance.coefficient_log_odds > 0 else 'negative')} association with recognition (log-odds coefficient per inch: {distance.coefficient_log_odds:.3f}, 95% CI {distance.ci95_low_log_odds:.3f} to {distance.ci95_high_log_odds:.3f}). The distance-only repeated out-of-fold ROC AUC was {by.loc['DISTANCE','roc_auc']:.3f}, PR AUC {by.loc['DISTANCE','pr_auc']:.3f}, log loss {by.loc['DISTANCE','log_loss']:.3f}, and Brier score {by.loc['DISTANCE','brier_score']:.3f}. The expanded geometry model changed ROC AUC by {comp.loc['DISTANCE -> A_GEOMETRY','delta_roc_auc']:+.3f} and log loss by {comp.loc['DISTANCE -> A_GEOMETRY','delta_log_loss']:+.3f}.", "",
        "Miss axis and handedness-aware location are included in Model A. Corner labels retain both vertical and horizontal components, such as ABOVE_INSIDE. These results describe association and out-of-fold discrimination, not perception causality.", "",
        "## 4. Pitch characteristics", "",
        f"The pitch block did not add reliable held-out information beyond geometry: it changed ROC AUC by {comp.loc['A_GEOMETRY -> B_PITCH','delta_roc_auc']:+.3f}, PR AUC by {comp.loc['A_GEOMETRY -> B_PITCH','delta_pr_auc']:+.3f}, log loss by {comp.loc['A_GEOMETRY -> B_PITCH','delta_log_loss']:+.3f}, and Brier score by {comp.loc['A_GEOMETRY -> B_PITCH','delta_brier_score']:+.3f}. Pitch family alone changed ROC AUC {comp.loc['A_GEOMETRY -> B_PITCH_TYPE','delta_roc_auc']:+.3f} and log loss {comp.loc['A_GEOMETRY -> B_PITCH_TYPE','delta_log_loss']:+.3f}; velocity/movement/release fields without pitch family changed ROC AUC {comp.loc['A_GEOMETRY -> B_MOVEMENT','delta_roc_auc']:+.3f} and log loss {comp.loc['A_GEOMETRY -> B_MOVEMENT','delta_log_loss']:+.3f}. Negative log-loss/Brier changes indicate improvement. Unsupported pitch-family rates remain present with sample warnings; they are not interpreted individually.", "",
        "## 5. Situation", "",
        f"Situation added the clearest incremental pilot signal. Adding count, outs, runners, inning, score, and remaining inventory changed ROC AUC by {comp.loc['B_PITCH -> C_SITUATION','delta_roc_auc']:+.3f}, PR AUC by {comp.loc['B_PITCH -> C_SITUATION','delta_pr_auc']:+.3f}, log loss by {comp.loc['B_PITCH -> C_SITUATION','delta_log_loss']:+.3f}, and Brier score by {comp.loc['B_PITCH -> C_SITUATION','delta_brier_score']:+.3f}. Average adjusted recognition was {secondary['controlled_marginal_estimates']['affected_team_challenges_remaining'][0]['average_adjusted_probability']:.1%} with one challenge and {secondary['controlled_marginal_estimates']['affected_team_challenges_remaining'][1]['average_adjusted_probability']:.1%} with two. The detailed coefficient table preserves standardized penalized estimates, but classical uncertainty is withheld for these expanded singular designs; no coefficient was selected for significance.", "",
        "## 6. Human effects", "",
    ]
    pitch_table = ["Supported pitch-family summaries (`n >= 20`):", "", "| Family | Opportunities | Mean miss (in) | Raw rate | Model-adjusted rate |", "|---|---:|---:|---:|---:|"]
    for row in secondary["pitch_type"]:
        if row["supported_n_ge_20"]:
            pitch_table.append(f"| {row['pitch_family']} | {row['opportunities']} | {row['mean_boundary_distance_inches']:.2f} | {row['recognition_rate']:.1%} | {row['model_adjusted_recognition_estimate']:.1%} |")
    pitch_table.append("")
    situation_index = lines.index("## 5. Situation")
    lines[situation_index:situation_index] = pitch_table
    for identity in ("batter","pitcher","catcher","umpire"):
        label=identity.upper(); row=comp.loc[f"C_SITUATION -> D_{label}"]; support=secondary["identity_support"][identity+"_id"]
        lines.append(f"- **{identity.title()}: {secondary['identity_signal'][identity]}.** {support['groups']} groups; median {support['median']:.1f} opportunities, maximum {support['maximum']}, and {support['groups_n_ge_5']} groups with at least five. Adding regularized identity changed ROC AUC {row.delta_roc_auc:+.3f} and log loss {row.delta_log_loss:+.3f}.")
    lines += ["", "Identity labels are used only as regularized model inputs. No individual coefficient table or ranking is published. Sparse groups and unseen identities in held-out games constrain these tests.", "", "## 7. Early versus late", "",
              f"Early, middle, and late recognition rates are reported with Wilson intervals. The controlled situation model uses raw inning alongside geometry, pitch, count, runners, score, and inventory. Average adjusted recognition probabilities at representative innings 2, 5, and 8 were {secondary['controlled_marginal_estimates']['inning'][0]['average_adjusted_probability']:.1%}, {secondary['controlled_marginal_estimates']['inning'][1]['average_adjusted_probability']:.1%}, and {secondary['controlled_marginal_estimates']['inning'][2]['average_adjusted_probability']:.1%}. These estimates are exploratory; the report does not characterize late-game behavior as optimal or suboptimal.", "", "## 8. Limitations", "",
              "This is one week and 484 opportunities. Repeated cross-validation reduces dependence on one split, but folds remain correlated across repeats and uncertainty is descriptive. Games are held together within folds to limit within-game leakage. Identity support is especially sparse. Regularized identity models do not provide classical AIC/BIC or coefficient p-values. Statcast geometry is public rounded measurement, and challenged pitches helped validate geometry in Sprint 1 but are a selected subset. Model comparisons can vary with reasonable encoding and regularization choices; only a fixed, documented specification was run. Results are predictive associations, not causal effects.", "", "## 9. Recommendation", "",
              "Do not expand the data during Sprint 2. Preserve this pilot as the fixed mechanism and pipeline check. A later, separately authorized sprint could test the primary geometry, pitch, and situation hypotheses across the full season, while identity effects should proceed only with preregistered support thresholds and grouped temporal validation. The strongest candidates for later validation are those with out-of-fold improvement in `model_comparisons.csv`; null and adverse changes are equally retained.", "", "## Evaluation design", "",
              f"All models use {CV_REPEATS} repeats of {CV_FOLDS}-fold stratified, group-by-game cross-validation. Every opportunity receives exactly {CV_REPEATS} held-out predictions, averaged for the published row-level probability. All predictive models use the same fixed L2 penalty (C=1) because expanded unpenalized pilot models were singular; no penalty search was performed. Classical AIC/BIC and coefficient uncertainty are therefore reported only for the stable unpenalized distance baseline. Calibration reports intercept, slope, five-bin expected calibration error, and Brier score. The figures show untruncated 0–1 probability axes, group sizes, and Wilson or model intervals.", "", "## Reproducibility and files", "",
              "Run `python -m src.offensive_recognition` after installing `requirements.txt`. Required tables are under `data/analysis/`; model coefficients, comparisons, identity support, pitch-family summaries, figures, and a run manifest are under `artifacts/sprint2/`. The notebook is a read-only inspection layer. The run manifest records input and output hashes and explicitly records that no full-season expansion occurred.", ""]
    (root/"docs/sprint2_offensive_recognition_report.md").write_text("\n".join(lines))


def run(root: Path) -> None:
    analysis=root/"data/analysis"; artifacts=root/"artifacts/sprint2"
    analysis.mkdir(parents=True,exist_ok=True);artifacts.mkdir(parents=True,exist_ok=True)
    before={p.name:_sha256(p) for p in sorted((root/"data/processed").glob("*")) if p.is_file()}
    features,audit=population_and_features(root)
    feature_fields = [
        "pitch_key","game_pk","game_date","recognized","survival_class","challenge_outcome","challenged",
        "distance_from_abs_boundary","abs_distance","abs_distance_inches","miss_axis","miss_side",
        "horizontal_distance","horizontal_distance_inches","vertical_distance","vertical_distance_inches",
        "corner_proximity","corner_proximity_inches","plate_x","plate_z","abs_zone_top","abs_zone_bot",
        "pitch_type","pitch_family","release_speed","release_spin_rate","spin_axis","spin_axis_sin","spin_axis_cos",
        "pfx_x","pfx_z","extension","release_pos_x","release_pos_z","pitch_hand","bat_side",
        "inning","balls","strikes","count","outs","on_1b","on_2b","on_3b","base_state","score_diff","offense_score_diff",
        "affected_team_challenges_remaining","two_strike_count","strike_three_call","inning_group","score_state",
        "batter_id","pitcher_id","catcher_id","umpire_id","date_scope","feature_version"
    ]
    features[feature_fields].to_csv(analysis/"offensive_recognition_features.csv",index=False,lineterminator="\n")
    _write_json(analysis/"offensive_recognition_population_audit.json",audit)
    desc=descriptive(features);desc.to_csv(analysis/"offensive_recognition_descriptive.csv",index=False,lineterminator="\n")
    metrics,predictions,comparisons,coefficients=fit_models(features)
    metrics.to_csv(analysis/"offensive_recognition_model_metrics.csv",index=False,lineterminator="\n",float_format="%.12g")
    predictions.to_csv(analysis/"offensive_recognition_predictions.csv",index=False,lineterminator="\n",float_format="%.12g")
    comparisons.to_csv(artifacts/"model_comparisons.csv",index=False,lineterminator="\n",float_format="%.12g")
    coefficients.to_csv(artifacts/"model_coefficients.csv",index=False,lineterminator="\n",float_format="%.12g")
    secondary=secondary_analyses(features,metrics,comparisons)
    _write_json(artifacts/"secondary_analyses.json",secondary)
    figures(features,desc,artifacts)
    report(root,audit,metrics,comparisons,coefficients,secondary)
    after={p.name:_sha256(p) for p in sorted((root/"data/processed").glob("*")) if p.is_file()}
    if before != after:
        raise RuntimeError("Sprint 1 accepted outputs changed during Sprint 2")
    # Finder metadata is not a research artifact and must never perturb the
    # accepted manifest or downstream Sprint 3 snapshot hash.
    outputs=sorted(
        [p for p in list(analysis.glob("*"))+list(artifacts.glob("*")) if not p.name.startswith(".")]
        + [root/"docs/sprint2_offensive_recognition_report.md"]
    )
    manifest={
        "analysis_version":"offensive_recognition_v1","pilot_start":PILOT_START,"pilot_end":PILOT_END,
        "full_season_expansion_performed":False,"random_seed":SEED,"cv_repeats":CV_REPEATS,"cv_folds":CV_FOLDS,
        "minimum_rate_display_n":MIN_DISPLAY_N,"sprint1_processed_sha256":before,
        "output_sha256":{str(p.relative_to(root)):_sha256(p) for p in outputs if p.is_file() and p.name!="run_manifest.json"},
    }
    _write_json(artifacts/"run_manifest.json",manifest)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--start",default=PILOT_START,choices=[PILOT_START],help="Sprint 2 is pilot-only")
    parser.add_argument("--end",default=PILOT_END,choices=[PILOT_END],help="Sprint 2 is pilot-only")
    args=parser.parse_args()
    if (args.start,args.end)!=(PILOT_START,PILOT_END): raise SystemExit("Sprint 2 may not expand beyond the pilot")
    run(args.root)
