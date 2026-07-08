"""Tests for OCR multi-page handling (routers/documents.py:ocr_document).

A multi-page PDF is OCR'd one vision call per page, so only the first
MAX_OCR_PDF_PAGES are processed. These tests assert that the cap is honored,
that exactly that many vision calls are made (no wasted spend on dropped
pages), and — critically — that the response reports total_pages /
pages_processed / truncated so the UI can warn the user that the back of a long
document was not analyzed instead of presenting a confident partial verdict.

The real (non-mock) path is exercised by flipping the router module's MOCK_MODE
binding off and stubbing get_client with a fake that returns canned page text,
so no network or API key is needed. PDFs are built in-memory with PyMuPDF.
"""
import base64
import threading

import fitz  # PyMuPDF (a production dependency)

import routers.documents as documents


def _make_pdf_b64(num_pages: int) -> str:
    """Build a real `num_pages`-page PDF and return it base64-encoded."""
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"Page {i + 1} body text")
    pdf_bytes = doc.tobytes()
    doc.close()
    return base64.b64encode(pdf_bytes).decode("ascii")


class _CountingClient:
    """Fake OpenAI client: counts create() calls, returns canned page text.

    Counting is locked because the endpoint fans page calls out across
    threads; the count must stay exact under concurrency.
    """

    def __init__(self):
        self.calls = 0
        self._lock = threading.Lock()

        class _Completions:
            def create(_self, **kwargs):
                with self._lock:
                    self.calls += 1
                    content = f"OCR TEXT {self.calls}"
                message = type("Msg", (), {"content": content})()
                choice = type("Choice", (), {"message": message})()
                return type("Resp", (), {"choices": [choice]})()

        self.chat = type("Chat", (), {"completions": _Completions()})()


def _post_pdf(client, num_pages):
    return client.post("/api/ocr", json={
        "file_data": _make_pdf_b64(num_pages),
        "file_type": "application/pdf",
        "file_name": f"{num_pages}page.pdf",
    })


def test_ocr_pdf_truncates_long_document_and_reports_it(client, monkeypatch):
    # A 7-page PDF with the default cap of 5: pages 6-7 must be dropped, the
    # caller must be told, and only 5 (paid) vision calls may be made.
    fake = _CountingClient()
    monkeypatch.setattr(documents, "MOCK_MODE", False)
    monkeypatch.setattr(documents, "MAX_OCR_PDF_PAGES", 5)
    monkeypatch.setattr(documents, "get_client", lambda: fake)

    response = _post_pdf(client, 7)
    assert response.status_code == 200
    data = response.json()

    assert data["total_pages"] == 7
    assert data["pages_processed"] == 5
    assert data["truncated"] is True
    assert fake.calls == 5  # no vision spend on the dropped pages
    # Multi-page extractions are labeled so the user can see where text ends.
    assert "--- Page 1 ---" in data["text"]
    assert "--- Page 5 ---" in data["text"]
    assert "--- Page 6 ---" not in data["text"]


def test_ocr_pdf_within_cap_is_not_truncated(client, monkeypatch):
    fake = _CountingClient()
    monkeypatch.setattr(documents, "MOCK_MODE", False)
    monkeypatch.setattr(documents, "MAX_OCR_PDF_PAGES", 5)
    monkeypatch.setattr(documents, "get_client", lambda: fake)

    response = _post_pdf(client, 3)
    assert response.status_code == 200
    data = response.json()

    assert data["total_pages"] == 3
    assert data["pages_processed"] == 3
    assert data["truncated"] is False
    assert fake.calls == 3


def test_ocr_pdf_respects_configured_page_cap(client, monkeypatch):
    # The cap is env-overridable (MAX_OCR_PDF_PAGES); a tighter cap truncates
    # sooner and processes fewer pages.
    fake = _CountingClient()
    monkeypatch.setattr(documents, "MOCK_MODE", False)
    monkeypatch.setattr(documents, "MAX_OCR_PDF_PAGES", 2)
    monkeypatch.setattr(documents, "get_client", lambda: fake)

    response = _post_pdf(client, 4)
    assert response.status_code == 200
    data = response.json()

    assert data["pages_processed"] == 2
    assert data["total_pages"] == 4
    assert data["truncated"] is True
    assert fake.calls == 2


def test_ocr_single_page_pdf_has_no_page_headers(client, monkeypatch):
    # A 1-page PDF should not get "--- Page 1 ---" framing (matches prior behavior).
    fake = _CountingClient()
    monkeypatch.setattr(documents, "MOCK_MODE", False)
    monkeypatch.setattr(documents, "MAX_OCR_PDF_PAGES", 5)
    monkeypatch.setattr(documents, "get_client", lambda: fake)

    response = _post_pdf(client, 1)
    assert response.status_code == 200
    data = response.json()

    assert data["total_pages"] == 1
    assert data["truncated"] is False
    assert "--- Page" not in data["text"]


def test_ocr_corrupt_pdf_is_rejected_as_400_before_any_vision_spend(client, monkeypatch):
    # Garbage bytes wearing a PDF content-type are the uploader's problem, not
    # a server fault: 400 (not 500), and no paid vision calls for it.
    fake = _CountingClient()
    monkeypatch.setattr(documents, "MOCK_MODE", False)
    monkeypatch.setattr(documents, "get_client", lambda: fake)

    response = client.post("/api/ocr", json={
        "file_data": base64.b64encode(b"this is not a pdf at all").decode("ascii"),
        "file_type": "application/pdf",
        "file_name": "garbage.pdf",
    })
    assert response.status_code == 400
    assert "pdf" in response.json()["detail"].lower()
    assert fake.calls == 0


def test_ocr_password_protected_pdf_is_rejected_as_400(client, monkeypatch):
    # An encrypted PDF renders as blank/error pages; tell the user to remove
    # the password instead of burning vision calls on unreadable pages.
    fake = _CountingClient()
    monkeypatch.setattr(documents, "MOCK_MODE", False)
    monkeypatch.setattr(documents, "get_client", lambda: fake)

    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "secret contract")
    pdf_bytes = doc.tobytes(
        encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="hunter2", owner_pw="hunter2"
    )
    doc.close()

    response = client.post("/api/ocr", json={
        "file_data": base64.b64encode(pdf_bytes).decode("ascii"),
        "file_type": "application/pdf",
        "file_name": "locked.pdf",
    })
    assert response.status_code == 400
    assert "password" in response.json()["detail"].lower()
    assert fake.calls == 0


def test_ocr_image_reports_single_page(client, monkeypatch):
    # Images are a single page and never truncate; the response carries the same
    # fields as the PDF path for a uniform client contract.
    class _Msg:
        content = "decoded image text"

    class _Completions:
        def create(self, **kwargs):
            return type("R", (), {"choices": [type("C", (), {"message": _Msg()})()]})()

    fake_client = type("Client", (), {
        "chat": type("Chat", (), {"completions": _Completions()})()
    })()

    monkeypatch.setattr(documents, "MOCK_MODE", False)
    monkeypatch.setattr(documents, "get_client", lambda: fake_client)

    response = client.post("/api/ocr", json={
        "file_data": base64.b64encode(b"fake png bytes").decode("ascii"),
        "file_type": "image/png",
        "file_name": "x.png",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "decoded image text"
    assert data["total_pages"] == 1
    assert data["pages_processed"] == 1
    assert data["truncated"] is False
