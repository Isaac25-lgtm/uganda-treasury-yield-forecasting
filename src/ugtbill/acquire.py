"""Lawful acquisition of official Bank of Uganda (BoU) Treasury-bill auction documents.

Source: the public BoU website (https://www.bou.or.ug), whose "Auction information"
page is served by a Strapi CMS endpoint that lists every published auction document
(Invitation to Tender, Auction results) with its upload path.

Rules (AGENTS.md):
- raw files are written under ``data/raw/`` (git-ignored) and never edited;
- every file is identified by SHA-256 in a committed manifest;
- short timeouts, at most 3 attempts per resource, polite delay between requests;
- CMS ``createdAt`` timestamps are recorded but are NOT release timestamps:
  2023-2025 documents were bulk-migrated (createdAt 2025-12-31 / 2026-04-25).
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

BOU_API = "https://bou.or.ug/api"
CATALOG_URL = (
    BOU_API
    + "/financial-market-auction-information"
    + "?populate=auctionInformation.items.file.file.file"
    + "&populate=auctionInformation.items.file.fileWithMonth.file.file"
)
BOU_FILE_BASE = "https://bou.or.ug"

BOND_PAT = re.compile(r"bond|placement|switch|conversion|tap[- ]sale|banking act", re.I)
BILL_PAT = re.compile(r"t[- _]?bill|treasury[- _]bills?|bills[- _]results", re.I)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def flatten_catalog(catalog: dict) -> list[dict]:
    """Flatten the nested Strapi auction-information payload into one row per document."""
    rows: list[dict] = []
    for item in catalog["data"]["auctionInformation"]["items"]:
        category = item.get("category")
        for year_block in item.get("file") or []:
            groups = [(m.get("month"), m.get("file") or []) for m in (year_block.get("fileWithMonth") or [])]
            groups.append((None, year_block.get("file") or []))
            for month, files in groups:
                for entry in files:
                    f = entry.get("file") or {}
                    rows.append(
                        {
                            "category": category,
                            "year": str(year_block.get("year") or ""),
                            "month": month or "",
                            "title": (entry.get("title") or "").strip(),
                            "name": f.get("name") or "",
                            "url_path": f.get("url") or "",
                            "ext": f.get("ext") or "",
                            "size_kb": f.get("size"),
                            "cms_created_at": f.get("createdAt") or "",
                        }
                    )
    return rows


def is_tbill_document(row: dict) -> bool:
    """Title-based pre-filter; content parsing confirms the 91/182/364-day tenors later."""
    text = f"{row['title']} {row['name']}"
    if BOND_PAT.search(text):
        return False
    if row["category"] == "Invitation to tender":
        return bool(BILL_PAT.search(text))
    if row["category"] == "Auction results":
        # Many T-bill result files have generic titles ("Press-Release June");
        # bonds are excluded above, the parser later rejects anything without bill tenors.
        return True
    return False


def select_tbill_documents(rows: list[dict], first_year: int = 2023) -> list[dict]:
    out = []
    seen = set()
    for r in rows:
        if not r["url_path"] or not r["year"].isdigit() or int(r["year"]) < first_year:
            continue
        if r["category"] not in ("Auction results", "Invitation to tender"):
            continue
        if not is_tbill_document(r):
            continue
        if r["url_path"] in seen:  # identical upload listed twice
            continue
        seen.add(r["url_path"])
        out.append(r)
    return out


def _curl(url: str, dest: Path, timeout: int) -> tuple[int, str]:
    """Download with curl (honours the environment proxy/CA settings). Returns (http_code, error)."""
    proc = subprocess.run(
        ["curl", "-sS", "-L", "-m", str(timeout), "-o", str(dest), "-w", "%{http_code}", url],
        capture_output=True,
        text=True,
    )
    code = int(proc.stdout.strip() or 0) if proc.stdout.strip().isdigit() else 0
    return code, proc.stderr.strip()


def download_documents(docs: list[dict], raw_dir: Path, manifest_path: Path, timeout: int = 30,
                       max_attempts: int = 3, delay: float = 0.4) -> list[dict]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for d in docs:
        fname = Path(d["url_path"]).name
        dest = raw_dir / fname
        url = BOU_FILE_BASE + d["url_path"]
        status, err, attempts = 0, "", 0
        if dest.exists() and dest.stat().st_size > 0:
            status, attempts = 200, 0  # cached from an earlier run in this container
        else:
            part = dest.with_name(dest.name + ".part")
            for attempts in range(1, max_attempts + 1):
                status, err = _curl(url, part, timeout)
                if status == 200 and not err:
                    part.replace(dest)  # only complete transfers become raw files
                    break
                part.unlink(missing_ok=True)
                if status in (403, 404, 407):  # policy / not found: do not retry
                    break
                time.sleep(2 ** attempts)
            time.sleep(delay)
        ok = status == 200 and dest.exists() and not err
        manifest.append(
            {
                **{k: d[k] for k in ("category", "year", "month", "title", "ext", "cms_created_at")},
                "source_url": url,
                "local_file": fname if ok else "",
                "http_status": status,
                "attempts": attempts,
                "bytes": dest.stat().st_size if ok else 0,
                "sha256": sha256_file(dest) if ok else "",
                "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "error": err,
            }
        )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(manifest[0]))
        w.writeheader()
        w.writerows(manifest)
    return manifest


def main(argv: list[str] | None = None) -> None:
    import argparse

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog", type=Path, default=Path("data/raw/bou/auction_information_catalog.json"))
    p.add_argument("--raw-dir", type=Path, default=Path("data/raw/bou/docs"))
    p.add_argument("--manifest", type=Path, default=Path("data/manifests/bou_tbill_documents.csv"))
    p.add_argument("--first-year", type=int, default=2023)
    p.add_argument("--fetch-catalog", action="store_true", help="re-download the CMS catalogue first")
    a = p.parse_args(argv)
    if a.fetch_catalog or not a.catalog.exists():
        a.catalog.parent.mkdir(parents=True, exist_ok=True)
        code, err = _curl(CATALOG_URL, a.catalog, 40)
        if code != 200:
            raise SystemExit(f"catalogue fetch failed: {code} {err}")
    rows = flatten_catalog(json.loads(a.catalog.read_text()))
    docs = select_tbill_documents(rows, a.first_year)
    print(f"catalogue rows={len(rows)} selected T-bill documents={len(docs)} sha256={sha256_file(a.catalog)}")
    man = download_documents(docs, a.raw_dir, a.manifest)
    ok = sum(1 for m in man if m["local_file"])
    print(f"downloaded ok={ok} failed={len(man) - ok} bytes={sum(m['bytes'] for m in man)}")


if __name__ == "__main__":
    main()
