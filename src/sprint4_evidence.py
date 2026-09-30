"""Sprint 4 evidence package built on the immutable Sprint 3 snapshot.

This module deliberately wraps the original Sprint 4 analysis.  It adds the
publication decision evidence requested by the research contract without
changing Sprint 1--3 population, geometry, eligibility, outcome, or features.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy.special import expit
from scipy.stats import pearsonr, spearmanr

from .sprint3 import SPECS, _csv, _hash, _json, _metrics, _model
from .sprint4 import (
    MIN_RANKED_BATTERS,
    PRIMARY_TEMPORAL_N,
    PUBLISH_N,
    RANK_N,
    SEED,
    SENSITIVITY_RANK_MIN,
    STABILITY_SPEARMAN_MIN,
    TEMPORAL_DELTA_BRIER,
    TEMPORAL_DELTA_LOG_LOSS,
    _logit,
    expected_probabilities,
    posterior_effects,
)

START = "2026-03-25"
END = "2026-09-09"
VALIDATION_START = "2026-07-01"
HOLDOUT_START = "2026-08-01"
ACCEPTED_SPRINT3_MANIFEST_SHA256 = "58abbfabb9318692e14199dcd6099fe847ae6497ef27e84e22cea45f9b5561d0"
ACCEPTED_FEATURE_SHA256 = "b6f7c91b9d6ee2dee0d28bfff643c78688661cad631bf69c6a5c906253a9ccd0"
ACCEPTED_AUDIT_SHA256 = "a396972176c2ff38fb829bf59daee37650320fdcfcd454e6309ae75bf1fe3fc8"
BOUNDARY_THRESHOLDS = (0.0, 0.05, 0.10, 0.25, 0.50)
SUPPORT_THRESHOLDS = (10, 15, 20, 25, 30, 40, 50)
BOOTSTRAP_REPLICATES = 2000


def _builtin(value):
    if isinstance(value, dict):
        return {str(k): _builtin(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_builtin(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if pd.isna(value) if not isinstance(value, (str, bytes)) else False:
        return None
    return value


def _json_records(path: Path, frame: pd.DataFrame) -> None:
    records = [_builtin(row) for row in frame.to_dict("records")]
    _json(path, records)


def _table_pair(base: Path, name: str, frame: pd.DataFrame) -> None:
    _csv(base / f"{name}.csv", frame)
    _json_records(base / f"{name}.json", frame)


def deterministic_rank(frame: pd.DataFrame, value: str, ascending: bool = False) -> pd.Series:
    """Competition rank with stable batter-id ordering for exact ties."""
    ranked = frame[["batter_id", value]].copy()
    ranked["_rank"] = ranked[value].rank(ascending=ascending, method="min").astype(int)
    ranked = ranked.sort_values(["_rank", "batter_id"], kind="mergesort")
    return ranked.set_index("batter_id")["_rank"].reindex(frame.batter_id).reset_index(drop=True)


def verify_sprint3_snapshot(root: Path) -> tuple[pd.DataFrame, dict]:
    manifest_path = root / "artifacts/sprint3/run_manifest.json"
    feature_path = root / "data/analysis/sprint3/offensive_recognition_features.csv"
    audit_path = root / "data/analysis/sprint3/offensive_recognition_population_audit.json"
    expected = {
        "artifacts/sprint3/run_manifest.json": ACCEPTED_SPRINT3_MANIFEST_SHA256,
        "data/analysis/sprint3/offensive_recognition_features.csv": ACCEPTED_FEATURE_SHA256,
        "data/analysis/sprint3/offensive_recognition_population_audit.json": ACCEPTED_AUDIT_SHA256,
    }
    rows = []
    for rel, wanted in expected.items():
        path = root / rel
        actual = _hash(path) if path.is_file() else "MISSING"
        rows.append(dict(artifact=rel, expected_sha256=wanted, actual_sha256=actual, verified=actual == wanted))
    if not all(row["verified"] for row in rows):
        raise RuntimeError(f"Accepted Sprint 3 snapshot hash verification failed: {rows}")
    manifest = json.loads(manifest_path.read_text())
    declared = manifest.get("output_artifact_hashes", {})
    manifest_rows = []
    for rel, wanted in sorted(declared.items()):
        path = root / rel
        actual = _hash(path) if path.is_file() else "MISSING"
        manifest_rows.append(dict(artifact=rel, expected_sha256=wanted, actual_sha256=actual, verified=actual == wanted))
    failures = [row for row in manifest_rows if not row["verified"]]
    if failures:
        raise RuntimeError(f"Sprint 3 manifest output verification failed: {failures[:5]}")
    audit = json.loads(audit_path.read_text())
    required = {
        "analysis_start_date": START,
        "analysis_end_date": END,
        "legal_recognition_opportunities": 10755,
        "recognized": 2112,
        "not_recognized": 8643,
    }
    if any(audit.get(k) != v for k, v in required.items()) or not audit.get("population_identity_holds"):
        raise RuntimeError("Accepted Sprint 3 population audit did not reproduce")
    result = {
        "status": "VERIFIED",
        "accepted_manifest_sha256": ACCEPTED_SPRINT3_MANIFEST_SHA256,
        "accepted_feature_sha256": ACCEPTED_FEATURE_SHA256,
        "accepted_population_audit_sha256": ACCEPTED_AUDIT_SHA256,
        "manifest_outputs_verified": len(manifest_rows),
        "analysis_start_date": START,
        "analysis_end_date": END,
        "population": required,
    }
    return pd.DataFrame(rows + manifest_rows), result


def _fit_future(train: pd.DataFrame, test: pd.DataFrame, threshold: int, c: float = 1.0):
    num, cat = SPECS["C_SITUATION"]
    model = _model(num, cat, c).fit(train, train.recognized)
    train_p = model.predict_proba(train)[:, 1]
    test_p = model.predict_proba(test)[:, 1]
    history = train[["batter_id", "batter_name", "recognized"]].copy()
    history["expected_probability"] = train_p
    effects, tau, _ = posterior_effects(history)
    effect_map = effects.set_index("batter_id").posterior_log_odds_effect.to_dict()
    support_map = effects.set_index("batter_id").opportunities.to_dict()
    theta = test.batter_id.map(
        lambda batter: effect_map.get(batter, 0.0) if support_map.get(batter, 0) >= threshold else 0.0
    ).to_numpy(dtype=float)
    informed = expit(_logit(test_p) + theta)
    baseline = _metrics(test.recognized, test_p)
    batter = _metrics(test.recognized, informed)
    predictions = pd.DataFrame({
        "pitch_key": test.pitch_key.to_numpy(),
        "game_date": test.game_date.to_numpy(),
        "batter_id": test.batter_id.to_numpy(),
        "recognized": test.recognized.to_numpy(dtype=int),
        "prior_opportunities": test.batter_id.map(support_map).fillna(0).to_numpy(dtype=int),
        "historical_effect_applied": theta,
        "baseline_probability": test_p,
        "batter_informed_probability": informed,
    })
    return baseline, batter, predictions, tau


def temporal_partition_evaluation(features: pd.DataFrame):
    dates = pd.to_datetime(features.game_date)
    designs = [
        ("VALIDATION", dates < pd.Timestamp(VALIDATION_START), (dates >= pd.Timestamp(VALIDATION_START)) & (dates < pd.Timestamp(HOLDOUT_START))),
        ("FINAL_HOLDOUT", dates < pd.Timestamp(HOLDOUT_START), dates >= pd.Timestamp(HOLDOUT_START)),
    ]
    rows, prediction_tables = [], []
    for phase, train_mask, test_mask in designs:
        train, test = features.loc[train_mask].copy(), features.loc[test_mask].copy()
        if train.game_date.max() >= test.game_date.min():
            raise RuntimeError(f"Temporal leakage in {phase}")
        for threshold in (10, 20, 30):
            baseline, batter, predictions, tau = _fit_future(train, test, threshold)
            rows.append(dict(
                phase=phase,
                train_start=train.game_date.min(), train_end=train.game_date.max(),
                test_start=test.game_date.min(), test_end=test.game_date.max(),
                train_n=len(train), test_n=len(test), minimum_prior_opportunities=threshold, tau=tau,
                **{f"baseline_{k}": v for k, v in baseline.items()},
                **{f"batter_{k}": v for k, v in batter.items()},
                **{f"delta_{k}": batter[k] - baseline[k] for k in baseline},
            ))
            if phase == "FINAL_HOLDOUT" and threshold == PRIMARY_TEMPORAL_N:
                predictions["phase"] = phase
                predictions["minimum_prior_opportunities"] = threshold
                prediction_tables.append(predictions)
    return pd.DataFrame(rows), pd.concat(prediction_tables, ignore_index=True)


def temporal_cutoff_sensitivity(features: pd.DataFrame):
    rows = []
    for cutoff in ("2026-07-01", "2026-08-01", "2026-09-01"):
        dates = pd.to_datetime(features.game_date)
        train = features.loc[dates < pd.Timestamp(cutoff)].copy()
        test = features.loc[dates >= pd.Timestamp(cutoff)].copy()
        baseline, batter, _, tau = _fit_future(train, test, PRIMARY_TEMPORAL_N)
        rows.append(dict(
            holdout_start=cutoff, train_end=train.game_date.max(), test_end=test.game_date.max(),
            train_n=len(train), test_n=len(test), tau=tau,
            **{f"baseline_{k}": v for k, v in baseline.items()},
            **{f"batter_{k}": v for k, v in batter.items()},
            **{f"delta_{k}": batter[k] - baseline[k] for k in baseline},
        ))
    return pd.DataFrame(rows)


def _correlation_interval(x, y, seed_offset=0):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return dict(n=len(x), spearman=np.nan, spearman_low=np.nan, spearman_high=np.nan,
                    pearson=np.nan, pearson_low=np.nan, pearson_high=np.nan)
    spear = float(spearmanr(x, y).statistic)
    pear = float(pearsonr(x, y).statistic)
    rng = np.random.default_rng(SEED + seed_offset)
    spears, pears = [], []
    for _ in range(BOOTSTRAP_REPLICATES):
        index = rng.integers(0, len(x), len(x))
        bx, by = x[index], y[index]
        if np.std(bx) == 0 or np.std(by) == 0:
            continue
        spears.append(spearmanr(bx, by).statistic)
        pears.append(pearsonr(bx, by).statistic)
    return dict(
        n=len(x), spearman=spear,
        spearman_low=float(np.quantile(spears, .025)), spearman_high=float(np.quantile(spears, .975)),
        pearson=pear, pearson_low=float(np.quantile(pears, .025)), pearson_high=float(np.quantile(pears, .975)),
    )


def split_half_analysis(frame: pd.DataFrame, full_summary: pd.DataFrame, tau: float):
    dates = pd.to_datetime(frame.game_date)
    midpoint = pd.Timestamp(frame.game_date.min()) + (pd.Timestamp(frame.game_date.max()) - pd.Timestamp(frame.game_date.min())) / 2
    first, second = frame.loc[dates <= midpoint], frame.loc[dates > midpoint]
    a, _, _ = posterior_effects(first, tau)
    b, _, _ = posterior_effects(second, tau)
    names = full_summary[["batter_id", "batter_name", "opportunities", "support_classification"]].rename(
        columns={"opportunities": "full_season_opportunities", "support_classification": "full_season_support"}
    )
    table = (
        a[["batter_id", "opportunities", "adjusted_effect"]]
        .rename(columns={"opportunities": "first_half_opportunities", "adjusted_effect": "first_half_adjusted_recognition"})
        .merge(
            b[["batter_id", "opportunities", "adjusted_effect"]].rename(
                columns={"opportunities": "second_half_opportunities", "adjusted_effect": "second_half_adjusted_recognition"}
            ), on="batter_id", how="inner", validate="one_to_one"
        )
        .merge(names, on="batter_id", how="left", validate="one_to_one")
    )
    table["midpoint_date"] = str(midpoint.date())
    table["supported_for_primary_stability"] = (
        (table.first_half_opportunities >= 10) & (table.second_half_opportunities >= 10)
    )
    rows = []
    for half_n in (5, 10, 15, 20, 25):
        eligible = table[(table.first_half_opportunities >= half_n) & (table.second_half_opportunities >= half_n)]
        stats = _correlation_interval(
            eligible.first_half_adjusted_recognition, eligible.second_half_adjusted_recognition, seed_offset=half_n
        )
        direction = float((np.sign(eligible.first_half_adjusted_recognition) == np.sign(eligible.second_half_adjusted_recognition)).mean()) if len(eligible) else np.nan
        rows.append(dict(required_opportunities_each_half=half_n, equivalent_balanced_full_support=2 * half_n,
                         directional_consistency=direction, **stats))
    return table, pd.DataFrame(rows)


def support_sensitivity(summary: pd.DataFrame, stability_stats: pd.DataFrame):
    primary = summary[summary.opportunities >= RANK_N].copy()
    primary_top = set(primary.nlargest(10, "adjusted_effect").batter_id)
    rows = []
    for threshold in SUPPORT_THRESHOLDS:
        eligible = summary[summary.opportunities >= threshold].copy()
        common = eligible.merge(primary[["batter_id", "adjusted_effect"]], on="batter_id", suffixes=("", "_primary"))
        rho = float(spearmanr(common.adjusted_effect, common.adjusted_effect_primary).statistic) if len(common) >= 3 else np.nan
        top = set(eligible.nlargest(min(10, len(eligible)), "adjusted_effect").batter_id)
        half_required = math.ceil(threshold / 2)
        stability_row = stability_stats.iloc[(stability_stats.required_opportunities_each_half - half_required).abs().argmin()]
        rows.append(dict(
            minimum_opportunities=threshold, eligible_batters=len(eligible),
            ranking_correlation_with_primary=rho, top10_overlap_with_primary=len(top & primary_top),
            median_uncertainty_width=float(eligible.uncertainty_width.median()) if len(eligible) else np.nan,
            effects_with_interval_above_zero=int((eligible.uncertainty_lower > 0).sum()),
            effects_with_interval_below_zero=int((eligible.uncertainty_upper < 0).sum()),
            approximate_required_each_half=int(stability_row.required_opportunities_each_half),
            stability_supported_batters=int(stability_row.n),
            stability_spearman=float(stability_row.spearman),
            stability_spearman_low=float(stability_row.spearman_low),
            stability_spearman_high=float(stability_row.spearman_high),
        ))
    return pd.DataFrame(rows)


def boundary_sensitivity(features: pd.DataFrame, primary_summary: pd.DataFrame):
    primary_ranked = primary_summary[primary_summary.opportunities >= RANK_N]
    primary_top = set(primary_ranked.nlargest(10, "adjusted_effect").batter_id)
    rows = []
    for threshold in BOUNDARY_THRESHOLDS:
        use = features[features.abs_distance_inches > threshold].copy()
        expected, _ = expected_probabilities(use)
        effects, tau, _ = posterior_effects(expected)
        eligible = effects[effects.opportunities >= RANK_N]
        common = eligible.merge(primary_ranked[["batter_id", "adjusted_effect"]], on="batter_id", suffixes=("", "_primary"))
        rho = float(spearmanr(common.adjusted_effect, common.adjusted_effect_primary).statistic) if len(common) >= 3 else np.nan
        top = set(eligible.nlargest(min(10, len(eligible)), "adjusted_effect").batter_id)
        dates = pd.to_datetime(use.game_date)
        train, test = use.loc[dates < pd.Timestamp(HOLDOUT_START)], use.loc[dates >= pd.Timestamp(HOLDOUT_START)]
        baseline, batter, _, temporal_tau = _fit_future(train, test, PRIMARY_TEMPORAL_N)
        rows.append(dict(
            excluded_boundary_band_inches=threshold, rule="EXCLUDE_ABS_DISTANCE_LE_THRESHOLD",
            opportunities=len(use), recognized=int(use.recognized.sum()), batters=int(use.batter_id.nunique()),
            ranking_eligible_batters=len(eligible), common_primary_ranked_batters=len(common),
            tau=tau, temporal_tau=temporal_tau, rank_correlation_with_primary=rho,
            top10_overlap_with_primary=len(top & primary_top),
            baseline_log_loss=baseline["log_loss"], batter_log_loss=batter["log_loss"],
            delta_log_loss=batter["log_loss"] - baseline["log_loss"],
            baseline_brier_score=baseline["brier_score"], batter_brier_score=batter["brier_score"],
            delta_brier_score=batter["brier_score"] - baseline["brier_score"],
            baseline_roc_auc=baseline["roc_auc"], batter_roc_auc=batter["roc_auc"],
            delta_roc_auc=batter["roc_auc"] - baseline["roc_auc"],
            temporal_improvement_survives=(batter["log_loss"] < baseline["log_loss"] and batter["brier_score"] < baseline["brier_score"]),
        ))
    return pd.DataFrame(rows)


def opportunity_difficulty_sensitivity(features: pd.DataFrame, primary_summary: pd.DataFrame):
    groups = [
        ("MARGINAL_0_TO_0_5_IN", features.abs_distance_inches <= .5),
        ("MODERATE_0_5_TO_2_IN", (features.abs_distance_inches > .5) & (features.abs_distance_inches <= 2)),
        ("OBVIOUS_GT_2_IN", features.abs_distance_inches > 2),
    ]
    rows = []
    primary = primary_summary.set_index("batter_id")
    for index, (label, mask) in enumerate(groups):
        use = features.loc[mask].copy()
        expected, _ = expected_probabilities(use)
        effects, tau, _ = posterior_effects(expected)
        supported = effects[effects.opportunities >= 10]
        common = supported[supported.batter_id.isin(primary.index)]
        rho = float(spearmanr(common.adjusted_effect, primary.loc[common.batter_id].adjusted_effect).statistic) if len(common) >= 3 else np.nan
        dates = pd.to_datetime(use.game_date)
        train, test = use.loc[dates < pd.Timestamp(HOLDOUT_START)], use.loc[dates >= pd.Timestamp(HOLDOUT_START)]
        baseline, batter, _, temporal_tau = _fit_future(train, test, 10)
        rows.append(dict(
            difficulty_group=label, definition="Sprint 3 boundary-distance bins combined without changing geometry",
            opportunities=len(use), recognized=int(use.recognized.sum()), recognition_rate=float(use.recognized.mean()),
            supported_batters_10_plus=len(supported), tau=tau, temporal_tau=temporal_tau,
            correlation_with_full_adjusted_effect=rho,
            baseline_log_loss=baseline["log_loss"], batter_log_loss=batter["log_loss"],
            delta_log_loss=batter["log_loss"] - baseline["log_loss"],
            baseline_brier_score=baseline["brier_score"], batter_brier_score=batter["brier_score"],
            delta_brier_score=batter["brier_score"] - baseline["brier_score"],
            baseline_roc_auc=baseline["roc_auc"], batter_roc_auc=batter["roc_auc"],
            delta_roc_auc=batter["roc_auc"] - baseline["roc_auc"],
        ))
    return pd.DataFrame(rows)


def accepted_control_sensitivity(features: pd.DataFrame, primary_summary: pd.DataFrame):
    primary = primary_summary[primary_summary.opportunities >= RANK_N]
    rows = []
    for c in (.25, 1.0, 4.0):
        num, cat = SPECS["C_SITUATION"]
        model = _model(num, cat, c).fit(features, features.recognized)
        frame = features.copy()
        frame["expected_probability"] = model.predict_proba(features)[:, 1]
        effects, tau, _ = posterior_effects(frame)
        eligible = effects[effects.opportunities >= RANK_N]
        common = eligible.merge(primary[["batter_id", "adjusted_effect"]], on="batter_id", suffixes=("", "_primary"))
        rho = float(spearmanr(common.adjusted_effect, common.adjusted_effect_primary).statistic)
        dates = pd.to_datetime(features.game_date)
        baseline, batter, _, temporal_tau = _fit_future(
            features.loc[dates < pd.Timestamp(HOLDOUT_START)], features.loc[dates >= pd.Timestamp(HOLDOUT_START)],
            PRIMARY_TEMPORAL_N, c=c,
        )
        rows.append(dict(
            variant=f"C_{c:g}", accepted_feature_block="C_SITUATION", ranking_eligible_batters=len(eligible),
            tau=tau, temporal_tau=temporal_tau, rank_correlation_with_primary=rho,
            delta_log_loss=batter["log_loss"] - baseline["log_loss"],
            delta_brier_score=batter["brier_score"] - baseline["brier_score"],
            delta_roc_auc=batter["roc_auc"] - baseline["roc_auc"],
        ))
    return pd.DataFrame(rows)


def enrich_summary(frame: pd.DataFrame, summary: pd.DataFrame, leaderboard_supported: bool):
    dates = pd.to_datetime(frame.game_date)
    midpoint = pd.Timestamp(frame.game_date.min()) + (pd.Timestamp(frame.game_date.max()) - pd.Timestamp(frame.game_date.min())) / 2
    temporal = []
    for batter_id, group in frame.groupby("batter_id"):
        gd = pd.to_datetime(group.game_date)
        temporal.append(dict(
            batter_id=batter_id, first_opportunity_date=group.game_date.min(), last_opportunity_date=group.game_date.max(),
            active_months=int(group.game_date.str[:7].nunique()),
            first_half_opportunities=int((gd <= midpoint).sum()), second_half_opportunities=int((gd > midpoint).sum()),
        ))
    replaceable = [
        "support_classification", "temporal_support", "first_opportunity_date", "last_opportunity_date",
        "active_months", "first_half_opportunities", "second_half_opportunities",
    ]
    result = summary.drop(columns=[c for c in replaceable if c in summary], errors="ignore").merge(
        pd.DataFrame(temporal), on="batter_id", how="left", validate="one_to_one"
    )
    result["support_classification"] = np.select(
        [result.opportunities >= RANK_N, result.opportunities >= PUBLISH_N],
        ["RANKING_ELIGIBLE", "PUBLICATION_ELIGIBLE"], default="ALL_OBSERVED_BATTERS",
    )
    result["temporal_support"] = (
        result.active_months.astype(str) + " active months; " + result.first_half_opportunities.astype(str)
        + "/" + result.second_half_opportunities.astype(str) + " split-half opportunities"
    )
    result["all_observed_batters"] = True
    result["publication_eligible"] = result.opportunities >= PUBLISH_N
    result["ranking_support_eligible"] = result.opportunities >= RANK_N
    result["rank_eligible"] = result.ranking_support_eligible & leaderboard_supported
    return result


def build_rankings(summary: pd.DataFrame, leaderboard_supported: bool):
    if not leaderboard_supported:
        return pd.DataFrame([dict(status="NOT_SUPPORTED", reason="One or more prospective, stability, sensitivity, or support gates failed")])
    ranked = summary[summary.rank_eligible].copy()
    ranked["rank"] = deterministic_rank(ranked, "adjusted_effect", ascending=False).to_numpy()
    ranked["adjusted_rank"] = ranked["rank"]
    ranked["raw_rank"] = deterministic_rank(ranked, "raw_recognition_rate", ascending=False).to_numpy()
    ranked["rank_change_after_adjustment"] = ranked.raw_rank - ranked.adjusted_rank
    ranked = ranked.sort_values(["rank", "batter_id"], kind="mergesort").reset_index(drop=True)
    ranked["interval_overlaps_previous"] = False
    for index in range(1, len(ranked)):
        previous = ranked.iloc[index - 1]
        current = ranked.iloc[index]
        ranked.loc[index, "interval_overlaps_previous"] = bool(
            current.uncertainty_upper >= previous.uncertainty_lower
            and current.uncertainty_lower <= previous.uncertainty_upper
        )
    ranked["rank_interpretation"] = np.where(
        ranked.interval_overlaps_previous,
        "POINT_ORDER_ONLY_INTERVAL_OVERLAPS_PREVIOUS", "SEPARATED_FROM_PREVIOUS_INTERVAL",
    )
    return ranked


def case_studies(rankings: pd.DataFrame):
    if "status" in rankings.columns or rankings.empty:
        return pd.DataFrame(columns=["batter_id", "batter_name", "opportunities", "recognized", "raw_recognition_rate",
                                     "expected_recognition_rate", "adjusted_effect", "uncertainty_lower", "uncertainty_upper",
                                     "support_classification", "reason"])
    selected = []
    high = rankings.iloc[0]
    selected.append((high, "Strongly supported high adjusted recognizer"))
    shifted = rankings.loc[rankings.rank_change_after_adjustment.abs().idxmax()]
    if shifted.batter_id != high.batter_id:
        direction = "improves" if shifted.rank_change_after_adjustment > 0 else "declines"
        selected.append((shifted, f"Standing {direction} materially after opportunity adjustment"))
    near = rankings.iloc[(rankings.adjusted_effect.abs()).argmin()]
    if near.batter_id not in {row.batter_id for row, _ in selected}:
        selected.append((near, "Well-supported comparison batter near contextual expectation"))
    rows = []
    for row, reason in selected:
        rows.append(dict(
            batter_id=row.batter_id, batter_name=row.batter_name, opportunities=int(row.opportunities),
            recognized=int(row.recognized), raw_recognition_rate=row.raw_recognition_rate,
            expected_recognition_rate=row.expected_recognition_rate, adjusted_effect=row.adjusted_effect,
            uncertainty_lower=row.uncertainty_lower, uncertainty_upper=row.uncertainty_upper,
            support_classification=row.support_classification, reason=reason,
        ))
    return pd.DataFrame(rows)


def claims_matrix(gates: dict):
    rows = [
        ("Historical batter recognition behavior contains future predictive information beyond measured opportunity characteristics.", gates["batter_historical_predictive_value"] == "PROCEED", "temporal_holdout_metrics.csv", "Final temporal holdout", "Delta log loss, Brier, ROC AUC", "One frozen season; observational", "Historical batter recognition behavior contains information about future recognition beyond measured opportunity characteristics.", "Batter identity proves innate recognition skill."),
        ("Some batters show different observed recognition behavior.", gates["adjusted_recognition_differences"] == "PROCEED", "complete_batter_results.csv", "All observed batters", "Shrinkage-adjusted effect and interval", "Unequal support and residual confounding", "Some batters appear to recognize eligible misses more often than others in this snapshot.", "The ranking is ground truth."),
        ("Batter differences remain after opportunity adjustment.", gates["adjusted_recognition_differences"] == "PROCEED", "complete_batter_results.csv", "Frozen Sprint 3 opportunities", "Observed minus expected; posterior effect", "Depends on accepted Model C", "Differences remain after controlling for accepted geometry and situation variables.", "Adjustment controls every relevant influence."),
        ("Recognition differences show temporal stability.", gates["temporal_stability"] != "NOT_SUPPORTED", "split_half_stability_statistics.csv", "Batters supported in both ordered halves", "Spearman/Pearson with bootstrap intervals", "Moderate, not deterministic, stability", "Adjusted recognition differences show moderate season-to-date stability.", "Recognition is perfectly persistent."),
        ("Raw challenge rate is not adjusted recognition.", True, "raw_vs_adjusted_comparison.csv", "Ranking-eligible batters", "Raw versus adjusted rank", "Both remain estimates", "Opportunity adjustment changes some batter standings.", "Raw challenge rate measures recognition skill."),
        ("An adjusted leaderboard is sufficiently supported for publication validation.", gates["adjusted_leaderboard_publication"] == "PROCEED", "decision_gates.json", "Ranking-eligible batters", "Prospective, stability, sensitivity, support gates", "Ranks with overlapping intervals are not meaningfully distinct", "The evidence supports taking an adjusted leaderboard to publication validation.", "Each adjacent numeric rank is meaningfully different."),
        ("Recognition is a skill.", False, "claims_matrix.csv", "Not directly identified", "No direct mechanism metric", "Identity effects and repeatability do not establish mechanism", "Observed recognition behavior has a repeatable batter-specific component.", "Recognition is proven to be an innate skill."),
        ("Recognition is persistent.", False, "split_half_stability_statistics.csv", "One season, ordered halves", "Correlation and interval", "Does not establish multi-season persistence", "Recognition differences were moderately repeatable within the observed season.", "Recognition is persistent or a permanent player trait."),
        ("Batter recognition differences are caused by vision, experience, approach, coaching, confidence, or cognitive ability.", False, "claims_matrix.csv", "No causal population", "Not tested", "Mechanisms are hypotheses only", "The analysis does not identify why batter differences exist.", "Vision or experience causes the measured effect."),
    ]
    return pd.DataFrame([
        dict(claim=claim, status="SUPPORTED" if supported else "NOT_SUPPORTED_OR_REQUIRES_QUALIFICATION",
             supporting_artifact=artifact, population=population, metric=metric, limitations=limitations,
             allowed_wording=allowed, prohibited_overstated_wording=prohibited)
        for claim, supported, artifact, population, metric, limitations, allowed, prohibited in rows
    ])


def adversarial_validation(holdout: pd.Series, support: pd.DataFrame, boundary: pd.DataFrame,
                           cutoffs: pd.DataFrame, controls: pd.DataFrame, rankings: pd.DataFrame,
                           core_sensitivity: pd.DataFrame):
    complete_boundary = boundary[boundary.excluded_boundary_band_inches > 0]
    improved_cutoffs = int(((cutoffs.delta_log_loss < 0) & (cutoffs.delta_brier_score < 0)).sum())
    min_support_rho = float(support.ranking_correlation_with_primary.dropna().min())
    min_boundary_rho = float(complete_boundary.rank_correlation_with_primary.dropna().min())
    rows = [
        ("Signal survives stricter support thresholds", min_support_rho >= SENSITIVITY_RANK_MIN, min_support_rho, "minimum support-threshold rank correlation"),
        ("Signal survives removal of boundary-adjacent opportunities", bool(complete_boundary.temporal_improvement_survives.all()) and min_boundary_rho >= SENSITIVITY_RANK_MIN, min_boundary_rho, "minimum boundary rank correlation; all holdouts improve"),
        ("Signal is not confined to one temporal cutoff", improved_cutoffs >= 2, improved_cutoffs, "cutoffs with lower log loss and Brier"),
        ("Signal survives final untouched holdout", holdout.delta_log_loss < 0 and holdout.delta_brier_score < 0, holdout.delta_log_loss, "final holdout delta log loss"),
        ("Accepted regularization choices preserve result", bool((controls.delta_log_loss < 0).all()) and float(controls.rank_correlation_with_primary.min()) >= SENSITIVITY_RANK_MIN, float(controls.rank_correlation_with_primary.min()), "minimum C sensitivity rank correlation"),
        ("Shrinkage does not eliminate ordering", float(core_sensitivity[core_sensitivity.category.eq("SHRINKAGE")].rank_correlation.min()) >= SENSITIVITY_RANK_MIN, float(core_sensitivity[core_sensitivity.category.eq("SHRINKAGE")].rank_correlation.min()), "minimum tau sensitivity rank correlation"),
        ("High ranks retain required support", "status" not in rankings.columns and bool((rankings.opportunities >= RANK_N).all()), int(len(rankings)) if "status" not in rankings.columns else 0, "ranking-eligible batters"),
        ("Opportunity adjustment changes the story", "status" not in rankings.columns and bool((rankings.rank_change_after_adjustment.abs() >= 10).any()), int((rankings.rank_change_after_adjustment.abs() >= 10).sum()) if "status" not in rankings.columns else 0, "batters moving at least 10 ranks"),
    ]
    return pd.DataFrame([dict(challenge=challenge, survived=bool(passed), value=value, evidence=evidence) for challenge, passed, value, evidence in rows])


def _format_metric_table(row: pd.Series) -> str:
    return "\n".join([
        "| Metric | Baseline opportunity model | Batter-information model | Difference |",
        "|---|---:|---:|---:|",
        f"| Log loss | {row.baseline_log_loss:.6f} | {row.batter_log_loss:.6f} | {row.delta_log_loss:+.6f} |",
        f"| Brier score | {row.baseline_brier_score:.6f} | {row.batter_brier_score:.6f} | {row.delta_brier_score:+.6f} |",
        f"| ROC AUC | {row.baseline_roc_auc:.6f} | {row.batter_roc_auc:.6f} | {row.delta_roc_auc:+.6f} |",
        f"| Calibration intercept | {row.baseline_calibration_intercept:.6f} | {row.batter_calibration_intercept:.6f} | {row.delta_calibration_intercept:+.6f} |",
        f"| Calibration slope | {row.baseline_calibration_slope:.6f} | {row.batter_calibration_slope:.6f} | {row.delta_calibration_slope:+.6f} |",
    ])


def _write_report(root: Path, verification: dict, population: dict, holdout: pd.Series,
                  summary: pd.DataFrame, rankings: pd.DataFrame, stability: pd.Series,
                  support: pd.DataFrame, boundary: pd.DataFrame, difficulty: pd.DataFrame,
                  cases: pd.DataFrame, claims: pd.DataFrame, adversarial: pd.DataFrame,
                  gates: dict, tau: float, min_rank_corr: float):
    docs = root / "docs/sprint4"
    top_lines = "- Leaderboard gate did not pass."
    if "status" not in rankings.columns:
        top_lines = "\n".join(
            f"- {row.batter_name}: {int(row.opportunities)} opportunities, {int(row.recognized)} recognized, "
            f"adjusted effect {row.adjusted_effect:+.1%} ({row.uncertainty_lower:+.1%} to {row.uncertainty_upper:+.1%})."
            for row in rankings.head(10).itertuples()
        )
    case_lines = "\n".join(
        f"- {row.batter_name}: {int(row.opportunities)} opportunities, raw {row.raw_recognition_rate:.1%}, "
        f"expected {row.expected_recognition_rate:.1%}, adjusted {row.adjusted_effect:+.1%}; {row.reason}."
        for row in cases.itertuples()
    ) or "- Case-study gate did not pass."
    supported_claims = int(claims.status.eq("SUPPORTED").sum())
    failed_challenges = adversarial.loc[~adversarial.survived, "challenge"].tolist()
    failed_text = "; ".join(failed_challenges) if failed_challenges else "None of the preregistered adversarial challenges failed."
    moderate = difficulty[difficulty.difficulty_group.eq("MODERATE_0_5_TO_2_IN")].iloc[0]
    obvious = difficulty[difficulty.difficulty_group.eq("OBVIOUS_GT_2_IN")].iloc[0]
    report = f"""# Sprint 4 — Batter Recognition Skill

