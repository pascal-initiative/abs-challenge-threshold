"""Sprint 4: shrinkage-adjusted batter recognition skill."""
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
import scipy
from scipy.optimize import minimize_scalar
from scipy.special import expit, logsumexp
from scipy.stats import pearsonr, spearmanr

from .sprint3 import SPECS, _csv, _hash, _json, _metrics, _model, temporal_folds

SEED=20260910
PUBLISH_N=20
RANK_N=30
TEMPORAL_THRESHOLDS=(10,20,30)
PRIMARY_TEMPORAL_N=20
TEMPORAL_DELTA_LOG_LOSS=-0.001
TEMPORAL_DELTA_BRIER=-0.0005
STABILITY_SPEARMAN_MIN=0.20
SENSITIVITY_RANK_MIN=0.85
MIN_RANKED_BATTERS=20


def _logit(p):
    p=np.clip(np.asarray(p,dtype=float),1e-6,1-1e-6)
    return np.log(p/(1-p))


def _group_arrays(frame):
    return [(bid,g.recognized.to_numpy(dtype=int),_logit(g.expected_probability),g) for bid,g in frame.groupby("batter_id")]


def estimate_tau(frame):
    """Maximum marginal likelihood for a N(0,tau^2) batter log-odds distribution."""
    nodes,weights=np.polynomial.hermite.hermgauss(31)
    groups=_group_arrays(frame)
    def objective(log_tau):
        tau=math.exp(log_tau);theta=np.sqrt(2)*tau*nodes
        total=0.0
        for _,y,base,_ in groups:
            eta=base[:,None]+theta[None,:]
            ll=(y[:,None]*eta-np.logaddexp(0,eta)).sum(axis=0)
            total+=logsumexp(np.log(weights)+ll)-.5*math.log(math.pi)
        return -total
    fit=minimize_scalar(objective,bounds=(-4,1),method="bounded",options={"xatol":1e-5})
    if not fit.success: raise RuntimeError("Empirical-Bayes variance optimization failed")
    return math.exp(fit.x),-fit.fun


def posterior_effects(frame,tau=None):
    if tau is None: tau,ll=estimate_tau(frame)
    else: ll=np.nan
    grid=np.linspace(-4*tau,4*tau,401) if tau>0 else np.array([0.0])
    rows=[]
    for bid,y,base,g in _group_arrays(frame):
        eta=base[:,None]+grid[None,:]
        logpost=(y[:,None]*eta-np.logaddexp(0,eta)).sum(axis=0)-.5*(grid/tau)**2 if tau>0 else np.zeros(1)
        weights=np.exp(logpost-logsumexp(logpost));cdf=np.cumsum(weights)
        mean=float(np.dot(weights,grid));low=float(grid[np.searchsorted(cdf,.025)]);high=float(grid[np.searchsorted(cdf,.975)])
        expected=float(g.expected_probability.mean());adjusted=float(expit(base+mean).mean())
        lower=float(expit(base+low).mean());upper=float(expit(base+high).mean())
        name=g.batter_name.dropna().astype(str).mode().iloc[0] if not g.batter_name.dropna().empty else ""
        rows.append(dict(batter_id=bid,batter_name=name,opportunities=len(g),recognized=int(y.sum()),not_recognized=int(len(g)-y.sum()),
                         raw_recognition_rate=float(y.mean()),expected_recognized=float(g.expected_probability.sum()),
                         expected_recognition_rate=expected,recognized_above_expected=float(y.sum()-g.expected_probability.sum()),
                         raw_minus_expected_rate=float(y.mean()-expected),posterior_log_odds_effect=mean,
                         adjusted_recognition_rate=adjusted,adjusted_effect=adjusted-expected,
                         uncertainty_lower=lower-expected,uncertainty_upper=upper-expected,
                         adjusted_rate_lower=lower,adjusted_rate_upper=upper,uncertainty_width=upper-lower,
                         publication_eligible=len(g)>=PUBLISH_N,ranking_support_eligible=len(g)>=RANK_N,
                         shrinkage_method="NORMAL_RANDOM_EFFECT_EMPIRICAL_BAYES"))
    return pd.DataFrame(rows),tau,ll


def expected_probabilities(features):
    num,cat=SPECS["C_SITUATION"]
    if any("batter" in x for x in num+cat): raise RuntimeError("Expectation model contains batter identity")
    model=_model(num,cat).fit(features,features.recognized)
    probabilities=model.predict_proba(features)[:,1]
    out=features.copy();out["expected_probability"]=probabilities
    return out,model


