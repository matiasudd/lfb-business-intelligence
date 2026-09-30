# London Fire Brigade C1 - Group 11

We are Matias Munoz Hoffmann and Clemente Ibarra. We investigate vehicle
mobilisation-to-arrival times in published London Fire Brigade records for
2023-2024. Our unit is one vehicle mobilisation, not one emergency.

## Our current submission

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

We used Codex for technical assistance, analytical code, figures and drafts.
We adopted and reviewed our criteria; we do not claim unaided code authorship.
Matias reviewed row flow/P90 and Clemente reviewed borough/hour comparisons
and limitations. We received no W1 instructor feedback.

We preserve the earlier `scripts/`, `notebooks/`, `outputs/`, `presentation/`
and `docs/` as preparation history, including the prior remote review.
Those are not our current delivery; we use `GROUP_11_C1/` for the final files.
Contains London Fire Brigade / Greater London Authority information; source
attribution and interpretation limits are recorded in our submission.

We maintain this repository privately. Collaborator and instructor invitations
remain pending. Publishing here does not constitute a Canvas submission.
We still need to package `GROUP_11_C1/` as ZIP or RAR and upload it to Canvas.
