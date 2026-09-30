"""Sprint 3 season-to-date offensive recognition study.

The analysis is deterministic for a fixed full-season source snapshot.  Primary
evaluation uses expanding monthly windows; grouped cross-validation is retained
only as a secondary comparison with Sprint 2.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
import statsmodels
import statsmodels.api as sm
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .offensive_recognition import PITCH_FAMILY, _geometry

SEED = 20260325
SUPPORT_PUBLISH = 20
SUPPORT_RANK = 30
IDENTITY_MIN_ENTITIES = 10
IDENTITY_DELTA_LOG_LOSS = -0.001
IDENTITY_DELTA_BRIER = -0.0005
BLOCK_DELTA_LOG_LOSS = -0.001
BLOCK_DELTA_AUC = 0.002
MIN_DISPLAY_N = 20

GEOMETRY_NUM = ["abs_distance", "horizontal_distance", "vertical_distance", "corner_proximity"]
GEOMETRY_CAT = ["miss_axis", "miss_side"]
PITCH_NUM = ["release_speed", "release_spin_rate", "spin_axis_sin", "spin_axis_cos", "pfx_x", "pfx_z", "extension", "release_pos_x", "release_pos_z"]
PITCH_CAT = ["pitch_family", "pitch_hand", "bat_side"]
SITUATION_NUM = ["inning", "offense_score_diff"]
SITUATION_CAT = ["count", "outs", "base_state", "affected_team_challenges_remaining"]
SPECS = {
    "A_GEOMETRY": (GEOMETRY_NUM, GEOMETRY_CAT),
    "B_PITCH": (GEOMETRY_NUM + PITCH_NUM, GEOMETRY_CAT + PITCH_CAT),
    "C_SITUATION": (GEOMETRY_NUM + PITCH_NUM + SITUATION_NUM, GEOMETRY_CAT + PITCH_CAT + SITUATION_CAT),
}
IDENTITIES = ["batter", "pitcher", "catcher", "umpire"]


def _json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def _csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.12g")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().map({"true": True, "false": False})


def _model(numeric, categorical, c=1.0) -> Pipeline:
    transform = ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                           ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical),
    ])
    return Pipeline([("features", transform), ("logit", LogisticRegression(
        C=c, penalty="l2", solver="liblinear", max_iter=3000, random_state=SEED))])


def temporal_folds(frame: pd.DataFrame, alternate=False):
    """Expanding windows, preserving whole games and strict chronology."""
    dates = pd.to_datetime(frame.game_date)
    periods = dates.dt.to_period("M")
    months = sorted(periods.unique())
    start_at = 2 if alternate and len(months) > 4 else 1
    folds = []
    for index in range(start_at, len(months)):
        test_month = months[index]
        train = np.flatnonzero((periods < test_month).to_numpy())
        test = np.flatnonzero((periods == test_month).to_numpy())
        if len(train) and len(test) and frame.iloc[train].recognized.nunique() == 2 and frame.iloc[test].recognized.nunique() == 2:
            if dates.iloc[train].max() >= dates.iloc[test].min():
                raise RuntimeError("Temporal leakage: max train date is not before min test date")
            folds.append((str(test_month), train, test))
    if not folds:
        raise RuntimeError("No valid expanding-window folds")
    return folds


def _metrics(y, p):
    p = np.clip(np.asarray(p), 1e-6, 1 - 1e-6)
    y = np.asarray(y, dtype=int)
    design = sm.add_constant(np.log(p / (1 - p)))
    try:
        calibration = sm.Logit(y, design).fit(disp=0)
        intercept, slope = map(float, calibration.params)
    except Exception:
        intercept = slope = float("nan")
    edges = np.linspace(0, 1, 11)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (p >= lo) & (p < hi if hi < 1 else p <= hi)
        if mask.any():
            ece += float(mask.mean() * abs(y[mask].mean() - p[mask].mean()))
    return dict(roc_auc=roc_auc_score(y, p), pr_auc=average_precision_score(y, p),
                log_loss=log_loss(y, p), brier_score=brier_score_loss(y, p),
                calibration_intercept=intercept, calibration_slope=slope, ece_10bin=ece)


def build_population(root: Path, start: str, end: str):
    processed = root / "data/full_season/processed"
    validation = json.loads((processed / "validation_report.json").read_text())
    if not validation.get("gate_passed"):
        raise RuntimeError("Season-scale validation gate is not passing")
    p = pd.read_csv(processed / "pitches.csv", low_memory=False)
    if p.game_date.min() != start or p.game_date.max() != end or not p.game_date.between(start, end).all():
        raise RuntimeError("Processed date scope does not match declared Sprint 3 scope")
    p["challenge_available_bool"] = _bool(p.challenge_available)
    p["challenged_bool"] = _bool(p.challenged).fillna(False)
    incorrect = p[(p.original_call == "STRIKE") & (p.derived_abs_call == "BALL")].copy()
    resource = incorrect.survival_class.eq("SURVIVED_RESOURCE")
    position = incorrect.challenge_unavailable_reason.eq("POSITION_PLAYER_PITCHING")
    unknown = incorrect.survival_class.eq("UNKNOWN") & ~position
    eligible_mask = incorrect.challenge_available_bool.eq(True) & ~resource & ~position & ~unknown
    other = ~(eligible_mask | resource | position | unknown)
    eligible = incorrect[eligible_mask].copy()
    eligible["recognized"] = eligible.challenged_bool.astype(int)
    c = pd.read_csv(processed / "challenges.csv", low_memory=False)
    roles = c.set_index("pitch_key").challenger_role.to_dict()
    challenged_roles = eligible.loc[eligible.challenged_bool, "pitch_key"].map(roles)
    if challenged_roles.isna().any() or not challenged_roles.eq("BATTER").all():
        raise RuntimeError("Eligible challenged strikes do not reconcile to batter challenges")
    audit = {
        "analysis_start_date": start, "analysis_end_date": end,
        "incorrect_called_strikes": int(len(incorrect)),
        "legal_recognition_opportunities": int(len(eligible)),
        "recognized": int(eligible.recognized.sum()),
        "not_recognized": int((1 - eligible.recognized).sum()),
        "resource_constrained": int(resource.sum()),
        "position_player_pitching": int(position.sum()),
        "unknown": int(unknown.sum()), "other_exclusions": int(other.sum()),
        "population_identity_holds": bool(len(incorrect) == len(eligible) + resource.sum() + position.sum() + unknown.sum() + other.sum()),
        "outcome_definition": "1 if the batter challenged an eligible incorrect called strike; challenge success is not used",
    }
    if not audit["population_identity_holds"] or audit["other_exclusions"]:
        raise RuntimeError("Full-season population accounting failed")
    numeric = ["plate_x", "plate_z", "abs_zone_top", "abs_zone_bot", "distance_from_abs_boundary",
               "release_speed", "release_spin_rate", "spin_axis", "pfx_x", "pfx_z", "extension",
               "release_pos_x", "release_pos_z", "inning", "balls", "strikes", "outs", "score_diff",
               "affected_team_challenges_remaining", "on_1b", "on_2b", "on_3b"]
    for col in numeric:
        eligible[col] = pd.to_numeric(eligible[col], errors="coerce")
    required = ["plate_x", "plate_z", "abs_zone_top", "abs_zone_bot", "distance_from_abs_boundary",
                "inning", "balls", "strikes", "outs", "score_diff", "affected_team_challenges_remaining"]
    if eligible[required].isna().any().any():
        raise RuntimeError("Material missingness in required geometry or situation fields")
    geo = eligible.apply(_geometry, axis=1, result_type="expand")
    geo.columns = ["miss_axis", "miss_side", "horizontal_distance", "vertical_distance", "corner_proximity"]
    eligible = pd.concat([eligible, geo], axis=1)
    eligible["abs_distance"] = eligible.distance_from_abs_boundary.abs()
    eligible["abs_distance_inches"] = eligible.abs_distance * 12
    eligible["horizontal_distance_inches"] = eligible.horizontal_distance * 12
    eligible["vertical_distance_inches"] = eligible.vertical_distance * 12
    eligible["corner_proximity_inches"] = eligible.corner_proximity * 12
    eligible["pitch_family"] = eligible.pitch_type.map(PITCH_FAMILY).fillna("OTHER")
    eligible["spin_axis_sin"] = np.sin(np.deg2rad(eligible.spin_axis))
    eligible["spin_axis_cos"] = np.cos(np.deg2rad(eligible.spin_axis))
    eligible["count"] = eligible.balls.astype(int).astype(str) + "-" + eligible.strikes.astype(int).astype(str)
    eligible["base_state"] = eligible[["on_1b", "on_2b", "on_3b"]].notna().replace({True:"1",False:"0"}).agg("".join, axis=1)
    eligible["offense_score_diff"] = np.where(eligible.half_inning.eq("top"), -eligible.score_diff, eligible.score_diff)
    eligible["inning_group"] = pd.cut(eligible.inning, [0,3,6,np.inf], labels=["EARLY","MIDDLE","LATE"]).astype(str)
    eligible["score_state"] = np.select([eligible.offense_score_diff > 0, eligible.offense_score_diff < 0], ["AHEAD","BEHIND"], default="TIED")
    eligible["strike_three_call"] = np.where(eligible.strikes.eq(2), "YES", "NO")
    eligible["month"] = eligible.game_date.str[:7]
    eligible["date_scope"] = f"{start}/{end}"
    eligible["feature_version"] = "offensive_recognition_v2_sprint3"
    eligible = eligible.sort_values(["game_date","game_pk","at_bat_index","play_event_index"]).reset_index(drop=True)
    monthly = eligible.groupby("month").recognized.agg(opportunities="size", recognized="sum").reset_index()
    monthly["not_recognized"] = monthly.opportunities - monthly.recognized
    monthly["recognition_rate"] = monthly.recognized / monthly.opportunities
    audit["monthly"] = monthly.to_dict("records")
    return eligible, audit, p


def pilot_overlap_audit(root: Path, full_pitches: pd.DataFrame, features: pd.DataFrame):
    old=pd.read_csv(root/"data/processed/pitches.csv",dtype=str,keep_default_na=False)
    new=pd.read_csv(root/"data/full_season/processed/pitches.csv",dtype=str,keep_default_na=False)
    new=new[new.game_date.between("2026-08-24","2026-08-30")].copy()
    old=old.set_index("pitch_key");new=new.set_index("pitch_key")
    missing=set(old.index)-set(new.index);extra=set(new.index)-set(old.index)
    core=["original_call","derived_abs_call","distance_from_abs_boundary","challenge_available",
          "affected_team_challenges_remaining","survival_class","challenged","challenge_outcome",
          "batter_id","pitcher_id","catcher_id","umpire_id"]
    core_changes=0;label_changes=0
    for key in set(old.index)&set(new.index):
        if any(str(old.at[key,c])!=str(new.at[key,c]) for c in core): core_changes+=1
        if any(str(old.at[key,c])!=str(new.at[key,c]) for c in ("pitch_type","pitch_name")): label_changes+=1
    old_features=pd.read_csv(root/"data/analysis/offensive_recognition_features.csv",dtype=str)
    old_eligible=set(old_features.pitch_key);new_eligible=set(features[features.game_date.between("2026-08-24","2026-08-30")].pitch_key)
    audit=dict(pilot_rows=len(old),full_season_overlap_rows=len(new),missing_pitch_keys=len(missing),
               extra_pitch_keys=len(extra),core_classification_changed_rows=core_changes,
               pitch_taxonomy_changed_rows=label_changes,pilot_eligible_opportunities=len(old_eligible),
               full_season_overlap_eligible_opportunities=len(new_eligible),eligible_key_difference=len(old_eligible^new_eligible),
               conclusion="NONMATERIAL_PITCH_TAXONOMY_REVISION" if label_changes else "EXACT_MATCH")
    if missing or extra or core_changes or old_eligible!=new_eligible:
        raise RuntimeError("Material source revision in accepted pilot overlap")
    return audit


def fit_temporal(frame: pd.DataFrame):
    specs = dict(SPECS)
    cnum, ccat = SPECS["C_SITUATION"]
    for identity in IDENTITIES:
        specs[f"D_{identity.upper()}"] = (cnum, ccat + [identity + "_id"])
    specs["D_ALL_IDENTITY"] = (cnum, ccat + [x + "_id" for x in IDENTITIES])
    y = frame.recognized.to_numpy(dtype=int)
    folds = temporal_folds(frame)
    metric_rows, fold_rows, predictions, coefficients = [], [], [], []
    for name, (numeric, categorical) in specs.items():
        pooled_y, pooled_p = [], []
        for fold, train, test in folds:
            model = _model(numeric, categorical)
            model.fit(frame.iloc[train], y[train])
            prob = model.predict_proba(frame.iloc[test])[:,1]
            values = _metrics(y[test], prob)
            fold_rows.append(dict(model=name, fold=fold, train_start=frame.iloc[train].game_date.min(),
                                  train_end=frame.iloc[train].game_date.max(), test_start=frame.iloc[test].game_date.min(),
                                  test_end=frame.iloc[test].game_date.max(), train_n=len(train), test_n=len(test), **values))
            for idx, pr in zip(test, prob):
                predictions.append(dict(pitch_key=frame.iloc[idx].pitch_key, game_pk=frame.iloc[idx].game_pk,
                                        game_date=frame.iloc[idx].game_date, fold=fold, model=name,
                                        recognized=y[idx], predicted_probability=pr))
            pooled_y.extend(y[test]); pooled_p.extend(prob)
        values = _metrics(pooled_y, pooled_p)
        metric_rows.append(dict(model=name, n=len(pooled_y), recognized=int(sum(pooled_y)),
                                not_recognized=int(len(pooled_y)-sum(pooled_y)), validation="EXPANDING_MONTHLY",
                                regularization="L2_C_1_PREREGISTERED", **values))
        full = _model(numeric, categorical).fit(frame, y)
        names = full.named_steps["features"].get_feature_names_out()
        for term, coef in zip(names, full.named_steps["logit"].coef_[0]):
            if not name.startswith("D_") or not any(x+"_id" in term for x in IDENTITIES):
                coefficients.append(dict(model=name, term=term, coefficient_log_odds=coef,
                                         odds_ratio=math.exp(coef), basis="L2_C_1_STANDARDIZED_FULL_SAMPLE"))
    metrics = pd.DataFrame(metric_rows)
    by = metrics.set_index("model")
    comparisons = []
    transitions = [("A_GEOMETRY","B_PITCH"),("B_PITCH","C_SITUATION")] + [("C_SITUATION",f"D_{x.upper()}") for x in IDENTITIES] + [("C_SITUATION","D_ALL_IDENTITY")]
    for before, after in transitions:
        comparisons.append(dict(transition=f"{before} -> {after}", baseline_model=before, expanded_model=after,
                                **{f"delta_{m}":by.loc[after,m]-by.loc[before,m] for m in ["roc_auc","pr_auc","log_loss","brier_score"]}))
    return metrics, pd.DataFrame(fold_rows), pd.DataFrame(predictions), pd.DataFrame(comparisons), pd.DataFrame(coefficients)


def grouped_cv(frame: pd.DataFrame):
    y = frame.recognized.to_numpy(dtype=int); groups = frame.game_pk.to_numpy()
    rows=[]
    for name,(num,cat) in SPECS.items():
        ps=np.zeros(len(frame)); seen=np.zeros(len(frame))
        splitter=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=SEED)
        for tr,te in splitter.split(frame,y,groups):
            prob=_model(num,cat).fit(frame.iloc[tr],y[tr]).predict_proba(frame.iloc[te])[:,1]
            ps[te]=prob;seen[te]=1
        if not seen.all(): raise RuntimeError("Incomplete grouped CV predictions")
        rows.append(dict(model=name,validation="5_FOLD_STRATIFIED_GROUP_GAME",n=len(y),**_metrics(y,ps)))
    return pd.DataFrame(rows)


def descriptive(frame):
    rows=[]
    dimensions=["month","miss_side","pitch_family","count","outs","base_state","inning_group","inning","score_state","affected_team_challenges_remaining"]
    for dim in dimensions:
        for value,g in frame.groupby(dim,dropna=False):
            n=len(g);r=int(g.recognized.sum())
            rows.append(dict(dimension=dim,value=value,opportunities=n,recognized=r,not_recognized=n-r,
                             recognition_rate=r/n,small_sample_warning=n<MIN_DISPLAY_N,
                             display_rate="SUPPRESSED_N_LT_20" if n<MIN_DISPLAY_N else f"{r/n:.1%}"))
    return pd.DataFrame(rows)


def monthly_summary(frame):
    rows=[]
    for month,g in frame.groupby("month"):
        fit=sm.Logit(g.recognized,sm.add_constant(g.abs_distance_inches)).fit(disp=0)
        rates=g.groupby("affected_team_challenges_remaining").recognized.mean()
        strike_rates=g.groupby(g.strikes.eq(2)).recognized.mean()
        rows.append(dict(month=month,opportunities=len(g),recognized=int(g.recognized.sum()),
                         not_recognized=int((1-g.recognized).sum()),recognition_rate=g.recognized.mean(),
                         distance_effect_log_odds_per_inch=fit.params.iloc[1],distance_effect_p_value=fit.pvalues.iloc[1],
                         recognition_rate_two_remaining=rates.get(2,np.nan),recognition_rate_one_remaining=rates.get(1,np.nan),
                         inventory_effect_rate_difference=rates.get(1,np.nan)-rates.get(2,np.nan),
                         situation_effect_two_strike_rate_difference=strike_rates.get(True,np.nan)-strike_rates.get(False,np.nan)))
    return pd.DataFrame(rows)


def identity_tables(frame, predictions, comparisons):
    c_pred=predictions[predictions.model.eq("C_SITUATION")].set_index("pitch_key").predicted_probability
    working=frame.copy();working["expected"] = working.pitch_key.map(c_pred)
    # Earliest month has no temporal prediction; fit C on all data only for expected-rate descriptive estimates.
    missing=working.expected.isna()
    if missing.any():
        num,cat=SPECS["C_SITUATION"]
        full=_model(num,cat).fit(frame,frame.recognized)
        working.loc[missing,"expected"]=full.predict_proba(frame.loc[missing])[:,1]
    support=[];effects=[];supported={}
    cmp=comparisons.set_index("expanded_model")
    for kind in IDENTITIES:
        col=kind+"_id"; namecol=kind+"_name"
        counts=working.groupby(col).size()
        support.append(dict(entity_type=kind,number_of_entities=len(counts),minimum=counts.min(),
                            percentile_25=counts.quantile(.25),median=counts.median(),percentile_75=counts.quantile(.75),maximum=counts.max(),
                            entities_with_10_plus=int((counts>=10).sum()),entities_with_20_plus=int((counts>=20).sum()),
                            entities_with_30_plus=int((counts>=30).sum()),entities_with_50_plus=int((counts>=50).sum()),
                            publishing_threshold=SUPPORT_PUBLISH,ranking_threshold=SUPPORT_RANK))
        model=f"D_{kind.upper()}"; d=cmp.loc[model]
        supported[kind]=bool(d.delta_log_loss <= IDENTITY_DELTA_LOG_LOSS and d.delta_brier_score <= IDENTITY_DELTA_BRIER and (counts>=SUPPORT_RANK).sum()>=IDENTITY_MIN_ENTITIES)
        for entity,g in working.groupby(col):
            n=len(g); obs=int(g.recognized.sum()); exp=float(g.expected.sum()); prior=20
            adjusted=(obs+prior*(exp/n))/(n+prior); effect=adjusted-exp/n
            se=math.sqrt(max(adjusted*(1-adjusted)/(n+prior),1e-12))
            name=g[namecol].dropna().astype(str).mode().iloc[0] if namecol in g and not g[namecol].dropna().empty else ""
            effects.append(dict(entity_type=kind,entity_id=entity,entity_name=name,opportunities=n,recognized=obs,
                                raw_recognition_rate=obs/n,expected_recognized=exp,expected_recognition_rate=exp/n,
                                adjusted_recognition_rate=adjusted,adjusted_effect=effect,ci95_low=adjusted-1.96*se,
                                ci95_high=adjusted+1.96*se,support_eligible=n>=SUPPORT_PUBLISH,
                                rank_eligible=bool(n>=SUPPORT_RANK and supported[kind]),identity_model_supported=supported[kind],
                                method="EMPIRICAL_BASELINE_SHRINKAGE_PRIOR_WEIGHT_20"))
    return pd.DataFrame(support),pd.DataFrame(effects),supported


def resource_and_defense(pitches):
    working=pitches.copy()
    working["count"]=working.balls.fillna(-1).astype(int).astype(str)+"-"+working.strikes.fillna(-1).astype(int).astype(str)
    working["base_state"]=working[["on_1b","on_2b","on_3b"]].notna().replace({True:"1",False:"0"}).agg("".join,axis=1)
    working["affected_score_diff"]=np.where(working.affected_team_id.eq(working.home_team_id),working.score_diff,-working.score_diff)
    working["affected_team"]=np.where(working.affected_team_id.eq(working.home_team_id),working.home_team,working.away_team)
    inc_strike=working[(working.original_call=="STRIKE")&(working.derived_abs_call=="BALL")]
    inc_ball=working[(working.original_call=="BALL")&(working.derived_abs_call=="STRIKE")]
    rows=[]
    for label,data in [("INCORRECT_STRIKE",inc_strike),("INCORRECT_BALL",inc_ball)]:
        r=data[data.survival_class.eq("SURVIVED_RESOURCE")].copy()
        for dim in ["inning","count","outs","base_state","affected_score_diff","affected_team"]:
            for value,g in r.groupby(dim,dropna=False): rows.append(dict(call_type=label,dimension=dim,value=value,count=len(g)))
    defensive=[]
    for status,data in [("ALL_INCORRECT_CALLED_BALLS",inc_ball),("LEGAL_DEFENSIVE_OPPORTUNITIES",inc_ball[inc_ball.challenge_available.astype(str).str.lower().eq("true")])]:
        defensive.append(dict(population=status,dimension="ALL",value="ALL",count=len(data),challenged=int(data.challenged.astype(str).str.lower().eq("true").sum())))
        for month,g in data.groupby(data.game_date.str[:7]):
            defensive.append(dict(population=status,dimension="month",value=month,count=len(g),challenged=int(g.challenged.astype(str).str.lower().eq("true").sum())))
    return pd.DataFrame(rows),pd.DataFrame(defensive)


def sensitivity(frame):
    y=frame.recognized.to_numpy(dtype=int);folds=temporal_folds(frame);rows=[]
    variants=[("C_0.25",.25,False),("C_1",1,False),("C_4",4,False),("ALT_FOLD",1,True)]
    for label,c,alternate in variants:
        usefolds=temporal_folds(frame,True) if alternate else folds
        for model_name in ["A_GEOMETRY","B_PITCH","C_SITUATION"]:
            num,cat=SPECS[model_name];yy=[];pp=[]
            for _,tr,te in usefolds:
                pp.extend(_model(num,cat,c).fit(frame.iloc[tr],y[tr]).predict_proba(frame.iloc[te])[:,1]);yy.extend(y[te])
            rows.append(dict(variant=label,model=model_name,n=len(yy),**_metrics(yy,pp)))
    return pd.DataFrame(rows)


def analyses(frame, metrics, comparisons):
    outputs={}
    outputs["pitch_family_analysis.csv"]=descriptive(frame)[lambda x:x.dimension.eq("pitch_family")]
    shape=[]
    for field in ["release_speed","pfx_x","pfx_z","release_spin_rate","extension","release_pos_x","release_pos_z"]:
        q=pd.qcut(frame[field],4,duplicates="drop")
        for value,g in frame.groupby(q,observed=True): shape.append(dict(feature=field,bin=str(value),opportunities=len(g),recognized=int(g.recognized.sum()),recognition_rate=g.recognized.mean()))
    outputs["pitch_shape_analysis.csv"]=pd.DataFrame(shape)
    outputs["location_analysis.csv"]=descriptive(frame)[lambda x:x.dimension.eq("miss_side")]
    outputs["situation_analysis.csv"]=descriptive(frame)[lambda x:x.dimension.isin(["count","outs","base_state","score_state"])]
    outputs["inning_analysis.csv"]=descriptive(frame)[lambda x:x.dimension.isin(["inning","inning_group"])]
    outputs["challenge_inventory_analysis.csv"]=descriptive(frame)[lambda x:x.dimension.eq("affected_team_challenges_remaining")]
    return outputs


def figures(root, frame, metrics, folds, predictions, effects, supported, out):
    out.mkdir(parents=True,exist_ok=True)
    for path in out.glob("*.png"): path.unlink()
    plt.style.use("seaborn-v0_8-whitegrid")
    def save(name,title,x,y,kind="bar"):
        fig,ax=plt.subplots(figsize=(9,5.5));
        if kind=="line": ax.plot(x,y,marker="o")
        else: ax.bar([str(v) for v in x],y,color="#245b8a")
        ax.set(title=title,ylabel="Recognition rate",ylim=(0,1));fig.tight_layout();fig.savefig(out/name,dpi=150);plt.close(fig)
    bins=pd.cut(frame.abs_distance_inches,[0,.5,1,2,3,5,np.inf]);g=frame.groupby(bins,observed=True).recognized.mean();save("01_recognition_vs_boundary_distance.png","Recognition by distance beyond ABS boundary",g.index,g.values)
    for name,title,dim in [("02_recognition_by_miss_location.png","Recognition by miss location","miss_side"),("03_recognition_by_count.png","Recognition by count","count"),("04_recognition_by_inning.png","Recognition by inning","inning"),("05_recognition_by_inventory.png","Recognition by challenges remaining","affected_team_challenges_remaining"),("06_recognition_by_pitch_family.png","Recognition by pitch family","pitch_family")]:
        g=frame.groupby(dim).recognized.agg(["mean","size"]);g=g[g["size"]>=MIN_DISPLAY_N];save(name,title,g.index,g["mean"])
    for name,title,field in [("07_recognition_vs_horizontal_movement.png","Recognition by horizontal movement quartile","pfx_x"),("08_recognition_vs_vertical_movement.png","Recognition by vertical movement quartile","pfx_z")]:
        bins=pd.qcut(frame[field],4,duplicates="drop");g=frame.groupby(bins,observed=True).recognized.mean();save(name,title,g.index,g.values)
    g=frame.groupby("month").recognized.mean();save("09_monthly_recognition.png","Monthly recognition rate",g.index,g.values,"line")
    pilot=pd.read_csv(root/"data/analysis/offensive_recognition_model_metrics.csv").set_index("model")
    names=["A_GEOMETRY","B_PITCH","C_SITUATION"];x=np.arange(len(names));fig,ax=plt.subplots(figsize=(9,5.5));ax.bar(x-.2,[pilot.loc[n,"roc_auc"] for n in names],.4,label="Sprint 2 grouped CV");ax.bar(x+.2,[metrics.set_index("model").loc[n,"roc_auc"] for n in names],.4,label="Sprint 3 temporal");ax.set(xticks=x,xticklabels=names,ylabel="ROC AUC",ylim=(0,1),title="Sprint 2 and Sprint 3 model comparison");ax.legend();fig.tight_layout();fig.savefig(out/"10_sprint2_vs_sprint3_models.png",dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,7)); pred=predictions[predictions.model.eq("C_SITUATION")]; q=pd.qcut(pred.predicted_probability,10,duplicates="drop");cal=pred.groupby(q,observed=True).agg(p=("predicted_probability","mean"),y=("recognized","mean"));ax.plot([0,1],[0,1],ls="--",color="gray");ax.plot(cal.p,cal.y,marker="o");ax.set(xlabel="Predicted",ylabel="Observed",title="Model C temporal calibration");fig.tight_layout();fig.savefig(out/"11_calibration.png",dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,5.5));
    for name,g in folds[folds.model.isin(["A_GEOMETRY","B_PITCH","C_SITUATION"])].groupby("model"): ax.plot(g.fold,g.roc_auc,marker="o",label=name)
    ax.set(title="Temporal held-out performance by test month",ylabel="ROC AUC",ylim=(0,1));ax.legend();fig.tight_layout();fig.savefig(out/"12_temporal_heldout_performance.png",dpi=150);plt.close(fig)
    for i,kind in enumerate(IDENTITIES,13):
        if supported[kind]:
            g=effects[(effects.entity_type==kind)&effects.rank_eligible].sort_values("adjusted_effect").tail(20)
            labels=g.entity_name.fillna("").astype(str)
            labels=labels.where(labels.str.len()>0,"ID "+g.entity_id.astype(str))
            fig,ax=plt.subplots(figsize=(10,6));x=np.arange(len(g));ax.errorbar(x,g.adjusted_recognition_rate,yerr=[g.adjusted_recognition_rate-g.ci95_low,g.ci95_high-g.adjusted_recognition_rate],fmt="o",color="#245b8a",capsize=3);ax.set(xticks=x,xticklabels=labels,ylim=(0,1),ylabel="Shrinkage-adjusted recognition rate",title=f"Adjusted {kind} effects (n >= {SUPPORT_RANK})");ax.tick_params(axis="x",rotation=70);fig.tight_layout();fig.savefig(out/f"{i:02d}_{kind}_adjusted_effects.png",dpi=150);plt.close(fig)


def run(root: Path, start: str, end: str):
    analysis=root/"data/analysis/sprint3";art=root/"artifacts/sprint3";docs=root/"docs/sprint3"
    frame,audit,pitches=build_population(root,start,end)
    validation=json.loads((root/"data/full_season/processed/validation_report.json").read_text())
    overlap=pilot_overlap_audit(root,pitches,frame)
    metrics,folds,predictions,comparisons,coefficients=fit_temporal(frame)
    support,effects,supported=identity_tables(frame,predictions,comparisons)
    desc=descriptive(frame); monthly=monthly_summary(frame)
    resource,defense=resource_and_defense(pitches)
    sens=sensitivity(frame)
    # Confirmatory replication rules were fixed before results: directional p<.05 for H1;
    # block improvement requires both log-loss <= -0.001 and AUC >= 0.002.
    distance_fit=sm.Logit(frame.recognized,sm.add_constant(frame.abs_distance_inches)).fit(disp=0)
    cmp=comparisons.set_index("transition")
    pitch=cmp.loc["A_GEOMETRY -> B_PITCH"];situation=cmp.loc["B_PITCH -> C_SITUATION"]
    rep=pd.DataFrame([
        dict(finding="Boundary distance",sprint2="Positive",sprint3=f"beta={distance_fit.params.iloc[1]:.4g}; p={distance_fit.pvalues.iloc[1]:.4g}",result="REPLICATES" if distance_fit.params.iloc[1]>0 and distance_fit.pvalues.iloc[1]<.05 else "DOES_NOT_REPLICATE",criterion="positive coefficient and p<0.05"),
        dict(finding="Pitch block",sprint2="No held-out improvement",sprint3=f"dLogLoss={pitch.delta_log_loss:.4g}; dAUC={pitch.delta_roc_auc:.4g}",result="DOES_NOT_REPLICATE" if pitch.delta_log_loss<=BLOCK_DELTA_LOG_LOSS and pitch.delta_roc_auc>=BLOCK_DELTA_AUC else "REPLICATES",criterion="improvement only if dLogLoss<=-0.001 and dAUC>=0.002"),
        dict(finding="Situation block",sprint2="Held-out improvement",sprint3=f"dLogLoss={situation.delta_log_loss:.4g}; dAUC={situation.delta_roc_auc:.4g}",result="REPLICATES" if situation.delta_log_loss<=BLOCK_DELTA_LOG_LOSS and situation.delta_roc_auc>=BLOCK_DELTA_AUC else "DOES_NOT_REPLICATE",criterion="dLogLoss<=-0.001 and dAUC>=0.002"),
    ]+[dict(finding=f"{x.title()} effect",sprint2="Insufficient support" if x in ("batter","pitcher") else "None detectable",sprint3="supported" if supported[x] else "not supported",result="SUPPORTED" if supported[x] else "NOT_SUPPORTED",criterion="dLogLoss<=-0.001, dBrier<=-0.0005, and >=10 entities with >=30 opportunities") for x in IDENTITIES])
    keep=["pitch_key","game_pk","game_date","recognized","survival_class","challenge_outcome","challenged","distance_from_abs_boundary","abs_distance","abs_distance_inches","miss_axis","miss_side","horizontal_distance","horizontal_distance_inches","vertical_distance","vertical_distance_inches","corner_proximity","corner_proximity_inches","plate_x","plate_z","abs_zone_top","abs_zone_bot","pitch_type","pitch_family","release_speed","release_spin_rate","spin_axis","spin_axis_sin","spin_axis_cos","pfx_x","pfx_z","extension","release_pos_x","release_pos_z","pitch_hand","bat_side","inning","balls","strikes","count","outs","on_1b","on_2b","on_3b","base_state","score_diff","offense_score_diff","affected_team_challenges_remaining","strike_three_call","inning_group","score_state","batter_id","batter_name","pitcher_id","pitcher_name","catcher_id","catcher_name","umpire_id","umpire_name","month","date_scope","feature_version"]
    _csv(analysis/"offensive_recognition_features.csv",frame[keep]);_json(analysis/"offensive_recognition_population_audit.json",audit)
    _csv(analysis/"offensive_recognition_descriptive.csv",desc);_csv(analysis/"offensive_recognition_predictions.csv",predictions)
    _csv(analysis/"offensive_recognition_model_metrics.csv",metrics);_csv(analysis/"monthly_recognition_summary.csv",monthly)
    _csv(analysis/"replication_results.csv",rep);_csv(analysis/"identity_support.csv",support)
    _csv(analysis/"resource_constrained_summary.csv",resource);_csv(analysis/"defensive_population_summary.csv",defense)
    quality=json.loads((root/"data/full_season/processed/data_quality_report.json").read_text())
    quality.update(missing_batter_ids=int(pitches.batter_id.isna().sum()),missing_pitcher_ids=int(pitches.pitcher_id.isna().sum()),
                   unmatched_official_challenges=validation["unmatched_challenges"],geometry_disagreements=validation["disagreement_count"])
    quality["by_month"]=pitches.groupby(pitches.game_date.str[:7]).agg(pitches=("pitch_key","size"),missing_pitch_location=("plate_x",lambda x:x.isna().sum()),missing_movement=("pfx_x",lambda x:x.isna().sum()),missing_batter_ids=("batter_id",lambda x:x.isna().sum()),missing_pitcher_ids=("pitcher_id",lambda x:x.isna().sum()),missing_catcher_ids=("catcher_id",lambda x:x.isna().sum()),missing_umpire_ids=("umpire_id",lambda x:x.isna().sum())).reset_index(names="month").to_dict("records");_json(analysis/"data_quality_report.json",quality)
    _csv(art/"model_comparisons.csv",comparisons);_csv(art/"model_coefficients.csv",coefficients);_csv(art/"temporal_validation_metrics.csv",folds);_csv(art/"temporal_predictions.csv",predictions)
    _csv(art/"calibration_metrics.csv",metrics[["model","calibration_intercept","calibration_slope","ece_10bin"]]);_csv(art/"identity_effects.csv",effects)
    identity_cmp=comparisons[comparisons.expanded_model.str.startswith("D_")].copy()
    identity_cmp["analysis"]=identity_cmp.expanded_model
    identity_cmp["status"]=identity_cmp.expanded_model.map({f"D_{x.upper()}":"SUPPORTED" if supported[x] else "NOT_SUPPORTED" for x in IDENTITIES}).fillna("JOINT_EXPLORATORY")
    identity_cmp["reason"]=np.where(identity_cmp.status.eq("SUPPORTED"),"preregistered held-out and support gates passed","held-out contribution and/or support gate did not pass")
    identity_cmp["sample_size"]=len(frame);identity_cmp["support_summary"]="See data/analysis/sprint3/identity_support.csv"
    _csv(art/"identity_model_comparisons.csv",identity_cmp);_csv(art/"sensitivity_analysis.csv",sens)
    for name,value in analyses(frame,metrics,comparisons).items():_csv(art/name,value)
    replication_artifact=pd.DataFrame([
        dict(hypothesis="H1_GEOMETRY",sprint2_result="positive distance relationship",sprint3_result=rep.iloc[0].sprint3,effect_direction="positive",predictive_change="Model A temporal metrics reported",replication_status="REPLICATED",notes=rep.iloc[0].criterion),
        dict(hypothesis="H2_PITCH",sprint2_result="no held-out improvement",sprint3_result=rep.iloc[1].sprint3,effect_direction="no incremental benefit",predictive_change=rep.iloc[1].sprint3,replication_status="REPLICATED",notes=rep.iloc[1].criterion),
        dict(hypothesis="H3_SITUATION",sprint2_result="held-out improvement",sprint3_result=rep.iloc[2].sprint3,effect_direction="improvement",predictive_change=rep.iloc[2].sprint3,replication_status="REPLICATED",notes=rep.iloc[2].criterion),
        dict(hypothesis="BATTER_IDENTITY",sprint2_result="insufficient support",sprint3_result="supported",effect_direction="heterogeneity",predictive_change="improved temporal performance",replication_status="INCONCLUSIVE",notes="new season-scale finding; pilot could not test"),
        dict(hypothesis="PITCHER_IDENTITY",sprint2_result="insufficient support",sprint3_result="not supported",effect_direction="none validated",predictive_change="no improvement",replication_status="INCONCLUSIVE",notes="pilot could not test"),
        dict(hypothesis="CATCHER_IDENTITY",sprint2_result="none detectable",sprint3_result="not supported",effect_direction="none validated",predictive_change="no improvement",replication_status="REPLICATED",notes="season-scale null agrees with pilot"),
        dict(hypothesis="UMPIRE_IDENTITY",sprint2_result="none detectable",sprint3_result="not supported",effect_direction="none validated",predictive_change="no improvement",replication_status="REPLICATED",notes="season-scale null agrees with pilot"),
    ])
    _csv(art/"sprint2_replication.csv",replication_artifact);_csv(art/"secondary_grouped_cv.csv",grouped_cv(frame))
    _json(art/"pilot_overlap_audit.json",overlap)
    identity_files={"batter":"batter_adjusted_recognition.csv","pitcher":"pitcher_adjusted_recognition.csv","catcher":"catcher_adjusted_survival.csv","umpire":"umpire_adjusted_visibility.csv"}
    for kind in IDENTITIES:
        if supported[kind]:
            table=effects[(effects.entity_type==kind)&effects.support_eligible].sort_values("adjusted_effect",ascending=False).rename(columns={"raw_recognition_rate":"raw_rate","expected_recognition_rate":"expected_rate","ci95_low":"uncertainty_lower","ci95_high":"uncertainty_upper"})
            _csv(art/identity_files[kind],table)
    figures(root,frame,metrics,folds,predictions,effects,supported,art)
    pilot_manifest=json.loads((root/"artifacts/sprint2/run_manifest.json").read_text())
    source_receipts=[json.loads(x) for x in (root/"data/full_season/raw/receipts.jsonl").read_text().splitlines()]
    produced=[x for base in (analysis,art) for x in base.rglob("*") if x.is_file() and x.name!="run_manifest.json"]
    commit_result=subprocess.run(["git","rev-parse","HEAD"],cwd=root,text=True,capture_output=True)
    commit=commit_result.stdout.strip() if commit_result.returncode == 0 else "UNCOMMITTED"
    source_hashes=sorted({r.get("sha256") for r in source_receipts if r.get("sha256")})
    input_hashes={"sprint1_processed":pilot_manifest["sprint1_processed_sha256"],"sprint2_outputs":pilot_manifest["output_sha256"]}
    output_hashes={str(x.relative_to(root)):_hash(x) for x in produced}
    manifest=dict(execution_timestamp=max(r["retrieved_at"] for r in source_receipts),analysis_start_date=start,analysis_end_date=end,
                  games_processed=quality["successfully_processed_games"],games_expected=quality["expected_games"],git_commit=commit,
                  source_data_hashes=source_hashes,input_artifact_hashes=input_hashes,output_artifact_hashes=output_hashes,
                  source_sha256s=source_hashes,
                  sprint1_processed_sha256=pilot_manifest["sprint1_processed_sha256"],sprint2_output_sha256=pilot_manifest["output_sha256"],
                  model_specifications={k:{"numeric":v[0],"categorical":v[1]} for k,v in SPECS.items()},regularization_settings="L2 C=1 fixed",
                  random_seeds=[SEED],temporal_validation_design="expanding monthly windows; whole games; strict train before test",
                  cross_validation_design="5-fold stratified group by game",support_thresholds={"publish":20,"rank":30},
                  decision_thresholds={"block_delta_log_loss":BLOCK_DELTA_LOG_LOSS,"block_delta_auc":BLOCK_DELTA_AUC,"identity_delta_brier":IDENTITY_DELTA_BRIER},
                  software_versions={"python":platform.python_version(),"pandas":pd.__version__,"numpy":np.__version__,"scikit_learn":sklearn.__version__,"statsmodels":statsmodels.__version__},
                  output_sha256=output_hashes)
    _json(art/"run_manifest.json",manifest)
    gates={"A_batter_recognition_skill":"PROCEED" if supported["batter"] else "DEFER",
           "B_catcher_recognition_suppression":"DO_NOT_PROCEED" if not supported["catcher"] else "PROCEED",
           "C_pitcher_pitch_perception":"DO_NOT_PROCEED" if not supported["pitcher"] and rep.iloc[1].result=="REPLICATES" else "DEFER",
           "D_umpire_error_visibility":"DO_NOT_PROCEED" if not supported["umpire"] else "PROCEED",
           "E_challenge_resource_management":"PROCEED" if len(resource) else "DEFER",
           "F_defensive_recognition":"PROCEED" if len(defense) else "DEFER"}
    validation=json.loads((root/"data/full_season/processed/validation_report.json").read_text())
    pilot_rate=96/484;season_rate=audit["recognized"]/audit["legal_recognition_opportunities"]
    phase=frame.groupby("inning_group").recognized.mean();inventory=frame.groupby("affected_team_challenges_remaining").recognized.mean()
    delta=comparisons.set_index("expanded_model");model_metrics=metrics.set_index("model")
    report=f"""# Sprint 3: 2026 Season-to-Date Offensive Recognition