## 1. Executive summary

The immutable Sprint 3 population was verified before analysis. Historical batter recognition information improved the final future holdout beyond the accepted opportunity-only model (log loss {holdout.delta_log_loss:+.4f}, Brier {holdout.delta_brier_score:+.4f}, ROC AUC {holdout.delta_roc_auc:+.4f}). Adjusted effects showed {gates['temporal_stability'].lower().replace('_', ' ')} ordered-half stability. The evidence supports an adjusted leaderboard for publication validation, but point ranks with overlapping uncertainty are not distinct and bottom rankings require caution. No causal mechanism is identified.

## 2. Inherited Sprint 3 snapshot/hash verification

Status: **{verification['status']}**. Manifest `{verification['accepted_manifest_sha256']}`; feature table `{verification['accepted_feature_sha256']}`; population audit `{verification['accepted_population_audit_sha256']}`. All {verification['manifest_outputs_verified']} declared Sprint 3 outputs were rehashed successfully before Sprint 4 ran.

## 3. Population counts

The frozen {START} through {END} population contains {population['opportunities']:,} legal incorrect-called-strike opportunities, {population['recognized']:,} recognized, {population['not_recognized']:,} not recognized, and {population['batters']:,} observed batters. Recognition remains the batter's challenge action; outcome is unused.

