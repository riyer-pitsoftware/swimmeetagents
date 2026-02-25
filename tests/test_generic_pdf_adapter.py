from datetime import datetime
from pathlib import Path

from tracker.adapters.generic_pdf import parse_generic_pdf_text
from tracker.pdftext import extract_pdf_text
from tracker.util import normalize_name


def test_generic_pdf_parse_fixture() -> None:
    data = Path("tests/fixtures/generic_results.pdf").read_bytes()
    text = extract_pdf_text(data)
    followed = {normalize_name("Avery Stone")}

    parsed = parse_generic_pdf_text(
        text=text,
        source_url="https://example.org/results.pdf",
        followed_athletes=followed,
        captured_at=datetime(2026, 1, 1),
    )

    assert len(parsed) == 1
    row = parsed[0]
    assert row.event_name == "100 Freestyle"
    assert row.athlete_name == "Avery Stone"
    assert row.time_text == "1:02.34"
