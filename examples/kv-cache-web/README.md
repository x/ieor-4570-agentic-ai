# kv-cache-web

Builds on `agents-sdk-web`: two agents read *The Hound of the Baskervilles* one chapter at a time and name their prime suspect after each. Their prompts differ in one line: one starts with the current time, which changes every request, and the other with today's date. The page graphs each side's time to first token and Gemini's `cached_tokens`, and shows which part of each context matched the last request. Run `gcloud auth application-default login`, then `uv run app.py`, and open http://localhost:8000.