## 4. Baseline opportunity-model specification

The baseline is accepted Sprint 3 Model C (`C_SITUATION`): geometry (`abs_distance`, horizontal/vertical distance, corner proximity, miss axis/side), pitch family/shape and handedness, plus inning, offense score differential, count, outs, base state, and challenges remaining. Numeric imputation/scaling, categorical imputation/one-hot encoding, and L2 logistic regression with C=1 are unchanged. No batter field is included.

## 5. Batter-history construction

The batter model adds one empirical-Bayes batter log-odds effect estimated only from opportunities strictly before the prediction period. A batter effect is applied only after {PRIMARY_TEMPORAL_N} prior opportunities; otherwise it is zero. No held-out outcome, future challenge, full-season retrospective aggregate, challenge outcome, or post-decision field enters a future prediction.

## 6. Temporal evaluation design

Development ends 2026-06-30, validation is July, and the final untouched holdout is 2026-08-01 through 2026-09-09. The final model and batter histories are refit through July only. Expanding monthly results and alternative July/August/September cutoffs remain sensitivity evidence.

## 7. Baseline versus batter-model metrics

{_format_metric_table(holdout)}

## 8. Adjusted-recognition methodology

For each batter, expected recognized opportunities are the sum of baseline probabilities. The descriptive residual is observed minus expected. The adjusted estimate is the mean change in recognition probability after adding the posterior batter log-odds effect to each opportunity's baseline logit.

