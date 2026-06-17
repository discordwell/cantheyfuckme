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
