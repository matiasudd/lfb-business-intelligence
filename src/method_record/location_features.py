"""Audit a many-mobilisations-to-one-incident join; learn location proxies on train only."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from features_v2 import ROOT,OUT,DATA,load_features,CAT,NUM,PAST_NUM

LOC_CAT=CAT+['incident_ground','postcode_area','incident_ward_code','outside_london_ground','origin_ground_match']
LOC_NUM=NUM+PAST_NUM+['destination_e_km','destination_n_km','origin_proxy_e_km','origin_proxy_n_km',
          'proxy_straight_line_km','proxy_delta_e_km','proxy_delta_n_km','location_available',
          'origin_proxy_available','earlier_station_proxy_distance_km','proxy_distance_log','proxy_distance_squared']

def norm(series):return series.fillna('Unknown').astype(str).str.strip().str.upper()

def load_locations():
    cache=OUT/'location_features.pkl';stamp=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if cache.exists() and (OUT/'location_code_hash.txt').read_text()==stamp:return pd.read_pickle(cache)
    parts=[]
    for year in [2023,2024]:
        f=ROOT/'external_data'/f'incident_locations_{year}.csv.gz'
        assert f.with_suffix('.json').exists(),'Finish extracting official XLSX inputs first.'
        parts.append(pd.read_csv(f,dtype={'IncidentNumber':'string'}))
    loc=pd.concat(parts,ignore_index=True);audit={'source_incident_rows':len(loc)}
    loc['IncidentNumber']=loc.IncidentNumber.str.strip()
    exact=int(loc.duplicated().sum());loc=loc.drop_duplicates()
    conflict=loc.IncidentNumber.duplicated(keep=False)
    audit['exact_duplicate_incident_rows_removed']=exact
    audit['ambiguous_incident_ids']=int(loc.loc[conflict,'IncidentNumber'].nunique())
    loc=loc[~conflict].copy()
    assert loc.IncidentNumber.is_unique
    d=load_features();before=len(d)
    d=d.merge(loc,on='IncidentNumber',how='left',validate='many_to_one',indicator='_incident_join',suffixes=('','_incident'))
    assert len(d)==before==384627 and d.ResourceMobilisationId.is_unique
    audit['mobilisations_after_join']=len(d);audit['matched_mobilisations']=int(d._incident_join.eq('both').sum())
    audit['unmatched_mobilisations']=int(d._incident_join.ne('both').sum())
    for axis in ['Easting_rounded','Northing_rounded']:d[axis]=pd.to_numeric(d[axis],errors='coerce')
    valid=d.Easting_rounded.between(0,700000)&d.Northing_rounded.between(0,1300000)
    d['location_available']=valid.astype(float)
    d['destination_e_km']=d.Easting_rounded.where(valid)/1000
    d['destination_n_km']=d.Northing_rounded.where(valid)/1000
    d['incident_ground']=norm(d.IncidentStationGround)
    d['postcode_area']=norm(d.Postcode_district)
    d['incident_ward_code']=norm(d.IncGeo_WardCode)
    d['outside_london_ground']=norm(d.FRS)
    station_names=pd.read_csv(DATA,usecols=['ResourceMobilisationId','DeployedFromStation_Name'])
    d=d.merge(station_names,on='ResourceMobilisationId',how='left',validate='one_to_one')
    d['origin_name']=norm(d.DeployedFromStation_Name)
    d['origin_ground_match']=np.where(d.origin_name.eq(d.incident_ground),'same','different')
    tr=d.partition.eq('train')
    # Each training incident contributes once to its station-ground centroid.
    centroid_input=d.loc[tr & valid,['IncidentNumber','incident_ground','destination_e_km','destination_n_km']].drop_duplicates('IncidentNumber')
    centres=centroid_input.groupby('incident_ground').agg(e=('destination_e_km','median'),n=('destination_n_km','median'),incidents=('IncidentNumber','size'))
    centres=centres[centres.incidents.ge(30)&(centres.index!='UNKNOWN')]
    centres.to_csv(OUT/'training_station_ground_centroids.csv')
    d['origin_proxy_e_km']=d.origin_name.map(centres.e)
    d['origin_proxy_n_km']=d.origin_name.map(centres.n)
    home=d.origin_type.eq('Home Station')
    d.loc[~home,['origin_proxy_e_km','origin_proxy_n_km']]=np.nan
    d['origin_proxy_available']=d.origin_proxy_e_km.notna().astype(float)
    d['proxy_delta_e_km']=d.destination_e_km-d.origin_proxy_e_km
    d['proxy_delta_n_km']=d.destination_n_km-d.origin_proxy_n_km
    d['proxy_straight_line_km']=np.hypot(d.proxy_delta_e_km,d.proxy_delta_n_km)
    d['proxy_distance_log']=np.log1p(d.proxy_straight_line_km)
    d['proxy_distance_squared']=d.proxy_straight_line_km**2
    code_name=d.loc[tr,['station','origin_name']].drop_duplicates()
    ambiguous=code_name.station.duplicated(keep=False)
    audit['ambiguous_origin_codes']=code_name.loc[ambiguous,'station'].unique().tolist()
    code_name=code_name[~ambiguous]
    first_name=d.first_dispatch_station.map(dict(zip(code_name.station,code_name.origin_name)))
    first_e=first_name.map(centres.e);first_n=first_name.map(centres.n)
    d['earlier_station_proxy_distance_km']=np.hypot(d.destination_e_km-first_e,d.destination_n_km-first_n)
    dates=pd.to_numeric(d.DateOfCall,errors='coerce')
    times=pd.to_numeric(d.TimeOfCall,errors='coerce')
    call_date=pd.to_datetime(dates,unit='D',origin='1899-12-30',utc=True,errors='coerce')
    call_time=call_date+pd.to_timedelta(np.round(times*86400),unit='s')
    lag=(d.timestamp-call_time).dt.total_seconds()/60
    available=lag.ge(0)&lag.le(7*24*60)&times.between(0,1,inclusive='left')
    d['call_to_dispatch_minutes']=lag.where(available)
    d['call_time_available']=available.astype(float)
    local_clock=call_time.dt.tz_localize(None).dt.tz_localize('Europe/London',ambiguous='NaT',nonexistent='NaT').dt.tz_convert('UTC')
    inferred_lag=(d.timestamp-local_clock).dt.total_seconds()/60
    inferred_ok=inferred_lag.ge(0)&inferred_lag.le(7*24*60)
    d['call_to_dispatch_local_hypothesis_minutes']=inferred_lag.where(inferred_ok)
    d['call_local_clock_available']=inferred_ok.astype(float)
    audit['negative_call_to_dispatch_rows']=int(lag.lt(0).sum())
    audit['valid_call_to_dispatch_rows']=int(available.sum())
    audit['negative_lag_after_local_clock_hypothesis']=int(inferred_lag.lt(0).sum())
    audit['valid_lag_after_local_clock_hypothesis']=int(inferred_ok.sum())
    audit['call_clock_policy']='Raw exact call-time differences excluded. Europe/London interpretation is an explicitly labelled sensitivity, inferred from seasonal one-hour offsets; source confirmation not obtained.'
    audit['location_rows']=int(valid.sum())
    audit['station_ground_centroids_learned']=len(centres)
    audit['distance_proxy_rows']=int(d.proxy_straight_line_km.notna().sum())
    audit['distance_definition']='Euclidean distance to median training-incident location in origin station ground; not the physical station location or road distance.'
    audit['prediction_availability']='Location labels/coordinates and published call-time corrections require as-of verification; no arrival or incident-outcome columns used.'
    audit['no_mobilisations_removed']=True
    (OUT/'incident_join_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    d.to_pickle(cache);(OUT/'location_code_hash.txt').write_text(stamp)
    print(json.dumps(audit,indent=2),flush=True)
    return d

if __name__=='__main__':load_locations()
