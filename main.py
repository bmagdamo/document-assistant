import os
import uuid
import logging
from typing import Optional

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

from session_store import SessionStore
from input_guard import InputGuard
from output_guard import OutputGuard
from prompt_builder import build_prompt, DOCUMENT

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Secure Document Assistant")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

session_store = SessionStore(ttl_minutes=30, max_turns=20)
input_guard = InputGuard()
output_guard = OutputGuard()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", ""),
    base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

class AskRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    session_id: str

@app.post("/ask", response_model=AskResponse)
@limiter.limit("20/minute")
async def ask(request: AskRequest):
    session_id = request.session_id or str(uuid.uuid4())
    question = request.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="question must not be empty")

    logger.info("Session %s | question: %.120s", session_id, question)

    blocked, reason = input_guard.check(question)
    if blocked:
        logger.warning("Session %s | INPUT BLOCKED: %s", session_id, reason)
        return AskResponse(
            answer="I can only answer questions about the Meridian engagement document.",
            session_id=session_id,
        )

    history = session_store.get(session_id)
    messages = build_prompt(history, question)

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=512,
        )
        raw_answer = completion.choices[0].message.content or ""
    except Exception as exc:
        logger.error("LLM error for session %s: %s", session_id, exc)
        raise HTTPException(status_code=502, detail="LLM request failed") from exc

    safe_answer, was_blocked = output_guard.check(raw_answer)
    if was_blocked:
        logger.warning("Session %s | OUTPUT BLOCKED — confidential data in LLM response", session_id)
        safe_answer = "I'm not able to share that information. Please ask about general engagement details."

    await session_store.add_turn(session_id, question, safe_answer)

    logger.info("Session %s | answer: %.120s", session_id, safe_answer)
    return AskResponse(answer=safe_answer, session_id=session_id)

@app.get("/health")
async def health():
    doc_ok = bool(DOCUMENT)
    return {
        "status": "ok" if doc_ok else "degraded",
        "model": MODEL,
        "document_loaded": doc_ok,
    }