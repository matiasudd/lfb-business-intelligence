"""Freeze validation choices, then score this retrospective test exactly once."""
from pathlib import Path
import json,hashlib,datetime
import numpy as np,pandas as pd,joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import average_precision_score,roc_auc_score
from rolling_outcomes import load_rolling
from features_v2 import ROOT,OUT,MODELS,BASE
from search_v2 import points
from experiment import metric,jsonable
from blend_models import score_bundle
from threadpoolctl import threadpool_limits

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def freeze():
    assert not (OUT/'round2_test_results.csv').exists(),'Test already scored; do not silently reopen selection.'
    entries=[]
    for family in ['common','blend_common']:
        selected=json.loads((OUT/f'{family}_selected.json').read_text())
        for key,meta in selected.items():
            p=MODELS/f'{family}_{key}.joblib'
            entries.append({'key':p.stem,'file':p.name,'sha256':sha(p),'validation':meta,
                            'validation_period':'2024-04-01 through 2024-06-30'})
    original={}
    for family in ['logistic','encoded_logistic','lightgbm','catboost','geo_logistic','geo_lightgbm','geo_catboost',
                   'station_logistic','station_lightgbm','station_catboost','rolling_logistic','rolling_lightgbm','rolling_catboost']:
        p=OUT/f'{family}_selected.json'
        if p.exists():
            for key,meta in json.loads(p.read_text()).items():
                if 'hypothesis' in key:continue
                location=family.startswith(('geo_','station_')) or (family.startswith('rolling_') and meta['variant'].startswith('location'))
                group=('location' if location else 'base',meta['recall_floor'])
                if group not in original or (meta['precision'],meta['AP'])>(original[group][0]['precision'],original[group][0]['AP']):
                    original[group]=(meta,MODELS/f'{family}_{key}.joblib')
    for (group,floor),(meta,p) in original.items():
        entries.append({'key':f'original_window_{group}_{floor}','file':p.name,'sha256':sha(p),'validation':meta,
                        'validation_period':'2024-01-01 through 2024-06-30'})
    primary={}
    for group in ['base','location']:
        for floor in [85,90]:
            choices=[e for e in entries if e['key'].startswith((f'common_{group}_',f'blend_common_{group}_'))
                     and e['validation']['recall_floor']==floor]
            winner=max(choices,key=lambda e:(e['validation']['precision'],e['validation']['AP']))
            primary[f'{group}_{floor}']=winner['key']
    plan={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prediction_time':'dispatch only; no 2-minute update',
          'target':'AttendanceTimeSeconds >= 600','cohort_rows':384627,'test_rows':102248,
          'primary_rule':'For each input base and recall floor, maximise precision on identical April-June validation rows; AP tie-break.',
          'thresholds_are_validation_only':True,'test_has_prior_exposure_in_coursework':True,
          'test_period':'2024-07-01 through 2024-12-30','primary':primary,'entries':entries,
          'prohibited':'Current-row turnout, travel, arrival, delay codes, final pump rank, incident response outcomes.',
          'qualification':'Conditional retrospective source fields; published geography as-of timing and 2025 station addresses unverified for 2023. Recent histories assume immediate arrival feedback.'}
    (OUT/'round2_locked_plan.json').write_text(json.dumps(jsonable(plan),indent=2),encoding='utf-8')
    return plan

