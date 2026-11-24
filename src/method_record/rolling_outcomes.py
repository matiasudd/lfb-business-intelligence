"""Strictly completed past arrivals, grouped by resource, station and destination."""
from pathlib import Path
import hashlib,time
import numpy as np
import pandas as pd
from station_geography import load_station_geography,GEO_NUM
from features_v2 import OUT

ROLL_NUM=[]
for group in ['resource','station','ward','station_borough']:
    for days in [7,30,90]:
        ROLL_NUM.extend([f'rolling_{group}_{days}d_n',f'rolling_{group}_{days}d_late',f'rolling_{group}_{days}d_mean'])
for group in ['station','ward']:
    ROLL_NUM.extend([f'active_{group}_not_arrived',f'active_{group}_over5m'])

def load_rolling():
    p=OUT/'rolling_features.pkl';stamp=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if p.exists() and (OUT/'rolling_features_hash.txt').read_text()==stamp:return pd.read_pickle(p)
    d=load_station_geography();start=time.monotonic()
    times=d.timestamp.dt.as_unit('ns').astype('int64').to_numpy()
    arrival=d.arrival.dt.as_unit('ns').astype('int64').to_numpy()
    duration=d.AttendanceTimeSeconds.to_numpy(dtype=float)
    for group in ['resource','station','ward','station_borough']:
        values={c:np.zeros(len(d)) for c in ROLL_NUM if c.startswith('rolling_'+group+'_')}
        for _,ids in d.groupby(group,sort=False).groups.items():
            ids=np.asarray(ids);o=ids[np.argsort(arrival[ids],kind='stable')]
            a=arrival[o];hi=np.searchsorted(a,times[ids],side='left')
            late=np.r_[0.,np.cumsum(duration[o]>=600)];sums=np.r_[0.,np.cumsum(duration[o])]
            assert (a[np.maximum(hi-1,0)][hi>0]<times[ids][hi>0]).all()
            for days in [7,30,90]:
                lo=np.searchsorted(a,times[ids]-int(days*86400*1e9),side='left');n=hi-lo
                values[f'rolling_{group}_{days}d_n'][ids]=np.log1p(n)
                values[f'rolling_{group}_{days}d_late'][ids]=(late[hi]-late[lo]+.5)/(n+10)
                values[f'rolling_{group}_{days}d_mean'][ids]=(sums[hi]-sums[lo]+10*300)/(n+10)/60
        for c,v in values.items():d[c]=v
    for group in ['station','ward']:
        active=np.zeros(len(d));older=np.zeros(len(d))
        for _,ids in d.groupby(group,sort=False).groups.items():
            ids=np.asarray(ids);dispatch=np.sort(times[ids]);a=np.sort(arrival[ids])
            begun=np.searchsorted(dispatch,times[ids],side='left');done=np.searchsorted(a,times[ids],side='left')
            active[ids]=np.log1p(begun-done)
            # Count live intervals [dispatch+5min, arrival]; intervals ending
            # earlier are empty. This is the observed status at the query time.
            aged_start=times[ids]+int(300*1e9);nonempty=arrival[ids]>aged_start
            counts=(np.searchsorted(np.sort(aged_start[nonempty]),times[ids],side='left')-
                    np.searchsorted(np.sort(arrival[ids][nonempty]),times[ids],side='left'))
            assert (counts>=0).all()
            older[ids]=np.log1p(counts)
        d[f'active_{group}_not_arrived']=active;d[f'active_{group}_over5m']=older
    assert d[ROLL_NUM].notna().all().all()
    d.to_pickle(p);(OUT/'rolling_features_hash.txt').write_text(stamp)
    print('Strict past arrival group features:',len(ROLL_NUM),'computed in',round(time.monotonic()-start,1),'seconds',flush=True)
    return d

if __name__=='__main__':load_rolling()
