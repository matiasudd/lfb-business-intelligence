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

## Confirmed C1 update - 29 September 2026

The current submission is in GROUP_11_C1/. We retain the 27 September review
evidence above and add the following confirmation from the current conversation.
Matias confirmed on behalf of both members that he reviewed row flow/P90,
Clemente reviewed borough/hour comparisons and limitations, and both accepted
the reflection text. No separate direct message from Clemente is inferred.
The team adopted the scope and criteria presented in the final report.
Matias subsequently confirmed that the instructor provided no W1 feedback.

Codex assistance included technical feasibility, quality-test syntax,
analytical code, figures and initial drafts. The final package preserves the
team's report description and the supporting interaction/verification record.
Simplifying code does not imply unaided student authorship.

The current notebook has 17 executed code cells without saved errors.
The current report includes the Instructor feedback and response text.
Original/reduced inputs and processed outputs are included; the processed
CSV is stored losslessly as gzip for GitHub. The earlier 13-slide deck and
older notebook remain preparation history, not final delivery files.
## Instructor feedback record at 27 September 2026

The supplied course announcement defines the C1 scope. Matías reported that the
London case was permitted. No additional project-specific instructor feedback
has been supplied for this record as of 27 September 2026.

## W2 rubric review on 27 October 2026

The team clarified the C1 instructor's feedback: using a moving P90-based
comparison reference would change the threshold as times improve. C1's P90 of
552 seconds informed the team's fixed, round 600-second threshold. W2 measures
the percentage of eligible mobilisations at or above that threshold and keeps
P90 as a supporting measure. The threshold is exploratory, not an official
service target.

At the team's request, Codex applied the rubric review to the W2 builder,
notebook and README. Revisions add numerical interpretations of all four
figures, the sample and retrospective holdout; explicit expected data types;
and visible counts for missing duration components and the zero-duration
boundary observation. Hillingdon and 11:00 GMT are explicitly connected to
the revised C1 conclusions. No source or KPI eligibility rule was changed.

The retained W1 source manifest was copied to
`docs/w2/w1_source_manifest.json`. Its original CSV URL, retrieval timestamp,
size and SHA256 match the preserved C1 source manifest. W2 checks this agreement
programmatically. This supports continuity of the retained materials without
asserting which files were submitted on the course platform.

The earlier C1 artifacts remain unchanged. The previous W2 tag is preserved;
the reviewed W2 version is identified by `w2-2026-10-27-reviewed`. Codex support
for these revisions is covered by the W2 AI-use disclosure. No additional
individual student review is inferred from the automated checks.

Reproduction was checked from a fresh clone of the existing repository with a
new local Python 3.12 environment installed from `requirements.txt`. The builder
completed, Jupyter nbconvert executed all 13 code cells without error outputs,
and `scripts/verify_w2.py` passed. It verified four figures, a 171-word management
summary, five passing critical quality checks, 384,627 partitioned rows, no
incident overlap, the missing-component and zero-duration counts, and matching
W1/C1 source manifests. All four regenerated figures were visually inspected.
The KPI remained 26,367 / 384,627, or 6.855213%.
