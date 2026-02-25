from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sqlite3

from tracker.types import ParsedResult, SeedSource
from tracker.util import normalize_name, parse_swim_time_to_centiseconds


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS athletes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  display_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL UNIQUE,
  club TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS seed_sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tag TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  active INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  source_url TEXT NOT NULL,
  first_seen_at TEXT NOT NULL,
  UNIQUE(name, source_url)
);

CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  meet_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  session_date TEXT,
  UNIQUE(meet_id, name),
  FOREIGN KEY(meet_id) REFERENCES meets(id)
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  gender TEXT,
  distance TEXT,
  stroke TEXT,
  UNIQUE(session_id, name),
  FOREIGN KEY(session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER NOT NULL,
  athlete_name TEXT NOT NULL,
  normalized_athlete_name TEXT NOT NULL,
  club TEXT,
  time_text TEXT NOT NULL,
  time_centiseconds INTEGER,
  source_url TEXT NOT NULL,
  captured_at TEXT NOT NULL,
  UNIQUE(event_id, normalized_athlete_name, time_text),
  FOREIGN KEY(event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS source_fetch_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_url TEXT NOT NULL,
  fetched_at TEXT NOT NULL,
  status TEXT NOT NULL,
  http_status INTEGER,
  error TEXT,
  backoff_seconds INTEGER DEFAULT 0
);
"""


@dataclass(frozen=True)
class FollowedAthlete:
    display_name: str
    normalized_name: str
    club: str | None


@dataclass(frozen=True)
class TimelineResult:
    captured_at: str
    meet_name: str
    session_name: str
    event_name: str
    athlete_name: str
    club: str | None
    time_text: str
    source_url: str


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self.conn.close()

    def init_schema(self) -> None:
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()

    def upsert_seed_sources(self, sources: list[SeedSource]) -> None:
        now = datetime.utcnow().isoformat()
        with self.conn:
            for src in sources:
                self.conn.execute(
                    """
                    INSERT INTO seed_sources(tag, url, active, updated_at)
                    VALUES (?, ?, 1, ?)
                    ON CONFLICT(url) DO UPDATE SET
                      tag=excluded.tag,
                      active=1,
                      updated_at=excluded.updated_at
                    """,
                    (src.tag, src.url, now),
                )

    def list_seed_sources(self) -> list[SeedSource]:
        cur = self.conn.execute(
            "SELECT tag, url FROM seed_sources WHERE active=1 ORDER BY tag, url"
        )
        return [SeedSource(row["tag"], row["url"]) for row in cur.fetchall()]

    def add_athlete(self, name: str, club: str | None = None) -> None:
        normalized = normalize_name(name)
        now = datetime.utcnow().isoformat()
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO athletes(display_name, normalized_name, club, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(normalized_name) DO UPDATE SET
                  display_name=excluded.display_name,
                  club=COALESCE(excluded.club, athletes.club)
                """,
                (name.strip(), normalized, club, now),
            )

    def remove_athlete(self, name: str) -> int:
        normalized = normalize_name(name)
        with self.conn:
            cur = self.conn.execute(
                "DELETE FROM athletes WHERE normalized_name=?", (normalized,)
            )
            return cur.rowcount

    def list_athletes(self) -> list[FollowedAthlete]:
        cur = self.conn.execute(
            "SELECT display_name, normalized_name, club FROM athletes ORDER BY display_name"
        )
        return [
            FollowedAthlete(row["display_name"], row["normalized_name"], row["club"])
            for row in cur.fetchall()
        ]

    def log_fetch(
        self,
        source_url: str,
        status: str,
        http_status: int | None = None,
        error: str | None = None,
        backoff_seconds: int = 0,
    ) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO source_fetch_log(source_url, fetched_at, status, http_status, error, backoff_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    source_url,
                    datetime.utcnow().isoformat(),
                    status,
                    http_status,
                    error,
                    backoff_seconds,
                ),
            )

    def insert_results(self, parsed_results: list[ParsedResult]) -> int:
        inserted = 0
        with self.conn:
            for result in parsed_results:
                meet_id = self._upsert_meet(result.meet_name, result.source_url)
                session_id = self._upsert_session(meet_id, result.session_name)
                event_id = self._upsert_event(session_id, result.event_name)
                normalized = normalize_name(result.athlete_name)
                cs = parse_swim_time_to_centiseconds(result.time_text)
                cur = self.conn.execute(
                    """
                    INSERT OR IGNORE INTO results(
                      event_id, athlete_name, normalized_athlete_name, club, time_text,
                      time_centiseconds, source_url, captured_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        result.athlete_name,
                        normalized,
                        result.club,
                        result.time_text,
                        cs,
                        result.source_url,
                        result.captured_at.isoformat(),
                    ),
                )
                inserted += cur.rowcount
        return inserted

    def _upsert_meet(self, name: str, source_url: str) -> int:
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            """
            INSERT OR IGNORE INTO meets(name, source_url, first_seen_at)
            VALUES (?, ?, ?)
            """,
            (name, source_url, now),
        )
        row = self.conn.execute(
            "SELECT id FROM meets WHERE name=? AND source_url=?", (name, source_url)
        ).fetchone()
        assert row is not None
        return int(row["id"])

    def _upsert_session(self, meet_id: int, name: str) -> int:
        self.conn.execute(
            "INSERT OR IGNORE INTO sessions(meet_id, name) VALUES (?, ?)", (meet_id, name)
        )
        row = self.conn.execute(
            "SELECT id FROM sessions WHERE meet_id=? AND name=?", (meet_id, name)
        ).fetchone()
        assert row is not None
        return int(row["id"])

    def _upsert_event(self, session_id: int, name: str) -> int:
        self.conn.execute(
            "INSERT OR IGNORE INTO events(session_id, name) VALUES (?, ?)",
            (session_id, name),
        )
        row = self.conn.execute(
            "SELECT id FROM events WHERE session_id=? AND name=?", (session_id, name)
        ).fetchone()
        assert row is not None
        return int(row["id"])

    def latest_personal_best(self, athlete_name: str, event_name: str) -> int | None:
        normalized = normalize_name(athlete_name)
        row = self.conn.execute(
            """
            SELECT MIN(r.time_centiseconds) AS pb
            FROM results r
            JOIN events e ON e.id = r.event_id
            WHERE r.normalized_athlete_name=?
              AND e.name=?
              AND r.time_centiseconds IS NOT NULL
            """,
            (normalized, event_name),
        ).fetchone()
        return None if row is None else row["pb"]

    def list_recent_results(
        self,
        limit: int = 100,
        athlete_name: str | None = None,
    ) -> list[TimelineResult]:
        query = """
        SELECT
          r.captured_at,
          m.name AS meet_name,
          s.name AS session_name,
          e.name AS event_name,
          r.athlete_name,
          r.club,
          r.time_text,
          r.source_url
        FROM results r
        JOIN events e ON e.id = r.event_id
        JOIN sessions s ON s.id = e.session_id
        JOIN meets m ON m.id = s.meet_id
        """
        params: list[object] = []
        if athlete_name:
            query += " WHERE r.normalized_athlete_name=?"
            params.append(normalize_name(athlete_name))
        query += " ORDER BY r.captured_at DESC LIMIT ?"
        params.append(limit)

        rows = self.conn.execute(query, params).fetchall()
        return [
            TimelineResult(
                captured_at=row["captured_at"],
                meet_name=row["meet_name"],
                session_name=row["session_name"],
                event_name=row["event_name"],
                athlete_name=row["athlete_name"],
                club=row["club"],
                time_text=row["time_text"],
                source_url=row["source_url"],
            )
            for row in rows
        ]
