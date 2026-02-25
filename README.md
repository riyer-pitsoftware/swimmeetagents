# Ontario Swim Tracker (Personal MVP)

Personal-use CLI tracker for Ontario swim meets. It follows selected athletes, ingests public results from seed sources in `sources.md`, stores normalized results in SQLite, and prints a timeline with personal-best detection.

## Safety + Compliance

- Public-only ingestion: no login flows, no bypassing access controls.
- Respect robots.txt for each fetch target.
- Conservative source blocking: domains related to private/restricted endpoints (for example Meet Mobile) are blocked.
- Conservative robots policy: if robots.txt cannot be fetched or parsed, source fetch is blocked.
- SSRF hardening: blocks localhost, private/link-local/reserved IP targets (including DNS-resolved private targets).
- Light traffic defaults:
  - watch mode polling defaults to 15 minutes (`TRACKER_POLL_SECONDS=900`)
  - minimum allowed polling is 10 minutes (`TRACKER_MIN_POLL_SECONDS=600`)
  - exponential backoff on errors
  - max download size per fetch defaults to 20MB (`TRACKER_MAX_DOWNLOAD_BYTES=20971520`)
- Minimal personal data: only athlete names/clubs from public results are stored.

If a source forbids bots or requires login, do not implement scraping for it. Track that as a bead instead.

## Canonical Sources

Seed sources are read from `./sources.md`.

Expected parse format per line:

- `[tag] https://example.com/page`
- trailing comments after `#` are ignored

## Runtime Isolation

This app is container-only.

- Do not run `python -m tracker.*` on the host.
- Entry points enforce a runtime guard and fail outside Docker.
- Use Docker Compose commands below for all operations.

## Setup (Docker Only)

```bash
docker compose build
```

## CLI

Manage followed athletes:

```bash
docker compose run --rm tracker-cli -m tracker.athletes add "First Last" --club VAC
docker compose run --rm tracker-cli -m tracker.athletes list
docker compose run --rm tracker-cli -m tracker.athletes remove "First Last"
```

Seed source commands:

```bash
docker compose run --rm tracker-cli -m tracker.sources refresh
docker compose run --rm tracker-cli -m tracker.sources list
```

Runner:

```bash
docker compose run --rm tracker-cli -m tracker.run --once
docker compose run --rm tracker-cli -m tracker.run --once --dry-run
docker compose run --rm tracker-cli -m tracker.run --watch
docker compose run --rm tracker-cli -m tracker.run --watch --source-url https://example.com/public-results.pdf
```

Web dashboard + API:

```bash
docker compose up -d tracker-web
```

Then open `http://127.0.0.1:8787`.

Stop web service:

```bash
docker compose down
```

Main API endpoints:
- `GET /api/athletes`
- `POST /api/athletes`
- `DELETE /api/athletes/<name>`
- `GET /api/sources`
- `POST /api/sources/refresh`
- `POST /api/run/once`
- `GET /api/results?athlete=<name>&limit=100`

## Quality Gates

```bash
python -m pip install -e .[dev]
python -m pytest -q
python -m compileall -q tracker tests
python -c "import tracker.sources, tracker.adapters.swim_ontario, tracker.adapters.generic_pdf"
ruff check tracker tests
ruff format --check tracker tests
bandit -q -r tracker
pip-audit -r requirements-audit.txt
docker compose config
```

## Data Model

Normalized schema includes:

- `meets`
- `sessions`
- `events`
- `results`
- `seed_sources`
- `source_fetch_log`
- `athletes`

See `docs/architecture.md` for adapter design and flow.
