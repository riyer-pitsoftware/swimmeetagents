from pathlib import Path

from tracker.db import Database
from tracker.types import SeedSource


def _open_db(path: Path) -> Database:
    db = Database(path)
    db.init_schema()
    return db


def test_upsert_seed_sources_deactivates_removed_entries(tmp_path: Path) -> None:
    db = _open_db(tmp_path / "tracker.db")
    try:
        db.upsert_seed_sources(
            [
                SeedSource(tag="one", url="https://example.com/one"),
                SeedSource(tag="two", url="https://example.com/two"),
            ],
            deactivate_missing=True,
        )
        db.upsert_seed_sources(
            [SeedSource(tag="one", url="https://example.com/one")],
            deactivate_missing=True,
        )

        active = db.list_seed_sources()
        assert [s.url for s in active] == ["https://example.com/one"]

        removed = db.conn.execute(
            "SELECT active FROM seed_sources WHERE url=?",
            ("https://example.com/two",),
        ).fetchone()
        assert removed is not None
        assert int(removed["active"]) == 0
    finally:
        db.close()


def test_upsert_seed_sources_keeps_existing_when_not_deactivating(tmp_path: Path) -> None:
    db = _open_db(tmp_path / "tracker.db")
    try:
        db.upsert_seed_sources(
            [
                SeedSource(tag="one", url="https://example.com/one"),
                SeedSource(tag="two", url="https://example.com/two"),
            ],
            deactivate_missing=True,
        )
        db.upsert_seed_sources(
            [SeedSource(tag="one-updated", url="https://example.com/one")],
            deactivate_missing=False,
        )

        active = db.list_seed_sources()
        assert [s.url for s in active] == [
            "https://example.com/one",
            "https://example.com/two",
        ]
    finally:
        db.close()
