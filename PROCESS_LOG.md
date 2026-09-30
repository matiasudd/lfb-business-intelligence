# Process log and AI disclosure

## Team and status

Matias Muñoz Hoffmann and Clemente Ibarra. Human review of the generated analytical
work and each member's actual contribution remain to be recorded. Do not submit
this as evidence that both students have already verified the work.

## Consequential user instructions (conversation record)

1. Find a public fire-service dataset suitable for C1 and C2.
2. The team accepted London after reviewing the proposed mobilisation dataset.
3. The user provided the professor's announcement: define project/KPI, GitHub,
   download, explore, clean, full EDA and upload, for 29 September.
4. The user authorised completing those steps, asking for clarification when needed.
5. Matias confirmed both members have GitHub accounts, no repository yet, London is
   permitted and no additional rubric is available.

These are summaries, not purported verbatim quotations. Selected original prompts
and relevant responses are included in [AI_INTERACTIONS.md](docs/AI_INTERACTIONS.md).
That file preserves the language of the conversation and distinguishes user
choices from assistant proposals. It is an excerpt, not a complete transcript.

## AI contribution and consequential suggestions

Codex sourced official LFB records, implemented the download and checksum manifest,
authored the audit, cleaning, notebook and supporting documentation, and proposed
the P90 metric and review rule. Generated findings must be checked against executed
outputs. No student-authored code or independent review is implied.

Accepted by user: London geography and use of LFB mobilisation data.
Proposed by AI, pending student acceptance: 2023-2024 window, all-mobilisation
population, P90 KPI, review heuristic and C2 prediction design.
Rejected during preparation: interpreting all mobilisation rows as distinct
emergencies; imputing the target automatically; deleting long times only because
they are extreme; using post-arrival variables as dispatch-time predictors.

## Verification

- Downloaded original CSV and dictionary from London Datastore; recorded SHA256.
- Compared dictionary fields and CSV schema; geography fields are in the CSV but
  absent from the older dictionary and are treated as source labels.
- Measured actual missingness, duplicate patterns, timestamp consistency and coverage.
- Reconciled cleaning stages, monthly and geographic totals.
- Independently recomputed the main P90 from sorted observations.
- Execution and presentation verification status is recorded in outputs/validation.json.
- Notebook executed top-to-bottom with zero error outputs. Nine rendered figures
  and HTML summary/takeaways were inspected; all nine HTML images loaded. Thirteen
  final slide renders were inspected; five charts retain editable workbook data.
- Found 31 December 2024 absent and a 20-minute ceiling. Consulted LFB FOI 8420.1;
  narrowed conclusions to the published population and disclosed uncertain CSV filters.
- Matias authenticated GitHub CLI as matiasudd and selected a private repository.
  He asked to defer invitations to Clemente and the instructor.

## Human contribution record at initial preparation (superseded below)

| Member | Actual work performed | Evidence/commit | Verification and date |
|---|---|---|---|
| Matias Muñoz Hoffmann | Proposed the fire-service topic; selected London; supplied professor instructions; confirmed case permission; selected private GitHub publication and completed account authentication; requested learning and compliance review | Conversation excerpts in docs/AI_INTERACTIONS.md | Independent technical review and acceptance of analytical choices not yet confirmed |
| Clemente Ibarra | Identified as teammate by Matias; no direct contribution evidence supplied in this conversation | Not yet supplied | Not yet confirmed |

## Feedback record

No C1 feedback has been supplied in this conversation. This does not establish
whether the team received feedback elsewhere. For each comment record the
source, change requested, accepted/adapted/rejected decision, reason and commit.
This record must continue into C2.

## Confirmed C1 update - 29 September 2026

The current submission is in GROUP_11_C1/. Earlier pending-review statements
above describe the initial preparation, not the current confirmed status.
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
