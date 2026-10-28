# Architecture (hackathon vertical slice)

Single-process FastAPI application. Domain logic is pure and deterministic;
the store persists state as JSON; the model only interprets evidence.

```text
Synthetic seed (app/seed.py)
  -> Event validation/normalization/idempotency (app/events.py, app/store.py:ingest_event)
  -> Entity resolution = seeded identity map (nodes carry source_record_ids)
  -> Graph + provenance check + features (app/graph.py)
  -> Versioned rules + risk-score-v1 (app/rules.py)
  -> Evidence items + package + hash (app/evidence.py)
  -> Investigation view (app/main.py + templates/investigation.html)
  -> Meta adapter + validators (app/ai_adapter.py)
  -> Replay cursor (app/replay.py) / bounded what-if (app/simulate.py)
  -> Human decision + case machine (app/cases.py) + audit (app/store.py)
```

## Module boundaries

- Domain services (`seed/events/graph/rules/evidence/cases/replay/simulate`)
  compute authoritative facts. No HTTP or model concepts inside them.
- `store.py` owns persistence (atomic JSON writes) and audit sequencing.
- `ai_adapter.py` owns the only external call: server-side httpx POST to the
  OpenAI-compatible Meta endpoint, plus response parsing and validation.
- `main.py` owns routing, error envelope `{error: {code, message, trace_id}}`,
  and page rendering. It never manufactures facts.
- Frontend (`templates/`, `static/`) renders API/store state only. The SVG
  graph is laid out deterministically (BFS layers) from backend data.

## Data

- Money in integer minor units (kobo). IDs stable per blueprint prefixes.
- `data/state.json` (gitignored) holds the active scenario run; reset re-seeds
  deterministically from the versioned manifest.
- No database server, queue, or cache: deliberately the smallest durable
  option (ADR-001). SQLite/Postgres remain a forward option without contract
  changes (store interface is the seam).
