import json
import sys
from pathlib import Path

import duckdb
from agents import Agent, ModelSettings, Runner, RunHooks, function_tool, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel

# Traces upload to OpenAI by default, which needs an OpenAI key. We're on Gemini.
set_tracing_disabled(True)

# Use the full data if download-full.sh has been run, otherwise the committed 5% sample.
DATA = "data/311-full.parquet" if Path("data/311-full.parquet").exists() else "data/311-sample.parquet"
MAX_ROWS = 100

db = duckdb.connect()
db.sql(f"CREATE VIEW requests AS SELECT * FROM '{DATA}'")


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
    instructions="You answer questions about NYC 311 data. The data is in the `requests` table.",
    # LiteLLM routes the call to Gemini. api_key is unused: Vertex AI uses your gcloud credentials.
    model=LitellmModel(model="vertex_ai/gemini-3.5-flash-lite", api_key="unused"),
    model_settings=ModelSettings(extra_args={"vertex_location": "global"}),
    tools=[run_sql],
)

if __name__ == "__main__":
    # One task in, one answer out. No chat loop.
    task = " ".join(sys.argv[1:]) or input("TASK: ")
    result = Runner.run_sync(agent, task, hooks=PrintToolCalls())
    print(f"ANSWER: {result.final_output}")
