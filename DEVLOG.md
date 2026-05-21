# DEVLOG

## How I used AI tooling

I used Claude Code throughout this build — primarily for scaffolding, iteration on the security layers, and catching my own blind spots when I'd been staring at the same code too long.

---

## What I started with

My first prompt was broad: scaffold a FastAPI app with a POST /ask endpoint, server-side session management, and a prompt builder that takes a document + conversation history. I wanted to see what it would generate before steering it.

The initial scaffold was mostly reasonable. The session store came out clean — TTL expiry, history cap, asyncio lock. The prompt builder was straightforward. What it got wrong on the first pass was conversation state design: it returned the session_id to the client and trusted whatever came back. I corrected that to always look up history server-side using the session_id as a key, never accepting history payloads from the client. That's the core security decision here — an attacker who can inject conversation history can gradually shift what the assistant believes it has already said.

---

## The input guard

I asked it to generate regex patterns for common prompt injection attempts. It came back with a long list — about 15–20 patterns that included things like matching on phrases like "revenue" or "financial data." I pared that back significantly. Broad keyword matching creates too many false positives and gives a false sense of security. The input guard is a first-pass filter for obvious jailbreak syntax, not a semantic firewall. The system prompt and output guard carry the real weight.

---

## The output guard

This went through a few iterations. The first version was purely regex-based — patterns for `[CONFIDENTIAL]`, EIN format, and a handful of document-specific strings. That's easy to bypass with light paraphrasing.

I asked Claude to add a Presidio-based PII scan as a second layer, which it did without issue. But I kept thinking about the obfuscation problem: what if the model returns "four seven dash three eight two one zero nine six"? Regex won't catch that.

So I prompted for a third layer: a second LLM call that acts as a semantic judge, evaluating the response before it goes out. The judge prompt I wrote by hand — I didn't trust the tool to enumerate the right confidential categories on its own. I specified the seven categories explicitly: EINs in any format or encoding, related-party transactions, ownership percentages, undisclosed transaction values, non-public strategic plans, private conversations, and flagged audit findings. The judge runs at temperature 0 and fails closed — any error or unexpected response blocks the output.

One bug that snuck in: the judge prompt was assembled with Python's `.format(text=text)`. If the LLM response contained curly braces (JSON output, code), that would raise a `KeyError`. The except block caught it and failed closed, so it was silent — the judge would appear to block every response with braces rather than erroring visibly. Caught that late.

---

## Rate limiting

This had a few rounds of debugging. The first implementation set up IP-based rate limiting with slowapi but had a bug where the handler wasn't wired to the app state correctly. After fixing that, I added session-level rate limiting on top. The session limiter had its own bug: it was checking whether the session existed before initializing it, but `get()` was being called before `check_rate_limit()`, which meant the first request on a brand-new session would always pass regardless of the count. Fixed by initializing the session entry inside the rate limit check. Later caught a separate issue where the rate limit method was synchronous and modifying shared state without holding the async lock — harmless on a single worker but a real race condition if the deployment ever scales horizontally.

---

## What I didn't get to

The input guard still has gaps that regex can't close — encoding tricks (base64, pig latin, letter-by-letter spelling), multi-turn context manipulation where no single message looks like an attack, and language switching. A proper fix would be a second LLM call on the input side mirroring the output judge, or a dedicated classifier. I ran out of time before adding that.

The other thing I'd add: canary values. Embed a few synthetic "confidential" values in the document that don't appear in the real data, then add a monitor that fires if those values ever appear in a response. Gives you detection coverage for attacks that slip past both guards.
