"""Article 4 decision-value analysis: the economics of spending vs preserving an ABS challenge.

Reads the validated Article 4 dataset and processed Articles 1-3 tables
(read-only).  Every model used for a decision-time quantity is evaluated
chronologically and applied through leave-one-month-out cross-fitting, so no
observation receives a prediction from a model trained on its own game.
Hindsight quantities are labelled HINDSIGHT and never enter a model.
See METHODOLOGY.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import warnings
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/abs-article4-mpl")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import statsmodels
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
A4 = HERE.parent
ROOT = A4.parents[1]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(A4)); sys.path.insert(0, str(ROOT))
from dv_core import classify_spend, edge_class, flip_value, suffix_option_values, suffix_prophet  # noqa: E402

SEED = 20260925
PRIMARY, OLD = "correction_value_runs_pooled", "correction_value_runs"
TAUS = (0.0, 0.05, 0.10)
BOOT = 200
BLUE, ORANGE, AQUA, INK, INK2, GRID, SURF = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": .6,
                     "axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "axes.titlesize": 11,
                     "legend.frameon": False, "lines.linewidth": 2, "savefig.dpi": 200})
DMAX = 6.0  # inches; spline upper bound (distances clipped here)


# ============================================================ utilities
def digest(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as r:
        for b in iter(lambda: r.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jd(v):
    if isinstance(v, (np.integer,)): return int(v)
    if isinstance(v, (np.floating, float)): return None if not np.isfinite(v) else round(float(v), 6)
    if isinstance(v, (np.bool_,)): return bool(v)
    raise TypeError(type(v))


def wcsv(df, name):
    df.to_csv(OUT / name, index=False, float_format="%.6g", lineterminator="\n")


def savefig(fig, name):
    fig.tight_layout(); fig.savefig(FIG / name, facecolor=SURF); plt.close(fig)


def logit(p):
    p = np.clip(np.asarray(p, float), 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def metrics(y, p):
    y = np.asarray(y, int); p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    lp = logit(p)
    cal = sm.GLM(y, sm.add_constant(lp), family=sm.families.Binomial()).fit()
    icpt = sm.GLM(y, np.ones_like(lp), offset=lp, family=sm.families.Binomial()).fit()
    ece = 0.0
    for lo, hi in zip(np.linspace(0, 1, 11)[:-1], np.linspace(0, 1, 11)[1:]):
        m = (p >= lo) & ((p < hi) if hi < 1 else (p <= hi))
        if m.any(): ece += m.mean() * abs(y[m].mean() - p[m].mean())
    return {"n": len(y), "base_rate": y.mean(), "mean_pred": p.mean(), "roc_auc": roc_auc_score(y, p) if len(set(y)) > 1 else np.nan,
            "log_loss": log_loss(y, p, labels=[0, 1]), "brier": brier_score_loss(y, p),
            "calibration_intercept": icpt.params[0], "calibration_slope": cal.params[1], "ece_10bin": ece}


def deciles(y, p, label):
    q = pd.qcut(pd.Series(p).rank(method="first"), 10, labels=False)
    t = pd.DataFrame({"d": q, "p": p, "y": y}).groupby("d").agg(mean_pred=("p", "mean"), observed=("y", "mean"), n=("y", "size")).reset_index()
    t["model"] = label
    return t


def glm(df, formula, cluster=None):
    m = smf.glm(formula, data=df, family=sm.families.Binomial())
    if cluster is None:
        return m.fit()
    return m.fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(df[cluster])[0]})


def spline(col="absd"):
    return f"bs({col}, df=4, lower_bound=0, upper_bound={DMAX})"


# ============================================================ loading
def load():
    o = pd.read_csv(A4 / "output/article4_opportunities.csv", low_memory=False, dtype={"base_state": str})
    ai = pd.read_csv(A4 / "output/article4_all_incorrect_calls.csv", low_memory=False, dtype={"base_state": str})
    seq = pd.read_csv(A4 / "output/article4_team_game_sequences.csv", low_memory=False)
    re288 = pd.read_csv(A4 / "output/article4_re288_table.csv", dtype={"base_state": str})
    cols = ["pitch_key", "game_pk", "game_date", "at_bat_index", "play_event_index", "inning", "half_inning", "outs", "balls", "strikes",
            "on_1b", "on_2b", "on_3b", "home_score", "away_score", "home_team_id", "away_team_id", "original_call", "derived_abs_call",
            "distance_from_abs_boundary", "plate_x", "plate_z", "abs_zone_top", "abs_zone_bot", "bat_side", "pitch_hand", "pitch_type",
            "challenged", "challenge_outcome", "affected_team_challenges_remaining", "affected_team_id", "offense_challenges_remaining",
            "defense_challenges_remaining", "position_player_pitching", "source_game_feed", "survival_class"]
    p = pd.read_csv(ROOT / "data/full_season/processed/pitches.csv", usecols=cols, low_memory=False)
    ch = pd.read_csv(ROOT / "data/full_season/processed/challenges.csv")
    from src.offensive_recognition import PITCH_FAMILY
    for d in (o, ai):
        feats(d, PITCH_FAMILY, from_article4=True)
    feats(p, PITCH_FAMILY, from_article4=False)
    # Fixed category levels = levels with >= 50 eligible opportunities AND >= 50 official challenges;
    # anything else maps to the most common level.  Deterministic, and no training month can meet an unseen level.
    chal = p[p.pitch_key.isin(set(ch.pitch_key))]
    for col in ("pitch_family", "hand", "edge"):
        vo, vc = o[col].value_counts(), chal[col].value_counts()
        levels = sorted(l for l in vo.index if vo.get(l, 0) >= 50 and vc.get(l, 0) >= 50)
        mode = vo.idxmax()
        for f in (o, ai, p):
            f[col] = pd.Categorical(f[col].where(f[col].isin(levels), mode), categories=levels)
    return o, ai, seq, re288, p, ch


def feats(d, fam, from_article4):
    if from_article4:
        d["absd"] = d.abs_distance_inches.clip(upper=DMAX)
        d["side"] = d.opportunity_side
        d["challenged_i"] = d.challenged.astype(str).str.lower().eq("true").astype(int)
        d["inv"] = d.challenge_inventory
    else:
        d["absd"] = (d.distance_from_abs_boundary.abs() * 12).clip(upper=DMAX)
        d["side"] = np.where(d.original_call.eq("STRIKE"), "OFFENSE", np.where(d.original_call.eq("BALL"), "DEFENSE", None))
        d["challenged_i"] = d.challenged.astype(str).str.lower().eq("true").astype(int)
        d["inv"] = d.affected_team_challenges_remaining
        d["pitch_family"] = d.pitch_type.map(fam).fillna("OTHER")
    d["edge"] = edge_class(d.plate_x, d.plate_z, d.abs_zone_top, d.abs_zone_bot, d.bat_side)
    d["edge"] = d.edge.fillna("UNKNOWN")
    d["terminal"] = ((d.strikes == 2) | (d.balls == 3)).astype(int)
    d["month"] = d.game_date.astype(str).str[:7]
    d["ord"] = d.at_bat_index * 1000 + d.play_event_index
    d["hand"] = d.bat_side.fillna("U").astype(str) + d.pitch_hand.fillna("U").astype(str)


# ============================================================ cross-fitted models
def chrono_and_crossfit(train, formula, target, apply_frames, label):
    """Expanding-window chronological evaluation + leave-one-month-out predictions."""
    months = sorted(train.month.unique())
    chrono = []
    for m in months[1:]:
        tr, te = train[train.month < m], train[train.month == m]
        r = glm(tr, formula)
        chrono.append(pd.DataFrame({"month": m, "y": te[target].to_numpy(), "p": r.predict(te).to_numpy(), "side": te.side.to_numpy()}))
    chrono = pd.concat(chrono, ignore_index=True)
    preds = [pd.Series(np.nan, index=f.index) for f in apply_frames]
    for m in months:
        r = glm(train[train.month != m], formula)
        for f, s in zip(apply_frames, preds):
            idx = f.index[f.month == m]
            if len(idx):
                s.loc[idx] = r.predict(f.loc[idx]).to_numpy()
    full = glm(train, formula, cluster="game_pk")
    return chrono, preds, full


def select_spec(train, specs, target):
    """Pre-declared specs; choose the simplest within 0.001 chronological log loss of the best."""
    rows, chronos = [], {}
    for name, f in specs.items():
        c, _, _ = chrono_and_crossfit(train, f"{target} ~ " + f, target, [], name)
        m = metrics(c.y, c.p); m.update(spec=name, formula=f); rows.append(m); chronos[name] = c
    t = pd.DataFrame(rows)
    best = t.log_loss.min()
    chosen = next(n for n in specs if t.set_index("spec").loc[n, "log_loss"] <= best + 0.001)
    t["selected"] = t.spec.eq(chosen)
    return t, chosen


# ============================================================ option values
def build_streams(ai, p_col, v_col, q_col):
    """Future-opportunity streams: every incorrect call against a team that could be challenged
    if inventory allowed (eligible or exhausted; position-player pitching excluded)."""
    s = ai[ai.eligibility_status.isin(["ELIGIBLE", "INELIGIBLE_EXHAUSTED"]) & ai[v_col].notna() & ai[p_col].notna()].copy()
    s = s.sort_values(["game_pk", "entitled_team_id", "ord"])
    streams = {}
    for (g, t), x in s.groupby(["game_pk", "entitled_team_id"], sort=False):
        pv, vv, qv = x[p_col].to_numpy(), x[v_col].to_numpy(), x[q_col].to_numpy()
        ev = pv * vv
        pol = {}
        for tau in TAUS:
            pol[f"tau_{tau:.2f}"] = suffix_option_values(pv, vv, (ev >= tau).astype(float), 2)
        pol["league_behavior"] = suffix_option_values(pv, vv, qv, 2)
        t1, t2 = suffix_prophet(ev)
        vmax = np.maximum.accumulate(vv[::-1])[::-1] if len(vv) else vv
        streams[(g, t)] = {"ord": x.ord.to_numpy(), "pol": pol, "top1": t1, "top2": t2, "ev": ev, "v": vv,
                           "vmax": np.append(vmax, 0.0)}
    return streams


def state_starts(p):
    q = p.sort_values(["game_pk", "ord"])
    q["inn"] = q.inning.clip(upper=10)
    first = q.groupby(["game_pk", "inning", "half_inning", "outs"], sort=False).agg(ord=("ord", "first"), home_score=("home_score", "first"),
                                                                                away_score=("away_score", "first"), month=("month", "first")).reset_index()
    first = first[first.inning <= 10]
    teams = p.drop_duplicates("game_pk").set_index("game_pk")[["home_team_id", "away_team_id"]]
    return first, teams


def future_table(p, streams, first, teams):
    """One row per (team-game, state reached): realized future quantities from that state's start.
    These are per-game outcomes; decision rows only ever see their leave-month-out averages."""
    rows = []
    for r in first.itertuples(index=False):
        home, away = teams.loc[r.game_pk]
        for role, team in (("HOME", home), ("AWAY", away)):
            st = streams.get((r.game_pk, team))
            diff = (r.home_score - r.away_score) * (1 if role == "HOME" else -1)
            rec = {"game_pk": r.game_pk, "team_id": team, "role": role, "month": r.month, "inning": r.inning, "half": r.half_inning,
                   "outs": r.outs, "score_bucket": "LEAD" if diff > 0 else ("TRAIL" if diff < 0 else "TIE")}
            if st is None:
                i, n = 0, 0
            else:
                i = int(np.searchsorted(st["ord"], r.ord, side="left")); n = len(st["ord"])
            rec["n_future"] = n - i
            if st is None or i >= n:
                rec.update(max_v=0.0, max_ev=0.0, sum_ev=0.0, any_v_ge_025=0, any_v_ge_050=0, top2_ev=0.0,
                           **{f"OV1_{k}": 0.0 for k in list(f"tau_{t:.2f}" for t in TAUS) + ["league_behavior"]},
                           **{f"OV2_{k}": 0.0 for k in list(f"tau_{t:.2f}" for t in TAUS) + ["league_behavior"]})
            else:
                v, ev = st["v"][i:], st["ev"][i:]
                rec.update(max_v=v.max(), max_ev=ev.max(), sum_ev=ev.sum(), any_v_ge_025=int((v >= .25).any()), any_v_ge_050=int((v >= .5).any()),
                           top2_ev=st["top2"][i])
                for k, V in st["pol"].items():
                    rec[f"OV1_{k}"] = V[1, i]; rec[f"OV2_{k}"] = V[2, i]
            rows.append(rec)
    f = pd.DataFrame(rows)
    f["prophet1"] = f.max_ev; f["prophet2"] = f.top2_ev
    for k in [f"tau_{t:.2f}" for t in TAUS] + ["league_behavior"]:
        f[f"M2_{k}"] = f[f"OV2_{k}"] - f[f"OV1_{k}"]
    f["M2_prophet"] = f.prophet2 - f.prophet1
    f["any_future"] = (f.n_future > 0).astype(int)
    return f


POLICIES = [f"tau_{t:.2f}" for t in TAUS] + ["league_behavior"]
STATE_KEYS = ["inning", "half", "outs", "role"]
FUT_COLS = ["n_future", "any_future", "max_v", "max_ev", "sum_ev", "any_v_ge_025", "any_v_ge_050"] + \
           [f"OV1_{k}" for k in POLICIES] + [f"M2_{k}" for k in POLICIES] + ["prophet1", "M2_prophet"]


def state_estimates(f, keys=STATE_KEYS):
    """Full-sample state means with game-cluster bootstrap CIs, plus leave-one-month-out means."""
    rng = np.random.default_rng(SEED)
    rows = []
    for k, g in f.groupby(keys):
        rec = dict(zip(keys, k)); rec["n_team_games"] = len(g)
        X = g[FUT_COLS].to_numpy()
        idx = rng.integers(0, len(g), size=(BOOT, len(g)))
        boots = X[idx].mean(axis=1)
        for j, c in enumerate(FUT_COLS):
            rec[c] = X[:, j].mean(); rec[c + "_lo"] = np.percentile(boots[:, j], 2.5); rec[c + "_hi"] = np.percentile(boots[:, j], 97.5)
        rows.append(rec)
    full = pd.DataFrame(rows)
    sums = f.groupby(keys + ["month"])[FUT_COLS].sum(); cnt = f.groupby(keys + ["month"]).size()
    tot = f.groupby(keys)[FUT_COLS].sum(); tcnt = f.groupby(keys).size()
    lm = []
    for idx, n in cnt.items():
        key, m = idx[:-1], idx[-1]
        denom = tcnt.loc[key] - n
        if denom <= 0:
            continue
        vals = (tot.loc[key] - sums.loc[idx]) / denom
        lm.append({**dict(zip(keys, key)), "month": m, "n_other": int(denom), **vals.to_dict()})
    return full, pd.DataFrame(lm)


def attach_costs(d, fut_full, fut_lomo, keys=STATE_KEYS):
    """Preservation cost of a failed challenge now = P(fail) x marginal option value of the challenge lost."""
    d = d.copy()
    d["inning_s"] = d.inning.clip(upper=10); d["half"] = d.half_inning
    d["role"] = np.where(d.entitled_team_id.eq(d.home_team_id), "HOME", "AWAY")
    look = pd.DataFrame({k: (d.inning_s if k == "inning" else d[k]) for k in keys}, index=d.index)
    look["month"] = d.month
    look = look.reset_index()
    lm = look.merge(fut_lomo, on=keys + ["month"], how="left").set_index("index")
    fb = look.merge(fut_full, on=keys, how="left").set_index("index")
    inv = d.inv.to_numpy()
    for k in POLICIES + ["prophet"]:
        ov1 = lm[f"OV1_{k}" if k != "prophet" else "prophet1"]; m2 = lm[f"M2_{k}"]
        marg = np.where(inv == 1, ov1, m2)
        d[f"marg_{k}"] = marg
        d[f"cost_{k}"] = (1 - d.p_success) * marg
        lo1, hi1 = fb[(f"OV1_{k}" if k != "prophet" else "prophet1") + "_lo"], fb[(f"OV1_{k}" if k != "prophet" else "prophet1") + "_hi"]
        lo2, hi2 = fb[f"M2_{k}_lo"], fb[f"M2_{k}_hi"]
        c = np.where(inv == 1, ov1, m2); cf = np.where(inv == 1, fb[f"OV1_{k}" if k != "prophet" else "prophet1"], fb[f"M2_{k}"])
        # CI half-widths from the full-sample bootstrap applied around the leave-month-out point estimate
        d[f"cost_{k}_lo"] = (1 - d.p_success) * np.maximum(0, c - (cf - np.where(inv == 1, lo1, lo2)))
        d[f"cost_{k}_hi"] = (1 - d.p_success) * (c + (np.where(inv == 1, hi1, hi2) - cf))
    d["cost_low"] = d[[f"cost_{k}_lo" for k in POLICIES]].min(axis=1)
    d["cost_high"] = d[[f"cost_{k}_hi" for k in POLICIES + ["prophet"]]].max(axis=1)
    d["cost"] = d["cost_league_behavior"]
    d["net"] = d.ev - d.cost
    d["decision_class"] = classify_spend(d.ev, d.cost_low, d.cost_high)
    d["extras"] = d.inning.gt(9)
    return d


# ============================================================ scarcity models
CTRL = "C(side) + C(inning_bucket) + C(score_state) + late_close_i"


def prep_behavior(d):
    d = d.copy()
    d["score_state"] = np.select([d.entitled_team_score_diff > 0, d.entitled_team_score_diff < 0], ["AHEAD", "BEHIND"], "TIED")
    d["late_close_i"] = d.late_close.astype(str).str.lower().eq("true").astype(int)
    d["inv1"] = (d.inv == 1).astype(int)
    d["lprop"] = logit(d.propensity)
    d["ev4"] = d.ev / .25; d["net4"] = d.net / .25; d["cost4"] = d.cost / .25; d["v4"] = d.v / .25
    return d


def or_row(r, term, model, extra=None):
    ci = r.conf_int().loc[term]
    return {"model": model, "term": term, "odds_ratio": np.exp(r.params[term]), "ci_low": np.exp(ci[0]), "ci_high": np.exp(ci[1]),
            "p_value": r.pvalues[term], "n": int(r.nobs), **(extra or {})}


def scarcity_suite(d, label, team=False):
    d = prep_behavior(d)
    specs = {
        "M0_exploratory_modelA": f"challenged_i ~ inv1 + v4 + {spline('dist')} + terminal + {CTRL}",
        "M1_gross_ev": f"challenged_i ~ inv1 + {spline('ev_c')} + lprop + {CTRL}",
        "M2_ev_plus_cost": f"challenged_i ~ inv1 + {spline('ev_c')} + cost4 + lprop + {CTRL}",
        "M3_net_value": f"challenged_i ~ inv1 + {spline('net_c')} + lprop + {CTRL}",
        "M3i_net_x_inv": f"challenged_i ~ inv1 * net4 + lprop + {CTRL}",
        "M1i_ev_x_inv": f"challenged_i ~ inv1 * ev4 + lprop + {CTRL}",
    }
    if team:
        specs["M4_net_team_fe"] = specs["M3_net_value"] + " + C(entitled_team)"
    d["dist"] = d.absd
    d["ev_c"] = d.ev.clip(0, DMAX); d["net_c"] = (d.net.clip(-1, 2) + 1)  # shift into spline support [0, DMAX]
    rows, fits = [], {}
    for name, f in specs.items():
        cols = [c for c in ["challenged_i", "inv1", "v4", "dist", "terminal", "ev_c", "lprop", "cost4", "net_c", "net4", "ev4", "side",
                            "inning_bucket", "score_state", "late_close_i", "entitled_team", "game_pk"] if c in d.columns]
        dd = d.dropna(subset=[c for c in cols if c != "entitled_team"])
        if "cost4" in f and dd.cost4.std() == 0:
            rows.append({"model": name, "term": "inv1", "variant": label, "note": "NOT_ESTIMABLE: preservation cost is constant (zero) in this variant"})
            continue
        r = glm(dd, f, cluster="game_pk"); fits[name] = (r, dd)
        rows.append(or_row(r, "inv1", name, {"variant": label}))
        for t in ("inv1:net4", "inv1:ev4", "lprop", "cost4", "net4", "ev4"):
            if t in r.params.index:
                rows.append(or_row(r, t, name, {"variant": label}))
    return pd.DataFrame(rows), fits


# ============================================================ main
def main(out: Path):
    global OUT, FIG, SEQ, CH
    OUT, FIG = out, out / "figures"; FIG.mkdir(parents=True, exist_ok=True)
    from build import protected_files
    protected = protected_files(ROOT) + sorted((A4 / "output").glob("*.csv")) + [A4 / "output/manifest.json"] + \
        sorted((A4 / "exploratory/output").glob("*.csv")) + sorted((A4 / "exploratory/output").glob("*.json"))
    before = {str(x.relative_to(ROOT)): digest(x) for x in protected}
    manifest = json.loads((A4 / "output/manifest.json").read_text())
    hashes_ok = all(digest(A4 / "output" / f) == v["sha256"] for f, v in manifest["outputs"].items())
    o, ai, seq, re288, p, ch = load()
    SEQ, CH = seq, ch
    rec = {"eligible": len(o), "offense": int(o.side.eq("OFFENSE").sum()), "defense": int(o.side.eq("DEFENSE").sum()),
           "challenged": int(o.challenged_i.sum()), "all_incorrect": len(ai), "official_challenges": len(ch),
           "article4_hashes_match_manifest": hashes_ok}
    assert rec["offense"] == 10755 and rec["defense"] == 9409 and rec["challenged"] == 5098 and len(ch) == 9485 and hashes_ok, rec
    S = {"reconciliation": rec}

    # ---------------------------------------------------- A1 resource-independent challenge propensity
    prop_specs = {
        "P1_distance_side": f"{spline()} + C(side)",
        "P2_plus_edge": f"{spline()} + C(side) + C(edge)",
        "P3_plus_edge_pitch_hand": f"{spline()} + C(side) + C(edge) + C(pitch_family) + C(hand)",
        "P4_plus_edge_count_situation": f"{spline()} + C(side) + C(edge) + terminal + C(balls) + C(strikes) + C(outs) + C(inning_bucket)",
    }
    ptab, pchosen = select_spec(o, prop_specs, "challenged_i")
    # Primary = evidence-only (P1-P3 family): count/situation are kept out so value enters separately downstream.
    evidence_only = {k: v for k, v in prop_specs.items() if not k.startswith("P4")}
    _, pchosen_ev = select_spec(o, evidence_only, "challenged_i")
    ptab["primary_evidence_only_selected"] = ptab.spec.eq(pchosen_ev)
    chrono_p, (o["propensity"], ai["propensity"]), rfull_p = chrono_and_crossfit(o, "challenged_i ~ " + prop_specs[pchosen_ev], "challenged_i", [o, ai], pchosen_ev)
    pm = metrics(chrono_p.y, chrono_p.p)
    # Comparison with Article 3's held-out model C on the same offense rows (April onward)
    off = o[o.side.eq("OFFENSE") & o.expected_recognition_prob_temporal.notna()]
    cmp_rows = []
    chrono_off = []
    months = sorted(o.month.unique())
    for m in months[1:]:
        tr, te = o[o.month < m], o[(o.month == m) & o.side.eq("OFFENSE") & o.expected_recognition_prob_temporal.notna()]
        r = glm(tr, "challenged_i ~ " + prop_specs[pchosen_ev])
        chrono_off.append(pd.DataFrame({"y": te.challenged_i, "p_new": r.predict(te), "p_a3": te.expected_recognition_prob_temporal}))
    co = pd.concat(chrono_off)
    cmp_rows.append({"model": f"new_{pchosen_ev}_resource_independent", **metrics(co.y, co.p_new)})
    cmp_rows.append({"model": "article3_C_SITUATION_temporal (includes inventory)", **metrics(co.y, co.p_a3)})
    coef_p = pd.DataFrame({"term": rfull_p.params.index, "odds_ratio": np.exp(rfull_p.params), "ci_low": np.exp(rfull_p.conf_int()[0]),
                           "ci_high": np.exp(rfull_p.conf_int()[1]), "p_value": rfull_p.pvalues})
    dec_p = deciles(chrono_p.y.to_numpy(), chrono_p.p.to_numpy(), "propensity_chronological")
    by_side_p = pd.DataFrame([{"side": s, **metrics(g.y, g.p)} for s, g in chrono_p.groupby("side")])
    by_month_p = pd.DataFrame([{"month": m, **metrics(g.y, g.p)} for m, g in chrono_p.groupby("month")])
    miss = {c: float(o[c].isna().mean()) for c in ["absd", "edge", "pitch_family", "hand", "side"]}
    miss["edge_unknown_share"] = float(o.edge.eq("UNKNOWN").mean())
    wcsv(pd.concat([ptab.assign(section="spec_selection_chronological"), pd.DataFrame(cmp_rows).assign(section="comparison_article3_offense_april_on"),
                    coef_p.assign(section="coefficients_full_fit_game_clustered"), dec_p.assign(section="calibration_deciles_chronological"),
                    by_side_p.assign(section="by_side_chronological"), by_month_p.assign(section="by_month_chronological")], ignore_index=True),
         "article4_resource_independent_recognizability.csv")
    S["propensity"] = {"selected_evidence_only": pchosen_ev, "selected_any": pchosen, "chronological": pm, "comparison": cmp_rows,
                       "missingness": miss, "by_side": by_side_p.to_dict("records")}

    # ---------------------------------------------------- A2 challenge success model
    c = ch.merge(p.drop(columns=["challenge_outcome"]), on="pitch_key", how="left", suffixes=("", "_p"))
    c["success"] = c.outcome.eq("OVERTURNED").astype(int)
    c["side"] = np.where(c.challenger_role.eq("BATTER"), "OFFENSE", "DEFENSE")
    c["inning_bucket"] = pd.cut(c.inning, [0, 3, 6, 9, np.inf], labels=["1-3", "4-6", "7-9", "10+"]).astype(str)
    succ_specs = {
        "S0_coarse_side_count": "C(side) + terminal",
        "S1_distance_side": f"{spline()} * C(side)",
        "S2_plus_edge_terminal": f"{spline()} * C(side) + C(edge) + terminal",
        "S3_plus_pitch_hand": f"{spline()} * C(side) + C(edge) + terminal + C(pitch_family) + C(hand)",
    }
    stab, schosen = select_spec(c, {k: v for k, v in succ_specs.items() if k != "S0_coarse_side_count"}, "success")
    s0tab, _ = select_spec(c, {"S0_coarse_side_count": succ_specs["S0_coarse_side_count"]}, "success")
    stab = pd.concat([s0tab.assign(selected=False), stab], ignore_index=True)
    near = p[p.original_call.isin(["BALL", "STRIKE"]) & (p.distance_from_abs_boundary.abs() * 12 <= 3) & p.inv.gt(0) &
             ~p.position_player_pitching.astype(str).str.lower().eq("true")].copy()
    near["inning_bucket"] = pd.cut(near.inning, [0, 3, 6, 9, np.inf], labels=["1-3", "4-6", "7-9", "10+"]).astype(str)
    chrono_s, (o["p_success"], ai["p_success"], c["p_success_cf"], near["p_success"]), rfull_s = chrono_and_crossfit(
        c, "success ~ " + succ_specs[schosen], "success", [o, ai, c, near], schosen)
    _, (o["p_success_coarse"], ai["p_success_coarse"]), _ = chrono_and_crossfit(c, "success ~ " + succ_specs["S0_coarse_side_count"], "success", [o, ai], "S0")
    # Public-information benchmark: P(call is actually incorrect | same observables) among ALL called pitches
    # within 6 inches of the boundary, challenged or not.  This is what an uninformed challenger could expect.
    pub = p[p.original_call.isin(["BALL", "STRIKE"]) & (p.distance_from_abs_boundary.abs() * 12 <= DMAX) & p.derived_abs_call.notna()].copy()
    pub["incorrect"] = (pub.original_call != pub.derived_abs_call).astype(int)
    chrono_pub, (o["p_success_public"], ai["p_success_public"]), _ = chrono_and_crossfit(pub, "incorrect ~ " + succ_specs[schosen], "incorrect", [o, ai], "public")
    pub_m = metrics(chrono_pub.y, chrono_pub.p)
    pub_curve = pub.assign(db=pd.cut(pub.absd, [0, .5, 1, 1.5, 2, 3, 4, DMAX + .01], include_lowest=True)).groupby(["side", "db"], observed=True).agg(
        n=("incorrect", "size"), observed=("incorrect", "mean")).reset_index().assign(db=lambda x: x.db.astype(str))
    # chronological-only predictions (strictly earlier months) for sensitivity
    o["p_success_chrono"] = np.nan; ai["p_success_chrono"] = np.nan
    for m in sorted(c.month.unique())[1:]:
        r = glm(c[c.month < m], "success ~ " + succ_specs[schosen])
        for f in (o, ai):
            idx = f.index[f.month == m]
            f.loc[idx, "p_success_chrono"] = r.predict(f.loc[idx]).to_numpy()
    sm_all = metrics(chrono_s.y, chrono_s.p)
    s_side = pd.DataFrame([{"side": s, **metrics(g.y, g.p)} for s, g in chrono_s.groupby("side")])
    s_month = pd.DataFrame([{"month": m, **metrics(g.y, g.p)} for m, g in chrono_s.groupby("month")])
    s_dec = deciles(chrono_s.y.to_numpy(), chrono_s.p.to_numpy(), "success_chronological")
    s_bucket = chrono_s.assign(b=pd.cut(chrono_s.p, [0, .2, .4, .5, .6, .7, .8, .9, 1.0])).groupby("b", observed=True).agg(
        mean_pred=("p", "mean"), observed=("y", "mean"), n=("y", "size")).reset_index().assign(b=lambda x: x.b.astype(str))
    coef_s = pd.DataFrame({"term": rfull_s.params.index, "odds_ratio": np.exp(rfull_s.params), "ci_low": np.exp(rfull_s.conf_int()[0]),
                           "ci_high": np.exp(rfull_s.conf_int()[1]), "p_value": rfull_s.pvalues})
    by_dist = c.assign(db=pd.cut(c.absd, [0, .5, 1, 1.5, 2, 3, 4, DMAX + .01], include_lowest=True)).groupby(["side", "db"], observed=True).agg(
        n=("success", "size"), observed=("success", "mean"), cross_fitted_pred=("p_success_cf", "mean")).reset_index().assign(db=lambda x: x.db.astype(str))
    wcsv(pd.concat([stab.assign(section="spec_selection_chronological"), coef_s.assign(section="coefficients_full_fit_game_clustered"),
                    s_dec.assign(section="calibration_deciles_chronological"), s_bucket.assign(section="calibration_by_probability_bucket"),
                    s_side.assign(section="by_side_chronological"), s_month.assign(section="by_month_chronological"),
                    by_dist.assign(section="success_by_unsigned_distance"),
                    pd.DataFrame([{"spec": "PUBLIC_INFORMATION_incorrect_call_rate_all_called_pitches", **pub_m}]).assign(section="public_information_benchmark_chronological"),
                    pub_curve.assign(section="public_information_incorrect_rate_by_unsigned_distance")], ignore_index=True), "article4_challenge_success_model.csv")
    S["success_model"] = {"selected": schosen, "n": len(c), "base_success_rate": float(c.success.mean()), "chronological": sm_all,
                          "by_side": s_side.to_dict("records"), "by_month": s_month.to_dict("records"),
                          "eligible_opportunity_mean_p": float(o.p_success.mean()),
                          "public_information_benchmark": {"n": len(pub), "incorrect_rate": float(pub.incorrect.mean()), "chronological": pub_m,
                                                           "eligible_opportunity_mean_p": float(o.p_success_public.mean())}}

    # ---------------------------------------------------- A3 gross immediate expected value
    o["v"] = o[PRIMARY]; ai["v"] = ai[PRIMARY]
    o["ev"] = o.p_success * o.v; ai["ev"] = ai.p_success * ai.v
    d = o[o.v.notna()].copy()
    d["ev_bucket"] = pd.cut(d.ev, [-1, .05, .10, .20, .35, 10], labels=["<0.05", "0.05-0.10", "0.10-0.20", "0.20-0.35", ">=0.35"]).astype(str)
    d["prop_q"] = pd.qcut(d.propensity.rank(method="first"), 5, labels=[f"PQ{i}" for i in range(1, 6)]).astype(str)
    ev_rows = []
    for grp, x in [("ALL", d), ("CHALLENGED", d[d.challenged_i == 1]), ("UNCHALLENGED", d[d.challenged_i == 0]),
                   ("OFFENSE", d[d.side == "OFFENSE"]), ("DEFENSE", d[d.side == "DEFENSE"])]:
        e = x.ev
        ev_rows.append({"table": "distribution", "group": grp, "n": len(e), "total_ev_runs": e.sum(), "mean": e.mean(), "median": e.median(), "sd": e.std(),
                        **{f"p{q}": e.quantile(q / 100) for q in (10, 25, 75, 90, 95, 99)}, "max": e.max(),
                        "mean_p_success": x.p_success.mean(), "total_correction_value": x.v.sum()})
    for key in ("inv", "inning_bucket", "side", "ev_bucket", "prop_q"):
        for k, x in d.groupby(key):
            ev_rows.append({"table": f"behavior_by_{key}", "group": str(k), "n": len(x), "challenge_rate": x.challenged_i.mean(),
                            "mean": x.ev.mean(), "mean_p_success": x.p_success.mean(), "mean_value": x.v.mean()})
    for (k1, k2), x in d.groupby(["ev_bucket", "inv"]):
        ev_rows.append({"table": "behavior_by_ev_bucket_x_inv", "group": f"{k1}|inv={k2}", "n": len(x), "challenge_rate": x.challenged_i.mean(), "mean": x.ev.mean()})
    for (k1, k2, k3), x in d.groupby(["side", "ev_bucket", "inv"]):
        ev_rows.append({"table": "behavior_by_side_ev_bucket_x_inv", "group": f"{k1}|{k2}|inv={k3}", "n": len(x), "challenge_rate": x.challenged_i.mean(), "mean": x.ev.mean()})
    S["immediate_ev"] = [r for r in ev_rows if r["table"] == "distribution"]

    # ---------------------------------------------------- A4/A5 future opportunity & option value
    for f in (o, ai):
        f["q_use"] = f.propensity
    first, teams = state_starts(p)
    streams = build_streams(ai, "p_success", "v", "q_use")
    fut = future_table(p, streams, first, teams)
    fut_full, fut_lomo = state_estimates(fut)
    wcsv(fut_full.assign(section="state_means_full_sample_with_bootstrap_ci"), "article4_future_opportunity_value.csv")
    opt = fut_full[fut_full.outs.eq(0)][["inning", "half", "role", "n_team_games"] +
                                         [c_ for c_ in fut_full.columns if c_.startswith(("OV1_", "M2_", "prophet1"))]].copy()
    wcsv(opt, "article4_inventory_option_value.csv")
    S["option_value_top_of_half_outs0"] = opt.to_dict("records")

    # ---------------------------------------------------- A6 spend vs preserve
    d = attach_costs(d, fut_full, fut_lomo)
    d = add_failure_context(d, seq, ch)
    sp_rows = []
    reg = d[~d.extras]
    for key in (["decision_class"], ["decision_class", "inv"], ["decision_class", "side"], ["decision_class", "side", "inv"]):
        for k, x in reg.groupby(key):
            k = k if isinstance(k, tuple) else (k,)
            sp_rows.append({"table": "+".join(key), **dict(zip(key, map(str, k))), "n": len(x), "challenge_rate": x.challenged_i.mean(),
                            "passed": int((x.challenged_i == 0).sum()), "mean_ev": x.ev.mean(), "mean_cost": x.cost.mean(),
                            "mean_net": x.net.mean(), "mean_p_success": x.p_success.mean(), "mean_value": x.v.mean()})
    d["net_bin"] = pd.cut(d.net, [-2, -.05, 0, .05, .10, .20, .35, 5]).astype(str)
    for (k1, k2), x in reg.assign(net_bin=d.net_bin).groupby(["net_bin", "inv"]):
        sp_rows.append({"table": "net_bin+inv", "net_bin": k1, "inv": str(k2), "n": len(x), "challenge_rate": x.challenged_i.mean(), "mean_net": x.net.mean()})
    suite, fits = scarcity_suite(reg, "PRIMARY", team=True)
    marg = []
    r3, dd3 = fits["M3_net_value"]
    for nv in (-0.05, 0.0, 0.05, 0.10, 0.20, 0.35):
        x = dd3.copy(); x["net_c"] = nv + 1
        p1 = r3.predict(x.assign(inv1=1)).mean(); p2 = r3.predict(x.assign(inv1=0)).mean()
        marg.append({"table": "M3_marginal_by_net_value", "net_value": nv, "pred_rate_inv2": p2, "pred_rate_inv1": p1, "difference": p1 - p2, "ratio": p1 / p2})
    wcsv(pd.concat([pd.DataFrame(sp_rows), suite.assign(table="scarcity_models"), pd.DataFrame(marg)], ignore_index=True), "article4_spend_preserve.csv")
    row_cols = ["pitch_key", "game_pk", "game_date", "side", "entitled_team", "inning", "half_inning", "outs", "count", "base_state", "inv",
                "challenged_i", "challenge_outcome", "absd", "edge", "v", "propensity", "p_success", "ev"] + \
               [f"cost_{k}" for k in POLICIES + ["prophet"]] + ["cost", "cost_low", "cost_high", "net", "decision_class", "extras",
                                                                 "inv_state", "pas_since_failure", "failure_same_side", "failure_same_player",
                                                                 "cf_confidence", "cf_unrecorded_runner_action_possible"]
    wcsv(d[row_cols].rename(columns={"v": "correction_value_runs_pooled"}), "article4_immediate_expected_value.csv")
    S["spend_preserve"] = {"class_rates": [r for r in sp_rows if r["table"] in ("decision_class", "decision_class+inv")],
                           "scarcity_models": suite.to_dict("records"), "marginal": marg,
                           "passed_immediate_exceeds_share_of_passes": float((reg.decision_class.eq("IMMEDIATE_EXCEEDS_PRESERVATION") & reg.challenged_i.eq(0)).sum() / reg.challenged_i.eq(0).sum())}

    # ---------------------------------------------------- A7 post-failure
    pf_rows, pf_fits = post_failure(d)
    wcsv(pf_rows, "article4_post_failure.csv")
    S["post_failure"] = pf_rows.to_dict("records")

    # ---------------------------------------------------- A8 expiration (HINDSIGHT)
    exp_rows, exp_sum, tg = expiration(p, d, ai, seq)
    wcsv(exp_rows, "article4_expiration.csv")
    S["expiration"] = exp_sum

    # ---------------------------------------------------- A9 high-value early cohort
    hv, hv_sum = high_value_early(d, seq, tg)
    wcsv(hv, "article4_high_value_early.csv")
    S["high_value_early"] = hv_sum

    # ---------------------------------------------------- A10 Braves
    br = braves(d, re288, fut_lomo, fut_full)
    (OUT / "article4_braves_decision_value.json").write_text(json.dumps(br, indent=2, default=jd, sort_keys=True) + "\n")
    S["braves"] = br

    # ---------------------------------------------------- A11 sensitivity / falsification
    sens = sensitivity(o, ai, d, p, first, teams, fut, re288, near)
    wcsv(sens, "article4_decision_value_sensitivity.csv")
    S["sensitivity"] = sens.to_dict("records")

    figures(c, chrono_s, d, fut_full, sens, pf_rows, exp_rows, hv, br, suite)
    after = {str(x.relative_to(ROOT)): digest(x) for x in protected}
    S["validation"] = {"protected_unchanged": before == after, "protected_files": len(before),
                       "python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__,
                       "statsmodels": statsmodels.__version__, "scipy": scipy.__version__, "seed": SEED, "bootstrap_reps": BOOT,
                       "code_sha256": {f: digest(HERE / f) for f in ("analyze.py", "dv_core.py")},
                       "leakage": leakage_checks(o, c, fut, d),
                       "input_sha256": {k: v for k, v in before.items() if k.startswith("research/article4/output") or k.startswith("data/full_season/processed")}}
    (OUT / "article4_decision_value_summary.json").write_text(json.dumps(S, indent=1, default=jd, sort_keys=True) + "\n")
    write_validation(S, OUT.parent / "VALIDATION.md")
    if before != after:
        raise RuntimeError("STOP: protected inputs changed")
    print(json.dumps({k: S[k] for k in ("reconciliation",)}, default=jd))


# ============================================================ A7 helpers
def add_failure_context(d, seq, ch):
    """Decision-time context of the most recent failed challenge by the entitled team (strictly earlier)."""
    s = seq[seq.exercised & seq.challenge_outcome.eq("CONFIRMED")][["game_pk", "entitled_team_id", "pitch_key", "at_bat_index", "play_event_index", "opportunity_side", "inning"]]
    s = s.merge(ch[["pitch_key", "challenger_id"]], on="pitch_key", how="left")
    s["ord"] = s.at_bat_index * 1000 + s.play_event_index
    succ = seq[seq.exercised & seq.challenge_outcome.eq("OVERTURNED")][["game_pk", "entitled_team_id", "at_bat_index", "play_event_index"]].copy()
    succ["ord"] = succ.at_bat_index * 1000 + succ.play_event_index
    fail_by = {k: g.sort_values("ord") for k, g in s.groupby(["game_pk", "entitled_team_id"])}
    succ_by = {k: g.ord.to_numpy() for k, g in succ.groupby(["game_pk", "entitled_team_id"])}
    pas, same_side, same_player, n_fail, prior_succ, fail_inn = [], [], [], [], [], []
    for r in d.itertuples(index=False):
        g = fail_by.get((r.game_pk, r.entitled_team_id))
        sv = succ_by.get((r.game_pk, r.entitled_team_id), np.array([]))
        prior_succ.append(int((sv < r.ord).sum()))
        if g is None or not (g.ord < r.ord).any():
            pas.append(np.nan); same_side.append(None); same_player.append(None); n_fail.append(0); fail_inn.append(np.nan); continue
        e = g[g.ord < r.ord]; last = e.iloc[-1]
        n_fail.append(len(e)); pas.append(r.at_bat_index - last.at_bat_index); fail_inn.append(last.inning)
        same_side.append(bool(last.opportunity_side == r.side))
        involved = {r.batter_id} if r.side == "OFFENSE" else {r.catcher_id, r.pitcher_id}
        same_player.append(bool(last.challenger_id in involved))
    d = d.copy()
    d["pas_since_failure"] = pas; d["failure_same_side"] = same_side; d["failure_same_player"] = same_player
    d["prior_failures"] = n_fail; d["prior_successes"] = prior_succ; d["last_failure_inning"] = fail_inn
    grant = d.extra_inning_grants_before.fillna(0).gt(0)
    d["inv_state"] = np.select(
        [d.inv.eq(2) & d.prior_successes.eq(0), d.inv.eq(2) & d.prior_successes.gt(0),
         d.inv.eq(1) & grant, d.inv.eq(1) & d.pas_since_failure.le(3), d.inv.eq(1) & d.pas_since_failure.le(12), d.inv.eq(1)],
        ["INV2_NO_PRIOR_CHALLENGE_SUCCESS", "INV2_AFTER_PRIOR_SUCCESS", "INV1_EXTRA_INNING_GRANT", "INV1_FAILURE_WITHIN_3_PA",
         "INV1_FAILURE_4_TO_12_PA", "INV1_FAILURE_MORE_THAN_12_PA"], "OTHER")
    return d


def post_failure(d):
    reg = prep_behavior(d[~d.extras | d.inv_state.eq("INV1_EXTRA_INNING_GRANT")])
    reg["ev_c"] = reg.ev.clip(0, DMAX); reg["net_c"] = reg.net.clip(-1, 2) + 1
    rows = []
    for k, x in reg.groupby("inv_state"):
        rows.append({"table": "raw_by_inventory_state", "level": k, "n": len(x), "challenge_rate": x.challenged_i.mean(), "mean_ev": x.ev.mean(), "mean_net": x.net.mean()})
    base = f"challenged_i ~ C(inv_state, Treatment('INV2_NO_PRIOR_CHALLENGE_SUCCESS')) + {spline('net_c')} + lprop + {CTRL}"
    # Extra-inning grants occur only in extras (collinear with the 10+ inning bucket): described above, not modelled.
    reg = reg[~reg.extras & reg.inv_state.ne("OTHER")].copy()
    reg["inv_state"] = pd.Categorical(reg.inv_state, categories=sorted(reg.inv_state.unique()))
    r = glm(reg.dropna(subset=["net_c", "lprop"]), base, cluster="game_pk")
    for t in r.params.index:
        if t.startswith("C(inv_state"):
            rr = or_row(r, t, "inv_state_net_adjusted"); rr["level"] = t.split("[T.")[1].rstrip("]"); rows.append({"table": "adjusted_or_vs_inv2_no_prior", **rr})
    inv1 = reg[reg.inv.eq(1) & ~reg.inv_state.eq("INV1_EXTRA_INNING_GRANT") & reg.pas_since_failure.notna()].copy()
    inv1["log_pas"] = np.log1p(inv1.pas_since_failure)
    inv1["same_side_i"] = inv1.failure_same_side.astype(bool).astype(int); inv1["same_player_i"] = inv1.failure_same_player.astype(bool).astype(int)
    r2 = glm(inv1, f"challenged_i ~ log_pas + same_side_i + same_player_i + {spline('net_c')} + lprop + {CTRL}", cluster="game_pk")
    for t in ("log_pas", "same_side_i", "same_player_i"):
        rows.append({"table": "within_inv1_failure_context", **or_row(r2, t, "within_inv1"), "level": t})
    # Team fixed effects version of the inventory-state contrast
    r3 = glm(reg.dropna(subset=["net_c", "lprop"]), base + " + C(entitled_team)", cluster="game_pk")
    for t in r3.params.index:
        if t.startswith("C(inv_state"):
            rr = or_row(r3, t, "inv_state_net_adjusted_team_fe"); rr["level"] = t.split("[T.")[1].rstrip("]"); rows.append({"table": "adjusted_or_team_fe", **rr})
    return pd.DataFrame(rows), (r, r2)


# ============================================================ A8 expiration
def game_finals(p):
    raw = ROOT / "data/full_season/raw"
    rec = {json.loads(l)["sha256"]: json.loads(l) for l in (raw / "receipts.jsonl").read_text().splitlines()}
    out = []
    for g, sha in p.drop_duplicates("game_pk")[["game_pk", "source_game_feed"]].itertuples(index=False):
        f = json.loads((raw / rec[sha]["path"]).read_text())
        ls = f["liveData"]["linescore"]
        out.append({"game_pk": g, "final_home": ls["teams"]["home"]["runs"], "final_away": ls["teams"]["away"]["runs"],
                    "innings": max(i["num"] for i in ls["innings"])})
    return pd.DataFrame(out)


def expiration(p, d, ai, seq):
    """HINDSIGHT: which team-games ended with unused inventory, and what had been passed earlier."""
    q = p.sort_values(["game_pk", "ord"])
    last = q.groupby("game_pk").tail(1)
    fin = game_finals(p)
    rows = []
    ch_last = seq[seq.exercised].sort_values("sequence_number").groupby("team_game_id").tail(1)
    for r in last.itertuples(index=False):
        off = r.away_team_id if r.half_inning == "top" else r.home_team_id
        dfn = r.home_team_id if r.half_inning == "top" else r.away_team_id
        for team, inv in ((off, r.offense_challenges_remaining), (dfn, r.defense_challenges_remaining)):
            inv = int(inv)
            if str(r.challenged).lower() == "true" and r.challenge_outcome == "CONFIRMED" and team == r.affected_team_id:
                inv -= 1
            rows.append({"game_pk": r.game_pk, "team_id": team, "role": "HOME" if team == r.home_team_id else "AWAY", "final_inventory": max(inv, 0)})
    tg = pd.DataFrame(rows).merge(fin, on="game_pk")
    tg["margin"] = (tg.final_home - tg.final_away).abs(); tg["close_game"] = tg.margin.le(2); tg["extra_innings"] = tg.innings.gt(9)
    grants = d.groupby(["game_pk", "entitled_team_id"]).extra_inning_grants_before.max()
    dd = d.copy()
    passed = dd[dd.challenged_i.eq(0)]
    agg = dd.groupby(["game_pk", "entitled_team_id"]).agg(eligible_calls=("pitch_key", "size"), unchallenged=("challenged_i", lambda x: (x == 0).sum()))
    pagg = passed.groupby(["game_pk", "entitled_team_id"]).agg(value_passed=("v", "sum"), ev_passed=("ev", "sum"), max_value_passed=("v", "max"),
                                                              net_positive_passed=("net", lambda x: (x > 0).sum()),
                                                              immediate_exceeds_passed=("decision_class", lambda x: (x == "IMMEDIATE_EXCEEDS_PRESERVATION").sum()))
    idx = passed.loc[passed.groupby(["game_pk", "entitled_team_id"]).v.idxmax()].set_index(["game_pk", "entitled_team_id"])
    pagg["inning_of_max_passed"] = idx.inning
    tg = tg.merge(agg, left_on=["game_pk", "team_id"], right_index=True, how="left").merge(pagg, left_on=["game_pk", "team_id"], right_index=True, how="left")
    for c in ("eligible_calls", "unchallenged", "value_passed", "ev_passed", "net_positive_passed", "immediate_exceeds_passed"):
        tg[c] = tg[c].fillna(0)
    team_names = d.drop_duplicates("entitled_team_id").set_index("entitled_team_id").entitled_team
    tg["team"] = tg.team_id.map(team_names)
    tg["unused"] = tg.final_inventory.gt(0)
    out = []
    def summ(x, **k):
        u = x[x.unused]
        return {**k, "team_games": len(x), "pct_unused": x.unused.mean(), "pct_final_2": x.final_inventory.eq(2).mean(),
                "pct_final_1": x.final_inventory.eq(1).mean(), "pct_final_0": x.final_inventory.eq(0).mean(),
                "unused_mean_eligible_calls": u.eligible_calls.mean(), "unused_mean_unchallenged": u.unchallenged.mean(),
                "unused_mean_value_passed": u.value_passed.mean(), "unused_mean_ev_passed": u.ev_passed.mean(),
                "unused_median_max_value_passed": u.max_value_passed.median(),
                "unused_pct_with_immediate_exceeds_pass": (u.immediate_exceeds_passed > 0).mean(),
                "unused_pct_with_net_positive_pass": (u.net_positive_passed > 0).mean()}
    out.append(summ(tg, stratum="ALL", level="ALL"))
    for key in ("final_inventory", "role", "close_game", "extra_innings", "team"):
        for k, x in tg.groupby(key):
            out.append(summ(x, stratum=key, level=str(k)))
    inn = tg[tg.unused & tg.inning_of_max_passed.notna()].inning_of_max_passed.clip(upper=10).value_counts(normalize=True).sort_index()
    for k, v in inn.items():
        out.append({"stratum": "unused_inning_of_max_passed", "level": str(int(k)), "share": v})
    units_total = 2 * len(tg) + float(grants.sum())
    summary = {"LABEL": "HINDSIGHT", "team_games": len(tg), "pct_team_games_unused": float(tg.unused.mean()),
               "final_inventory_distribution": tg.final_inventory.value_counts(normalize=True).sort_index().to_dict(),
               "unused_units": int(tg.final_inventory.sum()), "challenge_units_available_incl_grants": units_total,
               "pct_units_unused": float(tg.final_inventory.sum() / units_total),
               "pct_unused_games_that_passed_immediate_exceeds": float((tg[tg.unused].immediate_exceeds_passed > 0).mean())}
    pi = passed[passed.decision_class.eq("IMMEDIATE_EXCEEDS_PRESERVATION")].merge(tg[["game_pk", "team_id", "unused"]], left_on=["game_pk", "entitled_team_id"],
                                                                                  right_on=["game_pk", "team_id"], how="left")
    summary["passed_immediate_exceeds_opportunities"] = len(pi)
    summary["pct_passed_immediate_exceeds_in_games_ending_unused"] = float(pi.unused.mean())
    pv = passed.merge(tg[["game_pk", "team_id", "unused"]], left_on=["game_pk", "entitled_team_id"], right_on=["game_pk", "team_id"], how="left")
    summary["pct_all_passed_in_games_ending_unused"] = float(pv.unused.mean())
    summary["pct_passed_value_ge_050_in_games_ending_unused"] = float(pv[pv.v >= .5].unused.mean())
    return pd.DataFrame(out), summary, tg


# ============================================================ A9
def high_value_early(d, seq, tg):
    s = seq.sort_values(["team_game_id", "sequence_number"])
    x = d[d.challenged_i.eq(0) & d.inning.le(3) & d.v.ge(0.5)].copy()
    later_use, later_max, later_max_ev = [], [], []
    ev_map = d.set_index("pitch_key").ev
    v_map = d.set_index("pitch_key").v
    for r in x.itertuples(index=False):
        g = s[(s.game_pk == r.game_pk) & (s.entitled_team_id == r.entitled_team_id)]
        ords = g.at_bat_index * 1000 + g.play_event_index
        lat = g[ords > r.ord]
        later_use.append(bool(lat.exercised.any()))
        le = lat[lat.sequence_event_class.eq("ELIGIBLE_INCORRECT_CALL")]
        later_max.append(le.pitch_key.map(v_map).max() if len(le) else np.nan)
        later_max_ev.append(le.pitch_key.map(ev_map).max() if len(le) else np.nan)
    x["hindsight_team_used_challenge_later"] = later_use
    x["hindsight_later_max_value"] = later_max; x["hindsight_later_max_ev"] = later_max_ev
    x["hindsight_later_value_exceeded"] = x.hindsight_later_max_value > x.v
    x["hindsight_later_ev_exceeded"] = x.hindsight_later_max_ev > x.ev
    x = x.merge(tg[["game_pk", "team_id", "final_inventory"]], left_on=["game_pk", "entitled_team_id"], right_on=["game_pk", "team_id"], how="left")
    x["hindsight_game_ended_unused"] = x.final_inventory.gt(0)
    cols = ["pitch_key", "game_date", "side", "entitled_team", "inning", "half_inning", "outs", "count", "base_state", "inv", "inv_state",
            "prior_failures", "absd", "edge", "v", "propensity", "p_success", "ev", "cost", "cost_low", "cost_high", "net", "decision_class",
            "hindsight_team_used_challenge_later", "hindsight_later_max_value", "hindsight_later_value_exceeded",
            "hindsight_later_max_ev", "hindsight_later_ev_exceeded", "final_inventory", "hindsight_game_ended_unused"]
    x = x[cols].rename(columns={"v": "correction_value_runs_pooled"})
    summ = {"LABEL": "HINDSIGHT columns prefixed hindsight_", "n": len(x), "mean_p_success": float(x.p_success.mean()), "mean_ev": float(x.ev.mean()),
            "mean_cost": float(x.cost.mean()), "pct_net_positive": float((x.net > 0).mean()),
            "decision_class": x.decision_class.value_counts().to_dict(), "inventory": x.inv.value_counts().to_dict(),
            "pct_prior_failure": float((x.prior_failures > 0).mean()),
            "pct_later_value_exceeded": float(x.hindsight_later_value_exceeded.mean()),
            "pct_later_ev_exceeded": float(x.hindsight_later_ev_exceeded.mean()),
            "pct_used_later": float(x.hindsight_team_used_challenge_later.mean()), "pct_game_ended_unused": float(x.hindsight_game_ended_unused.mean())}
    return x, summ


# ============================================================ A10
def braves(d, re288, fut_lomo, fut_full):
    r = d[d.pitch_key.eq("824887:3:7")].iloc[0]
    lk = re288.set_index(["balls", "strikes", "outs", "base_state"]).re_count_pooled.to_dict()
    obs = lk[(0, 0, 1, "110")]
    vals = {"recorded_no_runner_action": obs - lk[(0, 0, 2, "100")], "bichette_safe_at_second": obs - lk[(0, 0, 2, "010")], "bichette_out_inning_over": obs}
    out = {"pitch_key": "824887:3:7", "what_happened": "Called ball four on a 3-2 pitch to Benge with one out and Bichette on first; no official challenge recorded; Baty grand slam three batters later; final NYM 8, ATL 5.",
           "not_in_sources": ["steal attempt", "catcher throw", "call at second", "attempted hat-tap challenge"],
           "decision_time_inputs": {"unsigned_distance_in": float(r.absd), "nearest_edge": r.edge, "inventory": int(r.inv), "inning": 1, "half": "top", "outs": 1,
                                    "role": "HOME (Braves fielding)"},
           "resource_independent_challenge_propensity": float(r.propensity), "p_success": float(r.p_success),
           "preservation_cost_league_behavior": float(r.cost), "preservation_cost_range": [float(r.cost_low), float(r.cost_high)],
           "marginal_option_value_second_challenge": float(r.marg_league_behavior),
           "counterfactual_states": {}}
    for k, v in vals.items():
        ev = r.p_success * v
        out["counterfactual_states"][k] = {"correction_value": v, "gross_immediate_ev": ev, "net_vs_league_behavior_cost": ev - r.cost,
                                           "class": str(classify_spend([ev], [r.cost_low], [r.cost_high])[0])}
    out["realized_outcome_for_contrast_only"] = "Four more Mets runs scored in the inning. That realized outcome is not the decision-time value or cost."
    return out


# ============================================================ A11
def sensitivity(o, ai, d, p, first, teams, fut, re288, near):
    rows = []
    def run(label, dd):
        suite, _ = scarcity_suite(dd, label)
        for r in suite.itertuples(index=False):
            rows.append({"variant": label, "model": r.model, "term": r.term, "odds_ratio": r.odds_ratio, "ci_low": r.ci_low, "ci_high": r.ci_high, "n": r.n})
        reg = dd[~dd.extras] if "extras" in dd else dd
        rows.append({"variant": label, "model": "descriptive", "term": "passed_with_immediate_exceeds_share_of_passes",
                     "odds_ratio": float((reg.decision_class.eq("IMMEDIATE_EXCEEDS_PRESERVATION") & reg.challenged_i.eq(0)).sum() / max(1, reg.challenged_i.eq(0).sum())), "n": len(reg)})
    base = d[~d.extras]
    run("PRIMARY", base)
    # alternative preservation-value policies
    for k in POLICIES + ["prophet"]:
        x = base.copy(); x["cost"] = x[f"cost_{k}"]; x["net"] = x.ev - x.cost; run(f"cost_policy_{k}", x)
    # alternative success models (recompute EV, streams and costs)
    fut_cache = {}
    def rebuild(label, pcol, vcol):
        o2, ai2 = o.copy(), ai.copy()
        o2["p_success"] = o2[pcol] if pcol != "ORACLE" else 1.0
        ai2["p_success"] = ai2[pcol] if pcol != "ORACLE" else 1.0
        o2["v"] = o2[vcol]; ai2["v"] = ai2[vcol]
        o2["ev"] = o2.p_success * o2.v; ai2["ev"] = ai2.p_success * ai2.v
        st = build_streams(ai2, "p_success", "v", "q_use")
        f2 = future_table(p, st, first, teams)
        ff, fl = state_estimates(f2)
        x = attach_costs(o2[o2.v.notna() & o2.p_success.notna()].copy(), ff, fl)
        x = add_failure_context(x, SEQ, CH)
        return x[~x.extras]
    run("success_model_oracle_p1", rebuild("oracle", "ORACLE", PRIMARY))
    run("success_model_coarse_S0", rebuild("coarse", "p_success_coarse", PRIMARY))
    run("success_model_public_information", rebuild("public", "p_success_public", PRIMARY))
    run("success_model_chronological_only_no_march", rebuild("chrono", "p_success_chrono", PRIMARY))
    run("RE_sprint5_smoothing", rebuild("old", "p_success", OLD))
    # population / flag variants
    run("exclude_unrecorded_runner_action_flag", base[~base.cf_unrecorded_runner_action_possible.astype(str).str.lower().eq("true")])
    run("offense_only", base[base.side.eq("OFFENSE")])
    run("defense_only", base[base.side.eq("DEFENSE")])
    run("innings_1_to_8_only", base[base.inning.le(8)])
    # Score-bucket states for option value
    f3 = fut.copy()
    ff, fl = state_estimates(f3, keys=STATE_KEYS + ["score_bucket"])
    x = o[o.v.notna()].copy()
    x["score_bucket"] = np.select([x.entitled_team_score_diff > 0, x.entitled_team_score_diff < 0], ["LEAD", "TRAIL"], "TIE")
    x = attach_costs(x, ff, fl, keys=STATE_KEYS + ["score_bucket"])
    x = add_failure_context(x, SEQ, CH)
    run("option_value_states_include_score", x[~x.extras & x.cost.notna()])
    # Near-boundary population not conditioned on call correctness (flip values ignore runner action)
    nb = near_boundary(near, re288, o)
    for r in nb:
        rows.append(r)
    return pd.DataFrame(rows)


def near_boundary(near, re288, o):
    """Falsification: all called pitches within 3 inches of the boundary with inventory available,
    whether or not the call was correct.  Value = flip value (count/base-out only)."""
    lk = re288.set_index(["balls", "strikes", "outs", "base_state"]).re_count_pooled.to_dict()
    lk = {(int(a), int(b), int(c), str(e)): v for (a, b, c, e), v in lk.items()}
    n = near.copy()
    n["base_state"] = n[["on_1b", "on_2b", "on_3b"]].notna().astype(int).astype(str).agg("".join, axis=1)
    n = n[n.balls.le(3) & n.strikes.le(2) & n.outs.le(2)]
    n["v"] = [flip_value(int(b), int(s), int(ot), bs, c, lk) for b, s, ot, bs, c in zip(n.balls, n.strikes, n.outs, n.base_state, n.original_call)]
    n["ev"] = n.p_success * n.v
    n["entitled_team_id"] = n.affected_team_id
    team_home = n.entitled_team_id.eq(n.home_team_id)
    n["entitled_team_score_diff"] = np.where(team_home, n.home_score - n.away_score, n.away_score - n.home_score)
    n["late_close"] = n.inning.ge(7) & (n.home_score - n.away_score).abs().le(2)
    n["propensity"] = np.nan
    n["geometry_incorrect"] = ((n.original_call == "STRIKE") & (n.derived_abs_call == "BALL")) | ((n.original_call == "BALL") & (n.derived_abs_call == "STRIKE"))
    x = prep_behavior(n.assign(net=n.ev, cost=0.0))
    x["ev_c"] = x.ev.clip(0, DMAX)
    rows = []
    for label, f in (("NEAR_BOUNDARY_all_calls_ev_only", f"challenged_i ~ inv1 + {spline('ev_c')} + {spline('absd')} + C(edge) + {CTRL}"),
                     ("NEAR_BOUNDARY_all_calls_ev_x_inv", f"challenged_i ~ inv1 * ev4 + {spline('absd')} + C(edge) + {CTRL}")):
        dd = x.dropna(subset=["ev_c", "absd", "inning_bucket"])
        r = glm(dd, f, cluster="game_pk")
        for t in ("inv1", "inv1:ev4", "ev4"):
            if t in r.params.index:
                ci = r.conf_int().loc[t]
                rows.append({"variant": label, "model": label, "term": t, "odds_ratio": np.exp(r.params[t]), "ci_low": np.exp(ci[0]), "ci_high": np.exp(ci[1]), "n": int(r.nobs)})
    chk = o[o.cf_rule.eq("R1_NO_RUNNER_ACTION") & o.v.notna()].head(2000)
    diffs = [abs(flip_value(int(r.balls), int(r.strikes), int(r.outs), r.base_state, r.original_call, lk) - r.v) for r in chk.itertuples(index=False)]
    rows.append({"variant": "validation", "model": "flip_value_vs_article4_R1", "term": "max_abs_difference", "odds_ratio": float(np.max(diffs)), "n": len(diffs)})
    rows.append({"variant": "NEAR_BOUNDARY_all_calls_ev_only", "model": "descriptive", "term": "share_geometry_incorrect", "odds_ratio": float(n.geometry_incorrect.mean()), "n": len(n)})
    return rows


# ============================================================ leakage & validation
def leakage_checks(o, c, fut, d):
    chk = {}
    chk["propensity_features"] = "unsigned distance, side, nearest edge (and pitch family/handedness if selected): no inventory, no challenge history, no future fields"
    chk["success_features"] = "unsigned distance x side, nearest edge, terminal count (and pitch family/handedness if selected): no signed distance, no plate coordinates, no ABS result"
    chk["crossfit"] = "every prediction for a row in month m comes from a model fit without month m (so never on its own game)"
    chk["propensity_missing_predictions"] = int(o.propensity.isna().sum()); chk["success_missing_predictions"] = int(o.p_success.isna().sum())
    chk["option_value"] = "decision rows receive leave-one-month-out state means computed from other months' games only"
    # verify: signed distance cannot be recovered from features (edge x unsigned distance is identical inside/outside)
    chk["edge_symmetry_test"] = "tests/test_article4_decision_value.py::test_edge_symmetric_across_boundary"
    chk["cost_missing_rows"] = int(d.cost.isna().sum())
    chk["hindsight_in_models"] = "none; hindsight_ columns appear only in article4_high_value_early.csv and article4_expiration.csv"
    return chk


def write_validation(S, path):
    v = S["validation"]; r = S["reconciliation"]; pm = S["propensity"]["chronological"]; sm_ = S["success_model"]["chronological"]
    lines = ["# Article 4 decision-value analysis - validation", "", "Generated by `analyze.py`; do not hand-edit.", "",
             "## Inputs", "",
             f"- Eligible opportunities {r['eligible']:,} (offense {r['offense']:,}, defense {r['defense']:,}), {r['challenged']:,} challenged; all incorrect calls {r['all_incorrect']:,}; official challenges {r['official_challenges']:,}. Asserted.",
             f"- Article 4 dataset hashes match its manifest: **{r['article4_hashes_match_manifest']}**.",
             f"- Protected Articles 1-3, Article 4 and exploratory files unchanged by this run: **{v['protected_unchanged']}** ({v['protected_files']} files).", "",
             "## Leakage", ""] + [f"- **{k}**: {val}" for k, val in v["leakage"].items()] + [
             "", "## Model checks (chronological, strictly earlier months)", "",
             f"- Resource-independent challenge propensity ({S['propensity']['selected_evidence_only']}): AUC {pm['roc_auc']:.3f}, log loss {pm['log_loss']:.4f}, calibration slope {pm['calibration_slope']:.3f}, intercept {pm['calibration_intercept']:.3f}, ECE {pm['ece_10bin']:.4f} (n={pm['n']:,}).",
             f"- Challenge success ({S['success_model']['selected']}): AUC {sm_['roc_auc']:.3f}, log loss {sm_['log_loss']:.4f}, calibration slope {sm_['calibration_slope']:.3f}, intercept {sm_['calibration_intercept']:.3f}, ECE {sm_['ece_10bin']:.4f} (n={sm_['n']:,}).",
             "", "## Reproducibility", "",
             f"- Python {v['python']}, pandas {v['pandas']}, numpy {v['numpy']}, statsmodels {v['statsmodels']}, scipy {v['scipy']}; seed {v['seed']}; {v['bootstrap_reps']} game-cluster bootstrap replicates for state CIs.",
             f"- analyze.py `{v['code_sha256']['analyze.py']}`; dv_core.py `{v['code_sha256']['dv_core.py']}`.",
             "- Input hashes: `output/article4_decision_value_summary.json` -> validation.input_sha256.",
             "- Determinism: two complete builds compared byte-for-byte (see DECISION_VALUE_ANALYSIS.md, Validation).",
             "- Tests: `tests/test_article4_decision_value.py` (option-value recursion vs brute-force enumeration, retention after success, edge symmetry, classification)."]
    path.write_text("\n".join(lines) + "\n")


# ============================================================ figures
def figures(c, chrono_s, d, fut_full, sens, pf, exp_rows, hv, br, suite):
    # 1 success probability vs unsigned distance
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for side, col in (("OFFENSE", BLUE), ("DEFENSE", ORANGE)):
        x = c[c.side == side]; b = pd.cut(x.absd, np.arange(0, DMAX + .5, .5))
        t = x.groupby(b, observed=True).agg(obs=("success", "mean"), pred=("p_success_cf", "mean"), n=("success", "size"), mid=("absd", "mean"))
        t = t[t.n >= 20]
        ax.plot(t.mid, t.obs, "o", color=col, ms=6, label=f"{side.title()} observed")
        ax.plot(t.mid, t.pred, "-", color=col, alpha=.8, label=f"{side.title()} cross-fitted model")
    ax.set(xlabel="Unsigned distance from ABS boundary (inches; side of the edge not used)", ylabel="Share of challenges overturned",
           title="Challenge success vs boundary proximity (all 9,485 official challenges)", ylim=(0, 1))
    ax.legend(fontsize=8); savefig(fig, "fig01_success_vs_distance.png")
    # 2 gross EV distribution
    fig, ax = plt.subplots(figsize=(8, 4.2)); bins = np.linspace(0, 1.2, 61)
    for lab, x, col in (("Challenged", d[d.challenged_i == 1], AQUA), ("Unchallenged", d[d.challenged_i == 0], INK2)):
        ax.hist(x.ev, bins=bins, histtype="step", lw=2, color=col, label=f"{lab} (median {x.ev.median():.3f})", density=True)
    ax.set(yscale="log", xlabel="Gross immediate expected value = P(success) x correction value (runs)", ylabel="Density (log)",
           title="Gross immediate expected challenge value"); ax.legend(); savefig(fig, "fig02_gross_ev_distribution.png")
    # 3 option value by inning
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
    for i, role in enumerate(("HOME", "AWAY")):
        t = fut_full[(fut_full.role == role) & (fut_full.outs == 0)].copy()
        t["x"] = t.inning + np.where(t.half == "bottom", .5, 0); t = t.sort_values("x")
        ax[i].fill_between(t.x, t.OV1_league_behavior_lo, t.OV1_league_behavior_hi, color=BLUE, alpha=.18, lw=0)
        ax[i].plot(t.x, t.OV1_league_behavior, "-", color=BLUE, label="1 challenge: league-behavior use")
        ax[i].plot(t.x, t["OV1_tau_0.05"], "--", color=AQUA, label="1 challenge: use if EV >= 0.05")
        ax[i].plot(t.x, t.prophet1, ":", color=INK2, label="1 challenge: best single future opportunity (not a bound)")
        ax[i].plot(t.x, t.M2_league_behavior, "-", color=ORANGE, label="2nd challenge (marginal): league behavior")
        ax[i].set(xlabel="Inning (x.5 = bottom half), 0 outs", title=f"{role.title()} team: expected future option value")
    ax[0].set_ylabel("Expected runs recoverable (cross-game averages, 95% CI)"); ax[0].legend(fontsize=7)
    savefig(fig, "fig03_option_value_by_inning.png")
    # 4 immediate vs preservation
    reg = d[~d.extras]
    fig, ax = plt.subplots(figsize=(6.5, 6))
    for inv, col in ((2, BLUE), (1, ORANGE)):
        x = reg[reg.inv == inv].sample(min(3000, (reg.inv == inv).sum()), random_state=SEED)
        ax.scatter(x.cost, x.ev, s=6, alpha=.35, color=col, label=f"{inv} challenge{'s' if inv == 2 else ''} left", edgecolors="none")
    lim = max(reg.ev.quantile(.995), reg.cost.quantile(.995))
    ax.plot([0, lim], [0, lim], color=INK2, lw=1); ax.set(xlim=(0, lim), ylim=(0, lim),
                                                         xlabel="Preservation cost = P(fail) x marginal option value (runs)", ylabel="Gross immediate EV (runs)",
                                                         title="Immediate value vs preservation cost (sample of points)")
    ax.legend(); savefig(fig, "fig04_immediate_vs_preservation.png")
    # 5 challenge prob across spend/preserve
    fig, ax = plt.subplots(figsize=(8, 4.2))
    t = reg.assign(nb=pd.cut(reg.net, [-2, -.05, 0, .05, .10, .20, .35, 5])).groupby(["nb", "inv"], observed=True).challenged_i.agg(["mean", "size"]).reset_index()
    for inv, col, off in ((2, BLUE, -.1), (1, ORANGE, .1)):
        q = t[t.inv == inv]; x = np.arange(len(q)) + off
        ax.plot(x, q["mean"], "o-", color=col, label=f"{inv} left")
        for xx, yy, nn in zip(x, q["mean"], q["size"]):
            ax.annotate(f"{nn}", (xx, yy), xytext=(0, 6), textcoords="offset points", fontsize=7, color=INK2, ha="center")
    ax.set_xticks(range(len(q))); ax.set_xticklabels([str(i) for i in q.nb], rotation=20, fontsize=8)
    ax.set(xlabel="Net decision value = gross EV - preservation cost (runs; league-behavior benchmark)", ylabel="Share challenged",
           title="Actual challenge rate across the spend/preserve comparison (labels = n)"); ax.legend()
    savefig(fig, "fig05_challenge_rate_by_net_value.png")
    # 6 scarcity before/after
    x = suite[suite.term.eq("inv1")]
    fig, ax = plt.subplots(figsize=(8, 4))
    y = np.arange(len(x))
    ax.errorbar(x.odds_ratio, y, xerr=[x.odds_ratio - x.ci_low, x.ci_high - x.odds_ratio], fmt="o", color=ORANGE)
    ax.axvline(1, color=INK2, lw=1); ax.set_yticks(y); ax.set_yticklabels(x.model); ax.invert_yaxis()
    ax.set(xlabel="Odds ratio, one vs two challenges left (95% CI, game-clustered)", title="Scarcity association before and after decision-value adjustment")
    savefig(fig, "fig06_scarcity_before_after.png")
    # 7 post-failure
    t = pf[pf.table.eq("adjusted_or_vs_inv2_no_prior")]
    fig, ax = plt.subplots(figsize=(8, 3.8)); y = np.arange(len(t))
    ax.errorbar(t.odds_ratio, y, xerr=[t.odds_ratio - t.ci_low, t.ci_high - t.odds_ratio], fmt="o", color=BLUE)
    ax.axvline(1, color=INK2, lw=1); ax.set_yticks(y); ax.set_yticklabels(t.level); ax.invert_yaxis()
    ax.set(xlabel="Adjusted odds ratio vs two left with no prior success (net value, propensity, controls)", title="Challenge behavior by inventory history")
    savefig(fig, "fig07_post_failure.png")
    # 8 expiration
    e = exp_rows[exp_rows.stratum.isin(["ALL", "final_inventory", "close_game", "extra_innings", "role"])]
    fig, ax = plt.subplots(figsize=(8, 3.8)); y = np.arange(len(e))
    ax.barh(y, e.pct_unused.fillna(0), color=BLUE, height=.6)
    for yy, vv, n in zip(y, e.pct_unused.fillna(0), e.team_games):
        ax.text(vv + .01, yy, f"{vv:.0%} (n={int(n)})", va="center", fontsize=8, color=INK2)
    ax.set_yticks(y); ax.set_yticklabels([f"{a}={b}" for a, b in zip(e.stratum, e.level)]); ax.invert_yaxis()
    ax.set(xlim=(0, 1.15), xlabel="Share of team-games ending with at least one unused challenge (HINDSIGHT)", title="Challenge expiration")
    savefig(fig, "fig08_expiration.png")
    # 9 high-value early
    fig, ax = plt.subplots(figsize=(7, 5))
    for inv, col in ((2, BLUE), (1, ORANGE)):
        x = hv[hv.inv == inv]
        ax.scatter(x.cost, x.ev, s=30, color=col, alpha=.8, label=f"{inv} left (n={len(x)})", edgecolors="white", linewidths=.6)
    lim = max(hv.ev.max(), hv.cost.max()) * 1.05
    ax.plot([0, lim], [0, lim], color=INK2, lw=1)
    ax.set(xlim=(0, lim), ylim=(0, lim), xlabel="Preservation cost (runs)", ylabel="Gross immediate EV (runs)",
           title=f"Passed early opportunities worth >= 0.50 runs (n={len(hv)})"); ax.legend()
    savefig(fig, "fig09_high_value_early.png")
    # 10 Braves
    fig, ax = plt.subplots(figsize=(9, 4.4))
    labels = list(br["counterfactual_states"].keys()); y = np.arange(len(labels))
    cv = [br["counterfactual_states"][k]["correction_value"] for k in labels]; ev = [br["counterfactual_states"][k]["gross_immediate_ev"] for k in labels]
    ax.barh(y - .2, cv, height=.38, color=INK2, label="Correction value (if call corrected)")
    ax.barh(y + .2, ev, height=.38, color=BLUE, label=f"Gross EV (x P(success) = {br['p_success']:.2f})")
    ax.axvline(br["preservation_cost_league_behavior"], color=ORANGE, lw=2, label=f"Preservation cost {br['preservation_cost_league_behavior']:.3f}")
    ax.axvspan(br["preservation_cost_range"][0], br["preservation_cost_range"][1], color=ORANGE, alpha=.12, lw=0)
    ax.set_yticks(y); ax.set_yticklabels(labels); ax.invert_yaxis()
    ax.set(xlabel="Runs (decision-time expectations; realized 4-run inning not shown)", title="Braves 824887:3:7 decision-value decomposition")
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3); savefig(fig, "fig10_braves_decomposition.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=HERE / "output")
    a = ap.parse_args()
    main(a.output.resolve())
