"""Generate and execute the C1 notebook using the current Python environment."""
from pathlib import Path
import json
import os
import sys
import importlib.metadata
import nbformat as nbf
from nbclient import NotebookClient
from nbconvert import HTMLExporter
from jupyter_client import KernelManager

ROOT=Path(__file__).resolve().parents[1]
cells=[]
def md(text): cells.append(nbf.v4.new_markdown_cell(text))
def code(text): cells.append(nbf.v4.new_code_cell(text))

md('''# London Fire Brigade: mobilisation to arrival
**C1 | Business Intelligence | 29 September 2026**  
Matias Muñoz Hoffmann and Clemente Ibarra

Academic diagnostic analysis of published records, with AI-assisted preparation.
AI use and verification are documented in PROCESS_LOG.md.

## Context & Methods
**Question:** Which boroughs and dispatch hours merit a review of long mobilisation-to-arrival times?
**Decision:** prioritise investigation; no automatic staffing or dispatch recommendation.
**Population:** published pumping-appliance mobilisations dispatched in 2023-2024.
**Unit:** one mobilisation, not one incident. **KPI:** P90 attendance seconds / 60.

### Key assumptions and limits
- GMT follows the source dictionary. Hour refers to dispatch, not call receipt.
- 31 December 2024 is absent; December and annual 2024 totals are partial.
- The extract contains only Initial records and durations at most 20 minutes.
- [LFB methodology](https://www.london-fire.gov.uk/media/8863/foia84201-response-times-of-fire-brigades-and-data-collation-response.pdf)
  documents >20-minute exclusions for performance calculations; exact CSV selection rules are not fully verified.
- Unknown geography remains visible. Comparisons are unadjusted for incident mix and distance.

## Data
[Official dataset and metadata](https://data.london.gov.uk/dataset/london-fire-brigade-mobilisation-records-24r65).
Download first with `python scripts/download_data.py`. Hashes identify the exact original snapshot.
''')
code('''from pathlib import Path
import sys, json, io, contextlib
import pandas as pd
from IPython.display import display, Markdown, Image
ROOT = Path.cwd()
if ROOT.name == 'notebooks': ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from analysis import run
display(pd.DataFrame(json.loads((ROOT/'data/source_manifest.json').read_text())).T)
''')
md('''### Reproducible audit and cleaning
The companion `scripts/analysis.py` is part of the submission and contains all transformations.
It reads the original snapshot, profiles missingness and coverage, parses dates/numbers,
removes exact duplicate rows and quarantines conflicting IDs. No target imputation or
arbitrary outlier removal is applied. Missing partial durations do not invalidate a consistent total.
The pipeline exports every reconciliation and produces the charts below.
''')
code('''with contextlib.redirect_stdout(io.StringIO()):
    raw, period, clean, tables, audit, summary = run()
display(pd.read_csv(ROOT/'outputs/row_flow.csv'))
display(pd.DataFrame({'exclusion_flag': audit['exclusion_flags_overlap'].keys(),
                      'rows': audit['exclusion_flags_overlap'].values()}))
''')
md('## Summary')
code('''display(Markdown(f"""The selected published population contains **{len(clean):,} eligible mobilisations**
across **{clean.IncidentNumber.nunique():,} distinct incident IDs**. Median attendance is
**{summary['median_min']:.2f} minutes** and P90 is **{summary['p90_min']:.2f} minutes**.
The original four-year file contains {audit['exact_duplicates_removed']:,} exact duplicate rows;
{audit['excluded_kpi_rows']} selected-period rows are excluded by the KPI rules.
**Scope caveat:** the missing final day and the observed 20-minute ceiling prevent claims
about complete annual demand or the unobserved extreme tail."""))
''')
md('### Quality profile and missingness')
code("display(pd.read_csv(ROOT/'outputs/raw_profile.csv').sort_values('missing_pct',ascending=False))\ndisplay(pd.DataFrame(audit['parse_failures_all_years'].items(),columns=['field','parse_failures']))")
md('''Missing return times and missing delay codes are not filled with zero. A missing delay
description means unknown/unrecorded, not proven absence of a delay. Geography is not imputed.
The older dictionary lacks BoroughName and WardName; they are used as published labels.
''')
code('''display(pd.read_csv(ROOT/'outputs/exclusions_by_borough.csv').sort_values('excluded_pct',ascending=False).head(10))
display(pd.DataFrame({'metric':['missing geography','components unavailable/inconsistent','zero duration'],
    'eligible_rows':[audit['missing_borough_eligible'], audit['component_inconsistent_or_missing_eligible'],audit['zero_attendance_eligible']]}))
coverage=pd.read_csv(ROOT/'outputs/daily_coverage.csv')
display(coverage[coverage.mobilisations.eq(0)])
''')
md('### Verification of the KPI')
code('''elapsed=(clean.DateAndTimeArrived-clean.DateAndTimeMobilised).dt.total_seconds()
assert (elapsed-clean.AttendanceTimeSeconds).abs().le(1).all()
assert clean.ResourceMobilisationId.is_unique
assert len(period)==len(clean)+audit['excluded_kpi_rows']
assert sum(tables['monthly']['n'])==len(clean)
display(pd.Series(summary, name='value').to_frame())
display(Markdown(f"Independent sorted-value P90: **{audit['independent_p90_min']:.2f} minutes**."))
''')
md('''## Results
All figures refer to eligible published mobilisations in the requested 2023-2024 window;
31 December 2024 is absent. Published records do not measure all actual service demand.
''')
charts=[
('01_distribution','Distribution','The histogram shows the centre and right tail up to P99 for legibility. The KPI retains every eligible observation, including those outside the displayed range.'),
('02_density','Density','The KDE uses a deterministic sample of 20,000 records and reflection at zero. It is a smoothed display, not a fitted predictive model or an estimate of unobserved >20-minute responses.'),
('03_full_tail','Entire observed tail','This cumulative view retains all observed values. The 20-minute ceiling is a property of the source extract, not a cleaning cutoff imposed by this project.'),
('04_monthly','Monthly pattern','Median and P90 summarise different parts of the distribution. Volume is shown separately. December 2024 is partial; changes are descriptive and do not identify causes.'),
('05_borough','Geographic comparison','Unknown is a data-quality group, not a borough. Different case mix and distances may explain differences; this chart does not rank crew quality.'),
('06_hour','Dispatch hour','Hours use the documented GMT basis rather than local summer time. Longer observed durations at a given hour do not independently establish traffic as the cause.'),
('07_heatmap','Weekday and hour','Each cell pools published records in that weekday/hour combination. This highlights patterns for investigation, without statistical significance claims.'),
('08_correlations','Correlations','Total attendance contains turnout and travel by construction. Correlation with its components is partly arithmetic and is not causal evidence. Components are unavailable at dispatch and must not become C2 predictors.'),
('09_year_boxplot','Year comparison','Boxplots hide fliers only for display. All valid rows remain in the KPI. The 2024 total lacks the final calendar day; there is no full-year demand growth claim.')]
for name,title,note in charts:
    md('### '+title)
    code(f"display(Image(filename=str(ROOT/'outputs/figures/{name}.png')))" )
    md(note)
