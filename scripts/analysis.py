"""Reproducible C1 audit, conservative cleaning and descriptive analysis."""
from pathlib import Path
import hashlib
import json
import os
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1] / '.matplotlib'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
FIG = OUT / 'figures'
START, END = '2023-01-01', '2025-01-01'
TIMES = ['DateAndTimeMobilised', 'DateAndTimeMobile', 'DateAndTimeArrived', 'DateAndTimeLeft', 'DateAndTimeReturned']
NUMBERS = ['CalYear', 'HourOfCall', 'TurnoutTimeSeconds', 'TravelTimeSeconds', 'AttendanceTimeSeconds', 'PumpOrder']

def metrics(series):
    return pd.Series({'n': series.count(), 'median_min': series.median(), 'p90_min': series.quantile(.9), 'mean_min': series.mean()})

def grouped(data, columns):
    return data.groupby(columns, dropna=False)['attendance_min'].agg(n='size', median_min='median', p90_min=lambda s:s.quantile(.9), mean_min='mean').reset_index()

def run():
    FIG.mkdir(parents=True, exist_ok=True)
    raw_path = ROOT / 'data/raw/mobilisations_2021_2024.csv'
    manifest = json.loads((ROOT / 'data/source_manifest.json').read_text())
    with raw_path.open('rb') as f:
        assert hashlib.file_digest(f, 'sha256').hexdigest() == manifest[raw_path.name]['sha256']
    raw = pd.read_csv(raw_path, dtype='string', na_values=['NULL', 'Null', 'null', ''])
    profile = pd.DataFrame({'column':raw.columns, 'missing_n':raw.isna().sum().values,
                            'missing_pct':raw.isna().mean().values*100, 'distinct':raw.nunique().values})
    profile.to_csv(OUT / 'raw_profile.csv', index=False)
    pd.read_excel(ROOT / 'data/raw/mobilisations_metadata.xlsx').to_csv(OUT / 'source_dictionary.csv', index=False)
    d = raw.copy()
    # Only whitespace is normalized; original category spelling stays auditable.
    for col in d:
        d[col] = d[col].str.strip().replace('', pd.NA)
    parse_failures = {}
    for col in TIMES:
        original = d[col]
        d[col] = pd.to_datetime(original, format='%d/%m/%Y %H:%M:%S', errors='coerce', utc=True)
        parse_failures[col] = int((original.notna() & d[col].isna()).sum())
    for col in NUMBERS:
        original = d[col]
        d[col] = pd.to_numeric(original, errors='coerce')
        parse_failures[col] = int((original.notna() & d[col].isna()).sum())
    all_rows = len(d)
    exact_duplicates = int(d.duplicated().sum())
    d = d.drop_duplicates().copy()
    conflict = d['ResourceMobilisationId'].duplicated(keep=False)
    d.loc[conflict].to_csv(OUT / 'conflicting_ids.csv', index=False)
    # Conflicting IDs cannot be safely resolved by arbitrarily retaining a row.
    d['conflicting_id'] = conflict
    mobilised = d.DateAndTimeMobilised
    period = d[mobilised.ge(pd.Timestamp(START, tz='UTC')) & mobilised.lt(pd.Timestamp(END, tz='UTC'))].copy()
    period['month'] = period.DateAndTimeMobilised.dt.strftime('%Y-%m')
    period['hour_gmt'] = period.DateAndTimeMobilised.dt.hour
    period['weekday_gmt'] = period.DateAndTimeMobilised.dt.dayofweek
    period['year'] = period.DateAndTimeMobilised.dt.year
    elapsed = (period.DateAndTimeArrived-period.DateAndTimeMobilised).dt.total_seconds()
    flags = pd.DataFrame(index=period.index)
    flags['missing_id'] = period.ResourceMobilisationId.isna() | period.IncidentNumber.isna()
    flags['conflicting_id'] = period.conflicting_id
    flags['missing_or_negative_attendance'] = period.AttendanceTimeSeconds.isna() | period.AttendanceTimeSeconds.lt(0)
    flags['invalid_arrival'] = elapsed.isna() | elapsed.lt(0)
    flags['attendance_disagrees_timestamp'] = (elapsed-period.AttendanceTimeSeconds).abs().gt(1).fillna(False)
    period['eligible_kpi'] = ~flags.any(axis=1)
    reasons = pd.Series('', index=period.index)
    for name in flags:
        reasons.loc[flags[name]] += name + '|'
    period['exclusion_reason'] = reasons.str.rstrip('|')
    period['attendance_min'] = period.AttendanceTimeSeconds / 60
    period['borough'] = period.BoroughName.fillna('Unknown')
    period['station'] = period.DeployedFromStation_Name.fillna('Unknown')
    # Missing components do not invalidate a consistent total attendance time.
    period['components_complete'] = period.TurnoutTimeSeconds.notna() & period.TravelTimeSeconds.notna()
    period['components_consistent'] = (period.components_complete & period.TurnoutTimeSeconds.ge(0) & period.TravelTimeSeconds.ge(0)
        & (period.TurnoutTimeSeconds+period.TravelTimeSeconds-period.AttendanceTimeSeconds).abs().le(1)).fillna(False)
    clean = period[period.eligible_kpi].copy()
    assert len(clean) > 0
    assert clean.ResourceMobilisationId.is_unique
    assert clean.attendance_min.notna().all() and clean.attendance_min.ge(0).all()
    assert len(period) == len(clean) + int((~period.eligible_kpi).sum())
    checks = {'raw_rows':all_rows, 'exact_duplicates_removed':exact_duplicates,
        'conflicting_id_rows_all_years':int(conflict.sum()), 'period_rows_after_exact_dedup':len(period),
        'excluded_kpi_rows':int((~period.eligible_kpi).sum()), 'eligible_kpi_rows':len(clean),
        'distinct_incidents_in_eligible':int(clean.IncidentNumber.nunique()), 'parse_failures_all_years':parse_failures,
        'exclusion_flags_overlap':{c:int(flags[c].sum()) for c in flags},
        'component_inconsistent_or_missing_eligible':int((~clean.components_consistent).sum()),
        'missing_borough_eligible':int(clean.BoroughName.isna().sum()),
        'zero_attendance_eligible':int(clean.attendance_min.eq(0).sum()),
        'over_60_minutes_eligible':int(clean.attendance_min.gt(60).sum()),
        'date_min':str(period.DateAndTimeMobilised.min()), 'date_max':str(period.DateAndTimeMobilised.max())}
    daily = period.groupby(period.DateAndTimeMobilised.dt.floor('D')).size().reindex(pd.date_range(START, '2024-12-31', tz='UTC'), fill_value=0)
    checks['days_without_records'] = int(daily.eq(0).sum())
    daily.rename('mobilisations').to_csv(OUT / 'daily_coverage.csv')
    (OUT / 'audit.json').write_text(json.dumps(checks, indent=2), encoding='utf-8')
    period.loc[~period.eligible_kpi].to_csv(OUT / 'excluded_kpi.csv', index=False)
    clean.to_csv(ROOT / 'data/processed/mobilisations_2023_2024_clean.csv', index=False)
    flow = pd.DataFrame({'stage':['Source 2021-2024','After exact deduplication','Selected dispatch dates 2023-2024','KPI eligible'],
                         'rows':[all_rows,len(d),len(period),len(clean)]})
    flow.to_csv(OUT / 'row_flow.csv', index=False)
    summaries = {name:grouped(clean, cols) for name,cols in {'monthly':['month'], 'borough':['borough'],
        'hour':['hour_gmt'], 'station':['station'], 'year':['year'], 'borough_month':['borough','month'],
        'borough_hour':['borough','hour_gmt']}.items()}
    for name, table in summaries.items():
        table.to_csv(OUT / f'{name}_metrics.csv', index=False)
    bias = period.groupby('borough').agg(total=('eligible_kpi','size'), eligible=('eligible_kpi','sum'))
    bias['excluded_pct'] = (1-bias.eligible/bias.total)*100
    bias.to_csv(OUT / 'exclusions_by_borough.csv')
    summary = metrics(clean.attendance_min).to_dict()
    # Independent percentile computation from sorted values, not pandas quantile.
    ordered = sorted(clean.attendance_min.tolist())
    pos = (len(ordered)-1)*.9
    lower = int(pos)
    independent_p90 = ordered[lower] + (pos-lower)*(ordered[min(lower+1,len(ordered)-1)]-ordered[lower])
    assert abs(independent_p90-summary['p90_min']) < 1e-10
    assert int(summaries['borough'].n.sum()) == len(clean)
    assert int(summaries['monthly'].n.sum()) == len(clean)
    checks['independent_p90_min'] = independent_p90
    (OUT / 'audit.json').write_text(json.dumps(checks, indent=2), encoding='utf-8')
    summary['p99_min'] = float(clean.attendance_min.quantile(.99))
    summary['max_min'] = float(clean.attendance_min.max())
    summary['initial_mobilisations_n'] = int(clean.PlusCode_Code.eq('Initial').sum())
    summary['initial_mobilisations_p90_min'] = float(clean.loc[clean.PlusCode_Code.eq('Initial'), 'attendance_min'].quantile(.9))
    summary['positive_only_p90_min'] = float(clean.loc[clean.attendance_min.gt(0),'attendance_min'].quantile(.9))
    summary['known_borough_p90_min'] = float(clean.loc[clean.BoroughName.notna(),'attendance_min'].quantile(.9))
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    # Proposed review rule: >=100 observations, above contemporaneous global p90,
    # for >=3 consecutive months. This is a heuristic, not an LFB service target.
    bm = summaries['borough_month'].merge(summaries['monthly'][['month','p90_min']],on='month',suffixes=('','_global'))
    # Use the same complete-month window for the main rule and sensitivity analysis.
    review_months = pd.period_range('2023-01', '2024-11', freq='M').astype(str)
    bm = bm[bm.month.isin(review_months)].copy()
    bm['candidate_month'] = (bm.n >= 100) & (bm.p90_min > bm.p90_min_global) & bm.borough.ne('Unknown')
    review = []
    for borough, rows in bm.groupby('borough'):
        sequence = rows.set_index('month').candidate_month.reindex(review_months,fill_value=False)
        longest = current = 0
        for value in sequence:
            current = current+1 if value else 0
            longest = max(longest,current)
        review.append({'borough':borough,'longest_consecutive_months':longest,'review_candidate':longest>=3})
    pd.DataFrame(review).to_csv(OUT / 'review_candidates.csv',index=False)
    sensitivity=[]
    complete_months = list(review_months)
    for n_min in [50,100,200]:
        for months_min in [3,6]:
            count=0
            for borough, rows in bm[bm.month.isin(complete_months)].groupby('borough'):
                if borough == 'Unknown': continue
                series=rows.set_index('month').reindex(complete_months)
                seq=(series.n.ge(n_min)&series.p90_min.gt(series.p90_min_global)).fillna(False)
                current=longest=0
                for value in seq:
                    current=current+1 if value else 0
                    longest=max(current,longest)
                count+=int(longest>=months_min)
            sensitivity.append({'min_monthly_n':n_min,'consecutive_months':months_min,'candidate_boroughs':count,'scope':'2023-01 to 2024-11; incomplete December excluded'})
    pd.DataFrame(sensitivity).to_csv(OUT / 'review_sensitivity.csv',index=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130})
    def save(name, fig):
        fig.tight_layout()
        fig.savefig(FIG / f'{name}.png', bbox_inches='tight')
        plt.close(fig)
    values = clean.attendance_min.to_numpy(dtype=float)
    cap = summary['p99_min']
    fig, ax = plt.subplots(figsize=(10,5))
    ax.hist(values[values<=cap], bins=60, color='#287c8e', edgecolor='white', linewidth=.3)
    ax.axvline(summary['p90_min'],color='#ad4932',linestyle='--',label=f"P90 = {summary['p90_min']:.2f} min")
    ax.set(title=f'Dispatch to arrival, 2023-2024 (n={len(clean):,})',xlabel='Minutes; display limited to P99, all values retained in KPI',ylabel='Mobilisations')
    ax.legend(); save('01_distribution',fig)
    fig, ax = plt.subplots(figsize=(10,5))
    sample = np.random.default_rng(423).choice(values,size=min(20000,len(values)),replace=False)
    grid = np.linspace(0,cap,350)
    kde = gaussian_kde(sample)
    ax.plot(grid,kde(grid)+kde(-grid),color='#287c8e')
    ax.set(title='Density of dispatch-to-arrival time, 2023-2024',xlabel='Minutes (display to P99; reflected KDE at zero)',ylabel='Density')
    ax.text(.98,.95,f'Deterministic sample: {len(sample):,}',ha='right',transform=ax.transAxes)
    save('02_density',fig)
    fig, ax = plt.subplots(figsize=(10,5))
    ax.plot(np.sort(values),np.arange(1,len(values)+1)/len(values),color='#287c8e')
    ax.set_xscale('symlog',linthresh=1)
    ax.set(title='Cumulative distribution including the full tail',xlabel='Minutes (symmetric log scale above 1)',ylabel='Cumulative share')
    save('03_full_tail',fig)
    month = summaries['monthly']
    fig, axes = plt.subplots(2,1,figsize=(11,7),sharex=True)
    x = np.arange(len(month))
    axes[0].plot(x,month.p90_min,label='P90',color='#ad4932',marker='o')
    axes[0].plot(x,month.median_min,label='Median',color='#287c8e',marker='.')
    axes[0].set(ylabel='Minutes',title='Monthly dispatch-to-arrival times (Dec 2024: 31st absent)'); axes[0].legend()
    axes[1].bar(x,month.n,color='#287c8e'); axes[1].set(ylabel='Mobilisations',xlabel='Dispatch month (GMT)')
    ticks = [0,3,6,9,12,15,18,21,23]
    axes[1].set_xticks(ticks,month.month.iloc[ticks],rotation=45,ha='right')
    save('04_monthly',fig)
    b = summaries['borough'].query('n >= 100').sort_values('p90_min')
    fig, ax = plt.subplots(figsize=(11,11))
    ax.barh(b.borough,b.p90_min,color='#287c8e')
    ax.set(title='Published mobilisation P90 by borough (2023-2024; Dec 31 absent)',xlabel='Minutes; labels show eligible n; Unknown is missing geography')
    ax.set_xlim(0,b.p90_min.max()*1.25)
    for i, row in enumerate(b.itertuples()): ax.text(row.p90_min+.05,i,f'n={row.n:,}',va='center',fontsize=9)
    save('05_borough',fig)
    h = summaries['hour']
    fig, axes = plt.subplots(2,1,figsize=(10,7),sharex=True)
    axes[0].plot(h.hour_gmt,h.p90_min,color='#ad4932',label='P90'); axes[0].plot(h.hour_gmt,h.median_min,color='#287c8e',label='Median')
    axes[0].set(title='Times by dispatch hour (GMT), 2023-2024',ylabel='Minutes'); axes[0].legend()
    axes[1].bar(h.hour_gmt,h.n,color='#287c8e'); axes[1].set(xlabel='Dispatch hour GMT, not local summer time',ylabel='Mobilisations',xticks=range(0,24,2))
    save('06_hour',fig)
    matrix = clean.groupby(['weekday_gmt','hour_gmt']).attendance_min.quantile(.9).unstack().reindex(index=range(7),columns=range(24))
    fig, ax = plt.subplots(figsize=(12,4))
    im=ax.imshow(matrix.to_numpy(dtype=float),aspect='auto',cmap='cividis')
    ax.set(yticks=range(7),yticklabels=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],xticks=range(0,24,2),xlabel='Dispatch hour (GMT)',title='P90 by weekday and hour, 2023-2024')
    fig.colorbar(im,ax=ax,label='Minutes'); save('07_heatmap',fig)
    components = clean.loc[clean.components_consistent,['TurnoutTimeSeconds','TravelTimeSeconds','AttendanceTimeSeconds']].astype(float)
    corr=components.corr(method='spearman'); corr.to_csv(OUT / 'spearman_components.csv')
    fig, ax=plt.subplots(figsize=(8,6))
    im=ax.imshow(corr,cmap='coolwarm',vmin=-1,vmax=1)
    labels=['Turnout','Travel','Total']
    ax.set(xticks=range(3),xticklabels=labels,yticks=range(3),yticklabels=labels,title=f'Spearman correlations (complete consistent rows n={len(components):,})')
    for i in range(3):
        for j in range(3): ax.text(j,i,f'{corr.iloc[i,j]:.2f}',ha='center',va='center',color='black')
    fig.colorbar(im,ax=ax); save('08_correlations',fig)
    fig,ax=plt.subplots(figsize=(10,5))
    yearly=[clean.loc[clean.year.eq(y),'attendance_min'].to_numpy(dtype=float) for y in [2023,2024]]
    ax.boxplot(yearly,tick_labels=['2023','2024'],showfliers=False)
    ax.set(title='Dispatch-to-arrival distribution by year',ylabel='Minutes',xlabel='Fliers hidden in this view only; no outlier deletion')
    save('09_year_boxplot',fig)
    print(json.dumps({'audit':checks,'summary':summary},indent=2))
    return raw, period, clean, summaries, checks, summary

if __name__ == '__main__':
    run()
