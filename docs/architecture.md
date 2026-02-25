# Architecture (MVP)

## Scope

- Personal-use Ontario meet tracker.
- Ingest only public pages/files that permit automation.
- Use `sources.md` as canonical seed source list.

## Components

1. CLI modules
- `tracker.athletes`: manage followed athletes.
- `tracker.sources`: load/list seed sources.
- `tracker.run`: one-shot and watch scheduler.
- `tracker.web`: local dashboard and HTTP API for athletes/sources/run/timeline.

2. Storage (SQLite)
- `athletes`: followed names.
- `seed_sources`: parsed from `sources.md`.
- `meets`, `sessions`, `events`, `results`: normalized swim data.
- `source_fetch_log`: fetch outcomes + backoff metadata.

3. Adapter system
- Interface in `tracker.adapters.base` with:
  - `can_handle(...)`
  - `discover_urls(...)`
  - `parse_results(...)`
- Implemented adapters:
  - Swim Ontario folder/live results adapter (HTML index + linked files)
  - Generic public PDF results adapter

4. Fetch and policy guardrails
- `tracker.fetch`:
  - robots.txt allow-check before fetch
  - blocked-domain guard for restricted ecosystems
  - user-agent and timeout controls
- No login, no private endpoint reverse engineering.

## Data Flow

1. `tracker.run` loads config + initializes DB schema.
2. Seed sources refreshed from `sources.md`.
3. For each source:
- policy checks (domain block + robots)
- fetch page/file
- choose adapter
- parse results matching followed athletes
- optional one-level discovery of linked result files
- write results (unless `--dry-run`)
4. Print timeline and PB signals.

## Scheduling & Backoff

- `--once`: run one cycle.
- `--watch`: continuous run with source state tracking.
- Default interval: 900s (15 minutes).
- Minimum enforced: 600s (10 minutes).
- On errors: exponential backoff up to configured max.

## Testing strategy

- Unit tests for:
  - `sources.md` parser
  - Swim Ontario HTML discovery and parsing
  - Generic PDF parser
- Fixtures under `tests/fixtures/` are synthetic/public-safe.
