import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.environ.get("DATABASE_URL")

# Mock mode (for testing without API key)
MOCK_MODE = os.environ.get("MOCK_MODE", "false").lower() == "true"

# OpenAI
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.2")
# Cheaper/faster model for lightweight tasks like document classification
CLASSIFY_MODEL = os.environ.get("CLASSIFY_MODEL", "gpt-5.4-mini")

# Documents are truncated to this many characters before being sent to the LLM
MAX_DOC_CHARS = int(os.environ.get("MAX_DOC_CHARS", "15000"))

# Resource limits for public endpoints. The model only ever sees MAX_DOC_CHARS,
# so these ceilings sit far above any real document; they exist to reject
# abusive or accidental oversized payloads before we persist them, hold them in
# memory, or fan them out into per-item LLM calls.
#   MAX_INPUT_CHARS    - longest accepted document text (~1 MB; ~66x MAX_DOC_CHARS)
#   MAX_OCR_FILE_BYTES - largest accepted OCR upload, measured after base64 decode
#   MAX_COMPARE_QUOTES - most quotes /compare will extract in one request
MAX_INPUT_CHARS = int(os.environ.get("MAX_INPUT_CHARS", "1000000"))
MAX_OCR_FILE_BYTES = int(os.environ.get("MAX_OCR_FILE_BYTES", str(15 * 1024 * 1024)))
MAX_COMPARE_QUOTES = int(os.environ.get("MAX_COMPARE_QUOTES", "10"))

# Per-client-IP rate limiting. Size caps above only bound a *single* request;
# this bounds request *frequency* so a script cannot run up OpenAI spend (or
# brute-force logins) by firing many normal-sized requests. Two tiers keyed by
# path: the strict tier covers the LLM-backed (costly) endpoints plus auth
# (bcrypt is CPU-heavy and a brute-force target); the default tier covers
# everything else under /api/ (reference lookups, history, waitlist, logout).
# Limits are per RATE_LIMIT_*_WINDOW seconds and sit well above real human use.
RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS", "120"))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_STRICT_REQUESTS = int(os.environ.get("RATE_LIMIT_STRICT_REQUESTS", "20"))
RATE_LIMIT_STRICT_WINDOW = int(os.environ.get("RATE_LIMIT_STRICT_WINDOW", "60"))

# Endpoints subject to the strict tier (prefix match). Override with a
# comma-separated list of path prefixes.
RATE_LIMIT_STRICT_PREFIXES = tuple(
    prefix.strip()
    for prefix in os.environ.get(
        "RATE_LIMIT_STRICT_PREFIXES",
        "/api/analyze-,/api/check-coi-compliance,/api/ocr,/api/extract,"
        "/api/compare,/api/classify,/api/generate-proposal,"
        "/api/auth/login,/api/auth/signup",
    ).split(",")
    if prefix.strip()
)

# Number of trusted reverse proxies in front of the app. The documented
# deployment is one Caddy hop, which appends the real client IP as the LAST
# X-Forwarded-For entry, so the true client is the RATE_LIMIT_TRUSTED_PROXIES-th
# entry from the right. Set to 0 to ignore X-Forwarded-For and use the socket
# peer directly (correct for local/no-proxy runs); raise it if you add another
# proxy (e.g. Cloudflare) in front of Caddy.
RATE_LIMIT_TRUSTED_PROXIES = int(os.environ.get("RATE_LIMIT_TRUSTED_PROXIES", "1"))

# Cap on distinct client IPs tracked at once (LRU eviction beyond this), so the
# limiter's own bookkeeping can't be turned into a memory-exhaustion vector by
# rotating source IPs.
RATE_LIMIT_MAX_TRACKED_IPS = int(os.environ.get("RATE_LIMIT_MAX_TRACKED_IPS", "20000"))

# CORS: production is same-origin (frontend served by this app behind Caddy),
# so this list only needs the prod domains plus local dev servers.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ORIGINS",
        "https://cantheyfuckme.com,https://www.cantheyfuckme.com,"
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173,"
        "http://localhost:8081,http://127.0.0.1:8081",
    ).split(",")
    if origin.strip()
]

# Stripe
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_UNLOCK = os.environ.get("STRIPE_PRICE_UNLOCK", "price_unlock_3usd")

def get_api_key():
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith("OPENAI_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    if key:
                        return key
    home_config = Path.home() / ".openai" / "api_key"
    if home_config.exists():
        return home_config.read_text().strip()
    return None
