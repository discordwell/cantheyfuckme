"""Unit tests for the LLM helper layer in services/llm.py."""
import pytest
from fastapi import HTTPException

import services.llm as llm
from services.llm import (
    clean_llm_response,
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
