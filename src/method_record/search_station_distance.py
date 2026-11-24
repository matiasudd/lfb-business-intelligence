"""Validate physical station-postcode distance with original rows and target."""
import argparse,time
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder,OrdinalEncoder,StandardScaler,SplineTransformer
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits
from station_geography import load_station_geography,GEO_NUM
from location_features import LOC_CAT
from features_v2 import PAST_NUM
from search_v2 import Recorder

def run(family):
    d=load_station_geography();tr=d[d.partition.eq('train')].copy();va=d[d.partition.eq('validation')].copy()
    y=tr.target.to_numpy();yv=va.target.to_numpy();rec=Recorder('station_'+family)
    simplecats=['hour','weekday','month_of_year','station','origin_type','incident_ground','origin_ground_match']
    simplenums=[n for n in GEO_NUM if n.startswith('station_') or n in ['distance_excess_nearest_km','nearest_station_distance_km',
       'destination_e_km','destination_n_km','incident_elapsed_log','previous_dispatches_log','location_available']]
    variants=[('distance_simple',simplecats,simplenums),('distance_context',LOC_CAT,GEO_NUM)]
    for variant,cats,nums in variants:
        if family=='logistic':
            for splines in [False,True]:
                num=Pipeline([('missing',SimpleImputer(strategy='median',add_indicator=True)),('scale',StandardScaler())])
                trans=[('cat',OneHotEncoder(handle_unknown='ignore',min_frequency=20),cats),('num',num,nums)]
                if splines:
                    sp=Pipeline([('missing',SimpleImputer(strategy='median')),('spline',SplineTransformer(n_knots=6,degree=3)),('scale',StandardScaler())])
                    trans.append(('distance_spline',sp,['station_distance_km','distance_excess_nearest_km','station_ground_distance_km']))
                pre=ColumnTransformer(trans,sparse_threshold=1.)
                X=pre.fit_transform(tr);V=pre.transform(va)
                for cw in [None,'balanced']:
                    for c in [.002,.02,.2,2.]:
                        m=LogisticRegression(C=c,class_weight=cw,max_iter=2500,random_state=423);start=time.monotonic()
                        with threadpool_limits(limits=4):m.fit(X,y);s=m.predict_proba(V)[:,1]
                        rec.add(f'C{c}_{cw}_splines{splines}',variant,m,pre,s,yv,start,cats=cats,nums=nums)
        elif family=='lightgbm':
            from lightgbm import LGBMClassifier
            pre=ColumnTransformer([('cat',OrdinalEncoder(handle_unknown='use_encoded_value',unknown_value=-1,dtype=np.int32),cats),('num','passthrough',nums)])
            X=pre.fit_transform(tr);V=pre.transform(va)
            for leaves,iters,reg in [(7,450,10),(15,450,20),(31,450,50),(31,900,100)]:
                m=LGBMClassifier(n_estimators=iters,learning_rate=.04,num_leaves=leaves,min_child_samples=150,reg_lambda=reg,
                      colsample_bytree=.9,subsample=.8,subsample_freq=1,cat_smooth=30,cat_l2=20,random_state=423,n_jobs=4,verbosity=-1)
                start=time.monotonic();m.fit(X,y,categorical_feature=list(range(len(cats))));s=m.predict_proba(V)[:,1]
                rec.add(f'leaves{leaves}_iters{iters}_reg{reg}',variant,m,pre,s,yv,start,cats=cats,nums=nums)
        elif family=='catboost':
            from catboost import CatBoostClassifier
            X=tr[cats+nums].copy();V=va[cats+nums].copy()
            for n in nums:X[n]=X[n].fillna(-999.);V[n]=V[n].fillna(-999.)
            for c in cats:X[c]=X[c].astype(object);V[c]=V[c].astype(object)
            for depth,iters,reg in [(5,500,10),(7,650,20),(8,650,30)]:
                m=CatBoostClassifier(iterations=iters,depth=depth,learning_rate=.05,l2_leaf_reg=reg,
                      has_time=True,max_ctr_complexity=1,loss_function='Logloss',thread_count=4,random_seed=423,
                      allow_writing_files=False,verbose=False)
                start=time.monotonic();m.fit(X,y,cat_features=cats);s=m.predict_proba(V)[:,1]
                rec.add(f'd{depth}_iters{iters}_reg{reg}',variant,m,None,s,yv,start,cats=cats,nums=nums,fill_numeric=-999.)
        else:raise ValueError(family)
    print('Station distance search complete; no test evaluation performed.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('family');run(p.parse_args().family)
