import re
import uuid
from pathlib import Path

import litellm
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from context_panel import add_context_panel

# --- Config ---

SYSTEM_PROMPT = """
We are playing a guessing game. Think of a single everyday object,
but DO NOT SAY WHAT IT IS and DO NOT GIVE CLUES. The user will ask yes-or-no questions.
Reply to each question with exactly one line in this form:
"Yes. You have N questions remaining." or "No. You have N questions remaining."
Never ask questions. Never name the object. Never give clues.
When the user has no questions remaining, wait for them to guess or give up.
Stay consistent with your earlier answers. Only reveal the object
if the user gives up and asks what it was."""

THINK_IN_TRANSCRIPT = """
Before every reply, think inside <think></think> tags; the user never sees what's inside them.
In your first reply, choose the object inside the think tags."""

# Three ways to play. Only "transcript" keeps the model's thinking in its context.
MODES = {
    # An older, smaller Gemini, because it can switch thinking off entirely (Gemini 3 can't).
    "none": {"model": "vertex_ai/gemini-2.5-flash-lite", "vertex_location": "us-east1", "reasoning_effort": "disable"},
    # Gemini's own hidden thinking. Like most chat APIs, it isn't sent back on the next turn.
    "hidden": {"model": "vertex_ai/gemini-3.5-flash-lite", "vertex_location": "global", "reasoning_effort": "low"},
    # No hidden thinking: the model writes <think> tags into its reply, so they stay in the context.
    "transcript": {"model": "vertex_ai/gemini-2.5-flash-lite", "vertex_location": "us-east1", "reasoning_effort": "disable"},
}

# --- Session Store ---

# session_id -> list of messages. In-memory, single process.
sessions: dict[str, list] = {}
modes: dict[str, str] = {}

# --- The Model Call ---


def complete(session_id: str) -> str:
    """Append the model's next reply to the session and return the part the player sees."""
    messages = sessions[session_id]
    reply = litellm.completion(
        # Only role and content go to the model: hidden thinking from earlier turns is dropped.
        messages=[{"role": m["role"], "content": m["content"]} for m in messages],
        **MODES[modes[session_id]],
    ).choices[0].message

    entry = {"role": "assistant", "content": reply.content or ""}
    if getattr(reply, "reasoning_content", None):
        entry["thinking"] = reply.reasoning_content  # kept for the context panel, never sent back
    messages += [entry]
    return re.sub(r"<think>.*?</think>\s*", "", entry["content"], flags=re.S)


# --- FastAPI App ---

app = FastAPI()
add_context_panel(app, sessions)


class ChatRequest(BaseModel):
    message: str
    session_id: str


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.post("/new")
def new_game(mode: str = "none"):
    if mode not in MODES:
        raise HTTPException(400, f"mode must be one of {list(MODES)}")
    session_id = str(uuid.uuid4())
    prompt = SYSTEM_PROMPT + (THINK_IN_TRANSCRIPT if mode == "transcript" else "")
    sessions[session_id] = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": "Let's play 5 questions."},
    ]
    modes[session_id] = mode
    # The model writes its own opening line, so with thinking on it can choose an object now.
    try:
        opening = complete(session_id)
    except Exception as e:
        raise HTTPException(502, f"Model call failed: {type(e).__name__}: {str(e)[:300]}")
    return {"session_id": session_id, "response": opening}


@app.post("/chat")
def chat(request: ChatRequest):
    messages = sessions.get(request.session_id)
    if messages is None:
        raise HTTPException(404, "Unknown session. Start a new game.")

    messages += [{"role": "user", "content": request.message}]
    try:
        return {"response": complete(request.session_id)}
    except Exception as e:
        # Take the question back out so the context matches what the page shows.
        messages.pop()
        raise HTTPException(502, f"Model call failed: {type(e).__name__}: {str(e)[:300]}")


@app.post("/rewind")
def rewind(session_id: str):
    # Erase the last question and its answer, never the opening (system, user, assistant).
    messages = sessions.get(session_id, [])
    if len(messages) > 3:
        del messages[-2:]
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
