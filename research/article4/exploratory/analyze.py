"""Article 4 exploratory analysis: what is a challenge worth?

Reads the validated Article 4 dataset (research/article4/output) and writes
exploratory tables, figures, a machine-readable summary and a validation
report to research/article4/exploratory/output.  Nothing upstream is modified.

Primary run-expectancy estimator: the pooled-count RE288 alternative
(`correction_value_runs_pooled`).  The Sprint 5 smoothing estimator
(`correction_value_runs`) is a sensitivity.  All values are decision-point
counterfactual run expectancy; realized later runs are never used.  Fields
prefixed `hindsight_` / analysis 3 outputs are retrospective only.
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
from scipy import stats
from statsmodels.stats.proportion import proportion_confint

warnings.filterwarnings("ignore", category=RuntimeWarning)
HERE = Path(__file__).resolve().parent
A4 = HERE.parent
SEED = 20260924
PRIMARY, OLD = "correction_value_runs_pooled", "correction_value_runs"
THRESHOLDS = [0.10, 0.25, 0.50, 0.75, 1.00]
VALUE_BINS = [-np.inf, 0.10, 0.25, 0.50, 0.75, np.inf]
VALUE_LABELS = ["<0.10", "0.10-0.25", "0.25-0.50", "0.50-0.75", ">=0.75"]
LOW_VALUE_CUT = 0.05  # fixed a priori for the "very low value excluded" sensitivity
# Reference palette (dataviz skill), light mode; <=3 categorical series per chart.
BLUE, ORANGE, AQUA, INK, INK2, GRID, SURF = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": .6,
                     "axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "axes.titlesize": 11,
                     "legend.frameon": False, "lines.linewidth": 2, "savefig.dpi": 200})


# ------------------------------------------------------------------ utilities
def digest(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as r:
        for b in iter(lambda: r.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jdefault(v):
    if isinstance(v, (np.integer,)): return int(v)
    if isinstance(v, (np.floating,)): return None if not np.isfinite(v) else round(float(v), 6)
    if isinstance(v, (np.bool_,)): return bool(v)
    if isinstance(v, float): return None if not np.isfinite(v) else round(v, 6)
    raise TypeError(type(v))


def wilson(k, n):
    if n == 0: return (np.nan, np.nan)
    lo, hi = proportion_confint(k, n, method="wilson")
    return lo, hi


def write_csv(df: pd.DataFrame, name: str):
    df.to_csv(OUT / name, index=False, float_format="%.6g", lineterminator="\n")


def savefig(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, facecolor=SURF)
    plt.close(fig)


def logit(p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


# -------------------------------------------------------------------- loading
def load():
    o = pd.read_csv(A4 / "output/article4_opportunities.csv", low_memory=False,
                    dtype={"base_state": str, "obs_base_state": str, "cor_base_state": str})
    allinc = pd.read_csv(A4 / "output/article4_all_incorrect_calls.csv", low_memory=False, dtype={"base_state": str},
                         usecols=["pitch_key", PRIMARY, OLD, "correction_value_runs_lower", "correction_value_runs_upper"])
    seq = pd.read_csv(A4 / "output/article4_team_game_sequences.csv", low_memory=False, dtype={"base_state": str})
    re288 = pd.read_csv(A4 / "output/article4_re288_table.csv", dtype={"base_state": str})
    o["challenged"] = o.challenged.astype(bool)
    o["inv"] = o.challenge_inventory.astype(int)
    o["inv1"] = (o.inv == 1).astype(int)
    o["side"] = o.opportunity_side
    o["score_state"] = np.select([o.entitled_team_score_diff > 0, o.entitled_team_score_diff < 0], ["AHEAD", "BEHIND"], "TIED")
    o["late_close_i"] = o.late_close.astype(bool).astype(int)
    o["early"] = o.inning.le(3)
    o["inning_c"] = o.inning.clip(upper=10)
    global DMAX
    DMAX = float(o.abs_distance_inches.quantile(.995))
    o["dist"] = o.abs_distance_inches.clip(upper=DMAX)
    o["terminal"] = o.strike_three_or_ball_four_at_stake.astype(bool).astype(int)
    o["logit_er"] = logit(o.expected_recognition_prob_temporal)
    o["ambiguous"] = o.cf_confidence.eq("AMBIGUOUS")
    o["month"] = o.game_date.str[:7]
    return o, allinc, seq, re288


# ------------------------------------------------------------------- models
CONTROLS = "C(side) + C(inning_bucket) + C(score_state) + late_close_i + bs(dist, df=4)"


DMAX = None


def _bounded(formula):
    return formula.replace("bs(dist, df=4)", f"bs(dist, df=4, lower_bound=0, upper_bound={DMAX:.6f})")


def fit_logit(df, formula, cluster="game_pk"):
    formula = _bounded(formula)
    d = df.dropna(subset=[c for c in ["v", "dist"] if c in df.columns]).copy()
    d["y"] = d.challenged.astype(int)
    m = smf.glm("y ~ " + formula, data=d, family=sm.families.Binomial())
    r = m.fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d[cluster])[0]})
    return r, d


def or_table(r, model, keep=None):
    ci = r.conf_int()
    rows = []
    for name in r.params.index:
        if keep and not any(k in name for k in keep):
            continue
        rows.append({"model": model, "term": name, "coef": r.params[name], "odds_ratio": np.exp(r.params[name]),
                     "or_ci_low": np.exp(ci.loc[name, 0]), "or_ci_high": np.exp(ci.loc[name, 1]), "p_value": r.pvalues[name],
                     "n": int(r.nobs)})
    return rows


def calibration(r, d, model):
    p = r.predict(d); y = d.challenged.astype(int)
    q = pd.qcut(p, 10, labels=False, duplicates="drop")
    t = pd.DataFrame({"decile": q, "p": p, "y": y}).groupby("decile").agg(mean_pred=("p", "mean"), obs_rate=("y", "mean"), n=("y", "size")).reset_index()
    t["model"] = model
    return t


def grouped_cv_logloss(df, formula, k=5):
    """Group-by-game K-fold held-out log loss (for team-block comparison)."""
    formula = _bounded(formula)
    d = df.dropna(subset=["v", "dist"]).copy(); d["y"] = d.challenged.astype(int)
    games = np.array(sorted(d.game_pk.unique())); rng = np.random.default_rng(SEED); rng.shuffle(games)
    fold_of = {g: i % k for i, g in enumerate(games)}; d["fold"] = d.game_pk.map(fold_of)
    ll = []
    for f in range(k):
        tr, te = d[d.fold != f], d[d.fold == f]
        r = smf.glm("y ~ " + formula, data=tr, family=sm.families.Binomial()).fit()
        p = np.clip(r.predict(te), 1e-6, 1 - 1e-6)
        ll.append(-(te.y * np.log(p) + (1 - te.y) * np.log(1 - p)).sum())
    return float(np.sum(ll) / len(d))


# ============================================================ ANALYSIS 1
def analysis1(o, vcol, tag="primary", figs=True):
    d = o[o[vcol].notna()].copy(); d["v"] = d[vcol]
    groups = {"ALL": d, "OFFENSE": d[d.side.eq("OFFENSE")], "DEFENSE": d[d.side.eq("DEFENSE")],
              "CHALLENGED": d[d.challenged], "UNCHALLENGED": d[~d.challenged],
              "OFFENSE_CHALLENGED": d[d.side.eq("OFFENSE") & d.challenged], "OFFENSE_UNCHALLENGED": d[d.side.eq("OFFENSE") & ~d.challenged],
              "DEFENSE_CHALLENGED": d[d.side.eq("DEFENSE") & d.challenged], "DEFENSE_UNCHALLENGED": d[d.side.eq("DEFENSE") & ~d.challenged]}
    rows = []
    for g, x in groups.items():
        if x.empty:
            continue
        v = x.v.to_numpy(); s = np.sort(v)[::-1]; tot = s.sum(); n = len(s)
        row = {"spec": tag, "group": g, "n": n, "total_value_runs": tot, "mean": v.mean(), "median": np.median(v), "sd": v.std(ddof=1),
               **{f"p{q}": np.percentile(v, q) for q in (10, 25, 50, 75, 90, 95, 99)}, "max": v.max()}
        for t in THRESHOLDS:
            row[f"n_ge_{t:.2f}"] = int((v >= t).sum()); row[f"pct_ge_{t:.2f}"] = (v >= t).mean()
            row[f"value_share_ge_{t:.2f}"] = v[v >= t].sum() / tot
        for top in (1, 5, 10, 20):
            k = max(1, int(round(n * top / 100)))
            row[f"top{top}pct_value_share"] = s[:k].sum() / tot
        row["gini"] = gini(v)
        rows.append(row)
    dist = pd.DataFrame(rows)
    # game-cluster bootstrap for top-10% share and mean (ALL)
    rng = np.random.default_rng(SEED); games = d.game_pk.unique(); by = {g: x.v.to_numpy() for g, x in d.groupby("game_pk")}
    boots = []
    for _ in range(300):
        v = np.concatenate([by[g] for g in rng.choice(games, len(games))]); s = np.sort(v)[::-1]
        boots.append((s[:max(1, int(round(len(s) * .1)))].sum() / s.sum(), v.mean(), (v >= .5).sum() / len(v)))
    b = np.array(boots)
    ci = {"top10_share_ci": np.percentile(b[:, 0], [2.5, 97.5]).tolist(), "mean_ci": np.percentile(b[:, 1], [2.5, 97.5]).tolist(),
          "pct_ge_0.50_ci": np.percentile(b[:, 2], [2.5, 97.5]).tolist()}
    # value by count (where value lives)
    bycount = d.groupby(["side", "count"]).agg(n=("v", "size"), total_value=("v", "sum"), mean_value=("v", "mean"),
                                               challenge_rate=("challenged", "mean")).reset_index()
    bycount["share_of_side_opportunities"] = bycount.n / bycount.groupby("side").n.transform("sum")
    bycount["share_of_side_value"] = bycount.total_value / bycount.groupby("side").total_value.transform("sum")
    if figs:
        fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        bins = np.linspace(0, 2, 81)
        for side, col in (("OFFENSE", BLUE), ("DEFENSE", ORANGE)):
            ax[0].hist(d.loc[d.side.eq(side), "v"], bins=bins, histtype="step", color=col, lw=2, label=side.title())
        ax[0].set(yscale="log", xlabel="Correction value (runs, pooled-count RE288)", ylabel="Opportunities (log scale)",
                  title="Correction value per eligible opportunity")
        ax[0].legend()
        for g, col, lab in (("CHALLENGED", AQUA, "Challenged"), ("UNCHALLENGED", INK2, "Unchallenged")):
            v = np.sort(groups[g].v)
            ax[1].plot(v, np.arange(1, len(v) + 1) / len(v), color=col, label=lab)
        ax[1].set(xlabel="Correction value (runs)", ylabel="Cumulative share of opportunities", title="ECDF: challenged vs unchallenged", xlim=(0, 2))
        ax[1].legend(loc="lower right")
        savefig(fig, "fig01_value_distribution.png")
        fig, ax = plt.subplots(figsize=(6, 5))
        for g, col, lab in (("ALL", INK, "All"), ("OFFENSE", BLUE, "Offense"), ("DEFENSE", ORANGE, "Defense")):
            s = np.sort(groups[g].v)[::-1]; cum = np.cumsum(s) / s.sum(); x = np.arange(1, len(s) + 1) / len(s)
            ax.plot(x, cum, color=col, label=lab)
        ax.plot([0, 1], [0, 1], color=GRID, lw=1, ls="--")
        for top in (.1, .2):
            s = np.sort(groups["ALL"].v)[::-1]; k = int(len(s) * top)
            ax.annotate(f"top {int(top*100)}% = {s[:k].sum()/s.sum():.0%} of value", (top, s[:k].sum() / s.sum()), xytext=(top + .12, s[:k].sum() / s.sum() - .12),
                        color=INK2, arrowprops=dict(arrowstyle="-", color=INK2, lw=.8))
        ax.set(xlabel="Share of opportunities (highest value first)", ylabel="Share of total correctable value", title="Concentration of correctable value")
        ax.legend(loc="lower right")
        savefig(fig, "fig02_value_concentration.png")
    return dist, ci, bycount


def gini(v):
    v = np.sort(np.clip(v, 0, None)); n = len(v)
    return float((2 * np.arange(1, n + 1) - n - 1).dot(v) / (n * v.sum()))


# ============================================================ ANALYSIS 2
def analysis2(o, vcol, tag="primary", figs=True):
    d = o[o[vcol].notna()].copy(); d["v"] = d[vcol]; d["v4"] = d.v / 0.25
    d["vbin"] = pd.cut(d.v, VALUE_BINS, labels=VALUE_LABELS)
    desc = []
    for keys in (["side", "inv"], ["side", "vbin", "inv"], ["side", "inning_bucket", "inv"], ["vbin", "inv"], ["side", "terminal", "inv"]):
        for k, g in d.groupby(keys, observed=True):
            k = k if isinstance(k, tuple) else (k,)
            lo, hi = wilson(int(g.challenged.sum()), len(g))
            desc.append({"spec": tag, "table": "+".join(keys), **dict(zip(keys, [str(x) for x in k])), "n": len(g),
                         "challenged": int(g.challenged.sum()), "rate": g.challenged.mean(), "ci_low": lo, "ci_high": hi,
                         "mean_value": g.v.mean(), "mean_dist_in": g.abs_distance_inches.mean()})
    desc = pd.DataFrame(desc)
    models, rows = {}, []
    specs = {
        "A_value_state": f"C(inv1) * v4 + {CONTROLS} + terminal",
        "B_full_state_fe": f"C(inv1) * v4 + {CONTROLS} + C(count) + C(outs) + C(base_state)",
        "A_no_interaction": f"C(inv1) + v4 + {CONTROLS} + terminal",
    }
    for name, f in specs.items():
        r, dd = fit_logit(d, f); models[name] = (r, dd)
        rows += or_table(r, name, keep=["inv1", "v4", "terminal", "late_close", "side", "inning_bucket"])
    # Offense with held-out recognition probability (no March)
    off = d[d.side.eq("OFFENSE") & d.logit_er.notna()]
    r, dd = fit_logit(off, "C(inv1) * v4 + logit_er + C(inning_bucket) + C(score_state) + late_close_i + bs(dist, df=4) + terminal")
    models["C_offense_heldout_recognition"] = (r, dd)
    rows += or_table(r, "C_offense_heldout_recognition", keep=["inv1", "v4", "logit_er", "terminal"])
    for side in ("OFFENSE", "DEFENSE"):
        r, dd = fit_logit(d[d.side.eq(side)], f"C(inv1) * v4 + C(inning_bucket) + C(score_state) + late_close_i + bs(dist, df=4) + terminal")
        models[f"A_{side.lower()}_only"] = (r, dd)
        rows += or_table(r, f"A_{side.lower()}_only", keep=["inv1", "v4"])
    coefs = pd.DataFrame(rows); coefs.insert(0, "spec", tag)
    # Marginal inventory effect at chosen values (model A), via average predictions
    r, dd = models["A_value_state"]
    marg = []
    for val in (0.10, 0.25, 0.50, 0.75, 1.00):
        x = dd.copy(); x["v4"] = val / .25
        p1 = r.predict(x.assign(inv1=1)).mean(); p2 = r.predict(x.assign(inv1=0)).mean()
        marg.append({"spec": tag, "model": "A_value_state", "value_runs": val, "pred_rate_inv2": p2, "pred_rate_inv1": p1,
                     "difference_inv1_minus_inv2": p1 - p2, "ratio_inv1_over_inv2": p1 / p2})
    marg = pd.DataFrame(marg)
    # bootstrap (game clusters) for the marginal difference at the median value, model A
    cal = calibration(r, dd, "A_value_state")
    if figs:
        fig, ax = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
        for i, side in enumerate(("OFFENSE", "DEFENSE")):
            t = desc[(desc.table == "side+vbin+inv") & (desc.side == side)]
            for inv, col, off_x in (("2", BLUE, -.08), ("1", ORANGE, .08)):
                q = t[t.inv == inv]; x = np.arange(len(q)) + off_x
                ax[i].errorbar(x, q.rate, yerr=[q.rate - q.ci_low, q.ci_high - q.rate], fmt="o-", color=col, ms=6, capsize=0,
                               label=f"{inv} challenge{'s' if inv == '2' else ''} left")
                for xx, rr, nn in zip(x, q.rate, q.n):
                    ax[i].annotate(f"n={nn}", (xx, rr), xytext=(4, -12 if inv == "1" else 6), textcoords="offset points", fontsize=7, color=INK2)
            ax[i].set_xticks(range(len(VALUE_LABELS))); ax[i].set_xticklabels(VALUE_LABELS)
            ax[i].set(title=f"{side.title()}: challenge rate by value and inventory", xlabel="Correction value (runs)")
        ax[0].set_ylabel("Share challenged (95% Wilson CI)"); ax[0].legend(loc="upper left")
        savefig(fig, "fig04_inventory_by_value.png")
        fig, ax = plt.subplots(figsize=(8, 4.2))
        for side, col in (("OFFENSE", BLUE), ("DEFENSE", ORANGE)):
            x = d[d.side.eq(side)]
            b = pd.qcut(x.v.rank(method="first"), 20, labels=False)
            t = x.groupby(b).agg(v=("v", "mean"), r=("challenged", "mean"))
            ax.plot(t.v, t.r, "o-", color=col, ms=5, label=side.title())
        ax.set(xscale="log", xlabel="Correction value (runs, log scale; 20 equal-count bins)", ylabel="Share challenged",
               title="Challenge rate vs immediate correction value")
        ax.legend()
        savefig(fig, "fig03_challenge_rate_vs_value.png")
        fig, ax = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
        for i, side in enumerate(("OFFENSE", "DEFENSE")):
            x = d[d.side.eq(side)]
            for inv, col in ((2, BLUE), (1, ORANGE)):
                t = x[x.inv == inv].groupby("inning_c").agg(r=("challenged", "mean"), n=("challenged", "size"))
                t = t[t.n >= 30]
                ax[i].plot(t.index, t.r, "o-", color=col, ms=5, label=f"{inv} left")
            ax[i].set(title=f"{side.title()}: challenge rate by inning", xlabel="Inning (10 = extras)")
        ax[0].set_ylabel("Share challenged"); ax[0].legend()
        savefig(fig, "fig05_inning_inventory.png")
    return desc, coefs, marg, cal, models


# ============================================================ ANALYSIS 3 (HINDSIGHT)
def analysis3(o, allinc, seq, vcol, tag="primary", figs=True):
    """RETROSPECTIVE / HINDSIGHT ONLY: uses later events in the same game."""
    vmap = allinc.set_index("pitch_key")[vcol]
    s = seq.sort_values(["team_game_id", "sequence_number"]).copy()
    s["v"] = s.pitch_key.map(vmap)
    s["elig"] = s.sequence_event_class.eq("ELIGIBLE_INCORRECT_CALL")
    s["exh"] = s.sequence_event_class.eq("INELIGIBLE_INCORRECT_CALL_EXHAUSTED")
    s["realized"] = np.where(s.exercised & s.challenge_outcome.eq("OVERTURNED") & s.v.notna(), s.v, np.where(s.exercised, 0.0, np.nan))
    final_inv = s.groupby("team_game_id").inventory_after.last()
    rows = []
    for tg, g in s.groupby("team_game_id", sort=False):
        v = g.v.to_numpy(); e = g.elig.to_numpy(); x = g.exercised.to_numpy(); ex = g.exh.to_numpy(); rv = g.realized.to_numpy()
        for i in np.flatnonzero(e):
            if not np.isfinite(v[i]):
                continue
            later = np.arange(i + 1, len(g)); le = later[e[later]]; lv = v[le]; lvf = lv[np.isfinite(lv)]
            lx = later[x[later]]
            first_use = lx[0] if len(lx) else None
            rows.append({"team_game_id": tg, "pitch_key": g.pitch_key.iat[i], "hs_later_eligible_n": len(le),
                         "hs_later_max_value": lvf.max() if len(lvf) else np.nan,
                         "hs_later_exceeds": bool(len(lvf) and (lvf > v[i]).any()),
                         "hs_later_exceeds_and_challenged": bool(any(np.isfinite(v[j]) and v[j] > v[i] and x[j] for j in le)),
                         "hs_later_exceeds_while_exhausted": bool(any(np.isfinite(v[j]) and v[j] > v[i] for j in later[ex[later]])),
                         "hs_team_used_later": len(lx) > 0,
                         "hs_first_later_challenge_value": rv[first_use] if first_use is not None else np.nan,
                         "hs_later_realized_sum": np.nansum(rv[later]) if len(later) else 0.0,
                         "hs_game_ended_with_unused": final_inv[tg] > 0})
    h = pd.DataFrame(rows)
    d = o[["pitch_key", "side", "inning", "inning_bucket", "inv", "challenged", "entitled_team", "early"]].merge(h, on="pitch_key")
    d["v"] = d.pitch_key.map(vmap); d["vbin"] = pd.cut(d.v, VALUE_BINS, labels=VALUE_LABELS)
    out = []
    def summarize(x, **keys):
        return {"spec": tag, **keys, "n": len(x), "pct_any_later_eligible": (x.hs_later_eligible_n > 0).mean(),
                "mean_later_eligible_n": x.hs_later_eligible_n.mean(), "median_later_max_value": x.hs_later_max_value.median(),
                "pct_later_more_valuable": x.hs_later_exceeds.mean(), "pct_later_more_valuable_and_challenged": x.hs_later_exceeds_and_challenged.mean(),
                "pct_later_more_valuable_while_exhausted": x.hs_later_exceeds_while_exhausted.mean(),
                "pct_team_used_a_challenge_later": x.hs_team_used_later.mean(),
                "mean_first_later_challenge_value": x.hs_first_later_challenge_value.mean(),
                "pct_game_ended_with_unused_inventory": x.hs_game_ended_with_unused.mean(), "mean_passed_value": x.v.mean()}
    for chal, lab in ((False, "PASSED"), (True, "CHALLENGED")):
        x = d[d.challenged == chal]
        out.append(summarize(x, decision=lab, cut="ALL"))
        for keys in (["inning_bucket"], ["vbin"], ["inv"], ["side"], ["side", "inning_bucket"], ["inning_bucket", "vbin"]):
            for k, g in x.groupby(keys, observed=True):
                k = k if isinstance(k, tuple) else (k,)
                out.append(summarize(g, decision=lab, cut="+".join(keys), **{kk: str(vv) for kk, vv in zip(keys, k)}))
        for t in (0.25, 0.50, 0.75):
            for early_lab, em in (("innings_1_3", x.inning.le(3)), ("innings_1_6", x.inning.le(6)), ("innings_7_plus", x.inning.ge(7))):
                g = x[em & (x.v >= t)]
                out.append(summarize(g, decision=lab, cut=f"value_ge_{t:.2f}+{early_lab}"))
    hs = pd.DataFrame(out)
    # team-game level: passed a meaningful opportunity and finished with unused inventory
    tg = []
    passed = d[~d.challenged]
    ngames = seq.team_game_id.nunique()
    all_tg = pd.Series(final_inv)
    for t in (0.25, 0.50, 0.75):
        p = passed[passed.v >= t]
        games = p.groupby("team_game_id").hs_game_ended_with_unused.first()
        early_games = p[p.inning.le(3)].groupby("team_game_id").hs_game_ended_with_unused.first()
        tg.append({"spec": tag, "threshold": t, "team_games_in_sequences": ngames,
                   "team_games_passing_meaningful": len(games), "of_which_ended_with_unused": int(games.sum()),
                   "pct_ended_with_unused": games.mean(),
                   "team_games_passing_meaningful_innings_1_3": len(early_games), "of_which_ended_with_unused_early": int(early_games.sum()),
                   "pct_ended_with_unused_early": early_games.mean(),
                   "all_team_games_ending_with_unused_pct": (all_tg > 0).mean()})
    tgdf = pd.DataFrame(tg)
    team = passed[passed.v >= .5].groupby("entitled_team").agg(n=("v", "size"), pct_later_more_valuable=("hs_later_exceeds", "mean"),
                                                                pct_ended_unused=("hs_game_ended_with_unused", "mean")).reset_index()
    team["spec"] = tag
    if figs:
        fig, ax = plt.subplots(figsize=(8, 4.2))
        x = hs[(hs.decision == "PASSED") & (hs.cut == "inning_bucket+vbin")]
        for vb, col in (("0.25-0.50", AQUA), ("0.50-0.75", BLUE), (">=0.75", ORANGE)):
            q = x[x.vbin == vb].set_index("inning_bucket").reindex(["1-3", "4-6", "7-9"])
            q = q.where(q.n >= 20)
            ax.plot(range(3), q.pct_later_more_valuable, "o-", color=col, label=f"passed value {vb}: later more valuable")
            ax.plot(range(3), q.pct_game_ended_with_unused_inventory, "o--", color=col, alpha=.6, label=f"passed value {vb}: game ended unused")
        ax.set_xticks(range(3)); ax.set_xticklabels(["1-3", "4-6", "7-9"])
        ax.set(xlabel="Inning of the passed opportunity (cells n>=20; extras omitted)", ylabel="Share of passed opportunities", ylim=(0, 1),
               title="HINDSIGHT: what happened after a meaningful opportunity was passed")
        ax.legend(fontsize=7, loc="center right", ncol=1)
        savefig(fig, "fig09_hindsight_later_value.png")
    return hs, tgdf, team, d


# ============================================================ ANALYSIS 4
def analysis4(o, seq, vcol, tag="primary", figs=True):
    d = o[o[vcol].notna()].copy(); d["v"] = d[vcol]; d["v4"] = d.v / .25
    s = seq.copy()
    allc = s[s.exercised].groupby("entitled_team").agg(all_challenges=("exercised", "size"),
                                                      all_overturned=("challenge_outcome", lambda x: (x == "OVERTURNED").sum()),
                                                      challenges_of_geometry_correct_calls=("sequence_event_class", lambda x: (x == "CHALLENGE_OF_GEOMETRY_CORRECT_CALL").sum()))
    raw = d.groupby("entitled_team").agg(opportunities=("v", "size"), challenges=("challenged", "sum"), rate=("challenged", "mean"),
                                         value_encountered=("v", "sum"), value_recovered=("challenge_value_runs_p", "sum"),
                                         value_unchallenged=("missed_p", "sum"), mean_dist=("abs_distance_inches", "mean")).join(allc)
    raw["value_capture_ratio"] = raw.value_recovered / raw.value_encountered
    raw["all_challenge_success_rate"] = raw.all_overturned / raw.all_challenges
    splits = []
    for keys in (["side"], ["inning_bucket"], ["inv"]):
        for (team, k), g in d.groupby(["entitled_team"] + keys):
            splits.append({"entitled_team": team, "split": keys[0], "level": str(k), "n": len(g), "rate": g.challenged.mean(),
                           "value_capture_ratio": g.challenge_value_runs_p.sum() / g.v.sum()})
    splits = pd.DataFrame(splits)
    base = f"C(inv1) * v4 + {CONTROLS} + terminal"
    r0, d0 = fit_logit(d, base)
    r1, d1 = fit_logit(d, base + " + C(entitled_team, Sum)")
    lr = 2 * (r1.llf - r0.llf); df_ = len(r1.params) - len(r0.params)
    ll0 = grouped_cv_logloss(d, base); ll1 = grouped_cv_logloss(d, base + " + C(entitled_team, Sum)")
    teams = sorted(d.entitled_team.unique())
    # Sum coding: last team's effect = -sum(others); recover all with delta-method covariance
    names = [n for n in r1.params.index if n.startswith("C(entitled_team, Sum)")]
    b = r1.params[names].to_numpy(); V = r1.cov_params().loc[names, names].to_numpy()
    L = np.vstack([np.eye(len(names)), -np.ones(len(names))])
    eff = L @ b; se = np.sqrt(np.diag(L @ V @ L.T))
    adj = pd.DataFrame({"entitled_team": teams, "adj_log_odds_vs_league": eff, "se_cluster": se,
                        "adj_or_vs_league": np.exp(eff), "or_ci_low": np.exp(eff - 1.96 * se), "or_ci_high": np.exp(eff + 1.96 * se)})
    adj["z"] = adj.adj_log_odds_vs_league / adj.se_cluster
    adj["bonferroni_significant"] = adj.z.abs() > stats.norm.ppf(1 - .025 / len(adj))
    # expected (no-team model) vs observed challenges and value capture
    d0 = d0.assign(p=r0.predict(d0))
    oe = d0.groupby("entitled_team").agg(obs=("y", "sum"), exp=("p", "sum"), exp_recovered=("p", lambda x: np.nan))
    ev = d0.assign(ev=d0.p * d0.v).groupby("entitled_team").ev.sum()
    adj = adj.merge(raw.reset_index(), on="entitled_team").merge(oe[["obs", "exp"]].reset_index(), on="entitled_team")
    adj["obs_over_expected_challenges"] = adj.obs / adj.exp
    adj["expected_value_recovered_if_league_behavior"] = adj.entitled_team.map(ev)
    adj["value_recovered_over_expected"] = adj.value_recovered / adj.expected_value_recovered_if_league_behavior
    # between-team SD (method of moments on adjusted log-odds)
    tau2 = max(0.0, np.var(eff, ddof=1) - np.mean(se ** 2))
    # early-vs-late conservation screen: residual O-E by team in innings 1-3 vs 7+
    d0["early_bucket"] = np.select([d0.inning.le(3), d0.inning.ge(7)], ["EARLY", "LATE"], "MIDDLE")
    el = []
    for team, g in d0.groupby("entitled_team"):
        rec = {"entitled_team": team}
        for b_ in ("EARLY", "LATE"):
            x = g[g.early_bucket == b_]
            rec[f"{b_.lower()}_n"] = len(x); rec[f"{b_.lower()}_obs"] = x.y.sum(); rec[f"{b_.lower()}_exp"] = x.p.sum()
            rec[f"{b_.lower()}_var"] = (x.p * (1 - x.p)).sum()
        rec["early_o_minus_e_rate"] = (rec["early_obs"] - rec["early_exp"]) / rec["early_n"]
        rec["late_o_minus_e_rate"] = (rec["late_obs"] - rec["late_exp"]) / rec["late_n"]
        rec["early_minus_late"] = rec["early_o_minus_e_rate"] - rec["late_o_minus_e_rate"]
        rec["z_early_minus_late"] = rec["early_minus_late"] / np.sqrt(rec["early_var"] / rec["early_n"] ** 2 + rec["late_var"] / rec["late_n"] ** 2)
        el.append(rec)
    el = pd.DataFrame(el)
    el["early_late_bonferroni_significant"] = el.z_early_minus_late.abs() > stats.norm.ppf(1 - .025 / len(el))
    chi2 = float((el.z_early_minus_late ** 2).sum()); p_chi = float(stats.chi2.sf(chi2, len(el)))
    team_adj = adj.merge(el, on="entitled_team")
    team_adj.insert(0, "spec", tag)
    summary = {"lr_stat_team_block": lr, "lr_df": df_, "lr_p_naive": float(stats.chi2.sf(lr, df_)),
               "cv_logloss_no_team": ll0, "cv_logloss_with_team": ll1, "cv_delta_logloss": ll1 - ll0,
               "between_team_sd_log_odds": float(np.sqrt(tau2)), "teams_bonferroni_significant": int(adj.bonferroni_significant.sum()),
               "adj_or_range": [float(adj.adj_or_vs_league.min()), float(adj.adj_or_vs_league.max())],
               "early_late_chi2": chi2, "early_late_df": len(el), "early_late_p": p_chi,
               "early_late_teams_bonferroni": int(el.early_late_bonferroni_significant.sum()),
               "raw_rate_range": [float(raw.rate.min()), float(raw.rate.max())],
               "vcr_range": [float(raw.value_capture_ratio.min()), float(raw.value_capture_ratio.max())],
               "corr_raw_rate_vs_adj_or": float(np.corrcoef(adj.rate, adj.adj_or_vs_league)[0, 1])}
    if figs:
        t = team_adj.sort_values("adj_or_vs_league")
        fig, ax = plt.subplots(1, 2, figsize=(12, 8), sharey=True)
        y = np.arange(len(t))
        ax[0].errorbar(t.adj_or_vs_league, y, xerr=[t.adj_or_vs_league - t.or_ci_low, t.or_ci_high - t.adj_or_vs_league], fmt="o", color=BLUE, ms=5)
        ax[0].axvline(1, color=INK2, lw=1); ax[0].set_xscale("log")
        ax[0].set_xticks([0.5, 0.7, 1.0, 1.4, 2.0]); ax[0].set_xticklabels(["0.5", "0.7", "1.0", "1.4", "2.0"]); ax[0].minorticks_off()
        ax[0].set(yticks=y, yticklabels=t.entitled_team, xlabel="Adjusted challenge odds vs league (95% CI, game-clustered)",
                  title="Adjusted team challenge propensity")
        ax[1].errorbar(t.early_minus_late, y, xerr=1.96 * t.early_minus_late / t.z_early_minus_late.replace(0, np.nan), fmt="o", color=ORANGE, ms=5)
        ax[1].axvline(0, color=INK2, lw=1)
        ax[1].set(xlabel="(Obs - Exp rate) innings 1-3 minus innings 7+ (95% CI)", title="Early-vs-late residual (negative = relatively fewer early)")
        savefig(fig, "fig08_team_adjusted.png")
    return raw.reset_index(), splits, team_adj, summary


# ============================================================ ANALYSIS 5
def analysis5(o, seq, vcol, tag="primary", figs=True):
    d = o[o[vcol].notna()].copy(); d["v"] = d[vcol]
    rows = []
    side_all = seq[seq.exercised].assign(side=lambda x: x.opportunity_side).groupby("side").agg(
        all_challenges=("exercised", "size"), all_overturned=("challenge_outcome", lambda x: (x == "OVERTURNED").sum()))
    for side, g in d.groupby("side"):
        rows.append({"spec": tag, "side": side, "level": "ALL", "opportunities": len(g), "opportunities_per_team_game": len(g) / seq.team_game_id.nunique(),
                     "challenged": int(g.challenged.sum()), "challenge_rate": g.challenged.mean(),
                     "success_rate_eligible": (g.challenge_outcome == "OVERTURNED").sum() / g.challenged.sum(),
                     "all_challenges_including_correct_calls": int(side_all.loc[side, "all_challenges"]),
                     "success_rate_all_challenges": side_all.loc[side, "all_overturned"] / side_all.loc[side, "all_challenges"],
                     "mean_value": g.v.mean(), "median_value": g.v.median(), "p90_value": g.v.quantile(.9),
                     "total_value": g.v.sum(), "recovered_value": g.challenge_value_runs_p.sum(), "unchallenged_value": g.missed_p.sum(),
                     "value_capture_ratio": g.challenge_value_runs_p.sum() / g.v.sum(),
                     "mean_distance_in": g.abs_distance_inches.mean(), "pct_terminal_count": g.terminal.mean()})
        for key in ("inv", "inning_bucket", "terminal"):
            for k, x in g.groupby(key):
                lo, hi = wilson(int(x.challenged.sum()), len(x))
                rows.append({"spec": tag, "side": side, "level": f"{key}={k}", "opportunities": len(x), "challenged": int(x.challenged.sum()),
                             "challenge_rate": x.challenged.mean(), "rate_ci_low": lo, "rate_ci_high": hi, "mean_value": x.v.mean(),
                             "total_value": x.v.sum(), "recovered_value": x.challenge_value_runs_p.sum(),
                             "value_capture_ratio": x.challenge_value_runs_p.sum() / x.v.sum()})
    od = pd.DataFrame(rows)
    d["v4"] = d.v / .25
    r, dd = fit_logit(d, f"C(side) * v4 + C(inv1) + C(inning_bucket) + C(score_state) + late_close_i + bs(dist, df=4) + terminal")
    coefs = pd.DataFrame(or_table(r, "side_interaction", keep=["side", "v4"]))
    # distance-matched comparison: within 0.5-inch distance bins, which side challenges more?
    d["dbin"] = (d.abs_distance_inches // .5).clip(upper=12)
    m = d.groupby(["dbin", "side"]).challenged.agg(["mean", "size"]).unstack("side")
    if figs:
        fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
        t = d.groupby(["side", "dbin"]).challenged.agg(["mean", "size"]).reset_index()
        for side, col in (("OFFENSE", BLUE), ("DEFENSE", ORANGE)):
            q = t[(t.side == side) & (t["size"] >= 30)]
            ax[0].plot(q.dbin * .5 + .25, q["mean"], "o-", color=col, ms=5, label=side.title())
        ax[0].set(xlabel="Distance from ABS boundary (inches; outside for offense, inside for defense)", ylabel="Share challenged",
                  title="Challenge rate by miss distance")
        ax[0].legend()
        t = od[od.level.str.startswith("inning_bucket=")].copy(); t["ib"] = t.level.str.split("=").str[1]
        for side, col in (("OFFENSE", BLUE), ("DEFENSE", ORANGE)):
            q = t[t.side == side].set_index("ib").reindex(["1-3", "4-6", "7-9", "10+"])
            ax[1].plot(range(4), q.value_capture_ratio, "o-", color=col, label=side.title())
        ax[1].set_xticks(range(4)); ax[1].set_xticklabels(["1-3", "4-6", "7-9", "10+"])
        ax[1].set(xlabel="Inning", ylabel="Value capture ratio", title="Share of correctable value recovered")
        ax[1].legend()
        savefig(fig, "fig06_offense_defense.png")
    return od, coefs, m


# ============================================================ ANALYSIS 6
def analysis6(o, vcol, tag="primary", figs=True):
    d = o[o[vcol].notna()].copy(); d["v"] = d[vcol]; d["v4"] = d.v / .25
    d["lv"] = np.log(d.v.clip(lower=.01))
    rows, coefs = [], []
    # Offense: held-out recognition probability (April onward)
    off = d[d.side.eq("OFFENSE") & d.logit_er.notna()].copy()
    off["er_q"] = pd.qcut(off.expected_recognition_prob_temporal, 5, labels=[f"ER_Q{i}" for i in range(1, 6)])
    off["v_q"] = pd.qcut(off.v.rank(method="first"), 5, labels=[f"V_Q{i}" for i in range(1, 6)])
    for inv in ("ALL", 2, 1):
        x = off if inv == "ALL" else off[off.inv == inv]
        for (a, b), g in x.groupby(["er_q", "v_q"], observed=True):
            rows.append({"spec": tag, "side": "OFFENSE", "evidence_measure": "heldout_expected_recognition", "inventory": str(inv),
                         "evidence_bin": a, "value_bin": b, "n": len(g), "challenge_rate": g.challenged.mean(),
                         "evidence_mid": g.expected_recognition_prob_temporal.median(), "value_mid": g.v.median(), "mean_distance_in": g.abs_distance_inches.mean()})
    # Both sides: direct geometry
    for side in ("OFFENSE", "DEFENSE"):
        x0 = d[d.side == side].copy()
        x0["dist_q"] = pd.qcut(x0.abs_distance_inches.rank(method="first"), 5, labels=[f"D_Q{i}" for i in range(1, 6)])
        x0["v_q"] = pd.qcut(x0.v.rank(method="first"), 5, labels=[f"V_Q{i}" for i in range(1, 6)])
        for inv in ("ALL", 2, 1):
            x = x0 if inv == "ALL" else x0[x0.inv == inv]
            for (a, b), g in x.groupby(["dist_q", "v_q"], observed=True):
                rows.append({"spec": tag, "side": side, "evidence_measure": "boundary_distance", "inventory": str(inv),
                             "evidence_bin": a, "value_bin": b, "n": len(g), "challenge_rate": g.challenged.mean(),
                             "evidence_mid": g.abs_distance_inches.median(), "value_mid": g.v.median(), "mean_distance_in": g.abs_distance_inches.mean()})
    grid = pd.DataFrame(rows)
    # Continuous models
    r1, _ = fit_logit(off, "logit_er * lv + C(inv1) + C(inv1):lv + C(inning_bucket)")
    coefs += or_table(r1, "F1_offense_heldout_x_logvalue", keep=["logit_er", "lv", "inv1"])
    r2, _ = fit_logit(d, "C(side) * (bs(dist, df=4) + lv) + C(inv1) * lv + C(inning_bucket)")
    coefs += or_table(r2, "F2_distance_x_logvalue_both_sides", keep=["lv", "inv1"])
    r3, _ = fit_logit(d, "C(side) + dist + lv + dist:lv + C(inv1) + C(inning_bucket)")
    coefs += or_table(r3, "F3_linear_distance_x_logvalue", keep=["dist", "lv", "inv1"])
    # Recognition model already contains situation (count, inventory...).  Check its correlation with value.
    corr = {"spearman_heldout_er_vs_value_offense": float(stats.spearmanr(off.expected_recognition_prob_temporal, off.v).correlation),
            "spearman_distance_vs_value_offense": float(stats.spearmanr(d[d.side.eq("OFFENSE")].abs_distance_inches, d[d.side.eq("OFFENSE")].v).correlation),
            "spearman_distance_vs_value_defense": float(stats.spearmanr(d[d.side.eq("DEFENSE")].abs_distance_inches, d[d.side.eq("DEFENSE")].v).correlation)}
    if figs:
        fig, axs = plt.subplots(2, 3, figsize=(15, 10.5))
        panels = [("OFFENSE", "heldout_expected_recognition", "ALL"), ("OFFENSE", "boundary_distance", "ALL"), ("DEFENSE", "boundary_distance", "ALL"),
                  ("OFFENSE", "boundary_distance", "1"), ("OFFENSE", "boundary_distance", "2"), ("DEFENSE", "boundary_distance", "1")]
        for ax, (side, ev, inv) in zip(axs.ravel(), panels):
            t = grid[(grid.side == side) & (grid.evidence_measure == ev) & (grid.inventory == inv)]
            m = t.pivot(index="value_bin", columns="evidence_bin", values="challenge_rate")
            n = t.pivot(index="value_bin", columns="evidence_bin", values="n")
            im = ax.imshow(m.to_numpy(), origin="lower", cmap="Blues", vmin=0, vmax=.8, aspect="auto")
            for i in range(m.shape[0]):
                for j in range(m.shape[1]):
                    val = m.to_numpy()[i, j]
                    ax.text(j, i, f"{val:.0%}\nn={int(n.to_numpy()[i, j])}", ha="center", va="center", fontsize=7,
                            color="white" if val > .45 else INK)
            ax.set_xticks(range(m.shape[1])); ax.set_xticklabels([c.split("_")[-1] for c in m.columns])
            ax.set_yticks(range(m.shape[0])); ax.set_yticklabels([c.split("_")[-1] for c in m.index])
            ax.set(xlabel=("Held-out recognition quintile" if ev.startswith("held") else "Distance quintile") + " (low to high)",
                   ylabel="Correction value quintile", title=f"{side.title()}, inventory={inv}")
            ax.grid(False)
        fig.subplots_adjust(hspace=.38, wspace=.3, right=.86)
        fig.colorbar(im, ax=axs, shrink=.6, label="Share challenged")
        fig.suptitle("Decision frontier: evidence x consequence (quintiles for display only)")
        fig.savefig(FIG / "fig07_decision_frontier.png", facecolor=SURF); plt.close(fig)
    return grid, pd.DataFrame(coefs).assign(spec=tag), corr


# ============================================================ ANALYSIS 7
CA = ["ca_stolen_base_attempt", "ca_catcher_throw_any_evidence", "ca_runner_out", "ca_secondary_play_reviewed", "ca_any_secondary_action"]


def analysis7(o, vcol, tag="primary"):
    d = o[o[vcol].notna()].copy(); d["v"] = d[vcol]; d["v4"] = d.v / .25
    d["dbin"] = (d.abs_distance_inches // 1).clip(upper=8)
    rows = []
    for flag in CA:
        d["f"] = d[flag].astype(bool).astype(int)
        for side in ("ALL", "OFFENSE", "DEFENSE"):
            x = d if side == "ALL" else d[d.side == side]
            k1 = int(x.f.sum())
            row = {"spec": tag, "indicator": flag, "side": side, "n_flagged": k1, "rate_flagged": x.loc[x.f == 1, "challenged"].mean(),
                   "n_unflagged": int((x.f == 0).sum()), "rate_unflagged": x.loc[x.f == 0, "challenged"].mean()}
            # stratified (exact strata) comparison
            strata = ["side", "count", "outs", "base_state", "dbin", "inv"]
            g = x.groupby(strata)
            diffs, w = [], []
            for _, s in g:
                if s.f.nunique() == 2:
                    a = s[s.f == 1].challenged.mean(); b = s[s.f == 0].challenged.mean(); nf = (s.f == 1).sum()
                    diffs.append(a - b); w.append(nf)
            row["stratified_n_flagged_matched"] = int(np.sum(w)) if w else 0
            row["stratified_rate_difference"] = float(np.average(diffs, weights=w)) if w else np.nan
            if k1 >= 20:
                try:
                    r, _ = fit_logit(x, "f + v4 + bs(dist, df=4) + C(inv1) + C(inning_bucket) + terminal" + (" + C(side)" if side == "ALL" else ""))
                    ci = r.conf_int().loc["f"]
                    row.update(adj_or=np.exp(r.params["f"]), adj_or_ci_low=np.exp(ci[0]), adj_or_ci_high=np.exp(ci[1]), adj_p=r.pvalues["f"])
                except Exception as exc:  # noqa: BLE001
                    row["model_note"] = str(exc)[:80]
            rows.append(row)
    return pd.DataFrame(rows)


# ============================================================ ANALYSIS 8
def analysis8(o, re288):
    t = re288.set_index(["balls", "strikes", "outs", "base_state"])
    look = {c: t[c].to_dict() for c in ("re_count_pooled", "re_smoothed")}
    row = o[o.pitch_key.eq("824887:3:7")].iloc[0]
    res = {"pitch_key": "824887:3:7", "facts": {"game": "Mets at Braves, 2026-08-10, top 1st", "pre_pitch": "1 out, Bichette on 1st, 3-2 to Carson Benge",
                                                   "pitch": f"{row.signed_boundary_distance_inches:.2f} in (negative = inside the ABS zone) near the top edge",
                                                   "call": "ball four", "official_challenge": bool(row.challenged), "later": "Baty grand slam three batters later", "final": "NYM 8, ATL 5"},
           "not_in_sources": ["steal attempt", "catcher throw", "call at second", "attempted hat-tap challenge"]}
    for est, lk in look.items():
        obs = lk[(0, 0, 1, "110")]
        res[est] = {"RE_observed_walk": obs,
                    "recorded_no_runner_action": obs - lk[(0, 0, 2, "100")],
                    "bichette_safe_at_second": obs - lk[(0, 0, 2, "010")],
                    "bichette_out_inning_over": obs - 0.0}
    res["dataset_value_pooled"] = float(row[PRIMARY]); res["dataset_value_sprint5"] = float(row[OLD])
    res["realized_runs_rest_of_inning"] = 4
    res["note"] = "Realized runs are shown only to contrast with decision-point value; they are not the cost of the missed correction."
    return res


# ============================================================ ANALYSIS 9 core metrics
def core_metrics(o, allinc, seq, vcol, label, figs=False):
    x = o.copy()
    if True:  # recompute realized/missed values for the variant's value column
        x["challenge_value_runs_p"] = np.where(x.challenged & x.challenge_outcome.eq("OVERTURNED"), x[vcol], np.where(x.challenged, 0.0, np.nan))
        x["missed_p"] = np.where(~x.challenged, x[vcol], np.nan)
    dist, ci, _ = analysis1(x, vcol, label, figs=False)
    a = dist.set_index("group")
    m = {"n": int(a.loc["ALL", "n"]), "total_value": a.loc["ALL", "total_value_runs"], "mean": a.loc["ALL", "mean"], "median": a.loc["ALL", "median"],
         "top10_share": a.loc["ALL", "top10pct_value_share"], "top1_share": a.loc["ALL", "top1pct_value_share"],
         "pct_ge_0.50": a.loc["ALL", "pct_ge_0.50"],
         "recovered_share": (x.loc[x[vcol].notna(), "challenge_value_runs_p"].sum() / x[vcol].sum())}
    d = x[x[vcol].notna()].copy(); d["v"] = d[vcol]; d["v4"] = d.v / .25
    if d.side.nunique() > 1:
        r, dd = fit_logit(d, f"C(inv1) * v4 + {CONTROLS} + terminal")
    else:
        r, dd = fit_logit(d, "C(inv1) * v4 + C(inning_bucket) + C(score_state) + late_close_i + bs(dist, df=4) + terminal")
    ci_ = r.conf_int()
    for term, key in (("C(inv1)[T.1]", "inv1_or_at_zero_value"), ("v4", "value_or_per_0.25"), ("C(inv1)[T.1]:v4", "inv1_x_value_or")):
        m[key] = np.exp(r.params[term]); m[key + "_ci"] = [np.exp(ci_.loc[term, 0]), np.exp(ci_.loc[term, 1])]
    xx = dd.copy(); med = float(np.median(dd.v4))
    xx["v4"] = med
    m["inv1_minus_inv2_rate_at_median_value"] = r.predict(xx.assign(inv1=1)).mean() - r.predict(xx.assign(inv1=0)).mean()
    xx["v4"] = 2.0
    m["inv1_minus_inv2_rate_at_0.50"] = r.predict(xx.assign(inv1=1)).mean() - r.predict(xx.assign(inv1=0)).mean()
    if d.side.nunique() > 1:
        m["defense_vs_offense_adj_or"] = np.exp(r.params["C(side)[T.OFFENSE]"]) ** -1
    hs, tg, _, _ = analysis3(x, allinc, seq, vcol, label, figs=False)
    q = hs[(hs.decision == "PASSED") & (hs.cut == "value_ge_0.50+innings_1_3")]
    m["hindsight_early_ge0.50_later_more_valuable"] = float(q.pct_later_more_valuable.iloc[0]) if len(q) else np.nan
    m["hindsight_early_ge0.50_n"] = int(q.n.iloc[0]) if len(q) else 0
    m["hindsight_ge0.50_games_ended_unused"] = float(tg.loc[tg.threshold == .5, "pct_ended_with_unused"].iloc[0])
    return m


# ============================================================================ main
def main(out: Path):
    global OUT, FIG
    OUT, FIG = out, out / "figures"
    FIG.mkdir(parents=True, exist_ok=True)
    root = A4.parents[1]
    sys.path.insert(0, str(A4))
    from build import protected_files  # noqa: E402
    protected = protected_files(root) + sorted((A4 / "output").glob("*.csv")) + [A4 / "output/manifest.json"]
    before = {str(p.relative_to(root)): digest(p) for p in protected}
    manifest = json.loads((A4 / "output/manifest.json").read_text())
    o, allinc, seq, re288 = load()
    # Input reconciliation
    rec = {"opportunities": len(o), "offense": int(o.side.eq("OFFENSE").sum()), "defense": int(o.side.eq("DEFENSE").sum()),
           "offense_challenged": int(o[o.side.eq("OFFENSE")].challenged.sum()), "defense_challenged": int(o[o.side.eq("DEFENSE")].challenged.sum()),
           "primary_value_missing": int(o[PRIMARY].isna().sum()), "ambiguous": int(o.ambiguous.sum()),
           "primary_negative_values": int((o[PRIMARY] < 0).sum()), "sprint5_negative_values": int((o[OLD] < 0).sum()),
           "sequence_rows": len(seq), "sequence_challenges": int(seq.exercised.sum()),
           "input_hashes_match_article4_manifest": all(digest(A4 / "output" / f) == v["sha256"] for f, v in manifest["outputs"].items() if (A4 / "output" / f).exists())}
    assert rec["offense"] == 10755 and rec["offense_challenged"] == 2112 and rec["defense"] == 9409 and rec["defense_challenged"] == 2986, rec
    assert rec["primary_negative_values"] == 0 and rec["primary_value_missing"] == rec["ambiguous"] == 40, rec
    assert rec["input_hashes_match_article4_manifest"], "Article 4 dataset changed since validation"
    o["challenge_value_runs_p"] = np.where(o.challenged & o.challenge_outcome.eq("OVERTURNED"), o[PRIMARY], np.where(o.challenged, 0.0, np.nan))
    o["missed_p"] = np.where(~o.challenged, o[PRIMARY], np.nan)
    S = {"reconciliation": rec}

    # 1
    dist, ci, bycount = analysis1(o, PRIMARY)
    write_csv(pd.concat([dist.assign(table="distribution"), bycount.assign(table="by_count", spec="primary")], ignore_index=True), "article4_value_distribution.csv")
    S["value_distribution"] = {"by_group": dist.set_index("group").to_dict("index"), "bootstrap_all": ci,
                               "top_counts_by_value_share": bycount.sort_values("share_of_side_value", ascending=False).groupby("side").head(4).to_dict("records")}
    # 2
    desc, coefs, marg, cal, models = analysis2(o, PRIMARY)
    write_csv(pd.concat([desc.assign(section="descriptive"), coefs.assign(section="model_odds_ratios"),
                         marg.assign(section="marginal_inventory_effect"), cal.assign(section="calibration_model_A", spec="primary")], ignore_index=True),
              "article4_inventory_analysis.csv")
    S["inventory"] = {"odds_ratios": coefs.to_dict("records"), "marginal": marg.to_dict("records"),
                      "calibration_A": cal.to_dict("records"),
                      "overall_rates": desc[desc.table == "side+inv"].to_dict("records")}
    # 3
    hs, tg, team_hs, hsd = analysis3(o, allinc, seq, PRIMARY)
    write_csv(pd.concat([hs.assign(section="HINDSIGHT_opportunity_level"), tg.assign(section="HINDSIGHT_team_game_unused"),
                         team_hs.assign(section="HINDSIGHT_team_passed_ge_0.50")], ignore_index=True), "article4_hindsight_conservation.csv")
    S["hindsight"] = {"LABEL": "RETROSPECTIVE / HINDSIGHT - not decision-time information",
                      "passed_all": hs[(hs.decision == "PASSED") & (hs.cut == "ALL")].to_dict("records"),
                      "challenged_all": hs[(hs.decision == "CHALLENGED") & (hs.cut == "ALL")].to_dict("records"),
                      "early_thresholds": hs[hs.cut.str.startswith("value_ge")].to_dict("records"),
                      "team_games_unused": tg.to_dict("records")}
    # 4
    raw, splits, team_adj, tsum = analysis4(o, seq, PRIMARY)
    write_csv(pd.concat([team_adj.assign(section="team_adjusted"), splits.assign(section="raw_splits", spec="primary")], ignore_index=True), "article4_team_adjusted.csv")
    S["teams"] = tsum
    # 5
    od, odc, odm = analysis5(o, seq, PRIMARY)
    write_csv(pd.concat([od.assign(section="side_summary"), odc.assign(section="side_model", spec="primary")], ignore_index=True), "article4_offense_defense.csv")
    S["offense_defense"] = {"summary": od[od.level == "ALL"].to_dict("records"), "model": odc.to_dict("records")}
    # 6
    grid, fco, corr = analysis6(o, PRIMARY)
    write_csv(pd.concat([grid.assign(section="binned_surface"), fco.assign(section="continuous_models")], ignore_index=True), "article4_decision_frontier.csv")
    S["frontier"] = {"models": fco.to_dict("records"), "correlations": corr}
    # 7
    ca = analysis7(o, PRIMARY)
    write_csv(ca, "article4_competing_attention_analysis.csv")
    S["competing_attention"] = ca.to_dict("records")
    # 8
    br = analysis8(o, re288)
    (OUT / "article4_braves_case_exploratory.json").write_text(json.dumps(br, indent=2, default=jdefault) + "\n")
    S["braves"] = br
    # 9 sensitivity
    variants = {
        "PRIMARY_pooled": (o, PRIMARY),
        "SPRINT5_smoothing": (o, OLD),
        "ambiguous_included_at_sprint5_bound_midpoint": (o.assign(**{PRIMARY: o[PRIMARY].fillna((o.correction_value_runs_lower + o.correction_value_runs_upper) / 2)}), PRIMARY),
        "exclude_unrecorded_runner_action_possible": (o[~o.cf_unrecorded_runner_action_possible.astype(bool)], PRIMARY),
        "offense_only": (o[o.side.eq("OFFENSE")], PRIMARY),
        "defense_only": (o[o.side.eq("DEFENSE")], PRIMARY),
        f"exclude_value_below_{LOW_VALUE_CUT}": (o[o[PRIMARY] >= LOW_VALUE_CUT], PRIMARY),
        "exclude_82_sprint5_negative_rows": (o[~o.re_ordering_violation.astype(bool)], PRIMARY),
    }
    allinc_mid = allinc.copy()
    allinc_mid[PRIMARY] = allinc_mid[PRIMARY].fillna((allinc_mid.correction_value_runs_lower + allinc_mid.correction_value_runs_upper) / 2)
    sens = {}
    for name, (x, vcol) in variants.items():
        ai = allinc_mid if name.startswith("ambiguous") else allinc
        sens[name] = core_metrics(x, ai, seq, vcol, name)
    base = sens["PRIMARY_pooled"]
    srows = []
    for name, m in sens.items():
        for k, v in m.items():
            if isinstance(v, list):
                continue
            b = base.get(k)
            status = classify(k, b, v, m.get(k + "_ci"), base.get(k + "_ci")) if name != "PRIMARY_pooled" else "REFERENCE"
            srows.append({"variant": name, "metric": k, "value": v, "primary_value": b, "status": status,
                          "ci_low": (m.get(k + "_ci") or [np.nan, np.nan])[0], "ci_high": (m.get(k + "_ci") or [np.nan, np.nan])[1]})
    sens_df = pd.DataFrame(srows)
    write_csv(sens_df, "article4_sensitivity.csv")
    S["sensitivity"] = sens
    # 10 unexpected-findings support tables
    S["unexpected"] = unexpected(o, seq)
    # Validation
    after = {str(p.relative_to(root)): digest(p) for p in protected}
    val = validation(o, seq, models, rec, before, after, manifest, sens_df)
    S["validation"] = val
    (OUT / "article4_exploratory_summary.json").write_text(json.dumps(S, indent=1, default=jdefault, sort_keys=True) + "\n")
    write_validation_md(val, rec, sens_df)
    if before != after:
        raise RuntimeError("STOP: protected inputs changed")
    print(json.dumps({"reconciliation": rec, "teams": tsum}, indent=1, default=jdefault))


def classify(metric, base, v, ci, base_ci):
    """UNCHANGED_NULL_IN_BOTH: odds ratio whose 95% CI includes 1 in both specifications.
    UNCHANGED: same sign and within 10% relative (or 0.01 absolute for shares/rates).
    DIRECTIONAL: same sign, larger difference.  MATERIAL: sign change or CI-based significance status flips."""
    if base is None or v is None or not np.isfinite(base) or not np.isfinite(v):
        return "NOT_COMPUTED"
    ratio_metric = metric.endswith("_or") or "_or_" in metric or metric.endswith("or_per_0.25") or "adj_or" in metric
    if ratio_metric:
        sb, sv = np.sign(np.log(base)), np.sign(np.log(v))
    else:
        sb, sv = np.sign(base), np.sign(v)
    if ci is not None and base_ci is not None:
        sig_b = not (base_ci[0] <= 1 <= base_ci[1]); sig_v = not (ci[0] <= 1 <= ci[1])
        if sig_b != sig_v:
            return "MATERIALLY_CHANGED"
        if not sig_b and not sig_v:
            return "UNCHANGED_NULL_IN_BOTH"
    if sb != sv and abs(base) > 1e-9:
        return "MATERIALLY_CHANGED"
    rel = abs(v - base) / abs(base) if abs(base) > 1e-9 else np.inf
    absdiff = abs(v - base)
    if rel <= .10 or (abs(base) < 1.5 and absdiff <= .01 and not ratio_metric):
        return "UNCHANGED"
    return "DIRECTIONALLY_UNCHANGED_MAGNITUDE_DIFFERS"


def unexpected(o, seq):
    d = o[o[PRIMARY].notna()].copy(); d["v"] = d[PRIMARY]
    u = {}
    # value by count concentration
    t = d.groupby("count").v.agg(["sum", "size"]); t = t / t.sum()
    u["share_value_3_2"] = float(t.loc["3-2", "sum"]); u["share_opps_3_2"] = float(t.loc["3-2", "size"])
    term = d.groupby("terminal").v.agg(["sum", "size"]); term = term / term.sum()
    u["share_value_terminal_counts"] = float(term.loc[1, "sum"]); u["share_opps_terminal_counts"] = float(term.loc[1, "size"])
    # failed challenges (geometry-correct calls) as a share of all challenges
    ch = seq[seq.exercised]
    u["challenges_total"] = len(ch); u["challenges_of_geometry_correct_calls"] = int(ch.sequence_event_class.eq("CHALLENGE_OF_GEOMETRY_CORRECT_CALL").sum())
    u["challenges_confirmed_total"] = int(ch.challenge_outcome.eq("CONFIRMED").sum())
    # inventory-1 rows: how did the team get to 1?
    d1 = d[d.inv == 1]
    u["inv1_share_by_inning_bucket"] = d1.inning_bucket.value_counts(normalize=True).to_dict()
    # high-value unchallenged share
    hv = d[d.v >= .5]
    u["challenge_rate_value_ge_0.50"] = float(hv.challenged.mean()); u["n_value_ge_0.50"] = len(hv)
    u["challenge_rate_value_lt_0.10"] = float(d[d.v < .1].challenged.mean())
    # terminal count challenge rates by side
    u["terminal_rates"] = d.groupby(["side", "terminal"]).challenged.mean().rename("rate").reset_index().to_dict("records")
    # distance by value: is there a geometry-consequence interaction in raw rates?
    d["near"] = d.abs_distance_inches < 1
    u["rate_near_lt1in_by_terminal"] = d.groupby(["side", "near", "terminal"]).challenged.agg(["mean", "size"]).reset_index().to_dict("records")
    # month trend
    u["monthly_rate"] = d.groupby(["side", "month"]).challenged.mean().rename("rate").reset_index().to_dict("records")
    # 2-strike offense vs 3-ball defense
    u["late_close_rates"] = d.groupby(["side", "late_close_i"]).challenged.mean().rename("rate").reset_index().to_dict("records")
    return u


def validation(o, seq, models, rec, before, after, manifest, sens_df):
    from fields import DECISION_TIME_FIELDS  # noqa: E402
    model_inputs = {"inv1": "challenge_inventory", "side": "opportunity_side", "inning_bucket": "inning_bucket", "score_state": "entitled_team_score_diff",
                    "late_close_i": "late_close", "dist": "abs_distance_inches", "terminal": "strike_three_or_ball_four_at_stake",
                    "count": "count", "outs": "outs", "base_state": "base_state", "logit_er": "expected_recognition_prob_temporal",
                    "entitled_team": "entitled_team"}
    decision_ok = {k: (v in DECISION_TIME_FIELDS or v in ("opportunity_side", "entitled_team", "abs_distance_inches", "expected_recognition_prob_temporal"))
                   for k, v in model_inputs.items()}
    hind_cols = [c for c in o.columns if c.startswith("hindsight_")]
    val = {"reconciliation": rec, "protected_inputs_unchanged": before == after, "protected_files": len(before),
           "article4_manifest_version": manifest["version"],
           "model_inputs_decision_time": decision_ok,
           "value_variable_note": "correction_value_runs_pooled is computed from the pre-pitch state and the pitch's own recorded outcome (the state at the moment a challenge must be requested) with a season-level RE table; it contains no later-game information.",
           "heldout_recognition_note": "expected_recognition_prob_temporal is an expanding-window prediction trained on earlier months only; March rows (391) have none and are excluded from recognition-based models.",
           "hindsight_fields_in_models": [c for c in hind_cols],
           "model_sizes": {k: int(v[0].nobs) for k, v in models.items()},
           "model_converged": {k: bool(v[0].converged) for k, v in models.items()},
           "min_cell_n_inventory_value_side": None,
           "python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "statsmodels": statsmodels.__version__,
           "scipy": scipy.__version__, "matplotlib": matplotlib.__version__, "seed": SEED,
           "input_sha256": {k: v for k, v in before.items() if k.startswith("research/article4/output")},
           "code_sha256": digest(Path(__file__))}
    return val


def write_validation_md(val, rec, sens_df):
    lines = ["# Article 4 exploratory analysis - validation", "", "Generated by `analyze.py`; do not hand-edit.", "",
             "## Inputs and reconciliation", "",
             f"- Article 4 dataset version: `{val['article4_manifest_version']}`; every input CSV hash equals the Article 4 manifest: **{rec['input_hashes_match_article4_manifest']}**.",
             f"- Opportunities: {rec['opportunities']:,} = offense {rec['offense']:,} ({rec['offense_challenged']:,} challenged) + defense {rec['defense']:,} ({rec['defense_challenged']:,} challenged). Asserted equal to the Article 4 validation counts.",
             f"- Primary (pooled-count) value missing only for the {rec['ambiguous']} AMBIGUOUS rows; negative primary values: {rec['primary_negative_values']}; negative Sprint 5-smoothing values: {rec['sprint5_negative_values']}.",
             f"- Team-game sequence rows: {rec['sequence_rows']:,}; challenges in sequences: {rec['sequence_challenges']:,}.",
             f"- Protected Articles 1-3 files and Article 4 outputs unchanged by this analysis: **{val['protected_inputs_unchanged']}** ({val['protected_files']} files hashed before/after).", "",
             "## Leakage audit", "",
             "Model inputs and their Article 4 timing class (all must be decision-time):", "", "| model term | source field | decision-time |", "|---|---|---|"]
    lines += [f"| {k} | | {v} |" for k, v in val["model_inputs_decision_time"].items()]
    lines += ["", f"- Hindsight fields used in any model: {val['hindsight_fields_in_models'] or 'none'} (hindsight quantities are recomputed only inside Analysis 3 and written with a HINDSIGHT label).",
              f"- {val['value_variable_note']}", f"- {val['heldout_recognition_note']}", "",
              "## Models", "", "| model | n | converged |", "|---|---|---|"]
    lines += [f"| {k} | {n:,} | {val['model_converged'][k]} |" for k, n in val["model_sizes"].items()]
    lines += ["", "All logistic models: binomial GLM, standard errors clustered by game (statsmodels `cov_type='cluster'`). Calibration of model A by predicted-probability decile is in `article4_inventory_analysis.csv` (section `calibration_model_A`).", "",
              "## Sensitivity status counts", "", "| variant | unchanged | unchanged (null in both) | directional | material | not computed |", "|---|---|---|---|---|---|"]
    for v, g in sens_df[sens_df.variant != "PRIMARY_pooled"].groupby("variant", sort=False):
        c = g.status.value_counts()
        lines.append(f"| {v} | {c.get('UNCHANGED', 0)} | {c.get('UNCHANGED_NULL_IN_BOTH', 0)} | {c.get('DIRECTIONALLY_UNCHANGED_MAGNITUDE_DIFFERS', 0)} | {c.get('MATERIALLY_CHANGED', 0)} | {c.get('NOT_COMPUTED', 0)} |")
    lines += ["", "## Reproducibility", "",
              f"- Python {val['python']}, pandas {val['pandas']}, numpy {val['numpy']}, statsmodels {val['statsmodels']}, scipy {val['scipy']}, matplotlib {val['matplotlib']}; seed {val['seed']}.",
              f"- analyze.py SHA-256 `{val['code_sha256']}`.", "- Input SHA-256 values are in `article4_exploratory_summary.json` under `validation.input_sha256`.",
              "- Two consecutive runs are compared byte-for-byte for CSV/JSON outputs (see the final report)."]
    (OUT / "VALIDATION_ANALYSIS.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=HERE / "output")
    main(ap.parse_args().output.resolve())