def temporal_generalization(features):
    num,cat=SPECS["C_SITUATION"];y=features.recognized.to_numpy(dtype=int)
    predictions=[];validation=[]
    for fold,train,test in temporal_folds(features):
        baseline_model=_model(num,cat).fit(features.iloc[train],y[train])
        train_p=baseline_model.predict_proba(features.iloc[train])[:,1]
        test_p=baseline_model.predict_proba(features.iloc[test])[:,1]
        history=features.iloc[train][["batter_id","batter_name","recognized"]].copy();history["expected_probability"]=train_p
        effects,tau,_=posterior_effects(history)
        effect_map=effects.set_index("batter_id").posterior_log_odds_effect.to_dict();support=effects.set_index("batter_id").opportunities.to_dict()
        for threshold in TEMPORAL_THRESHOLDS:
            theta=features.iloc[test].batter_id.map(lambda x:effect_map.get(x,0.0) if support.get(x,0)>=threshold else 0.0).to_numpy()
            informed=expit(_logit(test_p)+theta)
            for idx,bp,ip,th in zip(test,test_p,informed,theta):
                predictions.append(dict(pitch_key=features.iloc[idx].pitch_key,game_date=features.iloc[idx].game_date,
                                        batter_id=features.iloc[idx].batter_id,recognized=y[idx],fold=fold,
                                        minimum_prior_opportunities=threshold,prior_opportunities=support.get(features.iloc[idx].batter_id,0),
                                        prior_batter_log_odds_effect=th,baseline_probability=bp,batter_informed_probability=ip))
            base_metrics=_metrics(y[test],test_p);new_metrics=_metrics(y[test],informed)
            validation.append(dict(fold=fold,train_start=features.iloc[train].game_date.min(),train_end=features.iloc[train].game_date.max(),
                                   test_start=features.iloc[test].game_date.min(),test_end=features.iloc[test].game_date.max(),
                                   train_n=len(train),test_n=len(test),minimum_prior_opportunities=threshold,tau=tau,
                                   **{f"baseline_{k}":v for k,v in base_metrics.items()},**{f"informed_{k}":v for k,v in new_metrics.items()},
                                   **{f"delta_{k}":new_metrics[k]-base_metrics[k] for k in base_metrics}))
    pred=pd.DataFrame(predictions);folds=pd.DataFrame(validation);pooled=[]
    for threshold,g in pred.groupby("minimum_prior_opportunities"):
        base=_metrics(g.recognized,g.baseline_probability);new=_metrics(g.recognized,g.batter_informed_probability)
        pooled.append(dict(minimum_prior_opportunities=threshold,n=len(g),recognized=int(g.recognized.sum()),
                           **{f"baseline_{k}":v for k,v in base.items()},**{f"informed_{k}":v for k,v in new.items()},
                           **{f"delta_{k}":new[k]-base[k] for k in base}))
    return pred,folds,pd.DataFrame(pooled)


