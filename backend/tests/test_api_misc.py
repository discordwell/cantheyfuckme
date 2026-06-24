"""Mock-mode tests for the non-analyzer API surface: health, documents,
classification, auth validation, waitlist, and reference data."""


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


# ---------- documents ----------

def test_extract_mock(client):
    response = client.post("/api/extract", json={"text": "CERTIFICATE OF INSURANCE for Acme LLC"})
    assert response.status_code == 200
    body = response.json()
    assert "insured_name" in body
    assert isinstance(body["coverages"], list)


def test_compare_requires_two_quotes(client):
    response = client.post("/api/compare", json=[{"text": "only one quote"}])
    assert response.status_code == 400


def test_compare_two_quotes_mock(client):
    # Regression: this used to 500 in mock mode because the comparison step
    # called the real LLM client unconditionally.
    response = client.post("/api/compare", json=[
        {"text": "Policy for Acme LLC. Premium total: $1,200/yr. GL: $1M. Umbrella: $2M"},
        {"text": "Policy for Acme LLC. Premium total: $900/yr. GL: $500K"},
    ])
    assert response.status_code == 200
    body = response.json()
    assert "recommendation" in body
    assert len(body["comparison_table"]) == 2
    assert set(body["pros_cons"].keys()) == {"0", "1"}


def test_generate_proposal_mock(client):
    response = client.post("/api/generate-proposal", json={"insured_name": "Acme LLC"})
    assert response.status_code == 200
    assert "Acme LLC" in response.json()["proposal"]


def test_ocr_mock(client):
    response = client.post("/api/ocr", json={
        "file_data": "aGVsbG8=",
        "file_type": "application/pdf",
        "file_name": "test.pdf",
    })
    assert response.status_code == 200
    assert "Mock OCR" in response.json()["text"]


def test_classify_gym_contract(client):
    response = client.post("/api/classify", json={
        "text": "GYM MEMBERSHIP AGREEMENT: monthly dues, cancel policy, fitness center rules"
    })
    assert response.status_code == 200
    body = response.json()
    # Regression: classify must emit the *canonical* short form ("gym"), not the
    # internal "gym_contract" label. The SPA routes the analyze button by this
    # value, so returning "gym_contract" made the analyze button a silent no-op
    # for gym (and four other) document types.
    assert body["document_type"] == "gym"
    assert body["supported"] is True


def test_classify_unknown_document(client):
    response = client.post("/api/classify", json={"text": "purple monkey dishwasher"})
    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] == "unknown"
    assert body["supported"] is False


def test_classify_recovers_from_prose_wrapped_llm_response(client, monkeypatch):
    """The classify model sometimes prefaces its JSON with a sentence of prose.
    That used to fail json.loads and fall through to 'unknown' — wrongly telling
    the user a supported document is unsupported. Lenient parsing recovers the
    object. Exercises the real (non-mock) branch with a stubbed client.
    """
    import routers.documents as documents
    import services.llm as llm

    class _FakeCompletions:
        def create(self, **kwargs):
            content = (
                "The document is a gym membership agreement.\n"
                '```json\n{"type": "gym_contract", "confidence": 0.92}\n```'
            )
            message = type("Msg", (), {"content": content})()
            choice = type("Choice", (), {"message": message})()
            return type("Resp", (), {"choices": [choice]})()

    fake = type("Client", (), {
        "chat": type("Chat", (), {"completions": _FakeCompletions()})()
    })()

    # Take the real LLM branch in classify, and make get_client() return the fake.
    monkeypatch.setattr(documents, "MOCK_MODE", False)
    monkeypatch.setattr(llm, "MOCK_MODE", False)
    monkeypatch.setattr(llm, "_client", fake)

    response = client.post("/api/classify", json={"text": "gym membership agreement"})
    assert response.status_code == 200
    body = response.json()
    # Recovered "gym_contract" from the prose, then canonicalized to the routable
    # short form the SPA needs.
    assert body["document_type"] == "gym"
    assert body["supported"] is True


def test_classify_emits_canonical_doc_types(client):
    """Every formerly-suffixed contract type must classify to its short, routable
    identifier. These five are the ones the SPA could not route before the fix."""
    cases = {
        "EMPLOYMENT AGREEMENT with non-compete and at-will arbitration clause": "employment",
        "INDEPENDENT CONTRACTOR freelance agreement, deliverables and SOW": "freelancer",
        "INFLUENCER sponsorship brand deal with content usage rights": "influencer",
        "TIMESHARE vacation ownership resort with annual maintenance fee": "timeshare",
        "GYM fitness membership with monthly dues and cancel policy": "gym",
    }
    for text, expected in cases.items():
        body = client.post("/api/classify", json={"text": text}).json()
        assert body["document_type"] == expected, f"{text!r} -> {body['document_type']!r}"
        assert "_contract" not in body["document_type"]


def test_every_classifiable_supported_type_has_an_analyzer_route(client):
    """Contract guard: any supported doc type the classifier can emit must have a
    real analyzer endpoint the client can POST to. This is exactly the invariant
    the gym/employment/... routing bug violated — classify returned a value with
    no matching /api/analyze-* route."""
    from data.supported_doc_types import SUPPORTED_DOC_TYPES, canonical_doc_type
    from main import app

    routes = {r.path for r in app.routes}
    for key, info in SUPPORTED_DOC_TYPES.items():
        if not info["supported"]:
            continue
        canonical = canonical_doc_type(key)
        # COI uses a bespoke compliance route; everything else is /api/analyze-*
        # with underscores rendered as hyphens in the path.
        expected = (
            "/api/check-coi-compliance"
            if canonical == "coi"
            else f"/api/analyze-{canonical.replace('_', '-')}"
        )
        assert expected in routes, f"{key!r} -> canonical {canonical!r} has no route {expected!r}"


# ---------- auth ----------

def test_signup_rejects_invalid_email(client):
    response = client.post("/api/auth/signup", json={"email": "not-an-email", "password": "longenough"})
    assert response.status_code == 400


def test_signup_rejects_short_password(client):
    response = client.post("/api/auth/signup", json={"email": "a@b.com", "password": "short"})
    assert response.status_code == 400


def test_login_unknown_user_is_401(client):
    response = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "whatever"})
    assert response.status_code == 401


def test_me_unauthenticated(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["authenticated"] is False


def test_history_requires_auth(client):
    response = client.get("/api/user/history")
    assert response.status_code == 401


def test_logout_without_session(client):
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json()["success"] is True


# ---------- waitlist ----------

def test_waitlist_rejects_invalid_email(client):
    response = client.post("/api/waitlist", json={"email": "nope", "document_type": "hoa"})
    assert response.status_code == 400


def test_waitlist_accepts_valid_email_without_db(client):
    response = client.post("/api/waitlist", json={"email": "a@b.com", "document_type": "hoa"})
    assert response.status_code == 200
    assert response.json()["success"] is True


# ---------- reference data ----------

def test_project_types(client):
    response = client.get("/api/project-types")
    assert response.status_code == 200
    body = response.json()
    assert "commercial_construction" in body


def test_states(client):
    response = client.get("/api/states")
    assert response.status_code == 200
