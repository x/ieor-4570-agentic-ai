import json
import uuid
from pathlib import Path

import uvicorn
from agents import ModelSettings, Runner, RunHooks, SQLiteSession, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel
from agents.run import RunConfig
from agents.sandbox import Manifest, SandboxAgent, SandboxPathGrant, SandboxRunConfig
from agents.sandbox.capabilities import Shell
from agents.sandbox.sandboxes.unix_local import UnixLocalSandboxClient
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Traces upload to OpenAI by default, which needs an OpenAI key. We're on Gemini.
set_tracing_disabled(True)

# --- The Workspace ---

# No index: the corpus is the markdown files, organized as items/<type>/<rarity>/<Item>.md.
# The sandbox gets read-only access to them where they are. Nothing is copied.
ITEMS_DIR = (Path(__file__).parent / "items").resolve()
manifest = Manifest(extra_path_grants=(SandboxPathGrant(path=str(ITEMS_DIR), read_only=True),))

# --- The Agent ---

agent = SandboxAgent(
    name="Keeper",
    instructions=f"""\
<role>
You are the Keeper of Curious Things, proprietor of a magic item shop that exists
in the spaces between planes. You speak with quiet authority, as though you have
seen the rise and fall of empires and found them all mildly interesting.
</role>

<instructions>
- Your inventory is in {ITEMS_DIR}, one markdown file per item, filed as
  <type>/<rarity>/<Item>.md. It is read-only. Types: armor, potion, ring, rod, scroll, staff,
  wand, weapon, wondrous, other. Rarities: common, uncommon, rare, very-rare,
  legendary, artifact, varies.
- When a customer asks about items, search the shelves with ls, grep, and cat
  (rg is not installed) before answering. Only offer items whose files you have read.
- Describe each item's type, rarity, and whether it requires attunement.
- For small talk, answer directly without searching.
</instructions>
""",
    default_manifest=manifest,
    # Shell gives the model one tool, exec_command. We leave out Filesystem (apply_patch):
    # the Keeper reads the shelves, it doesn't rewrite them.
    capabilities=[Shell()],
    # LiteLLM routes the call to Gemini, the same way agents-sdk-web does.
    # api_key is unused: Vertex AI authenticates with your gcloud credentials.
    model=LitellmModel(model="vertex_ai/gemini-3.5-flash-lite", api_key="unused"),
    model_settings=ModelSettings(extra_args={"vertex_location": "global"}),
)

# Unix-local runs commands in a temporary directory on this machine. On macOS, sandbox-exec
# enforces the read-only grant; Linux has no confinement. Use DockerSandboxClient for real isolation.
run_config = RunConfig(sandbox=SandboxRunConfig(client=UnixLocalSandboxClient()))


class RecordToolCalls(RunHooks):
    """Watches the run and records each tool call, for the page to show.

    Make a new one per request: it holds this run's calls.
    """

    def __init__(self):
        self.tool_calls = []

    async def on_tool_end(self, context, agent, tool, result):
        self.tool_calls += [{"name": tool.name, "args": json.loads(context.tool_arguments), "result": str(result)}]


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
    session_id = request.session_id or str(uuid.uuid4())
    session = SQLiteSession(session_id, SESSIONS_DB)
    hooks = RecordToolCalls()

    try:
        result = await Runner.run(agent, request.message, session=session, hooks=hooks, run_config=run_config)
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
