import json
import uuid
from pathlib import Path

import chromadb
import uvicorn
from agents import Agent, ModelSettings, Runner, RunHooks, SQLiteSession, function_tool, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Traces upload to OpenAI by default, which needs an OpenAI key. We're on Gemini.
set_tracing_disabled(True)

# --- Tools ---

# index_items.py builds this once, offline. The app only reads it.
CHROMA_PATH = Path(__file__).parent / "chroma_data"
TOP_K = 3

try:
    collection = chromadb.PersistentClient(path=str(CHROMA_PATH)).get_collection("magic_items")
except Exception:
    raise SystemExit("No index found. Run `uv run index_items.py` first.")


# @function_tool builds the JSON schema from the signature and docstring.
@function_tool
def search_magic_items(query: str) -> str:
    """Search the shop's inventory for magic items matching a description. Use this whenever
    a customer asks about items, their properties, or what you have available.

    Args:
        query: A natural-language description of the items to search for,
            e.g. 'a sword that deals fire damage'.
    """
    results = collection.query(query_texts=[query], n_results=TOP_K)
    documents, distances = results["documents"][0], results["distances"][0]
    return "\n---\n".join(
        f"[relevance: {1 - dist:.2f}]\n{doc}" for doc, dist in zip(documents, distances)
    )


# --- The Agent ---

agent = Agent(
    name="Keeper",
    instructions="""\
<role>
You are the Keeper of Curious Things, proprietor of a magic item shop that exists
in the spaces between planes. You speak with quiet authority, as though you have
seen the rise and fall of empires and found them all mildly interesting.
</role>

<instructions>
- When a customer asks about magic items, call search_magic_items before answering.
  Only offer items the search returned.
- Describe each item's type, rarity, and whether it requires attunement.
- For small talk, answer directly without searching.
</instructions>
""",
    # LiteLLM routes the call to Gemini, the same way agents-sdk-web does.
    # api_key is unused: Vertex AI authenticates with your gcloud credentials.
    model=LitellmModel(model="vertex_ai/gemini-3.5-flash-lite", api_key="unused"),
    model_settings=ModelSettings(extra_args={"vertex_location": "global"}),
    tools=[search_magic_items],
)


class RecordToolCalls(RunHooks):
    """Watches the run and records each tool call, for the page to show.

    Make a new one per request: it holds this run's calls.
    """

    def __init__(self):
        self.tool_calls = []

    async def on_tool_end(self, context, agent, tool, result):
        # For a function tool, context is a ToolContext: it carries the call's arguments.
        self.tool_calls += [{"name": tool.name, "args": json.loads(context.tool_arguments), "result": result}]


# --- Session Store ---

SESSIONS_DB = "conversations.db"

# --- FastAPI App ---

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: list[dict]


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Get or create the session. A new SQLiteSession on the same file sees the same history.
    session_id = request.session_id or str(uuid.uuid4())
    session = SQLiteSession(session_id, SESSIONS_DB)
    hooks = RecordToolCalls()

    try:
        # The Runner is our run_agent() loop. The session loads and saves the history.
        result = await Runner.run(agent, request.message, session=session, hooks=hooks)
        response, tool_calls = result.final_output, hooks.tool_calls
    except Exception as e:
        # Auth, billing, a model that is not running: show it in the chat, not as a 500.
        response, tool_calls = f"Model call failed: {type(e).__name__}: {str(e)[:300]}", []

    return ChatResponse(response=response, session_id=session_id, tool_calls=tool_calls)


@app.post("/clear")
async def clear(session_id: str | None = None):
    if session_id:
        await SQLiteSession(session_id, SESSIONS_DB).clear_session()
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
