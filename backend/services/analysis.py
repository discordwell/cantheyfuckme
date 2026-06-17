"""Shared plumbing for the document analyzer endpoints.

Every analyzer follows the same flow: hash the document, identify the user,
check premium access, produce a result dict (mock or LLM), persist the
upload, then build the typed report with the finalization fields set.
run_analysis owns that flow; endpoints supply only the pieces that differ.
"""
from typing import Callable, Optional, Sequence, Tuple, Type

from fastapi import Request
from pydantic import BaseModel

from config import MOCK_MODE
from services.auth import get_current_user, hash_document, check_premium_access
from services.db_ops import save_upload
from services.limits import check_text_size
from services.llm import llm_json_call


def get_doc_context(request: Request, text: str) -> Tuple[str, Optional[object], bool]:
    """Return (document_hash, current_user, is_premium) for a request.

    Every analyzer endpoint (plus the two-step COI and lease flows) resolves its
    context here first, so this is the single place that enforces the input-size
    ceiling for document text.
    """
    check_text_size(text)
    doc_hash = hash_document(text)
    user = get_current_user(request)
    is_premium = check_premium_access(user.id, doc_hash) if user else False
    return doc_hash, user, is_premium


def finalize_report(
    report_cls: Type[BaseModel],
    result: dict,
    *,
    doc_hash: str,
    is_premium: bool,
    issue_keys: Sequence[str],
) -> BaseModel:
    """Build the typed report and stamp the shared metadata fields."""
    report = report_cls(**result)
    report.document_hash = doc_hash
    report.is_premium = is_premium
    report.total_issues = sum(len(result.get(key) or []) for key in issue_keys)
    return report


def run_analysis(
    *,
    request: Request,
    text: str,
    doc_type: str,
    report_cls: Type[BaseModel],
    issue_keys: Sequence[str],
    mock_fn: Callable[[], dict],
    prompt_fn: Callable[[], str],
    state: Optional[str] = None,
    max_tokens: int = 4096,
) -> BaseModel:
    """Run a single-prompt analyzer end to end.

    mock_fn and prompt_fn are thunks so prompt construction only happens
    in the mode that needs it.
    """
    doc_hash, user, is_premium = get_doc_context(request, text)

    if MOCK_MODE:
        result = mock_fn()
    else:
        result = llm_json_call(prompt_fn(), max_tokens=max_tokens)

    save_upload(doc_type, text, state, result, user_id=user.id if user else None)

    return finalize_report(
        report_cls, result,
        doc_hash=doc_hash, is_premium=is_premium, issue_keys=issue_keys,
    )
