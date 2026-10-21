import json
import sys
from pathlib import Path

import duckdb
from agents import Agent, ModelSettings, Runner, RunHooks, function_tool, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel

from entities import expand

# Traces upload to OpenAI by default, which needs an OpenAI key. We're on Gemini.
set_tracing_disabled(True)

# build_mappings.py builds both files once, offline. The agent only reads them.
DATA = Path(__file__).parent / "data"
MAX_ROWS = 100

try:
    MAPPINGS = json.loads((DATA / "311_mappings.json").read_text())
    # The security boundary is the connection, not the prompt: read-only, no file or network
    # access, and the agent can't SET its way out of either.
    db = duckdb.connect(
        str(DATA / "311.duckdb"),
        read_only=True,
        config={"enable_external_access": False, "lock_configuration": True},
    )
except (FileNotFoundError, duckdb.Error):
    raise SystemExit("No database found. Run `uv run build_mappings.py` first.")


@function_tool
def read_mappings() -> str:
    """Read the requests table's columns: name, type, a description, and whether it's an enum.

    Call this first. Call get_enum_values for an enum column's valid values.
    """
    return json.dumps([
        {"name": c["name"], "type": c["type"], "description": c["description"], "is_enum": "enum_values" in c}
        for c in MAPPINGS["columns"]
    ])


@function_tool
def get_enum_values(column: str) -> str:
    """Get the exact valid values of an enum column. Match them exactly: equality is case-sensitive.

    Args:
        column: The column name, e.g. 'complaint_type'.
    """
    match = next((c for c in MAPPINGS["columns"] if c["name"] == column), None)
    if match is None:
        return json.dumps({"error": f"No column '{column}'. Call read_mappings for the columns."})
    if "enum_values" not in match:
        return json.dumps({"error": f"'{column}' is not an enum column. Query its distinct values with run_sql."})
    return json.dumps({"column": column, "enum_values": match["enum_values"]})


@function_tool
def run_sql(query: str) -> str:
    """Run a SQL query against the database and return the results.

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

    return json.dumps(
        {
            "columns": columns,
            "rows": rows[:MAX_ROWS],
            "truncated": len(rows) > MAX_ROWS,
        },
        default=str,
    )


class PrintToolCalls(RunHooks):
    """Prints each tool call and the start of its result."""

    async def on_tool_end(self, context, agent, tool, result):
        print(f"TOOL: {tool.name}({json.loads(context.tool_arguments)}) -> {result[:300]}\n")


agent = Agent(
    name="NYC 311 Analyst",
    instructions="""\
You answer questions about NYC 311 service requests from 2020 through 2025.
The data is in the `requests` table, one row per request.

- Call read_mappings first to see the columns.
- Before filtering on an enum column, call get_enum_values. Never guess values.
- A question may end with notes, like "Park Slope is incident_zip 11215, 11217."
  Use them: they say what a term means in the database.""",
    # LiteLLM routes the call to Gemini. api_key is unused: Vertex AI uses your gcloud credentials.
    model=LitellmModel(model="vertex_ai/gemini-3.5-flash-lite", api_key="unused"),
    model_settings=ModelSettings(extra_args={"vertex_location": "global"}),
    tools=[read_mappings, get_enum_values, run_sql],
)

if __name__ == "__main__":
    # One task in, one answer out. No chat loop.
    task = " ".join(sys.argv[1:]) or input("TASK: ")
    task = expand(task)  # before the agent runs, like classic RAG
    result = Runner.run_sync(agent, task, hooks=PrintToolCalls())
    print(f"ANSWER: {result.final_output}")
