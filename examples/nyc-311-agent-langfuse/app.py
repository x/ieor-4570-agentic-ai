import json
import os
import uuid
from pathlib import Path

import duckdb
import uvicorn
from agents import Agent, ModelSettings, Runner, RunHooks, Session, SQLiteSession, function_tool
from agents.extensions.models.litellm_model import LitellmModel
from fastapi import FastAPI
from fastapi.responses import FileResponse
from langfuse import get_client, observe, propagate_attributes
from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from pydantic import BaseModel

import entities

# The Agents SDK traces every run. OpenInference turns those traces into OpenTelemetry spans, replacing
# the SDK's default exporter (which uploads to OpenAI), and the Langfuse client exports the spans to
# Langfuse. It reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and LANGFUSE_BASE_URL; without them, it
# warns and exports nothing.
OpenAIAgentsInstrumentor().instrument()
# Cloud Run names every deploy in K_REVISION (e.g. nyc-311-agent-langfuse-00004-spt). As the Langfuse
# release, it tags each production trace with the deploy that served it.
if "K_REVISION" in os.environ:
    os.environ.setdefault("LANGFUSE_RELEASE", os.environ["K_REVISION"])
langfuse = get_client()


# The entity lookup gets its own span, so the trace shows the question before and after expansion.
@observe(name="expand-entities", as_type="retriever", capture_input=False)
def expand(question: str) -> str:
    # observe() would record the call as {"args": [...], "kwargs": {}}. The question alone reads better.
    langfuse.update_current_span(input=question)
    return entities.expand(question)


# build_mappings.py builds both files once, offline. The agent only reads them.
DATA = Path(__file__).parent / "data"
MAX_ROWS = 100
MODEL = "gemini-3.5-flash-lite"
# LiteLLM routes MODEL to Vertex AI. The provider goes here rather than as a "vertex_ai/" prefix on the
# model name, so traces record "gemini-3.5-flash-lite", a name Langfuse has prices for.
VERTEX = {"custom_llm_provider": "vertex_ai", "vertex_location": "global"}

try:
    MAPPINGS = json.loads((DATA / "311_mappings.json").read_text())
    # The security boundary is the connection, not the prompt: read-only, no file or network
    # access, and the agent can't SET its way out of either.
    db = duckdb.connect(
        str(DATA / "311.duckdb"),
        read_only=True,
        config={"enable_external_access": False, "lock_configuration": True},
    )
except (FileNotFoundError, duckdb.Error):
    raise SystemExit("No database found. Run `uv run build_mappings.py` first.")


@function_tool
def read_mappings() -> str:
    """Read the requests table's columns: name, type, a description, and whether it's an enum.

    Call this first. Call get_enum_values for an enum column's valid values.
    """
    return json.dumps([
        {"name": c["name"], "type": c["type"], "description": c["description"], "is_enum": "enum_values" in c}
        for c in MAPPINGS["columns"]
    ])


@function_tool
def get_enum_values(column: str) -> str:
    """Get the exact valid values of an enum column. Match them exactly: equality is case-sensitive.

    Args:
        column: The column name, e.g. 'complaint_type'.
    """
    match = next((c for c in MAPPINGS["columns"] if c["name"] == column), None)
    if match is None:
        return json.dumps({"error": f"No column '{column}'. Call read_mappings for the columns."})
    if "enum_values" not in match:
        return json.dumps({"error": f"'{column}' is not an enum column. Query its distinct values with run_sql."})
    return json.dumps({"column": column, "enum_values": match["enum_values"]})


@function_tool
def run_sql(query: str) -> str:
    """Run a SQL query against the database and return the results.

    Args:
        query: A DuckDB SQL query.
    """
    # The SDK runs tools in threads. Each call gets its own cursor: DuckDB connections aren't thread-safe.
    with db.cursor() as cursor:
        try:
            cursor.execute(query)
            rows = cursor.fetchmany(MAX_ROWS + 1)
        except duckdb.Error as e:
            # The model cannot see an exception. Return something it can reason about.
            return json.dumps({"error": str(e)})
        columns = [column[0] for column in cursor.description or []]

    return json.dumps(
        {
            "columns": columns,
            "rows": rows[:MAX_ROWS],
            "truncated": len(rows) > MAX_ROWS,
        },
        default=str,
    )