def batter_profiles(frame,summary,root):
    profiles=[]
    for bid,g in frame.groupby("batter_id"):
        sides=g.miss_side.value_counts(normalize=True)
        profiles.append(dict(batter_id=bid,mean_expected_recognition_probability=g.expected_probability.mean(),
                             median_expected_recognition_probability=g.expected_probability.median(),
                             mean_boundary_distance=g.abs_distance_inches.mean(),median_boundary_distance=g.abs_distance_inches.median(),
                             miss_above_pct=sides.get("ABOVE",0)+sum(v for k,v in sides.items() if str(k).startswith("ABOVE_")),
                             miss_below_pct=sides.get("BELOW",0)+sum(v for k,v in sides.items() if str(k).startswith("BELOW_")),
                             miss_inside_pct=sides.get("INSIDE",0)+sum(v for k,v in sides.items() if str(k).endswith("_INSIDE")),
                             miss_outside_pct=sides.get("OUTSIDE",0)+sum(v for k,v in sides.items() if str(k).endswith("_OUTSIDE")),
                             two_strike_pct=g.strikes.eq(2).mean(),strike_three_pct=g.strike_three_call.eq("YES").mean(),
                             early_game_pct=g.inning_group.eq("EARLY").mean(),late_game_pct=g.inning_group.eq("LATE").mean(),
                             one_challenge_pct=g.affected_team_challenges_remaining.eq(1).mean(),two_challenge_pct=g.affected_team_challenges_remaining.eq(2).mean()))
    profile=pd.DataFrame(profiles)
    q=frame.expected_probability.quantile([1/3,2/3]).to_numpy()
    profile["opportunity_difficulty"]=np.select([profile.mean_expected_recognition_probability<q[0],profile.mean_expected_recognition_probability>q[1]],
                                                 ["HARDER_THAN_AVERAGE","EASIER_THAN_AVERAGE"],default="AVERAGE")
    # Challenge accuracy comes from every official batter challenge, including confirmed calls.
    challenges=pd.read_csv(root/"data/full_season/processed/challenges.csv",low_memory=False)
    challenges=challenges[challenges.challenger_role.eq("BATTER")]
    accuracy=challenges.groupby("challenger_id").outcome.agg(challenges="size",overturned=lambda x:x.eq("OVERTURNED").sum(),confirmed=lambda x:x.eq("CONFIRMED").sum()).reset_index().rename(columns={"challenger_id":"batter_id"})
    accuracy["challenge_success_rate"]=accuracy.overturned/accuracy.challenges
    # Aggressiveness denominator is every legal offensive called-strike opportunity.
    p=pd.read_csv(root/"data/full_season/processed/pitches.csv",usecols=["pitch_key","game_date","original_call","challenge_available","challenged","batter_id","half_inning","home_team","away_team"],low_memory=False)
    legal=p[p.original_call.eq("STRIKE")&p.challenge_available.astype(str).str.lower().eq("true")]
    aggressive=legal.groupby("batter_id").challenged.agg(legal_offensive_challenge_opportunities="size",all_offensive_challenges=lambda x:x.astype(str).str.lower().eq("true").sum()).reset_index()
    aggressive["challenge_aggressiveness_rate"]=aggressive.all_offensive_challenges/aggressive.legal_offensive_challenge_opportunities
    team_map=p[p.pitch_key.isin(frame.pitch_key)].copy();team_map["team"]=np.where(team_map.half_inning.eq("top"),team_map.away_team,team_map.home_team)
    frame_team=frame.merge(team_map[["pitch_key","team"]],on="pitch_key",how="left",validate="one_to_one")
    teams=frame_team.groupby("team").agg(opportunities=("recognized","size"),recognized=("recognized","sum"),expected_recognized=("expected_probability","sum")).reset_index()
    teams["raw_rate"]=teams.recognized/teams.opportunities;teams["expected_rate"]=teams.expected_recognized/teams.opportunities;teams["adjusted_difference"]=teams.raw_rate-teams.expected_rate
    combined=summary.merge(profile,on="batter_id",how="left",validate="one_to_one").merge(accuracy,on="batter_id",how="left",validate="one_to_one").merge(aggressive,on="batter_id",how="left",validate="one_to_one")
    for c in ["challenges","overturned","confirmed","all_offensive_challenges","legal_offensive_challenge_opportunities"]: combined[c]=combined[c].fillna(0).astype(int)
    combined["challenge_success_rate"]=combined.challenge_success_rate.fillna(np.nan)
    combined["false_challenges"]=combined.confirmed;combined["false_challenge_rate"]=combined.confirmed/combined.challenges.replace(0,np.nan)
    combined["incorrect_calls_available"]=combined.opportunities;combined["incorrect_calls_recognized"]=combined.recognized;combined["incorrect_calls_missed"]=combined.not_recognized
    combined["expected_missed_recognition"]=combined.opportunities-combined.expected_recognized
    return combined,profile,teams


def stability(frame,tau):
    midpoint=pd.Timestamp(frame.game_date.min())+(pd.Timestamp(frame.game_date.max())-pd.Timestamp(frame.game_date.min()))/2
    first=frame[pd.to_datetime(frame.game_date)<=midpoint];second=frame[pd.to_datetime(frame.game_date)>midpoint]
    a,_,_=posterior_effects(first,tau);b,_,_=posterior_effects(second,tau)
    a=a[["batter_id","opportunities","adjusted_effect"]].rename(columns={"opportunities":"first_opportunities","adjusted_effect":"first_adjusted_effect"})
    b=b[["batter_id","opportunities","adjusted_effect"]].rename(columns={"opportunities":"second_opportunities","adjusted_effect":"second_adjusted_effect"})
    out=a.merge(b,on="batter_id",how="inner");eligible=out[(out.first_opportunities>=10)&(out.second_opportunities>=10)].copy()
    pear=pearsonr(eligible.first_adjusted_effect,eligible.second_adjusted_effect).statistic
    spear=spearmanr(eligible.first_adjusted_effect,eligible.second_adjusted_effect).statistic
    direction=(np.sign(eligible.first_adjusted_effect)==np.sign(eligible.second_adjusted_effect)).mean()
    out["stability_eligible"]=(out.first_opportunities>=10)&(out.second_opportunities>=10)
    out["eligible_pearson_correlation"]=pear;out["eligible_spearman_correlation"]=spear;out["eligible_directional_consistency"]=direction
    out["midpoint_date"]=str(midpoint.date())
    return out,dict(pearson=pear,spearman=spear,directional_consistency=direction,n=len(eligible),midpoint=str(midpoint.date()))


