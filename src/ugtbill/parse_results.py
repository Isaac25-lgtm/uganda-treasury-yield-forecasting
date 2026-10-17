"""Parse BoU "RESULTS OF TREASURY BILLS AUCTION" press releases (text PDFs and DOCX).

Each printed numeric cell is stored twice: the raw printed string and a parsed float.
A string that does not parse as a plain decimal (e.g. the documented ``13..001`` typo)
yields ``NaN`` with ``parse_flag='unparseable'`` — repairs happen only in a declared
sensitivity (:func:`repair_double_dot`), never here.

Documents whose results table is an image or vector-glyph drawing (no text layer) are
reported as ``status='no_text_layer'`` and never guessed.
"""

from __future__ import annotations

import re
import subprocess
from datetime import date, datetime
from pathlib import Path

from .parse_itt import MONTHS, parse_date_words
from .pdftext import extract_text

TENORS = (91, 182, 364)
LABELS = {
    "maturity_date": r"MATURITY\s+DATE",
    "cutoff_price": r"CUT[\s-]*OFF\s+PRICE",
    "disc_rate": r"ANN(?:UAL|\.)?\s*DISC(?:OUNT)?\.?\s+RATE",
    "mmy": r"MONEY\s+(?:MKT|MARKET)\s+YIELD",
    "eff_yield": r"EFFECTIVE\s+YIELD",
    "offered": r"OFFERED",
    "tendered": r"TENDERED",
    "accepted": r"ACCEPTED\s+BIDS",
    "bid_cover": r"BID\s+TO\s+COVER(?:\s+RATIO)?",
}
NUMERIC = ("cutoff_price", "disc_rate", "mmy", "eff_yield", "offered", "tendered", "accepted", "bid_cover")
_TOKEN = re.compile(r"\d{1,2}-[A-Za-z]{3}-\d{2,4}|\d[\d,]*(?:\.+\d+)?|N/?A\b|-(?=\s|$)")
_PLAIN = re.compile(r"^\d[\d,]*(?:\.\d+)?$")


def _dash_date(s: str) -> date | None:
    m = re.fullmatch(r"(\d{1,2})[-\s]+([A-Za-z]{3,9})[-\s,]+(\d{2,4})", s.strip())
    if not m:
        return None
    y = int(m.group(3))
    y = y + 2000 if y < 100 else y
    mi = MONTHS.get(m.group(2).lower()) or MONTHS.get(m.group(2).lower()[:3])
    try:
        return date(y, mi, int(m.group(1))) if mi else None
    except ValueError:
        return None


def to_float(s: str | None) -> float:
    if s is None or not _PLAIN.match(s.strip()):
        return float("nan")
    return float(s.replace(",", ""))


def _docx_rows(text: str) -> list[str]:
    """DOCX tables come out one cell per line; rebuild 'LABEL v1 v2 v3' rows."""
    cells = [c.strip(" |\t") for c in re.split(r"\n|\|", text)]
    cells = [c for c in cells if c]
    rows, i = [], 0
    while i < len(cells):
        if any(re.match(p, cells[i], re.I) for p in LABELS.values()) or cells[i].upper().startswith("MATURITIES"):
            rows.append(" ".join(cells[i:i + 4]))
            i += 4
        else:
            rows.append(cells[i])
            i += 1
    return rows


