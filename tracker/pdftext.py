from __future__ import annotations

import re


def extract_pdf_text(data: bytes) -> str:
    text = ""
    # Try pypdf when available; fall back to lightweight extraction.
    try:
        from io import BytesIO

        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(BytesIO(data))
        pieces = []
        for page in reader.pages:
            pieces.append(page.extract_text() or "")
        text = "\n".join(pieces).strip()
        if text:
            return text
    except Exception:
        text = ""

    raw = data.decode("latin-1", errors="ignore")
    chunks = re.findall(r"\(([^\)]{1,300})\)", raw)
    if chunks:
        return "\n".join(chunks)
    return raw