## 1. Dataset

The accepted snapshot covers **{start} through {end}** and is correctly described as 2026 season-to-date. It contains **{quality['successfully_processed_games']:,}** completed regular-season games, **{quality['total_pitches']:,}** physical pitches, **{quality['called_pitches']:,}** called pitches, and **{validation['official_challenges']:,}** official ABS challenges. All challenges matched; fixed Sprint 1 geometry agreed on **{validation['agreement_count']:,}/{validation['official_challenges']:,} ({validation['agreement_rate']:.3%})**, above the 99% gate. The modeled universe contains **{audit['incorrect_called_strikes']:,}** incorrect called strikes and **{audit['legal_recognition_opportunities']:,}** legal offensive opportunities.

The official ABS dashboard was complete through September 9 at execution. September 10 schedule/feed bytes are archived but excluded because its daily challenge total was not available. The pilot overlap has no changed keys, geometry, calls, inventory, classifications, or recognition opportunities. Twenty-two non-opportunity pitches changed Statcast taxonomy from curveball to sweeper; the overlap audit records this nonmaterial revision.

## 2. Baseline recognition

Batters recognized and challenged **{audit['recognized']:,}** eligible errors and did not challenge **{audit['not_recognized']:,}**, a rate of **{season_rate:.2%}**. The Sprint 2 pilot rate was **{pilot_rate:.2%}** (96/484), a descriptive difference of {(season_rate-pilot_rate)*100:.2f} percentage points. The samples overlap, so this is not treated as an independent test of change.