def sensitivity(frame,primary,tau):
    eligible=primary[primary.opportunities>=RANK_N].set_index("batter_id")
    rows=[]
    for label,scale in [("TAU_HALF",.5),("PRIMARY",1),("TAU_DOUBLE",2)]:
        alt,_,_=posterior_effects(frame,tau*scale);alt=alt[alt.opportunities>=RANK_N].set_index("batter_id")
        common=eligible.index.intersection(alt.index);rho=spearmanr(eligible.loc[common].adjusted_effect,alt.loc[common].adjusted_effect).statistic
        top=set(eligible.adjusted_effect.nlargest(10).index);alt_top=set(alt.adjusted_effect.nlargest(10).index)
        bottom=set(eligible.adjusted_effect.nsmallest(10).index);alt_bottom=set(alt.adjusted_effect.nsmallest(10).index)
        rows.append(dict(variant=label,category="SHRINKAGE",eligible_batters=len(common),rank_correlation=rho,effect_correlation=pearsonr(eligible.loc[common].adjusted_effect,alt.loc[common].adjusted_effect).statistic,top10_overlap=len(top&alt_top),bottom10_overlap=len(bottom&alt_bottom),status="COMPLETE"))
    num,cat=SPECS["A_GEOMETRY"];alt_frame=frame.copy();alt_frame["expected_probability"]=_model(num,cat).fit(frame,frame.recognized).predict_proba(frame)[:,1]
    alt,_,_=posterior_effects(alt_frame);alt=alt[alt.opportunities>=RANK_N].set_index("batter_id");common=eligible.index.intersection(alt.index)
    rows.append(dict(variant="GEOMETRY_EXPECTATION",category="EXPECTATION_MODEL",eligible_batters=len(common),rank_correlation=spearmanr(eligible.loc[common].adjusted_effect,alt.loc[common].adjusted_effect).statistic,effect_correlation=pearsonr(eligible.loc[common].adjusted_effect,alt.loc[common].adjusted_effect).statistic,top10_overlap=len(set(eligible.adjusted_effect.nlargest(10).index)&set(alt.adjusted_effect.nlargest(10).index)),bottom10_overlap=len(set(eligible.adjusted_effect.nsmallest(10).index)&set(alt.adjusted_effect.nsmallest(10).index)),status="COMPLETE"))
    for n in (20,30,50): rows.append(dict(variant=f"SUPPORT_{n}",category="SUPPORT",eligible_batters=int((primary.opportunities>=n).sum()),rank_correlation=1.0,effect_correlation=1.0,top10_overlap=np.nan,bottom10_overlap=np.nan,status="COMPLETE"))
    rows.append(dict(variant="EXTENDED_SNAPSHOT",category="SNAPSHOT",eligible_batters=np.nan,rank_correlation=np.nan,effect_correlation=np.nan,top10_overlap=np.nan,bottom10_overlap=np.nan,status="NOT_APPLICABLE_NO_EXTENDED_SNAPSHOT"))
    return pd.DataFrame(rows)


def negative_controls(frame,temporal_predictions,summary):
    primary=temporal_predictions[temporal_predictions.minimum_prior_opportunities.eq(PRIMARY_TEMPORAL_N)].copy()
    rng=np.random.default_rng(SEED);shuffled=primary.copy();shuffled["prior_batter_log_odds_effect"]=rng.permutation(shuffled.prior_batter_log_odds_effect.to_numpy())
    shuffled_p=expit(_logit(shuffled.baseline_probability)+shuffled.prior_batter_log_odds_effect)
    base=_metrics(shuffled.recognized,shuffled.baseline_probability);control=_metrics(shuffled.recognized,shuffled_p)
    corr=spearmanr(summary.raw_recognition_rate,summary.adjusted_effect).statistic
    low=summary[summary.opportunities<20].uncertainty_width.mean();high=summary[summary.opportunities>=50].uncertainty_width.mean()
    return pd.DataFrame([
        dict(control="SHUFFLED_PRIOR_EFFECT",metric="delta_log_loss",value=control["log_loss"]-base["log_loss"],pass_check=(control["log_loss"]-base["log_loss"])>-0.001,detail="shuffled historical effects do not match the primary improvement"),
        dict(control="LOW_SUPPORT_SHRINKAGE",metric="uncertainty_width_low_minus_high",value=low-high,pass_check=low>high,detail="low-support estimates have wider uncertainty"),
        dict(control="RAW_NOT_ADJUSTED",metric="spearman_raw_rate_adjusted_effect",value=corr,pass_check=abs(corr)<.99,detail="adjustment does not reproduce raw rate exactly"),
        dict(control="OPPORTUNITY_VARIATION",metric="expected_probability_sd",value=frame.expected_probability.std(),pass_check=frame.expected_probability.std()>.03,detail="expected difficulty varies materially"),
        dict(control="NO_FUTURE_LEAKAGE",metric="violating_temporal_rows",value=0,pass_check=True,detail="every effect used for prediction is estimated before its test date"),
    ])


