"""Round 2: maximise precision subject to validation recall of 85% or 90%."""
import argparse,json,time,warnings,hashlib
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import precision_recall_curve,average_precision_score,roc_auc_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,OrdinalEncoder,StandardScaler
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits
from features_v2 import ROOT,OUT,MODELS,load_features,CAT,NUM,PAST_NUM,RouteEncoding,BASE
from experiment import metric,jsonable

def points(y,s):
    p,r,t=precision_recall_curve(y,s);p,r=p[:-1],r[:-1]
    out={}
    for goal in [.85,.9]:
        ix=np.flatnonzero(r>=goal-1e-12);i=ix[np.lexsort((t[ix],p[ix]))[-1]]
        out[str(int(goal*100))]=metric(y,s,t[i])
    return out

class Recorder:
    def __init__(self,family):self.family=family;self.rows=[];self.best={}
    def add(self,name,variant,model,pre,s,y,started,**extra):
        ps=points(y,s);ap=float(average_precision_score(y,s));auc=float(roc_auc_score(y,s))
        for floor,m in ps.items():
            row={'candidate':name,'variant':variant,'family':self.family,'recall_floor':int(floor),
                 'seconds':time.monotonic()-started,'AP':ap,'AUC':auc,**m}
            self.rows.append(row);key=f'{variant}_{floor}'
            score=(m['precision'],ap)
            if key not in self.best or score>tuple(self.best[key]['selection_score']):
                meta={**row,'selection_score':score,'parameters':model.get_params()}
                self.best[key]=jsonable(meta)
                bundle={'model':model,'pre':pre,'metadata':meta,**extra}
                joblib.dump(bundle,MODELS/f'{self.family}_{key}.joblib',compress=3)
                np.savez_compressed(MODELS/f'{self.family}_{key}_validation.npz',y=y,score=s)
        pd.DataFrame(self.rows).to_csv(OUT/f'{self.family}_validation.csv',index=False)
        (OUT/f'{self.family}_selected.json').write_text(json.dumps(self.best,indent=2),encoding='utf-8')
        print(f'{self.family} {variant} {name}: AP={ap:.3f}; P@85={ps["85"]["precision"]:.3f}; P@90={ps["90"]["precision"]:.3f}; {time.monotonic()-started:.1f}s',flush=True)

def run(family):
    d=load_features();tr=d[d.partition.eq('train')].copy();va=d[d.partition.eq('validation')].copy()
    y=tr.target.to_numpy();yv=va.target.to_numpy()
    rec=Recorder(family)
    if family=='logistic':
        for variant,nums in [('context',NUM),('past_completed',NUM+PAST_NUM)]:
            for freq in [1,5,20,50]:
                pre=ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore',min_frequency=freq),CAT),('num',StandardScaler(),nums)],sparse_threshold=1.)
                X=pre.fit_transform(tr);V=pre.transform(va)
                for cw in [None,'balanced']:
                    for c in [.02,.1,.5,2.]:
                        m=LogisticRegression(C=c,class_weight=cw,max_iter=2000,random_state=423)
                        start=time.monotonic()
                        with threadpool_limits(limits=4):m.fit(X,y);s=m.predict_proba(V)[:,1]
                        rec.add(f'C{c}_freq{freq}_{cw}',variant,m,pre,s,yv,start,cats=CAT,nums=nums)
    elif family=='encoded_logistic':
        for alpha in [10,50,200]:
            encoder=RouteEncoding(alpha=alpha);et,ev=encoder.fit_transform(tr,va)
            t=tr.join(et);v=va.join(ev);nums=NUM+PAST_NUM+et.columns.tolist()
            pre=ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore',min_frequency=20),CAT),('num',StandardScaler(),nums)],sparse_threshold=1.)
            X=pre.fit_transform(t);V=pre.transform(v)
            for cw in [None,'balanced']:
                for c in [.02,.1,.5,2.]:
                    m=LogisticRegression(C=c,class_weight=cw,max_iter=2000,random_state=423);start=time.monotonic()
                    with threadpool_limits(limits=4):m.fit(X,y);s=m.predict_proba(V)[:,1]
                    rec.add(f'alpha{alpha}_C{c}_{cw}','crossfit_routes',m,pre,s,yv,start,route_encoder=encoder,cats=CAT,nums=nums)
    elif family=='lightgbm':
        from lightgbm import LGBMClassifier
        for variant,nums in [('context',NUM),('past_completed',NUM+PAST_NUM)]:
            pre=ColumnTransformer([('cat',OrdinalEncoder(handle_unknown='use_encoded_value',unknown_value=-1,dtype=np.int32),CAT),('num','passthrough',nums)])
            X=pre.fit_transform(tr);V=pre.transform(va)
            for leaves,iters,reg,weight in [(15,450,10,None),(31,450,20,None),(63,450,50,None),
                                             (31,900,50,None),(31,450,50,{0:1,1:3}),(63,700,100,None)]:
                m=LGBMClassifier(n_estimators=iters,learning_rate=.04,num_leaves=leaves,min_child_samples=150,
                    reg_lambda=reg,colsample_bytree=.85,subsample=.8,subsample_freq=1,max_cat_to_onehot=4,
                    cat_smooth=30,cat_l2=20,class_weight=weight,random_state=423,n_jobs=4,verbosity=-1)
                start=time.monotonic()
                with threadpool_limits(limits=4):m.fit(X,y,categorical_feature=list(range(len(CAT))));s=m.predict_proba(V)[:,1]
                rec.add(f'leaves{leaves}_iters{iters}_reg{reg}_w{weight}',variant,m,pre,s,yv,start,cats=CAT,nums=nums)
    elif family=='catboost':
        from catboost import CatBoostClassifier
        for variant,nums in [('context',NUM),('past_completed',NUM+PAST_NUM)]:
            X=tr[CAT+nums].copy();V=va[CAT+nums].copy()
            for c in CAT:X[c]=X[c].astype(object);V[c]=V[c].astype(object)
            for depth,iters,reg,weight in [(5,500,10,None),(7,650,20,None),(8,650,30,None),(6,800,30,[1,3])]:
                m=CatBoostClassifier(iterations=iters,depth=depth,learning_rate=.05,l2_leaf_reg=reg,
                      class_weights=weight,has_time=True,max_ctr_complexity=1,loss_function='Logloss',
                      thread_count=4,random_seed=423,allow_writing_files=False,verbose=False)
                start=time.monotonic();m.fit(X,y,cat_features=CAT);s=m.predict_proba(V)[:,1]
                rec.add(f'd{depth}_iters{iters}_reg{reg}_w{weight}',variant,m,None,s,yv,start,cats=CAT,nums=nums)
    else:raise ValueError(family)
    print(f'{family} search complete; no round-2 test evaluation performed.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('family',choices=['logistic','encoded_logistic','lightgbm','catboost'])
    run(p.parse_args().family)
