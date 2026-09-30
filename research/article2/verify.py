"""Independent artifact checks; optional deterministic reproduction comparison."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def main(root,out,compare):
    meta=json.loads((out/'manifest.json').read_text());checks=[]
    def check(v,label):
        assert v,label
        checks.append(label)
    def table(n):return pd.read_csv(out/'tables'/f'{n}.csv')
    check(all(digest(root/k)==v for k,v in meta['source_checksums'].items()),'Frozen source hashes unchanged')
    overall=table('overall').iloc[0]
    check(overall.opportunities==10755 and overall.challenges==2112,'Exact primary population and outcome count')
    for name in ['count','inning','inventory','distance','month','location']:
        x=table(name);check(x.opportunities.sum()==10755 and x.challenges.sum()==2112,f'{name}: complete denominators')
    check(set(table('count')['count'])=={f'{b}-{s}' for b in range(4) for s in range(3)},'All twelve counts reported')
    split=table('temporal_split').set_index('split')
    check(split.loc['train','end']<split.loc['validation','start'] and split.loc['validation','end']<split.loc['test','start'],'Strict temporal partitions')
    pred=table('test_predictions');check(len(pred)==2830 and pred.pitch_key.is_unique and pred.challenged.sum()==567,'Unique temporal-test predictions')
    for _,r in table('model_comparison').query("period=='test' and model!='intercept'").iterrows():
        p=pred[r.model]
        check(np.allclose([log_loss(pred.challenged,p),brier_score_loss(pred.challenged,p),roc_auc_score(pred.challenged,p)],[r.log_loss,r.brier,r.auc],atol=1e-9,rtol=1e-9),f'Model {r.model}: held-out metrics independently recomputed')
    for k,v in meta['model_specs'].items():
        check(not set(v['numeric']+v['categorical'])&{'challenged','recognized','challenge_outcome','official_abs_call','survival_class','batter_id'},f'Model {k}: no outcome or identity predictor')
    rolling=table('rolling_predictions');selected=meta['selected_baseline'];valid=rolling[rolling[selected].notna()]
    check(len(rolling)==10755 and len(valid)==10364 and rolling.pitch_key.is_unique,'Rolling coverage explicitly excludes only first 391 training rows')
    folds=table('rolling_folds');check((folds.train_end<folds.test_start).all(),'Every rolling fold trains on earlier dates')
    b=table('batter_actual_expected')
    check(b.opportunities.sum()==len(valid) and b.actual.sum()==valid.challenged.sum() and np.isclose(b.expected.sum(),valid[selected].sum()),'Batter observed and expected counts reconcile to rolling predictions')
    check(np.allclose(b.above_expected,b.actual-b.expected),'Above-expected definition verified')
    c=table('batter_candidates');check((c.opportunities>=50).all(),'Every candidate meets opportunity threshold')
    check((c[c['list'].isin(['above','highest_adjusted'])].above_expected>0).all() and (c[c['list'].isin(['below','lowest_adjusted'])].above_expected<0).all(),'Candidate lists have the correct residual direction')
    check(len(list((out/'figures').glob('*.png')))==7 and len(list((out/'figures').glob('*.pdf')))==7,'Seven PNG and PDF figures present')
    for f in (out/'tables').glob('*.csv'): check(f.with_suffix('.md').exists(),f'Markdown counterpart: {f.name}')
    if compare:
        paths=list((out/'tables').glob('*'))+list((out/'figures').glob('*.png'))+[out/'REPORT.md',out/'FIGURES.md']
        check(all(digest(p)==digest(compare/p.relative_to(out)) for p in paths),'Repeated run: identical analytical tables, reports and PNGs')
    result={'passed':True,'checks':checks,'count':len(checks)}
    (out.parent/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--compare',type=Path);a=p.parse_args();main(a.source_root,a.output,a.compare)
