"""Parse BoU Treasury-bill Invitation to Tender (ITT) documents.

The ITT is published before the auction and is the only auction-specific document
whose content is *pre-bid*: issue number, auction date, bid deadline, per-tenor
offered amounts and the printed issue date of the notice. Nothing in it depends on
bids received.
"""

from __future__ import annotations

import re
from datetime import date, datetime

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], start=1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
MONTHS["sept"] = 9

_DATE_WORDS = re.compile(
    r"(?:(?:mon|tues|wednes|thurs|fri|satur|sun)day,?\s+)?"
    r"(?:(?P<d1>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<m1>[A-Za-z]{3,9})\.?,?\s+(?P<y1>\d{4})"
    r"|(?P<m2>[A-Za-z]{3,9})\.?[\s,]+(?P<d2>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<y2>\d{4}))",
    re.I,
)


def parse_date_words(s: str) -> date | None:
    m = _DATE_WORDS.search(s)
    if not m:
        return None
    d, mon, y = (m["d1"], m["m1"], m["y1"]) if m["d1"] else (m["d2"], m["m2"], m["y2"])
    mi = MONTHS.get(mon.lower()) or MONTHS.get(mon.lower()[:3])
    if not mi:
        return None
    try:
        return date(int(y), mi, int(d))
    except ValueError:
        return None


def _amount(s: str) -> float | None:
    m = re.search(r"([\d,]{5,})(?:\.\d+)?\s*/?=?", s)
    return float(m.group(1).replace(",", "")) if m else None


def parse_itt(text: str) -> dict:
    """Return pre-bid fields. Missing fields are None (never zero-filled)."""
    out: dict = {"issue_no": None, "auction_date": None, "notice_date": None,
                 "offer_total": None, "offer_91": None, "offer_182": None, "offer_364": None,
                 "bid_deadline": None}
    m = re.search(r"ISSUE\s+NO\.?\s*:?\s*(\d{3,5})", text, re.I)
    if m:
        out["issue_no"] = int(m.group(1))
    for line in text.splitlines():
        u = line.upper()
        if re.search(r"OFFER(ED|ING) AMOUNT", u) and out["offer_total"] is None:
            out["offer_total"] = _amount(line.split(":", 1)[-1])
        tm = re.search(r"\b(91|182|364)\s*[- ]?DAYS?\b", u)
        if tm and ("ISIN" in u or re.search(r"[\d,]{9,}\s*/?=", line)) and "MATURITY" not in u:
            key = f"offer_{tm.group(1)}"
            amt = _amount(line[tm.end():])
            if out[key] is None and amt is not None and amt > 1e6:
                out[key] = amt
        if "AUCTION DATE" in u and out["auction_date"] is None:
            out["auction_date"] = parse_date_words(line)
    m = re.search(r"by\s+(\d{1,2})[.:](\d{2})\s*([ap]\.?m)", text, re.I)
    if m:
        out["bid_deadline"] = f"{int(m.group(1)):02d}:{m.group(2)}{m.group(3).replace('.', '').lower()}"
    # Notice date: the dated line printed just above "MANAGEMENT" at the foot of the notice.
    # Fallback: the last line that consists only of a (weekday) date.
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i, ln in enumerate(lines):
        if ln.upper() == "MANAGEMENT" and i > 0:
            out["notice_date"] = parse_date_words(lines[i - 1])
            break
    if out["notice_date"] is None:
        for ln in reversed(lines):
            if len(ln) < 40 and _DATE_WORDS.fullmatch(ln.rstrip(". ")):
                out["notice_date"] = parse_date_words(ln)
                break
    return out


def as_iso(d: date | datetime | None) -> str | None:
    return d.isoformat() if d else None
