"""Additional as-of dispatch context; the original C2/W3 files are read-only."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import coo_matrix

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'C2_Model_Improvement_20261122'
sys.path.insert(0,str(BASE))
from experiment import prepare,past_counts,DATA
from extra_logistic import enrich,EXTRA

OUT=ROOT/'outputs';OUT.mkdir(exist_ok=True)
MODELS=ROOT/'models';MODELS.mkdir(exist_ok=True)
CAT=EXTRA['H_route_conditional'][0]+['resource','call_dispatch_hour_gap','first_dispatch_station',
       'first_current_station','same_first_station','last_dispatch_gap_band']
NUM=EXTRA['H_route_conditional'][1]+['previous_dispatches_log','previous_same_station_log',
       'previous_other_station_log','last_dispatch_gap_log','borough_dispatches_15m','borough_dispatches_60m',
       'ward_dispatches_15m','ward_dispatches_60m']
PAST_NUM=['past_global_n_15m','past_global_mean_15m','past_global_late_share_15m',
          'past_global_n_60m','past_global_mean_60m','past_global_late_share_60m',
          'prior_incident_arrivals','prior_incident_mean_duration','prior_incident_late_share']

def completed_context(d):
    """Join only arrival events strictly before each prediction timestamp."""
    d=d.copy();times=d.timestamp.dt.as_unit('ns').astype('int64').to_numpy()
    at=d.arrival.dt.as_unit('ns').astype('int64').to_numpy()
    order=np.argsort(at,kind='stable');a=at[order]
    dur=d.AttendanceTimeSeconds.to_numpy(dtype=float)[order]
    late=(dur>=600).astype(float)
    sumdur=np.r_[0.,np.cumsum(dur)];sumlate=np.r_[0.,np.cumsum(late)]
    hi=np.searchsorted(a,times,side='left')
    for w in [15,60]:
        lo=np.searchsorted(a,times-int(w*60*1e9),side='left');n=hi-lo
        d[f'past_global_n_{w}m']=np.log1p(n)
        d[f'past_global_mean_{w}m']=np.divide(sumdur[hi]-sumdur[lo],n,out=np.zeros(len(d)),where=n>0)/60
        d[f'past_global_late_share_{w}m']=np.divide(sumlate[hi]-sumlate[lo],n,out=np.zeros(len(d)),where=n>0)
    nall=np.zeros(len(d));means=np.zeros(len(d));rates=np.zeros(len(d))
    all_durations=d.AttendanceTimeSeconds.to_numpy(dtype=float)
    for _,ix in d.groupby('IncidentNumber',sort=False).groups.items():
        if len(ix)==1:continue
        ix=np.asarray(ix);o=np.argsort(at[ix],kind='stable');arr=at[ix][o]
        vals=all_durations[ix[o]]
        cs=np.r_[0.,np.cumsum(vals)];cl=np.r_[0.,np.cumsum(vals>=600)]
        n=np.searchsorted(arr,times[ix],side='left')
        nall[ix]=np.log1p(n)
        means[ix]=np.divide(cs[n],n,out=np.zeros(len(n)),where=n>0)/60
        rates[ix]=np.divide(cl[n],n,out=np.zeros(len(n)),where=n>0)
    d['prior_incident_arrivals']=nall;d['prior_incident_mean_duration']=means;d['prior_incident_late_share']=rates
    # A future arrival timestamp cannot alter any earlier-time join.
    cut=pd.Timestamp('2024-07-01',tz='UTC').value
    prefix=times<cut;past=a<cut
    h=np.searchsorted(a[past],times[prefix],side='left')
    assert np.array_equal(h,hi[prefix])
    assert (d.arrival>=d.timestamp).all(), 'No own outcome may be available before prediction.'
    return d

def load_features():
    cache=OUT/'features_v2.pkl'
    stamp=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if cache.exists() and (OUT/'features_code_hash.txt').read_text()==stamp:
        return pd.read_pickle(cache)
    d=enrich(prepare())
    more=pd.read_csv(DATA,usecols=['ResourceMobilisationId','Resource_Code','DateAndTimeArrived'])
    d=d.merge(more,on='ResourceMobilisationId',how='left',validate='one_to_one')
    d=d.sort_values(['timestamp','ResourceMobilisationId'],kind='stable').reset_index(drop=True)
    d['arrival']=pd.to_datetime(d.DateAndTimeArrived,utc=True)
    d['resource']=d.Resource_Code.fillna('Unknown').astype(str)
    d['call_dispatch_hour_gap']=((d.timestamp.dt.hour-d.HourOfCall.astype(int))%24).clip(upper=5).astype(str)
    prior=d.groupby('IncidentNumber').timestamp.rank(method='min').to_numpy()-1
    same=d.groupby(['IncidentNumber','station']).timestamp.rank(method='min').to_numpy()-1
    d['previous_dispatches_log']=np.log1p(prior)
    d['previous_same_station_log']=np.log1p(same)
    d['previous_other_station_log']=np.log1p(prior-same)
    first=d.groupby('IncidentNumber',sort=False).station.transform('first')
    d['first_dispatch_station']=np.where(prior>0,first,'No earlier dispatch')
    d['same_first_station']=np.where(prior>0,np.where(first.eq(d.station),'same','different'),'none')
    d['first_current_station']=d.first_dispatch_station+' | '+d.station
    uniq=d[['IncidentNumber','timestamp']].drop_duplicates().sort_values(['IncidentNumber','timestamp'])
    uniq['previous_dispatch_timestamp']=uniq.groupby('IncidentNumber').timestamp.shift()
    d=d.merge(uniq,on=['IncidentNumber','timestamp'],how='left',validate='many_to_one')
    gap=(d.timestamp-d.previous_dispatch_timestamp).dt.total_seconds().fillna(0)/60
    d['last_dispatch_gap_log']=np.log1p(gap)
    d['last_dispatch_gap_band']=pd.cut(gap,[-1,0,.5,2,5,15,60,np.inf],labels=False).astype(str)
    times=d.timestamp.dt.as_unit('ns').astype('int64').to_numpy()
    for col in ['borough','ward']:
        for w in [15,60]:
            values=np.zeros(len(d))
            for _,ix in d.groupby(col,sort=False).groups.items():
                ix=np.asarray(ix);values[ix]=np.log1p(past_counts(times[ix],w))
            d[f'{col}_dispatches_{w}m']=values
    d=completed_context(d)
    assert len(d)==384627 and d.ResourceMobilisationId.is_unique
    assert d[NUM+PAST_NUM].notna().all().all()
    d.to_pickle(cache);(OUT/'features_code_hash.txt').write_text(stamp)
    return d

class RouteEncoding:
    """Group-cross-fitted target summaries and train-only route embeddings."""
    def __init__(self,alpha=30,dimensions=12):self.alpha=alpha;self.dimensions=dimensions
    def _fit_maps(self,d):
        self.prior=float(d.target.mean());self.maps={}
        for c in ['station','ward','borough','station_borough','station_ward','first_current_station']:
            g=d.groupby(c).target.agg(['sum','count'])
            self.maps[c]=((g['sum']+self.alpha*self.prior)/(g['count']+self.alpha)).to_dict()
        return self
    def _rates(self,d):
        out=pd.DataFrame(index=d.index)
        for c,m in self.maps.items():
            rate=d[c].map(m).fillna(self.prior).clip(.001,.999)
            out[f'train_rate_{c}']=np.log(rate/(1-rate))
        return out
    def fit_transform(self,tr,va):
        # Related vehicles are kept together when constructing training summaries.
        folds=(pd.util.hash_pandas_object(tr.IncidentNumber,index=False).to_numpy()%5).astype(int)
        oof=pd.DataFrame(index=tr.index)
        for k in range(5):
            fit=tr.iloc[np.flatnonzero(folds!=k)];hold=tr.iloc[np.flatnonzero(folds==k)]
            enc=RouteEncoding(self.alpha,self.dimensions)._fit_maps(fit)
            z=enc._rates(hold)
            for c in z:oof.loc[z.index,c]=z[c]
        self._fit_maps(tr)
        # Co-occurrence embeddings do not use outcomes.
        self.stations={s:i for i,s in enumerate(sorted(tr.station.unique()))}
        self.wards={s:i for i,s in enumerate(sorted(tr.ward.unique()))}
        rows=tr.station.map(self.stations).to_numpy();cols=tr.ward.map(self.wards).to_numpy()
        mat=coo_matrix((np.ones(len(tr)),(rows,cols)),shape=(len(self.stations),len(self.wards))).tocsr()
        mat.data=np.log1p(mat.data)
        svd=TruncatedSVD(n_components=self.dimensions,random_state=423)
        us=svd.fit_transform(mat);vs=svd.components_.T
        scale=np.sqrt(np.maximum(svd.singular_values_,1e-8))
        self.station_vectors=us/scale;self.ward_vectors=vs*scale
        return pd.concat([oof,self._embedding(tr)],axis=1),self.transform(va)
    def _embedding(self,d):
        si=d.station.map(self.stations).fillna(-1).to_numpy(dtype=int)
        wi=d.ward.map(self.wards).fillna(-1).to_numpy(dtype=int)
        a=np.zeros((len(d),self.dimensions));b=a.copy()
        a[si>=0]=self.station_vectors[si[si>=0]];b[wi>=0]=self.ward_vectors[wi[wi>=0]]
        prod=a*b
        out=pd.DataFrame(prod,index=d.index,columns=[f'route_embedding_product_{i}' for i in range(self.dimensions)])
        out['route_embedding_affinity']=prod.sum(axis=1)
        return out
    def transform(self,d):return pd.concat([self._rates(d),self._embedding(d)],axis=1)

if __name__=='__main__':
    d=load_features();print(d.groupby('partition').target.agg(['size','sum','mean']))
    print('Context features ready; no current or future outcome is a predictor.')
