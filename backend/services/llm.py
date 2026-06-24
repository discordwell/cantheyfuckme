import json
from typing import Optional

from openai import OpenAI
from fastapi import HTTPException

from config import get_api_key, MOCK_MODE, OPENAI_MODEL


# Lazy client initialization
_client = None


def get_client():
    global _client
    if MOCK_MODE:
        return None  # Mock mode doesn't need a client
    if _client is None:
        api_key = get_api_key()
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY not configured. Set it in environment, .env file, or ~/.openai/api_key"
            )
        _client = OpenAI(api_key=api_key)
    return _client


def clean_llm_response(response_text: str) -> str:
    """Clean up potential markdown formatting from LLM JSON responses.

    Handles the common pattern where LLMs wrap JSON in ```json``` code blocks.
    """
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    return response_text.strip()


def llm_text_call(prompt: str, *, model: str = None, max_tokens: int = 4096, system: str = None) -> str:
    """Send a single prompt to the LLM and return the cleaned text response."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = get_client().chat.completions.create(
        model=model or OPENAI_MODEL,
        max_completion_tokens=max_tokens,
        messages=messages,
    )

    content = response.choices[0].message.content
    if not content:
        raise HTTPException(status_code=502, detail="Empty response from language model")
    return clean_llm_response(content)


def _extract_json_object(text: str) -> Optional[str]:
    """Return the first balanced ``{...}`` span in ``text``, or None.

    Recovery path for ``loads_json_lenient``: the prompts tell the model to
    return only JSON, but it occasionally wraps the object in a sentence of
    preamble, a trailing sign-off, or a stray markdown fence. We locate the
    first ``{`` and walk to its matching ``}``, tracking string literals and
    escapes so braces inside a string value (e.g. a clause quoted in
    ``clause_text``) don't throw off the depth count. Every analyzer/extraction
    prompt returns a JSON *object*, so targeting objects is sufficient and can't
    be fooled by a stray ``[`` in prose. Returns None when there is no ``{`` or
    the braces never balance (truncated output), so the caller surfaces the
    original parse error rather than a half-object.
    """
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def loads_json_lenient(text: str):
    """Parse JSON from an LLM response, tolerating prose around the object.

    The happy path is a direct ``json.loads`` (handles plain or already
    de-fenced JSON, including string values that contain braces). Only when that
    fails — almost always because the model added a preamble, a trailing remark,
    or a code fence around an otherwise-valid object — do we fall back to
    extracting the first balanced ``{...}`` span and parsing that. Raises
    ``json.JSONDecodeError`` if neither yields valid JSON, so each caller chooses
    how to surface it: a 500 for the analyzers, a graceful "unknown" for
    classification.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        span = _extract_json_object(text)
        if span is not None and span != text:
            return json.loads(span)  # propagates JSONDecodeError if still invalid
        raise


def llm_json_call(prompt: str, *, model: str = None, max_tokens: int = 4096, system: str = None) -> dict:
    """Send a single prompt to the LLM and parse the JSON response.

    Parsing is lenient (see ``loads_json_lenient``): a model that wraps its JSON
    in a line of prose or a markdown fence still succeeds instead of 500-ing the
    whole analysis, which is the single path every analyzer depends on.
    """
    text = llm_text_call(prompt, model=model, max_tokens=max_tokens, system=system)
    try:
        return loads_json_lenient(text)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse response: {str(e)}")


def parse_limit_to_number(limit_str: str) -> int:
    """Parse a limit string like '$1,000,000' or '$1M' to an integer"""
    if not limit_str:
        return 0
    # Remove $ and commas
    cleaned = limit_str.replace('$', '').replace(',', '').strip().upper()
    # Handle M for million, K for thousand
    if 'M' in cleaned:
        try:
            return int(float(cleaned.replace('M', '')) * 1000000)
        except (ValueError, OverflowError):
            return 0
    if 'K' in cleaned:
        try:
            return int(float(cleaned.replace('K', '')) * 1000)
        except (ValueError, OverflowError):
            return 0
    try:
        return int(cleaned)
    except (ValueError, OverflowError):
        return 0


def calculate_extraction_confidence(coi_data: dict) -> dict:
    """Calculate overall extraction confidence and determine if human review is needed"""
    confidence_data = coi_data.get('confidence', {})

    # Critical fields that need confidence assessment
    critical_fields = [
        'gl_limit_per_occurrence',
        'gl_limit_aggregate',
        'additional_insured_checked',
        'waiver_of_subrogation_checked',
        'cg_20_10_endorsement',
        'cg_20_37_endorsement'
    ]

    # Calculate confidence scores
    confidence_scores = []
    low_confidence_fields = []
    review_reasons = []

    for field in critical_fields:
        field_conf = confidence_data.get(field, {})
        level = field_conf.get('level', 'low') if isinstance(field_conf, dict) else 'low'

        if level == 'high':
            confidence_scores.append(1.0)
        elif level == 'medium':
            confidence_scores.append(0.7)
        else:  # low
            confidence_scores.append(0.3)
            low_confidence_fields.append(field)
            reason = field_conf.get('reason', 'Not clearly visible in document') if isinstance(field_conf, dict) else 'No confidence data'
            review_reasons.append(f"{field}: {reason}")

    # Calculate overall confidence
    overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5

    # Determine if human review is needed
    # Threshold: 0.8 (80% confidence) - based on research recommendations
    needs_human_review = overall_confidence < 0.8 or len(low_confidence_fields) > 0

    # Add additional review reasons
    if not coi_data.get('additional_insured_checked'):
        review_reasons.append("Additional Insured not checked - verify this is intentional")
    if not coi_data.get('cg_20_10_endorsement') and not coi_data.get('cg_20_37_endorsement'):
        review_reasons.append("No CG endorsements found - may indicate incomplete coverage")

    return {
        "overall_confidence": round(overall_confidence, 2),
        "needs_human_review": needs_human_review,
        "review_reasons": review_reasons[:5],  # Limit to top 5 reasons
        "low_confidence_fields": low_confidence_fields,
        "extraction_notes": f"Analyzed {len(critical_fields)} critical fields. {len(low_confidence_fields)} have low confidence."
    }
