"""Predeclared temporal sensitivity: train through March, validate April-June."""
import json,time
from pathlib import Path
import numpy as np,pandas as pd,joblib
from sklearn.base import clone
from rolling_outcomes import load_rolling
from features_v2 import OUT,MODELS,CAT,NUM,PAST_NUM
from search_v2 import Recorder
from threadpoolctl import threadpool_limits

def run():
    d=load_rolling();tr=d[d.timestamp.lt('2024-04-01')].copy()
    va=d[d.timestamp.ge('2024-04-01')&d.timestamp.lt('2024-07-01')].copy()
    assert not set(tr.IncidentNumber)&set(va.IncidentNumber)
    assert not set(tr.IncidentNumber)&set(d.loc[d.partition.eq('test'),'IncidentNumber'])
    plan={'training_end_exclusive':'2024-04-01','validation_end_exclusive':'2024-07-01',
          'training_rows':len(tr),'validation_rows':len(va),'training_positives':int(tr.target.sum()),
          'validation_positives':int(va.target.sum()),'test_not_read_for_selection':True,
          'selection':'Freeze source-best hyperparameters from original validation; choose threshold on April-June only.'}
    (OUT/'recent_training_plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    rec=Recorder('recent');sources=[]
    groups={
        'base_logistic':['logistic','rolling_logistic'], 'base_lightgbm':['lightgbm','rolling_lightgbm'],
        'base_catboost':['catboost','rolling_catboost'],
        'location_logistic':['geo_logistic','station_logistic','rolling_logistic'],
        'location_lightgbm':['geo_lightgbm','station_lightgbm','rolling_lightgbm'],
        'location_catboost':['geo_catboost','station_catboost','rolling_catboost']}
    for label,families in groups.items():
        candidates=[]
        for f in families:
            p=OUT/f'{f}_selected.json'
            if p.exists():
                for key,meta in json.loads(p.read_text()).items():
                    if 'hypothesis' in key:continue
                    if f.startswith('rolling_') and label.startswith('base') and not meta['variant'].startswith('base'):continue
                    if f.startswith('rolling_') and label.startswith('location') and not meta['variant'].startswith('location'):continue
                    candidates.append((meta,MODELS/f'{f}_{key}.joblib'))
        # One fixed configuration per family/input group; select for the
        # user's primary lower bound, then examine both operating thresholds.
        chosen={}
        for goal in [85]:
            matches=[a for a in candidates if a[0]['recall_floor']==goal]
            if not matches:continue
            meta,path=max(matches,key=lambda a:(a[0]['precision'],a[0]['AP']))
            chosen[str(path)]=meta
        for path,meta in chosen.items():sources.append((label,Path(path),meta))
    plan['source_configurations']=[{'group':label,'path':path.name,'candidate':meta['candidate']} for label,path,meta in sources]
    (OUT/'recent_training_plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    for label,path,meta in sources:
        b=joblib.load(path);m=clone(b['model']);cats=b['cats'];nums=b['nums'];start=time.monotonic()
        if b['pre'] is not None:
            pre=clone(b['pre']);X=pre.fit_transform(tr);V=pre.transform(va)
            extra={}
            if 'lightgbm' in label:extra={'categorical_feature':list(range(len(cats)))}
            with threadpool_limits(limits=4):m.fit(X,tr.target,**extra);s=m.predict_proba(V)[:,1]
        else:
            pre=None;X=tr[cats+nums].copy();V=va[cats+nums].copy()
            for c in cats:X[c]=X[c].astype(object);V[c]=V[c].astype(object)
            if 'fill_numeric' in b:
                X[nums]=X[nums].fillna(b['fill_numeric']);V[nums]=V[nums].fillna(b['fill_numeric'])
            m.fit(X,tr.target,cat_features=cats);s=m.predict_proba(V)[:,1]
        rec.add(meta['family']+'_'+meta['candidate'],label,m,pre,s,va.target.to_numpy(),start,
                cats=cats,nums=nums,source_bundle=str(path),train_end='2024-04-01',validation_start='2024-04-01',
                **({'fill_numeric':b['fill_numeric']} if 'fill_numeric' in b else {}))
    print('Recent training sensitivity complete; no test evaluation performed.',flush=True)

def compare_on_common_validation():
    d=load_rolling();full=d[d.partition.eq('validation')]
    mask=full.timestamp.ge('2024-04-01').to_numpy();y=full.target.to_numpy()[mask]
    plan=json.loads((OUT/'recent_training_plan.json').read_text());rec=Recorder('common')
    for source in plan['source_configurations']:
        label=source['group'];path=MODELS/source['path'];b=joblib.load(path)
        arr=np.load(MODELS/f'{path.stem}_validation.npz');assert np.array_equal(arr['y'],full.target.to_numpy())
        rec.add('train_2023__'+b['metadata']['candidate'],label,b['model'],b['pre'],arr['score'][mask],y,time.monotonic(),
                cats=b['cats'],nums=b['nums'],train_end='2024-01-01',validation_start='2024-04-01',source_bundle=path.name,
                **({'fill_numeric':b['fill_numeric']} if 'fill_numeric' in b else {}))
    meta=json.loads((OUT/'recent_selected.json').read_text())
    seen=set()
    for key,row in meta.items():
        identity=(row['variant'],row['candidate'])
        if identity in seen:continue
        seen.add(identity);path=MODELS/f'recent_{key}.joblib';b=joblib.load(path)
        arr=np.load(MODELS/f'{path.stem}_validation.npz');assert np.array_equal(arr['y'],y)
        rec.add('train_to_March2024__'+row['candidate'],row['variant'],b['model'],b['pre'],arr['score'],y,time.monotonic(),
                cats=b['cats'],nums=b['nums'],train_end='2024-04-01',validation_start='2024-04-01',source_bundle=path.name,
                **({'fill_numeric':b['fill_numeric']} if 'fill_numeric' in b else {}))
    print('Original and recent fits compared on identical April-June rows.',flush=True)

if __name__=='__main__':run();compare_on_common_validation()
