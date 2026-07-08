import logging
import math
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from config import (
    CORS_ORIGINS,
    RATE_LIMIT_ENABLED,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW,
    RATE_LIMIT_STRICT_REQUESTS,
    RATE_LIMIT_STRICT_WINDOW,
    RATE_LIMIT_STRICT_PREFIXES,
    RATE_LIMIT_TRUSTED_PROXIES,
    RATE_LIMIT_MAX_TRACKED_IPS,
)
from database import init_db
from routers import auth, payments, documents, analyzers, reference, waitlist
from services.rate_limit import SlidingWindowRateLimiter, get_client_ip

# Make app module logs (INFO+) visible alongside uvicorn's own logging.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# Initialize database on startup
init_db()

app = FastAPI(
    title="Can They Fuck Me?",
    description="AI contract analysis: find the clauses designed to screw you before you sign",
)

# Per-IP rate limiters. The strict tier guards the costly LLM endpoints (and
# auth) while the default tier covers the rest of /api/. Both are module globals
# so tests can swap in tighter limits without re-importing.
_strict_limiter = SlidingWindowRateLimiter(
    RATE_LIMIT_STRICT_REQUESTS, RATE_LIMIT_STRICT_WINDOW,
    max_tracked_keys=RATE_LIMIT_MAX_TRACKED_IPS,
)
_default_limiter = SlidingWindowRateLimiter(
    RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW,
    max_tracked_keys=RATE_LIMIT_MAX_TRACKED_IPS,
)

# API paths that must never be throttled:
#   /api/health         - liveness probes would otherwise trip the limiter.
#   /api/stripe-webhook - Stripe deliveries are signature-authenticated (no abuse
#       upside to limiting) and arrive from a small set of Stripe egress IPs that
#       share one bucket, so a 429 would drop legitimate payment events.
_RATE_LIMIT_EXEMPT_PATHS = frozenset({"/api/health", "/api/stripe-webhook"})


# Registered before CORS so that CORSMiddleware ends up outermost (Starlette runs
# the most-recently-added middleware first); a 429 returned here then still gets
# CORS headers, so a cross-origin SPA can read its detail message.
@app.middleware("http")
async def rate_limit_requests(request: Request, call_next):
    path = request.url.path
    # Only meter the API surface; static SPA assets and the exempt paths above
    # stay unthrottled.
    if RATE_LIMIT_ENABLED and path.startswith("/api/") and path not in _RATE_LIMIT_EXEMPT_PATHS:
        client_ip = get_client_ip(request, RATE_LIMIT_TRUSTED_PROXIES)
        limiter = _strict_limiter if path.startswith(RATE_LIMIT_STRICT_PREFIXES) else _default_limiter
        retry_after = limiter.check(client_ip)
        if retry_after is not None:
            wait = max(1, math.ceil(retry_after))
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded. Try again in {wait} second{'s' if wait != 1 else ''}."},
                headers={"Retry-After": str(wait)},
            )
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router)
app.include_router(payments.router)
app.include_router(documents.router)
app.include_router(analyzers.router)
app.include_router(reference.router)
app.include_router(waitlist.router)


# Deliberately async (the rest of the API is plain `def` so blocking LLM/DB
# work runs in the threadpool): liveness runs on the event loop itself, so it
# answers instantly even when every worker thread is busy with slow analyses.
@app.get("/api/health")
async def health():
    return {"message": "cantheyfuckme.com API", "status": "running"}


# Serve built frontend if present (production Docker build)
FRONTEND_DIR = (Path(__file__).parent.parent / "frontend" / "dist").resolve()
if FRONTEND_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        # Resolve and confine to the dist directory so crafted paths
        # (e.g. /../backend/.env) cannot escape it.
        file = (FRONTEND_DIR / path).resolve()
        if file.is_file() and file.is_relative_to(FRONTEND_DIR):
            return FileResponse(file)
        return FileResponse(FRONTEND_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
