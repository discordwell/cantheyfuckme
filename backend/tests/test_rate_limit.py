"""Tests for per-IP rate limiting (services/rate_limit.py + main.py middleware).

The limiter and IP helper are tested as pure units with an injected clock so the
assertions are deterministic. The middleware is then exercised end-to-end via the
TestClient with the limiter enabled and shrunk to tiny limits — the offline suite
otherwise runs with RATE_LIMIT_ENABLED=false (see conftest.py).
"""
import pytest

import main
from services.rate_limit import SlidingWindowRateLimiter, get_client_ip


# ---------------- SlidingWindowRateLimiter ----------------

def test_allows_up_to_limit_then_blocks():
    limiter = SlidingWindowRateLimiter(3, 10)
    assert limiter.check("k", now=0) is None
    assert limiter.check("k", now=1) is None
    assert limiter.check("k", now=2) is None
    # 4th hit inside the window is rejected; next slot frees when hit@0 expires.
    assert limiter.check("k", now=3) == pytest.approx(7.0)


def test_rejected_hits_do_not_extend_the_block():
    limiter = SlidingWindowRateLimiter(3, 10)
    for t in (0, 1, 2):
        limiter.check("k", now=t)
    # Hammering while blocked must not push recovery further out...
    assert limiter.check("k", now=9) == pytest.approx(1.0)
    # ...and once the oldest in-window hit ages out, the key is allowed again.
    assert limiter.check("k", now=10) is None


def test_window_slides():
    limiter = SlidingWindowRateLimiter(2, 10)
    assert limiter.check("k", now=0) is None
    assert limiter.check("k", now=5) is None
    assert limiter.check("k", now=6) is not None  # over limit
    # hit@0 expires at t=10, leaving room for one more.
    assert limiter.check("k", now=11) is None


def test_keys_are_independent():
    limiter = SlidingWindowRateLimiter(1, 10)
    assert limiter.check("a", now=0) is None
    assert limiter.check("a", now=1) is not None
    assert limiter.check("b", now=1) is None  # different key, own budget


@pytest.mark.parametrize("max_requests", [0, -1])
def test_non_positive_limit_disables(max_requests):
    limiter = SlidingWindowRateLimiter(max_requests, 10)
    for t in range(100):
        assert limiter.check("k", now=t) is None


def test_non_positive_window_is_rejected_for_active_limiter():
    # A zero/negative window would purge every hit each call and fail open;
    # an active limiter must refuse it rather than silently disable itself.
    with pytest.raises(ValueError):
        SlidingWindowRateLimiter(5, 0)
    with pytest.raises(ValueError):
        SlidingWindowRateLimiter(5, -1)
    # ...but a disabled limiter (max_requests <= 0) doesn't care about the window.
    assert SlidingWindowRateLimiter(0, 0).check("k", now=0) is None


def test_memory_is_bounded_by_lru_eviction():
    limiter = SlidingWindowRateLimiter(5, 10, max_tracked_keys=2)
    limiter.check("a", now=0)
    limiter.check("b", now=0)
    limiter.check("c", now=0)  # pushes out least-recently-used "a"
    assert len(limiter._hits) == 2
    assert "a" not in limiter._hits
    assert "c" in limiter._hits


def test_reset_clears_state():
    limiter = SlidingWindowRateLimiter(1, 10)
    assert limiter.check("k", now=0) is None
    assert limiter.check("k", now=1) is not None
    limiter.reset()
    assert limiter.check("k", now=2) is None


# ---------------- get_client_ip ----------------

class _Headers:
    def __init__(self, data):
        self._data = {k.lower(): v for k, v in data.items()}

    def get(self, key, default=None):
        return self._data.get(key.lower(), default)


class _Client:
    def __init__(self, host):
        self.host = host


class _Request:
    def __init__(self, headers=None, client_host="10.0.0.1"):
        self.headers = _Headers(headers or {})
        self.client = _Client(client_host) if client_host is not None else None


def test_ip_uses_last_xff_entry_behind_one_proxy():
    # Caddy appends the real client as the last entry; earlier entries are
    # client-supplied and must be ignored (spoof resistance).
    req = _Request({"X-Forwarded-For": "9.9.9.9, 203.0.113.7"})
    assert get_client_ip(req, trusted_proxies=1) == "203.0.113.7"


