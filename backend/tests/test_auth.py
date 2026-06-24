"""Tests for password hashing, the login timing mitigation, and session-token
resolution / logout revocation.

These cover three fixes:
  * bcrypt 5.0 raises ValueError for passwords longer than 72 bytes, which made
    signup (and login with a long password) 500. hash_password/verify_password
    now truncate to bcrypt's 72-byte boundary so long passphrases work.
  * login() must run a bcrypt comparison even for unknown emails so response
    timing can't be used to enumerate which accounts exist.
  * logout() must revoke the server-side session from whichever credential the
    client presents. The SPA authenticates with an Authorization: Bearer token
    (kept in localStorage), but logout used to read only the auth_token cookie,
    so a Bearer-only client's session survived until its 30-day expiry.

The full signup/login happy path needs a database; here we unit-test the crypto
helpers and token resolution directly and exercise the no-DB login/logout
branches through the API.
"""
import types

import routers.auth as auth_router
from services.auth import (hash_password, verify_password, dummy_verify,
                           get_session_token)


# ---------- hash_password / verify_password ----------

def test_hash_verify_round_trip():
    h = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", h) is True


def test_verify_rejects_wrong_password():
    h = hash_password("correct horse battery staple")
    assert verify_password("wrong password", h) is False


def test_long_password_does_not_crash_and_round_trips():
    # >72 bytes: bcrypt would raise ValueError without our truncation, which is
    # what used to turn signup into an opaque 500.
    long_pw = "a" * 100
    h = hash_password(long_pw)  # must not raise
    assert verify_password(long_pw, h) is True


def test_passwords_sharing_first_72_bytes_are_equivalent():
    # Documents the truncation contract: only the first 72 bytes are significant,
    # so hash and verify stay consistent for any over-length input.
    base = "x" * 72
    assert verify_password(base + "DIFFERENT", hash_password(base + "ending")) is True


def test_multibyte_password_round_trips():
    # UTF-8 multibyte chars push the byte count past the char count; truncation
    # happens on bytes but is applied identically on both sides, so it round-trips.
    pw = "café-" + "🔒" * 40
    h = hash_password(pw)
    assert verify_password(pw, h) is True


def test_verify_fails_closed_on_malformed_hash():
    # A corrupt/empty stored hash must be a non-match, not a 500.
    assert verify_password("anything", "not-a-bcrypt-hash") is False
    assert verify_password("anything", "") is False


def test_dummy_verify_is_always_false_and_safe():
    assert dummy_verify("anything") is False
    assert dummy_verify("a" * 100) is False  # long input must not raise either


# ---------- login timing mitigation (no DB) ----------

def test_login_unknown_user_still_runs_verification(client, monkeypatch):
    """With no DB the user is always unknown; login must still perform a bcrypt
    comparison (via dummy_verify) so timing doesn't leak account existence."""
    calls = []

    def spy(password):
        calls.append(password)
        return False

    monkeypatch.setattr(auth_router, "dummy_verify", spy)
    resp = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "whatever"})
    assert resp.status_code == 401
    assert calls == ["whatever"], "dummy_verify should run for a non-existent account"


def test_login_long_password_returns_401_not_500(client):
    # Exercises the real dummy_verify with an over-length password to prove the
    # login verification path no longer crashes on >72-byte input.
    resp = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "a" * 200})
    assert resp.status_code == 401


# ---------- get_session_token ----------

def _fake_request(headers=None, cookies=None):
    """Minimal stand-in for a Request: get_session_token only reads .headers.get
    and .cookies.get, both of which a plain dict satisfies."""
    return types.SimpleNamespace(headers=headers or {}, cookies=cookies or {})


def test_session_token_prefers_bearer_header():
    # When both are present the header wins (it is the SPA's source of truth).
    req = _fake_request(
        headers={"Authorization": "Bearer header-tok"},
        cookies={"auth_token": "cookie-tok"},
    )
    assert get_session_token(req) == "header-tok"


def test_session_token_falls_back_to_cookie():
    req = _fake_request(cookies={"auth_token": "cookie-tok"})
    assert get_session_token(req) == "cookie-tok"


def test_session_token_none_when_absent():
    assert get_session_token(_fake_request()) is None


def test_session_token_ignores_non_bearer_scheme():
    # A non-Bearer Authorization header is not a session token; fall back to the
    # cookie (preserves the prior get_current_user behaviour).
    req = _fake_request(
        headers={"Authorization": "Basic Zm9vOmJhcg=="},
        cookies={"auth_token": "cookie-tok"},
    )
    assert get_session_token(req) == "cookie-tok"


# ---------- logout revokes the right session (no DB) ----------

def test_logout_revokes_session_from_bearer_token(client, monkeypatch):
    """The SPA logs out with an Authorization: Bearer header (and, cross-origin,
    no cookie). Logout must revoke that server-side session, not silently no-op."""
    deleted = []
    monkeypatch.setattr(auth_router, "delete_session", lambda tok: deleted.append(tok))
    resp = client.post("/api/auth/logout", headers={"Authorization": "Bearer sess-bearer"})
    assert resp.status_code == 200
    assert deleted == ["sess-bearer"]


def test_logout_revokes_session_from_cookie(client, monkeypatch):
    deleted = []
    monkeypatch.setattr(auth_router, "delete_session", lambda tok: deleted.append(tok))
    resp = client.post("/api/auth/logout", headers={"Cookie": "auth_token=sess-cookie"})
    assert resp.status_code == 200
    assert deleted == ["sess-cookie"]


def test_logout_prefers_bearer_over_cookie(client, monkeypatch):
    deleted = []
    monkeypatch.setattr(auth_router, "delete_session", lambda tok: deleted.append(tok))
    resp = client.post(
        "/api/auth/logout",
        headers={"Authorization": "Bearer sess-bearer", "Cookie": "auth_token=sess-cookie"},
    )
    assert resp.status_code == 200
    assert deleted == ["sess-bearer"]