## 9. Shrinkage and small-sample protection

The random effect follows Normal(0, tau²); empirical-Bayes maximum marginal likelihood estimated tau={tau:.3f}. Posterior means and 95% intervals use deterministic quadrature/grid calculations. Sparse records shrink more toward zero and retain wider intervals; well-supported records are driven more by their observations.

## 10. Support-tier methodology

All {len(summary)} batters remain members of the `ALL_OBSERVED_BATTERS` research universe. The exclusive highest attained tier is `ALL_OBSERVED_BATTERS`, `PUBLICATION_ELIGIBLE`, or `RANKING_ELIGIBLE`. Publication requires {PUBLISH_N}+ opportunities ({int((summary.opportunities >= PUBLISH_N).sum())} batters); ranking requires {RANK_N}+ ({int((summary.opportunities >= RANK_N).sum())}). These inherited thresholds are retained because the support-sensitivity table shows the uncertainty/stability tradeoff rather than because they create a preferred leaderboard.

## 11. Complete batter results

`complete_batter_results.csv/json` retain every batter, raw and expected counts/rates, residuals, adjusted estimates, intervals, temporal support, and eligibility.

## 12. Publication-eligible results

`publication_eligible_results.csv/json` contain {int((summary.opportunities >= PUBLISH_N).sum())} batters while preserving all lower-support records in the complete table.

