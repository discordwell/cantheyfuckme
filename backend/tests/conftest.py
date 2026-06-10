"""Test fixtures.

The suite runs fully offline: MOCK_MODE replaces LLM calls with keyword-based
mocks, and DATABASE_URL is cleared so no Postgres is touched. Both must be
set before any app module is imported (config reads them at import time).
"""
import os
import sys
from pathlib import Path

os.environ["MOCK_MODE"] = "true"
# Empty string is falsy for `if DATABASE_URL:` and, because the key exists,
# load_dotenv() will not override it from a local .env file.
os.environ["DATABASE_URL"] = ""

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    from main import app
    return TestClient(app)
