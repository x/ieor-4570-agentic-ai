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

# Every game starts from this transcript. The assistant line is scripted: no object was chosen.
OPENING = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "Let's play 5 questions."},
    {"role": "assistant", "content": "I have my object in mind. You have 5 questions remaining."},
]

# --- Session Store ---

# session_id -> list of messages. In-memory, single process.
sessions: dict[str, list] = {}

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
def new_game():
    session_id = str(uuid.uuid4())
    sessions[session_id] = list(OPENING)
    return {"session_id": session_id}


@app.post("/chat")
def chat(request: ChatRequest):
    messages = sessions.get(request.session_id)
    if messages is None:
        raise HTTPException(404, "Unknown session. Start a new game.")

    messages += [{"role": "user", "content": request.message}]

    try:
        reply = litellm.completion(
            model="vertex_ai/gemini-3.5-flash-lite",
            vertex_location="global",
            # No hidden thinking: each answer is sampled from the visible transcript alone.
            reasoning_effort="none",
            messages=messages,
        ).choices[0].message.content
    except Exception as e:
        # Take the question back out so the context matches what the page shows.
        messages.pop()
        raise HTTPException(502, f"Model call failed: {type(e).__name__}: {str(e)[:300]}")

    messages += [{"role": "assistant", "content": reply}]
    return {"response": reply}


@app.post("/rewind")
def rewind(session_id: str):
    # Erase the last question and its answer, never the opening.
    messages = sessions.get(session_id, [])
    if len(messages) > len(OPENING):
        del messages[-2:]
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
