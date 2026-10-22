"""Evaluate the agent as a Langfuse experiment: upload the dataset, run the agent on every item, score each answer.

    uv run --env-file .env evals.py
    uv run --env-file .env evals.py evals/neighborhoods.jsonl --no-expand
"""
import argparse
import json
import os
from pathlib import Path

# Experiment traces always land in the sdk-experiment environment, but their scores take the client's
# environment. Set it before app.py creates the client, so the scores land next to their traces.
os.environ["LANGFUSE_TRACING_ENVIRONMENT"] = "sdk-experiment"

import duckdb
import litellm
from agents import MaxTurnsExceeded
from langfuse import Evaluation
from pydantic import BaseModel, Field, ValidationError

from app import INSTRUCTIONS, MODEL, PROMPT, VERTEX, answer, langfuse

parser = argparse.ArgumentParser()
parser.add_argument("dataset", nargs="?", default="evals/dataset.jsonl")
parser.add_argument("--no-expand", dest="expand", action="store_false", help="turn the entity expansion off")
args = parser.parse_args()


# ---------- The dataset ----------

# Each sample becomes a dataset item. Its id makes the upload an upsert: rerunning updates, never duplicates.
DATASET = f"nyc-311-{Path(args.dataset).stem}"
SAMPLES = [json.loads(line) for line in Path(args.dataset).read_text().splitlines()]
# Langfuse Cloud's firewall rejects some gold SQL as SQL injection (`HAVING count(*) >= 100`), so the
# gold SQL stays here, looked up by question, and never uploads.
GOLD_SQL = {sample["input"]: sample["metadata"].pop("gold_sql") for sample in SAMPLES}
langfuse.create_dataset(name=DATASET)
for sample in SAMPLES:
    langfuse.create_dataset_item(
        dataset_name=DATASET,
        id=sample["id"],
        input=sample["input"],
        expected_output=sample["target"],
        metadata=sample["metadata"],
    )


async def task(*, item, **kwargs):
    try:
        result = await answer(item.input, expand_entities=args.expand)
    except MaxTurnsExceeded:
        return {"answer": "", "queries": []}  # out of turns with no final answer: score it, don't crash
    queries = [call["args"].get("query", "") for call in result["tool_calls"] if call["name"] == "run_sql"]
    return {"answer": result["response"], "queries": queries}


async def judge(prompt: str, schema: type[BaseModel]) -> BaseModel | None:
    """Ask the judge model for JSON matching schema. None if it doesn't parse."""
    response = await litellm.acompletion(
        model=MODEL,
        **VERTEX,
        messages=[{"role": "user", "content": prompt}],
        response_format=schema,
    )
    try:
        return schema.model_validate_json(response.choices[0].message.content)
    except ValidationError:
        return None


# ---------- Deterministic checks ----------


def parses(query: str) -> bool:
    try:
        duckdb.extract_statements(query)
        return True
    except duckdb.Error:
        return False


def deterministic_checks(*, output, **kwargs):
    queries = output["queries"]
    return [
        Evaluation(name="called_run_sql", value=float(len(queries) > 0)),
        Evaluation(name="sql_parsed", value=float(len(queries) > 0 and all(parses(q) for q in queries))),
        Evaluation(name="one_query", value=float(len(queries) == 1)),
        Evaluation(name="query_count", value=len(queries)),
    ]


# ---------- Model-graded: golden reference ----------

REFERENCE_PROMPT = """You are comparing the SQL an agent ran to a reference query, both against the same DuckDB table of NYC 311 service requests.
The table only holds requests from 2020 through 2025, so a filter to that date range changes nothing.

Question: {question}

Agent's SQL, in the order it ran:
{queries}

Reference SQL: {gold_sql}

Final answer: {answer}

Does the SQL the final answer was based on compute the same answer as the reference SQL? Ignore formatting, aliases, column order, and extra columns. If the agent never ran SQL, it does not."""


class ReferenceGrade(BaseModel):
    reason: str
    same_answer: bool


async def model_graded_reference(*, input, output, **kwargs):
    prompt = REFERENCE_PROMPT.format(
        question=input,
        queries="\n\n".join(output["queries"]) or "(none)",
        gold_sql=GOLD_SQL[input],
        answer=output["answer"],
    )
    grade = await judge(prompt, ReferenceGrade)
    if grade is None:
        return []  # the judge's JSON didn't parse: leave the item unscored rather than failed
    return Evaluation(name="matches_reference", value=float(grade.same_answer), comment=grade.reason)


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


async def model_graded_rubric(*, input, output, expected_output, **kwargs):
    grades = await judge(RUBRIC_PROMPT.format(question=input, answer=output["answer"], target=expected_output), RubricGrades)
    if grades is None:
        return []
    return [
        Evaluation(name=name, value=float(criterion.passed), comment=criterion.reason)
        for name, criterion in grades
    ]


# The production prompt version the agent will run with (0 is the fallback), so runs compare by prompt.
PROMPT_VERSION = langfuse.get_prompt(PROMPT, fallback=INSTRUCTIONS).version
result = langfuse.get_dataset(DATASET).run_experiment(
    name="nyc-311-agent",
    description=f"{MODEL}, prompt v{PROMPT_VERSION}, entity expansion {'on' if args.expand else 'off'}",
    task=task,
    evaluators=[model_graded_rubric, model_graded_reference, deterministic_checks],
    max_concurrency=10,
    metadata={"model": MODEL, "prompt_version": str(PROMPT_VERSION), "expand": str(args.expand)},
)
print(result.format())
langfuse.flush()
