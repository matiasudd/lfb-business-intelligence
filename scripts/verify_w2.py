"""Verify the executed W2 deliverable and extract its four figures."""
from pathlib import Path
import base64
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
holdout = pd.read_csv(root / "outputs/w2/holdout_kpi.csv")
assert holdout.eligible_n.sum() == 384627
assert holdout.over_10m_n.sum() == 26172
assert len(holdout) == 3

print(f"Verified: {len(code_cells)} executed code cells, {len(images)} figures, "
      f"{word_count}-word summary, 5 passing critical checks, 384,627 split rows.")
