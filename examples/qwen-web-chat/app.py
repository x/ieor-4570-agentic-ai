import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from litellm import completion
from pydantic import BaseModel

# --- Config ---

# Ollama serves the model on http://localhost:11434.
# Run `ollama pull qwen2.5:1.5b` once before starting this server.
MODEL = "ollama_chat/qwen2.5:1.5b"
SYSTEM_PROMPT = "You are a polite and knowledgeable AI assistant. Keep answers short."


def generate_response(messages: list[dict]) -> str:
    # The messages list goes straight to the model server. Ollama applies
    # the model's chat template; we never write the special tokens by hand.
    response = completion(
        model=MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=128,
    )
    return response.choices[0].message.content.strip()


# --- Session Store ---

# session_id -> list of {"role": ..., "content": ...}
# In-memory, single process. Use Redis or a database in production.
sessions: dict[str, list[dict]] = {}

# --- FastAPI App ---

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # 1. Get or create the session
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in sessions:
        sessions[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 2. Append the user turn
    sessions[session_id].append({"role": "user", "content": request.message})

    # 3. Generate the assistant turn from the whole transcript
    reply = generate_response(sessions[session_id])

    # 4. Append it, so the next request sees it
    sessions[session_id].append({"role": "assistant", "content": reply})

    return ChatResponse(response=reply, session_id=session_id)


@app.post("/clear")
def clear(session_id: str | None = None):
    if session_id and session_id in sessions:
        del sessions[session_id]
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
