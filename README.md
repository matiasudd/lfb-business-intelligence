# London Fire Brigade BI — Group 11

## Workshop 2 delivery (C1 continuation)

**Authors:** Matías Muñoz Hoffmann and Clemente Ibarra. The executable English
notebook is [`notebooks/W2_project.ipynb`](notebooks/W2_project.ipynb). Its
source builder is [`scripts/build_w2_notebook.py`](scripts/build_w2_notebook.py),
and its CSV evidence is in [`outputs/w2/`](outputs/w2/). The original C1
submission in `GROUP_11_C1/` remains unchanged.

The C1 question—where and when published London Fire Brigade vehicle
mobilisations have longer mobilisation-to-arrival times—continues. Following
the team's clarification of the instructor's C1 comment, W2 replaces P90 as
the primary KPI with the **share of eligible mobilisations lasting 10 minutes
or more**: `100 × count(AttendanceTimeSeconds >= 600) / eligible mobilisations`.
Exactly 600 seconds is included. C1's P90 was 552 seconds (9.2 minutes),
which informed the choice of a fixed, round 600-second cutoff. Unlike a
moving P90 cutoff, it stays at 600 seconds when response times change. P90
and the median remain supporting measures. The threshold is an exploratory
team choice, **not an official LFB service target**. In the retained published
2023–2024 case, the KPI is 26,367 / 384,627 = **6.855%**.

To reproduce from a fresh clone, use Python 3.12 and run these commands from
the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/build_w2_notebook.py
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/W2_project.ipynb --ExecutePreprocessor.timeout=600
python scripts/verify_w2.py
```

On macOS/Linux, activate with `source .venv/bin/activate` instead. The included
cleaned C1 snapshot and audit files are sufficient to run W2; no additional
download of the original large CSV is required. If PowerShell activation is
restricted, invoke `.\.venv\Scripts\python.exe` in place of `python` in the
remaining commands.

The notebook reads `GROUP_11_C1/data/case_tables/mobilisations_2023_2024_clean.csv.gz`
and C1's saved audit. It recreates validation, figures, a fixed-seed 25%
sample, a leakage audit, and chronological train/validation/test subsets.
The generated tables in `outputs/w2/` are audit evidence, not additional raw
sources. The output has been executed locally with `requirements.txt`.

The available source lacks 31 December 2024 and has no recorded duration
above 20 minutes. `Unknown` geography stays in the overall denominator:
1,288 such rows have a 45.03% at-least-10-minute rate. Geographic contrasts are
descriptive, unadjusted, and cannot establish causes. C1 inspected the full
dataset before W2, so W2's chronological test is a retrospective robustness
check rather than a pristine predictive evaluation. No model is trained.

The notebook includes the required feedback-to-action table, variable
dictionary, target/observed/analytical populations, chart interpretations,
sample comparison, split counts and overlap check, train-only preprocessing,
management summary, source links and AI-use disclosure. The team clarified that
the C1 instructor's feedback concerned a moving P90-based comparison threshold;
the revised ten-minute threshold remains fixed even if P90 falls in later
periods. No W1 instructor feedback was received.

The retained W1 source manifest is included as
[`docs/w2/w1_source_manifest.json`](docs/w2/w1_source_manifest.json).
It records the same original CSV URL, retrieval timestamp, size and SHA256 as
[`GROUP_11_C1/data/source_manifest.json`](GROUP_11_C1/data/source_manifest.json):
`f18f9ea1943ce54ac58e3429ed2d242f9d1fa714d3a556d43d44b8a4fcf9afba`.
This documents source continuity between the retained W1 and C1 materials.
It does not establish which files were uploaded to the course platform.

**27 October review:** Each figure and the sample comparison now have a numeric
interpretation, the dictionary states expected data types explicitly, and the
validation table reports 1,816 rows with missing duration components plus one
timestamp-consistent zero duration. Both remain in the KPI under the existing
eligibility rules. The updated C1 conclusions and holdout interpretation are
explicit; the ten-minute threshold and analytical population are unchanged.

**AI-use statement for W2:** The team chose the dataset and defined the fixed
ten-minute KPI after the instructor's feedback. OpenAI Codex supported Python
coding, validation checks, and the wording of explanations. The team remains
responsible for reviewing the results and defending its choices at the workshop.

**Repository:** https://github.com/matiasudd/lfb-business-intelligence
**W2 version tag:** `w2-2026-10-27-reviewed` (supersedes `w2-2026-10-22-final`). The notebook, README and supporting
files are published on `main` in the public repository. A separate submission
to the course platform, if required, remains the team's responsibility.

## Historical C1 delivery

We are Matias Munoz Hoffmann and Clemente Ibarra. We investigate vehicle
mobilisation-to-arrival times in published London Fire Brigade records for
2023-2024. Our unit is one vehicle mobilisation, not one emergency.

## C1 submission

We keep our current delivery in [`GROUP_11_C1/`](GROUP_11_C1/).
Our [submission README](GROUP_11_C1/README.md) describes the sources, software,
execution order, AI assistance, individual reviews and interpretation limits.

- [Report PDF](GROUP_11_C1/report/GROUP_11_C1_Report.pdf)
- [Presentation PDF](GROUP_11_C1/presentation/GROUP_11_C1_Slides.pdf)
- [Editable presentation](GROUP_11_C1/presentation/C1_LFB_English_Final.pptx)
- [Executed notebook](GROUP_11_C1/analysis/C1_LFB.ipynb)
- [Analysis code](GROUP_11_C1/analysis/analysis.py)
- [Code guide](GROUP_11_C1/analysis/CODE_GUIDE.md)
- [Data and verification evidence](GROUP_11_C1/data/)
- [Process history and confirmed reviews](PROCESS_LOG.md)

Our saved notebook has 17 executed code cells without error outputs. We obtained
384,627 eligible mobilisations, median attendance of 5.65 minutes and P90 of
9.20 minutes. Hillingdon and the 11:00 GMT group are examples for contextual
investigation, not causal findings or rankings of crew quality. The source lacks
31 December 2024 and contains no observed duration above 20 minutes.

We used Codex to support coding, figure preparation and drafting. The team
selected the problem and reviewed the stated criteria and findings; we do not
claim unaided code authorship.
Matias reviewed row flow/P90 and Clemente reviewed borough/hour comparisons
and limitations. We received no W1 instructor feedback.

We preserve the earlier `scripts/`, `notebooks/`, `outputs/`, `presentation/`
and `docs/` as preparation history, including the prior remote review.
Those are not our current delivery; we use `GROUP_11_C1/` for the final files.
Contains London Fire Brigade / Greater London Authority information; source
attribution and interpretation limits are recorded in our submission.

The C1 section records the earlier deliverable. GitHub publication alone does
not establish whether a course-platform submission was completed.