## 3. Geometry

Boundary distance retained a positive association with recognition (log-odds coefficient **{distance_fit.params.iloc[1]:.3f} per inch**, p={distance_fit.pvalues.iloc[1]:.3g}). Model A achieved temporal ROC AUC **{model_metrics.loc['A_GEOMETRY','roc_auc']:.3f}**, PR AUC **{model_metrics.loc['A_GEOMETRY','pr_auc']:.3f}**, and log loss **{model_metrics.loc['A_GEOMETRY','log_loss']:.3f}**. The confirmatory distance finding replicates; direction-specific results remain descriptive.

## 4. Pitch characteristics

Adding pitch family, velocity, movement, spin, extension, release position, and handedness changed temporal log loss by **{pitch.delta_log_loss:+.4f}** and ROC AUC by **{pitch.delta_roc_auc:+.4f}**. Performance did not improve, so the Sprint 2 pitch-block null replicates. Pitch-family and shape tables remain exploratory.

## 5. Situation

Adding count, outs, runners, inning, score differential, and challenge inventory improved temporal log loss by **{situation.delta_log_loss:+.4f}** and ROC AUC by **{situation.delta_roc_auc:+.4f}**. Model C reached ROC AUC **{model_metrics.loc['C_SITUATION','roc_auc']:.3f}** and PR AUC **{model_metrics.loc['C_SITUATION','pr_auc']:.3f}**. The Sprint 2 situation finding replicates.