def run():
    plan=freeze();d=load_rolling();te=d[d.partition.eq('test')].copy();y=te.target.to_numpy()
    assert len(te)==102248 and y.sum()==7433
    rows=[];scores={};bundles={}
    for e in plan['entries']:
        p=MODELS/e['file'];assert sha(p)==e['sha256'];b=joblib.load(p);s=score_bundle(b,te)
        m=metric(y,s,e['validation']['threshold'])
        row={'key':e['key'],'family':e['validation']['family'],'variant':e['validation']['variant'],
             'candidate':e['validation']['candidate'],'validation_period':e['validation_period'],
             'recall_floor':e['validation']['recall_floor'],'validation_precision':e['validation']['precision'],
             'validation_recall':e['validation']['recall'],'AP':average_precision_score(y,s),'AUC':roc_auc_score(y,s),**m}
        scores[e['key']]=s;bundles[e['key']]=b;rows.append(row)
    # Refit the exact original hour-only C2 specification on 2023 only.
    tr=d[d.partition.eq('train')];enc=OneHotEncoder(handle_unknown='ignore');X=enc.fit_transform(tr[['hour']]);V=enc.transform(te[['hour']])
    m=LogisticRegression(class_weight='balanced',C=1.,max_iter=1000,random_state=423)
    with threadpool_limits(limits=4):m.fit(X,tr.target);s=m.predict_proba(V)[:,1]
    orig=metric(y,s,.5);assert [orig[k] for k in ['TN','FP','FN','TP']]==[50298,44517,2820,4613]
    rows.append({'key':'C2_original','family':'Logistic','variant':'hour_only','candidate':'C2 unchanged','recall_floor':None,
                 'AP':average_precision_score(y,s),'AUC':roc_auc_score(y,s),**orig});scores['C2_original']=s
    table=pd.DataFrame(rows);table.to_csv(OUT/'round2_test_results.csv',index=False)
    np.savez_compressed(OUT/'round2_test_scores.npz',y=y,incident=te.IncidentNumber.to_numpy(dtype=str),**scores)
    keys=['C2_original']+list(dict.fromkeys(plan['primary'].values()))
    primary=table.set_index('key').loc[keys].reset_index();primary.to_csv(OUT/'primary_comparison.csv',index=False)
    monthly=[];subgroups=[]
    for key in keys:
        threshold=float(table.set_index('key').loc[key,'threshold']);s=scores[key]
        for month,indices in te.groupby(te.timestamp.dt.strftime('%Y-%m')).indices.items():
            ix=np.asarray(indices);monthly.append({'key':key,'month':month,'n':len(ix),'positives':int(y[ix].sum()),**metric(y[ix],s[ix],threshold)})
        groupings={'origin_type':te.origin_type.to_numpy(),
                   'location_join':np.where(te.location_available.eq(1),'matched','missing'),
                   'distance':pd.cut(te.station_distance_km,[-1,2,5,np.inf],labels=['0-2km','2-5km','5km+']).astype(object).fillna('unavailable').to_numpy()}
        for name,g in groupings.items():
            for value in np.unique(g):
                ix=np.flatnonzero(g==value)
                subgroups.append({'key':key,'group':name,'value':value,'n':len(ix),'positives':int(y[ix].sum()),**metric(y[ix],s[ix],threshold)})
    pd.DataFrame(monthly).to_csv(OUT/'monthly_test.csv',index=False);pd.DataFrame(subgroups).to_csv(OUT/'subgroup_test.csv',index=False)
    bootstrap(te,table,scores,keys)
    audit={'test_rows':len(te),'test_positives':int(y.sum()),'models_and_policies':len(rows),'primary':plan['primary'],
           'C2_exact_reproduction':True,'test_data_sha256':sha(BASE/'data/mobilisations_2023_2024_clean.csv.gz'),
           'no_test_threshold_tuning':True,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (OUT/'round2_evaluation_complete.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print(primary[['key','precision','recall','FN','FP','alerts']].to_string(index=False),flush=True)

def bootstrap(te,table,scores,keys):
    y=te.target.to_numpy();codes,unique=pd.factorize(te.IncidentNumber);n=len(unique);arrays=[]
    for key in keys:
        threshold=float(table.set_index('key').loc[key,'threshold']);pred=scores[key]>=threshold
        arrays.append(np.stack([np.bincount(codes,weights=condition,minlength=n) for condition in [pred&(y==1),pred&(y==0),~pred&(y==1)]]))
    arrays=np.stack(arrays);rng=np.random.default_rng(423);samples=[]
    for _ in range(400):
        weights=np.bincount(rng.integers(0,n,n),minlength=n);counts=arrays@weights
        samples.append(np.stack([counts[:,0]/(counts[:,0]+counts[:,1]),counts[:,0]/(counts[:,0]+counts[:,2])],axis=1))
    samples=np.stack(samples);rows=[]
    for i,key in enumerate(keys):
        low,high=np.quantile(samples[:,i,:],[.025,.975],axis=0)
        rows.append({'key':key,'precision_lower':low[0],'precision_upper':high[0],'recall_lower':low[1],'recall_upper':high[1],
                     'replicates':400,'incident_clusters':n})
    pd.DataFrame(rows).to_csv(OUT/'incident_bootstrap.csv',index=False)

if __name__=='__main__':run()