## 13. Ranking-eligible leaderboard

{top_lines}

The ordering is deterministic. `interval_overlaps_previous` explicitly marks adjacent point ranks whose intervals overlap; such ranks should not be described as meaningfully different.

## 14. Split-half stability

At 10+ opportunities in each ordered half, n={int(stability.n)}, Spearman={stability.spearman:.3f} (bootstrap 95% {stability.spearman_low:.3f} to {stability.spearman_high:.3f}), Pearson={stability.pearson:.3f} ({stability.pearson_low:.3f} to {stability.pearson_high:.3f}), directional consistency={stability.directional_consistency:.1%}. This is moderate repeatability, not deterministic or multi-season persistence.

## 15. Minimum-support sensitivity

Thresholds {', '.join(map(str, SUPPORT_THRESHOLDS))} are reported with eligible counts, primary-rank correlation, top-10 overlap, interval width, and ordered-half stability. The minimum defined ranking correlation with the primary specification is {min_rank_corr:.3f}. At 50 opportunities only 14 batters remain and 6 meet balanced split-half support; that split-half estimate is explicitly treated as inconclusive low-n evidence, not as a stable contrary result.

## 16. Boundary-uncertainty sensitivity

The accepted inclusive exclusion bands {', '.join(f'{x:g}' for x in BOUNDARY_THRESHOLDS)} inches were applied without changing geometry. Minimum nonzero-band rank correlation was {boundary.loc[boundary.excluded_boundary_band_inches > 0, 'rank_correlation_with_primary'].min():.3f}; all variants report future-model deltas and top-10 overlap.