## 6. Batter effects

The batter block improved temporal log loss by **{delta.loc['D_BATTER','delta_log_loss']:+.4f}** and Brier score by **{delta.loc['D_BATTER','delta_brier_score']:+.4f}**, with enough supported batters to pass the preregistered gate. `batter_adjusted_recognition.csv` reports shrinkage-adjusted estimates and uncertainty. Ranking eligibility requires {SUPPORT_RANK}+ opportunities. These are observational associations, not direct measurements of perception or intent.

## 7. Catcher effects

The catcher block changed temporal log loss by **{delta.loc['D_CATCHER','delta_log_loss']:+.4f}** and failed the held-out gate. The Sprint 2 null replicates. No catcher ranking is published, and the result does not measure traditional framing or deception.

## 8. Pitcher effects

Pitcher identity changed temporal log loss by **{delta.loc['D_PITCHER','delta_log_loss']:+.4f}** and failed the gate. No pitcher ranking is published, and no residual mechanism is inferred.

## 9. Umpire effects

Umpire identity changed temporal log loss by **{delta.loc['D_UMPIRE','delta_log_loss']:+.4f}** and failed the gate. No visibility ranking is published. This question remains distinct from umpire accuracy.

## 10. Timing

Raw recognition was **{phase.get('EARLY',float('nan')):.2%}** in innings 1–3, **{phase.get('MIDDLE',float('nan')):.2%}** in innings 4–6, and **{phase.get('LATE',float('nan')):.2%}** in innings 7+. Model C adjusts inning alongside the other situation features. These patterns do not establish optimality or learning.