def test_ip_falls_back_to_socket_peer_without_xff():
    req = _Request(client_host="198.51.100.4")
    assert get_client_ip(req, trusted_proxies=1) == "198.51.100.4"


def test_ip_ignores_xff_when_no_trusted_proxies():
    req = _Request({"X-Forwarded-For": "9.9.9.9"}, client_host="198.51.100.4")
    assert get_client_ip(req, trusted_proxies=0) == "198.51.100.4"


def test_ip_with_two_trusted_proxies_picks_second_from_right():
    req = _Request({"X-Forwarded-For": "203.0.113.7, 70.0.0.1, 70.0.0.2"})
    assert get_client_ip(req, trusted_proxies=2) == "70.0.0.1"


def test_short_xff_chain_falls_back_to_socket_peer_not_spoofable_entry():
    # Chain shorter than the configured proxy count: every XFF entry is
    # client-supplied, so we must NOT trust the left-most one — fall through to
    # the (unforgeable) socket peer instead.
    req = _Request({"X-Forwarded-For": "9.9.9.9"}, client_host="198.51.100.4")
    assert get_client_ip(req, trusted_proxies=2) == "198.51.100.4"


def test_ip_unknown_when_no_client_and_no_header():
    req = _Request(client_host=None)
    assert get_client_ip(req, trusted_proxies=1) == "unknown"


# ---------------- middleware integration ----------------

@pytest.fixture
def rate_limited(monkeypatch):
    """Enable the middleware with caller-chosen tiny limiters for one test."""
    monkeypatch.setattr(main, "RATE_LIMIT_ENABLED", True)

    def configure(*, strict=None, default=None):
        if strict is not None:
            monkeypatch.setattr(main, "_strict_limiter", strict)
        if default is not None:
            monkeypatch.setattr(main, "_default_limiter", default)

    return configure


def test_strict_endpoint_429s_over_limit(client, rate_limited):
    rate_limited(strict=SlidingWindowRateLimiter(2, 60))
    body = {"contract_text": "gym membership cancel dues"}

    assert client.post("/api/analyze-gym", json=body).status_code == 200
    assert client.post("/api/analyze-gym", json=body).status_code == 200

    blocked = client.post("/api/analyze-gym", json=body)
    assert blocked.status_code == 429
    assert "rate limit" in blocked.json()["detail"].lower()
    assert int(blocked.headers["Retry-After"]) >= 1


def test_default_tier_throttles_non_llm_endpoints(client, rate_limited):
    rate_limited(default=SlidingWindowRateLimiter(1, 60))
    assert client.get("/api/states").status_code == 200
    assert client.get("/api/states").status_code == 429


def test_health_is_exempt(client, rate_limited):
    # Liveness probes must never be throttled, even with a limit of 1.
    rate_limited(default=SlidingWindowRateLimiter(1, 60))
    for _ in range(5):
        assert client.get("/api/health").status_code == 200


def test_stripe_webhook_is_exempt(client, rate_limited):
    # Signature-authenticated webhook from shared Stripe IPs must not be 429'd.
    # The route is reached every call (its own status depends on Stripe config);
    # the invariant under test is simply that the middleware never throttles it,
    # even past a limit of 1.
    rate_limited(default=SlidingWindowRateLimiter(1, 60))
    for _ in range(3):
        assert client.post("/api/stripe-webhook").status_code != 429


def test_spoofed_xff_prefix_cannot_dodge_the_limit(client, rate_limited):
    # With one trusted proxy the real client is the last XFF entry; a spoofed
    # prefix must not mint a fresh bucket, and a genuinely different client must.
    rate_limited(strict=SlidingWindowRateLimiter(1, 60))
    body = {"contract_text": "gym membership cancel dues"}

    assert client.post("/api/analyze-gym", json=body,
                       headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    # Same real client (last entry), just a spoofed prefix -> still throttled.
    assert client.post("/api/analyze-gym", json=body,
                       headers={"X-Forwarded-For": "9.9.9.9, 1.1.1.1"}).status_code == 429
    # A different real client gets its own budget.
    assert client.post("/api/analyze-gym", json=body,
                       headers={"X-Forwarded-For": "2.2.2.2"}).status_code == 200


def test_disabled_by_default_in_suite(client):
    # Sanity check that the offline suite isn't subject to throttling.
    body = {"contract_text": "gym membership cancel dues"}
    for _ in range(25):
        assert client.post("/api/analyze-gym", json=body).status_code == 200
