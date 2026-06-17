"""Size guards for public, user-supplied request bodies.

The analyzers only ever feed MAX_DOC_CHARS of text to the model, but the raw
payload is still parsed into memory, persisted to the database, and (for OCR)
base64-decoded and rendered before any truncation happens. Without a ceiling a
single oversized request can balloon memory use, DB writes, or LLM spend. These
helpers reject such input early with a clean 413 whose string ``detail`` the SPA
surfaces directly (it reads ``data.detail`` off error responses).
"""
from fastapi import HTTPException

from config import MAX_INPUT_CHARS, MAX_OCR_FILE_BYTES


def check_text_size(text: str, *, label: str = "Document") -> None:
    """Reject document text longer than MAX_INPUT_CHARS characters (413)."""
    if text and len(text) > MAX_INPUT_CHARS:
        raise HTTPException(
            status_code=413,
            detail=(
                f"{label} too large: {len(text):,} characters "
                f"(maximum {MAX_INPUT_CHARS:,})."
            ),
        )


def check_ocr_file_size(file_data: str) -> None:
    """Reject base64 OCR uploads whose decoded size exceeds MAX_OCR_FILE_BYTES (413).

    base64 expands bytes by ~4/3, so the decoded length is about 3/4 of the
    encoded string. Checking that estimate up front means we never materialize
    an oversized blob in memory just to measure it.
    """
    approx_bytes = (len(file_data) * 3) // 4
    if approx_bytes > MAX_OCR_FILE_BYTES:
        max_mb = MAX_OCR_FILE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=(
                f"File too large: ~{approx_bytes // (1024 * 1024)} MB "
                f"(maximum {max_mb} MB)."
            ),
        )
