import uuid
from pathlib import Path

import chromadb
import uvicorn
from agents import Agent, ModelSettings, Runner, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Traces upload to OpenAI by default, which needs an OpenAI key. We're on Gemini.
set_tracing_disabled(True)

# --- The Index ---

# index_items.py builds this once, offline. The app only reads it.
CHROMA_PATH = Path(__file__).parent / "chroma_data"
TOP_K = 3

try:
    collection = chromadb.PersistentClient(path=str(CHROMA_PATH)).get_collection("magic_items")
except Exception:
    raise SystemExit("No index found. Run `uv run index_items.py` first.")


def search_magic_items(query: str) -> str:
    """Return the TOP_K items whose embeddings are closest to the query's embedding."""
    results = collection.query(query_texts=[query], n_results=TOP_K)
    documents, distances = results["documents"][0], results["distances"][0]
    return "\n---\n".join(
        f"[relevance: {1 - dist:.2f}]\n{doc}" for doc, dist in zip(documents, distances)
    )


# --- The Agent ---

# No tools: the model never decides to search. The pipeline below searches for it.
agent = Agent(
    name="Keeper",
    instructions="""\
<role>
You are the Keeper of Curious Things, proprietor of a magic item shop that exists
in the spaces between planes. You speak with quiet authority, as though you have
seen the rise and fall of empires and found them all mildly interesting.
</role>

<instructions>
- Each customer message arrives with items from your shelves in <context>.
  Only offer items from the context.
- Describe each item's type, rarity, and whether it requires attunement.
</instructions>
""",
    # LiteLLM routes the call to Gemini, the same way agents-sdk-web does.
    # api_key is unused: Vertex AI authenticates with your gcloud credentials.
    model=LitellmModel(model="vertex_ai/gemini-3.5-flash-lite", api_key="unused"),
    model_settings=ModelSettings(extra_args={"vertex_location": "global"}),
)

# --- The Pipeline ---


async def run_rag(message: str) -> tuple[str, str]:
    """One pass, the same on every message: retrieve, augment, generate."""
    # 1-2. Embed the user's message, verbatim, and retrieve. Every message, no exceptions.
    docs = search_magic_items(message)

    # 3. Augment: paste the retrieved items in front of the message
    prompt = f"<context>\n{docs}\n</context>\n\n{message}"

    # 4. Generate: an agent with no tools, so the Runner makes exactly one model call
    result = await Runner.run(agent, prompt)
    return result.final_output, docs


# --- FastAPI App ---

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    retrieved: str


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # No session: like Lewis et al., every message is answered on its own.
    # The id only exists so index.html works unchanged.
    session_id = request.session_id or str(uuid.uuid4())

    try:
        response, retrieved = await run_rag(request.message)
    except Exception as e:
        # Auth, billing, a model that is not running: show it in the chat, not as a 500.
        response, retrieved = f"Model call failed: {type(e).__name__}: {str(e)[:300]}", ""

    return ChatResponse(response=response, session_id=session_id, retrieved=retrieved)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
