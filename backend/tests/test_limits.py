"""Tests for the request-size guards on public endpoints (services/limits.py).

Oversized document text and OCR uploads are rejected with 413 before any
DB / LLM / decode work happens; malformed base64 is a 400 rather than a 500.
All of this runs offline in MOCK_MODE.
"""
from config import MAX_INPUT_CHARS, MAX_COMPARE_QUOTES

import routers.documents as documents
import services.limits as limits

# One character past the ceiling: the smallest input that must be rejected.
OVERSIZED = "A" * (MAX_INPUT_CHARS + 1)


# ---------- document text caps (analyzers + COI + lease share get_doc_context) ----------

def test_analyzer_rejects_oversized_text(client):
    response = client.post("/api/analyze-gym", json={"contract_text": OVERSIZED, "state": "CA"})
    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


def test_coi_rejects_oversized_text(client):
    response = client.post("/api/check-coi-compliance", json={"coi_text": OVERSIZED})
    assert response.status_code == 413


def test_lease_rejects_oversized_text(client):
    response = client.post("/api/analyze-lease", json={"lease_text": OVERSIZED, "state": "NY"})
    assert response.status_code == 413


def test_text_at_limit_is_accepted(client):
    # The boundary itself must pass: exactly MAX_INPUT_CHARS is allowed.
    response = client.post("/api/analyze-gym", json={"contract_text": "A" * MAX_INPUT_CHARS})
    assert response.status_code == 200


# ---------- documents router ----------

def test_extract_rejects_oversized_text(client):
    response = client.post("/api/extract", json={"text": OVERSIZED})
    assert response.status_code == 413


def test_classify_rejects_oversized_text(client):
    response = client.post("/api/classify", json={"text": OVERSIZED})
    assert response.status_code == 413


def test_compare_rejects_too_many_quotes(client):
    quotes = [{"text": "quote"} for _ in range(MAX_COMPARE_QUOTES + 1)]
    response = client.post("/api/compare", json=quotes)
    assert response.status_code == 400
    assert "too many" in response.json()["detail"].lower()


def test_compare_rejects_oversized_quote(client):
    response = client.post("/api/compare", json=[{"text": "ok"}, {"text": OVERSIZED}])
    assert response.status_code == 413


# ---------- OCR ----------

def test_ocr_rejects_oversized_file(client, monkeypatch):
    # Shrink the byte ceiling so the test stays fast instead of POSTing ~20 MB.
    monkeypatch.setattr(limits, "MAX_OCR_FILE_BYTES", 100)
    response = client.post("/api/ocr", json={
        "file_data": "A" * 200,  # decodes to ~150 bytes, over the 100-byte cap
        "file_type": "image/png",
        "file_name": "x.png",
    })
    assert response.status_code == 413


def test_ocr_rejects_invalid_base64(client, monkeypatch):
    # Real mode reaches the decode; malformed base64 should be a 400, not a 500.
    # The decode raises before get_client() is reached, so no client stub needed.
    monkeypatch.setattr(documents, "MOCK_MODE", False)
    response = client.post("/api/ocr", json={
        "file_data": "!!! not valid base64 !!!",
        "file_type": "image/png",
        "file_name": "x.png",
    })
    assert response.status_code == 400


def test_ocr_accepts_whitespace_wrapped_base64(client, monkeypatch):
    # Regression: validate=True must not reject newline-wrapped base64 (e.g. the
    # 76-column MIME encoding `base64.encodebytes` emits) that the old lenient
    # decode accepted. The handler normalizes whitespace before decoding.
    import base64

    class _Msg:
        content = "decoded text"

    class _Completions:
        def create(self, **kwargs):
            return type("R", (), {"choices": [type("C", (), {"message": _Msg()})()]})()

    fake_client = type("Client", (), {
        "chat": type("Chat", (), {"completions": _Completions()})()
    })()

    monkeypatch.setattr(documents, "MOCK_MODE", False)
    monkeypatch.setattr(documents, "get_client", lambda: fake_client)

    wrapped = base64.encodebytes(b"fake image bytes " * 8).decode()
    assert "\n" in wrapped  # encodebytes wraps at 76 cols
    response = client.post("/api/ocr", json={
        "file_data": wrapped,
        "file_type": "image/png",
        "file_name": "x.png",
    })
    assert response.status_code == 200
    assert response.json()["text"] == "decoded text"