md('### Exact values and candidate reviews')
code('''display(tables['year'])
display(tables['borough'].query("borough != 'Unknown'").sort_values('p90_min',ascending=False).head(5))
display(tables['hour'].sort_values('p90_min',ascending=False).head(5))
display(pd.read_csv(ROOT/'outputs/review_sensitivity.csv'))
''')
md('''The proposed rule flags a borough with at least 100 eligible records per month and
P90 above the contemporary global P90 for at least three consecutive months. It is an
academic heuristic, not an LFB target. Both the candidate list and sensitivity analysis use
January 2023 to November 2024, excluding incomplete December 2024. The sensitivity table
changes volume and persistence requirements. Candidate lists support further investigation.
''')
md('## Conclusions')
code('''top=tables['borough'].query("borough != 'Unknown'").sort_values('p90_min',ascending=False).iloc[0]
hour=tables['hour'].sort_values('p90_min',ascending=False).iloc[0]
display(Markdown(f"""1. Among named boroughs, **{top.borough}** has the highest observed P90,
**{top.p90_min:.2f} min**, across **{int(top.n):,}** eligible records.
2. The highest pooled hourly P90 occurs at **{int(hour.hour_gmt):02d}:00 GMT**,
**{hour.p90_min:.2f} min**. This is an association, not a traffic-effect estimate.
3. We recommend reviewing case mix and source eligibility before using these patterns operationally.
4. The missing final day and the observed 20-minute ceiling limit conclusions about annual
demand and extreme durations. Several mobilisations can belong to one incident, so the
results describe vehicle mobilisations rather than independent emergencies."""))
''')
md('''### Reproducibility and sources
The original manifest, audited tables, source dictionary and source links are retained.
See `docs/SOURCES.md`, `docs/KPI.md` and `scripts/analysis.py`. Checks compare timestamp
differences with recorded attendance, independently recompute P90 and reconcile group totals.
This does not constitute external verification of every operational record.
''')

def main():
    (ROOT/'notebooks').mkdir(exist_ok=True)
    (ROOT/'outputs').mkdir(exist_ok=True)
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}})
    # An explicit kernel command avoids accidentally using another system Python.
    km=KernelManager(kernel_name='python3')
    km.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
    client=NotebookClient(nb,timeout=600,km=km,resources={'metadata':{'path':str(ROOT)}})
    client.execute(cwd=str(ROOT))
    nbf.validate(nb)
    nbf.write(nb,ROOT/'notebooks/C1_LFB.ipynb')
    html,_=HTMLExporter().from_notebook_node(nb)
    (ROOT/'outputs/C1_LFB.html').write_text(html,encoding='utf-8')
    packages=['pandas','numpy','matplotlib','scipy','nbformat','nbclient','nbconvert','ipykernel','openpyxl']
    versions={p:importlib.metadata.version(p) for p in packages}
    (ROOT/'requirements.txt').write_text('\n'.join(f'{p}=={v}' for p,v in versions.items())+'\n')
    validation={'notebook_executed':True,'format_valid':True,'error_outputs':sum(o.output_type=='error' for c in nb.cells if c.cell_type=='code' for o in c.outputs),
                'versions':versions}
    (ROOT/'outputs/validation.json').write_text(json.dumps(validation,indent=2))
    print(json.dumps(validation,indent=2))

if __name__=='__main__': main()
