import json

import litellm
import requests

# Open-Meteo is free and needs no API key.
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    # Models ignore the schema sometimes, e.g. {"city": "London", "country": "UK"}.
    if not isinstance(location, str):
        return json.dumps({"error": "location must be a city name string, e.g. 'London'."})
    try:
        places = requests.get(GEOCODE_URL, params={"name": location, "count": 1}, timeout=10).json()
        if not places.get("results"):
            return json.dumps({"error": f"City '{location}' was not found."})
        place = places["results"][0]

        current = requests.get(
            FORECAST_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
            },
            timeout=10,
        ).json()["current"]
    except requests.RequestException as e:
        # The model cannot see an exception. Return something it can reason about.
        return json.dumps({"error": f"Weather service failed: {e}"})

    return json.dumps({
        "location": place["name"],
        "temp_f": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "wind_mph": current["wind_speed_10m"],
    })


# What the model sees: the "set notes" in the screenplay.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather (temperature, humidity, wind) for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name, e.g. 'New York'"},
                },
                "required": ["location"],
            },
        },
    },
]

# What the harness runs: tool name -> Python function.
TOOL_MAP = {"get_weather": get_weather}


def run_tool(name: str, args: dict) -> str:
    """Run one tool call. Models invent tool names and arguments; never let that crash the loop."""
    if name not in TOOL_MAP:
        return json.dumps({"error": f"Unknown tool '{name}'. Available: {list(TOOL_MAP)}"})
    try:
        return TOOL_MAP[name](**args)
    except TypeError as e:
        return json.dumps({"error": f"Bad arguments for {name}: {e}"})


MODEL = "ollama_chat/qwen2.5:7b"
SYSTEM_PROMPT = (
    "You are a helpful assistant. When a question depends on "
    "the weather or outdoor conditions, call get_weather "
    "first, then answer in a sentence."
)
MAX_TOOL_ROUNDS = 5

# Initialize context with the system prompt
messages = [{"role": "system", "content": SYSTEM_PROMPT}]

while True:
    user_msg = input("USER: ")

    # Append user's message to the context
    messages += [{"role": "user", "content": user_msg}]

    # Keep completing until the model stops asking for tools, or we hit the limit.
    # A small model will happily call tools forever; the harness sets the bound.
    for _ in range(MAX_TOOL_ROUNDS):
        reply = litellm.completion(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        ).choices[0].message

        # Append assistant's reply: text, tool calls, or both.
        # model_dump() keeps it a plain dict: the raw object carries provider-specific
        # fields that trip Pydantic when LiteLLM re-serializes it next round.
        messages += [reply.model_dump()]

        if not reply.tool_calls:
            break

        # The harness, not the model, runs each tool
        for call in reply.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments)
            result = run_tool(name, args)
            print(f"TOOL: {name}({args}) -> {result}")

            # Append the tool's result to the context
            messages += [{
                "role": "tool",
                "tool_call_id": call.id,
                "content": result,
            }]

    else:
        print("ASSISTANT: Sorry, I hit my tool-call limit before finishing.\n")
        continue

    print(f"ASSISTANT: {reply.content}\n")