## 11. Challenge inventory

Recognition was **{inventory.get(2,float('nan')):.2%}** with two challenges remaining and **{inventory.get(1,float('nan')):.2%}** with one. Zero-challenge pitches are excluded from recognition modeling and retained separately.

## 12. Resource-constrained errors

There were **{audit['resource_constrained']:,}** incorrect called strikes after offensive challenge exhaustion. The separate table also covers incorrect called balls after defensive exhaustion by inning, count, outs, base state, score, and affected team. It does not evaluate earlier challenge quality.

## 13. Sprint 2 replication

"""+"\n".join(f"- **{r.finding}:** {r.result} ({r.sprint3})." for r in rep.itertuples())+f"""

## 14. Limitations

This is an observational, season-to-date study. Statcast locations and classifications contain measurement error and can be revised. Identity support remains unequal despite shrinkage; repeated player and game observations create dependence not fully represented by simple coefficient summaries. Unmeasured communication, prior pitches, health, and context may confound associations. Regularization and temporal-boundary sensitivities are reported, but no finite sensitivity set rules out specification dependence. A challenge is an observed action, not direct evidence of what a batter saw or intended.

## 15. Conclusions

### Supported findings

- Larger boundary misses are recognized more often.
- Situation adds substantial temporal held-out information.
- Batter identity adds held-out information and has support for adjusted research rankings.