def parse_results_text(text: str, is_docx: bool = False) -> dict:
    lines = _docx_rows(text) if is_docx else text.splitlines()
    out: dict = {"auction_no": None, "auction_date": None, "settlement_date": None,
                 "printed_release_date": None, "status": "ok", "tenors": {}}
    m = re.search(r"AUCTION\s+NO\.?\s*:?\s*(\d{3,5})", text, re.I)
    out["auction_no"] = int(m.group(1)) if m else None
    m = re.search(r"(?:AUCTION\s+DATE\s*:?|HELD\s+ON\s*:?)\s*(?:[A-Za-z]+\.?,?\s+)?(\d{1,2}[-\s]+[A-Za-z]+[-\s,]+\d{2,4})", text, re.I)
    out["auction_date"] = _dash_date(m.group(1)) if m else None
    m = re.search(r"(?:SETTLEMENT\s+DATE\s*:?|ISSUE\s+DATE\s*:?|SETTLED(?:\s+ON)?)\s*(?:[A-Za-z]+\.?,?\s+)?(\d{1,2}[-\s]+[A-Za-z]+[-\s,]+\d{2,4})", text, re.I)
    out["settlement_date"] = _dash_date(m.group(1)) if m else None
    tenor_cols = None
    raw: dict[str, list[str]] = {}
    for ln in lines:
        u = ln.upper().strip()
        if u.startswith("MATURITIES"):
            tenor_cols = [int(x) for x in re.findall(r"\b(91|182|364|28|63)\b", u)]
            continue
        for key, pat in LABELS.items():
            if key in raw:
                continue
            if re.match(r"\s*" + pat, u):
                rest = re.sub(r"^\s*" + pat + r"\s*:?", "", u)
                toks = _TOKEN.findall(rest)
                if toks:
                    raw[key] = toks
                break
    # printed release date near "MANAGEMENT"
    flat = [ln.strip() for ln in lines if ln.strip()]
    for i, ln in enumerate(flat):
        if ln.upper() == "MANAGEMENT":
            for cand in (flat[i + 1] if i + 1 < len(flat) else "", flat[i - 1]):
                d = parse_date_words(cand) or _monthname_date(cand)
                if d:
                    out["printed_release_date"] = d
                    break
            break
    if not raw.get("cutoff_price") or not raw.get("mmy"):
        out["status"] = "no_text_layer"
        return out
    tenor_cols = tenor_cols or list(TENORS)
    for j, t in enumerate(tenor_cols):
        if t not in TENORS:
            continue
        rec = {}
        for key, toks in raw.items():
            s = toks[j] if j < len(toks) else None
            rec[key + "_raw"] = s
            if key == "maturity_date":
                rec[key] = _dash_date(s) if s else None
            else:
                rec[key] = to_float(s)
        core = [rec.get(k + "_raw") for k in ("cutoff_price", "mmy")]
        if any(c is not None and re.fullmatch(r"N/?A|-", c) for c in core):
            rec["parse_flag"] = "not_awarded"  # printed N/A: no bids accepted for this tenor
        elif all(rec.get(k + "_raw") is None or _PLAIN.match(rec[k + "_raw"]) for k in NUMERIC):
            rec["parse_flag"] = "ok"
        else:
            rec["parse_flag"] = "unparseable"
        out["tenors"][t] = rec
    if len(raw.get("cutoff_price", [])) != len(tenor_cols):
        out["status"] = "column_mismatch"
    return out


def _monthname_date(s: str) -> date | None:
    m = re.search(r"([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(\d{4})", s)
    if not m:
        return None
    mi = MONTHS.get(m.group(1).lower()) or MONTHS.get(m.group(1).lower()[:3])
    try:
        return date(int(m.group(3)), mi, int(m.group(2))) if mi else None
    except ValueError:
        return None


def pdf_creation_date(path: Path) -> datetime | None:
    """PDF CreationDate metadata (producer-side timestamp; evidence, not proof, of release time)."""
    if Path(path).suffix.lower() != ".pdf":
        return None
    p = subprocess.run(["pdfinfo", "-isodates", str(path)], capture_output=True, text=True)
    m = re.search(r"CreationDate:\s+(\S+)", p.stdout)
    if not m:
        return None
    try:
        return datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_results_file(path: Path) -> dict:
    path = Path(path)
    text = extract_text(path)
    if "TREASURY BILL" not in text.upper():
        return {"status": "not_tbill_results", "tenors": {}}
    out = parse_results_text(text, is_docx=path.suffix.lower() == ".docx")
    out["pdf_creation_date"] = pdf_creation_date(path)
    return out


# ---- identity and declared repairs -------------------------------------------------

def mmy_from_price(price: float, days: int, basis: int = 365) -> float:
    """Money-market (simple) yield in % implied by a discount price per 100."""
    return (100.0 / price - 1.0) * basis / days * 100.0


def price_from_mmy(mmy: float, days: int, basis: int = 365) -> float:
    return 100.0 / (1.0 + mmy / 100.0 * days / basis)


def repair_double_dot(raw: str | None) -> float:
    """Declared sensitivity repair for printed strings like '13..001' -> 13.001."""
    if raw is None:
        return float("nan")
    fixed = re.sub(r"\.{2,}", ".", raw)
    return to_float(fixed)
