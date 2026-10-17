"""Text extraction from official PDFs/DOCX (poppler ``pdftotext -layout``; DOCX via its XML)."""

from __future__ import annotations

import re
import subprocess
import zipfile
from pathlib import Path


def extract_text(path: Path) -> str:
    path = Path(path)
    if path.suffix.lower() == ".docx":
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf8", "replace")
        xml = re.sub(r"</w:p>|</w:tr>", "\n", xml)
        xml = re.sub(r"</w:tc>", "   ", xml)
        return re.sub(r"<[^>]+>", "", xml)
    proc = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True)
    return proc.stdout