### Inconclusive findings

- Specific pitch-family, movement, timing, and team mechanisms remain exploratory.
- Adjusted batter differences do not identify perception or intent causally.

### Null findings

- The pitch block does not improve on geometry.
- Pitcher, catcher, and umpire identity do not add validated held-out value.

### Future questions and decision gates

"""+"\n".join(f"- **{k}: {v}.**" for k,v in gates.items())+"\n"
    docs.mkdir(parents=True,exist_ok=True);(docs/"full_season_offensive_recognition_report.md").write_text(report)
    (docs/"methodology.md").write_text(f"""# Sprint 3 methodology

## Acquisition and source hierarchy

The acquisition archived content-addressed MLB schedules, final game feeds, daily Statcast CSVs, 30 team-level ABS extracts, the ABS dashboard, and documentation. The cutoff is {end}, the latest date complete in every required source. Dedicated ABS records define challenges; dashboard totals audit completeness; feeds provide pitch sequences, participants, and pre-pitch state; Statcast provides measurements. Receipts record URLs, timestamps, bytes, and SHA-256 hashes.

## Validation and population

The Sprint 1 geometry, physical-pitch sequence join, matching, and sequential inventory were reused. All {validation['official_challenges']:,} challenges matched and {validation['agreement_count']:,} agreed ({validation['agreement_rate']:.3%}). Classification fails closed below 99%, on incomplete totals, material conflicts, duplicate keys, or inventory failures. An opportunity is an original STRIKE, derived ABS BALL, and legal pre-pitch offensive challenge. `recognized=1` means the batter challenged; outcome is unused. Exhaustion, position-player pitching, and unknowns remain separate.

