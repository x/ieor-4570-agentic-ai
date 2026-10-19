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
We are playing a guessing game. First, choose a single everyday object and think of it, but DO NOT SAY WHAT IT IS in your replies and DO NOT GIVE CLUES.
When the user starts the game, reply with:
"I have my object in mind. You have 5 questions remaining."
Then the user will ask yes-or-no questions. With either:
- "Yes. You have N questions remaining."
- "No. You have N questions remaining."
If the user is out of questions (0 questions remaining), say either:
- "Yes. You must now guess the object."
- "No. You must now guess the object."
If the user's guess is correct, reply with "You're correct! You win!"
If the user's guess is incorrect, reply with "You're incorrect. It was <your object>. You lose."
Never ask questions. Never name the object until the game is over. Never give clues.
When the user has no questions remaining, wait for them to guess or give up.
Stay consistent with your earlier answers."""

# The models the page offers. Gemini 3 can't switch thinking off; the older 2.5 can.
MODELS = {
    "gemini-2.5-flash-lite": {"vertex_location": "us-east1", "reasoning_effort": "disable"},
    "gemini-3.5-flash-lite": {"vertex_location": "global", "reasoning_effort": "low"},
}

# --- Session Store ---

# session_id -> list of messages. In-memory, single process.
sessions: dict[str, list] = {}
models: dict[str, str] = {}  # session_id -> key in MODELS

# --- The Model Call ---


def complete(session_id: str) -> str:
    """Append the model's next reply to the session and return its text."""
    messages = sessions[session_id]
    reply = litellm.completion(
        # Only role and content go to the model: hidden thinking from earlier turns is dropped.
        messages=[{"role": m["role"], "content": m["content"]} for m in messages],
        model="vertex_ai/" + models[session_id],
        **MODELS[models[session_id]],
    ).choices[0].message

    entry = {"role": "assistant", "content": reply.content or ""}
    if getattr(reply, "reasoning_content", None):
        entry["thinking"] = reply.reasoning_content  # kept for the context panel, never sent back
    messages += [entry]
    return entry["content"]


# --- FastAPI App ---

app = FastAPI()
add_context_panel(app, sessions)


class ChatRequest(BaseModel):
    message: str
    session_id: str


@app.get("/")
def index():
    # no-cache: browsers otherwise keep serving an old page after a redeploy
    return FileResponse(Path(__file__).parent / "index.html", headers={"Cache-Control": "no-cache"})


@app.post("/new")
def new_game(model: str = "gemini-2.5-flash-lite"):
    if model not in MODELS:
        raise HTTPException(400, f"model must be one of {list(MODELS)}")
    session_id = str(uuid.uuid4())
    sessions[session_id] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Let's play 5 questions."},
    ]
    models[session_id] = model
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
