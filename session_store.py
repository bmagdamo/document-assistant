import time
import asyncio

class SessionStore:
    def __init__(self, ttl_minutes: int = 30, max_turns: int = 20):
        self._ttl = ttl_minutes * 60
        self._max_turns = max_turns
        self._store: dict = {}
        self._lock = asyncio.Lock()

    def _expire(self) -> None:
        """Remove sessions idle past the TTL. Must be called while holding self._lock."""
        cutoff = time.time() - self._ttl
        stale = [sid for sid, e in self._store.items() if e["last_active"] < cutoff]
        for sid in stale:
            del self._store[sid]

    def get(self, session_id: str) -> list[dict]:
        """Return conversation history for a session (no lock needed — read-only snapshot)."""
        entry = self._store.get(session_id)
        if not entry:
            return []
        return list(entry["history"])

    async def add_turn(self, session_id: str, user_msg: str, assistant_msg: str) -> None:
        async with self._lock:
            self._expire()
            if session_id not in self._store:
                self._store[session_id] = {
                    "history": [],
                    "last_active": time.time(),
                    "request_times": [],
                }
            entry = self._store[session_id]
            entry["history"].append({"role": "user", "content": user_msg})
            entry["history"].append({"role": "assistant", "content": assistant_msg})
            entry["last_active"] = time.time()
            if len(entry["history"]) > self._max_turns * 2:
                entry["history"] = entry["history"][-(self._max_turns * 2):]

    async def check_and_record_request(self, session_id: str, max_per_minute: int = 10) -> bool:
        """Returns True if the request is allowed. Initializes the session entry if needed."""
        async with self._lock:
            self._expire()
            now = time.time()
            if session_id not in self._store:
                self._store[session_id] = {
                    "history": [],
                    "last_active": now,
                    "request_times": [],
                }
            entry = self._store[session_id]
            timestamps = [t for t in entry.get("request_times", []) if now - t < 60]
            timestamps.append(now)
            entry["request_times"] = timestamps
            return len(timestamps) <= max_per_minute