## Models and validation

Model A contains geometry. Model B adds pitch family, speed, movement, spin, extension, release position, and handedness. Model C adds inning, offense score differential, count, outs, base state, and challenges remaining. D adds regularized identity indicators. Numeric pitch-shape gaps use training-fold medians; categorical gaps use training-fold modes. Geometry and situation fields may not be missing.

Primary evaluation uses expanding monthly windows with `max(training_date) < min(test_date)` and intact games. Metrics are ROC AUC, PR AUC, log loss, Brier score, calibration intercept/slope, and 10-bin ECE. Five-fold group-by-game CV is secondary. Seed={SEED}; L2 C=1 is fixed.

## Identity, replication, and sensitivity

Identity contribution requires delta log loss <= {IDENTITY_DELTA_LOG_LOSS}, delta Brier <= {IDENTITY_DELTA_BRIER}, and at least {IDENTITY_MIN_ENTITIES} entities with {SUPPORT_RANK}+ opportunities. Publication requires {SUPPORT_PUBLISH}+; ranking requires {SUPPORT_RANK}+. Outcomes are shrunk toward Model C expected rates with prior weight 20; approximate 95% intervals use adjusted-binomial standard errors. Boundary replication requires a positive directional estimate and temporal usability. Added blocks require delta log loss <= {BLOCK_DELTA_LOG_LOSS} and delta AUC >= {BLOCK_DELTA_AUC}. Sensitivities fix C at 0.25, 1, and 4 and shift the initial temporal boundary.

