# Case brief

## Business question

Which London boroughs and dispatch hours exhibit persistently long vehicle
mobilisation-to-arrival times and should be prioritised for operational review?

## Decision owner and action

Hypothetical audience: an LFB operations planning analyst. The intended action is
to shortlist areas for investigation using delay records, incident context and
resource availability. We do not recommend station closures, new sites, staffing
levels or dispatch rules from this dataset alone.

## Why this case

The public source provides timestamped records, a continuous outcome and operational
categories. That supports C1 data-quality assessment and descriptive EDA, and a
later comparison of predictive models in C2. London was accepted as the project's
geography by the team, which reports that the case is permitted for the course.

## Scope and data flow

LFB publication -> original CSV and dictionary -> SHA256 manifest -> raw profile ->
explicit cleaning and eligibility flags -> validated analysis table -> KPI and EDA ->
operational-review candidates -> human review and communication.

Selected period: dispatch dates from 2023-01-01 inclusive to 2025-01-01 exclusive,
using the dictionary's GMT time basis. The requested two-year window has a coverage
gap: 31 December 2024 is absent. December and annual 2024 totals are partial.
We do not insert zero events for that absent day. Presence of records on other
days is not proof that every real mobilisation was published.

All source rows are labelled Initial and observed attendance is at most 1,200
seconds. A 2024 LFB methodology response documents exclusions over 20 minutes in
published performance calculations. That is consistent with selection in this
extract, but does not prove the exact extraction rules used for this CSV.
Our conclusions concern published records, not the unobserved extreme tail.

## C2 extension

Possible outcome: mobilisation-to-arrival seconds. Use dispatch-time available
calendar, origin and destination variables, subject to verifying availability and
coverage. Evaluate a simple baseline and candidate models on later dates; group or
separate incidents at split boundaries to avoid repeated-incident contamination.
Do not use arrival timestamps, realised travel/turnout times, recorded delay
reasons, or eventual arrival rank as predictors. Audit borough and tail errors.
Keep C1 feedback as incorporated, adapted or rejected with justification.
