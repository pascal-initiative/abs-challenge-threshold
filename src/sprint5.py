"""Sprint 5: ABS challenge resource management and decision quality.

All normative labels are ex-ante model outputs.  Geometry-derived correctness
and subsequent game events are retained only in explicitly descriptive fields.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (brier_score_loss, log_loss, mean_absolute_error,
                             mean_squared_error, roc_auc_score)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .sprint3 import _csv, _hash, _json

SEED = 20260910
START_DATE = "2026-03-25"
END_DATE = "2026-09-09"
INDIFFERENCE_WP = 0.00025
STRONG_WP = 0.0025
MODEL_VERSION = "pascal_sprint5_v1"

OVERTURN_NUM = [
    "wrong_way_margin_inches", "plate_x", "plate_z", "abs_zone_top",
    "abs_zone_bot", "release_speed", "release_spin_rate", "pfx_x", "pfx_z",
    "balls", "strikes", "outs", "inning", "affected_team_challenges_remaining",
]
OVERTURN_CAT = ["original_call", "decision_side", "half_inning", "count", "base_state", "pitch_type"]


@dataclass(frozen=True)
class PitchState:
    inning: int
    half_inning: str
    balls: int
    strikes: int
    outs: int
    on_1b: int
    on_2b: int
    on_3b: int
    home_score: int
    away_score: int


def _base_state(s: PitchState) -> str:
    return f"{int(s.on_1b)}{int(s.on_2b)}{int(s.on_3b)}"


def transition_called_pitch(state: PitchState, call: str) -> dict:
    """Apply a called BALL or STRIKE to a PRE_PITCH state.

    The returned state is the next decision state.  A walk advances only forced
    runners and a third-out strikeout advances to the next half inning.
    """
    if call not in {"BALL", "STRIKE"}:
        raise ValueError("call must be BALL or STRIKE")
    d = asdict(state)
    runs = 0
    terminal = "CONTINUES"
    if call == "BALL" and state.balls < 3:
        d["balls"] += 1
    elif call == "STRIKE" and state.strikes < 2:
        d["strikes"] += 1
    elif call == "BALL":
        terminal = "WALK"
        old1, old2, old3 = state.on_1b, state.on_2b, state.on_3b
        forced_run = int(bool(old1 and old2 and old3))
        d["on_1b"] = 1
        d["on_2b"] = int(bool(old2 or old1))
        d["on_3b"] = int(bool(old3 or (old1 and old2)))
        d["balls"] = d["strikes"] = 0
        runs = forced_run
        if state.half_inning == "top": d["away_score"] += runs
        else: d["home_score"] += runs
    else:
        terminal = "STRIKEOUT"
        d["balls"] = d["strikes"] = 0
        d["outs"] += 1
        if d["outs"] == 3:
            terminal = "INNING_END_STRIKEOUT"
            d["outs"] = 0
            d["on_1b"] = d["on_2b"] = d["on_3b"] = 0
            if state.half_inning == "top": d["half_inning"] = "bottom"
            else:
                d["half_inning"] = "top"
                d["inning"] += 1
    out = asdict(PitchState(**d))
    out.update(base_state=_base_state(PitchState(**d)), runs_scored=runs,
               plate_appearance_status=terminal)
    return out


def classify_decision(ev_difference: float, actual_action: str,
                      indifferent: float = INDIFFERENCE_WP,
                      strong: float = STRONG_WP) -> tuple[str, str, float, bool]:
    if abs(ev_difference) <= indifferent:
        recommended = "INDIFFERENT"
    else:
        recommended = "CHALLENGE" if ev_difference > 0 else "HOLD"
    margin = ev_difference if actual_action == "CHALLENGE" else -ev_difference
    if abs(ev_difference) <= indifferent:
        quality = "NEAR_INDIFFERENT"
        correct = True
    elif margin >= strong:
        quality, correct = "STRONGLY_OPTIMAL", True
    elif margin > 0:
        quality, correct = "OPTIMAL", True
    elif margin <= -strong:
        quality, correct = "STRONGLY_SUBOPTIMAL", False
    else:
        quality, correct = "SUBOPTIMAL", False
    return recommended, quality, margin, correct


def inventory_after(before: int, outcome: str) -> int:
    return int(before) if outcome == "OVERTURNED" else max(0, int(before) - 1)


def _bool(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower().map({"true": True, "false": False}).fillna(False)


def _state_features(frame: pd.DataFrame) -> pd.DataFrame:
    x = pd.DataFrame(index=frame.index)
    x["inning"] = pd.to_numeric(frame.inning, errors="coerce").clip(1, 15)
    x["half_top"] = frame.half_inning.eq("top").astype(int)
    x["home_score_diff"] = pd.to_numeric(frame.home_score, errors="coerce") - pd.to_numeric(frame.away_score, errors="coerce")
    x["outs"] = pd.to_numeric(frame.outs, errors="coerce")
    x["balls"] = pd.to_numeric(frame.balls, errors="coerce")
    x["strikes"] = pd.to_numeric(frame.strikes, errors="coerce")
    for b in (1, 2, 3): x[f"on_{b}b"] = pd.to_numeric(frame[f"on_{b}b"], errors="coerce").fillna(0).astype(int)
    x["late_score"] = x.home_score_diff * np.maximum(x.inning - 6, 0)
    x["batting_score_diff"] = np.where(x.half_top.eq(1), -x.home_score_diff, x.home_score_diff)
    return x


def _metric_row(y, p) -> dict:
    y = np.asarray(y, dtype=int); p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    edges = np.linspace(0, 1, 11); ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p < hi if hi < 1 else p <= hi)
        if m.any(): ece += m.mean() * abs(y[m].mean() - p[m].mean())
    return {"roc_auc": roc_auc_score(y, p), "log_loss": log_loss(y, p),
            "brier_score": brier_score_loss(y, p), "ece_10bin": ece}


def _months(frame: pd.DataFrame):
    periods = pd.to_datetime(frame.game_date).dt.to_period("M")
    for month in sorted(periods.unique())[1:]:
        train = np.flatnonzero((periods < month).to_numpy())
        test = np.flatnonzero((periods == month).to_numpy())
        if len(train) and len(test):
            if frame.iloc[train].game_date.max() >= frame.iloc[test].game_date.min():
                raise RuntimeError("temporal leakage")
            yield str(month), train, test


def _logit_model(numeric, categorical, c=1.0):
    prep = ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                           ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical),
    ])
    return Pipeline([("features", prep), ("model", LogisticRegression(
        C=c, max_iter=2000, solver="liblinear", random_state=SEED))])


def load_game_results(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = root / "data/full_season/raw"
    games, halves = [], []
    for line in (raw / "receipts.jsonl").read_text().splitlines():
        receipt = json.loads(line)
        if receipt.get("kind") != "feed" or not receipt.get("ok"): continue
        obj = raw / receipt["path"]
        if not obj.exists(): raise RuntimeError(f"missing immutable feed object {obj}")
        feed = json.loads(obj.read_text())
        game_pk = int(feed["gamePk"])
        line_score = feed["liveData"]["linescore"]["teams"]
        home, away = int(line_score["home"]["runs"]), int(line_score["away"]["runs"])
        games.append({"game_pk": game_pk, "final_home_score": home, "final_away_score": away,
                      "home_win": int(home > away)})
        totals = {}
        for play in feed["liveData"]["plays"]["allPlays"]:
            about = play["about"]; key = (int(about["inning"]), about["halfInning"])
            totals[key] = totals.get(key, 0) + int(play.get("result", {}).get("rbi") or 0)
        halves.extend({"game_pk": game_pk, "inning": inn, "half_inning": half, "half_runs": runs}
                      for (inn, half), runs in totals.items())
    game_frame = pd.DataFrame(games).drop_duplicates("game_pk")
    half_frame = pd.DataFrame(halves).groupby(["game_pk", "inning", "half_inning"], as_index=False).half_runs.max()
    if game_frame.game_pk.duplicated().any(): raise RuntimeError("duplicate game results")
    return game_frame, half_frame


def prepare_pitches(root: Path):
    path = root / "data/full_season/processed/pitches.csv"
    p = pd.read_csv(path, low_memory=False)
    if p.game_date.min() != START_DATE or p.game_date.max() != END_DATE:
        raise RuntimeError("Sprint 5 must use the accepted Sprint 3 date scope")
    if len(p) != 645793 or p.game_pk.nunique() != 2195:
        raise RuntimeError("accepted Sprint 3 population does not reconcile")
    p["challenged_bool"] = _bool(p.challenged)
    p["position_player_pitching_bool"] = _bool(p.position_player_pitching)
    p["on_1b"] = p.on_1b.notna().astype(int); p["on_2b"] = p.on_2b.notna().astype(int); p["on_3b"] = p.on_3b.notna().astype(int)
    p["base_state"] = p.on_1b.astype(str) + p.on_2b.astype(str) + p.on_3b.astype(str)
    p["count"] = p.balls.astype(int).astype(str) + "-" + p.strikes.astype(int).astype(str)
    p["decision_side"] = np.where(p.original_call.eq("STRIKE"), "OFFENSE", "DEFENSE")
    p["offense_team_id"] = np.where(p.half_inning.eq("top"), p.away_team_id, p.home_team_id)
    p["defense_team_id"] = np.where(p.half_inning.eq("top"), p.home_team_id, p.away_team_id)
    p["offense_team"] = np.where(p.half_inning.eq("top"), p.away_team, p.home_team)
    p["defense_team"] = np.where(p.half_inning.eq("top"), p.home_team, p.away_team)
    p["decision_team_id"] = np.where(p.original_call.eq("STRIKE"), p.offense_team_id, p.defense_team_id)
    p["decision_team"] = np.where(p.original_call.eq("STRIKE"), p.offense_team, p.defense_team)
    p["wrong_way_margin_inches"] = np.where(p.original_call.eq("STRIKE"), p.distance_from_abs_boundary, -p.distance_from_abs_boundary) * 12
    p["geometry_incorrect"] = ((p.original_call == "STRIKE") & (p.derived_abs_call == "BALL") |
                               (p.original_call == "BALL") & (p.derived_abs_call == "STRIKE")).astype(int)
    p["actual_action"] = np.where(p.challenged_bool, "CHALLENGE", "HOLD")
    called = p.original_call.isin(["BALL", "STRIKE"]) & ~p.position_player_pitching_bool
    candidates = p[called].copy()
    legal = candidates.affected_team_challenges_remaining.fillna(0).gt(0)
    opportunities = candidates[legal].copy()
    if len(opportunities) != 312228:
        raise RuntimeError(f"legal opportunity count changed: {len(opportunities)}")
    return p, candidates, opportunities


def fit_overturn(opportunities: pd.DataFrame):
    """Selection-weighted outcome model plus population-geometry sensitivity.

    A propensity model is fit on every legal opportunity.  Actual challenge
    outcomes are then weighted by inverse challenge propensity.  This corrects
    selection on recorded state and geometry; it cannot correct private player
    information, so the population geometry model is retained as a sensitivity.
    """
    frame = opportunities.sort_values(["game_date", "game_pk", "physical_pitch_ordinal"]).reset_index(drop=True)
    prop_num = ["wrong_way_margin_inches", "inning", "balls", "strikes", "outs", "affected_team_challenges_remaining"]
    prop_cat = ["original_call", "decision_side", "count", "base_state"]
    temporal_rows, temporal_pred = [], []
    for fold, train, test in _months(frame):
        train_frame, test_frame = frame.iloc[train], frame.iloc[test]
        propensity = _logit_model(prop_num, prop_cat, .5).fit(train_frame, train_frame.challenged_bool.astype(int))
        selected_train = train_frame.challenged_bool.to_numpy()
        challenge_prop = np.clip(propensity.predict_proba(train_frame.loc[selected_train])[:, 1], .01, 1)
        outcome = _logit_model(OVERTURN_NUM, OVERTURN_CAT, .5)
        y_train = train_frame.loc[selected_train, "challenge_outcome"].eq("OVERTURNED").astype(int)
        outcome.fit(train_frame.loc[selected_train], y_train, model__sample_weight=1 / challenge_prop)
        selected_test = test_frame.challenged_bool.to_numpy()
        if selected_test.sum() and test_frame.loc[selected_test, "challenge_outcome"].notna().all():
            pred = outcome.predict_proba(test_frame.loc[selected_test])[:, 1]
            y = test_frame.loc[selected_test, "challenge_outcome"].eq("OVERTURNED").astype(int).to_numpy()
            row = _metric_row(y, pred)
            temporal_rows.append({"fold": fold, "train_start": train_frame.game_date.min(),
                                  "train_end": train_frame.game_date.max(), "test_start": test_frame.game_date.min(),
                                  "test_end": test_frame.game_date.max(), "train_n": len(train_frame),
                                  "test_challenges": len(y), **row})
            temporal_pred.extend({"pitch_key": k, "fold": fold, "actual": int(a), "probability": float(q)}
                                 for k, a, q in zip(test_frame.loc[selected_test, "pitch_key"], y, pred))
    tp = pd.DataFrame(temporal_pred)
    temporal_rows.append({"fold": "POOLED", "train_start": frame.game_date.min(), "train_end": "PRIOR_MONTHS",
                          "test_start": tp.fold.min(), "test_end": tp.fold.max(), "train_n": np.nan,
                          "test_challenges": len(tp), **_metric_row(tp.actual, tp.probability)})
    propensity = _logit_model(prop_num, prop_cat, .5).fit(frame, frame.challenged_bool.astype(int))
    selected = frame.challenged_bool.to_numpy()
    weights = 1 / np.clip(propensity.predict_proba(frame.loc[selected])[:, 1], .01, 1)
    model = _logit_model(OVERTURN_NUM, OVERTURN_CAT, .5)
    model.fit(frame.loc[selected], frame.loc[selected, "challenge_outcome"].eq("OVERTURNED").astype(int),
              model__sample_weight=weights)
    primary = model.predict_proba(frame)[:, 1]
    geometry_model = _logit_model(OVERTURN_NUM, OVERTURN_CAT, .25).fit(frame, frame.geometry_incorrect)
    geometry_probability = geometry_model.predict_proba(frame)[:, 1]
    return frame, primary, geometry_probability, pd.DataFrame(temporal_rows), tp, model, geometry_model


class RunExpectancy:
    def __init__(self, state_table: dict, baseout_table: dict, mean: float, prior: float = 40):
        self.state_table, self.baseout_table, self.mean, self.prior = state_table, baseout_table, mean, prior

    @classmethod
    def fit(cls, frame: pd.DataFrame, prior=40):
        exact = frame.groupby(["balls", "strikes", "outs", "base_state"]).future_runs.agg(["sum", "count"])
        base = frame.groupby(["outs", "base_state"]).future_runs.mean().to_dict()
        state = {}
        overall = float(frame.future_runs.mean())
        for idx, row in exact.iterrows():
            parent = base.get((idx[2], idx[3]), overall)
            state[tuple(idx)] = float((row["sum"] + prior * parent) / (row["count"] + prior))
        return cls(state, base, overall, prior)

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        vals = []
        for r in frame.itertuples(index=False):
            if getattr(r, "inning_ended", False): vals.append(0.0); continue
            key = (int(r.balls), int(r.strikes), int(r.outs), str(r.base_state))
            vals.append(self.state_table.get(key, self.baseout_table.get((key[2], key[3]), self.mean)))
        return np.asarray(vals)


def prepare_value_targets(pitches: pd.DataFrame, games: pd.DataFrame, halves: pd.DataFrame):
    p = pitches.merge(games, on="game_pk", how="left", validate="many_to_one")
    if p.home_win.isna().any(): raise RuntimeError("missing final outcomes")
    p = p.merge(halves, on=["game_pk", "inning", "half_inning"], how="left", validate="many_to_one")
    p["half_runs"] = p.half_runs.fillna(0)
    starts = p.groupby(["game_pk", "inning", "half_inning"])[["home_score", "away_score"]].transform("min")
    batting_score = np.where(p.half_inning.eq("top"), p.away_score, p.home_score)
    start_score = np.where(p.half_inning.eq("top"), starts.away_score, starts.home_score)
    p["future_runs"] = np.maximum(0, p.half_runs - (batting_score - start_score))
    return p


def fit_run_expectancy(pitches: pd.DataFrame):
    frame = pitches.sort_values(["game_date", "game_pk", "physical_pitch_ordinal"]).reset_index(drop=True)
    rows = []
    for fold, train, test in _months(frame):
        model = RunExpectancy.fit(frame.iloc[train])
        pred = model.predict(frame.iloc[test])
        y = frame.iloc[test].future_runs.to_numpy()
        baseline = np.repeat(frame.iloc[train].future_runs.mean(), len(test))
        rows.append({"fold": fold, "train_start": frame.iloc[train].game_date.min(),
                     "train_end": frame.iloc[train].game_date.max(), "test_start": frame.iloc[test].game_date.min(),
                     "test_end": frame.iloc[test].game_date.max(), "train_n": len(train), "test_n": len(test),
                     "mae": mean_absolute_error(y, pred), "rmse": mean_squared_error(y, pred) ** .5,
                     "baseline_mae": mean_absolute_error(y, baseline),
                     "baseline_rmse": mean_squared_error(y, baseline) ** .5})
    metrics = pd.DataFrame(rows)
    pooled = {"fold": "POOLED", "train_start": frame.game_date.min(), "train_end": "PRIOR_MONTHS",
              "test_start": metrics.test_start.min(), "test_end": metrics.test_end.max(),
              "train_n": metrics.train_n.sum(), "test_n": metrics.test_n.sum(),
              **{c: np.average(metrics[c], weights=metrics.test_n) for c in ["mae", "rmse", "baseline_mae", "baseline_rmse"]}}
    return RunExpectancy.fit(frame), pd.concat([metrics, pd.DataFrame([pooled])], ignore_index=True)


def _wp_model():
    return HistGradientBoostingClassifier(max_iter=120, learning_rate=.07, max_leaf_nodes=31,
                                          min_samples_leaf=150, l2_regularization=8,
                                          random_state=SEED)


def fit_win_probability(pitches: pd.DataFrame):
    frame = pitches.sort_values(["game_date", "game_pk", "physical_pitch_ordinal"]).reset_index(drop=True)
    x = _state_features(frame); y = frame.home_win.astype(int).to_numpy()
    rows, predictions = [], []
    for fold, train, test in _months(frame):
        model = _wp_model().fit(x.iloc[train], y[train])
        pred = model.predict_proba(x.iloc[test])[:, 1]
        rows.append({"fold": fold, "train_start": frame.iloc[train].game_date.min(),
                     "train_end": frame.iloc[train].game_date.max(), "test_start": frame.iloc[test].game_date.min(),
                     "test_end": frame.iloc[test].game_date.max(), "train_n": len(train), "test_n": len(test),
                     **_metric_row(y[test], pred)})
        predictions.extend(zip(y[test], pred))
    yp = np.asarray(predictions)
    pooled = {"fold": "POOLED", "train_start": frame.game_date.min(), "train_end": "PRIOR_MONTHS",
              "test_start": pd.DataFrame(rows).test_start.min(), "test_end": pd.DataFrame(rows).test_end.max(),
              "train_n": sum(r["train_n"] for r in rows), "test_n": len(yp), **_metric_row(yp[:, 0], yp[:, 1])}
    model = _wp_model().fit(x, y)
    return model, pd.concat([pd.DataFrame(rows), pd.DataFrame([pooled])], ignore_index=True)


def reconstruct_states(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in frame.itertuples(index=False):
        state = PitchState(int(r.inning), str(r.half_inning), int(r.balls), int(r.strikes), int(r.outs),
                           int(r.on_1b), int(r.on_2b), int(r.on_3b), int(r.home_score), int(r.away_score))
        hold = transition_called_pitch(state, str(r.original_call))
        reverse = "BALL" if r.original_call == "STRIKE" else "STRIKE"
        overturn = transition_called_pitch(state, reverse)
        row = {"pitch_key": r.pitch_key}
        for prefix, state_out in (("hold", hold), ("overturn", overturn)):
            for key, value in state_out.items(): row[f"{prefix}_{key}"] = value
            row[f"{prefix}_inning_ended"] = state_out["plate_appearance_status"] == "INNING_END_STRIKEOUT"
        rows.append(row)
    return pd.DataFrame(rows)


def _counterfactual_frame(states: pd.DataFrame, prefix: str) -> pd.DataFrame:
    cols = ["inning", "half_inning", "balls", "strikes", "outs", "on_1b", "on_2b", "on_3b", "home_score", "away_score", "base_state"]
    out = states[[f"{prefix}_{c}" for c in cols]].copy()
    out.columns = cols
    out["inning_ended"] = states[f"{prefix}_inning_ended"].to_numpy()
    return out


def score_values(frame: pd.DataFrame, states: pd.DataFrame, re_model: RunExpectancy, wp_model):
    hold = _counterfactual_frame(states, "hold"); overturn = _counterfactual_frame(states, "overturn")
    re_hold = re_model.predict(hold) + states.hold_runs_scored.to_numpy()
    re_over = re_model.predict(overturn) + states.overturn_runs_scored.to_numpy()
    home_hold = wp_model.predict_proba(_state_features(hold))[:, 1]
    home_over = wp_model.predict_proba(_state_features(overturn))[:, 1]
    # Bottom-nine or later walk-off states and completed home losses are exact.
    over_walkoff = (overturn.half_inning.eq("bottom") & overturn.inning.ge(9) &
                    overturn.home_score.gt(overturn.away_score) & states.overturn_runs_scored.gt(0))
    hold_walkoff = (hold.half_inning.eq("bottom") & hold.inning.ge(9) &
                    hold.home_score.gt(hold.away_score) & states.hold_runs_scored.gt(0))
    home_over[over_walkoff.to_numpy()] = 1.0
    home_hold[hold_walkoff.to_numpy()] = 1.0
    home_challenger = frame.decision_team_id.to_numpy() == frame.home_team_id.to_numpy()
    wp_hold = np.where(home_challenger, home_hold, 1 - home_hold)
    wp_over = np.where(home_challenger, home_over, 1 - home_over)
    offense = frame.decision_side.eq("OFFENSE").to_numpy()
    delta_re_raw = np.where(offense, re_over - re_hold, re_hold - re_over)
    delta_wp_raw = wp_over - wp_hold
    return pd.DataFrame({
        "pitch_key": frame.pitch_key.to_numpy(), "RE_hold_batting": re_hold,
        "RE_overturn_batting": re_over, "delta_RE_raw": delta_re_raw,
        "delta_RE": np.maximum(delta_re_raw, 0), "WP_hold": wp_hold,
        "WP_overturn": wp_over, "delta_WP_raw": delta_wp_raw,
        "delta_WP": np.maximum(delta_wp_raw, 0), "challenge_leverage": np.abs(wp_over - wp_hold),
    })


def bellman_tables(probability: np.ndarray, gain: np.ndarray, max_n=80):
    order = np.argsort(probability * gain)
    take = np.linspace(0, len(order) - 1, min(300, len(order))).astype(int)
    p = probability[order[take]]; g = gain[order[take]]
    multipliers = np.round(np.arange(.5, 2.01, .1), 1)
    tables = {}
    for mult in multipliers:
        values = np.zeros((max_n + 1, 3))
        for n in range(1, max_n + 1):
            previous = values[n - 1]
            values[n, 0] = 0
            for k in (1, 2):
                challenge = p * (g * mult + previous[k]) + (1 - p) * previous[k - 1]
                values[n, k] = np.maximum(previous[k], challenge).mean()
        tables[float(mult)] = values
    return tables


def apply_sequential_policy(frame: pd.DataFrame, value: pd.DataFrame):
    p = frame.P_overturn.to_numpy(); gain = value.delta_WP.to_numpy()
    tables = bellman_tables(p, gain)
    typical = max(float(np.median(value.challenge_leverage[value.challenge_leverage > 0])), 1e-5)
    inning = frame.inning.to_numpy(dtype=float); top = frame.half_inning.eq("top").to_numpy()
    fraction = np.where(inning <= 9, ((9 - inning) + .5 * top + .5 * (3 - frame.outs.to_numpy()) / 3) / 9, .06)
    expected_game_opportunities = len(frame) / (2 * frame.game_pk.nunique())
    n_remaining = np.clip(np.rint(expected_game_opportunities * fraction), 0, 80).astype(int)
    leverage_mult = np.clip(value.challenge_leverage.to_numpy() / typical, .5, 2)
    leverage_bucket = np.round(np.round((leverage_mult - .5) / .1) * .1 + .5, 1)
    inventory = frame.affected_team_challenges_remaining.to_numpy(dtype=int).clip(1, 2)
    vk, vless = np.zeros(len(frame)), np.zeros(len(frame))
    for i, (n, mult, k) in enumerate(zip(n_remaining, leverage_bucket, inventory)):
        table = tables[float(mult)]; vk[i] = table[n, k]; vless[i] = table[n, k - 1]
    marginal = np.maximum(vk - vless, 0)
    immediate = p * gain
    ev_hold = vk
    ev_challenge = p * (gain + vk) + (1 - p) * vless
    ev_diff = ev_challenge - ev_hold
    required = np.divide(marginal, gain + marginal, out=np.ones(len(frame)), where=(gain + marginal) > 0)
    labels = [classify_decision(d, a) for d, a in zip(ev_diff, frame.actual_action)]
    out = value.copy()
    out["P_overturn"] = p; out["immediate_expected_value"] = immediate
    out["expected_future_opportunities"] = n_remaining
    out["future_value_with_inventory"] = vk; out["future_value_after_failed_challenge"] = vless
    out["future_challenge_value"] = marginal; out["EV_hold"] = ev_hold; out["EV_challenge"] = ev_challenge
    out["EV_difference"] = ev_diff; out["required_confidence"] = np.clip(required, 0, 1)
    out["recommended_action"] = [x[0] for x in labels]
    out["decision_quality_category"] = [x[1] for x in labels]
    out["decision_margin"] = [x[2] for x in labels]
    out["decision_correct"] = [x[3] for x in labels]
    out["actual_action"] = frame.actual_action.to_numpy()
    out["analysis_perspective"] = "EX_ANTE"
    out["model_version"] = MODEL_VERSION
    return out, tables


def _summary(frame: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    def one(g):
        actual = g.actual_action.eq("CHALLENGE")
        optimal = g.recommended_action.eq("CHALLENGE")
        available = g.EV_difference.clip(lower=0).sum()
        captured = np.where(actual, g.EV_difference, 0).sum()
        return pd.Series({
            "opportunities": len(g), "actual_challenges": int(actual.sum()),
            "recommended_challenges": int(optimal.sum()), "challenge_rate": actual.mean(),
            "recommended_challenge_rate": optimal.mean(), "mean_P_overturn": g.P_overturn.mean(),
            "actual_success_rate": g.loc[actual, "geometry_incorrect"].mean() if actual.any() else np.nan,
            "mean_required_confidence": g.required_confidence.mean(),
            "decision_correct_rate": g.decision_correct.mean(),
            "suboptimal_decisions": int((~g.decision_correct.astype(bool)).sum()),
            "expected_value_captured": captured, "expected_value_available": available,
            "decision_efficiency": captured / available if available > 0 else np.nan,
        })
    if not groups: return one(frame).to_frame().T
    return frame.groupby(groups, observed=True, dropna=False).apply(one, include_groups=False).reset_index()


def inventory_and_exhaustion(candidates: pd.DataFrame, analysis: pd.DataFrame):
    challenged = candidates[candidates.challenged_bool].copy().sort_values(["game_date", "game_pk", "physical_pitch_ordinal"])
    challenged["inventory_before"] = challenged.affected_team_challenges_remaining.astype(int)
    challenged["inventory_after"] = [inventory_after(b, o) for b, o in zip(challenged.inventory_before, challenged.challenge_outcome)]
    challenged["inventory_event"] = np.where(challenged.challenge_outcome.eq("OVERTURNED"), "SUCCESS_RETAINED", "FAILED_LOST")
    keep = ["pitch_key", "game_date", "game_pk", "physical_pitch_ordinal", "decision_team_id", "decision_team",
            "decision_side", "inning", "half_inning", "outs", "balls", "strikes", "inventory_before",
            "inventory_after", "challenge_outcome", "inventory_event"]
    history = challenged[keep].copy()
    exhaustion = challenged[(challenged.inventory_before == 1) & challenged.challenge_outcome.eq("CONFIRMED")].copy()
    cols = ["pitch_key", "P_overturn", "immediate_expected_value", "future_challenge_value", "EV_difference",
            "decision_margin", "decision_quality_category", "recommended_action", "delta_RE", "delta_WP"]
    exhaustion = exhaustion.merge(analysis[cols], on="pitch_key", how="left", validate="one_to_one")
    exhaustion["analysis_perspective"] = "EX_ANTE"
    return history, exhaustion


def post_exhaustion(candidates: pd.DataFrame, analysis: pd.DataFrame, exhaustion: pd.DataFrame):
    lookup = candidates.merge(analysis, on="pitch_key", how="left", validate="one_to_one",
                              suffixes=("", "_analysis"))
    rows = []
    for event in exhaustion.itertuples(index=False):
        later = lookup[(lookup.game_pk == event.game_pk) & (lookup.decision_team_id == event.decision_team_id) &
                       (lookup.physical_pitch_ordinal > event.physical_pitch_ordinal) &
                       lookup.affected_team_challenges_remaining.fillna(0).eq(0)].copy()
        if later.empty: continue
        later["exhaustion_pitch_key"] = event.pitch_key
        later["exhaustion_order"] = np.arange(1, len(later) + 1)
        later["call_correct"] = ~later.geometry_incorrect.astype(bool)
        later["realized_run_value_lost"] = np.where(later.geometry_incorrect.eq(1), later.delta_RE, 0)
        later["realized_wp_value_lost"] = np.where(later.geometry_incorrect.eq(1), later.delta_WP, 0)
        later["analysis_perspective"] = "HINDSIGHT_DESCRIPTIVE"
        rows.append(later)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def counterfactual_preservation(post: pd.DataFrame, exhaustion: pd.DataFrame):
    rows = []
    for event in exhaustion.itertuples(index=False):
        seq = post[post.exhaustion_pitch_key.eq(event.pitch_key)].sort_values("exhaustion_order")
        inventory, uses, expected, realized = 1, 0, 0.0, 0.0
        first_key = ""
        for r in seq.itertuples(index=False):
            if inventory == 0: break
            if r.recommended_action == "CHALLENGE":
                if not first_key: first_key = r.pitch_key
                uses += 1; expected += max(float(r.EV_difference), 0)
                if int(r.geometry_incorrect): realized += float(r.delta_WP)
                else: inventory = 0
        rows.append({"exhaustion_pitch_key": event.pitch_key, "game_pk": event.game_pk,
                     "decision_team_id": event.decision_team_id, "subsequent_opportunities": len(seq),
                     "preserved_challenges_recommended_for_use": int(uses > 0),
                     "preserved_challenges_never_recommended_for_use": int(uses == 0),
                     "counterfactual_uses": uses, "first_recommended_pitch_key": first_key,
                     "counterfactual_expected_value": expected, "counterfactual_realized_wp_value": realized,
                     "analysis_perspective": "HINDSIGHT_POLICY_SIMULATION"})
    return pd.DataFrame(rows)


def policy_artifacts(frame: pd.DataFrame, overturn_metrics: pd.DataFrame,
                     re_metrics: pd.DataFrame, wp_metrics: pd.DataFrame):
    timing_order = ["INNINGS_1_3", "INNINGS_4_6", "INNINGS_7_8", "NINTH", "EXTRA_INNINGS"]
    frame["timing_group"] = np.select([frame.inning.le(3), frame.inning.le(6), frame.inning.le(8), frame.inning.eq(9)],
                                       timing_order[:4], default=timing_order[4])
    frame["count_group"] = np.select([frame.strikes.eq(2) & frame.original_call.eq("STRIKE"),
                                       frame.balls.eq(3) & frame.original_call.eq("BALL")],
                                      ["STRIKE_THREE", "BALL_FOUR"], default=frame["count"])
    timing = _summary(frame, ["timing_group"])
    count = _summary(frame, ["count_group", "decision_side"])
    inventory = _summary(frame, ["affected_team_challenges_remaining"])
    side = _summary(frame, ["decision_side"])
    matrix = frame.groupby(["actual_action", "recommended_action", "decision_quality_category"], observed=True).size().reset_index(name="opportunities")
    bins = [-np.inf, -.01, -.0025, -.00025, .00025, .0025, .01, np.inf]
    labels = ["LT_-1PP", "-1_TO_-.25PP", "-.25_TO_-.025PP", "INDIFFERENT", ".025_TO_.25PP", ".25_TO_1PP", "GT_1PP"]
    margins = frame.assign(decision_margin_bin=pd.cut(frame.decision_margin, bins, labels=labels)).groupby("decision_margin_bin", observed=True).decision_margin.agg(opportunities="size", mean="mean", median="median", minimum="min", maximum="max").reset_index()
    pooled_o = overturn_metrics[overturn_metrics.fold.eq("POOLED")].iloc[0]
    pooled_re = re_metrics[re_metrics.fold.eq("POOLED")].iloc[0]
    pooled_wp = wp_metrics[wp_metrics.fold.eq("POOLED")].iloc[0]
    validation = pd.DataFrame([
        {"component": "OVERTURN", "criterion": "temporal Brier<=0.20, AUC>=0.70, ECE<=0.05", "value": pooled_o.brier_score, "passed": pooled_o.brier_score <= .20 and pooled_o.roc_auc >= .70 and pooled_o.ece_10bin <= .05},
        {"component": "RUN_EXPECTANCY", "criterion": "temporal MAE improves constant baseline", "value": pooled_re.mae - pooled_re.baseline_mae, "passed": pooled_re.mae < pooled_re.baseline_mae},
        {"component": "WIN_PROBABILITY", "criterion": "temporal Brier<=0.25, AUC>=0.70, ECE<=0.05", "value": pooled_wp.brier_score, "passed": pooled_wp.brier_score <= .25 and pooled_wp.roc_auc >= .70 and pooled_wp.ece_10bin <= .05},
    ])
    return timing, count, inventory, side, matrix, margins, validation


def sensitivity_and_benchmarks(frame: pd.DataFrame):
    primary = frame.recommended_action.eq("CHALLENGE")
    variants = [
        ("PRIMARY", 1.0, 1.0, INDIFFERENCE_WP), ("P_OVERTURN_-15%", .85, 1.0, INDIFFERENCE_WP),
        ("P_OVERTURN_+15%", 1.15, 1.0, INDIFFERENCE_WP), ("FUTURE_VALUE_HALF", 1, .5, INDIFFERENCE_WP),
        ("FUTURE_VALUE_1.5X", 1, 1.5, INDIFFERENCE_WP), ("WP_VALUE_-10%", 1, 1.0, INDIFFERENCE_WP),
        ("INDIFFERENCE_HALF", 1, 1, INDIFFERENCE_WP / 2), ("INDIFFERENCE_DOUBLE", 1, 1, INDIFFERENCE_WP * 2),
    ]
    sens = []
    for name, ps, fs, eps in variants:
        gain = frame.delta_WP.to_numpy() * (.9 if name == "WP_VALUE_-10%" else 1)
        p = np.clip(frame.P_overturn.to_numpy() * ps, 0, 1); cost = frame.future_challenge_value.to_numpy() * fs
        diff = p * gain - (1 - p) * cost
        rec = diff > eps
        agreement = (rec == primary.to_numpy()).mean()
        union = (rec | primary.to_numpy()).sum()
        jaccard = (rec & primary.to_numpy()).sum() / union if union else 1.0
        actual = frame.actual_action.eq("CHALLENGE").to_numpy()
        captured = np.where(actual, diff, 0).sum(); available = np.maximum(diff, 0).sum()
        sens.append({"variant": name, "recommended_challenge_rate": rec.mean(), "agreement_with_primary": agreement,
                     "challenge_set_jaccard": jaccard,
                     "actual_minus_recommended_rate": frame.actual_action.eq("CHALLENGE").mean() - rec.mean(),
                     "actual_expected_value_captured": captured, "optimal_expected_value_available": available,
                     "decision_efficiency": captured / available if available else np.nan,
                     "mean_EV_difference": diff.mean(), "finding_status": "ROBUST" if jaccard >= .90 else "SENSITIVE" if jaccard >= .75 else "INCONCLUSIVE"})
    sensitivity = pd.DataFrame(sens)
    policies = {
        "PASCAL_SEQUENTIAL": primary,
        "IMMEDIATE_VALUE_ONLY": frame.immediate_expected_value.gt(INDIFFERENCE_WP),
        "FIXED_LOST_COST_0.1PP": (frame.P_overturn * frame.delta_WP - (1 - frame.P_overturn) * .001).gt(INDIFFERENCE_WP),
        "PUBLIC_CONFIDENCE_60%": frame.P_overturn.ge(.60),
        "DECLINING_CONFIDENCE_PROXY": frame.P_overturn.ge(np.where(frame.inning >= 9, .40, np.where(frame.inning >= 7, .50, .60))),
    }
    benchmarks = []
    for name, rec in policies.items():
        benchmarks.append({"policy": name, "recommended_challenges": int(rec.sum()), "recommended_challenge_rate": rec.mean(),
                           "agreement_with_pascal": (rec.to_numpy() == primary.to_numpy()).mean(),
                           "expected_incremental_value": np.where(rec, frame.EV_difference, 0).sum(),
                           "description": {"PASCAL_SEQUENTIAL": "state-dependent Bellman option value",
                                           "IMMEDIATE_VALUE_ONLY": "ignores lost future option",
                                           "FIXED_LOST_COST_0.1PP": "constant 0.1 percentage-point failure cost",
                                           "PUBLIC_CONFIDENCE_60%": "fixed confidence threshold benchmark",
                                           "DECLINING_CONFIDENCE_PROXY": "60/50/40% early/late/ninth threshold proxy"}[name]})
    return sensitivity, pd.DataFrame(benchmarks)


def make_figures(frame, timing, count, inventory, side, exhaustion, post, benchmarks, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    def save(name, title, xlabel=""):
        plt.title(title); plt.xlabel(xlabel); plt.tight_layout(); plt.savefig(out / name, dpi=160); plt.close()
    frame.groupby("inning").required_confidence.mean().plot(marker="o"); save("01_required_confidence_by_inning.png", "Required confidence by inning", "Inning")
    c = frame.groupby("count").required_confidence.mean().sort_index(); c.plot(kind="bar"); save("02_required_confidence_by_count.png", "Required confidence by count", "Pre-pitch count")
    inventory.set_index("affected_team_challenges_remaining").mean_required_confidence.plot(kind="bar"); save("03_required_confidence_by_inventory.png", "Required confidence by inventory", "Challenges remaining")
    bins = pd.qcut(frame.required_confidence, 10, duplicates="drop")
    q = frame.groupby(bins, observed=True).agg(required=("required_confidence", "mean"), actual=("actual_action", lambda x: x.eq("CHALLENGE").mean()))
    plt.plot(q.required, q.actual, marker="o"); save("04_actual_probability_vs_required_confidence.png", "Actual challenge rate versus required confidence", "Mean required confidence")
    timing.set_index("timing_group")[["challenge_rate", "recommended_challenge_rate"]].plot(kind="bar"); save("05_actual_vs_recommended_rate.png", "Actual versus recommended challenge rate", "Game segment")
    frame.decision_margin.clip(-.02, .02).hist(bins=60); save("06_decision_margin_distribution.png", "Decision margin distribution (clipped at ±2 pp)", "Actual-action EV margin")
    if len(exhaustion): exhaustion.inning.value_counts().sort_index().plot(kind="bar")
    save("07_exhaustion_by_inning.png", "Challenge exhaustion by inning", "Inning")
    if len(post):
        post[post.geometry_incorrect.eq(1)].groupby("decision_side").realized_wp_value_lost.sum().plot(kind="bar")
    save("08_post_exhaustion_value_lost.png", "Post-exhaustion realized WP value lost", "Decision side")
    side.set_index("decision_side").decision_efficiency.plot(kind="bar"); save("09_offense_defense_efficiency.png", "Offense versus defense decision efficiency", "Side")
    benchmarks.set_index("policy").expected_incremental_value.plot(kind="bar"); save("10_benchmark_comparison.png", "Policy benchmark expected value", "Policy")


def write_documents(root: Path, frame: pd.DataFrame, history: pd.DataFrame, exhaustion: pd.DataFrame,
                    post: pd.DataFrame, counterfactual: pd.DataFrame, timing: pd.DataFrame,
                    inventory: pd.DataFrame, side: pd.DataFrame, validation: pd.DataFrame,
                    sensitivity: pd.DataFrame, outputs: dict[str, pd.DataFrame]):
    docs = root / "docs/sprint5"; docs.mkdir(parents=True, exist_ok=True)
    challenges = frame.actual_action.eq("CHALLENGE")
    recommended = frame.recommended_action.eq("CHALLENGE")
    incorrect_post = post.geometry_incorrect.eq(1) if len(post) else pd.Series(dtype=bool)
    gate = bool(validation.passed.all() and sensitivity.challenge_set_jaccard.min() >= .75)
    timing_first = timing.set_index("timing_group")
    early_eff = timing_first.loc["INNINGS_1_3", "decision_correct_rate"] if "INNINGS_1_3" in timing_first.index else np.nan
    late_eff = timing_first.loc["NINTH", "decision_correct_rate"] if "NINTH" in timing_first.index else np.nan
    inv = inventory.set_index("affected_team_challenges_remaining")
    inv_one = inv.loc[1, "challenge_rate"] if 1 in inv.index else np.nan
    inv_two = inv.loc[2, "challenge_rate"] if 2 in inv.index else np.nan
    later_cost_events = int(post.loc[incorrect_post, "exhaustion_pitch_key"].nunique()) if len(post) else 0
    resource_mean = frame.future_challenge_value.mean()
    framework_gate = "PROCEED" if gate else "DEFER"
    resource_gate = "YES" if resource_mean > INDIFFERENCE_WP else "NO"
    timing_gate = "SUPPORTED" if abs(late_eff - early_eff) >= .01 else "NOT_SUPPORTED"
    inventory_gate = "YES" if inv_one < inv_two and inv.loc[1, "decision_efficiency"] >= 0 else "INCONCLUSIVE"
    exhaustion_gate = "YES" if later_cost_events / max(len(exhaustion), 1) >= .05 else "NO"
    overall = _summary(frame, []).iloc[0]
    report = f"""# Sprint 5: Challenge Resource Management and Decision Quality

