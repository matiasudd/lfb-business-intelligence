"""Compare recent completed response history without own/future outcomes."""
import argparse,time
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder,OrdinalEncoder,StandardScaler
from sklearn.linear_model import LogisticRegression
from rolling_outcomes import load_rolling,ROLL_NUM
from features_v2 import CAT,NUM,PAST_NUM
from location_features import LOC_CAT
from station_geography import GEO_NUM
from search_v2 import Recorder
from threadpoolctl import threadpool_limits

def run(family):
    d=load_rolling();tr=d[d.partition.eq('train')].copy();va=d[d.partition.eq('validation')].copy()
    y=tr.target.to_numpy();yv=va.target.to_numpy();rec=Recorder('rolling_'+family)
    for variant,cats,nums in [('base_history',CAT,NUM+PAST_NUM+ROLL_NUM),('location_history',LOC_CAT,GEO_NUM+ROLL_NUM)]:
        if family=='logistic':
            pre=ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore',min_frequency=20),cats),
                ('num',Pipeline([('missing',SimpleImputer(strategy='median',add_indicator=True)),('scale',StandardScaler())]),nums)],sparse_threshold=1.)
            X=pre.fit_transform(tr);V=pre.transform(va)
            for cw in [None,'balanced']:
                for c in [.002,.02,.2]:
                    m=LogisticRegression(C=c,class_weight=cw,max_iter=2500,random_state=423);start=time.monotonic()
                    with threadpool_limits(limits=4):m.fit(X,y);s=m.predict_proba(V)[:,1]
                    rec.add(f'C{c}_{cw}',variant,m,pre,s,yv,start,cats=cats,nums=nums)
        elif family=='lightgbm':
            from lightgbm import LGBMClassifier
            pre=ColumnTransformer([('cat',OrdinalEncoder(handle_unknown='use_encoded_value',unknown_value=-1,dtype=np.int32),cats),('num','passthrough',nums)])
            X=pre.fit_transform(tr);V=pre.transform(va)
            for leaves in [7,15,31]:
                m=LGBMClassifier(n_estimators=450,learning_rate=.04,num_leaves=leaves,min_child_samples=200,reg_lambda=50,
                      colsample_bytree=.9,subsample=.8,subsample_freq=1,cat_smooth=30,cat_l2=20,random_state=423,n_jobs=4,verbosity=-1)
                start=time.monotonic();m.fit(X,y,categorical_feature=list(range(len(cats))));s=m.predict_proba(V)[:,1]
                rec.add(f'leaves{leaves}',variant,m,pre,s,yv,start,cats=cats,nums=nums)
        elif family=='catboost':
            from catboost import CatBoostClassifier
            X=tr[cats+nums].copy();V=va[cats+nums].copy()
            for c in cats:X[c]=X[c].astype(object);V[c]=V[c].astype(object)
            for depth in [5,7]:
                m=CatBoostClassifier(iterations=600,depth=depth,learning_rate=.05,l2_leaf_reg=20,has_time=True,max_ctr_complexity=1,
                     loss_function='Logloss',thread_count=4,random_seed=423,allow_writing_files=False,verbose=False)
                start=time.monotonic();m.fit(X,y,cat_features=cats);s=m.predict_proba(V)[:,1]
                rec.add(f'd{depth}',variant,m,None,s,yv,start,cats=cats,nums=nums)
    print('Rolling search completed without test evaluation.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('family');run(p.parse_args().family)