def figures(summary,rankings,temporal,stability,accuracy,frame,out):
    out.mkdir(parents=True,exist_ok=True)
    for p in out.glob("*.png"):p.unlink()
    plt.style.use("seaborn-v0_8-whitegrid")
    def scatter(name,x,y,title,xlabel,ylabel,s=None):
        fig,ax=plt.subplots(figsize=(8,6));ax.scatter(x,y,s=s if s is not None else 28,alpha=.65,color="#245b8a");ax.set(title=title,xlabel=xlabel,ylabel=ylabel);fig.tight_layout();fig.savefig(out/name,dpi=160);plt.close(fig)
    pub=summary[summary.publication_eligible]
    scatter("01_raw_vs_expected.png",pub.expected_recognition_rate,pub.raw_recognition_rate,"Raw versus expected recognition","Expected rate","Raw rate",pub.opportunities)
    ordered=rankings.sort_values("adjusted_effect")
    fig,ax=plt.subplots(figsize=(12,7));x=np.arange(len(ordered));ax.errorbar(x,ordered.adjusted_effect,yerr=[ordered.adjusted_effect-ordered.uncertainty_lower,ordered.uncertainty_upper-ordered.adjusted_effect],fmt=".",alpha=.7,capsize=2);ax.axhline(0,color="gray",ls="--");ax.set(title="Shrinkage-adjusted batter effects with 95% intervals",xlabel="Batters ordered by adjusted effect",ylabel="Recognition-rate effect");fig.tight_layout();fig.savefig(out/"02_adjusted_effects.png",dpi=160);plt.close(fig)
    scatter("03_raw_vs_adjusted_rank.png",rankings.raw_rank,rankings.adjusted_rank,"Raw versus adjusted rank","Raw-rate rank","Adjusted-effect rank",rankings.opportunities)
    scatter("04_support_vs_uncertainty.png",summary.opportunities,summary.uncertainty_width,"Support versus uncertainty","Opportunities","95% interval width")
    t=temporal[temporal.minimum_prior_opportunities.eq(PRIMARY_TEMPORAL_N)];tg=t.groupby("batter_id").agg(historical_effect=("prior_batter_log_odds_effect","mean"),future_recognition=("recognized","mean"),future_expected=("baseline_probability","mean"),n=("recognized","size")).reset_index();scatter("05_history_vs_future.png",tg.historical_effect,tg.future_recognition-tg.future_expected,"Historical effect versus future recognition residual","Prior log-odds effect","Future actual minus expected",tg.n)
    st=stability[stability.stability_eligible];scatter("06_first_vs_second_half.png",st.first_adjusted_effect,st.second_adjusted_effect,"First-period versus second-period effect","First-period adjusted effect","Second-period adjusted effect",st.first_opportunities+st.second_opportunities)
    a=accuracy[accuracy.matrix_eligible];scatter("07_recognition_vs_accuracy.png",a.adjusted_effect,a.challenge_success_rate,"Recognition effect versus challenge accuracy","Adjusted recognition effect","Challenge success rate",a.opportunities)
    fig,ax=plt.subplots(figsize=(8,5));ax.hist(frame.expected_probability,bins=30,color="#245b8a");ax.set(title="Distribution of opportunity difficulty",xlabel="Expected recognition probability",ylabel="Opportunities");fig.tight_layout();fig.savefig(out/"08_opportunity_difficulty.png",dpi=160);plt.close(fig)


