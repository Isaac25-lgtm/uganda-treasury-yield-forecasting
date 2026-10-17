"""Compare a reproduced results/ directory against the committed results/tables.

    PYTHONPATH=src python3 -I scripts/compare_reproduction.py <reproduced_out_dir> [--write results/reproduction]

For each committed table: identical shape/columns/keys required; non-numeric cells must match exactly;
numeric cells are compared by max |difference| against an absolute tolerance. Wall-clock timing columns are
excluded because they are expected to differ between runs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TIMING_COLUMNS = {"fit_seconds"}
ABS_TOL = 1e-9          # "exact" up to floating-point formatting
ROUNDING_TOL = 1e-4     # tolerance used when a table was written rounded


def compare_tables(committed: pd.DataFrame, reproduced: pd.DataFrame) -> dict:
    out = {"committed_rows": len(committed), "reproduced_rows": len(reproduced),
           "same_columns": list(committed.columns) == list(reproduced.columns)}
    if not out["same_columns"] or len(committed) != len(reproduced):
        out.update(status="STRUCTURE_DIFFERS", max_abs_diff=np.nan, n_text_mismatch=np.nan)
        return out
    max_diff, text_mismatch, compared = 0.0, 0, []
    for c in committed.columns:
        if c in TIMING_COLUMNS:
            continue
        compared.append(c)
        a, b = committed[c], reproduced[c]
        numeric = all(pd.api.types.is_numeric_dtype(x) and not pd.api.types.is_bool_dtype(x) for x in (a, b))
        if numeric:
            both_nan = a.isna() & b.isna()
            if (a.isna() ^ b.isna()).any():
                text_mismatch += int((a.isna() ^ b.isna()).sum())
            d = (a - b).abs()[~both_nan]
            if len(d):
                max_diff = max(max_diff, float(d.max()))
        else:
            both_missing = a.isna() & b.isna()
            differ = (a.astype(object).where(a.notna(), "<NA>").astype(str)
                      != b.astype(object).where(b.notna(), "<NA>").astype(str))
            text_mismatch += int((differ & ~both_missing).sum())
    out.update(max_abs_diff=max_diff, n_text_mismatch=text_mismatch,
               excluded_columns=";".join(sorted(TIMING_COLUMNS & set(committed.columns))))
    if text_mismatch:
        out["status"] = "VALUES_DIFFER"
    elif max_diff <= ABS_TOL:
        out["status"] = "EXACT"
    elif max_diff <= ROUNDING_TOL:
        out["status"] = "WITHIN_ROUNDING_TOLERANCE"
    else:
        out["status"] = "VALUES_DIFFER"
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("reproduced", type=Path)
    ap.add_argument("--committed", type=Path, default=ROOT / "results/tables")
    ap.add_argument("--write", type=Path, default=None, help="directory for reproduction_matrix.csv")
    a = ap.parse_args(argv)
    rows = []
    for f in sorted(a.committed.glob("*.csv")):
        r = a.reproduced / "tables" / f.name
        if not r.exists():
            rows.append({"table": f.name, "status": "MISSING_IN_REPRODUCTION"})
            continue
        rows.append({"table": f.name, **compare_tables(pd.read_csv(f), pd.read_csv(r))})
    m = pd.DataFrame(rows)
    print(m.to_string(index=False))
    if a.write:
        a.write.mkdir(parents=True, exist_ok=True)
        m.to_csv(a.write / "reproduction_matrix.csv", index=False)
    return 0 if m["status"].isin(["EXACT", "WITHIN_ROUNDING_TOLERANCE"]).all() else 1


if __name__ == "__main__":
    sys.exit(main())
