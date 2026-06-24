"""Unit tests for the LLM helper layer in services/llm.py."""
import json

import pytest
from fastapi import HTTPException

import services.llm as llm
from services.llm import (
    clean_llm_response,
    loads_json_lenient,
    llm_json_call,
    llm_text_call,
    parse_limit_to_number,
    calculate_extraction_confidence,
)


# ---------- clean_llm_response ----------

def test_clean_plain_json_unchanged():
    assert clean_llm_response('{"a": 1}') == '{"a": 1}'


def test_clean_strips_json_fence():
    assert clean_llm_response('```json\n{"a": 1}\n```') == '{"a": 1}'


def test_clean_strips_bare_fence():
    assert clean_llm_response('```\n{"a": 1}\n```') == '{"a": 1}'


# ---------- loads_json_lenient ----------
# Every analyzer/extraction/classify call parses model output through this, so
# the prose-tolerance here is what keeps a chatty-but-valid response from 500-ing
# the whole analysis.

def test_lenient_parses_plain_object():
    assert loads_json_lenient('{"risk": "high"}') == {"risk": "high"}


def test_lenient_parses_array():
    # A valid top-level array still parses via the direct json.loads path.
    assert loads_json_lenient('[1, 2, 3]') == [1, 2, 3]


def test_lenient_recovers_from_preamble():
    assert loads_json_lenient('Here is the analysis: {"risk": "high"}') == {"risk": "high"}


def test_lenient_recovers_from_trailing_prose():
    assert loads_json_lenient('{"risk": "high"}\n\nLet me know if you need more.') == {"risk": "high"}


def test_lenient_recovers_from_fence_with_surrounding_prose():
    raw = 'Sure!\n```json\n{"risk": "high"}\n```\nHope that helps.'
    assert loads_json_lenient(raw) == {"risk": "high"}


def test_lenient_ignores_braces_inside_string_values():
    # A brace inside a string value must not unbalance the span extractor.
    raw = 'note => {"clause_text": "fee of { everything }", "ok": true}'
    assert loads_json_lenient(raw) == {"clause_text": "fee of { everything }", "ok": True}


def test_lenient_handles_nested_object_and_array():
    raw = 'result: {"a": [1, 2], "b": {"c": 3}} done'
    assert loads_json_lenient(raw) == {"a": [1, 2], "b": {"c": 3}}


def test_lenient_handles_escaped_quotes_and_braces_in_strings():
    # The load-bearing escape tracking: a literal '}' sitting inside an
    # escaped-quote span must not close the object early. Written so this fails
    # if the scanner stops tracking strings/escapes.
    raw = 'noise {"a": "he said \\"}\\" ok", "b": 2} trailing'
    assert loads_json_lenient(raw) == {"a": 'he said "}" ok', "b": 2}


def test_lenient_returns_first_object_when_two_present():
    # Recovery targets the FIRST balanced object; freeze that contract so a
    # future refactor of the scan can't silently change which object wins.
    raw = 'first {"a": 1} then {"b": 2}'
    assert loads_json_lenient(raw) == {"a": 1}


def test_lenient_raises_when_no_json_present():
    # No '{' to recover — must surface the parse error, not invent a result.
    with pytest.raises(json.JSONDecodeError):
        loads_json_lenient("there is no json here at all")


def test_lenient_raises_on_unbalanced_object():
    # Truncated output never balances, so recovery returns None and the original
    # parse error propagates (no half-object handed downstream).
    with pytest.raises(json.JSONDecodeError):
        loads_json_lenient('truncated {"a": 1, "b":')


# ---------- parse_limit_to_number ----------

@pytest.mark.parametrize("raw,expected", [
    ("$1,000,000", 1_000_000),
    ("$1M", 1_000_000),
    ("$2.5M", 2_500_000),
    ("250K", 250_000),
    ("$500", 500),
    ("", 0),
    (None, 0),
    ("not a number", 0),
    # Magnitudes that overflow float to infinity: int(inf) raises OverflowError,
    # not ValueError, so these must still degrade to 0 (regression guard).
    ("$1E400M", 0),
    ("INFM", 0),
    ("1E309K", 0),
])
def test_parse_limit_to_number(raw, expected):
    assert parse_limit_to_number(raw) == expected


