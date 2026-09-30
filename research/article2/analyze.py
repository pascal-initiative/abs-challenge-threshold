"""Article 2 research: isolated, deterministic analysis of the accepted ABS snapshot."""
from __future__ import annotations
import argparse, hashlib, json, os, sys, platform
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/abs-article2-mpl')
os.environ.setdefault('XDG_CACHE_HOME','/private/tmp/abs-article2-cache')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import scipy, sklearn, statsmodels
from scipy.special import expit, logit
from scipy.stats import norm
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, SplineTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score
from statsmodels.stats.proportion import proportion_confint
import statsmodels.api as sm
import statsmodels.formula.api as smf
SEED=20260915

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as r:
        for b in iter(lambda:r.read(1048576),b''): h.update(b)
    return h.hexdigest()

def markdown(f):
    f=f.copy()
    for c in f:
        f[c]=f[c].map(lambda x: f'{x:.5g}' if isinstance(x,(float,np.floating)) else str(x))
    return '| '+' | '.join(f.columns)+' |\n| '+' | '.join(['---']*len(f.columns))+' |\n'+'\n'.join('| '+' | '.join(row)+' |' for row in f.astype(str).values)+'\n'

def main(root,out):
    sys.path.insert(0,str(root))
    from src.sprint3 import build_population, PITCH_NUM
    assert out != root and not any(out == root/d or root/d in out.parents for d in ['data','src','docs','artifacts']), 'Refusing output inside existing research inputs or frozen artifacts'
    out.mkdir(parents=True,exist_ok=True)
    for d in ['tables','figures']: (out/d).mkdir(exist_ok=True)
    protected=[p for parent in ['data/full_season/processed','data/processed','data/analysis','artifacts/publication_validation','docs','src'] for p in (root/parent).rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    protected.append(root/'data/full_season/raw/receipts.jsonl')
    before={str(p.relative_to(root)):digest(p) for p in protected}
    f,a,allp=build_population(root,'2026-03-25','2026-09-09')
    assert len(f)==10755 and int(f.recognized.sum())==2112, 'STOP: primary population mismatch'
    assert f.pitch_key.is_unique and f.state_timing.eq('PRE_PITCH').all()
    validation=json.loads((root/'data/full_season/processed/validation_report.json').read_text())
    assert validation['agreement_count']==9482 and validation['official_challenges']==9485
    del allp
    print('Population reproduced: 10755 / 2112',flush=True)
    f['challenged']=f.recognized.astype(int)
    f['plate_side']=np.where(f.plate_x<0,'catcher_left','catcher_right')
    f['hand_location']=f.bat_side+':'+f.miss_side
    f['late_close']=((f.inning>=7)&(f.offense_score_diff.abs()<=2)).astype(int)
    f['pa_ending']=f.strikes.eq(2).astype(int)
    f['inning_ending']=((f.strikes==2)&(f.outs==2)).astype(int)
    f['game_ending']=((f.inning>=9)&(f.half_inning=='bottom')&(f.offense_score_diff<0)&f.inning_ending.eq(1)).astype(int)
    f['one_left']=f.affected_team_challenges_remaining.eq(1).astype(int)
    f['inventory_inning']=f.one_left*f.inning
    f['inventory_late_close']=f.one_left*f.late_close
    f['score_group']=pd.cut(f.offense_score_diff,[-np.inf,-3,-1,0,2,np.inf],labels=['behind 3+','behind 1–2','tied','ahead 1–2','ahead 3+']).astype(str)
    f['team']=f.affected_team_id.astype(str)
    # Equal-frequency bins use location only (no labels); final bin includes maximum.
    f['distance_group']='Q'+(pd.qcut(f.abs_distance_inches,8,labels=False,duplicates='raise')+1).astype(str)
    f['split']=np.select([f.game_date<'2026-07-01',f.game_date<'2026-08-01'],['train','validation'],default='test')
    tables={}
    def table(name,t):
        t=t.reset_index(drop=True); tables[name]=t
        t.to_csv(out/'tables'/f'{name}.csv',index=False,float_format='%.10g')
        (out/'tables'/f'{name}.md').write_text(markdown(t))
        return t
    def rates(name,keys,data=f):
        t=data.groupby(keys,observed=True,dropna=False).challenged.agg(opportunities='size',challenges='sum').reset_index()
        t['challenge_rate']=t.challenges/t.opportunities
        t['ci95_low'],t['ci95_high']=proportion_confint(t.challenges,t.opportunities,method='wilson')
        return table(name,t)
    rates('overall',['date_scope']); rates('count',['count']); rates('inning',['inning']); rates('month',['month'])
    rates('inventory',['affected_team_challenges_remaining']); rates('location',['miss_axis','miss_side','bat_side'])
    for c in ['inning_group','late_close','score_group','outs','base_state','half_inning','inning_ending','pa_ending','game_ending']:
        rates('situation_'+c,[c])
    dist=rates('distance',['distance_group'])
    desc=f.groupby('distance_group').abs_distance_inches.agg(distance_min='min',distance_max='max',distance_mean='mean').reset_index()
    dist=table('distance',dist.merge(desc,on='distance_group').sort_values('distance_mean'))
    table('distance_distribution',f[['abs_distance_inches','horizontal_distance_inches','vertical_distance_inches']].describe(percentiles=[.01,.1,.25,.5,.75,.9,.99]).reset_index(names='statistic'))
    bn=f.groupby('batter_id').size()
    table('batter_opportunity_distribution',bn.describe(percentiles=[.1,.25,.5,.75,.9,.95,.99]).reset_index().rename(columns={'index':'statistic',0:'opportunities'}))
    table('missingness',pd.DataFrame({'field':f.columns,'missing_n':f.isna().sum().values,'total_n':len(f)}))
    table('population_exclusions',pd.DataFrame([{'group':k,'n':a[k]} for k in ['incorrect_called_strikes','legal_recognition_opportunities','recognized','not_recognized','resource_constrained','position_player_pitching','unknown','other_exclusions']]))
    table('temporal_split',f.groupby('split').agg(start=('game_date','min'),end=('game_date','max'),opportunities=('pitch_key','size'),challenges=('challenged','sum'),batters=('batter_id','nunique')).reset_index())
    geomn=['horizontal_distance_inches','vertical_distance_inches']
    geomc=['miss_axis','miss_side','plate_side','bat_side','hand_location']
    sitn=['inning','offense_score_diff']
    sitc=['outs','base_state','half_inning','late_close','inning_ending','game_ending']
    specs={'A':(geomn,geomc),'B':(geomn,geomc+['count']),
           'C':(geomn+sitn,geomc+['count']+sitc),
           'D':(geomn+sitn+['inventory_inning','inventory_late_close'],geomc+['count']+sitc+['one_left'])}
    def model(spec,linear=False):
        num,cat=spec
        return Pipeline([('features',ColumnTransformer([
            ('distance',StandardScaler() if linear else SplineTransformer(n_knots=5,degree=3,knots='quantile',include_bias=False,extrapolation='linear'),['abs_distance_inches']),
            ('numeric',Pipeline([('impute',SimpleImputer(strategy='median',add_indicator=True)),('scale',StandardScaler())]),num),
            ('categories',OneHotEncoder(handle_unknown='ignore'),cat)])),
            ('logit',LogisticRegression(C=1,solver='lbfgs',max_iter=4000,random_state=SEED))])
    def fit(spec,tr,te,linear=False):
        m=model(spec,linear); m.fit(tr,tr.challenged); return m,m.predict_proba(te)[:,1]
    def metrics(y,p):
        if np.std(p)<1e-12:
            return dict(log_loss=log_loss(y,p),brier=brier_score_loss(y,p),auc=roc_auc_score(y,p),calibration_intercept=np.nan,calibration_slope=np.nan)
        cal=sm.GLM(y,sm.add_constant(logit(np.clip(p,1e-6,1-1e-6))),family=sm.families.Binomial()).fit()
        return dict(log_loss=log_loss(y,p),brier=brier_score_loss(y,p),auc=roc_auc_score(y,p),calibration_intercept=cal.params.iloc[0] if hasattr(cal.params,'iloc') else cal.params[0],calibration_slope=cal.params.iloc[1] if hasattr(cal.params,'iloc') else cal.params[1])
    tr=f[f.split=='train']; va=f[f.split=='validation']; te=f[f.split=='test']; dev=f[f.split!='test']
    vals={}; rows=[]
    for name,spec in specs.items():
        m,p=fit(spec,tr,va); vals[name]=log_loss(va.challenged,p)
        rows.append(dict(model=name,period='validation',n=len(va),challenges=int(va.challenged.sum()),**metrics(va.challenged,p)))
    # Material threshold fixed before scores are inspected: prefer simplest within .001 log loss.
    best=min(vals,key=vals.get); selected=next(k for k in specs if vals[k]<=vals[best]+.001)
    specs['E']=(specs[selected][0]+PITCH_NUM,specs[selected][1]+['pitch_family','pitch_hand'])
    m,p=fit(specs['E'],tr,va)
    rows.append(dict(model='E',period='validation',n=len(va),challenges=int(va.challenged.sum()),**metrics(va.challenged,p)))
    fitted={}; preds={}
    for name,spec in specs.items():
        m,p=fit(spec,dev,te); fitted[name]=m; preds[name]=p
        rows.append(dict(model=name,period='test',n=len(te),challenges=int(te.challenged.sum()),**metrics(te.challenged,p)))
    base=np.full(len(te),dev.challenged.mean()); rows.append(dict(model='intercept',period='test',n=len(te),challenges=int(te.challenged.sum()),**metrics(te.challenged,base)))
    comparison=table('model_comparison',pd.DataFrame(rows))
    print('Selected non-batter baseline',selected,vals,flush=True)
    def losses(y,p): return -(y*np.log(np.clip(p,1e-8,1-1e-8))+(1-y)*np.log(np.clip(1-p,1e-8,1-1e-8)))
    def block_ci(data,delta,group,reps=1000):
        d=pd.DataFrame({'g':data[group].values,'d':delta}).groupby('g').d.agg(['sum','size'])
        rng=np.random.default_rng(SEED); ix=rng.integers(0,len(d),size=(reps,len(d)))
        vals=d['sum'].values[ix].sum(1)/d['size'].values[ix].sum(1)
        return np.quantile(vals,[.025,.975])
    increments=[]
    pairs=[('A','B'),('B','C'),('C','D'),(selected,'E')]
    for x,y in pairs:
        delta=losses(te.challenged.values,preds[y])-losses(te.challenged.values,preds[x])
        for group in ['game_pk','batter_id']:
            lo,hi=block_ci(te,delta,group)
            increments.append(dict(baseline=x,added=y,cluster=group,n=len(te),challenges=int(te.challenged.sum()),delta_log_loss=delta.mean(),ci95_low=lo,ci95_high=hi,delta_brier=np.mean((te.challenged-preds[y])**2-(te.challenged-preds[x])**2),total_log_likelihood_gain=-delta.sum()))
    inc=table('incremental_performance',pd.DataFrame(increments)); table('pitch_increment',inc[inc.added=='E'])
    # Expanding monthly predictions for descriptive batter residuals and temporal stability.
    oof=f[['pitch_key','game_pk','game_date','month','batter_id','batter_name','team','challenged','split']].copy()
    for name in specs: oof[name]=np.nan
    folds=[]; monthly=[]
    for month in sorted(f.month.unique())[1:]:
        train=f[f.month<month]; test=f[f.month==month]
        folds.append(dict(month=month,train_start=train.game_date.min(),train_end=train.game_date.max(),test_start=test.game_date.min(),test_end=test.game_date.max(),train_n=len(train),test_n=len(test),test_challenges=int(test.challenged.sum()),shared_batters=len(set(train.batter_id)&set(test.batter_id))))
        for name,spec in specs.items():
            m,p=fit(spec,train,test); oof.loc[test.index,name]=p
            monthly.append(dict(model=name,month=month,n=len(test),challenges=int(test.challenged.sum()),**metrics(test.challenged,p)))
    table('rolling_folds',pd.DataFrame(folds)); table('monthly_model_performance',pd.DataFrame(monthly))
    table('rolling_predictions',oof)
    testpred=te[['pitch_key','game_pk','batter_id','challenged']].copy()
    for name,p in preds.items(): testpred[name]=p
    table('test_predictions',testpred)
    # Cluster-robust inference, separate from held-out regularized prediction.
    formula='challenged ~ bs(abs_distance_inches, df=5, degree=3) + C(miss_side) + C(bat_side) + C(plate_side):C(bat_side) + C(count)'
    infer=smf.glm(formula,f,family=sm.families.Binomial()).fit(cov_type='cluster',cov_kwds={'groups':f.batter_id})
    ci=infer.conf_int()
    coefficients=table('geometry_count_associations',pd.DataFrame({'term':infer.params.index,'log_odds':infer.params.values,'se_cluster_batter':infer.bse.values,'odds_ratio':np.exp(infer.params.values),'ci95_low':np.exp(ci[0].values),'ci95_high':np.exp(ci[1].values),'p_value':infer.pvalues.values,'n':len(f)}))
    # Standardize count predictions over common geometry (associational, not causal).
    countadj=[]
    for count in sorted(f['count'].unique()):
        tmp=f.copy();tmp['count']=count
        countadj.append(dict(count=count,standardized_probability=infer.predict(tmp).mean(),standardization_n=len(f)))
    table('count_adjusted',tables['count'].merge(pd.DataFrame(countadj),on='count'))
    # Batter residuals use only earlier-date trained predictions, fixed non-identity specification.
    eligible=oof[oof[selected].notna()].copy(); eligible['expected']=eligible[selected];eligible['variance']=eligible.expected*(1-eligible.expected)
    b=eligible.groupby(['batter_id','batter_name']).agg(opportunities=('challenged','size'),actual=('challenged','sum'),expected=('expected','sum'),conditional_variance=('variance','sum')).reset_index()
    b['actual_rate']=b.actual/b.opportunities;b['expected_rate']=b.expected/b.opportunities;b['above_expected']=b.actual-b.expected
    # Normal approximation is flagged conditional; no model-estimation or within-player dependence coverage.
    b['conditional_se']=np.sqrt(b.conditional_variance);b['conditional_ci95_low']=b.above_expected-1.96*b.conditional_se;b['conditional_ci95_high']=b.above_expected+1.96*b.conditional_se
    b['residual_rate']=b.above_expected/b.opportunities
    b['adjusted_rate']=eligible.challenged.mean()+b.residual_rate
    b['qualified']=b.opportunities>=50
    # Resample whole games within each batter; uncertainty is conditional on fixed baseline.
    eligible['residual']=eligible.challenged-eligible.expected
    block_rows=[]
    for batter,g in eligible.groupby('batter_id'):
        lo,hi=block_ci(g,g.residual.values,'game_pk')
        block_rows.append(dict(batter_id=batter,games=g.game_pk.nunique(),game_bootstrap_residual_rate_low=lo,game_bootstrap_residual_rate_high=hi))
    b=b.merge(pd.DataFrame(block_rows),on='batter_id',validate='one_to_one')
    b['simultaneous_low']=b.above_expected-norm.ppf(1-.05/(2*max(1,b.qualified.sum())))*b.conditional_se
    b['simultaneous_high']=b.above_expected+norm.ppf(1-.05/(2*max(1,b.qualified.sum())))*b.conditional_se
    # Fixed transparent 50-opportunity prior equivalent; descriptive stabilization, not learned talent.
    b['shrunken_residual_rate']=b.above_expected/(b.opportunities+50)
    table('batter_actual_expected',b.sort_values('above_expected',ascending=False))
    q=b[b.qualified]
    candidate=[]
    for label,col,ascending in [('above','above_expected',False),('below','above_expected',True),('highest_adjusted','shrunken_residual_rate',False),('lowest_adjusted','shrunken_residual_rate',True)]:
        z=q[q.above_expected>0] if label in ('above','highest_adjusted') else q[q.above_expected<0]
        z=z.sort_values(col,ascending=ascending).head(10).copy();z.insert(0,'list',label);candidate.append(z)
    table('batter_candidates',pd.concat(candidate))
    threshold=[]
    for n in [30,50,75,100]:
        z=b[b.opportunities>=n].copy()
        cutoff=norm.ppf(1-.05/(2*max(1,len(z))))
        z['simultaneous_low']=z.above_expected-cutoff*z.conditional_se
        z['simultaneous_high']=z.above_expected+cutoff*z.conditional_se
        threshold.append(dict(minimum_n=n,qualifying_batters=len(z),opportunities=int(z.opportunities.sum()),challenges=int(z.actual.sum()),median_conditional_rate_halfwidth=float((1.96*z.conditional_se/z.opportunities).median()),above_simultaneous=int((z.simultaneous_low>0).sum()),below_simultaneous=int((z.simultaneous_high<0).sum())))
    table('batter_thresholds',pd.DataFrame(threshold))
    temporal=[]
    for period,sub in [('April–June',eligible[eligible.game_date<'2026-07-01']),('July–September',eligible[eligible.game_date>='2026-07-01'])]:
        t=sub.groupby('batter_id').agg(n=('challenged','size'),actual=('challenged','sum'),expected=('expected','sum'));t['residual_rate']=(t.actual-t.expected)/t.n;t['period']=period;temporal.append(t.reset_index())
    bt=table('batter_temporal',pd.concat(temporal))
    left,right=temporal; shared=left[left.n>=20].merge(right[right.n>=20],on='batter_id',suffixes=('_early','_late'))
    stability={'batters_n20_both':len(shared),'pearson_residual_rate':shared.residual_rate_early.corr(shared.residual_rate_late),'spearman_residual_rate':shared.residual_rate_early.corr(shared.residual_rate_late,method='spearman')}
    # Fixed sensitivity grid, refit on same chronological split; no selection changes.
    robust=[]
    for threshold_inches in [0,.05,.1,.25,.5]:
        sub=f[f.abs_distance_inches>threshold_inches]; train=sub[sub.split!='test'];test=sub[sub.split=='test']
        for name in ['A','B','C','D','E']:
            m,p=fit(specs[name],train,test)
            robust.append(dict(check='boundary',value=threshold_inches,model=name,population_n=len(sub),population_challenges=int(sub.challenged.sum()),test_n=len(test),test_challenges=int(test.challenged.sum()),**metrics(test.challenged,p)))
    for name in ['A',selected]:
        m,p=fit(specs[name],dev,te,linear=True)
        robust.append(dict(check='linear_distance',value=0,model=name,population_n=len(f),population_challenges=int(f.challenged.sum()),test_n=len(te),test_challenges=int(te.challenged.sum()),**metrics(te.challenged,p)))
    table('robustness',pd.DataFrame(robust))
    # Remove most frequent entities defined from development opportunities, refit comparisons.
    concentration=[]
    for group,k in [('batter_id',10),('team',3)]:
        excluded=dev[group].value_counts().head(k).index
        train=dev[~dev[group].isin(excluded)];test=te[~te[group].isin(excluded)]
        for name in ['A','B','C','D','E']:
            m,p=fit(specs[name],train,test)
            concentration.append(dict(excluded_group=group,excluded_k=k,model=name,train_n=len(train),test_n=len(test),test_challenges=int(test.challenged.sum()),**metrics(test.challenged,p)))
    table('concentration',pd.DataFrame(concentration))
    # Boundary sensitivity of the distance association with repeated-batter robust uncertainty.
    slopes=[]
    for margin in [0,.05,.1,.25,.5]:
        sub=f[f.abs_distance_inches>margin]
        gm=smf.glm('challenged ~ abs_distance_inches + C(miss_side) + C(count) + C(bat_side)',sub,family=sm.families.Binomial()).fit(cov_type='cluster',cov_kwds={'groups':sub.batter_id})
        c=gm.conf_int().loc['abs_distance_inches']
        slopes.append(dict(exclude_at_or_below_inches=margin,n=len(sub),challenges=int(sub.challenged.sum()),odds_ratio_per_inch=np.exp(gm.params['abs_distance_inches']),ci95_low=np.exp(c.iloc[0]),ci95_high=np.exp(c.iloc[1])))
    table('distance_sensitivity_association',pd.DataFrame(slopes))
    # No-direction ablation isolates information beyond distance, no identity.
    m,p=fit(([],['bat_side']),dev,te)
    direction_delta=losses(te.challenged.values,preds['A'])-losses(te.challenged.values,p)
    direction_rows=[]
    for group in ['game_pk','batter_id']:
        lo,hi=block_ci(te,direction_delta,group)
        direction_rows.append(dict(cluster=group,n=len(te),challenges=int(te.challenged.sum()),delta_log_loss=direction_delta.mean(),ci95_low=lo,ci95_high=hi))
    table('direction_increment',pd.DataFrame(direction_rows))
    table('direction_ablation',pd.DataFrame([dict(model='distance_and_hand_only',n=len(te),challenges=int(te.challenged.sum()),**metrics(te.challenged,p)),dict(model='A_full_geometry',n=len(te),challenges=int(te.challenged.sum()),**metrics(te.challenged,preds['A']))]))
    # Publication-style static figures and exact plotting tables.
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':120,'savefig.dpi':300})
    captions=[]
    def save(name,fig,caption):
        fig.text(.08,.025,caption,fontsize=8,ha='left',va='bottom',wrap=True)
        fig.tight_layout(rect=[0,.12,1,1]);fig.savefig(out/'figures'/f'{name}.png');fig.savefig(out/'figures'/f'{name}.pdf');plt.close(fig)
        captions.append(f'### {name}\n\n{caption}\n\n![{name}](figures/{name}.png)\n')
    fig,ax=plt.subplots(figsize=(8,5));ax.errorbar(dist.distance_mean,dist.challenge_rate,yerr=[dist.challenge_rate-dist.ci95_low,dist.ci95_high-dist.challenge_rate],fmt='o',capsize=3,label='Equal-frequency groups; Wilson 95% CI')
    # Marginal fitted association on central 99% support; do not force monotonicity.
    curve=[]
    for d in np.linspace(f.abs_distance_inches.min(),f.abs_distance_inches.quantile(.99),100):
        tmp=f.copy();tmp.abs_distance_inches=d
        curve.append(dict(distance_inches=d,standardized_probability=infer.predict(tmp).mean(),standardization_n=len(f)))
    curve=table('distance_curve',pd.DataFrame(curve));ax.plot(curve.distance_inches,curve.standardized_probability,label='Count/location-adjusted spline')
    ax.set(xlabel='Miss beyond reconstructed ABS boundary (inches)',ylabel='Probability of challenging',title='Larger misses and batter challenge probability');ax.yaxis.set_major_formatter(PercentFormatter(1));ax.legend(fontsize=8)
    save('01_distance',fig,'10,755 opportunities; 2,112 challenges. Points: eight outcome-blind quantile bins.\nCurve: full-sample association, standardized over count/location; not a causal effect.')
    c=tables['count_adjusted'];fig,ax=plt.subplots(figsize=(9,5));x=np.arange(len(c));ax.bar(x,c.challenge_rate,color='#21618c',label='Observed');ax.plot(x,c.standardized_probability,'o',color='#ba4a00',label='Geometry-adjusted')
    ax.set_xticks(x,[f'{r["count"]}\nn={r.opportunities}' for _,r in c.iterrows()]);ax.set(ylabel='Challenge probability',xlabel='Pre-pitch count',title='Count and challenging an incorrect called strike');ax.yaxis.set_major_formatter(PercentFormatter(1));ax.legend()
    save('02_count',fig,'All 10,755 opportunities. Adjusted probabilities standardized over common geometry.\nTwo pre-pitch strikes means the called strike could end the plate appearance.')
    t=rates('situation_plot',['inning_group','late_close']);t=t.sort_values('inning_group',key=lambda x:x.map({'EARLY':0,'MIDDLE':1,'LATE':2}));fig,ax=plt.subplots(figsize=(8,5));ax.bar(np.arange(len(t)),t.challenge_rate,color='#2874a6');ax.set_xticks(np.arange(len(t)),[f"{ {'EARLY':'Innings 1–3','MIDDLE':'Innings 4–6','LATE':'Innings 7+'}[r.inning_group]}\n{'close' if r.late_close else 'all margins' if r.inning_group!='LATE' else 'not close'}\nn={r.opportunities}" for _,r in t.iterrows()]);ax.set(ylabel='Observed challenge probability',title='Game situation: descriptive challenge rates');ax.yaxis.set_major_formatter(PercentFormatter(1))
    save('03_situation',fig,'Late-and-close: inning 7+ and batting-team score margin within two runs.\nA context flag, not a leverage index. All 10,755 opportunities; groups are unadjusted.')
    z=f.copy();z['x_bin']=np.floor(z.plate_x*12/3)*3;z['height_bin']=np.floor(((z.plate_z-z.abs_zone_bot)/(z.abs_zone_top-z.abs_zone_bot))/.2)*.2
    zone=rates('zone_plot',['x_bin','height_bin'],z);shown=zone[zone.opportunities>=20]
    fig,ax=plt.subplots(figsize=(7,6));sc=ax.scatter(shown.x_bin+1.5,shown.height_bin+.1,c=shown.challenge_rate,s=120,cmap='viridis',vmin=0,vmax=.7,marker='s');fig.colorbar(sc,ax=ax,label='Observed challenge probability');ax.plot([-8.5,8.5,8.5,-8.5,-8.5],[0,0,1,1,0],color='black');ax.set(xlabel='Horizontal location, catcher perspective (inches)',ylabel='Height: 0 = zone bottom; 1 = zone top',title='Where incorrect called strikes are challenged')
    save('04_location',fig,f'3-inch × 0.2 zone-height cells; cells require n≥20. Shown: {int(shown.opportunities.sum()):,}/10,755.\nBlack outline is the plate-width rectangle; ABS also incorporates the ball radius.')
    fig,ax=plt.subplots(figsize=(7,6));ax.scatter(q.expected_rate,q.actual_rate,s=q.opportunities*1.1,alpha=.5);ax.plot([0,.4],[0,.4],'--',color='grey');ax.set(xlabel='Expected challenge rate (earlier-date models)',ylabel='Actual challenge rate',title=f'Batter behavior relative to opportunity difficulty (n={len(q)} batters)');ax.xaxis.set_major_formatter(PercentFormatter(1));ax.yaxis.set_major_formatter(PercentFormatter(1))
    for _,r in pd.concat([q.nlargest(1,'above_expected'),q.nsmallest(1,'above_expected')]).iterrows(): ax.annotate(r.batter_name,(r.expected_rate,r.actual_rate),fontsize=7)
    save('05_batters',fig,f'At least 50 predicted opportunities per batter; {int(q.opportunities.sum()):,} opportunities total.\nBubble size denotes opportunity count. Candidate behavior comparisons, not talent rankings.')
    cp=te[['challenged']].copy();cp['probability']=preds[selected];cp['bin']=pd.qcut(cp.probability,10,duplicates='drop').astype(str)
    ca=cp.groupby('bin').agg(n=('challenged','size'),challenges=('challenged','sum'),predicted=('probability','mean'),observed=('challenged','mean')).sort_values('predicted').reset_index();table('calibration',ca)
    fig,ax=plt.subplots(figsize=(6,6));ax.plot(ca.predicted,ca.observed,'o-');ax.plot([0,1],[0,1],'--',color='grey');ax.set(xlabel='Predicted challenge probability',ylabel='Observed challenge rate',title=f'Temporal test calibration: Model {selected}');ax.xaxis.set_major_formatter(PercentFormatter(1));ax.yaxis.set_major_formatter(PercentFormatter(1))
    save('06_calibration',fig,f'August 1–September 9, 2026; n={len(te):,}, challenges={int(te.challenged.sum()):,}.\nTen equal-frequency prediction groups. Selected on July, fitted through July 31.')
    t=inc[inc.cluster=='game_pk'];fig,ax=plt.subplots(figsize=(8,5));ax.errorbar(np.arange(len(t)),t.delta_log_loss,yerr=[t.delta_log_loss-t.ci95_low,t.ci95_high-t.delta_log_loss],fmt='o',capsize=4);ax.axhline(0,color='grey',ls='--');ax.set_xticks(np.arange(len(t)),t.baseline+' → '+t.added);ax.set(ylabel='Change in held-out log loss (lower is better)',title='Incremental information in challenge prediction')
    save('07_increment',fig,f'Temporal test n={len(te):,}. Paired game-cluster bootstrap, 1,000 resamples; 95% intervals.\nA geometry; B +count; C +context; D +inventory; E adds pitch features to selected baseline.')
    (out/'FIGURES.md').write_text('# Article 2 analytical figures\n\n'+'\n'.join(captions))
    feature_cols=sorted(set(['abs_distance_inches']+sum([n+c for n,c in specs.values()],[])))
    # Only selected decision-time predictors are passed to estimators.
    forbidden={'challenge_outcome','official_abs_call','recognized','challenged','survival_class','batter_id','batter_name'}
    assert not (set(feature_cols)&forbidden)
    missing=f[feature_cols].isna().sum(); assert f.challenged.notna().all()
    after={str(p.relative_to(root)):digest(p) for p in protected};assert before==after,'Frozen input modified'
    metadata={'seed':SEED,'source_root':str(root),'source_checksums':before,'frozen_files_unchanged':True,'population':a,'selected_baseline':selected,'model_specs':{k:{'numeric':v[0],'categorical':v[1]} for k,v in specs.items()},'distance_spec':'5 quantile knots, cubic B spline, linear extrapolation; training-only transformer fit','validation_scores':vals,'material_log_loss_threshold':.001,'batter_stability':stability,'feature_missingness':missing.to_dict(),'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__,'statsmodels':statsmodels.__version__,'matplotlib':matplotlib.__version__},'source_script_sha256':digest(Path(__file__))}
    (out/'manifest.json').write_text(json.dumps(metadata,indent=2,default=str)+'\n')
    write_report(out,tables,metadata,dist,curve,coefficients)
    print(comparison.to_string(index=False));print('Complete:',out,flush=True)

def write_report(out,t,meta,dist,curve,co):
    selected=meta['selected_baseline']; a=meta['population'];test=t['model_comparison'].query("period == 'test'"); inc=t['incremental_performance'].query("cluster == 'game_pk'")
    counts=t['count']; two=counts[counts['count'].str.endswith('2')];other=counts[~counts['count'].str.endswith('2')]
    decreases=int((np.diff(dist.challenge_rate)<0).sum()); fitted_decreases=int((np.diff(curve.standardized_probability)<0).sum())
    text=f'''# Article 2 research report — What makes a batter challenge?

Research evidence for review; **not an article draft**. Frozen 2026-03-25–2026-09-09 snapshot. No new acquisition, no reconstruction changes, no causal interpretation.

## Population and provenance

The existing `src.sprint3.build_population` independently reproduces **{a['legal_recognition_opportunities']:,} legal incorrect-called-strike opportunities**, **{a['recognized']:,} challenges**, and **{a['recognized']/a['legal_recognition_opportunities']:.2%}** observed challenging. Every outcome is whether the batter challenged; official overturn success is not used as the outcome. This matters because one reconstructed opportunity was officially confirmed.

Frozen validation reproduces 9,482/9,485 official decisions. The population comes from processed pitch records, not from filtering successful challenges. Exclusions:

{markdown(t['population_exclusions'])}

All 10,755 rows enter description and the temporal partitions; none are silently dropped for feature missingness. Missing numeric pitch characteristics are median-imputed with indicators inside training folds. Empty runner identifiers indicate unoccupied bases per existing parser. Missingness for every source/derived column is in `tables/missingness.csv`; predictor-specific counts and package versions are in the manifest. No validated public pre-pitch leverage index was found in these processed data, so this sprint uses transparent situation variables and does **not** manufacture a leverage index.

`manifest.json` records SHA-256 hashes of processed inputs, frozen publication-validation artifacts and source modules before and after analysis. They match. Raw response receipts and the existing run manifest retain original retrieval dates and raw hashes. Exact raw-byte regeneration requires the repository's archived objects; endpoint re-downloads can change. Reproduction of this sprint is offline from accepted processed inputs.

## Feature definitions and decision timing

- Absolute miss is the original signed circle/rectangle boundary distance in feet ×12, positive for these reconstructed balls. No revised geometry is used.
- Horizontal/vertical distances are positive center-to-rectangle components in inches, **not independently radius-adjusted misses**. The actual miss distance incorporates the 1.45-inch ball radius and rounded corners. `miss_side` distinguishes above/below, inside/outside and corners using actual batting stance; signed plate side is catcher's perspective. Hand/location combinations allow handedness differences.
- Count, outs, runners and home/away scores come from Statcast pre-pitch state, confirmed by the source parser and `state_timing == PRE_PITCH`. Offense score differential reverses home-minus-away for the top half.
- Late-close: inning ≥7 and absolute batting-team margin ≤2. Potential plate-appearance ending: two strikes. Potential inning ending: two strikes and two outs. Potential game ending: also bottom 9+ with batting team behind. These mean a strikeout could end play, without using what happened afterward; dropped-third-strike and unusual-event exceptions prevent calling them certain endings.
- Inventory is the existing sequential reconstruction, recorded **before** processing the current challenge. Both teams start with two; official confirmed challenges decrement inventory, overturned challenges retain it. At each extra inning, a team at zero receives one. Unknown/conflicting history propagates uncertainty, and position-player pitching blocks availability. We reuse `affected_team_challenges_remaining`, never recount from successful challenges or assume all rows start with two. One-left interacts with inning and late-close. No true leverage interaction can be estimated here.
- Velocity, movement, spin, extension, release position and pitch family describe the pitch already seen when a batter decides. They are physical covariates, not a claim the batter sees tracking-system numerical measurements. Official results, subsequent counts/scores, eventual winners, future inventory, identities and challenge outcome never enter model predictors.

## Model and validation design

Fixed L2 logistic regression, C=1, no class reweighting, 5-quantile-knot cubic spline for absolute distance, training-only preprocessing, seed {meta['seed']}. Sparse categories use one-hot encoding, unknown categories map to zero. Continuous features are scaled; no hyperparameter search. Distance is not constrained to be monotone.

Stages are cumulative: A geometry; B A+count; C B+game context; D C+inventory and its interactions. E adds the single prespecified pitch block to the selected A–D baseline. This ordering isolates context beyond count and inventory beyond both. It differs from earlier sprints' A/B/C labels; compare definitions, not letters.

Training uses March–June; July selects the simplest A–D model within .001 log loss of the best. The selected baseline is **{selected}**. Every stage is refitted on March–July and evaluated once on August–September 9. E is an incremental test, not allowed to redefine the non-pitch baseline after seeing final test scores.

{markdown(t['temporal_split'])}

{markdown(test)}

The test period is held out from this sprint's fitting and selection, but the same frozen season has appeared in earlier exploratory sprints. This is temporal validation of a specified analysis, **not a pristine never-seen external replication**. More-season validation remains needed. The same batters can occur on both sides of a boundary; no batter identity enters the model, but persistent team/player characteristics can still induce dependence. Game- and batter-cluster paired bootstrap intervals address test-loss dependence conditionally on the fitted models; they do not include retraining uncertainty.

### Incremental held-out performance

Negative change means improvement. Material improvement was defined before score inspection as ≥.001 lower log loss, with confidence and stability considered separately.

{markdown(inc)}

Full metrics include Brier, ROC AUC, calibration intercept/slope and summed out-of-sample log-likelihood gain. Classification accuracy is not used. E tests the complete pitch block once; a null result is not proof that every physical pitch attribute has zero effect.

## Descriptive geometry and count

Eight equal-frequency distance bins were constructed without reference to outcomes, providing about 1,344 opportunities per bin instead of sparse arbitrary tail bins. Wilson intervals describe binomial sampling uncertainty only; repeated-observation robustness uses cluster-based analyses below.

{markdown(dist)}

There are **{decreases} downward steps among seven adjacent observed-bin comparisons**, and **{fitted_decreases} downward steps on the 100-point adjusted spline grid**. This directly checks monotonicity rather than assuming it; smooth monotonic association is not established by a positive linear coefficient alone. The plotted spline stops at the 99th percentile to avoid tail extrapolation claims. Full tail observations remain in every model.

Pre-pitch two-strike counts: **{int(two.challenges.sum()):,}/{int(two.opportunities.sum()):,} ({two.challenges.sum()/two.opportunities.sum():.2%})**, versus **{int(other.challenges.sum()):,}/{int(other.opportunities.sum()):,} ({other.challenges.sum()/other.opportunities.sum():.2%})** for other counts.

{markdown(t['count_adjusted'])}

Geometry-adjusted probabilities average predictions after replacing count over the same observed geometry distribution; they are descriptive standardizations, not interventions. `geometry_count_associations.csv` contains odds ratios and batter-cluster robust intervals from an unpenalized spline model. Coefficients for count compare with 0-0. Correlated geometry columns are omitted from this inference model to avoid redundant radius/component terms; its coefficients are not the regularized prediction model's coefficients. Direction ablation compares distance+hand with full geometry:

{markdown(t['direction_ablation'])}

The conditional below-versus-above miss odds ratio is 1.74 (batter-cluster 95% CI 1.44–2.10; full sample n=10,755), controlling distance, count and hand/plate side in the association model. This supports directional asymmetry; corner and inside/outside coefficients require their individual support and intervals. Location tables and the zone map show substantial location mix differences. Use held-out ablation plus conditional coefficient intervals when discussing direction beyond distance; do not interpret raw heatmap colors as adjusted effects. Hand/location estimates can have limited support in rare corner cells.

## Situation and inventory

{markdown(t['situation_late_close'])}

{markdown(t['inventory'])}

Full inning, half-inning, score, outs, runner-state and potential-ending distributions are supplied separately. Raw inventory/context rates are confounded by count, geometry, game history and team/player behavior. C versus B and D versus C are the primary incremental checks, with game and batter bootstrap intervals. None establishes that conserving a challenge causes a change in behavior. Potential game-ending samples are explicitly reported in `situation_game_ending.csv`; avoid strong conclusions from rare cells.

## Batter actual versus expected behavior

Expected probabilities use expanding monthly fits (April–September), always trained on earlier dates without batter identity. March supplies the initial training set and has no honest prior-date prediction; its 391 opportunities remain in the primary population but are explicitly excluded from residual aggregation. Thus batter residuals cover 10,364 opportunities. The baseline specification was selected on July; earlier rolling residuals are retrospective descriptive diagnostics, not a fully prospective validation of that selection procedure. Early models train on few opportunities and can be miscalibrated.

The main candidate threshold is **50 predicted opportunities**: at p=.20, binomial sampling alone gives an approximate 95% halfwidth of 11 percentage points, so even this is only a candidate screen. Thresholds 30/50/75/100 are shown below. Actual-minus-summed-expected challenges measure challenge frequency conditional on modeled opportunities, **not recognition skill, optimal decisions, or challenge accuracy**.

{markdown(t['batter_thresholds'])}

`batter_actual_expected.csv` contains actual/expected counts/rates, above-expected counts, conditional normal intervals using sum p(1-p), whole-game within-batter bootstrap residual-rate intervals (1,000 resamples), and simultaneous Bonferroni intervals for the qualifying set. Normal intervals assume conditional independence and fixed predictions. The game bootstrap allows within-game dependence but not arbitrary season-long within-batter dependence. Both omit fitted-baseline uncertainty and may understate total uncertainty. They must not be presented as definitive talent intervals. The additional residual shrinkage divides above-expected counts by n+50 (a fixed 50-opportunity zero-effect prior equivalent), providing transparent descriptive stabilization, **not a fitted hierarchical talent model**. Adjusted rates are additive reference-rate summaries and are not guaranteed probabilities outside the observed range.

Qualified batter summary:

{markdown(t['batter_actual_expected'].query('qualified')[["batter_name","opportunities","actual","expected","above_expected","conditional_ci95_low","conditional_ci95_high"]])}

Candidate lists (up to ten per direction and up to ten per shrunken adjusted direction, only with the corresponding residual sign) are in `batter_candidates.csv`. Broad leaderboards and best/worst labels are not justified. The two-period stability diagnostic requires ≥20 observations in each period: {json.dumps(meta['batter_stability'])}. It can suggest persistence but does not establish innate recognition ability. Between-player differences can reflect coaching, teammates, pitch perceptions, omitted context, and baseline calibration.

## Robustness and diagnostic limits

Across every boundary threshold, B improves on A, C improves on B, and E worsens D. Removing the top ten development-period batters or top three teams leaves this ordering intact. Linear-distance A/D improve loss slightly, so spline flexibility is not required to reproduce the principal result. Compare increments **within** each retained sample; absolute loss across boundary thresholds is not comparable because prevalence and difficulty change.

{markdown(t['distance_sensitivity_association'])}

Count improves on geometry in all six rolling months. Context improves on count in five of six; it worsens April predictions when trained on only 391 March rows. Inventory also worsens April while improving five later months, and pitch features worsen the selected baseline in all six rolling months. Rolling early-season models have limited training support. Inspect monthly rather than only pooled performance; the final test is the primary evaluation. Only nine batters reach the conservative 50-opportunity residual threshold, and none reaches 75. This is a substantive sample-size limitation, not a reason to lower the threshold until attractive rankings appear.

- Boundary sensitivity refits A–E after removing misses ≤0, .05, .10, .25 and .50 inches. Every resulting denominator is in `robustness.csv`; the primary 10,755 population is unchanged. These are sensitivity analyses, not replacement populations.
- Alternative distance specification replaces the cubic spline with a linear term for A and the selected baseline, holding other choices fixed.
- Expanding monthly results supply an additional temporal stability check (`monthly_model_performance.csv`), including small March-trained April models. These rolling tests are not an independent new dataset.
- Game and batter clustered bootstrap intervals compare final-test losses. Cluster-robust batter standard errors assess geometry/count association. They do not eliminate unmeasured confounding or establish player residual independence.
- Excluding the ten most common batters or three most common teams (selected by development-period opportunity counts) refits A–E and tests on the corresponding remaining test rows. `concentration.csv` reports retained denominators. This is a targeted influence check, not exhaustive leave-every-team-out analysis.
- No dedicated catcher, pitcher or umpire analysis is performed. Their potential confounding remains unresolved.

## Recognition versus accuracy and future decision quality

The available source supports separate future official challenge-accuracy measurement: 2,112 official overturns / 4,335 batter challenges in the frozen publication audit. That accuracy numerator is not interchangeable with the 2,112 challenges among reconstructed opportunities: one confirmed reconstructed error and one overturned reconstructed strike offset in the totals. Opportunity recognition therefore must stay separate from official success rate.

A broader decision-quality metric would require all legal decision opportunities (including correctly called strikes), calibrated pre-decision overturn probabilities, reliable inventory and timing, validated count/state values for hold versus overturn, future resource cost and uncertainty. Player comparisons would additionally need partial pooling, out-of-time calibration and replication, reliable attribution of who prompted the challenge, and a defensible utility criterion. This dataset cannot identify a batter's private certainty, signals from others, motivations, or causal decision quality.

## Reproduction and deliverables

Run the adjacent `analyze.py` with the accepted repository as `--source-root` and a new `--output` directory. See `README.md` for exact setup and command. All CSVs, Markdown tables, report, plotting data and PNG/PDF figures are generated by code. `FIGURES.md` displays the seven review figures. No Article 1 files are written.

## Research findings summary

### Strong Evidence

- **Miss distance:** observed rates rise across all eight bins, from 162/1,345 (12.04%) in the closest group to 435/1,345 (32.34%) in the farthest. The adjusted spline rises on its central-support grid. Boundary sensitivity retains a positive adjusted per-inch association; this supports a broad increasing relationship, not a mathematical monotonic law.
- **Direction beyond distance:** full geometry improves final-test loss over distance+hand alone; paired cluster intervals appear in `direction_increment.csv`. Location carries information beyond the scalar distance: log-loss gain .00866 on 2,830 test opportunities (567 challenges), game-cluster 95% interval [.00449, .01318].
- **Count:** adding count reduces test log loss by .03955 (n=2,830, 567 challenges), with both game and batter cluster intervals below zero. Count remains informative after geometry adjustment.
- **Game context:** adds a smaller .00484 loss reduction beyond count on the same test rows, with both cluster intervals below zero. This supports the context block collectively, not every individual flag or a leverage effect.
- The requested population is reproducible: 2,112 challenges / 10,755 legal reconstructed incorrect-strike opportunities (19.64%).
- Raw count and miss-distance distributions are well measured in this frozen snapshot; the tables provide denominators and uncertainty. Count's incremental evidence should be judged from B–A test loss and both clustered intervals, rather than the raw strike-three contrast alone.

### Suggestive Evidence

- Adjusted location differences and batter residual candidates warrant follow-up. Conditional residual uncertainty and prior exploratory use limit interpretation as stable player traits.
- Inventory's .00126 test loss reduction has intervals spanning zero. It was selected on July, but its separate incremental value is suggestive, not robustly established. Raw rates are 612/3,168 (19.32%) with one challenge and 1,500/7,587 (19.77%) with two. These do not measure a causal conservation effect.

### No Evidence Found

- **Pitch-characteristic predictive gain:** E worsens final-test loss by .00043 and Brier by .00019 (n=2,830, 567 challenges); its intervals span zero. It also worsens July validation and each boundary/influence-check comparison. No material incremental improvement is found for this fixed pitch block.
- **Need for spline complexity:** linear-distance sensitivity performs slightly better on final-test A and D. We retain the prespecified models, but do not claim nonlinear modeling is necessary.
- No causal effect, optimal-decision claim or ranking of intrinsic recognition skill is established by this observational sprint.
- See the numerical assessment below for incremental blocks that fail the prespecified predictive-improvement threshold. Failure to improve prediction does not prove an effect is absent.

### Cannot Determine From Available Data

- A validated numerical pre-pitch leverage index, private confidence, advice from teammates, who initiated recognition, or causal reasons for challenging.
- Whether not challenging was a mistake, whether a successful challenge was optimal, or a complete player decision-quality ranking.

### Recommended Article 2 Claims

- State the frozen dates, population definition, denominator and estimated nature of unchallenged-call classification.
- Larger reconstructed misses are challenged more often, with location contributing beyond distance; count adds substantial predictive information, and game context a smaller amount. State exact temporal test sizes and performance.
- The tested pitch-characteristic block adds no meaningful held-out gain. Inventory is a plausible smaller contributor whose incremental uncertainty remains unresolved.
- Treat batter lists as opportunity-adjusted behavior candidates for further validation.

### Claims We Should NOT Make

- “These are the best/worst challengers,” “every unchallenged miss was a bad decision,” or “a successful challenge was necessarily correct strategy.”
- “Count/context/inventory causes challenging,” “the spline proves monotonicity at every distance,” or “pitch physics has no effect.”
- “All 2026 data,” “independent external replication,” or “the 19.64% recognition rate is challenge accuracy.”
'''
    text+='\n### Numerical assessment of tested information blocks\n\n'
    for _,r in inc.iterrows():
        claim='meets the material improvement threshold with a game-cluster interval below zero' if r.delta_log_loss<=-.001 and r.ci95_high<0 else 'does not establish material improvement with a game-cluster interval below zero'
        text+=f'- **{r.baseline} → {r.added}**: Δlog loss {r.delta_log_loss:+.5f}, 95% CI [{r.ci95_low:+.5f}, {r.ci95_high:+.5f}], n={int(r.n):,}: {claim}.\n'
    (out/'REPORT.md').write_text(text)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();main(args.source_root.resolve(),args.output.resolve())
