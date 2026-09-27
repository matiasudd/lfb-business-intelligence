# London Fire Brigade: mobilisation to arrival

Business Intelligence IIB423T-2 | C1 | 29 September 2026

**Team:** Matias Muñoz Hoffmann and Clemente Ibarra.

**Status:** C1 preparation for team review; publication metadata is in docs/ENTREGA.md.
The team confirmed that the London case is permitted; no additional rubric is available.

## Decision and scope

Identify boroughs and dispatch hours that merit an operational review of long
mobilisation-to-arrival times. This is an academic diagnostic study, not an
operational dispatch tool or an evaluation of individual firefighters.

Source: [London Fire Brigade Mobilisation Records](https://data.london.gov.uk/dataset/london-fire-brigade-mobilisation-records-24r65),
2021-2024 CSV; analysis period: dispatch timestamps in 2023-2024 (GMT as documented).
Each row represents a vehicle mobilisation. Multiple mobilisations can belong to
the same incident. The population covers published pumping-appliance responses,
not only fires. No incident-type information is available in this file.
The extract contains only Initial mobilisations, no durations above 20 minutes,
and no records on 31 December 2024. Results concern this published population;
December and annual 2024 totals are incomplete.

The main KPI is P90 of AttendanceTimeSeconds / 60 among eligible records.
It starts at mobilisation, not at the emergency call. All vehicle arrivals are
included; it is not a first-appliance response standard. See `docs/KPI.md`.

## Deliverables

- `notebooks/C1_LFB.ipynb`: executed analysis, methods, evidence and interpretation.
- `outputs/C1_LFB.html`: portable rendered notebook.
- `outputs/C1_LFB_reviewed.pptx`: 13-slide presentation with editable charts.
- `outputs/figures/`: distributions, comparisons, temporal patterns and correlations.
- `outputs/audit.json`, `row_flow.csv`, `raw_profile.csv`: quality and reconciliation.
- `outputs/summary.json` and `*_metrics.csv`: reproducible numerical evidence.
- `docs/CASE_BRIEF.md`, `KPI.md`, `DEFENSA_ES.md`: decision, measurement and study guide.
- `PROCESS_LOG.md`: AI contribution, verification and outstanding human review.
- `docs/AI_INTERACTIONS.md`: selected original prompts and relevant AI responses.
- `docs/ENTREGA.md`: publication and Canvas checklist.

## Reproduce

Python 3.12 was used. From this directory, create a virtual environment, install
`requirements.txt`, and run:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/download_data.py
.venv/Scripts/python.exe scripts/build_notebook.py
```

The build executes the notebook and regenerates tables, charts and HTML. The
notebook can also run top-to-bottom in a Python kernel with these dependencies.
Raw files and the processed CSV are excluded from Git. `data/source_manifest.json`
records the exact source URLs, retrieval timestamp and SHA256 checksums. Source
updates may change the download; retain the submitted raw snapshot separately
and check the manifest before comparing reproduced results. The downloader fails
on checksum drift rather than silently replacing an existing snapshot identity.

## Interpretation limits

Descriptive associations do not establish causality. Vehicle mix, incident type,
distance, traffic and resource availability are not controlled. Missing geographic
labels remain Unknown. No imputation of the target, no arbitrary outlier trimming,
and no claim of a statutory service-level breach. Multiple rows per incident
are not independent emergency events. The analysis does not extrapolate to Chile.

## Attribution and use

Contains London Fire Brigade / Greater London Authority information; source
portal lists Open Government Licence v2. Cite the publisher and the dataset when
reusing results. The publisher's dictionary is retained locally and exported to
`outputs/source_dictionary.csv`. This repository does not claim ownership of
source data. No names of victims, home addresses or credentials are required.

AI-assisted preparation is disclosed in PROCESS_LOG.md. Students must understand,
verify and accept the submission; the log does not claim that human review or an
individual contribution has occurred when it has not.
