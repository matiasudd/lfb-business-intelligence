"""Fresh-fit selected estimators and verify frozen test confusion counts."""
import json,hashlib,time
import numpy as np,pandas as pd,joblib
from sklearn.base import clone
from threadpoolctl import threadpool_limits
from rolling_outcomes import load_rolling
from features_v2 import OUT,MODELS,ROOT
from experiment import metric
from blend_models import BlendModel

def refit_primary(data=None):
    d=load_rolling() if data is None else data
    plan=json.loads((OUT/'round2_locked_plan.json').read_text());entries={e['key']:e for e in plan['entries']}
    expected=pd.read_csv(OUT/'round2_test_results.csv').set_index('key');cache={};checks=[]
    te=d[d.partition.eq('test')].copy();y=te.target.to_numpy()
    def fresh(name):
        b=joblib.load(MODELS/name);m=b['model']
        if isinstance(m,BlendModel):
            scores=[fresh(member) for member in m.members]
            return m.combine(scores)
        sig=hashlib.sha256(repr((type(m).__name__,m.get_params(),repr(clone(b['pre'])) if b['pre'] is not None else None,
                            b['cats'],b['nums'],b.get('train_end','2024-01-01'),b.get('fill_numeric'))).encode()).hexdigest()
        if sig in cache:return cache[sig]
        assert 'route_encoder' not in b,'No cross-fitted encoder is selected in the final protocol.'
        tr=d[d.timestamp.lt(b.get('train_end','2024-01-01'))].copy();model=clone(m);start=time.monotonic()
        if b['pre'] is not None:
            pre=clone(b['pre']);X=pre.fit_transform(tr);V=pre.transform(te);extra={}
            if type(m).__name__=='LGBMClassifier':extra={'categorical_feature':list(range(len(b['cats'])))}
            with threadpool_limits(limits=4):model.fit(X,tr.target,**extra);score=model.predict_proba(V)[:,1]
        else:
            cats=b['cats'];nums=b['nums'];X=tr[cats+nums].copy();V=te[cats+nums].copy()
            for c in cats:X[c]=X[c].astype(object);V[c]=V[c].astype(object)
            if 'fill_numeric' in b:X[nums]=X[nums].fillna(b['fill_numeric']);V[nums]=V[nums].fillna(b['fill_numeric'])
            model.fit(X,tr.target,cat_features=cats);score=model.predict_proba(V)[:,1]
        cache[sig]=score
        print('Fresh refit:',name,'training rows',len(tr),'seconds',round(time.monotonic()-start,1),flush=True)
        return score
    keys=list(dict.fromkeys(plan['primary'].values()))
    # Preserve an independently verified logistic option for the course defence.
    keys+=['common_location_logistic_85','common_location_logistic_90']
    saved=np.load(OUT/'round2_test_scores.npz')
    for key in dict.fromkeys(keys):
        e=entries[key];s=fresh(e['file']);m=metric(y,s,e['validation']['threshold']);row=expected.loc[key]
        assert all(int(m[k])==int(row[k]) for k in ['TN','FP','FN','TP','alerts'])
        diff=float(np.max(np.abs(s-saved[key])));assert diff<1e-7,(key,diff)
        checks.append({'key':key,'TN':m['TN'],'FP':m['FP'],'FN':m['FN'],'TP':m['TP'],'max_score_difference':diff})
    result={'independent_fresh_fits':len(cache),'verified_policies':len(checks),'checks':checks,'all_passed':True}
    (OUT/'fresh_refit_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return pd.DataFrame(checks)

if __name__=='__main__':print(refit_primary().to_string(index=False))
