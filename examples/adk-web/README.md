# adk-web

`agents-sdk-web`, rebuilt with Google ADK: plain functions replace `@function_tool`, ADK talks to Gemini natively instead of through LiteLLM, a `DatabaseSessionService` on a SQLite file holds the sessions, and `/chat` reads the tool calls out of the `Event`s the `Runner` yields. Run `gcloud auth application-default login`, then `uv run app.py`, and open http://localhost:8000.
