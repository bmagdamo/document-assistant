import re

INJECTION_PATTERNS = [
    # Classic overrides
    r"ignore\s+(all\s+)?(previous|prior|above|your)\s+(instructions?|prompts?|rules?|context)",
    r"forget\s+(all\s+)?(previous|prior|your)\s+(instructions?|prompts?|rules?|context)",
    r"disregard\s+(all\s+)?(previous|prior|above|your)\s+(instructions?|prompts?|rules?)",
    r"override\s+(your\s+)?(instructions?|system\s+prompt|rules?|guidelines?)",
    r"new\s+(instructions?|rules?|directives?|system\s+prompt)",
    r"you\s+are\s+now\s+",
    r"from\s+now\s+on\s+(you|act|behave|respond)",
    r"pretend\s+(you\s+)?(are|to\s+be)",
    r"act\s+as\s+(if\s+)?(you\s+are\s+|a\s+)?",
    r"roleplay\s+as",
    r"your\s+(true|real|actual)\s+(self|personality|instructions?)",
    # Persona reframes
    r"you\s+are\s+(not\s+)?(an?\s+)?(ai|assistant|language\s+model|llm|bot|claude|gpt|openai)",
    r"(developer|admin|administrator|system|anthropic|openai)\s+(mode|override|access|prompt|command)",
    r"jailbreak",
    r"\bdan\b",
    r"grandma\s+(trick|exploit|hack)",
    # Direct confidential field extraction
    r"\bein\b",
    r"employer\s+identification",
    r"tax\s+(id|identification|number)",
    r"47.?3821096",
    r"finding\s+(ref|reference)?\s*#?\s*24.?07",
    r"apex\s+component",
    r"related.party\s+transaction",
    r"12\s*%\s*(ownership|stake)",
    r"board.*sale",
    r"sale\s+process",
    r"h2\s+2025",
    r"march\s+3",
    r"private\s+conversation",
    # Encoding / obfuscation tricks
    r"base64",
    r"rot\s*13",
    r"pig\s+latin",
    r"morse\s+code",
    r"hex(adecimal)?",
    r"encode.*confidential",
    r"translate.*confidential",
    r"spell\s+(out|it|the)",
    r"word\s+by\s+word",
    r"letter\s+by\s+letter",
    r"acrostic",
    # Indirect extraction
    r"write\s+a\s+(regex|pattern|code|script|function).*(match|find|extract)",
    r"what\s+(would|does)\s+a\s+(tax\s+id|ein|number\s+like)",
    r"give\s+me\s+an?\s+example\s+of",
    r"hypothetically",
    r"in\s+a\s+fictional\s+(scenario|story|world)",
    r"if\s+(you|this)\s+(were|was)\s+not\s+(real|actual|confidential)",
    # Repetition / echo tricks
    r"repeat\s+(after|back|the|what|everything)",
    r"echo\s+(the|your|everything)",
    r"print\s+(the|your|everything|all)",
    r"copy\s+(the|your|everything|all)\s+(text|content|prompt|instructions?|document)",
    r"show\s+me\s+(your|the)\s+(system\s+prompt|instructions?|original\s+prompt)",
    r"what\s+(are|were)\s+your\s+(original\s+)?(instructions?|system\s+prompt|rules?)",
    # Summary tricks
    r"summarize\s+(all|everything|the\s+entire|the\s+full|the\s+whole)\s+(document|file|text|content)",
    r"list\s+(all|every)\s+(field|entry|item|piece\s+of\s+information)",
    r"what\s+(else|other\s+information)\s+(is|does)\s+(in|the)\s+(document|file)",
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