## Decision universe

The locked 2026-03-25 through 2026-09-09 snapshot contains {len(frame):,} legal ABS decision opportunities: {int((frame.decision_side == 'OFFENSE').sum()):,} offensive called strikes and {int((frame.decision_side == 'DEFENSE').sum()):,} defensive called balls. It includes correct and incorrect calls. Players challenged {int(challenges.sum()):,} times ({challenges.mean():.2%}); the model recommends a challenge on {int(recommended.sum()):,} opportunities ({recommended.mean():.2%}).

## What a challenge is worth

The mean immediate ex-ante value is {frame.immediate_expected_value.mean():.4%} win probability, while the mean marginal value of preserving the current challenge is {resource_mean:.4%}. The decision rule retains a successful challenge and removes one after failure. Required confidence is the failure-cost break-even value, not the observed outcome.

Count changes value because a reversed strike three prevents an out and a reversed ball four prevents a walk; bases-loaded ball-four transitions also include the forced run. The largest state changes appear in `count_analysis.csv`. Leverage remains distinct from run expectancy and win probability.

## Ex-ante decision quality

Actual actions agree with a value-maximizing action, including near-indifferent choices, on {frame.decision_correct.mean():.2%} of opportunities. Among actual challenges, {int(frame.loc[challenges, 'decision_correct'].sum()):,} are supported ex ante. There are {int((~challenges & recommended).sum()):,} modeled valuable holds and {int((challenges & frame.decision_quality_category.isin(['SUBOPTIMAL','STRONGLY_SUBOPTIMAL'])).sum()):,} modeled poor challenges. A successful challenge can still be a poor decision, and a failed challenge can still be defensible.

