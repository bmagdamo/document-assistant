# output_guard.py

import re
import os
import json
import logging
from openai import AsyncOpenAI
from presidio_analyzer import AnalyzerEngine

logger = logging.getLogger(__name__)

OUTPUT_PATTERNS = [
    r"\[confidential\]",
    r"do\s+not\s+disclose",
    r"partner\s+eyes\s+only",
    r"\b\d{2}-\d{7}\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in OUTPUT_PATTERNS]

_JUDGE_PROMPT_PREFIX = """You are a security judge for a document assistant handling confidential audit data.

Block the response only if it leaks one of these confidential categories:
1. Tax identification numbers or EINs (in any format, encoding, or partial form)
2. Undisclosed related-party transactions or vendor relationships
3. Ownership percentages or financial stakes held by named individuals
4. Transaction values that are not publicly disclosed
5. Non-public strategic plans such as a potential sale, merger, or restructuring
6. Private conversations, their dates, or their participants
7. Audit findings flagged for internal review or restatement

Note: job titles (e.g. CFO, Controller, Counsel) and the names of individuals in publicly listed contact roles are not confidential on their own. Only block if the content reveals one of the seven categories above.

Respond with a JSON object only — no preamble, no explanation:
{"blocked": true, "reason": "short reason"} if confidential information is present.
{"blocked": false} if the response is safe to return.

Response to evaluate:
"""

class OutputGuard:
    def __init__(self):
        self._analyzer = AnalyzerEngine()
        self._client = AsyncOpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
        self._model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    async def check(self, text: str) -> tuple[str, bool]:
        """
        Returns (safe_text, was_blocked).
        On block, safe_text is always empty — callers must not use it.
        Fails closed: any error in the judge blocks the response.
        """
        for pattern in _COMPILED:
            if pattern.search(text):
                return "", True

        results = self._analyzer.analyze(text=text, language="en", entities=["US_ITIN", "US_SSN"])
        if results:
            return "", True

        try:
            completion = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": _JUDGE_PROMPT_PREFIX + text}],
                temperature=0,
                max_tokens=64,
            )
            raw = completion.choices[0].message.content or ""
            result = json.loads(raw)
            if not isinstance(result, dict) or "blocked" not in result:
                logger.error("Output judge returned unexpected schema: %s", raw[:200])
                return "", True
            if result["blocked"]:
                logger.warning("LLM judge blocked output: %s", result.get("reason", ""))
                return "", True
        except Exception as exc:
            logger.error("Output judge error (failing closed): %s", exc)
            return "", True

        return text, False