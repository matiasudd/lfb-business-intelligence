"""Recreate the uncleaned 2023-2024 case input from the preserved source."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/mobilisations_2021_2024.csv.gz"
TARGET = ROOT / "data/reduced/mobilisations_2023_2024_input.csv.gz"
MANIFEST = ROOT / "data/reduced/reduced_input_manifest.json"


def main() -> None:
    expected = json.loads(MANIFEST.read_text(encoding="utf-8"))
    count = 0
    with gzip.open(SOURCE, "rt", encoding="utf-8-sig", newline="") as src, gzip.open(
        TARGET, "wt", encoding="utf-8", newline="", compresslevel=6
    ) as dst:
        rows = csv.DictReader(src)
        writer = csv.DictWriter(dst, fieldnames=rows.fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            if row["DateAndTimeMobilised"][6:10] in {"2023", "2024"}:
                writer.writerow(row)
                count += 1
    assert count == expected["rows"]
    digest = hashlib.sha256()
    with gzip.open(TARGET, "rb") as data:
        for chunk in iter(lambda: data.read(1 << 20), b""):
            digest.update(chunk)
    assert digest.hexdigest() == expected["uncompressed_sha256"]
    print(f"Verified uncleaned reduced case: {count:,} rows")


if __name__ == "__main__":
    main()
