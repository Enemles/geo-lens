# GEO Lens

**Measure how visible a brand is to AI assistants.**

The search bar is becoming a conversation. When someone asks ChatGPT or Claude
"what are the best X tools?", does *your* brand get mentioned, recommended, or
cited — or are you invisible? GEO Lens answers that. It asks several large
language models a set of realistic buyer-intent questions about a brand and its
market, then scores whether and how the brand surfaces. It's a small, focused
take on Generative Engine Optimization (GEO).

Built as a FastAPI service with a clean provider abstraction, concurrent
multi-model querying, caching, and an SSE streaming endpoint.

---

## What it does

Give it a brand (optionally a domain and market category):

```bash
curl -X POST localhost:8000/api/analyze -H 'Content-Type: application/json' \
  -d '{"brand": "Yolando", "domain": "yolando.ai", "category": "AI brand-visibility tools"}'
```

It builds a mix of **open-category** prompts ("what are the best X?" — does the
brand surface unprompted?) and **direct** prompts ("what do you know about X?" —
does the model know it at all?), fans them out across every configured
assistant, and returns a 0–100 **visibility score** plus a per-query breakdown:
mentioned / recommended / rank / excerpt.

The interesting signal is the *gap*: a brand the models will name when asked
directly but never recommend unprompted is exactly the brand GEO is meant to fix.

---

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# Runs immediately on a deterministic mock provider — no API keys needed.
uvicorn app.main:app --reload

# Interactive API docs (auto-generated from the Pydantic schemas):
open http://localhost:8000/docs
```

To query real models, copy `.env.example` to `.env` and add an
`ANTHROPIC_API_KEY` and/or `OPENAI_API_KEY`. Each provider with a key present is
registered automatically and queried in parallel.

```bash
pytest          # 27 tests, fully offline
```

---

## Architecture

```
HTTP  ──►  routers/        FastAPI routes (analyze, history, SSE stream)
           │
           ├─ services/analyzer.py   fan-out + aggregation (the orchestrator)
           │     ├─ services/cache.py    TTL cache w/ stampede protection
           │     └─ services/scoring.py  pure, deterministic mention scoring
           │
           ├─ providers/    one class per assistant behind a single interface
           │     ├─ base.py / mock.py / anthropic.py / openai.py
           │
           └─ models.py + database.py    SQLModel persistence (SQLite → Postgres)
```

**Design choices worth knowing:**

- **Provider abstraction.** GEO is inherently multi-model — a brand can be
  visible to one assistant and invisible to another — so the analyzer depends
  only on an `LLMProvider` interface (`async complete(prompt) -> str`). Adding an
  assistant is one subclass. A deterministic mock implements the same interface
  so the whole service runs and tests offline.
- **Scoring is isolated from the LLM.** All nondeterminism lives at the provider
  boundary; `scoring.py` is pure functions over text, so it's fast, free, and
  exhaustively unit-tested.
- **DTOs vs entities.** Pydantic schemas (`schemas.py`) are the API contract;
  SQLModel tables (`models.py`) are persistence. The OpenAPI schema generated
  from the DTOs is what a typed frontend client is generated from.

---

## Performance & scaling

This is the part that mattered most to get right — an analysis is *N prompts ×
M models*, and every call is a slow, metered network round-trip.

1. **Concurrency.** Calls are launched together with `asyncio.gather` (and
   `as_completed` for streaming) instead of sequentially. For 6 prompts × 2
   models that's the difference between ~1 slow call's latency and the sum of
   twelve.
2. **A global concurrency ceiling.** Firing everything at once trips provider
   rate limits (429s). A single shared `asyncio.Semaphore` caps how many calls
   are in flight across the entire fan-out — tune it with `MAX_CONCURRENT_CALLS`.
3. **Caching with stampede protection.** Identical `(provider, prompt)` pairs
   are served from a TTL cache. The non-obvious bit is a **per-key lock**:
   without it, concurrent cold misses for the same key would all hit the API at
   once. The first caller fills the entry; the rest wait and read it
   (double-checked locking). The shape is Redis-swappable.
4. **Pooled HTTP clients.** Each provider holds one `httpx.AsyncClient` reused
   across calls, so connections are pooled rather than re-handshaked per request,
   and closed cleanly on app shutdown via the lifespan.
5. **Bounded retries with backoff.** Transient 429/5xx/timeout failures retry
   with exponential backoff in one shared helper, so one flaky call doesn't sink
   an analysis.
6. **Streaming.** `POST /api/analyze/stream` emits an SSE `progress` event as
   each query lands and a final `summary`, so a UI shows real-time progress
   instead of a 30-second spinner.

---

## Type-safe frontend integration

FastAPI generates an OpenAPI 3 schema at `/openapi.json` from the Pydantic
models. A frontend generates a typed client from it — e.g.
`openapi-typescript` for types or `openapi-generator` for a full client — so the
contract between frontend and backend is checked at compile time and any
breaking API change surfaces as a type error, not a runtime 500. Error responses
use a consistent shape so the client can pattern-match on them.

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/analyze` | Run an analysis, persist it, return the full result |
| `POST` | `/api/analyze/stream` | Same, streamed as Server-Sent Events |
| `GET`  | `/api/analyses` | List past analyses (paginated) |
| `GET`  | `/api/analyses/{id}` | Fetch one analysis with its per-query breakdown |
| `DELETE` | `/api/analyses/{id}` | Delete an analysis |
| `GET`  | `/health` | Liveness check |

## Stack

Python 3.11 · FastAPI · Pydantic v2 · SQLModel · httpx · pytest · Docker

## Roadmap

- Structured-output scoring (ask the model for JSON, score that) to replace the
  v1 string heuristics
- Track visibility over time and chart trend per brand
- More assistants (Gemini, Perplexity) — each is one new provider class
# geo-lens
