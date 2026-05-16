import time
import asyncio

class SessionStore:
    def __init__(self, ttl_minutes: int = 30, max_turns: int = 20):
        self._ttl = ttl_minutes * 60
        self._max_turns = max_turns
        self._store: dict = {}
        self._lock = asyncio.Lock()

    def _expire(self) -> None:
        """Remove sessions idle past the TTL."""
        cutoff = time.time() - self._ttl
        stale = [sid for sid, e in self._store.items() if e["last_active"] < cutoff]
        for sid in stale:
            del self._store[sid]
    
    def get(self, session_id: str) -> list[dict]:
        """Return conversation history for a session."""
        self._expire()
        entry = self._store.get(session_id)
        if not entry:
            return []
        return list(entry["history"])

    async def add_turn(self, session_id: str, user_msg: str, assistant_msg: str) -> None:
        async with self._lock:
            self._expire()
            if session_id not in self._store:
                self._store[session_id] = {"history": [], "last_active": time.time()}
            entry = self._store[session_id]
            entry["history"].append({"role": "user", "content": user_msg})
            entry["history"].append({"role": "assistant", "content": assistant_msg})
            entry["last_active"] = time.time()
            if len(entry["history"]) > self._max_turns * 2:
                entry["history"] = entry["history"][-(self._max_turns * 2):]
