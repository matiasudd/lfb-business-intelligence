# KPI specification

| Field | Definition |
|---|---|
| Name | P90 mobilisation-to-arrival time |
| Decision | Prioritise boroughs for operational investigation |
| Observation | One published pumping-appliance mobilisation |
| Time window | Dispatch timestamp in 2023-2024, GMT per source dictionary |
| Value | AttendanceTimeSeconds / 60, minutes |
| Aggregation | 90th percentile, linear interpolation between ordered observations |
| Interpretation | Approximately 90% of eligible mobilisation durations fall at or below this value |
| Reporting | Monthly per borough; global, hourly and yearly context |
| Companion measures | Eligible n, distinct incidents, median, mean, missing/excluded share |
| Unknown geography | Included globally as Unknown; never silently assigned a borough |
| Data quality | Unique nonmissing mobilisation ID; valid incident ID, arrival and total duration; duration matches timestamps within 1 second |
| Target | No official target asserted; smaller values are desirable conditional on comparable case mix |

## Proposed review heuristic

Flag a borough if its monthly P90 is above the global P90 for the same month,
with at least 100 eligible mobilisations in each month, for at least three
consecutive months. This is an academic prioritisation heuristic, not a statutory
threshold, significance test or policy endorsed by LFB. The minimum n stabilises
the descriptive calculation but is not a precision guarantee. Report sensitivity
to the arbitrary choices before operational use. `review_sensitivity.csv` varies
the minimum n (50/100/200) and persistence (3/6 months), excluding incomplete
December 2024. The primary shortlist is descriptive, not an implementation order.

No separate action is triggered solely by a high percentile: first check exclusions,
incident mix, deployment patterns and persistence. Use hour-of-dispatch profiles
to guide a review; no resource reassignment is justified here.

## Measurement boundaries

Attendance time is checked against arrival minus mobilisation. It excludes call
handling before mobilisation. It includes all eligible vehicle arrivals, not just
the first arrival at an incident. P90s are computed from rows, never by averaging
borough or monthly P90s. Missing components do not invalidate a coherent total;
component correlations use only complete, nonnegative, consistent component rows.

Zero durations and long durations remain if timestamp-consistent. Their counts
and positive-only P90 sensitivity are disclosed. Histogram display may stop at
P99, but the KPI and full-tail cumulative distribution retain all eligible rows.
The full tail here means the entire observed extract: no source duration exceeds
20 minutes, and all source rows are Initial. The unobserved tail cannot be inferred.
