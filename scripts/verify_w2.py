"""Verify the executed W2 deliverable and extract its four figures."""
from pathlib import Path
import base64
import json
import re
import nbformat
import pandas as pd

root = Path(__file__).resolve().parents[1]
notebook = nbformat.read(root / "notebooks/W2_project.ipynb", as_version=4)
code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
assert code_cells and all(cell.execution_count is not None for cell in code_cells)
assert not any(output.output_type == "error" for cell in code_cells for output in cell.outputs)

figures = root / "outputs/w2/figures"
figures.mkdir(parents=True, exist_ok=True)
images = [output.data["image/png"] for cell in code_cells for output in cell.outputs
          if output.output_type in {"display_data", "execute_result"} and "image/png" in output.data]
assert len(images) >= 3
for index, data in enumerate(images, 1):
    (figures / f"figure_{index}.png").write_bytes(base64.b64decode(data))

summary_cell = next(cell.source for cell in notebook.cells
                    if cell.cell_type == "markdown" and "**Managerial summary" in cell.source)
summary = summary_cell.split("**Managerial summary (120–180 words).**", 1)[1].split("**AI-use disclosure.**", 1)[0]
word_count = len(re.findall(r"\b[\w–-]+\b", summary))
assert 120 <= word_count <= 180, word_count

checks = pd.read_csv(root / "outputs/w2/validation_checks.csv")
assert (checks.iloc[:5].affected_rows == 0).all()
flags = checks.set_index('check').affected_rows
assert flags['Missing turnout or travel component'] == 1816
assert flags['Zero recorded duration'] == 1
assert flags['Complete but inconsistent time components'] == 0
holdout = pd.read_csv(root / "outputs/w2/holdout_kpi.csv")
assert holdout.eligible_n.sum() == 384627
assert holdout.at_least_10m_n.sum() == 26367
assert len(holdout) == 3

w1_manifest = json.loads((root / 'docs/w2/w1_source_manifest.json').read_text(encoding='utf-8'))
c1_manifest = json.loads((root / 'GROUP_11_C1/data/source_manifest.json').read_text(encoding='utf-8'))
original_csv = 'mobilisations_2021_2024.csv'
assert all(w1_manifest[original_csv][key] == c1_manifest[original_csv][key]
           for key in ['url', 'retrieved_utc', 'bytes', 'sha256'])

assignment = pd.read_csv(root / 'outputs/w2/split_assignment.csv.gz',
                         dtype={'IncidentNumber': 'string'}, parse_dates=['DateAndTimeMobilised'])
assert len(assignment) == 384627
assert assignment.ResourceMobilisationId.notna().all()
assert assignment.ResourceMobilisationId.is_unique
assert set(assignment.split) == {'train', 'validation', 'test'}
assert assignment.groupby('IncidentNumber').split.nunique().max() == 1
periods = assignment.groupby('split').DateAndTimeMobilised.agg(['min', 'max'])
assert periods.loc['train', 'max'] < periods.loc['validation', 'min']
assert periods.loc['validation', 'max'] < periods.loc['test', 'min']

print(f"Verified: {len(code_cells)} executed code cells, {len(images)} figures, "
      f"{word_count}-word summary, 5 passing critical checks, 384,627 split rows, "
      "no incident overlap, missing-component/zero-duration flags, matching W1/C1 manifests.")
