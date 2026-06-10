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
    assert body["document_type"] == "gym_contract"
    assert body["supported"] is True


def test_classify_unknown_document(client):
    response = client.post("/api/classify", json={"text": "purple monkey dishwasher"})
    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] == "unknown"
    assert body["supported"] is False


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
