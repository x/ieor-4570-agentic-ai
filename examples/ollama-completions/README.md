# ollama-completions

The `tiny-llama-completions` exercise, with the model behind a local server.

1. Install Ollama: https://ollama.com/download
2. Pull the model once: `ollama pull qwen2.5:1.5b`
3. `uv run main.py`

Ollama loads the weights and serves them on `http://localhost:11434`.
LiteLLM calls that server with the same `completion()` function it uses for
OpenAI, Anthropic, or Google. Change `MODEL` to `gpt-4o-mini` and set an API
key, and nothing else changes.