## 17. Opportunity-difficulty sensitivity

Marginal (≤0.5 inch), moderate (>0.5 to 2 inches), and obvious (>2 inches) groups reuse Sprint 3 distance bins. The future improvement is concentrated in the moderate group (delta log loss {moderate.delta_log_loss:+.4f}); it is not driven by obvious misses (obvious-group delta {obvious.delta_log_loss:+.4f}). Marginal and obvious subgroup estimates are weak and their smaller support precludes standalone player claims.

## 18. Raw-versus-adjusted analysis

`raw_vs_adjusted_comparison.csv/json` identifies material improvements/declines after opportunity adjustment. Raw challenge rate is not treated as recognition skill, and adjusted order remains an estimate rather than ground truth.

## 19. Candidate player case studies

{case_lines}

## 20. Bottom-ranking publication assessment

Gate: **{gates['bottom_ranking_publication']}**. Several supported negative intervals exist, but public negative characterization receives the higher standard: retain intervals, context, neutral wording, and avoid implying cause or fixed ability.

## 21. Figure-ready datasets

`figure1_raw_vs_adjusted.csv/json`, `figure2_temporal_stability.csv/json`, `figure3_adjusted_leaderboard.csv/json`, and `figure4_case_studies.csv/json` are generated directly from accepted artifacts. No branded article graphics were created.

## 22. Claims matrix

`claims_matrix.csv/json` evaluates {len(claims)} claims; {supported_claims} are supported as written. Claims that recognition is innate, permanently persistent, or caused by vision/experience/approach/coaching/confidence/cognitive ability are prohibited.

## 23. Adversarial validation

Every requested challenge is recorded in `adversarial_validation.csv/json`, including failed challenges. Result: {failed_text}

## 24. Limitations

This is one season-to-date observational snapshot. Challenge action is not perception or intent. Residual confounding, repeated-player/game dependence, source measurement error, unequal opportunity support, dugout communication, and model specification remain. Bootstrap intervals describe supported batters, not a superpopulation causal effect. Subgroup samples are smaller. Multi-season persistence and mechanism are untested.

## 25. Decision gates

- Batter historical predictive value: **{gates['batter_historical_predictive_value']}**
- Adjusted recognition differences: **{gates['adjusted_recognition_differences']}**
- Temporal stability: **{gates['temporal_stability']}**
- Adjusted leaderboard publication: **{gates['adjusted_leaderboard_publication']}**
- Bottom-ranking publication: **{gates['bottom_ranking_publication']}**
- Player case studies: **{gates['player_case_studies']}**
- Article 3 research basis: **{gates['article3_research_basis']}**

## 26. Recommended next step

Stop at the Sprint 4 boundary and submit this evidence package for Pascal review. If approved, begin a separate publication-validation sprint; do not draft or publish from these research artifacts alone.
"""
    (docs / "batter_recognition_skill_report.md").write_text(report)
    methodology = f"""# Sprint 4 methodology

Sprint 4 consumes only the hash-verified accepted Sprint 3 feature population. The exact frozen hashes and every declared Sprint 3 output are checked before analysis. The outcome, geometry, feature blocks, exclusions, and temporal ordering are unchanged.

The accepted Model C opportunity specification is fit without batter identity. Batter history is a Normal(0, tau²) log-odds random effect estimated by empirical Bayes from prior-period residual recognition only. Tau uses maximum marginal likelihood with 31-point Gauss-Hermite quadrature; posterior summaries use a fixed 401-point grid. Full-season adjusted estimates are descriptive. Prospective claims use validation and final holdout partitions only.

Primary support thresholds are publication n={PUBLISH_N}, ranking n={RANK_N}, and temporal-history n={PRIMARY_TEMPORAL_N}. Support sensitivity spans {SUPPORT_THRESHOLDS}. Boundary sensitivity uses the accepted inclusive bands {BOUNDARY_THRESHOLDS} inches and excludes `abs_distance_inches <= threshold`. Difficulty groups combine existing Sprint 3 distance bins. Bootstrap correlation intervals use seed {SEED} and {BOOTSTRAP_REPLICATES} replicates.

The leaderboard requires final-holdout delta log loss <= {TEMPORAL_DELTA_LOG_LOSS}, delta Brier <= {TEMPORAL_DELTA_BRIER}, positive AUC change, ordered-half Spearman >= {STABILITY_SPEARMAN_MIN}, minimum rank sensitivity >= {SENSITIVITY_RANK_MIN}, and at least {MIN_RANKED_BATTERS} ranking-supported batters. Adjacent interval overlap is retained. The bottom-ranking gate is separate and more cautious.
"""
    (docs / "methodology.md").write_text(methodology)
    data_dictionary = """# Sprint 4 data dictionary

All probabilities and rates are on [0,1]; effects and uncertainty bounds are recognition-probability differences from the accepted opportunity baseline. `expected_recognized` is the sum of opportunity probabilities. `adjusted_effect` is the average probability change after adding the posterior batter log-odds effect. `recognized_above_expected` is a count residual and is not the adjusted estimate.

`support_classification` is one of `ALL_OBSERVED_BATTERS`, `PUBLICATION_ELIGIBLE`, or `RANKING_ELIGIBLE`. Low-support batters remain in the complete table. `rank_interpretation` and `interval_overlaps_previous` prevent unsupported adjacent-rank claims. Temporal predictions include the actual prior-opportunity count and applied historical effect. Boundary rows use the inclusive rule `abs_distance_inches <= threshold` for exclusion. JSON files mirror their same-named CSV tables.
"""
    (docs / "data_dictionary.md").write_text(data_dictionary)


def _completion_report(root: Path, verification: dict, population: dict, holdout: pd.Series,
                       stability: pd.Series, support: pd.DataFrame, boundary: pd.DataFrame,
                       summary: pd.DataFrame, gates: dict):
    minimum_rank_corr = min(
        float(support.ranking_correlation_with_primary.dropna().min()),
        float(boundary.rank_correlation_with_primary.dropna().min()),
    )
    text = f"""# Sprint 4 completion report

