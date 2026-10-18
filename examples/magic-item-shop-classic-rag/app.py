import uuid
from pathlib import Path

import chromadb
import litellm
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

# --- Config ---

SYSTEM_PROMPT = """\
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
"""
TOP_K = 3

# --- The Index ---

# index_items.py builds this once, offline. The app only reads it.
CHROMA_PATH = Path(__file__).parent / "chroma_data"
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


# --- The Pipeline ---


def run_rag(message: str) -> tuple[str, str]:
    """One pass, the same on every message: retrieve, augment, generate."""
    # 1-2. Embed the user's message, verbatim, and retrieve. Every message, no exceptions.
    docs = search_magic_items(message)

    # 3. Augment: paste the retrieved items into the prompt
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"<context>\n{docs}\n</context>\n\n{message}"},
    ]

    # 4. Generate: one completion, no tools, no loop
    reply = litellm.completion(
        model="vertex_ai/gemini-3.5-flash-lite",
        vertex_location="global",
        messages=messages,
    ).choices[0].message

    return reply.content, docs


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
def chat(request: ChatRequest):
    # No session: like Lewis et al., every message is answered on its own.
    # The id only exists so index.html works unchanged.
    session_id = request.session_id or str(uuid.uuid4())

    try:
        response, docs = run_rag(request.message)
        # Not a tool call, but shown like one so the page displays what was retrieved
        retrieval = [{"name": "search_magic_items", "args": {"query": request.message}, "result": docs}]
    except Exception as e:
        # Auth, billing, a model that is not running: show it in the chat, not as a 500.
        response, retrieval = f"Model call failed: {type(e).__name__}: {str(e)[:300]}", []

    return ChatResponse(response=response, session_id=session_id, tool_calls=retrieval)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