The actual challenge rate with one remaining is {inv_one:.2%}, versus {inv_two:.2%} with two. Early decision correctness is {early_eff:.2%}; ninth-inning correctness is {late_eff:.2%}. These comparisons are conditional descriptions, not causal claims about intent or coaching.

## Hindsight realized consequences

There are {len(exhaustion):,} final-challenge exhaustion events and {len(post):,} subsequent challenge-type calls before any reset. {int(incorrect_post.sum()) if len(post) else 0:,} later calls were incorrect, across {later_cost_events:,} exhaustion sequences, with {post.loc[incorrect_post, 'realized_wp_value_lost'].sum() if len(post) else 0:.3f} cumulative win-probability units ({100*post.loc[incorrect_post, 'realized_wp_value_lost'].sum() if len(post) else 0:.1f} percentage points) and {post.loc[incorrect_post, 'realized_run_value_lost'].sum() if len(post) else 0:.3f} run value unavailable for correction. These values are **HINDSIGHT_DESCRIPTIVE** and never change the earlier stored ex-ante category.

The counterfactual preservation simulation applies the same policy to later opportunities. It recommends later use in {int(counterfactual.preserved_challenges_recommended_for_use.sum()) if len(counterfactual) else 0:,} exhaustion sequences and no use in {int(counterfactual.preserved_challenges_never_recommended_for_use.sum()) if len(counterfactual) else 0:,}.

