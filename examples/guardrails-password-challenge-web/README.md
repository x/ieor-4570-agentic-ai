# guardrails-password-challenge-web

`guardrails-password-challenge`, as a web app on the **OpenAI Agents SDK**. Same seven levels,
same passwords, same model. Each level is its own `Agent`, with its own page handler and chat handler right below it.
The page handler renders `index.html` as a template at `/level/1` to `/level/7`.

| `guardrails-password-challenge` | `guardrails-password-challenge-web` |
|---|---|
| One `while` loop per level | One `Agent` and one `/level/N/chat` handler per level, run with `Runner.run()` |
| `if mentions_password(user_msg): ...` | `@input_guardrail` on `Agent(input_guardrails=[...])` |
| `if contains_password(password, reply): ...` | `@output_guardrail` on `Agent(output_guardrails=[...])` |
| A `litellm.completion()` call that answers YES or NO | A checker `Agent` with `output_type=Verdict` |
| `getattr(message, "reasoning_content", None)` | `RecordReasoning`, an `AgentHooks` that copies it into the context |

- `app.py` has everything: the guardrails, the seven level `Agent`s, and the web server.
- Every guardrail returns a `GuardrailFunctionOutput`. A trip halts the run and raises
  `InputGuardrailTripwireTriggered` or `OutputGuardrailTripwireTriggered`. Each chat handler reads every
  guardrail's result from `result.input_guardrail_results` and `result.output_guardrail_results`,
  or from the exception's `run_data` when one trips, and the page shows each one above the reply.
- The password and the keeper's reasoning travel in the run context, a `Game`, at `ctx.context`.
- An output guardrail only sees the final reply. For level 7, the `RecordReasoning` hook copies
  the keeper's reasoning into the context in `on_llm_end`, and the `plans_to_reveal` guardrail
  reads it there. Hooks watch; guardrails decide.
- There's no session: every message is a fresh one-shot run. Type the password in the chat to
  move on. Plain code checks it, no model.
- Tracing is off. By default the SDK uploads traces to OpenAI, which needs an OpenAI key.

## Setup

1. A GCP project with billing and the Agent Platform API enabled
   (older docs and the endpoint itself still call it Vertex AI)
2. `gcloud auth application-default login`. The app uses your gcloud default
   project, so run `gemini-hello-world` first to check it.
3. `uv run app.py`, then open http://localhost:8000
