import asyncio
import json
from pathlib import Path

import duckdb
import uvicorn
from agents import Agent, ModelSettings, Runner, function_tool, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse

from context_panel import AgentContexts, PanelHooks, add_context_panel

# Traces upload to OpenAI by default, which needs an OpenAI key. We're on Gemini.
set_tracing_disabled(True)

# LiteLLM routes the call to Gemini. api_key is unused: Vertex AI uses your gcloud credentials.
MODEL = LitellmModel(model="vertex_ai/gemini-3.5-flash-lite", api_key="unused")
# A stalled model call would hang the page: give up after 90 s, and retry twice.
SETTINGS = ModelSettings(extra_args={"vertex_location": "global", "timeout": 90, "num_retries": 2})

DATA = Path(__file__).parent / "data"
MAX_ROWS = 100

# --- Tools: each analyst gets its own three, over its own database ---


def sql_tools(name: str) -> list:
    """read_mappings, get_enum_values, and run_sql for one database. build_data.py builds the files."""
    try:
        mappings = json.loads((DATA / f"{name}_mappings.json").read_text())
        # The security boundary is the connection, not the prompt: read-only, no file or network
        # access, and the agent can't SET its way out of either.
        db = duckdb.connect(
            str(DATA / f"{name}.duckdb"),
            read_only=True,
            config={"enable_external_access": False, "lock_configuration": True},
        )
    except (FileNotFoundError, duckdb.Error):
        raise SystemExit("No database found. Run `uv run build_data.py` first.")

    @function_tool
    def read_mappings() -> str:
        """Read your table's columns: name, type, a description, and whether it's an enum.

        Call this first. Call get_enum_values for an enum column's valid values.
        """
        return json.dumps([
            {"name": c["name"], "type": c["type"], "description": c["description"], "is_enum": "enum_values" in c}
            for c in mappings["columns"]
        ])

    @function_tool
    def get_enum_values(column: str) -> str:
        """Get the exact valid values of an enum column. Match them exactly: equality is case-sensitive.

        Args:
            column: The column name.
        """
        match = next((c for c in mappings["columns"] if c["name"] == column), None)
        if match is None or "enum_values" not in match:
            return json.dumps({"error": f"'{column}' is not an enum column. Call read_mappings for the columns."})
        return json.dumps({"column": column, "enum_values": match["enum_values"]}, default=str)

    @function_tool
    def run_sql(query: str) -> str:
        """Run a DuckDB SQL query against your table and return the results.

        Args:
            query: A DuckDB SQL query.
        """
        # The SDK runs tools in threads. Each call gets its own cursor: DuckDB connections aren't thread-safe.
        with db.cursor() as cursor:
            try:
                cursor.execute(query)
                rows = cursor.fetchmany(MAX_ROWS + 1)
            except duckdb.Error as e:
                # The model cannot see an exception. Return something it can reason about.
                return json.dumps({"error": str(e)})
            columns = [column[0] for column in cursor.description or []]
        return json.dumps({"columns": columns, "rows": rows[:MAX_ROWS], "truncated": len(rows) > MAX_ROWS}, default=str)

    return [read_mappings, get_enum_values, run_sql]


# --- The analysts: one dataset each, with that dataset's rules ---

requests_analyst = Agent(
    name="311 Analyst",
    handoff_description="NYC 311 service requests, 2020-2025: complaints, agencies, boroughs, ZIP codes.",
    instructions="""\
You answer questions about NYC 311 service requests from 2020 through 2025.
The data is in the `requests` table, one row per request.

- Call read_mappings first to see the columns.
- Before filtering on an enum column, call get_enum_values. Never guess values.
- Answer in plain English, and say what time period the answer covers.
- If a question isn't about 311 requests, hand off to the Data Desk. Don't answer it.""",
    model=MODEL,
    model_settings=SETTINGS,
    tools=sql_tools("311"),
)

