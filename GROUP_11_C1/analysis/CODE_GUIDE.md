# How to read and run the C1 analysis

The code implements the methods described in the final report. It was prepared
with Codex assistance; simpler code is not evidence of unaided student authorship.

## Main steps in analysis.py

1. Read the compressed original and verify its SHA256 against the manifest.
2. Save the missing-value profile and the publisher's data dictionary.
3. Trim whitespace and convert date and numeric fields to usable types.
4. Remove exact duplicate rows, then identify conflicting mobilisation IDs.
5. Select dispatch dates from 1 January 2023 to before 1 January 2025.
6. Exclude invalid IDs, negative/missing totals and inconsistent arrival times.
7. Keep missing borough as Unknown and retain valid zero and long durations.
8. Convert seconds to minutes and calculate count, median, P90 and mean.
9. Repeat these metrics by borough, hour, month, station and year.
10. Check the P90 independently and reconcile grouped counts with the total.
11. Evaluate consecutive-month review rules, including sensitivity checks.
12. Export tables and the distribution, density, time and correlation charts.

`metrics` calculates overall metrics. `grouped` calculates the same metrics for
each group. `longest_run` counts consecutive qualifying months using a plain loop.
`run` performs the full workflow and returns the data, tables and audit results.

Do not remove the hash, eligibility or timestamp checks merely to shorten the
script: they explain why the analysis is reproducible and trustworthy.

## Run from the GROUP_11_C1 folder

```powershell
python analysis/analysis.py
```

The notebook calls this same script rather than maintaining a second cleaning
implementation. Run its cells in order to refresh all displayed results.

## Explain in the defense

- One row is a vehicle mobilisation, not an incident.
- P90 is calculated with `quantile(0.9)` on eligible times in minutes.
- The 20-minute observed maximum belongs to the source, not a cleaning cutoff.
- Correlations use complete and consistent components only.
- C1 is descriptive: the C2 model and dashboard remain proposed work.
