"""Tests for the SPA static-file fallback, including path-traversal containment.

The fallback route only exists when frontend/dist has been built, so these
tests skip on a backend-only checkout.
"""
import asyncio
from pathlib import Path

import pytest

import main


needs_dist = pytest.mark.skipif(
    not hasattr(main, "serve_frontend"),
    reason="frontend/dist not built; SPA fallback route not registered",
)


@needs_dist
def test_serves_index_for_unknown_path(client):
    response = client.get("/some/spa/route")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


@needs_dist
def test_traversal_path_falls_back_to_index():
    # Bypass client-side URL normalization by invoking the handler directly,
    # as uvicorn would for a raw "GET /../../backend/config.py" request.
    response = asyncio.run(main.serve_frontend("../../backend/config.py"))
    assert Path(response.path).name == "index.html"


@needs_dist
def test_traversal_never_escapes_dist():
    for attempt in (
        "../backend/.env",
        "../../backend/.env",
        "..%2F..%2Fbackend%2F.env",
        "assets/../../backend/main.py",
    ):
        response = asyncio.run(main.serve_frontend(attempt))
        resolved = Path(response.path).resolve()
        assert resolved.is_relative_to(main.FRONTEND_DIR), attempt


@needs_dist
def test_serves_real_files_inside_dist():
    response = asyncio.run(main.serve_frontend("index.html"))
    assert Path(response.path) == main.FRONTEND_DIR / "index.html"
