import asyncio
import html
import json
import uuid
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse

# WIKIMEDIA_USERNAME and WIKIMEDIA_PASSWORD come from the .env file next to this one.
load_dotenv(Path(__file__).parent / ".env")

import call_loop  # noqa: E402
import critic_tool  # noqa: E402
import handoffs  # noqa: E402
from common import DeckContext, StreamContext  # noqa: E402
from context_panel import AgentContexts, add_context_panel  # noqa: E402

HERE = Path(__file__).parent
METHODS = {"call-loop": call_loop.run, "handoffs": handoffs.run, "critic-tool": critic_tool.run}
SLIDES_PAGE = (HERE / "slides.html").read_text()

# run_id -> every agent's context, in order. In-memory, single process. The context panel reads it.
sessions: dict[str, AgentContexts] = {}

app = FastAPI()
add_context_panel(app, sessions)


@app.get("/")
def index():
    # no-cache: browsers otherwise keep serving an old page after a redeploy
    return FileResponse(HERE / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/slides", response_class=HTMLResponse)
def slides(md: str):
    """The deck's markdown arrives in the URL. Remark reads it from a <textarea>, so escape it."""
    return SLIDES_PAGE.replace("{{markdown}}", html.escape(md))


@app.get("/run")
async def run(url: str, method: str):
    """Run one generator-critic loop and stream what happens as Server-Sent Events."""
    if method not in METHODS:
        raise HTTPException(400, f"method must be one of {list(METHODS)}")
    run_id = str(uuid.uuid4())
    sessions[run_id] = AgentContexts()
    queue: asyncio.Queue = asyncio.Queue()
    ctx = DeckContext(url=url)
    hooks = StreamContext(queue, sessions[run_id])

    async def work():
        try:
            await METHODS[method](ctx, hooks)
            queue.put_nowait({"type": "done", "rounds": ctx.rounds, "markdown": ctx.deck})
        except Exception as e:
            # Auth, quota, a model that won't stop: show it on the page, not as a dropped stream.
            queue.put_nowait({"type": "error", "message": f"{type(e).__name__}: {str(e)[:500]}"})

    task = asyncio.create_task(work())

    async def events():
        try:
            yield f"data: {json.dumps({'type': 'start', 'run_id': run_id})}\n\n"
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event, default=str)}\n\n"
                if event["type"] in ("done", "error"):
                    break
        finally:
            task.cancel()  # the page closed the stream: stop spending tokens

    return StreamingResponse(events(), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