# ---------- llm_text_call / llm_json_call ----------

class FakeClient:
    """Stands in for the OpenAI client; returns a canned message content."""

    def __init__(self, content):
        self._content = content
        completions = self

        class Chat:
            pass

        self.chat = Chat()
        self.chat.completions = completions
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs

        class Message:
            content = self._content

        class Choice:
            message = Message()

        class Response:
            choices = [Choice()]

        return Response()


@pytest.fixture
def fake_llm(monkeypatch):
    def install(content):
        client = FakeClient(content)
        monkeypatch.setattr(llm, "MOCK_MODE", False)
        monkeypatch.setattr(llm, "_client", client)
        return client
    return install


def test_llm_json_call_parses_fenced_json(fake_llm):
    fake_llm('```json\n{"risk": "high"}\n```')
    assert llm_json_call("prompt") == {"risk": "high"}


def test_llm_json_call_rejects_invalid_json(fake_llm):
    fake_llm("this is not json")
    with pytest.raises(HTTPException) as exc:
        llm_json_call("prompt")
    assert exc.value.status_code == 500
    assert "Failed to parse" in exc.value.detail


def test_llm_json_call_recovers_from_preamble(fake_llm):
    # A model that prepends a sentence before the JSON object must not 500 the
    # analysis (every analyzer goes through this path).
    fake_llm('Here is the JSON you asked for:\n{"risk": "high"}')
    assert llm_json_call("prompt") == {"risk": "high"}


def test_llm_json_call_recovers_from_trailing_prose(fake_llm):
    fake_llm('{"risk": "high"}\n\nLet me know if you have questions.')
    assert llm_json_call("prompt") == {"risk": "high"}


def test_llm_json_call_recovers_from_fenced_response_with_prose(fake_llm):
    fake_llm('Sure thing!\n```json\n{"risk": "high"}\n```')
    assert llm_json_call("prompt") == {"risk": "high"}


def test_llm_json_call_handles_braces_in_string_values(fake_llm):
    fake_llm('Result: {"clause": "late fee of {amount}", "risk": "low"}')
    assert llm_json_call("prompt") == {"clause": "late fee of {amount}", "risk": "low"}


def test_llm_text_call_rejects_empty_content(fake_llm):
    fake_llm(None)
    with pytest.raises(HTTPException) as exc:
        llm_text_call("prompt")
    assert exc.value.status_code == 502


def test_llm_text_call_passes_model_and_system(fake_llm):
    client = fake_llm("ok")
    llm_text_call("prompt", model="test-model", max_tokens=99, system="sys")
    assert client.last_kwargs["model"] == "test-model"
    assert client.last_kwargs["max_completion_tokens"] == 99
    assert client.last_kwargs["messages"][0] == {"role": "system", "content": "sys"}
    assert client.last_kwargs["messages"][1] == {"role": "user", "content": "prompt"}


# ---------- calculate_extraction_confidence ----------

def test_confidence_all_high_needs_no_review():
    fields = [
        'gl_limit_per_occurrence', 'gl_limit_aggregate',
        'additional_insured_checked', 'waiver_of_subrogation_checked',
        'cg_20_10_endorsement', 'cg_20_37_endorsement',
    ]
    coi_data = {
        "additional_insured_checked": True,
        "cg_20_10_endorsement": True,
        "confidence": {f: {"level": "high"} for f in fields},
    }
    meta = calculate_extraction_confidence(coi_data)
    assert meta["overall_confidence"] == 1.0
    assert meta["needs_human_review"] is False


def test_confidence_missing_data_needs_review():
    meta = calculate_extraction_confidence({})
    assert meta["needs_human_review"] is True
    assert meta["overall_confidence"] < 0.8
