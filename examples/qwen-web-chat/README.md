# qwen-web-chat

A minimal web chatbot: a FastAPI server holding conversations in memory, a
static front-end, and `qwen2.5:1.5b` served locally by Ollama, called through
LiteLLM.

1. Install Ollama: https://ollama.com/download
2. Pull the model once: `ollama pull qwen2.5:1.5b`
3. `uv run app.py`, then open http://localhost:8000

- `index.html` is the complete front-end. Leave it alone.
- `app.py` is the server: session store, `/chat`, `/clear`, and the model call.

The session store is a dictionary from session ID to a list of
`{"role": ..., "content": ...}` messages. That list is sent as-is to the model
server on every turn.
