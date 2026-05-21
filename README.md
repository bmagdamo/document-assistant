# Document Assistant

An AI-powered document assistant that answers natural-language questions about an audit engagement summary. Confidential fields are protected at multiple layers — input filtering, system prompt constraints, and an LLM-based output judge — so the assistant can serve legitimate queries without leaking sensitive information.

## Requirements

- Docker and Docker Compose, **or** Python 3.12+ with [uv](https://docs.astral.sh/uv/)
- An OpenAI API key

## Quick Start (Docker)

1. Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=sk-...
   ```

2. Place the source document at `document.txt` in the project root.

3. Start the service:
   ```bash
   docker compose up
   ```

The API will be available at `http://localhost:8000`.

## Running Without Docker

```bash
uv sync
OPENAI_API_KEY=sk-... uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | API base URL (override for proxies) |
| `LLM_MODEL` | No | `gpt-4o-mini` | Model used for both the assistant and output judge |
| `DOCUMENT_PATH` | No | `document.txt` | Path to the source document |

## API

### POST /ask

Accepts a question and returns an answer grounded in the loaded document.

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What industry does Meridian operate in?"}'
```

```json
{
  "answer": "Meridian Industrial Supply Co. operates in industrial distribution...",
  "session_id": "3f2a1b4c-..."
}
```

To continue a conversation, pass the `session_id` returned from the previous response:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How many distribution centers do they have?", "session_id": "3f2a1b4c-..."}'
```

Sessions expire after 30 minutes of inactivity and are capped at 20 turns.

### GET /health

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok", "model": "gpt-4o-mini", "document_loaded": true}
```

## Live Endpoint

`https://PLACEHOLDER` — included in submission email.
