# agents-sdk-chat

`qwen-tool-calling`, rebuilt with the OpenAI Agents SDK on Gemini: `@function_tool` replaces the tool JSON, `Runner` replaces the inner loop, and a `SQLiteSession` holds the conversation. Run `gcloud auth application-default login`, then `uv run main.py`, and ask "Is it nice enough to go for a walk in New York?"