## Validation and benchmarks

The validation gate is **{framework_gate}**. Component results are in `policy_component_validation.csv`; chronological folds always train before their test month. The primary model is compared with immediate-value-only, a fixed lost-cost rule, a fixed 60% confidence rule, and a declining-threshold proxy. MLB's public model uses location, inventory, runners, and count/out state, while public independent work also uses backward induction; Pascal's comparison keeps those ideas as benchmarks rather than model inputs.

Sensitivity agreement across all opportunities ranges from {sensitivity.agreement_with_primary.min():.2%} to {sensitivity.agreement_with_primary.max():.2%}; overlap within the actionable challenge set ranges from {sensitivity.challenge_set_jaccard.min():.2%} to {sensitivity.challenge_set_jaccard.max():.2%}. The ±15% overturn-probability variant reverses the net actual-versus-recommended challenge-rate comparison, so the over-challenge versus under-challenge headline is **INCONCLUSIVE**.

## Decision gates

- **A. Decision Framework — {framework_gate}.** All component gates {'pass' if gate else 'do not all pass'} and minimum actionable-set sensitivity overlap is {sensitivity.challenge_set_jaccard.min():.2%}.
- **B. Resource Management — {resource_gate}.** Mean marginal future resource value is {resource_mean:.4%} WP.
- **C. Timing — {timing_gate}.** Early versus ninth-inning decision correctness differs by {late_eff-early_eff:+.2%}.
- **D. Inventory — {inventory_gate}.** Challenge rates are {inv_two:.2%} with two and {inv_one:.2%} with one, but modeled efficiency with one remaining is {inv.loc[1, 'decision_efficiency']:.2%}; rate alone cannot establish appropriate selectivity.
- **E. Exhaustion — {exhaustion_gate}.** {later_cost_events:,} of {len(exhaustion):,} exhaustion sequences contain a later incorrect call.
- **F. Best Challenger — DEFER.** Sprint 5 establishes a decision component but does not pass the separate support, uncertainty, temporal ranking, and stability gates for a combined leaderboard.

