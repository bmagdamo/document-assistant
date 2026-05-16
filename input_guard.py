import re

INJECTION_PATTERNS = [
    r"jailbreak",
    r"\bdan\b",
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"forget\s+(all\s+)?(previous|prior)\s+instructions?",
    r"you\s+are\s+now\s+(a\s+different|an?\s+unrestricted)",
    r"(developer|admin|system)\s+mode",
]

_COMPILED = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in INJECTION_PATTERNS]

class InputGuard:
    def check(self, text: str) -> tuple[bool, str]:
        """
        Returns (blocked, reason).
        blocked=True means reject before reaching the LLM.
        """
        if len(text) > 2000:
            return True, "input_too_long"

        for pattern in _COMPILED:
            if pattern.search(text):
                return True, f"injection_pattern:{pattern.pattern[:40]}"

        return False, ""