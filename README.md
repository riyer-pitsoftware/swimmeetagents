# Ontario Swim Tracker (Personal MVP)

Personal-use CLI tracker for Ontario swim meets. It follows selected athletes, ingests public results from seed sources in `sources.md`, stores normalized results in SQLite, and prints a timeline with personal-best detection.

## Safety + Compliance

- Public-only ingestion: no login flows, no bypassing access controls.
- Respect robots.txt for each fetch target.
- Conservative source blocking: domains related to private/restricted endpoints (for example Meet Mobile) are blocked.
- Light traffic defaults:
  - watch mode polling defaults to 15 minutes (`TRACKER_POLL_SECONDS=900`)
  - minimum allowed polling is 10 minutes (`TRACKER_MIN_POLL_SECONDS=600`)
  - exponential backoff on errors
- Minimal personal data: only athlete names/clubs from public results are stored.

If a source forbids bots or requires login, do not implement scraping for it. Track that as a bead instead.

## Canonical Sources

Seed sources are read from `./sources.md`.

Expected parse format per line:

- `[tag] https://example.com/page`
- trailing comments after `#` are ignored

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

## CLI

Manage followed athletes:

```bash
python -m tracker.athletes add "First Last" --club VAC
python -m tracker.athletes list
python -m tracker.athletes remove "First Last"
```

Seed source commands:

```bash
python -m tracker.sources refresh
python -m tracker.sources list
```

Runner:

```bash
python -m tracker.run --once
python -m tracker.run --once --dry-run
python -m tracker.run --watch
python -m tracker.run --watch --source-url https://example.com/public-results.pdf
```

Web dashboard + API:

```bash
python -m tracker.web
```

Then open `http://127.0.0.1:8787`.

Main API endpoints:
- `GET /api/athletes`
- `POST /api/athletes`
- `DELETE /api/athletes/<name>`
- `GET /api/sources`
- `POST /api/sources/refresh`
- `POST /api/run/once`
- `GET /api/results?athlete=<name>&limit=100`

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
