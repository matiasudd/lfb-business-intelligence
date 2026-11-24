"""Validation-only experiments; test evaluation is a separate, explicit stage."""
from pathlib import Path
import json, time, hashlib, warnings, os
import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy import sparse
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_curve, average_precision_score, roc_auc_score, confusion_matrix
from threadpoolctl import threadpool_limits
import joblib

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)
CACHE=ROOT/'models';CACHE.mkdir(exist_ok=True)
SEED=423
DATA=ROOT/'data/mobilisations_2023_2024_clean.csv.gz'

def jsonable(value):
    if isinstance(value,dict):return {str(k):jsonable(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [jsonable(v) for v in value]
    if isinstance(value,np.generic):return value.item()
    return value

def past_counts(times,minutes):
    """Count dispatch timestamps in [t-window,t), excluding simultaneous rows."""
    x=np.sort(np.asarray(times,dtype='int64'))
    return np.searchsorted(x,times,side='left')-np.searchsorted(x,np.asarray(times)-int(minutes*60*1e9),side='left')

def prepare():
    cols=['ResourceMobilisationId','IncidentNumber','DateAndTimeMobilised','AttendanceTimeSeconds',
          'HourOfCall','DeployedFromStation_Code','DeployedFromLocation','BoroughName','WardName']
    d=pd.read_csv(DATA,usecols=cols,dtype={'IncidentNumber':'string'})
    d['timestamp']=pd.to_datetime(d.DateAndTimeMobilised,utc=True)
    d['target']=d.AttendanceTimeSeconds.ge(600).astype('int8')
    d['hour']=d.timestamp.dt.hour.astype(str)
    d['weekday']=d.timestamp.dt.dayofweek.astype(str)
    d['month_of_year']=d.timestamp.dt.month.astype(str)
    d['call_hour']=d.HourOfCall.astype(str)
    minute=d.timestamp.dt.hour*60+d.timestamp.dt.minute+d.timestamp.dt.second/60
    d['time_sin']=np.sin(2*np.pi*minute/1440)
    d['time_cos']=np.cos(2*np.pi*minute/1440)
    first=d.groupby('IncidentNumber').timestamp.transform('min')
    elapsed=(d.timestamp-first).dt.total_seconds()/60
    assert elapsed.ge(0).all()
    d['incident_elapsed_log']=np.log1p(elapsed)
    prior=(d.groupby('IncidentNumber').timestamp.rank(method='min').astype(int)-1)
    d['earlier_incident_dispatches']=np.minimum(prior,5).astype(str)
    times=d.timestamp.dt.as_unit('ns').astype('int64').to_numpy()
    assert 1.6e18 < times.min() < 1.8e18, 'History calculations require nanoseconds.'
    for w in [15,60]: d[f'global_dispatches_{w}m']=np.log1p(past_counts(times,w))
    d['station']=d.DeployedFromStation_Code.fillna('Unknown').astype(str)
    d['origin_type']=d.DeployedFromLocation.fillna('Unknown').astype(str)
    for w in [15,60]:
        values=np.zeros(len(d),dtype=float)
        for _,ids in d.groupby('station').groups.items():
            ix=np.asarray(ids);values[ix]=np.log1p(past_counts(times[ix],w))
        d[f'station_dispatches_{w}m']=values
    d['borough']=d.BoroughName.fillna('Unknown').astype(str)
    d['ward']=d.WardName.fillna('Unknown').astype(str)
    d['station_borough']=d.station+' | '+d.borough
    d['partition']=np.where(d.timestamp.lt('2024-01-01'),'train',np.where(d.timestamp.lt('2024-07-01'),'validation','test'))
    assert len(d)==384627 and d.ResourceMobilisationId.is_unique
    sets={n:set(d.loc[d.partition.eq(n),'IncidentNumber']) for n in ['train','validation','test']}
    assert not any(sets[a]&sets[b] for a,b in [('train','validation'),('train','test'),('validation','test')])
    # Prefix invariance verifies that history features do not use later timestamps.
    for cut in ['2024-01-01','2024-07-01']:
        ix=np.flatnonzero(d.timestamp.lt(cut).to_numpy())
        assert np.array_equal(past_counts(times[ix],15),np.expm1(d.iloc[ix].global_dispatches_15m).round().astype(int))
    return d

CAL_CAT=['hour','weekday','month_of_year','call_hour']
CAL_NUM=['time_sin','time_cos']
HIST_CAT=CAL_CAT+['earlier_incident_dispatches']
HIST_NUM=CAL_NUM+['incident_elapsed_log','global_dispatches_15m','global_dispatches_60m']
ORIGIN_CAT=HIST_CAT+['station','origin_type']
ORIGIN_NUM=HIST_NUM+['station_dispatches_15m','station_dispatches_60m']
SETS={
 'A_hour':(['hour'],[],'Known dispatch timestamp; original C2 input'),
 'B_calendar':(CAL_CAT,CAL_NUM,'Calendar and call hour available at mobilisation'),
 'C_history':(HIST_CAT,HIST_NUM,'Only earlier dispatch timestamps, no duration outcomes; published-load proxies'),
 'D_origin':(ORIGIN_CAT,ORIGIN_NUM,'Origin assignment plausibly known at mobilisation; exact published-field timing unverified'),
 'E_geography_conditional':(ORIGIN_CAT+['borough','ward','station_borough'],ORIGIN_NUM,
                            'Conditional retrospective experiment: dispatch-time availability of published destination labels unverified'),
}

def metric(y,s,t):
    pred=np.asarray(s)>=t
    tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    p=tp/(tp+fp) if tp+fp else 0.
    r=tp/(tp+fn)
    return {'threshold':float(t),'TN':int(tn),'FP':int(fp),'FN':int(fn),'TP':int(tp),
            'precision':float(p),'recall':float(r),'f1':float(2*p*r/(p+r) if p+r else 0),
            'f2':float(5*p*r/(4*p+r) if 4*p+r else 0),'accuracy':float((tn+tp)/len(y)),
            'alerts':int(tp+fp),'alert_share':float((tp+fp)/len(y))}

def operating_points(y,s):
    p,r,t=precision_recall_curve(y,s,drop_intermediate=False)
    p,r=p[:-1],r[:-1]
    results={}
    for goal in [.8,.9,.95,.99,1.]:
        ix=np.flatnonzero(r>=goal-1e-12)
        # Maximise precision; break exact ties by greater threshold (fewer alerts).
        best=ix[np.lexsort((t[ix],p[ix]))[-1]]
        results[f'recall_{int(goal*100)}']=metric(y,s,t[best])
    for beta in [1,2]:
        score=(1+beta**2)*p*r/np.maximum(beta**2*p+r,1e-15)
        best=np.lexsort((t,r,score))[-1]
        results[f'best_f{beta}']=metric(y,s,t[best])
    results['default_050']=metric(y,s,.5)
    return results

def candidates(setname):
    for cw,label in [('balanced','balanced'),(None,'unweighted')]:
        for c in [.1,1.,10.]:
            yield 'Logistic',f'LR_{label}_C{c:g}',LogisticRegression(C=c,class_weight=cw,max_iter=1500,random_state=SEED)
    for depth,leaf in [(3,200),(6,200),(10,200),(12,500)]:
        yield 'DecisionTree',f'DT_d{depth}_l{leaf}',DecisionTreeClassifier(max_depth=depth,min_samples_leaf=leaf,class_weight='balanced',random_state=SEED)
    for depth,leaf in [(8,100),(14,100),(None,200)]:
        yield 'RandomForest',f'RF_d{depth}_l{leaf}',RandomForestClassifier(n_estimators=140,max_depth=depth,min_samples_leaf=leaf,
              max_features=.5,class_weight='balanced_subsample',max_samples=.75,n_jobs=4,random_state=SEED)

def run_validation(resume_sets=()):
    d=prepare(); tr=d.partition.eq('train'); va=d.partition.eq('validation')
    ytr=d.loc[tr,'target'].to_numpy(); yva=d.loc[va,'target'].to_numpy()
    protocol={'seed':SEED,'target':'AttendanceTimeSeconds >= 600','train':'2023',
              'validation':'January-June 2024','test':'July-30 December 2024; already used in original C2',
              'selection':'Within each feature set and family: maximum validation precision at recall >= 95%; tie-break F2 then simpler trial order',
              'review_policies':['recall >=80%','recall >=90%','recall >=95%','recall >=99%','recall 100%','maximum F1','maximum F2','default 0.50'],
              'sets':SETS,'feature_limits':'Published origin/destination fields lack confirmed as-of snapshots; D/E are conditional only.',
              'test_not_used_for_tuning':True,'versions':{'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__},
              'data_sha256':hashlib.sha256(DATA.read_bytes()).hexdigest()}
    (OUT/'protocol.json').write_text(json.dumps(jsonable(protocol),indent=2),encoding='utf-8')
    rows=[];best={}; allpoints=[]
    if resume_sets:
        prior_rows=pd.read_csv(OUT/'validation_trials.csv')
        rows=prior_rows[prior_rows.feature_set.isin(resume_sets)].to_dict('records')
        prior_points=pd.read_csv(OUT/'validation_operating_points.csv')
        allpoints=prior_points[prior_points.feature_set.isin(resume_sets)].to_dict('records')
        prior_best=json.loads((OUT/'validation_selected.json').read_text())
        best={k:v for k,v in prior_best.items() if v['feature_set'] in resume_sets}
    for setname,(cats,nums,_) in SETS.items():
        if setname in resume_sets:continue
        pre=ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore',min_frequency=20 if setname!='A_hour' else None),cats)]+
                              ([('num',StandardScaler(),nums)] if nums else []),sparse_threshold=1.)
        Xtr=pre.fit_transform(d.loc[tr]); Xva=pre.transform(d.loc[va])
        print(f'FEATURE SET {setname}: {Xtr.shape[1]} encoded columns',flush=True)
        for family,name,model in candidates(setname):
            started=time.monotonic()
            with threadpool_limits(limits=4):model.fit(Xtr,ytr)
            s=model.predict_proba(Xva)[:,1]
            points=operating_points(yva,s);main=points['recall_95']
            row={'feature_set':setname,'family':family,'candidate':name,'seconds':time.monotonic()-started,
                 'average_precision':average_precision_score(yva,s),'roc_auc':roc_auc_score(yva,s),
                 **main,'best_f2':points['best_f2']['f2']}
            rows.append(row)
            for policy,met in points.items():allpoints.append({'feature_set':setname,'family':family,'candidate':name,'policy':policy,**met})
            key=f'{setname}__{family}'; score=(main['precision'],points['best_f2']['f2'])
            if key not in best or score>tuple(best[key]['selection_score']):
                best[key]={'feature_set':setname,'family':family,'candidate':name,'selection_score':score,'validation_points':points,
                           'average_precision':row['average_precision'],'roc_auc':row['roc_auc']}
                joblib.dump({'preprocessor':pre,'model':model,'metadata':best[key]},CACHE/f'{key}.joblib',compress=3)
                np.savez_compressed(CACHE/f'{key}_validation.npz',y=yva,score=s.astype('float32'))
            print(f'{setname} {name}: AP={row["average_precision"]:.3f}; @95 recall P={main["precision"]:.3f}, alerts={main["alert_share"]:.1%}; F2={points["best_f2"]["f2"]:.3f}; {row["seconds"]:.1f}s',flush=True)
            pd.DataFrame(rows).to_csv(OUT/'validation_trials.csv',index=False)
            pd.DataFrame(allpoints).to_csv(OUT/'validation_operating_points.csv',index=False)
            (OUT/'validation_selected.json').write_text(json.dumps(jsonable(best),indent=2),encoding='utf-8')
    print('VALIDATION COMPLETE. Test has not been scored by this script.',flush=True)
    return best

if __name__=='__main__':run_validation()