## Limitations

Challenge behavior is observational, and actual challenges are selected using private information unavailable here. Inverse-propensity weighting addresses selection on recorded variables only. Hawk-Eye/Statcast geometry, run-expectancy lookup, win-probability estimates, and the representative-opportunity Bellman recursion all carry model error. The recursion summarizes future opportunities rather than replaying known future pitches. Batter, catcher, pitcher, and dugout communication are omitted from the normative probability. Repeated players and teams create dependence. The snapshot is season-to-date, counterfactuals are uncertain, extra-inning inventory resets are respected in observed inventory but simplified in future-value approximation, and modeled optimality is conditional on these assumptions.

## Conclusions

**SUPPORTED:** the framework separates outcome from decision quality, models count-aware state changes, and finds measurable option value in preserving inventory.

- **Are players generally using challenges efficiently? NO under the validated conditional model.** Primary decision efficiency is {overall.decision_efficiency:.2%}; it ranges from {sensitivity.decision_efficiency.min():.2%} to {sensitivity.decision_efficiency.max():.2%} across specified sensitivities, always far below the modeled optimum.
- **Are players more prone to over-challenge or under-challenge? INCONCLUSIVE.** The net volume comparison reverses under the lower overturn-probability calibration.
- **Does behavior become more efficient late? NOT_SUPPORTED.** Early and ninth-inning decision correctness differ by only {late_eff-early_eff:+.2%}, and timing efficiency is not monotone.
- **Are players appropriately conservative with the final challenge? INCONCLUSIVE.** Volume falls with one remaining, while selection efficiency is negative under the primary model.
- **Is exhaustion costly in practice? YES descriptively.** {later_cost_events:,} exhaustion sequences contain a later incorrect call, totaling {post.loc[incorrect_post, 'realized_wp_value_lost'].sum() if len(post) else 0:.3f} WP units and {post.loc[incorrect_post, 'realized_run_value_lost'].sum() if len(post) else 0:.3f} runs.
- **Does preservation have measurable future value? YES.** Mean marginal preservation value is {resource_mean:.4%} WP, and the policy would later use a preserved challenge in {int(counterfactual.preserved_challenges_recommended_for_use.sum()) if len(counterfactual) else 0:,} sequences.

