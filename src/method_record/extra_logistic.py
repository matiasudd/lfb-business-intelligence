"""Test non-linear feature representations while retaining logistic regression."""
import json,time
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score,roc_auc_score
from threadpoolctl import threadpool_limits
import joblib
from experiment import prepare,SETS,OUT,CACHE,SEED,operating_points,jsonable

def enrich(d):
    d=d.copy()
    d['hour_weekday']=d.hour+' | '+d.weekday
    d['hour_month']=d.hour+' | '+d.month_of_year
    d['station_hour']=d.station+' | '+d.hour
    d['station_ward']=d.station+' | '+d.ward
    elapsed=np.expm1(d.incident_elapsed_log)
    d['elapsed_band']=pd.cut(elapsed,[-1,0,.5,2,5,15,60,np.inf],labels=False).astype(str)
    tr=d.partition.eq('train')
    for col in ['station_borough','station_ward']:
        mapping=d.loc[tr,col].value_counts().to_dict()
        d[f'{col}_frequency_log']=np.log1p(d[col].map(mapping).fillna(0))
    return d

EXTRA={
 'F_history_interactions':(SETS['C_history'][0]+['hour_weekday','hour_month','elapsed_band'],SETS['C_history'][1],
                           'Known time/history features; fixed elapsed-time bands and calendar interactions'),
 'G_origin_interactions':(SETS['D_origin'][0]+['hour_weekday','hour_month','elapsed_band','station_hour'],SETS['D_origin'][1],
                          'Conditional origin availability, same qualification as D'),
 'H_route_conditional':(SETS['E_geography_conditional'][0]+['hour_weekday','hour_month','elapsed_band','station_hour','station_ward'],
                        SETS['E_geography_conditional'][1]+['station_borough_frequency_log','station_ward_frequency_log'],
                        'Conditional destination availability; route frequencies estimated on training rows only')
}

def run():
    d=enrich(prepare());tr=d.partition.eq('train');va=d.partition.eq('validation')
    ytr=d.loc[tr,'target'].to_numpy();yva=d.loc[va,'target'].to_numpy()
    rows=[];points_rows=[];best={}
    for setname,(cats,nums,_) in EXTRA.items():
        pre=ColumnTransformer([('cat',OneHotEncoder(min_frequency=20,handle_unknown='ignore'),cats),('num',StandardScaler(),nums)],sparse_threshold=1.)
        Xtr=pre.fit_transform(d.loc[tr]);Xva=pre.transform(d.loc[va])
        for cw,label in [('balanced','balanced'),(None,'unweighted')]:
            for c in [.05,.2,1.,5.]:
                name=f'LR_interactions_{label}_C{c:g}';started=time.monotonic()
                model=LogisticRegression(C=c,class_weight=cw,max_iter=1800,random_state=SEED)
                with threadpool_limits(limits=4):model.fit(Xtr,ytr);s=model.predict_proba(Xva)[:,1]
                points=operating_points(yva,s);main=points['recall_95']
                row={'feature_set':setname,'family':'Logistic','candidate':name,'seconds':time.monotonic()-started,
                     'average_precision':average_precision_score(yva,s),'roc_auc':roc_auc_score(yva,s),**main,'best_f2':points['best_f2']['f2']}
                rows.append(row)
                for policy,met in points.items():points_rows.append({'feature_set':setname,'family':'Logistic','candidate':name,'policy':policy,**met})
                key=f'{setname}__Logistic';score=(main['precision'],points['best_f2']['f2'])
                if key not in best or score>tuple(best[key]['selection_score']):
                    best[key]={'feature_set':setname,'family':'Logistic','candidate':name,'selection_score':score,'validation_points':points,
                               'average_precision':row['average_precision'],'roc_auc':row['roc_auc']}
                    joblib.dump({'preprocessor':pre,'model':model,'metadata':best[key]},CACHE/f'{key}.joblib',compress=3)
                    np.savez_compressed(CACHE/f'{key}_validation.npz',y=yva,score=s.astype('float32'))
                print(f'{setname} {name}: AP={row["average_precision"]:.3f}, P@95={main["precision"]:.3f}, F2={row["best_f2"]:.3f}; {row["seconds"]:.1f}s',flush=True)
                pd.DataFrame(rows).to_csv(OUT/'validation_logistic_extra_trials.csv',index=False)
                pd.DataFrame(points_rows).to_csv(OUT/'validation_logistic_extra_operating_points.csv',index=False)
                (OUT/'validation_logistic_extra_selected.json').write_text(json.dumps(jsonable(best),indent=2),encoding='utf-8')
    print('EXTRA LOGISTIC VALIDATION COMPLETE',flush=True)

if __name__=='__main__':run()
