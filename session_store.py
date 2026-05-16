import time


class SessionStore:
    def __init__(self, ttl_minutes: int = 30, max_turns: int = 20):
        self._ttl = ttl_minutes * 60
        self._max_turns = max_turns
        self._store: dict = {}

    def _expire(self) -> None:
        """Remove sessions idle past the TTL."""
        cutoff = time.time() - self._ttl
        stale = [sid for sid, e in self._store.items() if e["last_active"] < cutoff]
        for sid in stale:
            del self._store[sid]
