import asyncio
import html
import json
import uuid
from pathlib import Path

import uvicorn
from agents import Agent, ModelSettings, RunContextWrapper, RunHooks, Runner, function_tool, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse

import wikipedia
from context_panel import AgentContexts, PanelHooks, add_context_panel

# WIKIMEDIA_USERNAME and WIKIMEDIA_PASSWORD come from the .env file next to this one.
load_dotenv(Path(__file__).parent / ".env")

# Traces upload to OpenAI by default, which needs an OpenAI key. We're on Gemini.
set_tracing_disabled(True)

# LiteLLM routes the call to Gemini. api_key is unused: Vertex AI uses your gcloud credentials.
MODEL = LitellmModel(model="vertex_ai/gemini-3.5-flash-lite", api_key="unused")
# Judging takes a stronger model than drafting: flash-lite passes slides with obvious tells.
CRITIC_MODEL = LitellmModel(model="vertex_ai/gemini-3.5-flash", api_key="unused")
# A stalled model call would hang the page: give up after 90 s, and retry twice.
SETTINGS = ModelSettings(extra_args={"vertex_location": "global", "timeout": 90, "num_retries": 2})


# --- Background agents: Claude Code's pattern, for any agent ---


def notification(agent_id: str, description: str, run: asyncio.Task) -> str:
    """The message the main agent gets when a background agent stops, in Claude Code's format."""
    if run.cancelled():
        status, summary, result = "stopped", f'Agent "{description}" was stopped', ""
    elif run.exception():
        status, summary, result = "failed", f'Agent "{description}" failed: {run.exception()}', ""
    else:
        status, summary, result = "completed", f'Agent "{description}" completed', run.result().final_output
    return (
        f"<task-notification>\n<task-id>{agent_id}</task-id>\n<status>{status}</status>\n"
        f"<summary>{summary}</summary>\n<result>{result}</result>\n</task-notification>"
    )


class BackgroundAgents:
    """Sub-agents that work while the agent that started them keeps going, as in Claude Code.

    Pass this object as the run's context, and call start() from an async tool: the SDK runs a sync
    tool in a worker thread, which has no event loop to start a run on. start() returns at once.
    run() is an inbox loop: the main agent takes a turn with whatever is in its inbox, its turn can
    end while sub-agents work, and each sub-agent that stops puts a <task-notification> message in
    the inbox, which wakes it for another turn.
    """

    def __init__(self, hooks: RunHooks):
        self.hooks = hooks
        self.runs: list[asyncio.Task] = []
        self.inbox: asyncio.Queue[str] = asyncio.Queue()  # messages for the main agent: the user's, and each sub-agent's notification
        self.unread = 0  # messages the main agent hasn't read, counting sub-agents that haven't stopped

    def start(self, agent: Agent, prompt: str, description: str) -> str:
        """Start agent on prompt in the background. Returns the message for the tool to return."""
        agent_id = f"agent-{len(self.runs) + 1}"
        # A numbered copy, so each run gets its own column in the context panel
        agent = agent.clone(name=f"{agent.name} {len(self.runs) + 1}")
        # create_task, not await: the run starts now, and start() returns without waiting for it
        run = asyncio.create_task(Runner.run(agent, prompt, context=self, hooks=self.hooks, max_turns=10))
        # When the run stops, however it stops, queue its notification
        run.add_done_callback(lambda run: self.inbox.put_nowait(notification(agent_id, description, run)))
        self.runs.append(run)
        self.unread += 1
        return (
            f"Async agent launched successfully.\nagent_id: {agent_id}\nThe agent is working in the background. "
            "You will be notified automatically when it completes. Don't wait for it or check on it."
        )

    async def run(self, agent: Agent, input: str, max_turns: int = 20):
        """Run agent until its turn ends with no messages left to read. Returns the last turn's result."""
        self.inbox.put_nowait(input)  # the user's message is the first in the inbox
        self.unread += 1
        history = []
        while True:
            # Wait for a message, plus any others that arrived during the last turn
            messages = [await self.inbox.get()]
            while not self.inbox.empty():
                messages.append(self.inbox.get_nowait())
            self.unread -= len(messages)
            history += [{"role": "user", "content": message} for message in messages]
            result = await Runner.run(agent, history, context=self, hooks=self.hooks, max_turns=max_turns)
            history = result.to_input_list()
            if not self.unread:
                return result  # its turn is over, and no sub-agent is still out

    def cancel(self) -> None:
        for run in self.runs:
            run.cancel()