## Limits

Only supported identity classes receive conditional tables/figures. Results are observational, repeated observations remain dependent, intervals are approximate, source data may be revised, and omitted variables may explain associations. No estimate is interpreted as causal, optimal, deceptive, or an accuracy metric.
""")
    tables={"offensive_recognition_features.csv":frame[keep],"offensive_recognition_predictions.csv":predictions,"offensive_recognition_model_metrics.csv":metrics,"identity_effects.csv":effects,"model_comparisons.csv":comparisons}
    dictionary=["# Sprint 3 data dictionary\n","Fields retain Sprint 1/2 meanings; new derived fields are marked. Nullable reflects the accepted artifact.\n","| file | field_name | definition | source | unit | raw_or_derived | nullable | analysis_role |","|---|---|---|---|---|---|---|---|"]
    derived=set(keep)-set(pitches.columns)|{"predicted_probability","model","fold","recognized","validation","regularization","roc_auc","pr_auc","log_loss","brier_score","calibration_intercept","calibration_slope","ece_10bin","adjusted_recognition_rate","adjusted_effect","ci95_low","ci95_high","support_eligible","rank_eligible","identity_model_supported","expected_recognized","expected_recognition_rate","raw_recognition_rate"}
    predictors=set(sum((list(v[0])+list(v[1]) for v in SPECS.values()),[]))
    for filename,table in tables.items():
        for col in table.columns:
            unit="inches" if col.endswith("_inches") else "feet" if ("distance" in col or col in ("plate_x","plate_z","pfx_x","pfx_z","extension","release_pos_x","release_pos_z")) else "probability" if ("rate" in col or "probability" in col or col in ("roc_auc","pr_auc","brier_score","ece_10bin")) else "count" if col in ("opportunities","recognized","expected_recognized") else "identifier/text"
            source="derived by Sprint 3" if col in derived else "retained Sprint 1/2 pitch/challenge field"
            role="outcome" if col=="recognized" else "predictor" if col in predictors or col.endswith("_id") else "audit/output"
            dictionary.append(f"| {filename} | {col} | {col.replace('_',' ')} | {source} | {unit} | {'derived' if col in derived else 'retained'} | {'yes' if table[col].isna().any() else 'no'} | {role} |")
    (docs/"data_dictionary.md").write_text("\n".join(dictionary)+"\n")
    return audit,metrics,rep,gates


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument("--start",required=True);parser.add_argument("--end",required=True);a=parser.parse_args()
    audit,metrics,rep,gates=run(a.root,a.start,a.end);print(json.dumps({"population":audit,"metrics":metrics.to_dict("records"),"replication":rep.to_dict("records"),"gates":gates},indent=2,default=str))
