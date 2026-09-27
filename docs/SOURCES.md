# Sources and evidence boundaries

1. London Fire Brigade Mobilisation Records, official catalogue:
   https://data.london.gov.uk/dataset/london-fire-brigade-mobilisation-records-24r65
   Raw CSV and metadata links, retrieval timestamps and hashes are in
   `data/source_manifest.json`. The CSV is the numerical source of this analysis.
2. LFB official confirmation of open-data publication:
   https://www.london-fire.gov.uk/about-us/transparency/request-information-from-us/
3. LFB FOI 8420.1, response dated 5 February 2024:
   https://www.london-fire.gov.uk/media/8863/foia84201-response-times-of-fire-brigades-and-data-collation-response.pdf
   Defines attendance as mobilisation to arrival and documents counting exclusions
   in published performance, including durations greater than 20 minutes. This
   supports a selection caveat; it does not independently verify all CSV filters.
4. Course calendar supplied locally:
   Calendarization_2026_Third_Term_Business_Intelligence_IIB423T.docx, sections 6-8.
5. Professor announcement supplied as an image:
   presentation 29 September; project/KPI, GitHub, download, exploration, cleaning,
   full EDA (histograms, densities, correlations) and upload.

The dictionary predates geography columns in this CSV. GMT is its documented
timestamp basis; we preserve that basis and label dispatch hour explicitly. No
independent validation against an operational event log has been performed.
