"""Small predeclared ensemble grid; validation ranks freeze score scales."""
import json,time
from pathlib import Path
import numpy as np,joblib
from scipy.special import expit
from features_v2 import OUT,MODELS
from search_v2 import Recorder

def score_bundle(b,d):
    if isinstance(b['model'],BlendModel):return b['model'].predict_proba(d)[:,1]
    if 'route_encoder' in b:d=d.join(b['route_encoder'].transform(d))
    if b['pre'] is not None:X=b['pre'].transform(d)
    else:
        X=d[b['cats']+b['nums']].copy()
        for c in b['cats']:X[c]=X[c].astype(object)
        if 'fill_numeric' in b:X[b['nums']]=X[b['nums']].fillna(b['fill_numeric'])
    return b['model'].predict_proba(X)[:,1]

class BlendModel:
    def __init__(self,members,weights,references):
        self.members=members;self.weights=weights;self.references=references
    def get_params(self,deep=True):return {'member_files':self.members,'weights':self.weights,'scale':'validation empirical ranks; no evaluation labels'}
    def scale(self,s,ref):
        return (np.searchsorted(ref,s,side='left')+np.searchsorted(ref,s,side='right'))/(2*len(ref))
    def combine(self,scores):return sum(w*self.scale(s,r) for w,s,r in zip(self.weights,scores,self.references))
    def predict_proba(self,d):
        scores=[score_bundle(joblib.load(MODELS/name),d) for name in self.members]
        s=self.combine(scores);return np.column_stack([1-s,s])

def run():
    rec=Recorder('blend')
    groups={'base':[['logistic'],['lightgbm'],['catboost']],
            'location':[['geo_logistic','station_logistic','rolling_logistic'],
                        ['geo_lightgbm','station_lightgbm','rolling_lightgbm'],['geo_catboost','station_catboost','rolling_catboost']]}
    for variant,algos in groups.items():
        for floor in [85,90]:
            files=[]
            for families in algos:
                candidates=[]
                for family in families:
                    p=OUT/f'{family}_selected.json'
                    if not p.exists():continue
                    for key,meta in json.loads(p.read_text()).items():
                        if meta['recall_floor']!=floor or 'hypothesis' in key:continue
                        if variant=='location' and family.startswith('rolling') and not key.startswith('location'):continue
                        candidates.append((meta,MODELS/f'{family}_{key}.joblib'))
                meta,path=max(candidates,key=lambda x:(x[0]['precision'],x[0]['AP']))
                files.append(path.name)
            raw=[np.load(MODELS/f'{Path(f).stem}_validation.npz') for f in files]
            assert all(np.array_equal(raw[0]['y'],r['y']) for r in raw)
            scores=[r['score'] for r in raw];refs=[np.sort(s) for s in scores]
            weightlist=[[1/3]*3]
            for i,j in [(0,1),(0,2),(1,2)]:
                for w in [.25,.5,.75]:
                    a=[0.,0.,0.];a[i]=w;a[j]=1-w;weightlist.append(a)
            for weights in weightlist:
                active=[i for i,w in enumerate(weights) if w]
                m=BlendModel([files[i] for i in active],[weights[i] for i in active],[refs[i] for i in active])
                s=m.combine([scores[i] for i in active]);start=time.monotonic()
                rec.add(f'source{floor}_weights{weights}',variant,m,None,s,raw[0]['y'],start,cats=[],nums=[])
    print('Fixed-grid blend selection complete; no test evaluation performed.',flush=True)

def run_common():
    rec=Recorder('blend_common')
    for variant in ['base','location']:
        for floor in [85,90]:
            files=[f'common_{variant}_{algo}_{floor}.joblib' for algo in ['logistic','lightgbm','catboost']]
            raw=[np.load(MODELS/f'{Path(f).stem}_validation.npz') for f in files]
            assert all(np.array_equal(raw[0]['y'],r['y']) for r in raw)
            scores=[r['score'] for r in raw];refs=[np.sort(s) for s in scores]
            weights_grid=[[1/3]*3]
            for i,j in [(0,1),(0,2),(1,2)]:
                for w in [.25,.5,.75]:
                    weights=[0.,0.,0.];weights[i]=w;weights[j]=1-w;weights_grid.append(weights)
            for weights in weights_grid:
                active=[i for i,w in enumerate(weights) if w]
                m=BlendModel([files[i] for i in active],[weights[i] for i in active],[refs[i] for i in active])
                s=m.combine([scores[i] for i in active])
                rec.add(f'source{floor}_weights{weights}',variant,m,None,s,raw[0]['y'],time.monotonic(),
                        cats=[],nums=[],validation_start='2024-04-01')
    print('Common-validation blends selected without test evaluation.',flush=True)

if __name__=='__main__':run()