# --- Tools ---


@function_tool
def get_article(url: str) -> str:
    """Get the text of an English Wikipedia article, and the articles it links to.

    Args:
        url: The article's URL, e.g. 'https://en.wikipedia.org/wiki/Ada_Lovelace'.
    """
    try:
        article = wikipedia.fetch_article(url)
    except Exception as e:
        # The model cannot see an exception. Return something it can reason about.
        return json.dumps({"error": f"Could not fetch {url}: {type(e).__name__}: {e}"})
    links = "\n".join(f"- {link['text']}: {link['url']}" for link in article["links"])
    return f"# {article['title']}\n{article['description']}\nSource: {article['url']}\n\n{article['text']}\n\n## Links\n{links}"


# --- The researcher: one slide, from the articles the editor points it to ---

researcher = Agent(
    name="Researcher",
    instructions="""\
You research and write one slide of a Remark.js deck. Your task names the topic and some
Wikipedia articles to start from.

1. Read the articles with get_article. If they don't cover the topic, follow one of their links.
   Read at most 3 articles in all.
2. Reply with the slide and nothing else, using only facts from what you read:
   - A # heading, then at most 5 bullets, each starting with "- ".
   - End every bullet with a link to the article its fact came from, titled with the article's
     title, e.g. ([Harvard Mark I](https://en.wikipedia.org/wiki/Harvard_Mark_I)). Cite only
     articles you read.""",
    model=MODEL,
    model_settings=SETTINGS,
    tools=[get_article],
)


@function_tool
async def start_researcher(ctx: RunContextWrapper[BackgroundAgents], description: str, prompt: str) -> str:
    """Start a researcher in the background. It returns at once: the researcher works while you do.

    Args:
        description: A short description of the task, e.g. 'Slide 2: the Analytical Engine'.
        prompt: The researcher's whole task: the topic, and the URLs of the articles to start from.
    """
    return ctx.context.start(researcher, prompt, description)


# --- The critic: wikipedia-deck-critic's, for one slide instead of a deck ---

# A rubric from Wikipedia:Signs_of_AI_writing (https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).
critic = Agent(
    name="Critic",
    instructions="""\
You review slides for signs of AI writing, using this rubric from Wikipedia's "Signs of AI
writing" guide. A slide fails an item only if you can quote the text that breaks it.

1. Undue emphasis on significance or legacy: "stands as", "is a testament", "a pivotal/crucial
   role", "underscores its importance", "reflects broader", "enduring legacy", "indelible mark",
   "evolving landscape", "setting the stage for".
2. Promotional language: "boasts", "vibrant", "rich", "profound", "renowned", "groundbreaking",
   "showcasing", "nestled", "in the heart of", "diverse array", "commitment to".
3. Superficial analysis: a sentence that ends in an -ing phrase adding vague significance
   ("..., highlighting its influence", "..., underscoring the need for").
4. Vague attribution: "experts say", "is widely regarded", "many believe", with no named source.
5. AI vocabulary: "Additionally" starting a sentence, "delve", "crucial", "intricate",
   "interplay", "tapestry", "meticulous", "underscore", "foster", "enhance", "align with".
6. Copula avoidance: "serves as", "stands as", "functions as" where "is" would do.
7. Negative parallelism: "not just X, but also Y", "not X, but Y", "Y rather than X".
8. Rule of three: lists of exactly three adjectives or phrases used by reflex.
9. Style: Title Case Headings, bold text inside bullets, "**Label:** text" bullets, emoji,
   curly quotes.
10. Talking to the reader: "I hope this helps", "Let me know", "In summary", "In conclusion",
    or any note about the task itself.

Check the heading and every bullet against each item, one item at a time. Facts are not your
job: judge only the writing. If no item clearly fails, the slide passes.

Reply in plain text. The first line is exactly PASS or REVISE.
If REVISE, list at most 6 problems, one per line: the rubric item number, the exact text in
quotes, and a plainer rewrite. Don't rewrite the whole slide.""",
    model=CRITIC_MODEL,
    model_settings=SETTINGS,
)