# The agent's instructions live in Langfuse Prompt Management, as the production version of the
# nyc-311-analyst prompt. This copy is the fallback, for when Langfuse can't serve it, and the
# prompt's first version (see the README).
PROMPT = "nyc-311-analyst"
INSTRUCTIONS = """\
You answer questions about NYC 311 service requests from 2020 through 2025.
The data is in the `requests` table, one row per request.

- Call read_mappings first to see the columns.
- Before filtering on an enum column, call get_enum_values. Never guess values.
- A question may end with notes, like "Park Slope is incident_zip 11215, 11217."
  Use them: they say what a term means in the database."""

agent = Agent(
    name="NYC 311 Analyst",
    instructions=INSTRUCTIONS,
    # LiteLLM routes the call to Gemini. api_key is unused: Vertex AI uses your gcloud credentials.
    model=LitellmModel(model=MODEL, api_key="unused"),
    model_settings=ModelSettings(extra_args=VERTEX),
    tools=[read_mappings, get_enum_values, run_sql],
)


class RecordToolCalls(RunHooks):
    """Watches the run and records each tool call, for the page to show and the evals to check.

    Make a new one per run: it holds this run's calls.
    """

    def __init__(self):
        self.tool_calls = []

    async def on_tool_end(self, context, agent, tool, result):
        # read_mappings returns ~30 KB. The page gets the start; the trace has all of it.
        self.tool_calls += [{"name": tool.name, "args": json.loads(context.tool_arguments), "result": result[:300]}]


async def answer(question: str, session: Session | None = None, expand_entities: bool = True) -> dict:
    """Answer one question, continuing session's conversation if there is one. One call, one trace."""
    hooks = RecordToolCalls()
    # Fetched per question, from the SDK's cache: a new production version goes live within a minute
    # (the cache's 60-second TTL), with no redeploy. get_prompt returns the fallback when Langfuse can't
    # serve the prompt, but raises when the client has no keys.
    prompt = langfuse.get_prompt(PROMPT, fallback=INSTRUCTIONS) if os.environ.get("LANGFUSE_PUBLIC_KEY") else None
    # One trace per question, grouped by the chat's session in Langfuse's Sessions view. The session
    # goes on before the trace's root span starts, so the root carries it too. The prompt links every
    # generation in the trace to the prompt version that produced it (never the fallback).
    with (
        propagate_attributes(session_id=session.session_id if session else None, prompt=prompt),
        # The root span's input and output are what a reviewer reads in the Langfuse table.
        langfuse.start_as_current_observation(name="answer-question", input=question) as span,
    ):
        task = expand(question) if expand_entities else question  # before the agent runs, like classic RAG
        instructions = prompt.compile() if prompt else INSTRUCTIONS
        result = await Runner.run(agent.clone(instructions=instructions), task, session=session, hooks=hooks)
        span.update(output=result.final_output)
        return {"response": result.final_output, "tool_calls": hooks.tool_calls, "trace_url": langfuse.get_trace_url()}


# --- Session Store ---

# Every session lives in one SQLite file. On Cloud Run the filesystem is in memory, so this
# lasts as long as the instance. Each instance has its own copy.
SESSIONS_DB = "conversations.db"

# --- FastAPI App ---

# FastAPI traces every request once an OpenTelemetry tracer exists, and the Langfuse client starts one.
# Langfuse doesn't export those HTTP spans, so each trace's root would point at a parent it never sees.
app = FastAPI(telemetry={"tracing": False})


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: list[dict]
    trace_url: str | None = None


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Get or create the session. A new SQLiteSession on the same file sees the same history.
    session_id = request.session_id or str(uuid.uuid4())
    session = SQLiteSession(session_id, SESSIONS_DB)

    try:
        result = await answer(request.message, session=session)
    except Exception as e:
        # Auth, billing, a model that is not running: show it in the chat, not as a 500.
        result = {"response": f"Model call failed: {type(e).__name__}: {str(e)[:300]}", "tool_calls": []}

    return ChatResponse(session_id=session_id, **result)


@app.post("/clear")
async def clear(session_id: str | None = None):
    if session_id:
        await SQLiteSession(session_id, SESSIONS_DB).clear_session()
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
