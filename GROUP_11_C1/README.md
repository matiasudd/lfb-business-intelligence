# GROUP_11_C1 - London Fire Brigade

Business Intelligence C1 | 29 September 2026 | Group 11

We are Matias Munoz Hoffmann and Clemente Ibarra. We analyse vehicle
mobilisation-to-arrival times in published London Fire Brigade records for
2023-2024. We compare boroughs and dispatch hours to identify patterns for
further investigation, without claiming causal effects or ranking crew quality.

## Our submission files and reading order

1. `report/GROUP_11_C1_Report.pdf`: our self-contained report, including methods,
   findings, limitations, future work, process record and references. We have
   included the instructor-feedback statement in this report.
2. `presentation/GROUP_11_C1_Slides.pdf`: our presentation. We also include its
   editable source, `presentation/C1_LFB_English_Final.pptx`.
3. `analysis/C1_LFB.ipynb`: our executed notebook with saved outputs.
4. `analysis/analysis.py`: our profiling, cleaning, KPI and EDA code.
5. `analysis/CODE_GUIDE.md`: our step-by-step explanation of the code.
6. `data/case_tables/`: our processed data, audit tables, indicators and figures.

## Our data and sources

We preserve the original 24-column CSV in
`data/raw/mobilisations_2021_2024.csv.gz` and include the publisher's metadata
workbook. Our `data/source_manifest.json` records the exact URLs and source
checksums. Our code verifies the original uncompressed SHA256 before analysis.

We include an uncleaned 2023-2024 input extract of 386,504 rows in
`data/reduced/mobilisations_2023_2024_input.csv.gz`. We selected rows using the
year in `DateAndTimeMobilised`, without removing duplicates or changing values.
We document its selection and checksum in `data/reduced/reduced_input_manifest.json`.
We can reconstruct it using `analysis/reconstruct_reduced.py`.

We distinguish these input files from the processed outputs in
`data/case_tables/`, which include the cleaned case, exclusions, row flow,
profiles, KPI tables, sensitivity checks and nine figures.

For GitHub, we store the processed case as
`data/case_tables/mobilisations_2023_2024_clean.csv.gz`, a lossless gzip copy of
the CSV. Running our analysis regenerates the uncompressed CSV locally. This
storage choice does not change the rows or calculations.

Our source is the [official London Datastore catalog](https://data.london.gov.uk/dataset/london-fire-brigade-mobilisation-records-24r65).
The included source snapshot was retrieved on 23 September 2026. We preserve
it so that future changes to the public download do not alter our results.
We document supporting sources in `data/SOURCES.md` and include our prior W1
report as `data/W1_selection_evidence.pdf`. That prior report shows provisional
group number 00; our confirmed C1 group number is 11.

## Reproducing our analysis

Our saved analysis used Python 3.12, pandas 3.0.1, numpy 2.3.5,
matplotlib 3.11.2, scipy 1.18.1, nbformat 5.11.1, nbclient 0.11.0,
nbconvert 7.17.1, ipykernel 7.3.0 and openpyxl 3.1.5.
From this `GROUP_11_C1` folder, we can install the dependencies and rerun:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r analysis/requirements.txt
.venv/Scripts/jupyter-nbconvert.exe --to notebook --execute analysis/C1_LFB.ipynb --output C1_LFB_rerun.ipynb
```

We can also open the notebook in Jupyter with this environment and run all cells
in order. Our analysis uses project-relative paths. To run the analysis script
alone, we use `.venv/Scripts/python.exe analysis/analysis.py`; it reads the
included original snapshot and metadata and refreshes `data/case_tables/`.
To reconstruct the uncleaned reduced input, we use
`.venv/Scripts/python.exe analysis/reconstruct_reduced.py`, which verifies its
row count and uncompressed checksum.

Our supplied notebook has 17 executed code cells with saved outputs and no
error outputs. Our results include 384,627 eligible mobilisations, median
attendance of 5.65 minutes and P90 of 9.20 minutes. We have no unresolved
execution error recorded in that notebook. We exclude environments, caches,
installed applications and credentials from the submission.

## Our interpretation limits

We treat one row as one vehicle mobilisation, not one emergency. We calculate
P90 over eligible published records, not as an official first-appliance standard.
The source lacks 31 December 2024 and no observed duration exceeds 20 minutes.
We retain unknown boroughs in the global KPI. We do not infer causes or staff
performance from descriptive differences. We propose, but do not implement,
the C2 model and dashboard in C1.

## How we used AI and reviewed the work

We used OpenAI Codex for technical and coding assistance: exploring dataset
feasibility, working on syntax for quality checks and structuring the initial
deliverables. We also received assistance generating code, figures and drafts.
We adopted the scope and methodological criteria described in our report.
We preserve relevant interactions and verification evidence in
`data/AI_INTERACTIONS.md`; our acceptance does not imply unaided code authorship.

Matias reviewed row flow and P90; Clemente reviewed borough/hour comparisons
and limitations. We confirmed our reflection text, and Matias communicated
this confirmation on behalf of both of us on 29 September 2026. We record it
in `data/TEAM_CONFIRMATION.md`. Each of us remains responsible for explaining
the decisions and our own reviews during the defense.

We did not receive instructor feedback on W1. We retained our geographic focus
as a working decision, without claiming approval of the specific KPI or review
rule. We document this in our report and `data/INSTRUCTOR_FEEDBACK.md`.

## Canvas submission

We keep this project in a single `GROUP_11_C1` root folder with the required
subfolders. The rubric requires this folder inside `GROUP_11_C1.zip` or
`GROUP_11_C1.rar` for Canvas. The folder is currently unarchived; packaging
and uploading to Canvas remain pending.
