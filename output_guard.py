import re

OUTPUT_PATTERNS = [
    # EIN
    r"47.?3821096",
    r"\b\d{2}-\d{7}\b",
    # Finding #24-07
    r"apex\s+component\s+partners",
    r"related.party\s+transaction",
    r"12\s*%\s*(ownership|stake)",
    r"\$\s*1\.?4\s*(m|million)",
    r"finding\s*(ref|reference)?\s*#?\s*24.?07",
    r"not\s+disclosed\s+in\s+(draft\s+)?financial\s+statements",
    r"flagged\s+for\s+partner\s+review",
    # Board / sale process
    r"board.*considering.*sale",
    r"sale\s+process\s+in\s+h2",
    r"h2\s+2025.*sale",
    r"private\s+conversation.*march",
    r"march\s+3(rd)?.*okafor",
    r"okafor.*march\s+3",
    # Encoded EIN
    r"four\s*seven.{1,5}three\s*eight\s*two\s*one\s*zero\s*nine\s*six",
    # Confidentiality markers leaking into output
    r"\[confidential\]",
    r"do\s+not\s+disclose",
    r"partner\s+eyes\s+only",
]

_COMPILED = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in OUTPUT_PATTERNS]
