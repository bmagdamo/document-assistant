import re

# These patterns catch the most common prompt injection phrasings as a first-pass filter.
# This list is intentionally not exhaustive — the system prompt and output guard are the
# primary defenses. This layer reduces LLM load for obvious attacks and adds a logged signal.
INJECTION_PATTERNS = [
    r"jailbreak",
    r"\bdan\b",
    r"(ignore|disregard|forget|override|bypass|skip)\s+(all\s+)?(previous|prior|above|your|any|these|those|the)\s+(instructions?|rules?|constraints?|guidelines?|prompts?|context)",
    r"you\s+are\s+now\s+(a\s+different|an?\s+unrestricted|an?\s+unfiltered|a\s+new)",
    r"(developer|admin|system|god|root|maintenance|debug)\s+mode",
    r"act\s+as\s+(if\s+you\s+(have|are)|a\s+different|an?\s+unrestricted|an?\s+unfiltered)",
    r"pretend\s+(you\s+(have\s+no|are\s+not|don.t\s+have)|there\s+are\s+no)",
    r"roleplay\s+as",
    r"your\s+(true\s+self|real\s+(instructions?|rules?|self))",
    r"new\s+(instructions?|rules?|persona|identity|role|directive)",
    r"(encode|decode|translate|spell\s+out|say\s+.+word.by.word|base64|rot13|pig.?latin)",
    r"hypothetical(ly)?\s+(scenario|situation|world|universe)",
    r"in\s+a\s+(story|novel|fiction|game|simulation|alternate|hypothetical)",
    r"as\s+(a\s+)?fiction",
    r"what\s+(are|were)\s+your\s+(instructions?|rules?|system\s+prompt|prompt)",
    r"repeat\s+(your|the)\s+(instructions?|system\s+prompt|prompt|rules?)",
    r"show\s+me\s+(your|the)\s+(instructions?|system\s+prompt|prompt|rules?)",
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
