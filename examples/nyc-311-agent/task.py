"""Inspect task for the NYC 311 agent.

    uv run inspect eval task.py
"""
import os

import duckdb
import google.auth
from openai import AsyncOpenAI
from agents import MaxTurnsExceeded, ModelSettings, OpenAIResponsesModel, RunConfig, Runner
from inspect_ai import Task, task
from inspect_ai.agent import Agent, AgentState, agent, agent_bridge
from inspect_ai.dataset import json_dataset
from inspect_ai.model import ChatMessageAssistant, GenerateConfig, ResponseSchema, get_model, messages_to_openai_responses
from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, mean, model_graded_qa, scorer, stderr
from inspect_ai.solver import TaskState
from inspect_ai.util import json_schema
from pydantic import BaseModel, Field, ValidationError

import main

# Inspect's Vertex provider reads the project from the environment. Default it to the
# project `gcloud init` configured, the same one LiteLLM finds for main.py.
if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
    os.environ["GOOGLE_CLOUD_PROJECT"] = google.auth.default()[1] or ""
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")


@agent
def nyc_311_agent() -> Agent:
    """The agent from main.py, with its model calls routed to the model Inspect is evaluating."""

    async def execute(state: AgentState) -> AgentState:
        async with agent_bridge(state) as bridge:
            try:
                await Runner.run(
                    # Drop main.py's Vertex-only settings: Inspect configures the model now.
                    starting_agent=main.agent.clone(model_settings=ModelSettings()),
                    input=await messages_to_openai_responses(state.messages),
                    # Overrides the agent's own Gemini model: "inspect" is whatever --model says.
                    # The bridge intercepts the call, so the OpenAI key is never used, just required.
                    run_config=RunConfig(
                        model=OpenAIResponsesModel("inspect", AsyncOpenAI(api_key="unused"))
                    ),
                )
            except MaxTurnsExceeded:
                pass  # Out of turns with no final answer. Score that as a failure, not a crash.
            return bridge.state

    return execute


def sql_queries(state: TaskState) -> list[str]:
    """Every query the agent passed to run_sql, in order."""
    return [
        call.arguments.get("query", "")
        for message in state.messages
        if isinstance(message, ChatMessageAssistant)
        for call in message.tool_calls or []
        if call.function == "run_sql"
    ]


def parses(query: str) -> bool:
    try:
        duckdb.extract_statements(query)
        return True
    except duckdb.Error:
        return False


async def judge(prompt: str, schema: type[BaseModel]) -> BaseModel | None:
    """Ask the grader model for JSON matching schema. None if it doesn't parse."""
    # The "grader" model role (--model-role grader=...), or the model being evaluated if unset.
    result = await get_model(role="grader").generate(
        prompt,
        config=GenerateConfig(response_schema=ResponseSchema(name=schema.__name__, json_schema=json_schema(schema))),
    )
    try:
        return schema.model_validate_json(result.completion)
    except ValidationError:
        return None


# ---------- Deterministic checks ----------


@scorer(metrics={"called_run_sql": [accuracy()], "sql_parsed": [accuracy()], "one_query": [accuracy()], "query_count": [mean()]})
def deterministic_checks():
    async def score(state: TaskState, target: Target) -> Score:
        queries = sql_queries(state)
        check = lambda passed: CORRECT if passed else INCORRECT
        return Score(
            value={
                "called_run_sql": check(len(queries) > 0),
                "sql_parsed": check(len(queries) > 0 and all(parses(q) for q in queries)),
                "one_query": check(len(queries) == 1),
                "query_count": len(queries),
            },
            answer="\n\n".join(queries),
        )

    return score


# ---------- Model-graded: golden reference ----------

# Inspect fills in {question} (the agent's transcript, including its run_sql calls), {answer},
# {instructions}, and any sample metadata, like {gold_sql}.
REFERENCE_TEMPLATE = """You are comparing the SQL an agent ran to a reference query, both against the same DuckDB table of NYC 311 service requests.

[BEGIN DATA]
***
[Transcript]: {question}
***
[Reference SQL]: {gold_sql}
***
[Final answer]: {answer}
***
[END DATA]

Does the SQL the final answer was based on compute the same answer as the reference SQL? Ignore formatting, aliases, column order, and extra columns. If the agent never ran SQL, it does not.

{instructions}"""

model_graded_reference = model_graded_qa(template=REFERENCE_TEMPLATE, include_history=True)


# ---------- Model-graded: rubric ----------

RUBRIC_PROMPT = """You are grading an answer to a question about NYC 311 service requests against a rubric. Judge each criterion on its own.

Question: {question}

Answer: {answer}

Rubric:
- correct_answer: States that the answer is {target}. Other formatting of the same value counts (e.g. 12,345 for 12345, May 2023 for 2023-05, Bronx for BRONX).
- time_window: States the time period the answer covers.
- leads_with_answer: Gives the answer in its first sentence."""


class Criterion(BaseModel):
    reason: str
    passed: bool = Field(alias="pass")


class RubricGrades(BaseModel):
    correct_answer: Criterion
    time_window: Criterion
    leads_with_answer: Criterion


@scorer(metrics={"*": [accuracy(), stderr()]})
def model_graded_rubric():
    async def score(state: TaskState, target: Target) -> Score:
        prompt = RUBRIC_PROMPT.format(question=state.input_text, answer=state.output.completion, target=target.text)
        grades = await judge(prompt, RubricGrades)
        if grades is None:
            return Score.unscored(reason="grader_failed")
        return Score(
            value={name: CORRECT if criterion.passed else INCORRECT for name, criterion in grades},
            answer=state.output.completion,
            explanation=grades.model_dump_json(by_alias=True, indent=2),
        )

    return score


@task
def nyc_311() -> Task:
    return Task(
        dataset=json_dataset("evals/dataset.jsonl"),
        solver=nyc_311_agent(),
        # The first score of the first scorer (correct_answer) is the headline number.
        scorer=[model_graded_rubric(), model_graded_reference, deterministic_checks()],
        # The same Gemini model main.py uses. --model overrides it.
        model="google/vertex/gemini-3.5-flash-lite",
    )
