# qwen-chat

The simplest chatbot: a system prompt, a `messages` list, and a loop.

1. Install Ollama: https://ollama.com/download
2. Pull the model once: `ollama pull qwen2.5:1.5b`
3. `uv run main.py`

Every turn appends to `messages` and sends the whole list back to the model.
Ctrl-C to quit.
