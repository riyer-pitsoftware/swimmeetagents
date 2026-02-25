from __future__ import annotations

from datetime import datetime, timedelta

from tracker.db import Database
from tracker.types import ParsedResult
from tracker.web import create_app


def test_results_personal_best_semantics_is_tie_inclusive(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "tracker.db"
    monkeypatch.setenv("TRACKER_DB_PATH", str(db_path))

    db = Database(db_path)
    db.init_schema()
    try:
        base = datetime(2026, 1, 1, 12, 0, 0)
        db.insert_results(
            [
                ParsedResult(
                    source_url="https://example.com/one",
                    meet_name="Meet A",
                    session_name="Session 1",
                    event_name="50 Free",
                    athlete_name="Kid One",
                    club="VAC",
                    time_text="30.00",
                    captured_at=base,
                ),
                ParsedResult(
                    source_url="https://example.com/two",
                    meet_name="Meet A",
                    session_name="Session 2",
                    event_name="50 Free",
                    athlete_name="Kid One",
                    club="VAC",
                    time_text="29.50",
                    captured_at=base + timedelta(minutes=1),
                ),
                ParsedResult(
                    source_url="https://example.com/three",
                    meet_name="Meet A",
                    session_name="Session 3",
                    event_name="50 Free",
                    athlete_name="Kid One",
                    club="VAC",
                    time_text="29.50",
                    captured_at=base + timedelta(minutes=2),
                ),
            ]
        )
    finally:
        db.close()

    app = create_app()
    with app.test_client() as client:
        resp = client.get("/api/results?athlete=Kid%20One&limit=10")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body is not None
        assert body["personal_best_semantics"] == "tie_inclusive_all_time_best"

        rows = body["results"]
        assert [row["time_text"] for row in rows] == ["29.50", "29.50", "30.00"]
        assert [row["personal_best"] for row in rows] == [True, True, False]