# One review at a time: two critics at once would write over each other in the context panel
review_lock = asyncio.Lock()
# What a bullet's citation looks like: a markdown link to an English Wikipedia article
CITATION = "](https://en.wikipedia.org/wiki/"


@function_tool
async def review_slide(ctx: RunContextWrapper[BackgroundAgents], slide: str) -> str:
    """Have a critic review one slide for signs of AI writing, and check that every bullet cites
    its Wikipedia article. Waits for the verdict.

    Args:
        slide: The slide's markdown.
    """
    async with review_lock:
        result = await Runner.run(critic, slide, hooks=ctx.context.hooks)
    verdict = str(result.final_output).strip()
    # A deterministic check, no model needed: every bullet cites the Wikipedia article it came from
    uncited = [line for line in slide.splitlines() if line.lstrip().startswith(("- ", "* ")) and CITATION not in line]
    if not uncited:
        return verdict
    problems = verdict.removeprefix("PASS").removeprefix("REVISE").strip()
    cuts = [f'Uncited: "{line.strip()}" -> cut it' for line in uncited]
    return "\n".join(["REVISE"] + ([problems] if problems else []) + cuts)


# --- The editor: plans the deck, starts the researchers, and reviews what they send back ---

editor = Agent(
    name="Editor",
    instructions="""\
You edit a short Remark.js slide deck about a Wikipedia article. Researchers write the slides.
You plan the deck, write the title slide, and review every slide.

1. Call get_article with the URL the user gives you.
2. Pick 3 topics for slides 2, 3, and 4. For each, call start_researcher. Its prompt names the
   topic and 2 or 3 URLs from the article's links that cover it: other articles, never the
   article itself.
3. Reply with the title slide: the line `class: center, middle`, a # heading, and one line
   saying what the article is about. Don't wait for the researchers: you'll get a
   <task-notification> message as each one finishes.

When a <task-notification> arrives:
- If it completed, call review_slide with the slide in its <result>. If the review starts with
  REVISE, replace each text it quotes with its rewrite. Reply with the slide as it should go in.
- If it failed, write that slide yourself from the first article, ending each bullet with a link
  to it, and reply with the slide.
- Once you have slides 2, 3, and 4, reply with the whole deck instead, and nothing else: slides 1
  to 4 in order, separated by lines that contain only ---.
Every bullet ends with a link to the article its fact came from. Keep those links exactly as
they are, in every slide and in the whole deck.""",
    model=MODEL,
    model_settings=SETTINGS,
    tools=[get_article, start_researcher, review_slide],
)


# --- FastAPI App ---

HERE = Path(__file__).parent
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
async def run(url: str):
    """Build one deck and stream what happens as Server-Sent Events."""
    run_id = str(uuid.uuid4())
    sessions[run_id] = AgentContexts()
    queue: asyncio.Queue = asyncio.Queue()
    background = BackgroundAgents(PanelHooks(sessions[run_id], queue.put_nowait))

    async def work():
        try:
            result = await background.run(editor, url)
            queue.put_nowait({"type": "done", "markdown": str(result.final_output)})
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
            # The page closed the stream: stop spending tokens, in the editor and every researcher
            task.cancel()
            background.cancel()

    return StreamingResponse(events(), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
