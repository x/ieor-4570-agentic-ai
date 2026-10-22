# nyc-311-agent-langfuse

`nyc-311-agent-improved`, traced and evaluated with [Langfuse](https://langfuse.com), and served as a chat like `agents-sdk-web`. Each question becomes one trace, each chat a Langfuse session, and `evals.py` replaces the Inspect task with a Langfuse experiment that has the same rubric, golden-reference, and deterministic scores. Copy `.env.example` to `.env` with the keys from a free [Langfuse Cloud](https://cloud.langfuse.com) project (Settings > API Keys), run `gcloud auth application-default login` and `uv run build_mappings.py` once, then `uv run --env-file .env app.py` and open http://localhost:8000. Each answer links to its trace in Langfuse.

## Tracing

The Agents SDK traces every run on its own. `OpenAIAgentsInstrumentor().instrument()` (OpenInference) turns those traces into OpenTelemetry spans, replacing the SDK's default exporter, which uploads to OpenAI. `get_client()` starts the Langfuse client, which exports the spans to Langfuse's OpenTelemetry endpoint. Without the three `LANGFUSE_` variables, the client warns and exports nothing, and the agent still runs.

A trace looks like this:

```
answer-question                    span        the question in, the answer out
├── expand-entities                retriever   the question before and after the entity notes
└── Agent workflow                 agent       two empty wrappers OpenInference adds
    └── Agent workflow             chain       for the SDK's trace and run
        └── NYC 311 Analyst        agent
            ├── turn               chain
            │   ├── generation     generation  one model call: the messages sent, tokens, cost
            │   └── read_mappings  tool        the call the model asked for, and its result
            └── turn ...
```

- `answer()` in `app.py` opens the root span itself, so the trace's input and output are the question and the answer.
- Every generation's input is the whole conversation so far: the model API is stateless, so the SDK resends the history on every call, and the input tokens grow each turn.
- In the chat, `propagate_attributes(session_id=...)` starts before the root span, so every span in the trace, the root included, carries the chat's session. Langfuse's Sessions view groups a chat's traces, one per question.
- FastAPI traces every request with OpenTelemetry as soon as a tracer exists, which the Langfuse client provides. Langfuse doesn't export those HTTP spans, so `app.py` turns them off (`FastAPI(telemetry={"tracing": False})`); otherwise each trace's root span would point at a parent Langfuse never receives.
- LiteLLM gets the provider as `custom_llm_provider="vertex_ai"` instead of a `vertex_ai/` prefix on the model name. Langfuse prices a generation by matching its model name, and it has prices for `gemini-3.5-flash-lite`, not `vertex_ai/gemini-3.5-flash-lite`.

## The prompt

The agent's instructions are the `nyc-311-analyst` prompt in Langfuse Prompt Management. For every question, `answer()` fetches the prompt's `production` version and passes it to `propagate_attributes(prompt=...)`, which links each generation in the trace to the prompt version that produced it. The SDK caches the prompt for 60 seconds and refreshes it in the background, so promoting a new version to `production` in the Langfuse UI changes the running agent within a minute, with no redeploy. Each eval run's description names the prompt version, so experiments compare by prompt.

`INSTRUCTIONS` in `app.py` is the fallback, for when Langfuse can't serve the prompt; fallback runs aren't linked to any version. It's also the prompt's first version, created once with:

```
uv run --env-file .env python -c "from app import PROMPT, INSTRUCTIONS, langfuse; langfuse.create_prompt(name=PROMPT, prompt=INSTRUCTIONS, labels=['production'])"
```

Langfuse's OpenAI Agents page links prompts with a custom span processor. The SDK's `propagate_attributes(prompt=...)` does the same with one argument, and only links generations.

## Environments and releases

Langfuse filters every view by environment:

| Environment | Traces from |
|-|-|
| `default` | local runs of `app.py` |
| `production` | Cloud Run, which sets `LANGFUSE_TRACING_ENVIRONMENT=production` |
| `sdk-experiment` | `evals.py` |

The Langfuse SDK puts every experiment span in `sdk-experiment`, but gives the experiment's scores the client's environment. `evals.py` sets `LANGFUSE_TRACING_ENVIRONMENT=sdk-experiment` before the client starts, so the scores land next to their traces.

On Cloud Run, `app.py` copies the revision name (`K_REVISION`, e.g. `nyc-311-agent-langfuse-00005-sv8`) into `LANGFUSE_RELEASE`, which tags every span with the deploy that served it.

## Evals

```
uv run --env-file .env evals.py
uv run --env-file .env evals.py evals/neighborhoods.jsonl --no-expand
```

`evals.py` uploads the JSONL file as a Langfuse dataset (`nyc-311-dataset` or `nyc-311-neighborhoods`). Each sample's `id` makes the upload an upsert, so rerunning updates the items instead of duplicating them. It then runs the agent on every item as an experiment, one question per run with no session, and scores each answer:

- `deterministic_checks`: `called_run_sql`, `sql_parsed`, `one_query`, and `query_count`, from the agent's tool calls.
- `model_graded_reference`: whether the agent's SQL computes the same answer as the gold SQL.
- `model_graded_rubric`: `correct_answer`, `time_window`, and `leads_with_answer`, each with the judge's reason as the score's comment.

The gold SQL never uploads. Langfuse Cloud's firewall rejects some of it as SQL injection (`HAVING count(*) >= 100` returns a 403), so `evals.py` keeps it in a dictionary keyed by question. Each run prints its averages and a link to compare it with earlier runs in Langfuse.

## Online evals

`evals.py` scores the agent offline, against a fixed dataset. Langfuse also scores live traffic: an evaluation rule ("nyc-311 production answers") matches every root `answer-question` observation in `production` and runs three LLM-as-a-judge evaluators on its input and output, the question and the answer. Each writes a true/false score with the judge's reason to the observation, usually within half a minute:

- `answers_question`: gives the specific result the question asks for. A refusal, an error, or a description of the data fails.
- `time_window`: states the time period the answer covers.
- `leads_with_answer`: gives its result in the first sentence.

`time_window` and `leads_with_answer` match the offline rubric, so the same criteria show up for both. Live traffic has no expected answer, so `correct_answer` and `matches_reference` stay offline.

The evaluators and the rule are Langfuse settings. Create them under Evaluators, or with the `evaluators` and `evaluation-rules` endpoints of `npx langfuse-cli api`. The judge calls Gemini through a Langfuse LLM connection (Project Settings > LLM Connections) named `vertex-judge`: the Google Vertex AI adapter, location `global`, the custom model `gemini-3.5-flash-lite`, and the JSON key of a service account with only the Vertex AI User role. An evaluator created before its connection exists is paused (`LLM_CONNECTION_MISSING`); saving its definition again reactivates it.

## Cloud Run

Deploying needs `data/311.duckdb` and `data/311_mappings.json`, so run `uv run build_mappings.py` first. `.gitignore` leaves both out, but `.gcloudignore` uploads them. The Langfuse keys go in Secret Manager instead of the deploy command, so they never show up in your shell history or the service's settings.

1. Turn on the APIs (once per project):

   ```
   gcloud services enable run.googleapis.com secretmanager.googleapis.com aiplatform.googleapis.com
   ```

2. Store the two keys from your Langfuse project's Settings > API Keys. Each command waits for you to paste a key, without echoing it:

   ```
   read -rs K && printf %s "$K" | gcloud secrets create langfuse-public-key --data-file=-
   read -rs K && printf %s "$K" | gcloud secrets create langfuse-secret-key --data-file=-
   ```

3. Let Cloud Run's service account (the Compute Engine default, unless you picked another) read the secrets and call Gemini:

   ```
   PROJECT=$(gcloud config get-value project)
   SA=$(gcloud projects describe $PROJECT --format='value(projectNumber)')-compute@developer.gserviceaccount.com
   for s in langfuse-public-key langfuse-secret-key; do
     gcloud secrets add-iam-policy-binding $s --member=serviceAccount:$SA --role=roles/secretmanager.secretAccessor
   done
   gcloud projects add-iam-policy-binding $PROJECT --member=serviceAccount:$SA --role=roles/aiplatform.user
   ```

4. Deploy:

   ```
   gcloud run deploy nyc-311-agent-langfuse --source . --region us-east1 \
     --set-build-env-vars "GOOGLE_ENTRYPOINT=uvicorn app:app --host 0.0.0.0 --port \$PORT" \
     --set-secrets LANGFUSE_PUBLIC_KEY=langfuse-public-key:latest,LANGFUSE_SECRET_KEY=langfuse-secret-key:latest \
     --set-env-vars LANGFUSE_BASE_URL=https://us.cloud.langfuse.com,LANGFUSE_TRACING_ENVIRONMENT=production \
     --allow-unauthenticated --max-instances 1
   ```

Use `LANGFUSE_BASE_URL=https://cloud.langfuse.com` for a project in Langfuse's EU region. Redeploys keep the secrets and variables, so later deploys only need `gcloud run deploy nyc-311-agent-langfuse --source . --region us-east1`. To change a key, add a new version with `read -rs K && printf %s "$K" | gcloud secrets versions add langfuse-secret-key --data-file=-` and redeploy.
