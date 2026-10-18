# qwen-tool-calling

`qwen-chat`, upgraded to fetch the weather. The loop is the same; two things changed:

- `tools=TOOLS` is passed to the model, so it knows `get_weather` exists.
- An inner loop: if the reply contains `tool_calls`, the harness runs them, appends
  each result as a `"tool"` message, and completes again.

1. Install Ollama: https://ollama.com/download
2. Pull the model once: `ollama pull qwen2.5:7b`
3. `uv run main.py`

Try: "Is it nice enough to go for a walk in New York?"

`main.py` holds the tool's Python function and the JSON description the model sees.
The weather comes from Open-Meteo, which needs no API key.
