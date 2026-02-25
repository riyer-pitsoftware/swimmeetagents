from datetime import datetime
from pathlib import Path

from tracker.adapters.base import AdapterInput
from tracker.adapters.swim_ontario import SwimOntarioAdapter
from tracker.util import normalize_name


def test_swim_ontario_discovery_and_parse() -> None:
    html = Path("tests/fixtures/swim_ontario_index.html").read_bytes()
    adapter = SwimOntarioAdapter()
    payload = AdapterInput(
        source_url="https://swimontario.com/liveresults/2025/OSC/",
        fetched_url="https://swimontario.com/liveresults/2025/OSC/",
        content_type="text/html",
        body=html,
        fetched_at=datetime(2026, 1, 1),
    )

    discovered = adapter.discover_urls(payload)
    assert "https://swimontario.com/liveresults/2025/OSC/ResultList_001.pdf" in discovered
    assert "https://swimontario.com/liveresults/2025/OSC/results.html" in discovered

    pdf_payload = AdapterInput(
        source_url=payload.source_url,
        fetched_url="https://swimontario.com/liveresults/2025/OSC/ResultList_001.pdf",
        content_type="application/pdf",
        body=Path("tests/fixtures/generic_results.pdf").read_bytes(),
        fetched_at=datetime(2026, 1, 1),
    )
    followed = {normalize_name("Avery Stone")}
    parsed = adapter.parse_results(pdf_payload, followed)
    assert len(parsed) == 1
    assert parsed[0].athlete_name == "Avery Stone"
    assert parsed[0].time_text == "1:02.34"