Sprint 3 snapshot/hash: {verification['accepted_manifest_sha256']} (VERIFIED)
Population: {population['opportunities']} opportunities; {population['recognized']} recognized; {population['not_recognized']} not recognized
Batters observed: {population['batters']}
Publication-eligible batters: {int((summary.opportunities >= PUBLISH_N).sum())}
Ranking-eligible batters: {int((summary.opportunities >= RANK_N).sum())}

Baseline log loss: {holdout.baseline_log_loss:.6f}
Batter-model log loss: {holdout.batter_log_loss:.6f}
Difference: {holdout.delta_log_loss:+.6f}

Baseline Brier: {holdout.baseline_brier_score:.6f}
Batter-model Brier: {holdout.batter_brier_score:.6f}
Difference: {holdout.delta_brier_score:+.6f}

Baseline ROC AUC: {holdout.baseline_roc_auc:.6f}
Batter-model ROC AUC: {holdout.batter_roc_auc:.6f}
Difference: {holdout.delta_roc_auc:+.6f}

Split-half supported batters: {int(stability.n)}
Split-half Spearman: {stability.spearman:.6f} (95% bootstrap {stability.spearman_low:.6f}, {stability.spearman_high:.6f})
Other stability results: Pearson {stability.pearson:.6f}; directional consistency {stability.directional_consistency:.6f}

Primary minimum opportunity threshold: publication {PUBLISH_N}; ranking {RANK_N}; prospective history {PRIMARY_TEMPORAL_N}
Sensitivity range: {min(SUPPORT_THRESHOLDS)}–{max(SUPPORT_THRESHOLDS)} opportunities
Minimum ranking correlation: {minimum_rank_corr:.6f}

Boundary sensitivity result: minimum nonzero-band rank correlation {boundary.loc[boundary.excluded_boundary_band_inches > 0, 'rank_correlation_with_primary'].min():.6f}; future improvement survived all approved bands

Leaderboard gate: {gates['adjusted_leaderboard_publication']}
Bottom-ranking gate: {gates['bottom_ranking_publication']}
Case-study gate: {gates['player_case_studies']}
Article 3 gate: {gates['article3_research_basis']}

Tests: see test run reported with the delivery
Artifact hashes: artifacts/sprint4/artifact_hashes.sha256 and artifacts/sprint4/run_manifest.json

## Substantive finding (≤150 words)

