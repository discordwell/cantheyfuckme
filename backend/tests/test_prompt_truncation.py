"""Regression tests: document text is capped at MAX_DOC_CHARS before being
interpolated into LLM prompts.

These flip the router module's MOCK_MODE binding off and stub llm_json_call,
so the real prompt-building path runs without touching the network.
"""
from config import MAX_DOC_CHARS
import routers.documents as documents
import routers.analyzers as analyzers


def _long_doc() -> str:
    return ("A" * MAX_DOC_CHARS) + "OVERFLOWMARKER"


def test_extract_truncates_document(client, monkeypatch):
    captured = {}

    def fake_llm_json_call(prompt, **kwargs):
        captured["prompt"] = prompt
        return {}

    monkeypatch.setattr(documents, "MOCK_MODE", False)
    monkeypatch.setattr(documents, "llm_json_call", fake_llm_json_call)

    response = client.post("/api/extract", json={"text": _long_doc()})
    assert response.status_code == 200
    assert "OVERFLOWMARKER" not in captured["prompt"]
    assert "A" * 1000 in captured["prompt"]


def test_coi_compliance_truncates_document(client, monkeypatch):
    prompts = []

    def fake_llm_json_call(prompt, **kwargs):
        prompts.append(prompt)
        if len(prompts) == 1:  # extraction step
            return {"insured_name": "Acme"}
        return {  # compliance step
            "overall_status": "compliant",
            "risk_exposure": "Low",
            "fix_request_letter": "",
        }

    monkeypatch.setattr(analyzers, "MOCK_MODE", False)
    monkeypatch.setattr(analyzers, "llm_json_call", fake_llm_json_call)

    response = client.post("/api/check-coi-compliance", json={"coi_text": _long_doc()})
    assert response.status_code == 200
    assert "OVERFLOWMARKER" not in prompts[0]
    assert "A" * 1000 in prompts[0]
