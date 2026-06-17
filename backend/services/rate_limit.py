"""In-process per-key rate limiting for the public API.

The size guards in ``services/limits.py`` bound how big a *single* request can
be; this bounds how *often* a client may call us. Without it, the size caps
still let a script fire thousands of normal-sized requests, each one a paid
OpenAI call (or a bcrypt login attempt) — the actual cost-abuse / brute-force
vector for a free public service.

The implementation is a sliding-window log: per key we keep the timestamps of
recent hits and allow at most ``max_requests`` within any ``window_seconds``
interval. It is intentionally dependency-free and in-process, which is the right
fit for the documented single-container, single-worker deployment. Run with
multiple workers and each holds its own counters, so the effective ceiling is
multiplied by the worker count — a safe degradation, never a correctness bug.
"""
import threading
import time
from collections import OrderedDict, deque
from typing import Deque, Optional


class SlidingWindowRateLimiter:
    """Allow at most ``max_requests`` hits per key within ``window_seconds``.

    ``check`` records a hit and returns ``None`` when the request is allowed, or
    the number of seconds the caller should wait before retrying when the key is
    over its limit. Rejected requests are *not* recorded, so a client that keeps
    hammering does not push its own recovery time further out — it simply waits
    for the oldest in-window hit to age out.
    """

    def __init__(
        self,
        max_requests: int,
        window_seconds: float,
        *,
        max_tracked_keys: int = 20000,
    ):
        # A non-positive window would purge every prior hit on each call (cutoff
        # == now), silently turning an active limiter into a no-op — a
        # fail-*open* misconfiguration for a control whose whole job is to
        # throttle. Fail fast instead, matching the import-time int() parsing.
        if max_requests > 0 and window_seconds <= 0:
            raise ValueError("window_seconds must be positive when max_requests > 0")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_tracked_keys = max_tracked_keys
        # Insertion-ordered so we can evict least-recently-used keys cheaply.
        self._hits: "OrderedDict[str, Deque[float]]" = OrderedDict()
        self._lock = threading.Lock()

    def check(self, key: str, *, now: Optional[float] = None) -> Optional[float]:
        """Record a hit for ``key``; return ``None`` if allowed else seconds to wait.

        ``now`` is injectable so tests stay deterministic; in production it
        defaults to a monotonic clock (immune to wall-clock jumps).
        """
        if self.max_requests <= 0:
            return None  # a non-positive limit disables this tier entirely
        now = time.monotonic() if now is None else now
        cutoff = now - self.window_seconds

        with self._lock:
            hits = self._hits.get(key)
            if hits is None:
                hits = deque()
                self._hits[key] = hits

            # Drop hits that have aged out of the window.
            while hits and hits[0] <= cutoff:
                hits.popleft()

            self._hits.move_to_end(key)  # mark key as recently used

            if len(hits) >= self.max_requests:
                # Next slot frees up when the oldest in-window hit expires.
                retry_after = hits[0] + self.window_seconds - now
                return max(retry_after, 0.0)

            hits.append(now)
            self._evict_if_needed()
            return None

    def _evict_if_needed(self) -> None:
        # Bound memory: drop least-recently-used keys past the cap. Evicting an
        # active key merely resets its count, acceptable only under a flood of
        # distinct keys (which can't be perfectly defended in-process anyway).
        while len(self._hits) > self.max_tracked_keys:
            self._hits.popitem(last=False)

    def reset(self) -> None:
        """Forget all tracked state (used by tests)."""
        with self._lock:
            self._hits.clear()


def get_client_ip(request, trusted_proxies: int) -> str:
    """Best-effort real client IP, accounting for trusted reverse proxies.

    Each proxy appends the address it received the request *from* to
    ``X-Forwarded-For``, so behind ``trusted_proxies`` trusted hops the real
    client is the ``trusted_proxies``-th entry counted from the right; entries
    further left are client-supplied and spoofable, so they are ignored. With
    ``trusted_proxies <= 0`` the header is ignored entirely and the socket peer
    is used (correct when no proxy sits in front).
    """
    if trusted_proxies > 0:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            parts = [p.strip() for p in forwarded.split(",") if p.strip()]
            if len(parts) >= trusted_proxies:
                return parts[-trusted_proxies]
            # Chain shorter than expected (misconfigured proxy count, or a direct
            # hit carrying a forged header): every entry here is client-supplied
            # and spoofable, so trust none of them — fall through to the socket
            # peer, which is the real TCP source and cannot be forged.

    client = request.client
    return client.host if client and client.host else "unknown"
