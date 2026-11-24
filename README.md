# Group 11 — C3 final BI study

**Version for assessment: C3-2026-11-23-r1.** Authors: Matías Muñoz Hoffmann and Clemente Ibarra.

Question: can a dispatch-time flag identify vehicle arrivals taking at least 600 seconds in the published LFB 2023–2024 cohort? Our conclusion is a conditional retrospective model with better detection and persistently low precision. The ten-minute definition is analytical, not an official LFB target. One row is one vehicle mobilisation, not one incident.

## Reading order — no setup required

1. `notebooks/01_Data_and_EDA.ipynb`: sources/versions, unit, preparation row flow, quality checks, dictionary, EDA, sampling and coverage.
2. `notebooks/02_Models_and_Evaluation.ipynb`: ordered feature pipeline, availability, chronological windows, explicit classifier/preprocessing settings, validation cutoff, fair reference, metrics and limits.
3. `notebooks/03_Visual_System_and_Decisions.ipynb`: shared visual implementation, all three W3 redesign pairs, feedback-to-decision record, narrative choice, assigned responsibilities and AI disclosure.
4. `presentations/C3_Grupo11.pptx`: Presentation 1 (simulated LFB planning audience), then Presentation 2 (instructor internal review). Each member speaks substantively in both. Hidden backup slides support questions.

Optional offline browser copies of the same saved evidence are in `docs/readable_views/`. They do not execute code or require external resources.

**Read the saved notebook outputs. No installation, execution or download is required.** These notebooks were executed against archived private inputs. They show their methods beside saved evidence. Input files are intentionally omitted, including raw/clean data, extracts, fitted-model caches and row-level predictions. Running data-dependent cells elsewhere would require the original private archives; this is not a reviewer requirement.

## Ordered pipeline and file roles

Identified official inputs → scope and audited eligibility → calendar/context and optional incident-location join → strictly earlier history → training-only transforms and classifier → validation-only cutoffs → frozen retrospective test → saved charts and two audience-specific presentations.

`src/method_record/` preserves the actual original feature/search/evaluation methods as readable reference. Those historical scripts keep their original relative archive conventions and are not a standalone installation package. Notebook 02 explicitly refits the selected model and recalculates its validation cutoff. `src/visual_system.json` and `visual_system.py` implement visual rules used by notebook charts. `presentations/build_presentations.mjs` uses the same rules for editable slide objects. `figures/` contains SVG editable charts and PNG views, also embedded in the notebooks.

Software: Python 3, pandas, NumPy, scikit-learn, matplotlib, nbformat/nbclient and the first-party Artifact Tool for editable presentations. The exploration also tested CatBoost and LightGBM; recorded settings/results are described in notebook 02 and historical method files. No software installation is required to read this submission.

## Final result and its limits

Selected expanded logistic: C=0.002, balanced weights, score cutoff 0.34265157602812196 selected for validation recall >=85%. Test matrix [[61264,33551],[988,6445]], with rows actual under/at least ten minutes and columns predicted under/at least ten minutes. Recall 86.71%, precision 16.11%, 39,996 alerts on 102,248 test rows (7,433 actual long cases).

Original C2 trains on 2023; the selected final version trains through March 2024 and validates April–June. Both use the same July–30 December test rows. Earlier coursework explored this test period, so it remains retrospective. Published location fields require dispatch-time availability checks. Station postcode points are not vehicle GPS or road distances, and 2025 station addresses were not individually verified for every 2023 dispatch. Past-response features assume immediate arrival feedback. The source lacks 31 December 2024 and an observed tail above twenty minutes. Prediction does not establish intervention benefit.

## Sources and development

The mobilisation source snapshot was retrieved on 23 September 2026; URLs and SHA-256 are saved in notebook 01. The official incident catalogue, ONS postcode directory and address qualifications are described in notebook 02. The decision record links each important change/retention to saved evidence. Notebook 03 distinguishes assigned equitable review/defense responsibilities from personal work that has not been individually verified, and records Codex assistance.

No earlier data-bearing ZIP should replace this assessed version. `MANIFEST.json` identifies file hashes in this snapshot. Upload this repository version and the two clearly marked presentation sections through Canvas **before 24 November 2026, 14:00 Santiago**. The ten-minute team limit includes both presentations and questions.