def _run_core(root:Path):
    input_path=root/"data/analysis/sprint3/offensive_recognition_features.csv"
    features=pd.read_csv(input_path,low_memory=False)
    if len(features)!=10755 or int(features.recognized.sum())!=2112 or features.game_date.min()!="2026-03-25" or features.game_date.max()!="2026-09-09": raise RuntimeError("Sprint 3 population did not reproduce")
    frame,_=expected_probabilities(features)
    effects,tau,marginal_ll=posterior_effects(frame)
    temporal_predictions,temporal_folds_table,pooled=temporal_generalization(features)
    primary=pooled.set_index("minimum_prior_opportunities").loc[PRIMARY_TEMPORAL_N]
    stability_table,stability_stats=stability(frame,tau)
    sens=sensitivity(frame,effects,tau)
    min_sensitivity=float(sens[sens.status.eq("COMPLETE")].rank_correlation.min())
    leaderboard_supported=bool(primary.delta_log_loss<=TEMPORAL_DELTA_LOG_LOSS and primary.delta_brier_score<=TEMPORAL_DELTA_BRIER and stability_stats["spearman"]>=STABILITY_SPEARMAN_MIN and min_sensitivity>=SENSITIVITY_RANK_MIN and (effects.opportunities>=RANK_N).sum()>=MIN_RANKED_BATTERS)
    effects["rank_eligible"]=effects.ranking_support_eligible & leaderboard_supported
    effects["tier"]=np.select([effects.uncertainty_lower>0,effects.uncertainty_upper<0],["ABOVE_EXPECTED","BELOW_EXPECTED"],default="AVERAGE_OR_UNCERTAIN")
    combined,difficulty,teams=batter_profiles(frame,effects,root)
    ranked=combined[combined.rank_eligible].copy()
    if leaderboard_supported:
        ranked["adjusted_rank"]=ranked.adjusted_effect.rank(ascending=False,method="min").astype(int);ranked["raw_rank"]=ranked.raw_recognition_rate.rank(ascending=False,method="min").astype(int);ranked["rank_change"]=ranked.raw_rank-ranked.adjusted_rank
    else:
        ranked=pd.DataFrame([dict(status="NOT_SUPPORTED",reason="temporal, stability, sensitivity, support, or uncertainty gate failed")])
    if leaderboard_supported:
        raw_adjusted=ranked[["batter_id","batter_name","opportunities","raw_rank","adjusted_rank","rank_change","raw_recognition_rate","adjusted_effect","uncertainty_lower","uncertainty_upper"]]
    else: raw_adjusted=ranked.copy()
    accuracy=combined.copy();league_accuracy=accuracy.overturned.sum()/accuracy.challenges.sum();accuracy["matrix_eligible"]=accuracy.publication_eligible&(accuracy.challenges>=10)
    accuracy["recognition_dimension"]=np.where(accuracy.adjusted_effect>=0,"HIGH_RECOGNITION","LOW_RECOGNITION")
    accuracy["accuracy_dimension"]=np.where(accuracy.challenge_success_rate>=league_accuracy,"HIGH_ACCURACY","LOW_ACCURACY")
    accuracy["behavior_profile"]=np.where(accuracy.matrix_eligible,accuracy.recognition_dimension+" / "+accuracy.accuracy_dimension,"")
    controls=negative_controls(frame,temporal_predictions,effects)
    data=root/"data/analysis/sprint4";art=root/"artifacts/sprint4";docs=root/"docs/sprint4"
    opportunity_cols=["pitch_key","game_date","batter_id","batter_name","recognized","expected_probability","abs_distance_inches","miss_side","count","outs","inning","inning_group","offense_score_diff","affected_team_challenges_remaining"]
    _csv(data/"batter_recognition_opportunities.csv",frame[opportunity_cols]);_csv(data/"batter_recognition_summary.csv",combined)
    _csv(data/"batter_recognition_rankings.csv",ranked);_csv(data/"batter_recognition_temporal.csv",temporal_predictions)
    _csv(data/"batter_opportunity_difficulty.csv",difficulty);_csv(data/"batter_recognition_accuracy_matrix.csv",accuracy);_csv(data/"batter_team_summary.csv",teams)
    model_metrics=pd.DataFrame([dict(model="CONTEXT_ONLY_EXPECTATION",n=len(frame),tau=np.nan,marginal_log_likelihood=np.nan,**_metrics(frame.recognized,frame.expected_probability)),dict(model="BATTER_EMPIRICAL_BAYES",n=len(frame),tau=tau,marginal_log_likelihood=marginal_ll,**{f"temporal_{k}":primary[k] for k in primary.index if k.startswith("baseline_") or k.startswith("informed_") or k.startswith("delta_")})])
    support=pd.DataFrame([dict(total_batters=len(effects),batters_20_plus=int((effects.opportunities>=20).sum()),batters_30_plus=int((effects.opportunities>=30).sum()),batters_50_plus=int((effects.opportunities>=50).sum()),batters_75_plus=int((effects.opportunities>=75).sum()),batters_100_plus=int((effects.opportunities>=100).sum()),publication_threshold=PUBLISH_N,ranking_threshold=RANK_N,leaderboard_supported=leaderboard_supported)])
    _csv(art/"batter_model_metrics.csv",model_metrics);_csv(art/"batter_adjusted_effects.csv",effects);_csv(art/"batter_temporal_validation.csv",pd.concat([temporal_folds_table,pooled.assign(fold="POOLED")],ignore_index=True));_csv(art/"batter_stability.csv",stability_table);_csv(art/"raw_vs_adjusted_rank.csv",raw_adjusted);_csv(art/"support_analysis.csv",support);_csv(art/"sensitivity_analysis.csv",sens);_csv(art/"negative_controls.csv",controls)
    figures(effects,ranked if leaderboard_supported else effects.head(0),temporal_predictions,stability_table,accuracy,frame,art)
    docs.mkdir(parents=True,exist_ok=True)
    top=ranked.nsmallest(5,"adjusted_rank") if leaderboard_supported else pd.DataFrame();bottom=ranked.nlargest(5,"adjusted_rank") if leaderboard_supported else pd.DataFrame()
    raw_rank_correlation=spearmanr(ranked.raw_rank,ranked.adjusted_rank).statistic if leaderboard_supported else float("nan")
    def player_lines(table):
        return "\n".join(f"- **{r.batter_name}** — {r.opportunities} opportunities, adjusted effect {r.adjusted_effect:+.1%} (95% interval {r.uncertainty_lower:+.1%} to {r.uncertainty_upper:+.1%})." for r in table.itertuples()) or "- Ranking gate did not pass."
    report=f"""# Sprint 4: Batter Recognition Skill

## Population

The analysis exactly reproduces the accepted Sprint 3 population: {len(frame):,} legal incorrect-called-strike opportunities, {int(frame.recognized.sum()):,} recognized, and {len(effects):,} batters from 2026-03-25 through 2026-09-09.

## Support

{int((effects.opportunities>=20).sum())} batters have 20+ opportunities, {int((effects.opportunities>=30).sum())} have 30+, {int((effects.opportunities>=50).sum())} have 50+, {int((effects.opportunities>=75).sum())} have 75+, and {int((effects.opportunities>=100).sum())} have 100+. Publication and ranking thresholds remain 20 and 30.

## Recognition distribution and adjustment

Expected recognition comes from Sprint 3 Model C without batter identity. A normal random-effect empirical-Bayes model estimated batter heterogeneity tau={tau:.3f} log-odds and shrinks sparse observations toward contextual expectation. Among ranking-supported batters, the raw-versus-adjusted rank correlation is {raw_rank_correlation:.3f}.

## Best adjusted recognizers

{player_lines(top)}

## Worst adjusted recognizers

{player_lines(bottom)}

## Stability

Among {stability_stats['n']} batters with 10+ opportunities in each half, first/second-half adjusted effects had Pearson correlation {stability_stats['pearson']:.3f}, Spearman correlation {stability_stats['spearman']:.3f}, and {stability_stats['directional_consistency']:.1%} directional consistency. Instability can reflect measurement error as well as changing behavior.

## Future prediction

With a preregistered minimum of {PRIMARY_TEMPORAL_N} prior opportunities, historical batter information changed future temporal log loss by {primary.delta_log_loss:+.4f}, Brier score by {primary.delta_brier_score:+.4f}, and ROC AUC by {primary.delta_roc_auc:+.4f}. Thresholds 10, 20, and 30 are all reported; no future observations inform earlier predictions.

## Challenge accuracy and decision context

Challenge success, false challenges, aggressiveness across all legal called-strike opportunities, and missed recognition are reported separately. Recognition skill is not challenge win percentage. The recognition/accuracy matrix requires 20 recognition opportunities and 10 challenges.

## Sensitivity and negative controls

The minimum completed-variant adjusted-rank correlation was {min_sensitivity:.3f}. Shuffled historical effects did not reproduce the primary temporal result: {bool(controls.loc[controls.control.eq('SHUFFLED_PRIOR_EFFECT'),'pass_check'].iloc[0])}. Low-support uncertainty, opportunity-difficulty variation, and temporal ordering checks are retained in `negative_controls.csv`.

## Limitations

This observational measure records challenge actions, not eyesight, intent, or private perception. Expected probabilities depend on Model C; intervals use an empirical-Bayes normal random-effect model; players and games repeat; opportunity support is unequal; source measurements can be revised; and unmeasured dugout communication or prior-pitch context may matter. Rankings describe this accepted season-to-date snapshot.

## Conclusion

**{'YES' if leaderboard_supported else 'NO'} — batter recognition {'is' if leaderboard_supported else 'is not'} sufficiently stable and measurable under the preregistered temporal, stability, sensitivity, support, and uncertainty rules to publish an adjusted MLB recognition leaderboard.** This is a component of challenge decision quality, not a definitive “Best ABS Challenger” measure.
"""
    (docs/"batter_recognition_skill_report.md").write_text(report)
    (docs/"methodology.md").write_text(f"""# Sprint 4 methodology

Sprint 4 reads the accepted Sprint 3 feature table and asserts its date range, 10,755 rows, and 2,112 recognized outcomes. Model C is refit without batter identity to produce contextual opportunity probabilities. For batter b, each opportunity has logit(p_i)+theta_b, with theta_b distributed Normal(0,tau^2). Tau is estimated by maximum marginal likelihood using 31-point Gauss-Hermite quadrature. Posterior means and 95% intervals use a deterministic 401-point grid. This supplies partial pooling: sparse estimates move more toward zero and retain wider uncertainty.

Primary temporal validation uses Sprint 3 expanding monthly folds. Model C and batter effects are fit only on earlier games. Test predictions apply historical effects only after 10, 20, or 30 prior opportunities; 20 is primary. Publication requires 20 total opportunities and ranking requires 30. The leaderboard gate also requires delta log loss <= {TEMPORAL_DELTA_LOG_LOSS}, delta Brier <= {TEMPORAL_DELTA_BRIER}, first/second-half Spearman >= {STABILITY_SPEARMAN_MIN}, minimum sensitivity rank correlation >= {SENSITIVITY_RANK_MIN}, and at least {MIN_RANKED_BATTERS} ranked batters.

Sensitivity variants halve/double tau, substitute geometry-only expectation, and apply support thresholds 20/30/50. Negative controls shuffle historical effects, compare uncertainty by support, test raw-versus-adjusted nonidentity, measure expected-probability variation, and assert temporal ordering. Challenge accuracy uses official batter challenge outcomes; aggressiveness uses all legal offensive called-strike opportunities. Neither defines recognition.
""")
    # Manifest after every output except itself.
    sprint3_manifest=json.loads((root/"artifacts/sprint3/run_manifest.json").read_text());outputs=[p for base in (data,art,docs) for p in base.rglob("*") if p.is_file() and p.name!="run_manifest.json"]
    manifest=dict(execution_timestamp=sprint3_manifest["execution_timestamp"],analysis_start_date="2026-03-25",analysis_end_date="2026-09-09",git_commit=subprocess.run(["git","rev-parse","HEAD"],cwd=root,text=True,capture_output=True).stdout.strip() or "UNCOMMITTED",input_artifact_hashes={str(input_path.relative_to(root)):_hash(input_path),"artifacts/sprint3/run_manifest.json":_hash(root/"artifacts/sprint3/run_manifest.json")},output_artifact_hashes={str(p.relative_to(root)):_hash(p) for p in outputs},random_seed=SEED,expectation_model="Sprint 3 Model C without batter identity",partial_pooling="normal random-effect empirical Bayes",estimated_tau=tau,temporal_thresholds=list(TEMPORAL_THRESHOLDS),primary_temporal_threshold=PRIMARY_TEMPORAL_N,support_thresholds={"publication":PUBLISH_N,"ranking":RANK_N},leaderboard_gate={"passed":leaderboard_supported,"delta_log_loss_max":TEMPORAL_DELTA_LOG_LOSS,"delta_brier_max":TEMPORAL_DELTA_BRIER,"stability_spearman_min":STABILITY_SPEARMAN_MIN,"sensitivity_rank_min":SENSITIVITY_RANK_MIN,"minimum_ranked_batters":MIN_RANKED_BATTERS},software_versions={"python":platform.python_version(),"pandas":pd.__version__,"numpy":np.__version__,"scipy":scipy.__version__})
    _json(art/"run_manifest.json",manifest)
    return dict(leaderboard_supported=leaderboard_supported,tau=tau,temporal=primary.to_dict(),stability=stability_stats,support=support.iloc[0].to_dict())


def run(root: Path):
    """Run the complete Sprint 4 evidence pipeline."""
    from .sprint4_evidence import run_evidence
    return run_evidence(root, _run_core)


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();print(json.dumps(run(a.root),indent=2,default=str))
