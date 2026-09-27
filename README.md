# London Fire Brigade attendance times

Business Intelligence C1 — 29 September 2026
Matías Muñoz Hoffmann and Clemente Ibarra

## Project

Which London districts and dispatch hours show persistently long vehicle
mobilisation-to-arrival times and merit operational investigation?

The study uses published London Fire Brigade pumping-appliance mobilisation
records with dispatch dates in 2023–2024, on the GMT basis documented by the
source. One row represents one vehicle mobilisation. Several vehicles can attend
one incident. The data includes responses beyond fires.

The main KPI is the 90th percentile of attendance time in minutes. Among 384,627
eligible mobilisations, the median is 5.65 minutes and P90 is 9.20 minutes.
The measure starts at mobilisation and excludes earlier call handling.

## Files to review

| File | Content |
|---|---|
| [Executed notebook](notebooks/C1_LFB.ipynb) | Question, data quality, cleaning, validation, full EDA and conclusions |
| [Analysis in HTML](outputs/C1_LFB.html) | The same executed notebook in browser-readable form |
| [Presentation](presentation/C1_LFB.pptx) | English presentation and technical appendix |
| [Process record](PROCESS_LOG.md) | Decisions, checks, individual contributions and AI disclosure |
| [Case brief](docs/CASE_BRIEF.md) | Decision, population and scope |
| [KPI definition](docs/KPI.md) | Measurement and review rule |
| [Sources](docs/SOURCES.md) | Data provenance and evidence boundaries |

`scripts/` contains the reproducible analysis. `outputs/` contains its generated
audit tables, analytical results and figures. `data/source_manifest.json` records
the source URLs, retrieval information and SHA256 file hashes. There is one
presentation and one analytical notebook in the submitted repository.

## Findings and limits

Hillingdon has the highest P90 among named districts, at 10.67 minutes. The highest
pooled hourly P90 occurs at 11:00 GMT, at approximately 10.03 minutes. These are
descriptive comparisons without adjustment for distance or incident mix.

The source has no records for 31 December 2024. December and annual 2024 totals
are incomplete. All observed records are Initial and attendance durations do not
exceed 20 minutes. The exact source selection rules are not fully confirmed.
The data cannot describe the unobserved extreme tail or all actual demand.
Unknown geography remains visible. Repeated incident IDs represent multiple
mobilisations and are not automatically duplicates.

The district review rule and its sensitivity analysis both use January 2023 to
November 2024. The proposed rule identifies 19 districts at three consecutive
months and 15 at six months. These thresholds support investigation and are not
official service standards.

## Reproduction

Python 3.12 and the packages pinned in `requirements.txt` are required. Run from
the repository root:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/download_data.py
.venv/Scripts/python.exe scripts/build_notebook.py
```

On macOS or Linux, use `.venv/bin/python` instead of `.venv/Scripts/python.exe`.
The build executes the notebook and regenerates the analytical tables, figures
and HTML. The presentation is an editable PowerPoint document.

The original CSV is about 168 MB and is excluded from Git. The downloader checks
its SHA256 against the recorded snapshot and fails if the source has changed.
The processed CSV is generated in `data/processed/`. The submitted notebook and
HTML contain saved results, so reading the analysis does not require a download.

## Attribution

Contains London Fire Brigade / Greater London Authority information. The source
catalogue lists Open Government Licence v2. Source links and interpretation
limits are documented in `docs/SOURCES.md`. AI assistance and student review are
recorded in `PROCESS_LOG.md`.
