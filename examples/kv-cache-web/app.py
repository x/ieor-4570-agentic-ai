import asyncio
import hashlib
import re
import time
import uuid
from datetime import date, datetime
from pathlib import Path

import uvicorn
from agents import Agent, ModelSettings, Runner, RunHooks, SQLiteSession, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Traces upload to OpenAI by default, which needs an OpenAI key. We're on Gemini.
set_tracing_disabled(True)

HERE = Path(__file__).parent

# The Hound of the Baskervilles (Project Gutenberg #2852), one chapter per step.
CHAPTERS = re.split(r"\n(?=Chapter \d+\.\n)", (HERE / "hound.txt").read_text().strip())
QUESTION = "Who is your prime suspect so far? Answer in one sentence."

PROMPT = (
    "You are reading a mystery novel one chapter at a time. After each chapter, "
    "answer the reader's question in one sentence. Don't spoil later chapters."
)


# --- The Two Agents ---

# Instructions can be a function: the SDK calls it before every model request.
# Both put the clock on the first line of the prompt. Only one of them changes it.


def changing_time(context, agent) -> str:
    # Changes every request, so nothing after it can be read from the cache.
    return f"The current time is: {datetime.now().isoformat()}\n\n{PROMPT}"


def fixed_date(context, agent) -> str:
    # Changes once a day. Note: datetime.now().today() would still include the time.
    return f"The current date is: {date.today().isoformat()}\n\n{PROMPT}"


# api_key is unused: Vertex AI authenticates with your gcloud credentials.
MODEL = LitellmModel(model="vertex_ai/gemini-3.5-flash-lite", api_key="unused")
# Gemini 3.5 Flash-Lite, $ per 1M tokens (checked Nov 11, 2026). A cached token costs 10% of one prefilled.
PRICE_INPUT, PRICE_CACHED, PRICE_OUTPUT = 0.30, 0.03, 2.50
# include_usage asks for token counts on a streamed reply. That's where cached_tokens comes from.
SETTINGS = ModelSettings(include_usage=True, extra_args={"vertex_location": "global"})

AGENTS = {
    "changing": Agent(name="Changing time", instructions=changing_time, model=MODEL, model_settings=SETTINGS),
    "fixed": Agent(name="Fixed date", instructions=fixed_date, model=MODEL, model_settings=SETTINGS),
}


# --- Recording What Was Sent ---


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):  # [{"type": "output_text", "text": ...}, ...]
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return ""


class RecordContext(RunHooks):
    """Records the exact context sent to the model: the system prompt, then every input item."""

    def __init__(self):
        self.sent = []

    async def on_llm_start(self, context, agent, system_prompt, input_items):
        self.sent = [("system", system_prompt or "")]
        self.sent += [(item.get("role", "?"), text_of(item.get("content"))) for item in input_items]


def summarize(role: str, text: str) -> dict:
    """What the page draws for one message: a preview, its size, and a hash to compare requests by."""
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    return {
        "role": role,
        "preview": first_line[:90],
        "words": len(text.split()),
        "hash": hashlib.sha1(f"{role}:{text}".encode()).hexdigest()[:12],
    }


async def run_side(key: str, session_id: str, message: str) -> dict:
    session = SQLiteSession(f"{session_id}-{key}", SESSIONS_DB)
    hooks = RecordContext()

    start = time.perf_counter()
    first_token = None
    result = Runner.run_streamed(AGENTS[key], message, session=session, hooks=hooks)
    async for event in result.stream_events():
        # Time to first token: how long prefill took, before the answer's length matters.
        if first_token is None and event.type == "raw_response_event" and event.data.type == "response.output_text.delta":
            first_token = time.perf_counter()
    end = time.perf_counter()

    usage = result.context_wrapper.usage
    cached = usage.input_tokens_details.cached_tokens
    cost = ((usage.input_tokens - cached) * PRICE_INPUT + cached * PRICE_CACHED + usage.output_tokens * PRICE_OUTPUT) / 1e6
    return {
        "cost": cost,
        "ttft_ms": round(((first_token or end) - start) * 1000),
        "total_ms": round((end - start) * 1000),
        "input_tokens": usage.input_tokens,
        "cached_tokens": usage.input_tokens_details.cached_tokens,
        "system": hooks.sent[0][1],
        "context": [summarize(role, text) for role, text in hooks.sent],
        # The reply isn't part of what was sent. It joins the context on the next request.
        "reply": summarize("assistant", result.final_output or ""),
    }


# --- Session Store ---

# Each conversation's history lives in one SQLite file, as in agents-sdk-web.
SESSIONS_DB = "conversations.db"

# --- FastAPI App ---

app = FastAPI()


class StepRequest(BaseModel):
    session_id: str | None = None
    chapter: int = 0


@app.get("/")
def index():
    return FileResponse(HERE / "index.html")


@app.get("/chapters")
def chapters():
    return {"count": len(CHAPTERS)}


@app.post("/step")
async def step(request: StepRequest):
    session_id = request.session_id or str(uuid.uuid4())
    message = f"{CHAPTERS[request.chapter]}\n\n{QUESTION}"

    # Both sides run at the same moment, so they see the same network and server load.
    try:
        changing, fixed = await asyncio.gather(
            run_side("changing", session_id, message),
            run_side("fixed", session_id, message),
        )
    except Exception as e:
        # Auth, billing, a model that is not running: show it on the page, not as a 500.
        return {"session_id": session_id, "error": f"{type(e).__name__}: {str(e)[:300]}"}

    return {"session_id": session_id, "chapter": request.chapter, "changing": changing, "fixed": fixed}


@app.post("/clear")
async def clear(session_id: str | None = None):
    if session_id:
        for key in AGENTS:
            await SQLiteSession(f"{session_id}-{key}", SESSIONS_DB).clear_session()
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
