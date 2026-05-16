import os
import re
import uuid
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

from session_store import SessionStore
from input_guard import InputGuard
from output_guard import OutputGuard
from prompt_builder import build_prompt

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Secure Document Assistant")

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