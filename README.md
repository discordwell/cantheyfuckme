# CAN THEY FUCK ME?

> paste the contract → find out how they fuck you | [cantheyfuckme.com](https://cantheyfuckme.com)

A retro-styled, AI-powered contract analyzer for consumers. Paste (or upload) a contract before you sign it and get a plain-English breakdown of the clauses designed to screw you — with severity ratings, state-specific law references, and what to do about each one.

Free to use. No paywall. Optional sign-in saves your analysis history.

![Williamsburg 2015 vibes](https://img.shields.io/badge/aesthetic-williamsburg%202015-ff6b6b?style=flat-square)
![Python](https://img.shields.io/badge/python-3.12-4ecdc4?style=flat-square)
![TypeScript](https://img.shields.io/badge/typescript-5.0+-4ecdc4?style=flat-square)

## What It Analyzes

| Document | What it catches |
|----------|-----------------|
| Gym/fitness memberships | in-person-only cancellation, auto-renew traps, annual fees |
| Apartment & commercial leases | one-sided indemnification, waived protections, personal guaranties |
| Employment contracts | non-competes (with state enforceability), arbitration, IP overreach |
| Freelancer agreements | net-90 payment, unlimited revisions, work-for-hire overreach |
| Influencer/sponsorship deals | perpetual usage rights, category exclusivity |
| Timeshares | rescission deadlines by state, perpetuity clauses, fee escalators |
| Insurance policies | exclusions, ACV-vs-replacement traps, anti-concurrent causation |
| Auto purchase contracts | doc fee caps by state, yo-yo financing, junk add-ons |
| Home improvement contracts | mechanics liens, deposit limits, missing completion dates |
| Nursing home admissions | illegal responsible-party clauses, forced arbitration |
| Subscriptions/SaaS | auto-renewal dark patterns, cancellation friction |
| Debt settlements | statute-of-limitations restarts, missing paid-in-full language |
| Certificates of Insurance | coverage gaps vs. contract requirements (COI compliance) |

Documents are auto-classified on paste; PDFs and images go through vision OCR first.

## The Stack

- **Frontend**: React + TypeScript + Vite (Press Start 2P, VT323, CRT scanlines)
- **Backend**: Python 3.12 + FastAPI
- **AI**: OpenAI API (`OPENAI_MODEL` for analysis, `CLASSIFY_MODEL` for cheap classification)
- **Database**: PostgreSQL 16 (optional — runs without it, minus history/auth)
- **Hosting**: Docker Compose on a VPS behind Caddy (TLS)

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Either set a real key...
export OPENAI_API_KEY=your_key_here
# ...or run fully offline with keyword-based mock analysis
export MOCK_MODE=true

python main.py        # serves http://localhost:8081
```

### Frontend

```bash
cd frontend
npm install
npm run dev           # serves http://localhost:5173, talks to :8081
```

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | — | Required unless `MOCK_MODE=true` |
| `MOCK_MODE` | `false` | Keyword-based mock analysis, no API calls |
| `OPENAI_MODEL` | `gpt-5.2` | Main analysis + OCR model |
| `CLASSIFY_MODEL` | `gpt-5.4-mini` | Cheap document-type classification |
| `DATABASE_URL` | — | Postgres; omit to run without persistence |
| `CORS_ORIGINS` | prod + localhost | Comma-separated allowed origins |
| `MAX_DOC_CHARS` | `15000` | Document text cap before LLM prompts |
| `MAX_INPUT_CHARS` | `1000000` | Reject document text longer than this (HTTP 413) before persisting/processing |
| `MAX_OCR_FILE_BYTES` | `15728640` | Reject OCR uploads larger than this (measured after base64 decode) |
| `MAX_COMPARE_QUOTES` | `10` | Max quotes `/compare` will extract in one request |
| `RATE_LIMIT_ENABLED` | `true` | Per-IP request-frequency limiting (set `false` to disable) |
| `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW` | `120` / `60` | Default tier: requests per window-seconds for non-LLM `/api/` routes |
| `RATE_LIMIT_STRICT_REQUESTS` / `RATE_LIMIT_STRICT_WINDOW` | `20` / `60` | Strict tier: requests per window-seconds for LLM + auth routes |
| `RATE_LIMIT_TRUSTED_PROXIES` | `1` | Reverse-proxy hops in front of the app (one Caddy hop); set `0` for no proxy |
| `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` | — | Legacy credit purchases (unused; donations use a payment link) |

## API

All analyzer endpoints accept JSON and return a typed report with `overall_risk`, `risk_score`, `red_flags[]`, and document metadata.

| Endpoint | Description |
|----------|-------------|
| `POST /api/classify` | Detect document type |
| `POST /api/ocr` | PDF/image → text (vision) |
| `POST /api/analyze-{lease,gym,employment,freelancer,influencer,timeshare,insurance-policy,auto-purchase,home-improvement,nursing-home,subscription,debt-settlement}` | Contract analysis |
| `POST /api/check-coi-compliance` | COI vs. project requirements |
| `POST /api/auth/{signup,login,logout}`, `GET /api/auth/me` | Optional accounts |
| `GET /api/user/history` | Saved analyses |
| `GET /api/{states,project-types}` | Reference data |
| `POST /api/waitlist` | Request a new document type |
| `GET /api/health` | Liveness |

## Testing

```bash
cd backend
pip install -r requirements-dev.txt

# Offline suite: mock mode, no DB, no API key needed
python -m pytest tests/

# Legacy end-to-end suite against a running server.
# Disable rate limiting: the suite fires more LLM-endpoint calls per minute than
# the production per-IP ceiling, so it would otherwise throttle itself.
MOCK_MODE=true RATE_LIMIT_ENABLED=false python main.py &
python test_api.py
```

`test_expensive.py` exercises real LLM calls and costs money — run deliberately.

## Deployment

`./deploy.sh` builds the Docker image (frontend build baked in, served by FastAPI), ships it to the VPS, and restarts via `docker-compose.prod.yml`. Caddy terminates TLS for `cantheyfuckme.com` and reverse-proxies to port 8081.

## Disclaimer

This is automated document analysis, not legal advice. For decisions that matter, talk to a lawyer licensed in your state.

## License

MIT
