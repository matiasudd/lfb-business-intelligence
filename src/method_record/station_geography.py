"""Reproducible postcode-level station coordinates from official public sources."""
from pathlib import Path
import re,json,hashlib
import pandas as pd
import numpy as np
from location_features import load_locations,LOC_CAT,LOC_NUM
from features_v2 import ROOT,OUT,DATA

GEO_NUM=LOC_NUM+['station_postcode_e_km','station_postcode_n_km','station_distance_km',
    'station_distance_log','station_distance_squared','station_delta_e_km','station_delta_n_km',
    'station_distance_available','station_ground_distance_km','nearest_station_distance_km',
    'distance_excess_nearest_km','station_distance_hour_sin','station_distance_hour_cos']

def coordinates():
    source=ROOT/'external_data/ons_london_postcodes_feb2022.csv'
    # Portable review package keeps the 103 extracted postcode points and
    # provenance instead of redistributing the 128MB national lookup extract.
    if not source.exists():
        stations=pd.read_csv(OUT/'station_postcode_coordinates.csv')
        assert len(stations)==103 and stations.origin_name.is_unique
        assert stations[['oseast1m','osnrth1m']].notna().all().all()
        assert (OUT/'station_geography_sources.json').exists()
        return stations
    text=(ROOT/'external_data/station_addresses.txt').read_text(encoding='utf-8')
    text=re.sub(r'Appendix 2\s*747 Issue date: 10 March 2011 \d+ of 12','',text)
    text=text.replace('Appendix 2 - Station drainage','').replace('Fire Station Address Type of Drains','')
    text=re.sub(r'\s+',' ',text).strip()
    names=pd.read_csv(OUT/'training_station_ground_centroids.csv').incident_ground.tolist()
    names=sorted(names+['LAMBETH RIVER'],key=len,reverse=True)
    rows=[]
    for segment in re.split(r'\b(?:Separate|Combined|N/A)\b',text):
        s=segment.strip().upper()
        if not s:continue
        matches=[name for name in names if s.startswith(name+' ')]
        assert matches,s
        name=matches[0]
        # Official appendix typo: E2 OHU has a letter O in the inward digit.
        s=s.replace('E2 OHU','E2 0HU')
        # Independently cross-checked in official policy 849, appendix addresses.
        s=s.replace('SE1 5UO','SE1 5JH')
        pcs=re.findall(r'\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b',s)
        assert len(pcs)==1,(name,pcs,s)
        rows.append({'origin_name':name,'postcode':pcs[0].replace(' ',''),'address_source_text':segment})
    stations=pd.DataFrame(rows)
    assert len(stations)==103 and stations.origin_name.is_unique
    wanted=set(stations.postcode);parts=[]
    for chunk in pd.read_csv(source,usecols=['pcds','oseast1m','osnrth1m','doterm'],chunksize=100000,dtype={'pcds':str}):
        chunk['postcode']=chunk.pcds.str.replace(' ','')
        parts.append(chunk[chunk.postcode.isin(wanted)])
    pc=pd.concat(parts,ignore_index=True)
    assert pc.postcode.is_unique
    stations=stations.merge(pc,on='postcode',how='left',validate='many_to_one')
    assert stations.oseast1m.notna().all(),stations[stations.oseast1m.isna()].to_dict('records')
    assert stations.oseast1m.between(400000,600000).all() and stations.osnrth1m.between(100000,250000).all()
    stations.to_csv(OUT/'station_postcode_coordinates.csv',index=False)
    audit={'station_rows':len(stations),'matched_postcodes':int(stations.oseast1m.notna().sum()),
           'addresses_source':'https://www.london-fire.gov.uk/media/hcwdipyb/pn0747-101125.pdf',
           'coordinates_source':'https://data.london.gov.uk/dataset/postcode-directory-for-london-exp5p',
           'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
           'manual_typographical_correction':'Bethnal Green: E2 OHU corrected to E2 0HU. Old Kent Road: invalid SE1 5UO replaced with SE1 5JH per official policy 849. No coordinate imputation.',
           'address_crosscheck_source':'https://www.london-fire.gov.uk/media/5856/pn849-240621.pdf',
           'qualification':'Postcode points, not exact appliance or station coordinates; 2025 station addresses have not been independently verified for every 2023 dispatch.'}
    (OUT/'station_geography_sources.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    return stations

def load_station_geography():
    cache=OUT/'station_geography.pkl'
    stamp=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if cache.exists() and (OUT/'station_geography_hash.txt').read_text()==stamp:return pd.read_pickle(cache)
    d=load_locations();st=coordinates().set_index('origin_name')
    home=d.origin_type.eq('Home Station')
    d['station_postcode_e_km']=d.origin_name.map(st.oseast1m).where(home)/1000
    d['station_postcode_n_km']=d.origin_name.map(st.osnrth1m).where(home)/1000
    d['station_delta_e_km']=d.destination_e_km-d.station_postcode_e_km
    d['station_delta_n_km']=d.destination_n_km-d.station_postcode_n_km
    d['station_distance_km']=np.hypot(d.station_delta_e_km,d.station_delta_n_km)
    d['station_distance_log']=np.log1p(d.station_distance_km)
    d['station_distance_squared']=d.station_distance_km**2
    d['station_distance_available']=d.station_distance_km.notna().astype(float)
    ge=d.incident_ground.map(st.oseast1m)/1000;gn=d.incident_ground.map(st.osnrth1m)/1000
    d['station_ground_distance_km']=np.hypot(d.destination_e_km-ge,d.destination_n_km-gn)
    nearest=np.full(len(d),np.inf)
    # 103 fixed source points; no future mobilisation or response outcomes.
    for _,s in st.iterrows():
        dis=np.hypot(d.destination_e_km-s.oseast1m/1000,d.destination_n_km-s.osnrth1m/1000)
        nearest=np.minimum(nearest,dis.to_numpy())
    nearest[~np.isfinite(nearest)]=np.nan
    d['nearest_station_distance_km']=nearest
    d['distance_excess_nearest_km']=d.station_distance_km-nearest
    d['station_distance_hour_sin']=d.station_distance_km*d.time_sin
    d['station_distance_hour_cos']=d.station_distance_km*d.time_cos
    assert len(d)==384627 and d.ResourceMobilisationId.is_unique
    d.to_pickle(cache);(OUT/'station_geography_hash.txt').write_text(stamp)
    print('Postcode-distance features:',int(d.station_distance_km.notna().sum()),'of',len(d),flush=True)
    return d

if __name__=='__main__':load_station_geography()
