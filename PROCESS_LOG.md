# Process record

Matías Muñoz Hoffmann and Clemente Ibarra
C1 — London Fire Brigade attendance times

## Decisions and checks

| Decision | Reason and alternative | Verification and evidence |
|---|---|---|
| Use public London Fire Brigade records | The data includes vehicle-level timestamps and operational categories. Matías selected London after considering the proposed source. | Original CSV and dictionary, `data/source_manifest.json`, `docs/SOURCES.md` |
| Select dispatch dates in 2023–2024 | A defined two-year window permits monthly and annual comparisons. The source covers 2021–2024. | Date filters and coverage audit in `scripts/analysis.py`; missing final day disclosed |
| Use mobilisation as the observation | Several vehicles may attend one incident. Deduplicating by incident would remove valid responses. | Unique mobilisation IDs and distinct incident count in `outputs/audit.json` |
| Use P90 with median and volume | P90 describes longer times while the median describes the centre. A mean alone does not describe the upper distribution. | Independent sorted-value percentile check; `outputs/summary.json` |
| Remove exact duplicates and exclude conflicting IDs | Exact copies double-count a mobilisation. Conflicting rows cannot be resolved by choosing an arbitrary version. | Row reconciliation and `outputs/conflicting_ids.csv` |
| Keep unknown geography and valid long durations | Missing geography does not invalidate a coherent total. An extreme time can be a real observation. | Unknown group, timestamp checks and positive-only P90 sensitivity |
| Do not impute the target | Filling times with an average would introduce unobserved durations and alter the distribution. | Eligibility rules in `scripts/analysis.py` |
| Examine persistent monthly differences | The three-month and 100-record thresholds are exploratory choices. | Sensitivity to 3/6 months and 50/100/200 records in `outputs/review_sensitivity.csv` |
| Use the same complete-month review window | The main candidate list previously included incomplete December 2024 while sensitivity excluded it. Both now end in November 2024. | `outputs/review_candidates.csv` and `outputs/review_sensitivity.csv` |

## AI use and verification

OpenAI Codex supported the analysis code, source identification, initial analytical
proposals, and drafting and revision of the written and presentation content.
The students reviewed the methods and interpretations. The use of AI does not
replace responsibility for the submitted claims.

The London case was selected by Matías. The period, P90 and persistence rule were
initially proposed with AI assistance. Clemente reviewed their meaning and
limitations through a step-by-step discussion, including questions on the unit
of observation, duplicates, timestamp validation, missingness, outliers,
percentiles, correlation and the scope of the conclusions. On 27 September 2026,
Clemente confirmed that Matías had reviewed the completed work, in response to a
question about acceptance of the period, KPI and review rule.

The approach excludes arbitrary selection of conflicting records, automatic
target imputation, deletion of valid long times solely because they are extreme,
and causal interpretation of descriptive correlations. Relevant prompt and output
excerpts appear in [AI interactions](docs/AI_INTERACTIONS.md).

Technical checks include source hashes, data types and missingness, unique IDs,
time consistency, row-count reconciliation, group totals and an independent P90
calculation. On 27 September 2026, the original files matched the recorded hashes and the
notebook executed from start to finish with zero error outputs. The main counts,
median and P90 matched the previous version. Execution results are recorded in
`outputs/validation.json`.
These checks establish internal consistency rather than independent verification
of every operational event.

## Individual contributions

| Member | Contribution | Evidence |
|---|---|---|
| Matías Muñoz Hoffmann | Proposed the fire-service topic, selected London, provided the course instructions, created the private repository and reviewed the project. | Recorded project interactions; Git history; review confirmed by Clemente on 27 September 2026 |
| Clemente Ibarra | Reviewed the data preparation, KPI and each EDA interpretation through questions and answers; identified limits of causal claims; requested presentation and document revisions and repository organisation. | Study and review discussion on 23 and 27 September 2026; this repository revision |

## Instructor feedback

The supplied course announcement defines the C1 scope. Matías reported that the
London case was permitted. No additional project-specific instructor feedback
has been supplied for this record as of 27 September 2026.