survey_analyst = Agent(
    name="Subway Survey Analyst",
    handoff_description="The 2019 NYC subway rider survey: satisfaction, complaints, lines, riders.",
    instructions="""\
You answer questions about a 2019 survey of NYC subway riders.
The data is in the `survey` table, one row per response.

- Call read_mappings first to see the columns.
- Before filtering on an enum column, call get_enum_values. Never guess values.
- Missing values are NULL. Exclude them from filters, groups, and aggregates.
- top_three_complaints is a VARCHAR[] list. Unnest it with
  FROM survey, unnest(top_three_complaints) AS t(complaint).
- Answer in plain English.
- If a question isn't about the subway survey, hand off to the Data Desk. Don't answer it.""",
    model=MODEL,
    model_settings=SETTINGS,
    tools=sql_tools("survey"),
)

# --- The router and disambiguator: the Data Desk hands off clear questions, and sends vague ones back ---

desk = Agent(
    name="Data Desk",
    instructions="""\
You are the front desk of a data team. You don't query data yourself: you hand each question to the
analyst whose dataset can answer it.
- 311 Analyst: NYC 311 service requests, 2020-2025.
- Subway Survey Analyst: the 2019 NYC subway rider survey.

Hand off only a question that's clear enough to answer:
- It's about one dataset. "Complaints" could mean 311 complaints or riders' subway complaints.
- It says what to measure: a count, a share, a top value, a comparison.
- Its judgment words are pinned down: "bad", "worst", "a lot", and "recently" each need a measure.
A missing time period is fine: the analyst will cover the whole dataset.

If a question isn't clear, don't hand off. Ask one short question back, with two or three concrete
options the data can answer. Once the user answers, hand off. For example:
- "Is the subway bad?" -> "Bad how: overall satisfaction, delays, or a particular line?"
- "How many complaints were there?" -> "311 complaints from 2020-2025, or riders' complaints in the
  2019 subway survey?"
If neither dataset can answer, say which datasets the team has and what they cover.""",
    model=MODEL,
    model_settings=SETTINGS,
    handoffs=[requests_analyst, survey_analyst],
)

# Analysts hand back when a question belongs to the other dataset
requests_analyst.handoffs = [desk]
survey_analyst.handoffs = [desk]

# --- Session Store ---

# The router pattern's state lives outside the Runner. Runner.run starts with whatever agent you pass
# it, so to keep talking to the analyst who took over, the app remembers who finished the last turn.
# session_id -> {"history": the conversation so far, "agent": the agent in charge}
chats: dict[str, dict] = {}
# session_id -> every agent's context, in order, for the context panel
sessions: dict[str, AgentContexts] = {}

# --- FastAPI App ---

app = FastAPI()
add_context_panel(app, sessions)


@app.get("/")
def index():
    # no-cache: browsers otherwise keep serving an old page after a redeploy
    return FileResponse(Path(__file__).parent / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/chat")
async def chat(session_id: str, message: str, sticky: bool = True):
    """Run one turn and stream what happens as Server-Sent Events.

    sticky: start with the agent in charge (True), or back at the desk every message (False).
    """
    state = chats.setdefault(session_id, {"history": [], "agent": desk})
    contexts = sessions.setdefault(session_id, AgentContexts())
    start = state["agent"] if sticky else desk
    queue: asyncio.Queue = asyncio.Queue()
    hooks = PanelHooks(contexts, queue.put_nowait)  # puts each agent's context and steps on the queue

    async def work():
        try:
            history = state["history"] + [{"role": "user", "content": message}]
            result = await Runner.run(start, history, hooks=hooks, max_turns=20)
            # The two pieces of state the next turn needs: the conversation, and who's in charge
            state["history"] = result.to_input_list()
            state["agent"] = result.last_agent
            queue.put_nowait({"type": "answer", "agent": result.last_agent.name, "text": str(result.final_output)})
        except Exception as e:
            # Auth, quota, a model that won't stop: show it on the page, not as a dropped stream.
            queue.put_nowait({"type": "error", "message": f"{type(e).__name__}: {str(e)[:500]}"})

    task = asyncio.create_task(work())

    async def events():
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event, default=str)}\n\n"
                if event["type"] in ("answer", "error"):
                    break
        finally:
            task.cancel()  # the page closed the stream: stop spending tokens

    return StreamingResponse(events(), media_type="text/event-stream")


@app.post("/clear")
def clear(session_id: str):
    chats.pop(session_id, None)
    sessions.pop(session_id, None)
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
