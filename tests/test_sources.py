from pathlib import Path

from tracker.sources import parse_sources_markdown


def test_parse_sources_markdown_fixture() -> None:
    path = Path("tests/fixtures/sources_sample.md")
    sources = parse_sources_markdown(path)

    assert len(sources) == 2
    assert sources[0].tag == "swimontario_live_results_index"
    assert sources[0].url == "https://swimontario.com/liveresults/"
    assert sources[1].tag == "nyac_sample_pdf"
