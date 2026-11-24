"""Compare new call/location information under the same recall constraints."""
import argparse,time
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder,OrdinalEncoder,StandardScaler
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits
from location_features import load_locations,LOC_CAT,LOC_NUM
from features_v2 import PAST_NUM
from search_v2 import Recorder

def run(family):
    d=load_locations();tr=d[d.partition.eq('train')].copy();va=d[d.partition.eq('validation')].copy()
    y=tr.target.to_numpy();yv=va.target.to_numpy();rec=Recorder('geo_'+family)
    base=[n for n in LOC_NUM if n not in PAST_NUM]
    variants=[('geometry',LOC_CAT,base),('geometry_history',LOC_CAT,LOC_NUM),
              ('geometry_callclock_hypothesis',LOC_CAT,LOC_NUM+['call_to_dispatch_local_hypothesis_minutes','call_local_clock_available'])]
    if family=='catboost':
        # The clock interpretation remains unverified and did not help either
        # logistic or LightGBM. Do not spend further fits on that sensitivity.
        variants=[v for v in variants if 'hypothesis' not in v[0]]
    if family=='logistic':
        simplecats=['hour','weekday','month_of_year','station','origin_type','incident_ground','origin_ground_match']
        simplenums=['proxy_straight_line_km','proxy_distance_log','proxy_distance_squared','proxy_delta_e_km','proxy_delta_n_km',
                    'destination_e_km','destination_n_km','location_available','origin_proxy_available','incident_elapsed_log','previous_dispatches_log']
        variants=[('geometry_simple',simplecats,simplenums)]+variants
    for variant,cats,nums in variants:
        assert not set(cats+nums)&{'target','AttendanceTimeSeconds','arrival','DateAndTimeArrived','FirstPumpArriving_AttendanceTime'}
        if family=='logistic':
            num=Pipeline([('missing',SimpleImputer(strategy='median',add_indicator=True)),('scale',StandardScaler())])
            pre=ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore',min_frequency=20),cats),('num',num,nums)],sparse_threshold=1.)
            X=pre.fit_transform(tr);V=pre.transform(va)
            for cw in [None,'balanced']:
                for c in [.01,.1,1.,10.]:
                    m=LogisticRegression(C=c,class_weight=cw,max_iter=2500,random_state=423);start=time.monotonic()
                    with threadpool_limits(limits=4):m.fit(X,y);s=m.predict_proba(V)[:,1]
                    rec.add(f'C{c}_{cw}',variant,m,pre,s,yv,start,cats=cats,nums=nums)
        elif family=='lightgbm':
            from lightgbm import LGBMClassifier
            pre=ColumnTransformer([('cat',OrdinalEncoder(handle_unknown='use_encoded_value',unknown_value=-1,dtype=np.int32),cats),('num','passthrough',nums)])
            X=pre.fit_transform(tr);V=pre.transform(va)
            for leaves,iters,reg,weight in [(15,450,10,None),(31,450,20,None),(63,450,50,None),
                         (31,900,50,None),(31,450,50,{0:1,1:3}),(63,700,100,None)]:
                m=LGBMClassifier(n_estimators=iters,learning_rate=.04,num_leaves=leaves,min_child_samples=150,reg_lambda=reg,
                     colsample_bytree=.85,subsample=.8,subsample_freq=1,max_cat_to_onehot=4,cat_smooth=30,cat_l2=20,
                     class_weight=weight,random_state=423,n_jobs=4,verbosity=-1)
                start=time.monotonic()
                with threadpool_limits(limits=4):m.fit(X,y,categorical_feature=list(range(len(cats))));s=m.predict_proba(V)[:,1]
                rec.add(f'leaves{leaves}_iters{iters}_reg{reg}_w{weight}',variant,m,pre,s,yv,start,cats=cats,nums=nums)
        elif family=='catboost':
            from catboost import CatBoostClassifier
            X=tr[cats+nums].copy();V=va[cats+nums].copy()
            for c in cats:X[c]=X[c].astype(object);V[c]=V[c].astype(object)
            for depth,iters,reg,weight in [(5,500,10,None),(7,650,20,None),(8,650,30,None),(6,800,30,[1,3])]:
                m=CatBoostClassifier(iterations=iters,depth=depth,learning_rate=.05,l2_leaf_reg=reg,
                      class_weights=weight,has_time=True,max_ctr_complexity=1,loss_function='Logloss',thread_count=4,
                      random_seed=423,allow_writing_files=False,verbose=False)
                start=time.monotonic();m.fit(X,y,cat_features=cats);s=m.predict_proba(V)[:,1]
                rec.add(f'd{depth}_iters{iters}_reg{reg}_w{weight}',variant,m,None,s,yv,start,cats=cats,nums=nums)
        else:raise ValueError(family)
    print('Location search complete; no round-2 test evaluation performed.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('family',choices=['logistic','lightgbm','catboost']);run(p.parse_args().family)
