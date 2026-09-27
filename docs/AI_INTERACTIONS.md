# Relevant AI interactions

Selected excerpts from the preparation discussions. Spanish quotations retain
the original language. Explanations of outcomes and checks are summaries.

## Source and KPI

User:
> necesito que busques un dataset en la web respecto a bomberos que sea viable y utilizable con el proyecto, si tienes alguna duda o consulta hazmela saber

Assistant:
> Mi recomendación es London Fire Brigade Mobilisation Records.

Assistant:
> Como KPI principal propuesto, usaría el percentil 90 del tiempo entre movilización y llegada por zona y mes, acompañado del volumen y la mediana.

User:
> si nos sirve trabajar con londres

The team selected London. The analysis checks source identity with file hashes
and tests KPI eligibility separately. Evidence: `data/source_manifest.json`,
`docs/KPI.md`, `outputs/audit.json`.

## Implementation

User:
> realicemos todo lo que me indicas anteriormente en este chat, si tienes alguna duda hazmela saber de avanzar

Codex implemented the download, audit, cleaning and analytical notebook, and
prepared supporting text and slides. The code checks row counts, timestamp
consistency and the percentile calculation. Evidence: `scripts/analysis.py` and
`outputs/validation.json`.

## Source limitations

Assistant:
> La auditoría encontró dos límites importantes: falta el 31 de diciembre de 2024 y el tiempo máximo publicado es exactamente 20 minutos.

The conclusions were restricted to the published population. The absence of a
day was not treated as proof of zero real events. Evidence:
`outputs/daily_coverage.csv`, `outputs/summary.json`, `docs/SOURCES.md`.

## Student interpretation

Clemente, on timestamp validation:
> no deberia, ya que corresponde a 5 minutos y en realidad le tomo 8

Clemente, on internal consistency:
> no basta, ya que no sabesmos la vericidad de los datos. podrian haber datos malos pero que si cumplen con los requisitos para el analisis.

Clemente, on the histogram display limit:
> efectivamente sigue participando, aunque quede fuera del histograma, eso es solo una decision visual

The discussion corrected confusion between correlation and a share of total time,
and between three months and three consecutive months. It also distinguished
vehicle mobilisations from incidents and descriptive findings from causal claims.

## Presentation and revision

Clemente:
> por esto tambien quiero que utilices un lenguaje formal (universitario), pero que a la vez no sea muy complejo para nosotros, intenta utilizar palabras basicas y que suene fluido el discurso

AI drafted English slides and an oral practice script. The submitted presentation
retains the project evidence and concise source notes. The practice script is
separate from the submitted repository.

Clemente, confirming Matías's review on 27 September 2026:
> si el revisó todo lo que se ha hecho

The final review aligns the candidate and sensitivity periods and removes
superseded presentations and administrative drafts. `PROCESS_LOG.md` records
the resulting decisions and contributions.
