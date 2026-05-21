# DEVLOG

Claude Code was used to help with scaffolding, dealing with things I was less familiar with like API security, and iterating on plans.

---

## Starting out

My first prompt was to scaffold a FastAPI app with a POST /ask endpoint, server-side session management, and a prompt builder that takes a document and conversation history. I kept it broad to see what it would produce before steering it.

Most of it was fine. The session store came out clean and the prompt builder was straightforward. The main thing it got wrong was conversation state; it returned the session_id to the client and trusted whatever came back in the next request. I changed that to always look up history server-side using the session_id as a key, never accepting history from the client. An attacker who controls the conversation history can gradually shift what the model thinks it has already said, so from my perspective that was an important fix to make.

---

## Input guard

Asked it to generate regex patterns for common prompt injection attempts. It came back with 15-20 patterns, including things that matched on "revenue" or "financial data." The input guard is just a first pass for obvious jailbreak syntax, so I cut that down. I wanted to avoid rejecting real queries in favor of keeping information confidential. The system prompt and output guard do most of the work in making sure no sensitive info leaks.

---

## Output guard

Went through a few iterations. The first version was regex-only, matching on `[CONFIDENTIAL]`, EIN format, and a few document-specific strings. That's easy to get around with light paraphrasing.

I added a Presidio PII scan as a second layer. It still didn't seem to have full coverage; I could imagine a situation where somebody could get the LLM to spell out something like the EIN in words that wouldn't get caught by the output guard.

Because of this, a third layer was added, which was a second LLM call that acts as a judge and evaluates the response before it goes out. I Seven categories: EINs in any format or encoding, related-party transactions, ownership percentages, undisclosed transaction values, non-public strategic plans, private conversations, and flagged audit findings. 

One bug that snuck in: the judge prompt was assembled with Python's `.format(text=text)`. If the LLM response had curly braces in it, that raises a `KeyError`. The except block caught it and failed closed, so it wasn't visible. It would just silently block anything with braces. That bug was caught pretty late.

---

## Rate limiting

There were a few rounds of debugging here. The first implementation had a bug where the slowapi handler wasn't wired to the app state correctly. After fixing that I added session-level rate limiting on top of the IP-based limit. The session limiter had its own bug; the session entry wasn't being initialized until after the rate limit check, which meant the first request on any new session would always pass regardless of count. Fixed that by initializing the entry inside the check itself. There was also a separate issue where the rate limit method was synchronous and modifying shared state without holding the async lock. Fine on a single worker, but a would be risking a race condition if the deployment ever scaled.

---

## Git exposure

Something I caught after the fact: the system prompt in `prompt_builder.py` is a tracked file, and I'd written the confidential field descriptions specific enough that they named particular things, including a vendor name, an internal finding reference number, and a strategic timeline. None of those are the actual sensitive values, but they're still a roadmap. Someone reading the repo before probing the endpoint would know exactly which vendor to ask about and that there's a corporate event with a specific timeframe.


---

## Authentication

I left the endpoint unauthenticated for this submission. The rate limiting handles the abuse case well enough for a temporary eval endpoint, and the real security here is at the data layer anyway. Auth wouldn't change what the assistant will or won't say.

In production this would look different. For a service-to-service API like this, the standard approach is issued API keys per client with a bearer token header, scoped to specific permissions and rotatable without redeployment. If there are real user identities involved (an internal tool with SSO, for example), you'd sit behind OAuth2/OIDC and validate tokens against your identity provider on each request.

The session design would also change. Right now sessions are anonymous UUIDs living in memory. In production you'd tie the session ID to the authenticated identity so a user's conversation history belongs to them and can't be accessed with a different credential. The in-memory store would move to Redis or similar so sessions survive restarts and work across multiple instances.

---

## What I didn't get to

The input guard still has gaps that regex can't close, like encoding tricks, multi-turn manipulation where no single message looks like an attack, and language switching. The right fix is probably a second LLM call on the input side mirroring the output judge, or a dedicated classifier.

The other thing I'd add is canary values. The idea is to embed a few synthetic "confidential" values in the document that don't appear in the real data, then monitor for them in responses. That way you'd catch attacks that slip past both guards.