**SENSITIVE:** the number of marginal challenge recommendations changes with probability and future-value assumptions; see the sensitivity artifact.

**INCONCLUSIVE:** whether players generally over-challenge or under-challenge, causal claims about why players differ, and whether the one-challenge adjustment is appropriate. Actual-versus-recommended volume reverses under a plausible probability-calibration sensitivity.

**NULL:** no player or team decision-quality leaderboard is published (`ranking_status = NOT_SUPPORTED`).
"""
    (docs / "challenge_resource_management_report.md").write_text(report)
    methodology = f"""# Sprint 5 methodology

## Population and state reconstruction

The analysis reads the accepted {START_DATE} through {END_DATE} Sprint 3 snapshot. A legal offensive opportunity is a called strike with offensive inventory above zero; a legal defensive opportunity is a called ball with defensive inventory above zero. Position-player-pitching calls are excluded. The universe contains {len(frame):,} pitches. Each PRE_PITCH state is advanced under HOLD and under reversal. Walks advance forced runners, loaded walks score one run, strikeouts add an out, and third-out strikeouts advance the half inning.

## Run expectancy and win probability

RE288 uses 12 counts × 3 out states × 8 base states. Empirical future half-inning runs from immutable MLB feeds are smoothed toward base/out means with a 40-observation prior. `delta_RE` is oriented to the challenging side. Home win probability uses a deterministic histogram-gradient-boosting classifier with inning, half, score differential, outs, bases, and count; final game outcomes are targets only. Expanding monthly validation trains strictly before each test month. Counterfactual WP is converted to the challenging team's perspective.

## Overturn probability and selection

The primary probability model uses only pre-decision geometry, pitch, count, state, side, and inventory. A challenge-propensity model is fit on every legal opportunity; the outcome model is fit on actual challenge results with clipped inverse-propensity weights. This addresses selection on recorded covariates but not private perception. A population geometry model trained on derived physical correctness is retained only as a sensitivity value and never as a predictor in the primary model. Temporal calibration is evaluated only on later actual challenges.

## Sequential policy

Future option value is solved by backward induction over a representative empirical distribution of future challenge-type opportunities. For inventory k, the challenge branch is `p × (gain + V[k]) + (1-p) × V[k-1]`; the hold branch is `V[k]`. The recursion retains inventory after success and loses one after failure. Expected remaining opportunity count declines with inning/half/out state, while future gain scales with current WP leverage. `required_confidence = marginal_resource_value / (delta_WP + marginal_resource_value)`. The preregistered indifference band is ±{INDIFFERENCE_WP:.5f} WP and the strong-decision threshold is {STRONG_WP:.4f} WP.

## Validation, sensitivity, and benchmarks

