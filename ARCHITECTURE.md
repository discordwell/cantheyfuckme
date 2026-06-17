# Architecture

cantheyfuckme.com — AI contract analysis for consumers. Single Docker container serving a FastAPI backend and a prebuilt React SPA, with optional Postgres for accounts/history.

```
Browser ──HTTPS──> Caddy (VPS, TLS for cantheyfuckme.com)
                     │ reverse_proxy :8081
                     ▼
            FastAPI (backend/main.py)
              ├── /api/*  ........ JSON API (routers/)
              ├── /assets ........ built SPA assets (frontend/dist)
              └── /{path} ........ SPA fallback → index.html
                     │                      │
                     ▼                      ▼
              OpenAI API            PostgreSQL 16 (optional)
```

## Repository Layout

```
backend/
  main.py            # app wiring: CORS, routers, SPA serving
  config.py          # env-driven settings (models, CORS, Stripe, DB URL)
  database.py        # SQLAlchemy engine/session; degrades gracefully without DB
  models/            # ORM: Upload, Waitlist, User, AuthSession, PremiumUnlock
  schemas/           # Pydantic request/response models, one module per doc type
  prompts/           # LLM prompt templates, one module per doc type
  data/              # static reference data: state laws, red-flag catalogs
  services/
    llm.py           # OpenAI client, llm_text_call/llm_json_call helpers
    analysis.py      # shared analyzer flow (hash → mock|LLM → persist → report)
    auth.py          # bcrypt passwords, token sessions, premium unlocks
    db_ops.py        # upload/waitlist persistence
    limits.py        # request-size guards (413) for public endpoints
    rate_limit.py    # per-IP sliding-window rate limiter + client-IP resolution
    mock/            # keyword-based fake analyzers for MOCK_MODE
  routers/
    analyzers.py     # 13 document analyzers
    documents.py     # classify, OCR, extract, compare, proposal
    auth.py          # signup/login/logout/me/history
    payments.py      # legacy Stripe checkout + webhook (donations use a payment link)
    reference.py     # state law / project type lookups
    waitlist.py      # unsupported-doc-type signups
  tests/             # offline pytest suite (MOCK_MODE, no DB, no API key)
  test_api.py        # legacy end-to-end script against a live server
  test_expensive.py  # real-LLM smoke tests ($)
frontend/
  src/               # React SPA: hooks (useAnalyzer<T>, useAuth), components, api client
  dist/              # build output, baked into the Docker image
```

## Request Flow (analyzer)

1. SPA posts document text to `/api/analyze-<type>` (optionally with state/price context).
2. `services.analysis.run_analysis`:
   - SHA-256 hash of the text; resolve user from Bearer token or cookie.
   - `MOCK_MODE=true` → keyword-based mock result; otherwise build the per-type prompt (truncated to 15k chars) and call `llm_json_call`, which strips markdown fences and parses JSON.
   - Persist the upload (fire-and-forget; absent DB is fine).
   - Construct the typed Pydantic report and stamp `document_hash`, `is_premium`, `total_issues`.
3. COI and lease are two-step (extract → analyze) and orchestrate `llm_json_call` directly.

State-specific intelligence comes from `data/` (e.g. gym cancellation laws, non-compete enforceability, timeshare rescission windows) injected into prompts.

## Auth & Persistence

- Email + bcrypt password; 30-day random-token sessions in `auth_sessions`, sent as both an httponly cookie and a JSON token (SPA stores it in localStorage, sends `Authorization: Bearer`).
- Every analysis is saved to `uploads` (with `user_id` when signed in) → powers `/api/user/history`.
- `PremiumUnlock`/credits are legacy of a paywall era; the app is free now, code retained for Stripe re-enablement.
- No `DATABASE_URL` → all persistence no-ops; analysis still works.
- Engine uses `pool_pre_ping` (Postgres restarts don't surface as stale-connection errors); table creation retries lazily on first request if the DB wasn't up at boot.

## Configuration

All via env (see README table). Models are overridable: `OPENAI_MODEL` (analysis/OCR), `CLASSIFY_MODEL` (cheap classification). `MAX_DOC_CHARS` caps document text before prompt interpolation (default 15k, enforced on every LLM path including COI/extract). `CORS_ORIGINS` defaults to prod domains + localhost dev ports; production traffic is same-origin so CORS only matters for local dev.

## Security Notes

- SPA fallback resolves requested paths and confines them to `frontend/dist` (path-traversal guard in `main.py`, regression-tested).
- CORS is an explicit origin list (credentials mode), not a wildcard.
- Session tokens are 32-byte `secrets.token_urlsafe`; passwords bcrypt-hashed.
- Public endpoints enforce size ceilings (`services/limits.py`): document text > `MAX_INPUT_CHARS` and OCR uploads > `MAX_OCR_FILE_BYTES` are rejected with `413` before they're persisted, held in memory, or decoded; `/compare` caps quote count at `MAX_COMPARE_QUOTES`. The ceilings sit far above `MAX_DOC_CHARS` (the only text the model sees) so real documents are never refused. The analyzer guard lives in the shared `get_doc_context`, so every analyzer (plus the two-step COI/lease flows) inherits it. Malformed OCR base64 is a `400`, not a `500`.
- Per-IP rate limiting (`services/rate_limit.py`, wired as middleware in `main.py`) bounds request *frequency* — the size caps only bound a single request, leaving frequency abuse (LLM-cost run-up, login brute-force) open. A dependency-free in-process sliding-window limiter applies two tiers keyed by path: a strict tier (default 20/min) for the LLM-backed endpoints plus `auth/login`+`auth/signup`, and a default tier (120/min) for the rest of `/api/`. `/api/health` and the SPA routes are exempt. Over-limit requests get a `429` with a `Retry-After` header and a string `detail` (SPA-readable, and CORS-wrapped so cross-origin reads work). Client IP comes from `X-Forwarded-For` accounting for `RATE_LIMIT_TRUSTED_PROXIES` trusted hops (Caddy appends the real client as the last entry, so spoofed prefixes are ignored). In-process state is the right fit for the single-worker container; the tracked-IP table is LRU-bounded so it can't itself be exhausted. All thresholds are env-overridable; `RATE_LIMIT_ENABLED=false` turns it off (the offline + legacy test suites run with it off).

## Testing

- `backend/tests/` — offline pytest suite: all endpoints in mock mode, LLM helper units, traversal regression, size guards, and rate-limit units + middleware integration. Run: `cd backend && python -m pytest tests/`. (Limiting is disabled here via `conftest.py`; the rate-limit tests enable it explicitly with tiny limits.)
- `backend/test_api.py` — 29-test end-to-end script against a running server (mock or real). Run the server with `RATE_LIMIT_ENABLED=false` so the suite isn't throttled.
- `backend/test_expensive.py` — real OpenAI calls for prompt-quality spot checks.

## Deployment

`deploy.sh` → builds the multi-stage Dockerfile (Node builds the SPA; Python image serves it), pushes to the OVH VPS, restarts via `docker-compose.prod.yml` (app + Postgres 16 + volume). Caddy on the host owns TLS and proxies to :8081.
