from __future__ import annotations

import re


def extract_pdf_text(data: bytes) -> str:
    # Try pypdf when available; fall back to lightweight extraction.
    try:
        from pypdf import PdfReader  # type: ignore
        from io import BytesIO

        reader = PdfReader(BytesIO(data))
        pieces = []
        for page in reader.pages:
            pieces.append(page.extract_text() or "")
        text = "\n".join(pieces).strip()
        if text:
            return text
    except Exception:
        pass

    raw = data.decode("latin-1", errors="ignore")
    chunks = re.findall(r"\(([^\)]{1,300})\)", raw)
    if chunks:
        return "\n".join(chunks)
    return raw