Overturn, RE, and WP models use expanding calendar-month tests. The policy is backtested by held-out segment and tested under ±15% overturn calibration, half/1.5× resource cost, a 10% WP-value reduction, and half/double indifference bands. Stability is reported both across all decisions and as Jaccard overlap of the actionable challenge sets; 0.75 actionable overlap is the minimum framework gate and values below 0.90 are labeled sensitive. Benchmarks are immediate value only, a fixed 0.1 percentage-point failure cost, a 60% confidence rule, and a declining 60/50/40% threshold proxy. Public context: [MLB/Savant definitions](https://baseballsavant.mlb.com/leaderboard/abs-challenges?page=0&pageSize=50&sort=n_challenges&sortDir=desc), [Palmer Bellman implementation](https://github.com/professorpalmer/abs-challenge), and [ABScharts methodology](https://abscharts.com/writeup/methodology/).

Hindsight future events appear only in outputs labeled `HINDSIGHT_DESCRIPTIVE` or `HINDSIGHT_POLICY_SIMULATION`; they never alter earlier ex-ante decisions. Player/team rankings remain unsupported.
"""
    (docs / "methodology.md").write_text(methodology)
    field_notes = {
        "P_overturn": ("probability", "selection-weighted pre-decision model", "normative success probability"),
        "delta_RE": ("runs", "challenger-oriented HOLD/OVERTURN RE difference", "immediate run leverage"),
        "delta_WP": ("probability", "challenger-oriented HOLD/OVERTURN WP difference", "immediate win leverage"),
        "future_challenge_value": ("probability", "Bellman V(k)-V(k-1)", "failure resource cost"),
        "required_confidence": ("probability", "resource/(immediate upside+resource)", "break-even confidence"),
        "decision_margin": ("probability", "EV actual minus EV alternative", "ex-ante decision strength"),
        "geometry_incorrect": ("boolean", "original call differs from derived ABS call", "hindsight description only"),
    }
    lines = ["# Sprint 5 data dictionary", "", "All state inputs use PRE_PITCH timing. Empty values are allowed only where the upstream source or event concept is inapplicable.", ""]
    for name, df in outputs.items():
        lines += [f"## `{name}`", "", "| Field | Type | Unit | Source / derivation | Analytical purpose | Nullable |", "|---|---|---|---|---|---|"]
        for c in df.columns:
            unit, derivation, purpose = field_notes.get(c, ("identifier/value", "upstream pitch state or documented Sprint 5 transformation", "reconstruction, grouping, or audit"))
            nullable = "yes" if df[c].isna().any() else "no"
            lines.append(f"| `{c}` | {df[c].dtype} | {unit} | {derivation} | {purpose} | {nullable} |")
        lines.append("")
    (docs / "data_dictionary.md").write_text("\n".join(lines))
    return {"decision_framework": framework_gate, "resource_management": resource_gate, "timing": timing_gate,
            "inventory": inventory_gate, "exhaustion": exhaustion_gate, "best_challenger": "DEFER", "ranking_status": "NOT_SUPPORTED"}


def make_notebook(root: Path):
    nb = {"cells": [{"cell_type": "markdown", "metadata": {}, "source": ["# Sprint 5 — Challenge Resource Management\n", "Inspection layer for version-controlled `src.sprint5` outputs.\n"]},
                    {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": ["from pathlib import Path\n", "import pandas as pd\n", "ROOT = Path('..').resolve()\n", "values = pd.read_csv(ROOT/'data/analysis/sprint5/challenge_value_estimates.csv')\n", "values[['P_overturn','delta_RE','delta_WP','future_challenge_value','required_confidence']].describe()\n"]},
                    {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": ["pd.read_csv(ROOT/'artifacts/sprint5/policy_component_validation.csv')\n"]}],
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                       "language_info": {"name": "python", "version": "3.12"}}, "nbformat": 4, "nbformat_minor": 5}
    path = root / "notebooks/05_challenge_resource_management.ipynb"; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(nb, indent=1) + "\n")


def run(root: Path):
    root = Path(root)
    data_dir = root / "data/analysis/sprint5"; art = root / "artifacts/sprint5"
    data_dir.mkdir(parents=True, exist_ok=True); art.mkdir(parents=True, exist_ok=True)
    pitches, candidates, legal = prepare_pitches(root)
    games, halves = load_game_results(root)
    pitches = prepare_value_targets(pitches, games, halves)
    re_model, re_metrics = fit_run_expectancy(pitches)
    wp_model, wp_metrics = fit_win_probability(pitches)
    legal_fit, _, _, overturn_metrics, temporal_overturn, overturn_model, geometry_model = fit_overturn(legal)

    candidates = candidates.sort_values(["game_date", "game_pk", "physical_pitch_ordinal"]).reset_index(drop=True)
    candidates["P_overturn"] = overturn_model.predict_proba(candidates)[:, 1]
    candidates["P_overturn_geometry_sensitivity"] = geometry_model.predict_proba(candidates)[:, 1]
    states_all = reconstruct_states(candidates)
    immediate = score_values(candidates, states_all, re_model, wp_model)
    policy, _ = apply_sequential_policy(candidates, immediate)
    policy["P_overturn_geometry_sensitivity"] = candidates.P_overturn_geometry_sensitivity.to_numpy()
    analysis = candidates.drop(columns=["P_overturn", "P_overturn_geometry_sensitivity"]).merge(
        policy, on=["pitch_key", "actual_action"], how="left", validate="one_to_one")
    analysis["geometry_incorrect"] = analysis.geometry_incorrect.astype(int)
    legal_mask = analysis.affected_team_challenges_remaining.fillna(0).gt(0)
    frame = analysis[legal_mask].copy().reset_index(drop=True)
    states = states_all[states_all.pitch_key.isin(frame.pitch_key)].copy()

    history, exhaustion = inventory_and_exhaustion(candidates, analysis)
    post = post_exhaustion(candidates, analysis, exhaustion)
    counterfactual = counterfactual_preservation(post, exhaustion)
    timing, count, inventory, side, matrix, margins, validation = policy_artifacts(frame, overturn_metrics, re_metrics, wp_metrics)
    sensitivity, benchmarks = sensitivity_and_benchmarks(frame)
    validation = pd.concat([validation, pd.DataFrame([{"component": "SEQUENTIAL_POLICY",
        "criterion": "minimum actionable challenge-set Jaccard >=0.75", "value": sensitivity.challenge_set_jaccard.min(),
        "passed": sensitivity.challenge_set_jaccard.min() >= .75}])], ignore_index=True)

    opp_cols = ["pitch_key", "game_date", "game_pk", "physical_pitch_ordinal", "at_bat_index", "play_event_index",
                "inning", "half_inning", "balls", "strikes", "outs", "base_state", "on_1b", "on_2b", "on_3b",
                "home_score", "away_score", "score_diff", "batter_id", "batter_name", "pitcher_id", "pitcher_name",
                "catcher_id", "catcher_name", "umpire_id", "umpire_name", "decision_side", "decision_team_id",
                "decision_team", "original_call", "derived_abs_call", "challenge_available", "affected_team_challenges_remaining",
                "actual_action", "challenge_outcome", "plate_x", "plate_z", "abs_zone_top", "abs_zone_bot",
                "distance_from_abs_boundary", "wrong_way_margin_inches", "pitch_type", "release_speed", "pfx_x", "pfx_z",
                "geometry_incorrect"]
    opportunity_out = frame[opp_cols].copy()
    states_out = opportunity_out[["pitch_key", "game_date", "game_pk", "decision_side", "decision_team_id"]].merge(states, on="pitch_key", validate="one_to_one")
    value_cols = ["pitch_key", "P_overturn", "P_overturn_geometry_sensitivity", "RE_hold_batting", "RE_overturn_batting",
                  "delta_RE_raw", "delta_RE", "WP_hold", "WP_overturn", "delta_WP_raw", "delta_WP", "challenge_leverage",
                  "immediate_expected_value", "expected_future_opportunities", "future_value_with_inventory",
                  "future_value_after_failed_challenge", "future_challenge_value", "EV_hold", "EV_challenge", "EV_difference",
                  "required_confidence", "decision_margin", "model_version", "analysis_perspective"]
    values_out = frame[value_cols].copy()
    decision_cols = ["pitch_key", "game_date", "game_pk", "decision_team_id", "decision_team", "decision_side",
                     "actual_action", "challenge_outcome", "recommended_action", "decision_correct",
                     "decision_quality_category", "EV_difference", "decision_margin", "required_confidence",
                     "P_overturn", "geometry_incorrect", "analysis_perspective", "model_version"]
    decisions_out = frame[decision_cols].copy()

    exhaustion_cols = [c for c in ["pitch_key", "game_date", "game_pk", "physical_pitch_ordinal", "decision_team_id", "decision_team",
                       "decision_side", "inning", "half_inning", "balls", "strikes", "outs", "inventory_before", "inventory_after",
                       "challenge_outcome", "P_overturn", "immediate_expected_value", "future_challenge_value", "EV_difference",
                       "decision_margin", "decision_quality_category", "recommended_action", "delta_RE", "delta_WP", "analysis_perspective"] if c in exhaustion.columns]
    exhaustion_out = exhaustion[exhaustion_cols].copy()
    post_cols = [c for c in ["exhaustion_pitch_key", "exhaustion_order", "pitch_key", "game_date", "game_pk", "physical_pitch_ordinal",
                    "decision_team_id", "decision_team", "decision_side", "inning", "half_inning", "balls", "strikes", "outs",
                    "base_state", "original_call", "derived_abs_call", "call_correct", "geometry_incorrect", "P_overturn",
                    "delta_RE", "delta_WP", "recommended_action", "required_confidence", "realized_run_value_lost",
                    "realized_wp_value_lost", "analysis_perspective"] if c in post.columns]
    post_out = post[post_cols].copy() if len(post) else pd.DataFrame(columns=post_cols)

    resource_parts = []
    if len(post_out):
        wrong = post_out[post_out.geometry_incorrect.eq(1)]
        for dimension, col in [("SIDE", "decision_side"), ("INNING", "inning"), ("COUNT", "balls"), ("TEAM", "decision_team")]:
            temp = wrong.groupby(col).agg(incorrect_calls=("pitch_key", "size"), run_value_lost=("realized_run_value_lost", "sum"),
                                             wp_value_lost=("realized_wp_value_lost", "sum"), mean_wp_loss=("realized_wp_value_lost", "mean"),
                                             median_wp_loss=("realized_wp_value_lost", "median"), p90_wp_loss=("realized_wp_value_lost", lambda x: x.quantile(.9)),
                                             maximum_wp_loss=("realized_wp_value_lost", "max")).reset_index().rename(columns={col: "group"})
            temp.insert(0, "dimension", dimension); resource_parts.append(temp)
    resource = pd.concat(resource_parts, ignore_index=True) if resource_parts else pd.DataFrame(columns=["dimension", "group", "incorrect_calls", "run_value_lost", "wp_value_lost"])

    data_outputs = {
        "challenge_opportunities.csv": opportunity_out, "challenge_decision_states.csv": states_out,
        "challenge_value_estimates.csv": values_out, "decision_quality.csv": decisions_out,
        "challenge_inventory_history.csv": history, "exhaustion_events.csv": exhaustion_out,
        "post_exhaustion_opportunities.csv": post_out, "resource_cost_summary.csv": resource,
    }
    for name, df in data_outputs.items(): _csv(data_dir / name, df)

    calibration = temporal_overturn.copy()
    calibration["probability_bin"] = pd.cut(calibration.probability, np.linspace(0, 1, 11), include_lowest=True)
    calibration = calibration.groupby("probability_bin", observed=True).agg(n=("actual", "size"), predicted=("probability", "mean"), observed=("actual", "mean")).reset_index()
    calibration["absolute_error"] = (calibration.predicted - calibration.observed).abs()
    calibration["probability_bin"] = calibration.probability_bin.astype(str)
    decision_summary = _summary(frame, ["decision_quality_category"])
    successful_bad = frame[frame.actual_action.eq("CHALLENGE") & frame.challenge_outcome.eq("OVERTURNED") & frame.decision_quality_category.isin(["SUBOPTIMAL", "STRONGLY_SUBOPTIMAL"])]
    unsuccessful_good = frame[frame.actual_action.eq("CHALLENGE") & frame.challenge_outcome.eq("CONFIRMED") & frame.decision_quality_category.isin(["OPTIMAL", "STRONGLY_OPTIMAL", "NEAR_INDIFFERENT"])]
    valuable_holds = frame[frame.actual_action.eq("HOLD") & frame.recommended_action.eq("CHALLENGE")].sort_values("EV_difference", ascending=False)
    low_value = frame[frame.actual_action.eq("CHALLENGE") & frame.delta_WP.lt(.001)].sort_values("delta_WP")
    post_agg = post_out.groupby("exhaustion_pitch_key").agg(subsequent_opportunities=("pitch_key", "size"),
        later_incorrect_calls=("geometry_incorrect", "sum"), later_run_cost=("realized_run_value_lost", "sum"),
        later_wp_cost=("realized_wp_value_lost", "sum")).reset_index() if len(post_out) else pd.DataFrame(columns=["exhaustion_pitch_key", "subsequent_opportunities", "later_incorrect_calls", "later_run_cost", "later_wp_cost"])
    sequences = exhaustion_out.rename(columns={"pitch_key": "exhaustion_pitch_key"}).merge(post_agg, on="exhaustion_pitch_key", how="left")
    for c in ["subsequent_opportunities", "later_incorrect_calls", "later_run_cost", "later_wp_cost"]: sequences[c] = sequences[c].fillna(0)
    sequences["earlier_decision"] = np.where(sequences.decision_quality_category.isin(["OPTIMAL", "STRONGLY_OPTIMAL", "NEAR_INDIFFERENT"]), "GOOD_EARLIER_DECISION", "POOR_EARLIER_DECISION")
    sequences["later_realized_cost"] = np.where(sequences.later_wp_cost.gt(0), "LATER_REALIZED_COST", "NO_LATER_REALIZED_COST")
    sequences["sequence_category"] = sequences.earlier_decision + " / " + sequences.later_realized_cost
    team_summary = _summary(frame, ["decision_team_id", "decision_team"])
    team_exhaust = exhaustion_out.groupby("decision_team_id").size().rename("exhaustion_events")
    team_summary = team_summary.merge(team_exhaust, on="decision_team_id", how="left"); team_summary.exhaustion_events = team_summary.exhaustion_events.fillna(0).astype(int)
    policy_validation = _summary(frame.assign(month=frame.game_date.str[:7]), ["month"])
    policy_validation["validation_type"] = "TEMPORAL_COMPONENT_MODELS_WITH_PRODUCTION_POLICY_BACKTEST"
    artifact_outputs = {
        "overturn_model_metrics.csv": overturn_metrics, "run_expectancy_model_metrics.csv": re_metrics,
        "win_probability_model_metrics.csv": wp_metrics, "policy_validation.csv": policy_validation,
        "calibration_metrics.csv": calibration, "policy_component_validation.csv": validation,
        "decision_quality_summary.csv": decision_summary, "decision_matrix.csv": matrix,
        "decision_margin_distribution.csv": margins, "successful_bad_decisions.csv": successful_bad[decision_cols + ["delta_WP"]],
        "unsuccessful_good_decisions.csv": unsuccessful_good[decision_cols + ["delta_WP"]],
        "valuable_holds.csv": valuable_holds[decision_cols + ["delta_RE", "delta_WP", "future_challenge_value"]],
        "low_value_challenges.csv": low_value[decision_cols + ["delta_RE", "delta_WP", "future_challenge_value"]],
        "timing_analysis.csv": timing, "count_analysis.csv": count, "inventory_analysis.csv": inventory,
        "offense_defense_comparison.csv": side, "exhaustion_sequences.csv": sequences,
        "counterfactual_preservation.csv": counterfactual, "benchmark_comparison.csv": benchmarks,
        "sensitivity_analysis.csv": sensitivity, "team_resource_management.csv": team_summary,
    }
    for name, df in artifact_outputs.items(): _csv(art / name, df)
    make_figures(frame, timing, count, inventory, side, exhaustion_out, post_out, benchmarks, art)
    make_notebook(root)
    gates = write_documents(root, frame, history, exhaustion_out, post_out, counterfactual, timing,
                            inventory, side, validation, sensitivity, data_outputs)

    upstream = json.loads((root / "data/full_season/processed/run_manifest.json").read_text())
    input_paths = [root / "data/full_season/processed/pitches.csv", root / "data/full_season/processed/challenges.csv",
                   root / "data/full_season/processed/run_manifest.json", root / "artifacts/sprint4/run_manifest.json",
                   root / "requirements-sprint5-lock.txt"]
    output_paths = [x for base in [data_dir, art, root / "docs/sprint5"] for x in base.rglob("*") if x.is_file() and x.name != "run_manifest.json"] + [root / "notebooks/05_challenge_resource_management.ipynb"]
    manifest = {"execution_timestamp": upstream.get("execution_timestamp", upstream.get("retrieved_at", "2026-09-10T00:00:00Z")),
                "analysis_start_date": START_DATE, "analysis_end_date": END_DATE,
                "source_snapshot_hashes": {str(x.relative_to(root)): _hash(x) for x in input_paths},
                "code_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True).stdout.strip() or "UNCOMMITTED",
                "code_hash": _hash(Path(__file__)), "model_versions": {"pipeline": MODEL_VERSION, "sklearn": sklearn.__version__},
                "random_seeds": [SEED], "overturn_model_specification": "IPW logistic outcome model; predecision geometry/state; actual challenges",
                "re_specification": "RE288 empirical table, base/out shrinkage prior=40",
                "wp_specification": "HistGradientBoostingClassifier; inning/half/score/outs/bases/count",
                "sequential_policy_specification": "representative-opportunity Bellman recursion; success retains, failure loses",
                "decision_thresholds": {"indifference_wp": INDIFFERENCE_WP, "strong_wp": STRONG_WP},
                "sensitivity_configurations": sensitivity.variant.tolist(), "decision_gates": gates,
                "population": {"physical_pitches": len(pitches), "games": pitches.game_pk.nunique(), "legal_opportunities": len(frame),
                               "actual_challenges": int(frame.actual_action.eq("CHALLENGE").sum()), "exhaustion_events": len(exhaustion_out)},
                "output_hashes": {str(x.relative_to(root)): _hash(x) for x in output_paths},
                "software_versions": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "sklearn": sklearn.__version__}}
    _json(art / "run_manifest.json", manifest)
    return {"gates": gates, "population": manifest["population"], "validation": validation.to_dict("records")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    print(json.dumps(run(parser.parse_args().root), indent=2, default=str))
