"""The API must stay responsive while slow blocking work is in flight.

Production runs a single uvicorn worker: one event loop. The OpenAI client,
SQLAlchemy, and bcrypt are all synchronous/blocking, so an ``async def``
endpoint that calls them pins the loop and stalls EVERY in-flight request -
health checks included - for the duration of, say, a 30-second multi-page OCR.
Endpoints that do blocking work are therefore deliberately plain ``def`` so
FastAPI runs them in its worker threadpool. These tests pin the contract and
the observable behavior:

- No /api endpoint outside a small allowlist may be a coroutine function.
- A slow LLM call must not delay an unrelated /api/health request.
- A multi-page OCR fans its per-page vision calls out concurrently.
"""
import asyncio
import base64
import threading
import time

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

import routers.documents as documents
from main import app

# The only /api endpoints allowed to run on the event loop:
#   /api/health         - liveness must answer even when every worker thread
#                         is busy with slow analyses; it does no blocking work.
#   /api/stripe-webhook - needs `await request.body()` for signature
#                         verification; its DB work hops to the threadpool.
_ASYNC_ALLOWED = {"/api/health", "/api/stripe-webhook"}


def test_no_api_endpoint_blocks_the_event_loop_by_contract():
    checked = 0
    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith("/api"):
            continue
        checked += 1
        if route.path in _ASYNC_ALLOWED:
            assert asyncio.iscoroutinefunction(route.endpoint), (
                f"{route.path} is allowlisted as async but is not a coroutine; "
                "update _ASYNC_ALLOWED if it was intentionally made sync"
            )
        else:
            assert not asyncio.iscoroutinefunction(route.endpoint), (
                f"{route.path} is `async def`, but this API's work (LLM calls, "
                "DB, bcrypt) is blocking and would pin the single event loop, "
                "stalling every other request. Declare it plain `def` so it "
                "runs in the threadpool, or add it to _ASYNC_ALLOWED with a "
                "reason if it truly never blocks."
            )
    # The whole API surface must actually have been inspected.
    assert checked >= 30


class _SleepyClient:
    """Fake OpenAI client whose create() blocks, like a real network call."""

    def __init__(self, delay: float):
        self.delay = delay
        self.calls = 0
        self._lock = threading.Lock()
        outer = self

        class _Completions:
            def create(_self, **kwargs):
                with outer._lock:
                    outer.calls += 1
                time.sleep(outer.delay)
                message = type("Msg", (), {"content": "ocr text"})()
                choice = type("Choice", (), {"message": message})()
                return type("Resp", (), {"choices": [choice]})()

        self.chat = type("Chat", (), {"completions": _Completions()})()


def _image_payload():
    return {
        "file_data": base64.b64encode(b"fake png bytes").decode("ascii"),
        "file_type": "image/png",
        "file_name": "slow.png",
    }


def test_health_stays_responsive_during_a_slow_llm_call(monkeypatch):
    delay = 1.5
    monkeypatch.setattr(documents, "MOCK_MODE", False)
    monkeypatch.setattr(documents, "get_client", lambda: _SleepyClient(delay))

    # Entered as a context manager, TestClient keeps ONE portal (one event
    # loop) for all requests - matching the single-worker production topology.
    with TestClient(app) as client:
        ocr_result = {}

        def slow_ocr():
            ocr_result["response"] = client.post("/api/ocr", json=_image_payload())

        worker = threading.Thread(target=slow_ocr)
        worker.start()
        time.sleep(0.3)  # let the OCR request reach its blocking vision call

        start = time.monotonic()
        health = client.get("/api/health")
        health_elapsed = time.monotonic() - start
        worker.join()

    assert health.status_code == 200
    assert ocr_result["response"].status_code == 200
    # With the loop pinned, health could not have answered before the vision
    # call finished (~delay). Half the delay is a generous CI margin.
    assert health_elapsed < delay / 2, (
        f"/api/health took {health_elapsed:.2f}s during a {delay}s LLM call - "
        "the event loop is being blocked by an endpoint doing blocking work"
    )


def test_ocr_pdf_pages_fan_out_concurrently(client, monkeypatch):
    # 3 pages at 0.5s per vision call: the old sequential loop needed >= 1.5s;
    # the fan-out should finish in roughly one call's time. The 1.2s ceiling
    # is a generous CI margin that still rules out serial execution.
    import fitz  # PyMuPDF (a production dependency)

    per_page = 0.5
    fake = _SleepyClient(per_page)
    monkeypatch.setattr(documents, "MOCK_MODE", False)
    monkeypatch.setattr(documents, "MAX_OCR_PDF_PAGES", 5)
    monkeypatch.setattr(documents, "get_client", lambda: fake)

    doc = fitz.open()
    for i in range(3):
        doc.new_page().insert_text((72, 72), f"Page {i + 1} body text")
    pdf_b64 = base64.b64encode(doc.tobytes()).decode("ascii")
    doc.close()

    start = time.monotonic()
    response = client.post("/api/ocr", json={
        "file_data": pdf_b64,
        "file_type": "application/pdf",
        "file_name": "3page.pdf",
    })
    wall = time.monotonic() - start

    assert response.status_code == 200
    assert fake.calls == 3
    data = response.json()
    # Page labels are attached by index after collection, so order survives
    # the concurrent fan-out.
    assert "--- Page 1 ---" in data["text"]
    assert "--- Page 3 ---" in data["text"]
    assert wall < per_page * 3 * 0.8, (
        f"3-page OCR took {wall:.2f}s at {per_page}s/page - pages are being "
        "processed sequentially instead of concurrently"
    )
