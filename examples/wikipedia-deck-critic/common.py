"""What the three generator-critic variations share: the model, the deck context, the tools,
the two agents' instructions, and the hooks that stream each agent's context to the page."""

import asyncio
import json
from dataclasses import dataclass

from agents import ModelSettings, RunContextWrapper, function_tool, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel

import wikipedia
from context_panel import AgentContexts, PanelHooks

# Traces upload to OpenAI by default, which needs an OpenAI key. We're on Gemini.
set_tracing_disabled(True)

# LiteLLM routes the call to Gemini. api_key is unused: Vertex AI uses your gcloud credentials.
MODEL = LitellmModel(model="vertex_ai/gemini-3.5-flash-lite", api_key="unused")
# Judging takes a stronger model than drafting: flash-lite passes decks with obvious tells.
CRITIC_MODEL = LitellmModel(model="vertex_ai/gemini-3.5-flash", api_key="unused")
# A stalled model call would hang the page: give up after 90 s, and retry twice.
VERTEX = {"vertex_location": "global", "timeout": 90, "num_retries": 2}
SETTINGS = ModelSettings(extra_args=VERTEX)

# The critic gets this many reviews. After that, the deck ships as it is.
MAX_ROUNDS = 3


# --- Shared state ---


@dataclass
class DeckContext:
    """One run's state. Every agent and tool in the run sees the same object, and the model never does."""

    url: str
    deck: str = ""  # the latest draft, written by save_deck
    rounds: int = 0  # how many times the critic has reviewed a draft


# --- Tools ---


@function_tool
def get_article(url: str) -> str:
    """Get the text of an English Wikipedia article.

    Args:
        url: The article's URL, e.g. 'https://en.wikipedia.org/wiki/Ada_Lovelace'.
    """
    try:
        article = wikipedia.fetch_article(url)
    except Exception as e:
        # The model cannot see an exception. Return something it can reason about.
        return json.dumps({"error": f"Could not fetch {url}: {type(e).__name__}: {e}"})
    return f"# {article['title']}\n{article['description']}\nSource: {article['url']}\n\n{article['text']}"


@function_tool
def save_deck(ctx: RunContextWrapper[DeckContext], markdown: str) -> str:
    """Save a draft of the slide deck. Call this with the whole deck every time you change it.

    Args:
        markdown: The full deck in Remark markdown, slides separated by lines containing only ---.
    """
    slides = [s for s in markdown.split("\n---\n") if s.strip()]
    if not 3 <= len(slides) <= 5:
        # A deterministic check: no model needed to count slides.
        return json.dumps({"error": f"The deck has {len(slides)} slides. It needs 3 to 5. Not saved."})
    ctx.context.deck = markdown
    return json.dumps({"saved": True, "slides": len(slides)})


# --- Instructions ---

GENERATOR = """\
You turn a Wikipedia article into a short slide deck for Remark.js.

1. Call get_article with the URL the user gives you.
2. Write a deck of 3 to 5 slides in Remark markdown, using only facts from the article:
   - Separate slides with a line that contains only ---
   - The first slide is the title slide. Its first line is `class: center, middle`, then a # heading.
   - Every other slide starts with a # heading, then at most 5 bullets.
   - End the last slide with the article's URL as the source.
3. Call save_deck with the whole deck."""

# A rubric from Wikipedia:Signs_of_AI_writing (https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).
# Each item is a yes/no check the critic can point to in the text.
RUBRIC = """\
You review slide decks for signs of AI writing, using this rubric from Wikipedia's
"Signs of AI writing" guide. A deck fails an item only if you can quote the text that breaks it.

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

Check every heading and bullet against each item, one item at a time. Facts are not your job:
judge only the writing. If no item clearly fails, the deck passes."""

VERDICT_FORMAT = """\
Reply in plain text. The first line is exactly PASS or REVISE.
If REVISE, list at most 6 problems, one per line: the rubric item number, the exact text in
quotes, and a plainer rewrite. Don't rewrite the whole deck."""


# --- Hooks: stream each agent's context to the page ---


class StreamContext(PanelHooks):
    """PanelHooks (each agent's context, plus an activity feed) onto a queue that app.py streams to
    the page, plus an output event every time the generator saves a draft."""

    def __init__(self, queue: asyncio.Queue, contexts: AgentContexts):
        super().__init__(contexts, queue.put_nowait)

    async def on_tool_end(self, context, agent, tool, result):
        if tool.name == "save_deck" and context.context.deck:
            self.emit({"type": "output", "markdown": context.context.deck})
