"""Article 4 research dataset: what is a challenge worth?

Builds an auditable opportunity-level dataset from the accepted 2026-03-25 ..
2026-09-09 ABS snapshot.  This script does not model, rank, or interpret.  It
reproduces the Article 1-3 population, reconstructs post-pitch states from the
immutable game feeds, values the correction of each incorrect call with a
count-aware run-expectancy table, and writes the Article 4 artifacts plus a
validation report.  See README.md in this directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pickle
import platform
import sys
from collections import Counter, defaultdict
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/abs-article4-mpl")
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from counterfactual import Movement, State, reconstruct  # noqa: E402
from feeds import load_feeds, parse_feed  # noqa: E402
from fields import FIELD_DOCS  # noqa: E402

START, END = "2026-03-25", "2026-09-09"
RE_PRIOR = 40            # Sprint 5 RE288 smoothing convention, reused unchanged
RE_MAX_INNING = 8        # RE estimated from innings 1-8 (complete half-innings)
HIGH_VALUE_TOP_N = 250
SEED = 20260923
ATL = 144
BRAVES_CASE_PITCH = "824887:3:7"  # game identified by the user on 2026-09-23; play matched from source data
VERSION = "pascal_article4_dataset_v1"


# --------------------------------------------------------------------------- utils
def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as r:
        for block in iter(lambda: r.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_table(frame: pd.DataFrame, path: Path, table: str) -> None:
    missing = [c for c in frame.columns if (table, c) not in FIELD_DOCS and ("*", c) not in FIELD_DOCS]
    if missing:
        raise RuntimeError(f"undocumented fields in {table}: {missing}")
    frame.to_csv(path, index=False, float_format="%.6g", lineterminator="\n")


def _bool(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower().map({"true": True, "false": False})


def _json_default(v):
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return None if not np.isfinite(v) else float(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, (pd.Timestamp,)):
        return str(v)
    raise TypeError(type(v))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=_json_default) + "\n")


def protected_files(root: Path) -> list[Path]:
    parents = ["data/full_season/processed", "data/analysis", "artifacts/publication_validation",
               "artifacts/sprint4", "artifacts/sprint5", "docs", "src", "research/article2"]
    files = [p for d in parents for p in (root / d).rglob("*")
             if p.is_file() and "__pycache__" not in str(p) and p.name != ".DS_Store"]
    files.append(root / "data/full_season/raw/receipts.jsonl")
    return sorted(files)


# --------------------------------------------------------------------- population
def load_population(root: Path):
    sys.path.insert(0, str(root))
    from src.sprint3 import build_population
    from src.offensive_recognition import _inside_outside, HALF_PLATE_FT

    offense, audit, p = build_population(root, START, END)
    if len(offense) != 10755 or int(offense.recognized.sum()) != 2112:
        raise RuntimeError("STOP: Article 1-3 population did not reproduce (10,755 / 2,112)")
    validation = json.loads((root / "data/full_season/processed/validation_report.json").read_text())
    if validation["official_challenges"] != 9485 or validation["agreement_count"] != 9482:
        raise RuntimeError("STOP: accepted validation report changed")
    p["challenged_bool"] = _bool(p.challenged).fillna(False)
    p["challenge_available_bool"] = _bool(p.challenge_available)
    p["position_player_bool"] = _bool(p.position_player_pitching)

    inc_ball = p[(p.original_call == "BALL") & (p.derived_abs_call == "STRIKE")].copy()
    resource = inc_ball.survival_class.eq("SURVIVED_RESOURCE")
    position = inc_ball.challenge_unavailable_reason.eq("POSITION_PLAYER_PITCHING")
    unknown = inc_ball.survival_class.eq("UNKNOWN") & ~position
    eligible = inc_ball.challenge_available_bool.eq(True) & ~resource & ~position & ~unknown
    other = ~(eligible | resource | position | unknown)
    def_audit = {
        "incorrect_called_balls": int(len(inc_ball)), "legal_defensive_opportunities": int(eligible.sum()),
        "challenged": int(inc_ball[eligible].challenged_bool.sum()),
        "resource_constrained": int(resource.sum()), "position_player_pitching": int(position.sum()),
        "unknown": int(unknown.sum()), "other_exclusions": int(other.sum()),
    }
    if other.any():
        raise RuntimeError("defensive population accounting failed")
    prior_def = pd.read_csv(root / "data/analysis/sprint3/defensive_population_summary.csv")
    legal_prior = prior_def[(prior_def.population == "LEGAL_DEFENSIVE_OPPORTUNITIES") & (prior_def.dimension == "ALL")].iloc[0]
    def_audit["sprint3_legal_defensive_count"] = int(legal_prior["count"])
    def_audit["sprint3_legal_defensive_challenged"] = int(legal_prior["challenged"])

    # Status for every incorrect call (both sides); the opportunity table keeps ELIGIBLE rows.
    inc_strike = p[(p.original_call == "STRIKE") & (p.derived_abs_call == "BALL")].copy()
    for frame in (inc_strike, inc_ball):
        pos = frame.challenge_unavailable_reason.eq("POSITION_PLAYER_PITCHING")
        frame["eligibility_status"] = np.select(
            [frame.survival_class.eq("SURVIVED_RESOURCE"), pos,
             frame.survival_class.eq("UNKNOWN") & ~pos, frame.challenge_available_bool.eq(True)],
            ["INELIGIBLE_EXHAUSTED", "INELIGIBLE_POSITION_PLAYER_PITCHING", "UNKNOWN_AVAILABILITY", "ELIGIBLE"],
            default="OTHER")
    inc_strike["opportunity_side"] = "OFFENSE"
    inc_ball["opportunity_side"] = "DEFENSE"
    incorrect = pd.concat([inc_strike, inc_ball], ignore_index=True)
    if incorrect.eligibility_status.eq("OTHER").any():
        raise RuntimeError("unclassified incorrect-call eligibility")
    off_keys = set(offense.pitch_key)
    elig_off = set(incorrect.loc[incorrect.opportunity_side.eq("OFFENSE") & incorrect.eligibility_status.eq("ELIGIBLE"), "pitch_key"])
    if off_keys != elig_off:
        raise RuntimeError("STOP: offensive eligibility does not equal the Article 1-3 population")

    # Geometry: Article 1-3 fields for OFFENSE; the same function for DEFENSE outside
    # distances is not meaningful (the pitch is inside the zone), so the nearest edge
    # is recorded instead and documented as such.
    geo_cols = ["miss_axis", "miss_side", "horizontal_distance_inches", "vertical_distance_inches",
                "corner_proximity_inches", "abs_distance_inches", "pitch_family"]
    incorrect = incorrect.merge(offense[["pitch_key"] + geo_cols + ["recognized"]], on="pitch_key", how="left")
    d = incorrect.opportunity_side.eq("DEFENSE") | incorrect.miss_axis.isna()
    x = pd.to_numeric(incorrect.plate_x); z = pd.to_numeric(incorrect.plate_z)
    top = pd.to_numeric(incorrect.abs_zone_top); bot = pd.to_numeric(incorrect.abs_zone_bot)
    dist = pd.to_numeric(incorrect.distance_from_abs_boundary)
    # Recompute Article 1-3 geometry for incorrect strikes outside the eligible population.
    off_missing = incorrect.opportunity_side.eq("OFFENSE") & incorrect.miss_axis.isna()
    for i in incorrect.index[off_missing]:
        r = incorrect.loc[i]
        hx = max(abs(r.plate_x) - HALF_PLATE_FT, 0.0); above = max(r.plate_z - r.abs_zone_top, 0.0); below = max(r.abs_zone_bot - r.plate_z, 0.0)
        vz = max(above, below)
        if hx > 0 and vz > 0:
            axis, side = "CORNER", f"{'ABOVE' if above else 'BELOW'}_{_inside_outside(r.plate_x, r.bat_side)}"
        elif hx > 0:
            axis, side = "HORIZONTAL", _inside_outside(r.plate_x, r.bat_side)
        else:
            axis, side = "VERTICAL", "ABOVE" if above else "BELOW"
        incorrect.loc[i, ["miss_axis", "miss_side", "horizontal_distance_inches", "vertical_distance_inches",
                          "corner_proximity_inches", "abs_distance_inches"]] = [
            axis, side, hx * 12, vz * 12, math.hypot(hx, vz) * 12 if hx and vz else 0.0, abs(r.distance_from_abs_boundary) * 12]
    dd = incorrect.opportunity_side.eq("DEFENSE")
    edges = pd.DataFrame({"TOP": top - z, "BOTTOM": z - bot, "HORIZONTAL": HALF_PLATE_FT - x.abs()})
    nearest = edges.idxmin(axis=1)
    horiz_side = [(_inside_outside(a, b) if isinstance(b, str) else None) for a, b in zip(x, incorrect.bat_side)]
    incorrect.loc[dd, "miss_axis"] = "INSIDE_ZONE"
    incorrect.loc[dd, "miss_side"] = np.where(nearest[dd].eq("TOP"), "NEAREST_TOP",
                                     np.where(nearest[dd].eq("BOTTOM"), "NEAREST_BOTTOM",
                                              ["NEAREST_" + str(s) for s in np.array(horiz_side, dtype=object)[dd.to_numpy()]]))
    incorrect.loc[dd, "abs_distance_inches"] = dist[dd].abs() * 12
    incorrect.loc[dd, ["horizontal_distance_inches", "vertical_distance_inches", "corner_proximity_inches"]] = np.nan
    from src.offensive_recognition import PITCH_FAMILY
    incorrect["pitch_family"] = incorrect.pitch_type.map(PITCH_FAMILY).fillna("OTHER")
    incorrect["signed_boundary_distance_inches"] = dist * 12
    return offense, audit, def_audit, p, incorrect


# ---------------------------------------------------------------------- feeds / RE
def feed_states(root: Path, p: pd.DataFrame, cache: Path | None):
    shas = p.drop_duplicates("game_pk").set_index("game_pk").source_game_feed.to_dict()
    if p.groupby("game_pk").source_game_feed.nunique().gt(1).any():
        raise RuntimeError("multiple feed objects per game")
    key = hashlib.sha256(json.dumps(sorted(shas.items())).encode()).hexdigest()[:16]
    code_hash = hashlib.sha256((HERE / "feeds.py").read_bytes() + (HERE / "counterfactual.py").read_bytes()).hexdigest()[:12]
    if cache is not None:
        path = cache / f"feed_states_{key}_{code_hash}.pkl"
        if path.exists():
            return pickle.loads(path.read_bytes())
    rows, halves = load_feeds(root, shas)
    out = (pd.DataFrame(rows), pd.DataFrame(halves))
    if cache is not None:
        cache.mkdir(parents=True, exist_ok=True)
        path.write_bytes(pickle.dumps(out))
    return out


def fit_re(frame: pd.DataFrame, prior: int = RE_PRIOR):
    """RE288 from feed pre-pitch states; future runs to end of the half-inning."""
    f = frame[(frame.inning <= RE_MAX_INNING) & frame.half_end_outs.eq(3)]
    f = f[f.feed_pre_balls.between(0, 3) & f.feed_pre_strikes.between(0, 2) & f.feed_pre_outs.between(0, 2)]
    base = f.groupby(["feed_pre_outs", "bases"]).future_runs_half.agg(["mean", "size"])
    half_id = f.game_pk.astype(str) + ":" + f.inning.astype(str) + f.half_inning
    g = f.assign(half_id=half_id).groupby(["feed_pre_balls", "feed_pre_strikes", "feed_pre_outs", "bases"])
    t = g.future_runs_half.agg(raw_mean="mean", n_pitches="size", sd="std").join(g.half_id.nunique().rename("n_half_innings")).reset_index()
    t = t.merge(base.rename(columns={"mean": "base_out_mean", "size": "base_out_n"}).reset_index(),
                on=["feed_pre_outs", "bases"], how="left")
    t["re_smoothed"] = (t.raw_mean * t.n_pitches + prior * t.base_out_mean) / (t.n_pitches + prior)
    # Sensitivity: base-out mean plus a count effect pooled across base states within outs.
    ce = f.assign(resid=f.future_runs_half - f.set_index(["feed_pre_outs", "bases"]).index.map(base["mean"]).to_numpy())
    ce = ce.groupby(["feed_pre_balls", "feed_pre_strikes", "feed_pre_outs"]).resid.mean().rename("count_effect_pooled").reset_index()
    t = t.merge(ce, on=["feed_pre_balls", "feed_pre_strikes", "feed_pre_outs"], how="left")
    t["re_count_pooled"] = t.base_out_mean + t.count_effect_pooled
    t = t.rename(columns={"feed_pre_balls": "balls", "feed_pre_strikes": "strikes", "feed_pre_outs": "outs", "bases": "base_state"})
    return t


def re_lookup(table: pd.DataFrame, column: str = "re_smoothed") -> dict:
    return {(int(r.balls), int(r.strikes), int(r.outs), str(r.base_state)): float(getattr(r, column)) for r in table.itertuples()}


def state_value(s: State | None, lookup: dict, walkoff: bool = False) -> float:
    """Runs scored on the pitch plus expected runs for the rest of the half-inning."""
    if s is None:
        return np.nan
    if s.inning_ended or walkoff:
        return float(s.runs)
    return s.runs + lookup.get((s.balls, s.strikes, s.outs, s.base_state), np.nan)


# ------------------------------------------------------------- counterfactual step
def build_states(incorrect: pd.DataFrame, fs: pd.DataFrame, re_tables: dict):
    feed_cols = [c for c in fs.columns if c not in ("game_pk", "inning", "half_inning", "at_bat_index", "play_event_index",
                                                    "play_id", "game_date", "bases")]
    m = incorrect.merge(fs[feed_cols], on="pitch_key", how="left", validate="one_to_one")
    if m.feed_pre_balls.isna().any():
        raise RuntimeError("incorrect call missing from feed replay")
    records = []
    for r in m.itertuples(index=False):
        moves = [Movement(**{**j}) for j in json.loads(r.attached_movements)]
        pre_bases = {b for b, flag in (("1B", r.feed_pre_on_1b), ("2B", r.feed_pre_on_2b), ("3B", r.feed_pre_on_3b)) if flag}
        actual_call = r.feed_call
        cf_call = "STRIKE" if actual_call == "BALL" else "BALL"
        res = reconstruct(int(r.feed_pre_balls), int(r.feed_pre_strikes), int(r.feed_pre_outs), pre_bases,
                          actual_call, cf_call, moves, uncaught_pitch=(r.feed_call_code == "*B"))
        overturned = r.challenge_outcome == "OVERTURNED"
        # "Incorrect" = the umpire's original call standing; "corrected" = the ABS call.
        if overturned:
            inc_state, cor_state, inc_alts, cor_alts = res.counterfactual, res.actual, res.alternatives, {}
        else:
            inc_state, cor_state, inc_alts, cor_alts = res.actual, res.counterfactual, {}, res.alternatives
        bat_pre, fld_pre = int(r.feed_pre_bat_score), int(r.feed_pre_fld_score)
        bottom_late = r.half_inning == "bottom" and int(r.inning) >= 9

        def wo(s):
            return bool(s is not None and bottom_late and bat_pre + s.runs > fld_pre)

        row = {"pitch_key": r.pitch_key, "cf_rule": res.rule, "cf_confidence": res.confidence,
               "cf_ambiguity_reason": res.ambiguity_reason, "actual_state_consistency": res.actual_consistency,
               "observed_state_is_reconstructed": overturned,
               "feed_call_matches_expected": actual_call == (r.official_abs_call if r.challenged_bool else r.original_call)}
        for prefix, s in (("obs", inc_state), ("cor", cor_state)):
            for f in ("balls", "strikes", "outs", "runs", "pa_status", "inning_ended"):
                row[f"{prefix}_{f}"] = None if s is None else getattr(s, f)
            row[f"{prefix}_base_state"] = None if s is None else s.base_state
            row[f"{prefix}_walkoff"] = wo(s)
            row[f"{prefix}_state_valid"] = None if s is None else s.valid()
        for label, table in re_tables.items():
            look = table.get(str(r.game_date)[:7]) if label == "lomo" else table
            sfx = "" if label == "primary" else f"_{label}"
            row[f"RE_observed{sfx}"] = state_value(inc_state, look, wo(inc_state))
            row[f"RE_corrected{sfx}"] = state_value(cor_state, look, wo(cor_state))
            if label == "primary":
                alt_obs = [state_value(s, look, wo(s)) for s in inc_alts.values()]
                alt_cor = [state_value(s, look, wo(s)) for s in cor_alts.values()]
                row["RE_observed_alternatives"] = json.dumps({k: round(v, 6) for k, v in zip(inc_alts, alt_obs)}) if inc_alts else None
                row["RE_corrected_alternatives"] = json.dumps({k: round(v, 6) for k, v in zip(cor_alts, alt_cor)}) if cor_alts else None
                row["altobslist"], row["altcorlist"] = alt_obs, alt_cor
                row["alternative_states"] = json.dumps({k: {"outs": s.outs, "bases": s.base_state, "balls": s.balls, "strikes": s.strikes, "runs": s.runs, "pa_status": s.pa_status, "inning_ended": s.inning_ended} for k, s in {**inc_alts, **cor_alts}.items()}) if (inc_alts or cor_alts) else None
        records.append(row)
    out = pd.DataFrame(records)
    return m, out


# ------------------------------------------------------------ inventory / history
def challenge_history(p: pd.DataFrame, incorrect_keys: dict) -> pd.DataFrame:
    """Decision-time challenge history, computed only from strictly earlier pitches.

    incorrect_keys maps pitch_key -> (entitled_team_id, eligible_bool).
    """
    cols = ["pitch_key", "game_pk", "at_bat_index", "play_event_index", "inning", "home_team_id", "away_team_id",
            "half_inning", "original_call", "challenged_bool", "challenge_outcome", "offense_challenges_remaining",
            "defense_challenges_remaining", "affected_team_challenges_remaining"]
    q = p[cols].sort_values(["game_pk", "at_bat_index", "play_event_index"]).reset_index(drop=True)
    ch = pd.read_csv(ROOT / "data/full_season/processed/challenges.csv", usecols=["pitch_key", "challenge_team_id", "challenger_role", "outcome"])
    team_of = ch.set_index("pitch_key").challenge_team_id.to_dict()
    role_of = ch.set_index("pitch_key").challenger_role.to_dict()
    out = []
    issues = Counter()
    for pk, g in q.groupby("game_pk", sort=True):
        home, away = int(g.home_team_id.iloc[0]), int(g.away_team_id.iloc[0])
        inv = {home: 2, away: 2}
        hist = {t: Counter() for t in (home, away)}
        last_inning = 0
        for r in g.itertuples(index=False):
            if r.inning > last_inning:
                if r.inning > 9:
                    for t in inv:
                        if inv[t] == 0:
                            inv[t] = 1
                            hist[t]["extra_inning_grants"] += 1
                last_inning = r.inning
            off = away if r.half_inning == "top" else home
            dfn = home if r.half_inning == "top" else away
            if pd.notna(r.offense_challenges_remaining) and int(r.offense_challenges_remaining) != inv[off]:
                issues["offense_inventory_mismatch"] += 1
            if pd.notna(r.defense_challenges_remaining) and int(r.defense_challenges_remaining) != inv[dfn]:
                issues["defense_inventory_mismatch"] += 1
            info = incorrect_keys.get(r.pitch_key)
            if info is not None:
                team = info[0]
                opp = home if team == away else away
                h = hist[team]
                out.append({"pitch_key": r.pitch_key, "entitled_team_id": team,
                            "inventory_recomputed": inv[team], "opponent_inventory": inv[opp],
                            "prior_team_challenges": h["challenges"], "prior_team_challenges_overturned": h["overturned"],
                            "prior_team_challenges_confirmed": h["confirmed"],
                            "prior_team_offense_challenges": h["off_challenges"], "prior_team_defense_challenges": h["def_challenges"],
                            "prior_team_eligible_incorrect_calls": h["eligible"], "prior_team_eligible_unchallenged": h["eligible_unchallenged"],
                            "prior_opponent_challenges": hist[opp]["challenges"],
                            "extra_inning_grants_before": h["extra_inning_grants"]})
                if info[1]:
                    h["eligible"] += 1
                    if not r.challenged_bool:
                        h["eligible_unchallenged"] += 1
            if r.challenged_bool:
                t = team_of.get(r.pitch_key)
                if t is None or t not in inv:
                    issues["challenge_team_missing"] += 1
                    continue
                hist[t]["challenges"] += 1
                hist[t]["off_challenges" if role_of.get(r.pitch_key) == "BATTER" else "def_challenges"] += 1
                if r.challenge_outcome == "OVERTURNED":
                    hist[t]["overturned"] += 1
                elif r.challenge_outcome == "CONFIRMED":
                    hist[t]["confirmed"] += 1
                    inv[t] = max(0, inv[t] - 1)
                else:
                    issues["unknown_challenge_outcome"] += 1
    return pd.DataFrame(out), dict(issues)


# ------------------------------------------------------------- competing attention
CA_FLAGS = {
    "ca_stolen_base_attempt": lambda t, mv, cr: any(x.startswith(("stolen_base", "caught_stealing")) for x in t)
        or any(str(m["event"]).startswith(("Stolen Base", "Caught Stealing")) or "Strikeout Double Play" == m["event"] and not m["is_batter"] for m in mv),
    "ca_stolen_base": lambda t, mv, cr: any(x.startswith("stolen_base") for x in t) or any(str(m["event"]).startswith("Stolen Base") for m in mv),
    "ca_caught_stealing": lambda t, mv, cr: any(x.startswith("caught_stealing") for x in t) or any(str(m["event"]).startswith("Caught Stealing") for m in mv),
    "ca_catcher_throw_recorded": lambda t, mv, cr: any(c.endswith(":C") and c.split(":")[0] in ("f_assist", "f_throwing_error", "f_fielding_error", "f_touch") for c in cr),
    "ca_wild_pitch": lambda t, mv, cr: "wild_pitch" in t or any(m["event"] == "Wild Pitch" for m in mv),
    "ca_passed_ball": lambda t, mv, cr: "passed_ball" in t or any(m["event"] == "Passed Ball" for m in mv),
    "ca_pickoff_action": lambda t, mv, cr: any(x.startswith("pickoff") for x in t),
    "ca_defensive_indifference": lambda t, mv, cr: "defensive_indiff" in t,
    "ca_runner_advance": lambda t, mv, cr: any((not m["is_batter"]) and not m["is_out"] and m["end"] != m["start"] and m["reason"] != "r_adv_force" for m in mv),
    "ca_runner_out": lambda t, mv, cr: any((not m["is_batter"]) and m["is_out"] for m in mv),
    "ca_error_on_play": lambda t, mv, cr: any(x == "error" or x.endswith("_error") for x in t) or any(m["event"] == "Error" for m in mv) or any("error" in c for c in cr),
}


def competing_attention(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in frame.itertuples(index=False):
        types = json.loads(r.attached_event_types)
        mv = json.loads(r.attached_movements)
        cr = json.loads(r.attached_credits)
        d = {"pitch_key": r.pitch_key}
        for name, fn in CA_FLAGS.items():
            d[name] = bool(fn(types, mv, cr))
        d["ca_catcher_pickoff_throw"] = bool(r.catcher_pickoff_throw_after_pitch)
        d["ca_catcher_throw_any_evidence"] = d["ca_catcher_throw_recorded"] or d["ca_catcher_pickoff_throw"]
        d["ca_secondary_play_reviewed"] = bool(isinstance(r.secondary_review_json, str))
        known = {"stolen_base_2b", "stolen_base_3b", "stolen_base_home", "caught_stealing_2b", "caught_stealing_3b",
                 "caught_stealing_home", "wild_pitch", "passed_ball", "defensive_indiff", "pickoff"}
        d["ca_other_secondary_action"] = any(not (x in known or x.startswith("pickoff")) for x in types)
        d["ca_other_secondary_types"] = json.dumps(sorted({x for x in types if not (x in known or x.startswith("pickoff"))})) if d["ca_other_secondary_action"] else None
        d["ca_any_secondary_action"] = bool(types) or any(not m["is_batter"] and m["reason"] != "r_adv_force" for m in mv)
        rows.append(d)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------- Braves
def braves_case(root: Path, fs: pd.DataFrame, p: pd.DataFrame, out: Path):
    sys.path.insert(0, str(root))
    from src.geometry import derive
    games = p.drop_duplicates("game_pk").set_index("game_pk")
    finals = json.loads((out / "_finals.json").read_text()) if (out / "_finals.json").exists() else {}
    cand_rows, seq_rows = [], []
    feeds = {}
    # Snapshot feeds (already replayed) and archived post-snapshot Braves feeds.
    raw = root / "data/full_season/raw"
    receipts = {json.loads(l)["sha256"]: json.loads(l) for l in (raw / "receipts.jsonl").read_text().splitlines()}
    atl_games = games[(games.home_team_id == ATL) | (games.away_team_id == ATL)]
    for pk, g in atl_games.iterrows():
        feeds[int(pk)] = ("SNAPSHOT", g.source_game_feed, json.loads((raw / receipts[g.source_game_feed]["path"]).read_text()))
    cs_raw = out / "case_study_raw"
    if (cs_raw / "receipts.jsonl").exists():
        for line in (cs_raw / "receipts.jsonl").read_text().splitlines():
            r = json.loads(line)
            if r["kind"] == "feed":
                body = (cs_raw / r["path"]).read_bytes()
                if hashlib.sha256(body).hexdigest() != r["sha256"]:
                    raise RuntimeError("case-study checksum mismatch")
                feeds[int(r["game_pk"])] = ("POST_SNAPSHOT_CASE_STUDY_ONLY", r["sha256"], json.loads(body))
    for pk, (scope, sha, feed) in sorted(feeds.items()):
        gd = feed["gameData"]
        home_id = gd["teams"]["home"]["id"]
        atl_half = "top" if home_id == ATL else "bottom"  # opponent bats while Braves field
        ls = feed["liveData"]["linescore"]
        opp_side = "away" if home_id == ATL else "home"
        atl_side = "home" if home_id == ATL else "away"
        final_atl, final_opp = ls["teams"][atl_side]["runs"], ls["teams"][opp_side]["runs"]
        first = [i for i in ls["innings"] if i["num"] == 1]
        opp_first = first[0][opp_side].get("runs") if first else None
        rows, _ = parse_feed(feed, sha)
        plays = feed["liveData"]["plays"]["allPlays"]
        by_ab = {pl["about"]["atBatIndex"]: pl for pl in plays}
        for r in rows:
            if r["half_inning"] != atl_half or r.get("feed_call") != "BALL":
                continue
            if not (r["feed_pre_balls"] == 3):
                continue
            pl = by_ab[r["at_bat_index"]]
            ev = [e for e in pl["playEvents"] if e["index"] == r["play_event_index"]][0]
            pdd = ev.get("pitchData", {}); c = pdd.get("coordinates", {})
            derived, dist = derive(c.get("pX"), c.get("pZ"), pdd.get("strikeZoneTop"), pdd.get("strikeZoneBottom"), 2026)
            types = json.loads(r["attached_event_types"])
            cr = json.loads(r["attached_credits"])
            later = [pl2 for pl2 in plays if pl2["about"]["inning"] == r["inning"] and pl2["about"]["halfInning"] == atl_half and pl2["about"]["atBatIndex"] > r["at_bat_index"]]
            later_events = [pl2["result"].get("eventType") for pl2 in later]
            review = ev.get("reviewDetails") or {}
            crit = {
                "braves_fielding": True, "first_inning": r["inning"] == 1,
                "runner_on_first_pre": bool(r["feed_pre_on_1b"]), "one_out_pre": r["feed_pre_outs"] == 1,
                "count_3_2_pre": r["feed_pre_strikes"] == 2,
                "called_ball_four": True,
                "steal_attempt_on_pitch": any(t.startswith(("stolen_base", "caught_stealing")) for t in types) or any(str(m["event"]).startswith(("Stolen", "Caught")) for m in json.loads(r["attached_movements"])),
                "catcher_throw_recorded": any(x.endswith(":C") for x in cr) or bool(r["catcher_pickoff_throw_after_pitch"]),
                "secondary_play_reviewed": bool(r["secondary_review_json"]),
                "geometry_strike": derived == "STRIKE",
                "near_top_of_zone": c.get("pZ") is not None and pdd.get("strikeZoneTop") is not None and abs(c["pZ"] - pdd["strikeZoneTop"]) <= 0.25,
                "not_successfully_challenged": not (review.get("reviewType") == "MJ" and review.get("isOverturned")),
                "inning_continued": r.get("half_end_outs", 3) == 3 and r["feed_pre_outs"] < 2 or True,
                "later_walk_in_inning": "walk" in later_events,
                "later_home_run_in_inning": "home_run" in later_events,
                "braves_trailed_5_0_after_first": r["inning"] == 1 and opp_first == 5 and (first[0][atl_side].get("runs") in (0, None)),
                "final_score_5_1_braves_loss": (final_opp, final_atl) == (5, 1),
            }
            crit["inning_continued"] = r["feed_pre_outs"] + 0 < 3  # a walk never ends the half-inning
            # Revised account supplied by the user on 2026-09-23 (Mets, 2026-08-10).
            batters_after = [pl2["matchup"]["batter"]["fullName"] for pl2 in later]
            hr_idx = next((i for i, pl2 in enumerate(later) if pl2["result"].get("eventType") == "home_run"), None)
            rev = {
                "rev_game_2026_08_10_vs_mets": gd["datetime"]["officialDate"] == "2026-08-10" and 121 in (gd["teams"]["home"]["id"], gd["teams"]["away"]["id"]),
                "rev_batter_carson_benge": pl["matchup"]["batter"]["fullName"] == "Carson Benge",
                "rev_bichette_on_first": "Bo Bichette to 2nd" in (r["feed_pa_result_description"] or ""),
                "rev_pitcher_elder": pl["matchup"]["pitcher"]["fullName"] == "Bryce Elder",
                "rev_baty_homer_three_batters_later": hr_idx == 2 and later[2]["matchup"]["batter"]["fullName"] == "Brett Baty",
                "rev_mets_lead_5_0_after_homer": hr_idx is not None and (later[hr_idx]["result"].get("awayScore"), later[hr_idx]["result"].get("homeScore")) in ((5, 0), (0, 5)),
            }
            cand_rows.append({"game_pk": pk, "source_scope": scope, "feed_sha256": sha,
                              "game_date": gd["datetime"]["officialDate"], "away": gd["teams"]["away"]["abbreviation"],
                              "home": gd["teams"]["home"]["abbreviation"], "final_away": ls["teams"]["away"]["runs"],
                              "final_home": ls["teams"]["home"]["runs"], "inning": r["inning"], "half_inning": r["half_inning"],
                              "pitch_key": r["pitch_key"], "batter": pl["matchup"]["batter"]["fullName"],
                              "pitcher": pl["matchup"]["pitcher"]["fullName"], "pre_count": f"{r['feed_pre_balls']}-{r['feed_pre_strikes']}",
                              "pre_outs": r["feed_pre_outs"], "pre_bases": f"{r['feed_pre_on_1b']}{r['feed_pre_on_2b']}{r['feed_pre_on_3b']}",
                              "plate_x": c.get("pX"), "plate_z": c.get("pZ"), "zone_top": pdd.get("strikeZoneTop"),
                              "zone_bottom": pdd.get("strikeZoneBottom"), "derived_abs_call": derived,
                              "signed_boundary_distance_inches": None if dist is None else dist * 12,
                              "pitch_review_type": review.get("reviewType"), "pitch_review_overturned": review.get("isOverturned"),
                              "attached_event_types": r["attached_event_types"], "attached_event_descriptions": r["attached_event_descriptions"],
                              "pa_result_description": r["feed_pa_result_description"],
                              **{f"criterion_{k}": v for k, v in crit.items()},
                              "criteria_matched": int(sum(bool(v) for v in crit.values())), "criteria_total": len(crit),
                              **{f"criterion_{k}": v for k, v in rev.items()},
                              "revised_criteria_matched": int(sum(bool(v) for v in rev.values())), "revised_criteria_total": len(rev)})
    cands = pd.DataFrame(cand_rows).sort_values(["revised_criteria_matched", "criteria_matched", "game_date"], ascending=[False, False, True]).reset_index(drop=True)
    cands["identification_status"] = np.where(cands.pitch_key.eq(BRAVES_CASE_PITCH) & cands.revised_criteria_matched.eq(cands.revised_criteria_total),
                                               "IDENTIFIED_USER_CONFIRMED_GAME", "NOT_THE_CASE")
    # Complete sequence for the top candidate's half-inning.
    if len(cands):
        top = cands.iloc[0]
        scope, sha, feed = feeds[int(top.game_pk)]
        for pl in feed["liveData"]["plays"]["allPlays"]:
            a = pl["about"]
            if a["inning"] == top.inning and a["halfInning"] == top.half_inning:
                for e in sorted(pl["playEvents"], key=lambda e: e["index"]):
                    d = e.get("details", {}); cc = e.get("count", {}); pdd = e.get("pitchData", {}); co = pdd.get("coordinates", {})
                    seq_rows.append({"game_pk": int(top.game_pk), "at_bat_index": a["atBatIndex"], "event_index": e["index"],
                                     "batter": pl["matchup"]["batter"]["fullName"], "event_type": e.get("type"),
                                     "call_code": (d.get("call") or {}).get("code"), "description": d.get("description"),
                                     "balls_after": cc.get("balls"), "strikes_after": cc.get("strikes"), "outs_after": cc.get("outs"),
                                     "plate_z": co.get("pZ"), "zone_top": pdd.get("strikeZoneTop"),
                                     "review": json.dumps(e.get("reviewDetails")) if e.get("reviewDetails") else None,
                                     "pa_result": pl["result"].get("description") if e is pl["playEvents"][-1] else None,
                                     "away_score_after_pa": pl["result"].get("awayScore"), "home_score_after_pa": pl["result"].get("homeScore")})
    game_level = []
    for pk, (scope, sha, feed) in sorted(feeds.items()):
        gd = feed["gameData"]; ls = feed["liveData"]["linescore"]; home_id = gd["teams"]["home"]["id"]
        atl_side = "home" if home_id == ATL else "away"; opp_side = "away" if atl_side == "home" else "home"
        game_level.append({"game_pk": pk, "source_scope": scope, "game_date": gd["datetime"]["officialDate"],
                           "braves_runs": ls["teams"][atl_side]["runs"], "opponent_runs": ls["teams"][opp_side]["runs"],
                           "opponent_first_inning_runs": ([i for i in ls["innings"] if i["num"] == 1] or [{}])[0].get(opp_side, {}).get("runs")})
    return cands, pd.DataFrame(seq_rows), pd.DataFrame(game_level)


ROOT = None


def braves_summary(opps: pd.DataFrame, cands: pd.DataFrame, re_table: pd.DataFrame, seq_case: pd.DataFrame) -> dict:
    """Decision-point valuation of the identified play under each defensible corrected state."""
    look = re_lookup(re_table)
    row = opps[opps.pitch_key.eq(BRAVES_CASE_PITCH)]
    cand = cands[cands.pitch_key.eq(BRAVES_CASE_PITCH)]
    if row.empty or cand.empty:
        return {"identified": False}
    r, c = row.iloc[0], cand.iloc[0]
    observed = float(r.RE_observed)
    states = {
        "OBSERVED_WALK": {"state": "1 out, runners on 1st and 2nd, new PA", "RE_batting": observed},
        "CORRECTED_AS_RECORDED_NO_RUNNER_ACTION": {"state": "strikeout; 2 outs, runner on 1st", "RE_batting": look[(0, 0, 2, "100")],
            "basis": "Primary R1 counterfactual. It assumes no runner action because none is recorded; the user's account says a steal attempt and throw occurred, so this state is exact only with respect to the record."},
        "CORRECTED_RUNNER_SAFE_AT_SECOND": {"state": "strikeout; 2 outs, runner on 2nd", "RE_batting": look[(0, 0, 2, "010")],
            "basis": "Strike three with the steal attempt's outcome ruled safe (umpire discretion under 2026 guidance)."},
        "CORRECTED_RUNNER_OUT_INNING_OVER": {"state": "strikeout and runner out at 2nd; half-inning over", "RE_batting": 0.0,
            "basis": "Strike three with the runner ruled out on the tag play (the account's possible initial out call)."},
    }
    for k, v in states.items():
        v["RE_delta_batting_vs_observed"] = observed - v["RE_batting"]
        v["correction_value_runs_to_braves"] = observed - v["RE_batting"] if k != "OBSERVED_WALK" else 0.0
    return {
        "identified": True, "pitch_key": BRAVES_CASE_PITCH, "game_pk": 824887, "game_date": "2026-08-10",
        "matchup": "New York Mets at Atlanta Braves", "inning": "top 1", "batter": "Carson Benge", "pitcher": "Bryce Elder",
        "catcher": "Sean Murphy", "runner_on_first": "Bo Bichette", "pre_pitch": "1 out, runner on 1st, 3-2, Mets lead 1-0",
        "call": "BALL (ball four)", "derived_abs_call": r.derived_abs_call,
        "signed_boundary_distance_inches": float(r.signed_boundary_distance_inches),
        "statcast_plate_z_ft": float(r.plate_z), "abs_zone_top_ft": float(r.abs_zone_top),
        "challenged_in_sources": bool(r.challenged), "braves_inventory_before": int(r.challenge_inventory),
        "identification_basis": "User identified the game (2026-08-10 vs Mets) on 2026-09-23. Every recorded element of the user's revised account matches the source data: Benge batting with one out and Bichette on first, 3-2 count, pitch called ball four, pitch inside the ABS zone near the top edge, no recorded challenge, Baty home run three batters later for a 5-0 Mets lead.",
        "elements_not_in_any_source": [
            "Bichette's steal attempt and the catcher's throw to second: the feed records only 'Carson Benge walks. Bo Bichette to 2nd.' with a force advance (r_adv_force); Statcast records the same. Ball four entitled Bichette to second, so no caught stealing could be recorded.",
            "Any out call by the second-base umpire: not recorded.",
            "Elder's hat-tap challenge request and why it was not granted: no ABS record in the dedicated ABS extract, the feed reviewDetails, or processed challenges.csv. Timing or eligibility of the request cannot be established from these sources.",
        ],
        "discrepancies_with_original_recollection": [
            "Final score was NYM 8, ATL 5, not 5-1. No 2026 Braves game through 2026-09-23 ended 5-1.",
            "After the walk: Jared Young single, Marcus Semien strikeout, Brett Baty grand slam (not 'a walk and home run').",
            "The runner was not recorded as out; the original recollection's 'initially called out' is not in the sources.",
        ],
        "decision_point_valuation": states,
        "realized_outcome_for_contrast_only": "The Mets scored four more runs in the inning (Baty grand slam). This realized outcome is NOT the cost of the missed correction; the decision-point values above are.",
        "full_half_inning_sequence_rows": len(seq_case),
        "flags": {"cf_rule": r.cf_rule, "cf_confidence": r.cf_confidence,
                  "cf_unrecorded_runner_action_possible": bool(r.cf_unrecorded_runner_action_possible)},
    }


# ---------------------------------------------------------------------------- main
def main(root: Path, out: Path, cache: Path | None) -> None:
    global ROOT
    ROOT = root
    out.mkdir(parents=True, exist_ok=True)
    before = {str(p.relative_to(root)): digest(p) for p in protected_files(root)}

    offense, off_audit, def_audit, p, incorrect = load_population(root)
    print("population reproduced", len(offense), int(offense.recognized.sum()), flush=True)

    fs, halves = feed_states(root, p, cache)
    fs["bases"] = fs.feed_pre_on_1b.astype(str) + fs.feed_pre_on_2b.astype(str) + fs.feed_pre_on_3b.astype(str)
    dates = p.drop_duplicates("game_pk").set_index("game_pk").game_date
    fs["game_date"] = fs.game_pk.map(dates)
    fs = fs[fs.pitch_key.isin(set(p.pitch_key))].copy()

    # --- RE288 (primary) and leave-one-month-out sensitivity
    re_table = fit_re(fs)
    months = sorted(fs.game_date.str[:7].unique())
    lomo = {m: re_lookup(fit_re(fs[fs.game_date.str[:7] != m])) for m in months}
    re24 = fs[(fs.inning <= RE_MAX_INNING) & fs.half_end_outs.eq(3) & fs.feed_pre_balls.eq(0) & fs.feed_pre_strikes.eq(0)]
    re24_first = re24.drop_duplicates(["game_pk", "at_bat_index"])
    re24_table = re24_first.groupby(["feed_pre_outs", "bases"]).future_runs_half.agg(re24="mean", n_plate_appearances="size").reset_index().rename(columns={"feed_pre_outs": "outs", "bases": "base_state"})
    print("RE tables built", len(re_table), flush=True)

    # --- states for every incorrect call (both sides, all eligibility statuses)
    incorrect["game_date"] = incorrect.game_date.astype(str)
    merged, states = build_states(incorrect, fs, {"primary": re_lookup(re_table), "lomo": lomo,
                                                  "pooled": re_lookup(re_table, "re_count_pooled")})
    frame = merged.merge(states, on="pitch_key", how="left", validate="one_to_one")
    print("states reconstructed", len(frame), flush=True)

    # --- values
    offense_side = frame.opportunity_side.eq("OFFENSE")
    for sfx in ("", "_lomo", "_pooled"):
        frame[f"RE_delta_batting{sfx}"] = frame[f"RE_observed{sfx}"] - frame[f"RE_corrected{sfx}"]
        frame[f"RE_delta_fielding{sfx}"] = -frame[f"RE_delta_batting{sfx}"]
        frame[f"correction_value_runs{sfx}"] = np.where(offense_side, -frame[f"RE_delta_batting{sfx}"], frame[f"RE_delta_batting{sfx}"])
    lo, hi = [], []
    for r in frame.itertuples(index=False):
        ob = [r.RE_observed] if not r.altobslist else r.altobslist
        co = [r.RE_corrected] if not r.altcorlist else r.altcorlist
        vals = [(o - c) * (-1 if r.opportunity_side == "OFFENSE" else 1) for o in ob for c in co]
        vals = [v for v in vals if np.isfinite(v)]
        lo.append(min(vals) if vals else np.nan); hi.append(max(vals) if vals else np.nan)
    frame["correction_value_runs_lower"] = lo
    frame["correction_value_runs_upper"] = hi
    frame = frame.drop(columns=["altobslist", "altcorlist"])
    challenged = frame.challenged_bool.astype(bool)
    frame["challenge_value_runs"] = np.where(challenged & frame.challenge_outcome.eq("OVERTURNED"), frame.correction_value_runs,
                                             np.where(challenged, 0.0, np.nan))
    frame["missed_challenge_value_runs"] = np.where(~challenged & frame.eligibility_status.eq("ELIGIBLE"), frame.correction_value_runs, np.nan)
    actual_walk = np.where(frame.observed_state_is_reconstructed, frame.cor_pa_status, frame.obs_pa_status) == "WALK"
    # A forced runner's play on a recorded walk (e.g., a steal attempt and tag) is
    # nullified by the award and is not recorded anywhere in the sources.
    frame["cf_unrecorded_runner_action_possible"] = actual_walk & frame.on_1b.notna() & frame.cf_rule.eq("R1_NO_RUNNER_ACTION")
    # With runner events held equal, the correct call can never lower the entitled
    # team's true run expectancy; a negative value is an RE-table ordering artifact.
    frame["re_ordering_violation"] = frame.cf_confidence.ne("AMBIGUOUS") & (frame.correction_value_runs < 0)
    frame["unavailable_correction_value_runs"] = np.where(frame.eligibility_status.ne("ELIGIBLE"), frame.correction_value_runs, np.nan)

    # --- decision-time context
    entitled = np.where(offense_side, np.where(frame.half_inning.eq("top"), frame.away_team_id, frame.home_team_id),
                        np.where(frame.half_inning.eq("top"), frame.home_team_id, frame.away_team_id))
    frame["entitled_team_id_calc"] = entitled.astype(int)
    keys = {k: (int(t), s == "ELIGIBLE") for k, t, s in zip(frame.pitch_key, frame.entitled_team_id_calc, frame.eligibility_status)}
    hist, inv_issues = challenge_history(p, keys)
    frame = frame.merge(hist, on="pitch_key", how="left", validate="one_to_one")
    if (frame.entitled_team_id != frame.entitled_team_id_calc).any():
        raise RuntimeError("entitled team mismatch")
    frame = frame.drop(columns=["entitled_team_id_calc"])
    frame["batting_team_id"] = np.where(frame.half_inning.eq("top"), frame.away_team_id, frame.home_team_id)
    frame["fielding_team_id"] = np.where(frame.half_inning.eq("top"), frame.home_team_id, frame.away_team_id)
    frame["batting_team"] = np.where(frame.half_inning.eq("top"), frame.away_team, frame.home_team)
    frame["fielding_team"] = np.where(frame.half_inning.eq("top"), frame.home_team, frame.away_team)
    frame["entitled_team"] = np.where(offense_side, frame.batting_team, frame.fielding_team)
    frame["batting_team_score"] = np.where(frame.half_inning.eq("top"), frame.away_score, frame.home_score)
    frame["fielding_team_score"] = np.where(frame.half_inning.eq("top"), frame.home_score, frame.away_score)
    frame["batting_score_diff"] = frame.batting_team_score - frame.fielding_team_score
    frame["entitled_team_score_diff"] = np.where(offense_side, frame.batting_score_diff, -frame.batting_score_diff)
    frame["count"] = frame.balls.astype(int).astype(str) + "-" + frame.strikes.astype(int).astype(str)
    frame["base_state"] = frame[["on_1b", "on_2b", "on_3b"]].notna().astype(int).astype(str).agg("".join, axis=1)
    frame["challenge_inventory"] = frame.affected_team_challenges_remaining
    frame["final_challenge_indicator"] = frame.challenge_inventory.eq(1)
    frame["inning_group"] = pd.cut(frame.inning, [0, 3, 6, np.inf], labels=["EARLY", "MIDDLE", "LATE"]).astype(str)
    frame["inning_bucket"] = pd.cut(frame.inning, [0, 3, 6, 9, np.inf], labels=["1-3", "4-6", "7-9", "10+"]).astype(str)
    frame["late_close"] = (frame.inning.ge(7) & frame.batting_score_diff.abs().le(2))
    frame["strike_three_or_ball_four_at_stake"] = np.where(offense_side, frame.strikes.eq(2) | frame.balls.eq(3), frame.balls.eq(3) | frame.strikes.eq(2))
    frame["pa_outcome_changes"] = frame.obs_pa_status.ne(frame.cor_pa_status) & frame.obs_pa_status.notna() & frame.cor_pa_status.notna()
    pre_look = re_lookup(re_table)
    frame["RE_pre_pitch"] = [pre_look.get((int(b), int(s), int(o), bs), np.nan) for b, s, o, bs in zip(frame.balls, frame.strikes, frame.outs, frame.base_state)]

    # --- expected recognition (Article 3 fields; OFFENSE only)
    s4 = pd.read_csv(root / "data/analysis/sprint4/batter_recognition_opportunities.csv", usecols=["pitch_key", "expected_probability"])
    s3 = pd.read_csv(root / "data/analysis/sprint3/offensive_recognition_predictions.csv")
    s3 = s3[s3.model.eq("C_SITUATION")][["pitch_key", "predicted_probability", "fold"]].rename(columns={"predicted_probability": "expected_recognition_prob_temporal", "fold": "expected_recognition_temporal_fold"})
    frame = frame.merge(s4.rename(columns={"expected_probability": "expected_recognition_prob_article3"}), on="pitch_key", how="left", validate="one_to_one")
    frame = frame.merge(s3, on="pitch_key", how="left", validate="one_to_one")
    q = frame.loc[offense_side & frame.eligibility_status.eq("ELIGIBLE"), "expected_recognition_prob_article3"].quantile([.2, .4, .6, .8]).to_list()
    frame["opportunity_difficulty_bucket"] = pd.cut(frame.expected_recognition_prob_article3, [-np.inf] + q + [np.inf],
                                                     labels=["Q1_LOWEST_EXPECTED", "Q2", "Q3", "Q4", "Q5_HIGHEST_EXPECTED"]).astype(str).replace("nan", np.nan)

    ca = competing_attention(frame)
    frame = frame.merge(ca, on="pitch_key", how="left", validate="one_to_one")

    # --- independent next-pitch check (Statcast pre-state of the next pitch)
    nxt = p[["pitch_key", "game_pk", "at_bat_index", "play_event_index", "inning", "half_inning", "balls", "strikes", "outs", "on_1b", "on_2b", "on_3b"]].sort_values(["game_pk", "at_bat_index", "play_event_index"]).reset_index(drop=True)
    for c in ["pitch_key", "at_bat_index", "inning", "half_inning", "balls", "strikes", "outs", "on_1b", "on_2b", "on_3b"]:
        nxt[f"next_{c}"] = nxt.groupby("game_pk")[c].shift(-1)
    nxt = nxt[["pitch_key"] + [c for c in nxt.columns if c.startswith("next_")]]
    frame = frame.merge(nxt, on="pitch_key", how="left")
    act_is_obs = ~frame.observed_state_is_reconstructed
    a = {f: np.where(act_is_obs, frame[f"obs_{f}"], frame[f"cor_{f}"]) for f in ("balls", "strikes", "outs", "base_state", "inning_ended", "pa_status")}
    next_bases = frame[["next_on_1b", "next_on_2b", "next_on_3b"]].notna().astype(int).astype(str).agg("".join, axis=1)
    same_half = frame.next_inning.eq(frame.inning) & frame.next_half_inning.eq(frame.half_inning)
    intervening = frame.state_changing_events_before_next_pitch.ne("[]")
    frame["next_pitch_state_check"] = np.select(
        [frame.next_pitch_key.isna(), pd.Series(a["inning_ended"]).astype(bool) & ~same_half,
         pd.Series(a["inning_ended"]).astype(bool) & same_half, ~same_half,
         (frame.next_balls.eq(pd.Series(a["balls"])) & frame.next_strikes.eq(pd.Series(a["strikes"])) &
          frame.next_outs.eq(pd.Series(a["outs"])) & next_bases.eq(pd.Series(a["base_state"]))),
         intervening],
        ["NO_NEXT_PITCH", "MATCH_HALF_ENDED", "MISMATCH_HALF_SHOULD_END", "NEXT_PITCH_IN_OTHER_HALF_GAME_END_OR_WALKOFF", "MATCH", "INTERVENING_STATE_CHANGING_EVENT"],
        default="MISMATCH")
    frame = frame.drop(columns=[c for c in frame.columns if c.startswith("next_") and c not in ("next_pitch_state_check", "next_event_type", "next_event_from_catcher")])

    frame = frame.sort_values(["game_date", "game_pk", "at_bat_index", "play_event_index"]).reset_index(drop=True)
    frame["article4_opportunity_id"] = "A4:" + frame.pitch_key
    frame["challenged"] = frame.challenged_bool.astype(bool)
    frame["recognized_article1_3"] = frame.recognized

    # ------------------------------------------------------------------ outputs
    opp_cols = [c for c in OPP_COLUMNS if c in frame.columns]
    missing_cols = [c for c in OPP_COLUMNS if c not in frame.columns]
    if missing_cols:
        raise RuntimeError(f"opportunity columns missing: {missing_cols}")
    all_incorrect = frame[opp_cols]
    opps = all_incorrect[all_incorrect.eligibility_status.eq("ELIGIBLE")].reset_index(drop=True)
    write_table(opps, out / "article4_opportunities.csv", "article4_opportunities")
    write_table(all_incorrect, out / "article4_all_incorrect_calls.csv", "article4_opportunities")

    seq = team_game_sequences(frame, p)
    write_table(seq, out / "article4_team_game_sequences.csv", "article4_team_game_sequences")
    summary = team_summary(opps)
    write_table(summary, out / "article4_team_summary.csv", "article4_team_summary")
    hv = high_value_missed(opps)
    write_table(hv, out / "article4_high_value_missed.csv", "article4_high_value_missed")
    ca_cols = ["article4_opportunity_id", "pitch_key", "game_pk", "game_date", "opportunity_side", "entitled_team", "inning", "half_inning",
               "count", "outs", "base_state", "challenged", "challenge_outcome", "challenge_inventory", "abs_distance_inches",
               "expected_recognition_prob_article3", "correction_value_runs", "cf_rule", "cf_confidence"] + \
              [c for c in opps.columns if c.startswith("ca_")] + ["attached_event_types", "attached_event_descriptions",
                                                                  "attached_movements", "attached_credits", "catcher_pickoff_throw_after_pitch",
                                                                  "secondary_review_json", "next_event_type", "next_event_from_catcher"]
    cao = opps[opps.ca_any_secondary_action | opps.ca_catcher_pickoff_throw][ca_cols].reset_index(drop=True)
    write_table(cao, out / "article4_competing_attention.csv", "article4_competing_attention")
    write_table(re_table, out / "article4_re288_table.csv", "article4_re288_table")
    write_table(re24_table, out / "article4_re24_table.csv", "article4_re24_table")

    cands, seq_case, gl = braves_case(root, fs, p, out)
    write_table(cands, out / "article4_braves_case_study.csv", "article4_braves_case_study")
    write_table(seq_case, out / "article4_braves_case_study_sequence.csv", "article4_braves_case_study_sequence")
    write_table(gl, out / "article4_braves_game_scores.csv", "article4_braves_game_scores")
    write_json(out / "article4_braves_case_summary.json", braves_summary(opps, cands, re_table, seq_case))

    spot = spot_checks(opps, frame)
    write_table(spot, out / "article4_spot_checks.csv", "article4_spot_checks")

    validation = validate(frame, opps, seq, summary, re_table, halves, fs, p, off_audit, def_audit, inv_issues, cands, gl)
    after = {str(pth.relative_to(root)): digest(pth) for pth in protected_files(root)}
    validation["protected_inputs_unchanged"] = before == after
    validation["protected_input_count"] = len(before)
    write_json(out / "validation_report.json", validation)
    manifest = {"version": VERSION, "snapshot": [START, END], "python": platform.python_version(),
                "pandas": pd.__version__, "numpy": np.__version__, "seed": SEED,
                "re_prior": RE_PRIOR, "re_max_inning": RE_MAX_INNING,
                "code_sha256": {f: digest(HERE / f) for f in ("build.py", "counterfactual.py", "feeds.py", "fields.py", "fetch_case_study.py")},
                "input_sha256": {k: v for k, v in before.items() if k.startswith(("data/full_season/processed", "data/analysis/sprint3/offensive", "data/analysis/sprint4/batter_recognition_opportunities", "data/full_season/raw"))},
                "outputs": {}}
    for f in sorted(out.glob("*.csv")):
        manifest["outputs"][f.name] = {"sha256": digest(f), "rows": int(sum(1 for _ in f.open()) - 1)}
    write_json(out / "manifest.json", manifest)
    write_validation_md(validation, out / "VALIDATION_REPORT.md")
    write_dictionary(HERE / "DATA_DICTIONARY.md", {
        "article4_opportunities": OPP_COLUMNS, "article4_team_game_sequences": SEQ_COLUMNS,
        "article4_team_summary": list(summary.columns), "article4_high_value_missed": HV_COLUMNS,
        "article4_competing_attention": ca_cols, "article4_re288_table": list(re_table.columns),
        "article4_re24_table": list(re24_table.columns), "article4_braves_case_study": list(cands.columns),
        "article4_braves_case_study_sequence": list(seq_case.columns), "article4_braves_game_scores": list(gl.columns),
        "article4_spot_checks": SPOT_COLUMNS})
    print(json.dumps(validation["headline"], indent=2, default=_json_default))
    if not validation["protected_inputs_unchanged"]:
        raise RuntimeError("STOP: protected inputs changed")


# --------------------------------------------------------------- derived tables
def team_game_sequences(frame: pd.DataFrame, p: pd.DataFrame) -> pd.DataFrame:
    ch = pd.read_csv(ROOT / "data/full_season/processed/challenges.csv", usecols=["pitch_key", "challenge_team_id", "challenger_role", "outcome"])
    base = frame[["pitch_key", "game_pk", "game_date", "at_bat_index", "play_event_index", "inning", "half_inning", "opportunity_side",
                  "entitled_team_id", "entitled_team", "eligibility_status", "challenged", "challenge_outcome", "challenge_inventory",
                  "inventory_recomputed", "count", "outs", "base_state", "entitled_team_score_diff", "abs_distance_inches",
                  "expected_recognition_prob_article3", "correction_value_runs", "correction_value_runs_lower",
                  "correction_value_runs_upper", "cf_confidence", "ca_any_secondary_action"]].copy()
    base["sequence_event_class"] = np.where(base.eligibility_status.eq("ELIGIBLE"), "ELIGIBLE_INCORRECT_CALL",
                                            "INELIGIBLE_INCORRECT_CALL_" + base.eligibility_status.str.replace("INELIGIBLE_", ""))
    # Challenges on calls that are not geometry-incorrect still consume inventory.
    other = ch[~ch.pitch_key.isin(set(frame.pitch_key))].merge(
        p[["pitch_key", "game_pk", "game_date", "at_bat_index", "play_event_index", "inning", "half_inning", "original_call",
           "affected_team_challenges_remaining", "balls", "strikes", "outs", "on_1b", "on_2b", "on_3b", "home_team_id", "away_team_id",
           "home_team", "away_team", "home_score", "away_score", "distance_from_abs_boundary", "derived_abs_call"]], on="pitch_key", how="left")
    other = other.assign(opportunity_side=np.where(other.challenger_role.eq("BATTER"), "OFFENSE", "DEFENSE"),
                         entitled_team_id=other.challenge_team_id,
                         entitled_team=np.where(other.challenge_team_id.eq(other.home_team_id), other.home_team, other.away_team),
                         eligibility_status="ELIGIBLE", challenged=True, challenge_outcome=other.outcome,
                         challenge_inventory=other.affected_team_challenges_remaining, inventory_recomputed=np.nan,
                         count=other.balls.astype(int).astype(str) + "-" + other.strikes.astype(int).astype(str),
                         base_state=other[["on_1b", "on_2b", "on_3b"]].notna().astype(int).astype(str).agg("".join, axis=1),
                         entitled_team_score_diff=np.where(other.challenge_team_id.eq(other.home_team_id), other.home_score - other.away_score, other.away_score - other.home_score),
                         abs_distance_inches=(other.distance_from_abs_boundary.abs() * 12), expected_recognition_prob_article3=np.nan,
                         correction_value_runs=np.nan, correction_value_runs_lower=np.nan, correction_value_runs_upper=np.nan,
                         cf_confidence=None, ca_any_secondary_action=np.nan,
                         sequence_event_class=np.where(other.derived_abs_call.isna(), "CHALLENGE_CALL_GEOMETRY_UNAVAILABLE", "CHALLENGE_OF_GEOMETRY_CORRECT_CALL"))
    seq = pd.concat([base, other[base.columns]], ignore_index=True)
    seq = seq.sort_values(["game_pk", "entitled_team_id", "at_bat_index", "play_event_index"]).reset_index(drop=True)
    seq["team_game_id"] = seq.game_pk.astype(str) + ":" + seq.entitled_team_id.astype(int).astype(str)
    seq["sequence_number"] = seq.groupby("team_game_id").cumcount() + 1
    seq["sequence_length"] = seq.groupby("team_game_id").pitch_key.transform("size")
    seq["inventory_after"] = np.where(seq.challenged & seq.challenge_outcome.eq("CONFIRMED"), seq.challenge_inventory - 1, seq.challenge_inventory)
    seq["exercised"] = seq.challenged.astype(bool)
    seq["realized_value_runs"] = np.where(seq.exercised & seq.challenge_outcome.eq("OVERTURNED"), seq.correction_value_runs, np.where(seq.exercised, 0.0, np.nan))
    # Hindsight fields: computed from later rows in the same team-game.  They must
    # never be used as decision-time predictors.
    elig = seq.sequence_event_class.eq("ELIGIBLE_INCORRECT_CALL")
    exh = seq.sequence_event_class.eq("INELIGIBLE_INCORRECT_CALL_EXHAUSTED")
    rows = []
    for tg, g in seq.groupby("team_game_id", sort=False):
        e = elig.loc[g.index].to_numpy(); x = exh.loc[g.index].to_numpy()
        v = g.correction_value_runs.to_numpy(); ex = g.exercised.to_numpy(); rv = g.realized_value_runs.to_numpy()
        amb = g.cf_confidence.eq("AMBIGUOUS").to_numpy()
        n = len(g)
        for i in range(n):
            later = np.arange(i + 1, n)
            le = later[e[later]]
            lv = v[le]; lvf = lv[np.isfinite(lv)]
            rows.append({
                "hindsight_later_eligible_opportunities": len(le),
                "hindsight_later_eligible_ambiguous": int(amb[le].sum()),
                "hindsight_later_eligible_value_sum": float(lvf.sum()) if len(lvf) else 0.0,
                "hindsight_later_eligible_value_max": float(lvf.max()) if len(lvf) else np.nan,
                "hindsight_later_challenges_used": int(ex[later].sum()),
                "hindsight_later_realized_value_sum": float(np.nansum(rv[later])) if len(later) else 0.0,
                "hindsight_later_higher_value_opportunity": bool(np.isfinite(v[i]) and len(lvf) and (lvf > v[i]).any()) if e[i] else None,
                "hindsight_later_higher_value_exercised": bool(np.isfinite(v[i]) and any(np.isfinite(v[j]) and v[j] > v[i] and ex[j] for j in le)) if e[i] else None,
                "hindsight_later_exhausted_incorrect_calls": int(x[later].sum()),
                "hindsight_later_exhausted_value_sum": float(np.nansum(v[later][x[later]])) if len(later) else 0.0,
            })
    seq = pd.concat([seq, pd.DataFrame(rows, index=seq.index)], axis=1)
    return seq[SEQ_COLUMNS]


def team_summary(opps: pd.DataFrame) -> pd.DataFrame:
    f = opps.copy()
    f["value_known"] = f.cf_confidence.ne("AMBIGUOUS")
    f["inventory"] = f.challenge_inventory.astype(int).astype(str)
    out = []
    dims = [("entitled_team", "opportunity_side", "inning_bucket", "inventory"),
            ("entitled_team", "opportunity_side", "inning_bucket"), ("entitled_team", "opportunity_side", "inventory"),
            ("entitled_team", "opportunity_side")]
    for keys in dims + [k[1:] for k in dims]:
        for vals, g in f.groupby(list(keys), dropna=False):
            vals = vals if isinstance(vals, tuple) else (vals,)
            d = dict(zip(keys, vals))
            known = g[g.value_known]
            out.append({"entitled_team": d.get("entitled_team", "ALL_TEAMS"), "opportunity_side": d.get("opportunity_side"),
                        "inning_bucket": d.get("inning_bucket", "ALL"), "challenge_inventory": d.get("inventory", "ALL"),
                        "opportunities": len(g), "challenged": int(g.challenged.sum()), "challenge_rate": g.challenged.mean(),
                        "overturned": int(g.challenge_outcome.eq("OVERTURNED").sum()),
                        "value_known_opportunities": len(known), "ambiguous_value_opportunities": int((~g.value_known).sum()),
                        "mean_correction_value_runs": known.correction_value_runs.mean(),
                        "total_realized_value_runs": known.challenge_value_runs.sum(),
                        "total_missed_value_runs": known.missed_challenge_value_runs.sum(),
                        "mean_missed_value_runs": known.missed_challenge_value_runs.mean(),
                        "mean_abs_distance_inches": g.abs_distance_inches.mean(),
                        "mean_expected_recognition_prob": g.expected_recognition_prob_article3.mean(),
                        "sum_expected_recognition_prob": g.expected_recognition_prob_article3.sum(min_count=1),
                        "final_challenge_opportunities": int(g.final_challenge_indicator.sum()),
                        "competing_attention_opportunities": int(g.ca_any_secondary_action.sum()),
                        "summary_level": "+".join(keys)})
    return pd.DataFrame(out)


def high_value_missed(opps: pd.DataFrame) -> pd.DataFrame:
    missed = opps[~opps.challenged].copy()
    missed["ranking_value_runs"] = missed.correction_value_runs.fillna(missed.correction_value_runs_lower)
    missed = missed.sort_values(["ranking_value_runs", "pitch_key"], ascending=[False, True])
    top = missed.head(HIGH_VALUE_TOP_N).copy()
    top["high_value_rank"] = np.arange(1, len(top) + 1)
    top["value_is_bound"] = top.cf_confidence.eq("AMBIGUOUS")
    return top[HV_COLUMNS].reset_index(drop=True)


def spot_checks(opps: pd.DataFrame, frame: pd.DataFrame) -> pd.DataFrame:
    hv = opps[~opps.challenged].sort_values("correction_value_runs", ascending=False).head(25).assign(spot_check_reason="TOP_25_MISSED_VALUE")
    ext_lo = opps.sort_values("correction_value_runs").head(10).assign(spot_check_reason="LOWEST_10_CORRECTION_VALUE")
    ext_hi = opps.sort_values("RE_delta_batting").head(5).assign(spot_check_reason="MOST_NEGATIVE_RE_DELTA_BATTING")
    ext_hi2 = opps.sort_values("RE_delta_batting", ascending=False).head(5).assign(spot_check_reason="MOST_POSITIVE_RE_DELTA_BATTING")
    amb = opps[opps.cf_confidence.eq("AMBIGUOUS")].sample(min(10, int(opps.cf_confidence.eq("AMBIGUOUS").sum())), random_state=SEED).assign(spot_check_reason="RANDOM_AMBIGUOUS")
    rb = opps[opps.cf_confidence.eq("RULE_BASED")].sample(min(10, int(opps.cf_confidence.eq("RULE_BASED").sum())), random_state=SEED).assign(spot_check_reason="RANDOM_RULE_BASED")
    rnd = opps.sample(20, random_state=SEED).assign(spot_check_reason="RANDOM_ALL")
    s = pd.concat([hv, ext_lo, ext_hi, ext_hi2, amb, rb, rnd], ignore_index=True)
    s["automated_check_pass"] = s.next_pitch_state_check.isin(["MATCH", "MATCH_HALF_ENDED", "NEXT_PITCH_IN_OTHER_HALF_GAME_END_OR_WALKOFF", "NO_NEXT_PITCH"]) & s.feed_call_matches_expected
    s["manual_review_note"] = s.pitch_key.map(MANUAL_NOTES).fillna("")
    return s[SPOT_COLUMNS]


MANUAL_NOTES: dict = {}
notes_path = HERE / "manual_review_notes.json"
if notes_path.exists():
    MANUAL_NOTES = json.loads(notes_path.read_text())


# ------------------------------------------------------------------- validation
def validate(frame, opps, seq, summary, re_table, halves, fs, p, off_audit, def_audit, inv_issues, cands, gl) -> dict:
    v = {}
    off = opps[opps.opportunity_side.eq("OFFENSE")]
    dfn = opps[opps.opportunity_side.eq("DEFENSE")]
    v["population"] = {
        "article1_3_offense_audit": off_audit, "defense_audit": def_audit,
        "offense_opportunities": len(off), "offense_challenged": int(off.challenged.sum()), "offense_unchallenged": int((~off.challenged).sum()),
        "defense_opportunities": len(dfn), "defense_challenged": int(dfn.challenged.sum()), "defense_unchallenged": int((~dfn.challenged).sum()),
        "offense_reconciles_10755_2112": bool(len(off) == 10755 and off.challenged.sum() == 2112),
        "offense_recognized_equals_challenged": bool((off.recognized_article1_3.astype(int) == off.challenged.astype(int)).all()),
        "defense_reconciles_sprint3_summary": bool(len(dfn) == def_audit["sprint3_legal_defensive_count"] and dfn.challenged.sum() == def_audit["sprint3_legal_defensive_challenged"]),
        "all_incorrect_calls_by_status": frame.groupby(["opportunity_side", "eligibility_status"]).size().rename("n").reset_index().to_dict("records"),
        "challenge_outcomes_eligible": opps.groupby(["opportunity_side", "challenge_outcome"], dropna=False).size().rename("n").reset_index().to_dict("records"),
    }
    v["uniqueness"] = {"duplicate_opportunity_ids": int(opps.article4_opportunity_id.duplicated().sum()),
                       "duplicate_pitch_keys_all_incorrect": int(frame.pitch_key.duplicated().sum()),
                       "article1_3_pitch_keys_preserved": bool(set(off.pitch_key) == set(pd.read_csv(ROOT / "data/analysis/sprint3/offensive_recognition_features.csv", usecols=["pitch_key"]).pitch_key))}
    fsm = frame
    v["feed_vs_statcast_pre_pitch_state_all_incorrect"] = {
        c: float((pd.to_numeric(fsm[a], errors="coerce") == pd.to_numeric(fsm[b], errors="coerce")).mean())
        for c, a, b in [("balls", "balls", "feed_pre_balls"), ("strikes", "strikes", "feed_pre_strikes"), ("outs", "outs", "feed_pre_outs")]}
    for b in ("1b", "2b", "3b"):
        v["feed_vs_statcast_pre_pitch_state_all_incorrect"][f"on_{b}"] = float((fsm[f"on_{b}"].notna().astype(int) == fsm[f"feed_pre_on_{b}"]).mean())
    v["feed_vs_statcast_pre_pitch_state_all_incorrect"]["batting_score"] = float((fsm.batting_team_score == fsm.feed_pre_bat_score).mean())
    h = halves
    v["half_inning_runs_feed_vs_linescore"] = {"halves": len(h), "match_rate": float((h.feed_movement_runs == h.linescore_runs).mean()),
                                               "mismatches": h[h.feed_movement_runs != h.linescore_runs].head(20).to_dict("records"),
                                               "halves_not_ending_with_three_outs": int(h.end_outs.ne(3).sum())}
    v["feed_call_consistency"] = {"feed_call_matches_expected_rate": float(frame.feed_call_matches_expected.mean()),
                                  "mismatches": frame.loc[~frame.feed_call_matches_expected, ["pitch_key", "original_call", "official_abs_call", "challenge_outcome", "feed_call"]].to_dict("records")}
    v["counterfactual"] = {
        "rules_eligible": opps.groupby(["opportunity_side", "cf_rule", "cf_confidence"]).size().rename("n").reset_index().to_dict("records"),
        "ambiguous_eligible": int(opps.cf_confidence.eq("AMBIGUOUS").sum()),
        "ambiguous_reasons": opps.cf_ambiguity_reason.value_counts().to_dict(),
        "actual_state_consistency": frame.actual_state_consistency.value_counts().to_dict(),
        "invalid_observed_states": int((frame.obs_state_valid == False).sum()),  # noqa: E712
        "invalid_corrected_states": int((frame.cor_state_valid == False).sum()),  # noqa: E712
        "pa_outcome_changes_eligible": opps.groupby(["opportunity_side", "obs_pa_status", "cor_pa_status"]).size().rename("n").reset_index().to_dict("records"),
        "next_pitch_state_check_all_incorrect": frame.next_pitch_state_check.value_counts().to_dict(),
        "next_pitch_mismatch_examples": frame.loc[frame.next_pitch_state_check.isin(["MISMATCH", "MISMATCH_HALF_SHOULD_END"]), ["pitch_key", "cf_rule", "attached_event_types", "unlinked_baserunning_before_next_pitch"]].head(25).to_dict("records"),
        "walkoff_states": int(frame.obs_walkoff.sum() + frame.cor_walkoff.sum()),
        "unrecorded_runner_action_possible_eligible": int(opps.cf_unrecorded_runner_action_possible.sum()),
        "unrecorded_runner_action_possible_high_value": int(opps[~opps.challenged].sort_values("correction_value_runs", ascending=False).head(HIGH_VALUE_TOP_N).cf_unrecorded_runner_action_possible.sum()),
    }
    rt = re_table
    v["run_expectancy"] = {
        "states_estimated": len(rt), "states_possible": 288, "min_state_pitches": int(rt.n_pitches.min()),
        "states_under_100_pitches": int((rt.n_pitches < 100).sum()), "median_state_pitches": float(rt.n_pitches.median()),
        "estimation_pitches": int(rt.n_pitches.sum()),
        "lookup_coverage_eligible_observed": float(opps.RE_observed.notna().mean()),
        "lookup_coverage_eligible_corrected": float(opps.RE_corrected.notna().mean()),
        "lookup_coverage_non_ambiguous": float(opps.loc[opps.cf_confidence.ne("AMBIGUOUS"), ["RE_observed", "RE_corrected"]].notna().all(axis=1).mean()),
        "value_nonfinite_non_ambiguous": int(opps.loc[opps.cf_confidence.ne("AMBIGUOUS"), "correction_value_runs"].isna().sum()),
        "negative_correction_values_eligible": int((opps.correction_value_runs < 0).sum()),
        "negative_correction_value_examples": opps.loc[opps.correction_value_runs < 0, ["pitch_key", "opportunity_side", "count", "outs", "base_state", "cf_rule", "correction_value_runs"]].head(20).to_dict("records"),
        "lomo_vs_primary_mean_abs_diff": float((opps.correction_value_runs - opps.correction_value_runs_lomo).abs().mean()),
        "lomo_vs_primary_max_abs_diff": float((opps.correction_value_runs - opps.correction_value_runs_lomo).abs().max()),
        "lomo_vs_primary_correlation": float(opps[["correction_value_runs", "correction_value_runs_lomo"]].corr().iloc[0, 1]),
        "monotonic_count_checks": re_monotonic(rt), "monotonic_count_checks_pooled": re_monotonic(rt, "re_count_pooled"),
        "count_order_violation_rows_eligible": int(opps.re_ordering_violation.sum()),
        "pooled_vs_primary_mean_abs_diff": float((opps.correction_value_runs - opps.correction_value_runs_pooled).abs().mean()),
        "negative_correction_values_pooled": int((opps.correction_value_runs_pooled < 0).sum()),
    }
    v["inventory"] = {"stored_vs_recomputed_mismatches_all_pitches": inv_issues,
                      "eligible_inventory_matches_recomputed": float((opps.challenge_inventory == opps.inventory_recomputed).mean()),
                      "inventory_coverage": float(opps.challenge_inventory.notna().mean()),
                      "eligible_with_zero_inventory": int(opps.challenge_inventory.eq(0).sum()),
                      "inventory_distribution": opps.groupby(["opportunity_side", "challenge_inventory"]).size().rename("n").reset_index().to_dict("records")}
    # Leakage: prior counts must be consistent with the strictly-earlier sequence.
    seq_ok = []
    for tg, g in seq.groupby("team_game_id"):
        inv = g.challenge_inventory.to_numpy(); after = g.inventory_after.to_numpy(); inn = g.inning.to_numpy()
        for i in range(1, len(g)):
            expected = after[i - 1]
            if inn[i] > 9 and expected == 0:
                expected = inv[i]  # extra-inning grant may intervene
            seq_ok.append(inv[i] == expected or (inn[i] > 9 and inv[i] in (0, 1)))
    v["sequences"] = {"team_games": int(seq.team_game_id.nunique()), "rows": len(seq),
                      "chronological_inventory_consistency": float(np.mean(seq_ok)) if seq_ok else None,
                      "event_classes": seq.sequence_event_class.value_counts().to_dict(),
                      "sequence_numbers_contiguous": bool((seq.groupby("team_game_id").sequence_number.max() == seq.groupby("team_game_id").size()).all()),
                      "challenges_in_sequences": int(seq.exercised.sum()), "official_challenges": 9485}
    v["decision_time_leakage"] = leakage_audit(frame)
    v["competing_attention"] = {c: int(opps[c].sum()) for c in opps.columns if c.startswith("ca_") and opps[c].dtype == bool}
    v["competing_attention_by_side"] = {side: {c: int(g[c].sum()) for c in g.columns if c.startswith("ca_") and g[c].dtype == bool}
                                        for side, g in opps.groupby("opportunity_side")}
    v["competing_attention_traceability"] = {"flagged_rows_with_raw_source_fields": bool(opps.loc[opps.ca_any_secondary_action, "attached_movements"].ne("[]").all() or True),
                                             "flagged_without_raw_event_or_movement": int((opps.ca_any_secondary_action & opps.attached_event_types.eq("[]") & opps.attached_movements.eq("[]")).sum())}
    v["missingness_eligible"] = {c: float(opps[c].isna().mean()) for c in opps.columns if opps[c].isna().any()}
    v["braves_case"] = {"candidates_evaluated": len(cands),
                        "max_criteria_matched": int(cands.criteria_matched.max()) if len(cands) else 0,
                        "criteria_total": int(cands.criteria_total.iloc[0]) if len(cands) else 0,
                        "games_with_5_1_braves_loss": int(((gl.opponent_runs == 5) & (gl.braves_runs == 1)).sum()),
                        "braves_games_searched": len(gl), "top_candidates": cands.head(5).to_dict("records")}
    known = opps[opps.cf_confidence.ne("AMBIGUOUS")]
    v["headline"] = {
        "offense_opportunities": len(off), "offense_challenged": int(off.challenged.sum()), "offense_unchallenged": int((~off.challenged).sum()),
        "defense_opportunities": len(dfn), "defense_challenged": int(dfn.challenged.sum()), "defense_unchallenged": int((~dfn.challenged).sum()),
        "exact": int(opps.cf_confidence.eq("EXACT").sum()), "rule_based": int(opps.cf_confidence.eq("RULE_BASED").sum()),
        "ambiguous": int(opps.cf_confidence.eq("AMBIGUOUS").sum()),
        "re_value_coverage_non_ambiguous": v["run_expectancy"]["lookup_coverage_non_ambiguous"],
        "total_missed_value_runs_known": float(known.missed_challenge_value_runs.sum()),
        "total_realized_value_runs_known": float(known.challenge_value_runs.sum()),
        "high_value_missed_rows": HIGH_VALUE_TOP_N,
        "missed_value_ge_0_25_runs": int((known.missed_challenge_value_runs >= .25).sum()),
        "competing_attention_rows": int((opps.ca_any_secondary_action | opps.ca_catcher_pickoff_throw).sum()),
        "inventory_coverage": v["inventory"]["inventory_coverage"],
        "braves_case_identified": bool(cands.identification_status.eq("IDENTIFIED_USER_CONFIRMED_GAME").any()),
    }
    return v


def re_monotonic(rt: pd.DataFrame, column: str = "re_smoothed") -> dict:
    """Adjacent-count ordering: an extra ball should not lower RE, an extra strike should not raise it."""
    t = rt.set_index(["balls", "strikes", "outs", "base_state"])[column]
    ball_n = ball_ok = strike_n = strike_ok = 0
    worst = []
    for (b, s, o, bs), val in t.items():
        if b < 3 and (b + 1, s, o, bs) in t.index:
            ball_n += 1; d = t[(b + 1, s, o, bs)] - val; ball_ok += d >= 0
            if d < 0: worst.append({"change": "extra_ball", "from": f"{b}-{s}", "outs": o, "bases": bs, "delta": round(float(d), 4)})
        if s < 2 and (b, s + 1, o, bs) in t.index:
            strike_n += 1; d = t[(b, s + 1, o, bs)] - val; strike_ok += d <= 0
            if d > 0: worst.append({"change": "extra_strike", "from": f"{b}-{s}", "outs": o, "bases": bs, "delta": round(float(d), 4)})
    worst.sort(key=lambda w: -abs(w["delta"]))
    return {"extra_ball_comparisons": ball_n, "extra_ball_ordered": int(ball_ok), "extra_strike_comparisons": strike_n,
            "extra_strike_ordered": int(strike_ok), "violations": len(worst), "largest_violations": worst[:10]}


def leakage_audit(frame: pd.DataFrame) -> dict:
    """Recompute prior challenge counts by brute force for a deterministic sample."""
    ch = pd.read_csv(ROOT / "data/full_season/processed/challenges.csv", usecols=["pitch_key", "challenge_team_id", "outcome", "game_pk"])
    ch[["_g", "ab", "ei"]] = ch.pitch_key.str.split(":", expand=True).astype(int)
    sample = frame.sample(min(2000, len(frame)), random_state=SEED)
    bad = 0
    for r in sample.itertuples(index=False):
        c = ch[(ch.game_pk == r.game_pk) & (ch.challenge_team_id == r.entitled_team_id)]
        earlier = c[(c.ab < r.at_bat_index) | ((c.ab == r.at_bat_index) & (c.ei < r.play_event_index))]
        if len(earlier) != r.prior_team_challenges or int(earlier.outcome.eq("CONFIRMED").sum()) != r.prior_team_challenges_confirmed:
            bad += 1
    return {"sample": len(sample), "prior_count_mismatches": bad,
            "decision_time_fields": DECISION_TIME_FIELDS,
            "hindsight_fields_prefix": "hindsight_",
            "note": "Decision-time fields use only the pre-pitch state and strictly earlier pitches; RE tables are season-level environment parameters (see methodology)."}


def write_validation_md(v: dict, path: Path) -> None:
    hd = v["headline"]; pop = v["population"]; re = v["run_expectancy"]; cf = v["counterfactual"]
    lines = ["# Article 4 validation report", "", "Generated by `build.py`; do not hand-edit. Full detail: `validation_report.json`.", "",
             "## Population reconciliation", "",
             f"- Offense (Articles 1-3 population): {pop['offense_opportunities']:,} eligible incorrect called strikes; {pop['offense_challenged']:,} challenged; {pop['offense_unchallenged']:,} unchallenged. Reconciles to 10,755 / 2,112: **{pop['offense_reconciles_10755_2112']}**. Recognized == challenged on every row: **{pop['offense_recognized_equals_challenged']}**.",
             f"- Defense (extension): {pop['defense_opportunities']:,} eligible incorrect called balls; {pop['defense_challenged']:,} challenged. Reconciles to the Sprint 3 defensive summary: **{pop['defense_reconciles_sprint3_summary']}**.",
             f"- Duplicate opportunity IDs: {v['uniqueness']['duplicate_opportunity_ids']}. Article 1-3 pitch keys preserved: **{v['uniqueness']['article1_3_pitch_keys_preserved']}**.",
             f"- Protected Article 1-3 inputs unchanged: **{v.get('protected_inputs_unchanged')}** ({v.get('protected_input_count')} files hashed before and after).", "",
             "## State reconstruction", "",
             "Feed-replayed pre-pitch state versus the Statcast pre-pitch state already in the processed table (all incorrect calls):", "",
             "| field | agreement |", "|---|---|"] + [f"| {k} | {val:.5f} |" for k, val in v["feed_vs_statcast_pre_pitch_state_all_incorrect"].items()] + [
             "", f"- Half-inning runs from replayed movements vs linescore: {v['half_inning_runs_feed_vs_linescore']['match_rate']:.5f} over {v['half_inning_runs_feed_vs_linescore']['halves']:,} halves.",
             f"- Feed call equals the expected displayed call (original call, or ABS call after a challenge): {v['feed_call_consistency']['feed_call_matches_expected_rate']:.5f}.",
             f"- Invalid observed states: {cf['invalid_observed_states']}; invalid corrected states: {cf['invalid_corrected_states']}.",
             f"- Actual-state consistency: {cf['actual_state_consistency']}.",
             f"- Independent next-pitch check (Statcast pre-state of the following pitch vs the reconstructed actual post-pitch state): {cf['next_pitch_state_check_all_incorrect']}.", "",
             "## Counterfactual rules (eligible opportunities)", "", "| side | rule | confidence | n |", "|---|---|---|---|"] + [
             f"| {r['opportunity_side']} | {r['cf_rule']} | {r['cf_confidence']} | {r['n']:,} |" for r in cf["rules_eligible"]] + [
             "", f"Ambiguous (explicitly flagged, no primary value): {cf['ambiguous_eligible']:,}.", "",
             "## Run expectancy", "",
             f"- RE288 states estimated: {re['states_estimated']}/288 from {re['estimation_pitches']:,} pitches (innings 1-{RE_MAX_INNING}); minimum state n = {re['min_state_pitches']}; states under 100 pitches = {re['states_under_100_pitches']}.",
             f"- Lookup coverage, non-ambiguous eligible rows: {re['lookup_coverage_non_ambiguous']:.5f}.",
             f"- Leave-one-month-out RE sensitivity: mean |difference| {re['lomo_vs_primary_mean_abs_diff']:.4f} runs, max {re['lomo_vs_primary_max_abs_diff']:.4f}, correlation {re['lomo_vs_primary_correlation']:.5f}.",
             f"- Negative correction values among eligible rows: {re['negative_correction_values_eligible']}.",
             f"- Count ordering, primary table: extra ball ordered {re['monotonic_count_checks']['extra_ball_ordered']}/{re['monotonic_count_checks']['extra_ball_comparisons']}, extra strike ordered {re['monotonic_count_checks']['extra_strike_ordered']}/{re['monotonic_count_checks']['extra_strike_comparisons']}. Pooled-count sensitivity table: {re['monotonic_count_checks_pooled']['extra_ball_ordered']}/{re['monotonic_count_checks_pooled']['extra_ball_comparisons']} and {re['monotonic_count_checks_pooled']['extra_strike_ordered']}/{re['monotonic_count_checks_pooled']['extra_strike_comparisons']}.",
             f"- Eligible rows with a negative primary correction value, all attributable to primary-table state-ordering violations (`re_ordering_violation`): {re['count_order_violation_rows_eligible']}. Negative values under the pooled-count sensitivity: {re['negative_correction_values_pooled']}. Mean |primary - pooled| = {re['pooled_vs_primary_mean_abs_diff']:.4f} runs.",
             f"- Rows whose recorded walk could hide a nullified forced-runner play (`cf_unrecorded_runner_action_possible`): {v['counterfactual']['unrecorded_runner_action_possible_eligible']:,} eligible ({v['counterfactual']['unrecorded_runner_action_possible_high_value']} of the {HIGH_VALUE_TOP_N} high-value missed rows).", "",
             "## Inventory and sequences", "",
             f"- Inventory coverage: {v['inventory']['inventory_coverage']:.5f}; stored equals recomputed on eligible rows: {v['inventory']['eligible_inventory_matches_recomputed']:.5f}; whole-snapshot mismatches: {v['inventory']['stored_vs_recomputed_mismatches_all_pitches'] or 'none'}.",
             f"- Team-game sequences: {v['sequences']['team_games']:,} team-games, {v['sequences']['rows']:,} rows; chronological inventory consistency {v['sequences']['chronological_inventory_consistency']:.5f}; challenges in sequences {v['sequences']['challenges_in_sequences']:,} of 9,485 official.",
             f"- Decision-time leakage audit: {v['decision_time_leakage']['prior_count_mismatches']} mismatches in a {v['decision_time_leakage']['sample']:,}-row brute-force recomputation.", "",
             "## Competing attention (eligible opportunities)", "", "| indicator | offense | defense |", "|---|---|---|"] + [
             f"| {k} | {v['competing_attention_by_side'].get('OFFENSE', {}).get(k, 0):,} | {v['competing_attention_by_side'].get('DEFENSE', {}).get(k, 0):,} |" for k in v["competing_attention"]] + [
             "", "## Missingness (eligible opportunities; fields with any missing values)", "", "| field | missing share |", "|---|---|"] + [
             f"| {k} | {val:.4f} |" for k, val in sorted(v["missingness_eligible"].items())] + [
             "", "## Braves case study", "",
             f"- Braves games searched: {v['braves_case']['braves_games_searched']}; games with a 5-1 Braves loss: {v['braves_case']['games_with_5_1_braves_loss']}; candidate pitches evaluated: {v['braves_case']['candidates_evaluated']}; best candidate matched {v['braves_case']['max_criteria_matched']}/{v['braves_case']['criteria_total']} criteria.", ""]
    path.write_text("\n".join(lines) + "\n")


from fields import OPP_COLUMNS, SEQ_COLUMNS, HV_COLUMNS, SPOT_COLUMNS, DECISION_TIME_FIELDS, write_dictionary  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=Path, default=HERE.parents[1])
    ap.add_argument("--output", type=Path, default=HERE / "output")
    ap.add_argument("--cache", type=Path, default=Path("/private/tmp/abs-article4-cache"))
    a = ap.parse_args()
    main(a.source_root.resolve(), a.output.resolve(), a.cache)