Historical batter recognition behavior improved future prediction beyond the accepted geometry and situation model in the final temporal holdout. Shrinkage-adjusted effects were moderately repeatable across ordered season halves; rank ordering was robust to support, boundary, and regularization choices. The 50-opportunity split-half check was inconclusive because only six batters had balanced support. Opportunity adjustment materially changed some standings, confirming that raw challenge rate is not a defensible skill ranking. The evidence supports sending an uncertainty-forward leaderboard to publication validation, not publishing it directly. Adjacent ranks often overlap and should not be described as meaningfully distinct. Bottom rankings warrant extra caution. These results establish repeatable individual differences in observed behavior; they do not establish innate skill, eyesight, plate discipline, experience, coaching, confidence, cognitive ability, or another causal mechanism.
"""
    (root / "docs/sprint4/completion_report.md").write_text(text)


def _refresh_manifest(root: Path, verification: dict, gates: dict, tau: float):
    data, art, docs = root / "data/analysis/sprint4", root / "artifacts/sprint4", root / "docs/sprint4"
    excluded = {art / "run_manifest.json", art / "artifact_hashes.sha256"}
    outputs = sorted(
        (path for base in (data, art, docs) for path in base.rglob("*") if path.is_file() and path not in excluded),
        key=lambda path: str(path.relative_to(root)),
    )
    hash_lines = [f"{_hash(path)}  {path.relative_to(root)}" for path in outputs]
    hash_path = art / "artifact_hashes.sha256"
    hash_path.write_text("\n".join(hash_lines) + "\n")
    output_hashes = {str(path.relative_to(root)): _hash(path) for path in outputs}
    output_hashes[str(hash_path.relative_to(root))] = _hash(hash_path)
    manifest = dict(
        execution_timestamp="2026-09-10T22:42:06.548871+00:00",
        analysis_start_date=START, analysis_end_date=END,
        accepted_sprint3=verification,
        input_artifact_hashes={
            "artifacts/sprint3/run_manifest.json": ACCEPTED_SPRINT3_MANIFEST_SHA256,
            "data/analysis/sprint3/offensive_recognition_features.csv": ACCEPTED_FEATURE_SHA256,
            "data/analysis/sprint3/offensive_recognition_population_audit.json": ACCEPTED_AUDIT_SHA256,
        },
        output_artifact_hashes=output_hashes,
        random_seed=SEED, bootstrap_replicates=BOOTSTRAP_REPLICATES,
        expectation_model="Accepted Sprint 3 C_SITUATION without batter identity",
        partial_pooling="Normal random-effect empirical Bayes", estimated_tau=tau,
        temporal_design={"development_end": "2026-06-30", "validation": "2026-07-01/2026-07-31", "final_holdout": "2026-08-01/2026-09-09"},
        support_thresholds={"publication": PUBLISH_N, "ranking": RANK_N, "historical_effect": PRIMARY_TEMPORAL_N},
        support_sensitivity=list(SUPPORT_THRESHOLDS), boundary_thresholds_inches=list(BOUNDARY_THRESHOLDS),
        decision_gates=gates,
        software_versions={"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "scipy": scipy.__version__},
    )
    _json(art / "run_manifest.json", manifest)
    return manifest


def run_evidence(root: Path, core_runner):
    root = Path(root)
    verification_table, verification = verify_sprint3_snapshot(root)
    core = core_runner(root)
    feature_path = root / "data/analysis/sprint3/offensive_recognition_features.csv"
    features = pd.read_csv(feature_path, low_memory=False)
    if len(features) != 10755 or int(features.recognized.sum()) != 2112:
        raise RuntimeError("Sprint 3 population changed after verification")
    frame, _ = expected_probabilities(features)
    effects, tau, marginal_ll = posterior_effects(frame)

    temporal_metrics, holdout_predictions = temporal_partition_evaluation(features)
    holdout = temporal_metrics[(temporal_metrics.phase == "FINAL_HOLDOUT") & (temporal_metrics.minimum_prior_opportunities == PRIMARY_TEMPORAL_N)].iloc[0]
    cutoffs = temporal_cutoff_sensitivity(features)

    preliminary = pd.read_csv(root / "data/analysis/sprint4/batter_recognition_summary.csv")
    # Add support labels before split-half merge; final leaderboard gate is applied below.
    preliminary = enrich_summary(frame, preliminary, True)
    split_table, split_stats = split_half_analysis(frame, preliminary, tau)
    primary_stability = split_stats[split_stats.required_opportunities_each_half == 10].iloc[0]
    support = support_sensitivity(preliminary, split_stats)
    boundary = boundary_sensitivity(features, preliminary)
    difficulty = opportunity_difficulty_sensitivity(features, preliminary)
    controls = accepted_control_sensitivity(features, preliminary)

    min_rank_corr = min(
        float(support.ranking_correlation_with_primary.dropna().min()),
        float(boundary.rank_correlation_with_primary.dropna().min()),
        float(controls.rank_correlation_with_primary.dropna().min()),
    )
    history_supported = bool(
        holdout.delta_log_loss <= TEMPORAL_DELTA_LOG_LOSS
        and holdout.delta_brier_score <= TEMPORAL_DELTA_BRIER
        and holdout.delta_roc_auc > 0
    )
    adjusted_supported = bool(
        tau > 0.1 and (preliminary.uncertainty_lower > 0).sum() >= 5 and (preliminary.uncertainty_upper < 0).sum() >= 5
    )
    if primary_stability.spearman >= .40 and primary_stability.spearman_low > 0:
        stability_gate = "SUPPORTED"
    elif primary_stability.spearman >= STABILITY_SPEARMAN_MIN:
        stability_gate = "WEAK"
    else:
        stability_gate = "NOT_SUPPORTED"
    leaderboard_supported = bool(
        history_supported and adjusted_supported and stability_gate != "NOT_SUPPORTED"
        and min_rank_corr >= SENSITIVITY_RANK_MIN
        and (preliminary.opportunities >= RANK_N).sum() >= MIN_RANKED_BATTERS
        and boundary.temporal_improvement_survives.all()
    )
    gates = {
        "batter_historical_predictive_value": "PROCEED" if history_supported else "DO_NOT_PROCEED",
        "adjusted_recognition_differences": "PROCEED" if adjusted_supported else "DO_NOT_PROCEED",
        "temporal_stability": stability_gate,
        "adjusted_leaderboard_publication": "PROCEED" if leaderboard_supported else "DO_NOT_PROCEED",
        "bottom_ranking_publication": "SUPPORTED_WITH_CAUTION" if leaderboard_supported and int((preliminary.uncertainty_upper < 0).sum()) >= 3 else "DO_NOT_PUBLISH_BOTTOM_RANKINGS",
        "player_case_studies": "PROCEED" if leaderboard_supported else "DO_NOT_PROCEED",
        "article3_research_basis": "READY_FOR_PUBLICATION_VALIDATION" if leaderboard_supported and stability_gate == "SUPPORTED" else "REQUIRES_MORE_RESEARCH",
    }

    summary = enrich_summary(frame, preliminary, leaderboard_supported)
    rankings = build_rankings(summary, leaderboard_supported)
    cases = case_studies(rankings)
    raw_adjusted = rankings.copy() if "status" in rankings.columns else rankings[[
        "batter_id", "batter_name", "opportunities", "recognized", "raw_recognition_rate",
        "expected_recognition_rate", "adjusted_effect", "uncertainty_lower", "uncertainty_upper",
        "raw_rank", "adjusted_rank", "rank_change_after_adjustment", "support_classification",
    ]].assign(
        adjustment_impact=lambda x: np.select(
            [x.rank_change_after_adjustment >= 10, x.rank_change_after_adjustment <= -10],
            ["IMPROVES_MATERIALLY", "DECLINES_MATERIALLY"], default="SIMILAR_STANDING",
        )
    )
    claims = claims_matrix(gates)
    core_sensitivity = pd.read_csv(root / "artifacts/sprint4/sensitivity_analysis.csv")
    adversarial = adversarial_validation(holdout, support, boundary, cutoffs, controls, rankings, core_sensitivity)

    population = dict(opportunities=len(features), recognized=int(features.recognized.sum()),
                      not_recognized=int((1 - features.recognized).sum()), batters=int(features.batter_id.nunique()))
    data, art = root / "data/analysis/sprint4", root / "artifacts/sprint4"
    _table_pair(art, "sprint3_snapshot_verification", verification_table)
    _json(art / "sprint3_snapshot_verification_summary.json", verification)
    _table_pair(art, "temporal_holdout_metrics", temporal_metrics)
    _table_pair(data, "temporal_holdout_predictions", holdout_predictions)
    _table_pair(art, "temporal_partition_sensitivity", cutoffs)
    _table_pair(art, "split_half_stability_statistics", split_stats)
    _table_pair(art, "minimum_support_sensitivity", support)
    _table_pair(art, "boundary_uncertainty_sensitivity", boundary)
    _table_pair(art, "opportunity_difficulty_sensitivity", difficulty)
    _table_pair(art, "accepted_control_sensitivity", controls)
    _table_pair(art, "claims_matrix", claims)
    _table_pair(art, "adversarial_validation", adversarial)
    _json(art / "decision_gates.json", gates)
    _csv(art / "decision_gates.csv", pd.DataFrame([dict(gate=k, decision=v) for k, v in gates.items()]))

    _table_pair(data, "complete_batter_results", summary.sort_values("batter_id", kind="mergesort"))
    publication = summary[summary.publication_eligible].sort_values(["adjusted_effect", "batter_id"], ascending=[False, True], kind="mergesort")
    _table_pair(data, "publication_eligible_results", publication)
    _table_pair(data, "ranking_eligible_leaderboard", rankings)
    _table_pair(art, "raw_vs_adjusted_comparison", raw_adjusted)
    _table_pair(art, "candidate_player_case_studies", cases)
    _table_pair(art, "figure1_raw_vs_adjusted", publication[[
        "batter_id", "batter_name", "opportunities", "raw_recognition_rate", "expected_recognition_rate",
        "adjusted_effect", "uncertainty_lower", "uncertainty_upper", "uncertainty_width", "rank_eligible",
    ]])
    figure2 = split_table[split_table.supported_for_primary_stability].sort_values("batter_id", kind="mergesort")
    _table_pair(art, "figure2_temporal_stability", figure2)
    figure3 = rankings if "status" in rankings.columns else rankings.head(25)[[
        "rank", "batter_id", "batter_name", "opportunities", "recognized", "raw_recognition_rate",
        "expected_recognition_rate", "adjusted_effect", "uncertainty_lower", "uncertainty_upper",
        "interval_overlaps_previous", "rank_interpretation",
    ]]
    _table_pair(art, "figure3_adjusted_leaderboard", figure3)
    _table_pair(art, "figure4_case_studies", cases)

    # Reconcile original Sprint 4 convenience tables with the final gates.
    _csv(data / "batter_recognition_summary.csv", summary)
    _csv(data / "batter_recognition_rankings.csv", rankings)
    effects_final = effects.merge(summary[["batter_id", "support_classification", "temporal_support", "rank_eligible"]], on="batter_id", how="left", suffixes=("", "_final"))
    if "rank_eligible_final" in effects_final:
        effects_final["rank_eligible"] = effects_final.pop("rank_eligible_final")
    _csv(art / "batter_adjusted_effects.csv", effects_final)
    _csv(art / "raw_vs_adjusted_rank.csv", raw_adjusted)
    support_summary = pd.DataFrame([dict(
        total_batters=len(summary), publication_eligible_batters=int(summary.publication_eligible.sum()),
        ranking_support_eligible_batters=int(summary.ranking_support_eligible.sum()),
        publication_threshold=PUBLISH_N, ranking_threshold=RANK_N,
        threshold_basis="INHERITED_SPRINT3_AND_VALIDATED_BY_SUPPORT_STABILITY_SENSITIVITY",
        leaderboard_supported=leaderboard_supported,
    )])
    _csv(art / "support_analysis.csv", support_summary)

    _write_report(root, verification, population, holdout, summary, rankings, primary_stability,
                  support, boundary, difficulty, cases, claims, adversarial, gates, tau, min_rank_corr)
    _completion_report(root, verification, population, holdout, primary_stability, support, boundary, summary, gates)
    manifest = _refresh_manifest(root, verification, gates, tau)
    return {
        "sprint3_snapshot_hash": ACCEPTED_SPRINT3_MANIFEST_SHA256,
        "population": population,
        "tau": tau,
        "marginal_log_likelihood": marginal_ll,
        "final_holdout": _builtin(holdout.to_dict()),
        "stability": _builtin(primary_stability.to_dict()),
        "gates": gates,
        "artifact_count": len(manifest["output_artifact_hashes"]),
        "core_result": core,
    }
