# Relevant AI interactions

## Final report description

Tool used: OpenAI Codex (technical and coding assistance).

Scope of use: The tool was used as support to explore the technical feasibility
of the fire department dataset, assist with code syntax for data quality tests,
and structure the initial draft of the C1 deliverables according to the rubric.

The team adopted the London case, 2023-2024 scope, P90 and median, no artificial
target imputation, no arbitrary removal of valid long times, and no post-dispatch
predictors for future models. This describes adopted criteria, not unaided code
authorship. The excerpts below preserve how suggestions and implementation arose.
Technical assistance included generating code, figures and initial drafts.

Verification evidence: `case_tables/row_flow.csv` reconciles the row counts;
`case_tables/audit.json` records identifier, timestamp and independent P90 checks;
`case_tables/summary.json` records the resulting 384,627 rows and P90 of 9.20 min.
The confirmed human reviews are documented in `TEAM_CONFIRMATION.md`.

Selected verbatim excerpts from the project conversation, in chronological order.
This is not a full transcript. No credentials or authentication codes are included.
Spanish is retained to preserve the original wording. Assistant proposals are not
automatically student decisions. Technical implementation is attributed to Codex.

## 1. Dataset search

User:
> necesito que busques un dataset en la web respecto a bomberos que sea viable y utilizable con el proyecto, si tienes alguna duda o consulta hazmela saber

Assistant:
> Mi recomendación es London Fire Brigade Mobilisation Records.

Assistant:
> Como KPI principal propuesto, usaría el percentil 90 del tiempo entre movilización y llegada por zona y mes, acompañado del volumen y la mediana.

User:
> si nos sirve trabajar con londres

Outcome: London was selected by the user. The KPI remained an assistant proposal.
Verification: official CSV and dictionary downloaded; source identity and checksums
recorded in data/source_manifest.json. Analytical eligibility was audited later.

## 2. Scope and implementation

User:
> dime los pasos a pasos para realizar lo correspondiente a la entrega C1. además te adjunto las instrucciones que nos dejó el profesor para tu conocimiento.

Assistant:
> El anuncio confirma siete requisitos: elegir y justificar el proyecto/KPI, crear una cuenta de GitHub, descargar los datos, explorarlos, limpiarlos, realizar un EDA completo y subir el proyecto.

User:
> realicemos todo lo que me indicas anteriormente en este chat, si tienes alguna duda hazmela saber de avanzar

Outcome: the user authorised implementation. Codex wrote the scripts, notebook,
documentation and slides. This authorisation is not evidence of human verification.

## 3. Team and case admission

User responses to clarification:
> Matias Muñoz Hoffmann

> aún no existe, pero ambos tenemos cuenta

> si se puede usar el caso de londres, y no hay una rubrica aún

Outcome: team identity, existing GitHub accounts and reported case permission
were documented. No additional scoring rubric was supplied.

## 4. Data quality changed the interpretation

Assistant:
> La auditoría encontró dos límites importantes: falta el 31 de diciembre de 2024 y el tiempo máximo publicado es exactamente 20 minutos.

Assistant:
> No voy a presentar estos datos como dos años completos ni asumir que representan toda la cola de demoras; comprobaré esos puntos y los dejaré visibles en las conclusiones.

Outcome: partial coverage and source selection were disclosed in the notebook,
case brief and presentation. No missing day was interpreted as zero emergencies.
Verification: daily coverage table, observed maxima and LFB FOI 8420.1. The FOI
describes performance counting exclusions; exact CSV filters remain unverified.

## 5. Publication choices

User:
> matiasudd, el repositorio es privado

User, regarding collaborator invitations:
> agreguemoslos despues al repositorio

Outcome: private repository created; invitations deferred at the user's request.
Verification: remote API confirmed private visibility and matching commit SHA.

## 6. Learning and compliance review

User:
> necesito que me digas los pasos que seguiste y en que parte se hacían para lograr lo que hiciste anteriormente, ya que mañana tengo un workshop y debo hacer todo lo anterior de manera individual

User:
> los archivos del certamen 1 que me adjuntaste, cumple con lo que solicita en la pauta y las instrucciones?

Assistant:
> Cubren los siete puntos del anuncio, pero todavía no están completamente cerrados para la entrega.

User:
> termina de realizar los pendientes que quedan y luego adjuntame los entregables y explicame el trabajo que realizaste

Outcome: documentation closeout requested. Human review, actual individual
contributions, feedback and evaluator access require accurate team information.
No acceptance or human verification is inferred merely from requesting completion.

## Suggestions not adopted

Codex did not deduplicate by incident ID, automatically impute missing attendance
times, remove valid long durations solely because they were extreme, or propose
realised travel/arrival information as dispatch-time predictors. These are
implementation decisions by the assistant; students must explain and validate
them before taking ownership of the submission.

## Verification trail

- analysis/analysis.py: actual transformations and assertions.
- data/case_tables/audit.json and row_flow.csv: exclusions and reconciliations.
- data/case_tables/summary.json: calculated KPI values.
- data/case_tables/review_sensitivity.csv: sensitivity calculations.
- data/SOURCES.md: external evidence and interpretation limits.
- data/TEAM_CONFIRMATION.md: confirmed human reviews.
