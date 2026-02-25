from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from tracker.config import AppConfig
from tracker.db import Database
from tracker.runtime_guard import require_container_runtime
from tracker.run import run_once
from tracker.sources import parse_sources_markdown
from tracker.util import parse_swim_time_to_centiseconds


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).with_name("templates")),
        static_folder=str(Path(__file__).with_name("static")),
    )

    def _db() -> Database:
        config = AppConfig.load()
        db = Database(config.db_path)
        db.init_schema()
        return db

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.get("/api/athletes")
    def list_athletes():
        db = _db()
        try:
            athletes = [asdict(row) for row in db.list_athletes()]
            return jsonify({"athletes": athletes})
        finally:
            db.close()

    @app.post("/api/athletes")
    def add_athlete():
        payload = request.get_json(silent=True) or {}
        name = (payload.get("name") or "").strip()
        club = (payload.get("club") or "").strip() or None
        if not name:
            return jsonify({"error": "name is required"}), 400

        db = _db()
        try:
            db.add_athlete(name, club)
            return jsonify({"ok": True})
        finally:
            db.close()

    @app.delete("/api/athletes/<path:name>")
    def remove_athlete(name: str):
        db = _db()
        try:
            deleted = db.remove_athlete(name)
            return jsonify({"ok": True, "deleted": deleted})
        finally:
            db.close()

    @app.get("/api/sources")
    def list_sources():
        db = _db()
        try:
            sources = [asdict(row) for row in db.list_seed_sources()]
            return jsonify({"sources": sources})
        finally:
            db.close()

    @app.post("/api/sources/refresh")
    def refresh_sources():
        config = AppConfig.load()
        db = _db()
        try:
            sources = parse_sources_markdown(config.sources_file)
            db.upsert_seed_sources(sources)
            return jsonify({"ok": True, "count": len(sources)})
        finally:
            db.close()

    @app.post("/api/run/once")
    def run_once_api():
        config = AppConfig.load()
        payload = request.get_json(silent=True) or {}
        dry_run = bool(payload.get("dry_run", True))
        extra_urls = payload.get("source_urls") or []
        if not isinstance(extra_urls, list):
            return jsonify({"error": "source_urls must be an array"}), 400

        db = _db()
        try:
            exit_code = run_once(db, config, [str(v) for v in extra_urls], dry_run=dry_run)
            return jsonify({"ok": exit_code == 0, "exit_code": exit_code})
        finally:
            db.close()

    @app.get("/api/results")
    def list_results():
        athlete = request.args.get("athlete")
        try:
            limit = int(request.args.get("limit", "100"))
        except ValueError:
            return jsonify({"error": "limit must be an integer"}), 400
        limit = max(1, min(limit, 500))

        db = _db()
        try:
            rows = db.list_recent_results(limit=limit, athlete_name=athlete)
            response: list[dict[str, object]] = []
            for row in rows:
                pb = db.latest_personal_best(row.athlete_name, row.event_name)
                current_cs = parse_swim_time_to_centiseconds(row.time_text)
                response.append(
                    {
                        **asdict(row),
                        "personal_best": bool(
                            pb is not None and current_cs is not None and current_cs <= pb
                        ),
                    }
                )
            return jsonify({"results": response})
        finally:
            db.close()

    return app


def main() -> int:
    require_container_runtime()
    app = create_app()
    app.run(host="127.0.0.1", port=8787, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
