"""Tests for password hashing and the login timing mitigation.

These cover two fixes:
  * bcrypt 5.0 raises ValueError for passwords longer than 72 bytes, which made
    signup (and login with a long password) 500. hash_password/verify_password
    now truncate to bcrypt's 72-byte boundary so long passphrases work.
  * login() must run a bcrypt comparison even for unknown emails so response
    timing can't be used to enumerate which accounts exist.

The full signup/login happy path needs a database; here we unit-test the crypto
helpers directly and exercise the no-DB login branch through the API.
"""
import routers.auth as auth_router
from services.auth import hash_password, verify_password, dummy_verify


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
