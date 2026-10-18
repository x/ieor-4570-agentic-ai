import json

import requests
from agents import Agent, ModelSettings, Runner, RunHooks, SQLiteSession, function_tool, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel

# Traces upload to OpenAI by default, which needs an OpenAI key. We're on Gemini.
set_tracing_disabled(True)

# Open-Meteo is free and needs no API key.
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


# @function_tool builds the JSON schema from the signature and docstring:
# no TOOLS list, no TOOL_MAP, no run_tool.
@function_tool
def get_weather(location: str) -> str:
    """Get the current weather (temperature, humidity, wind) for a city.

    Args:
        location: City name, e.g. 'New York'.
    """
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


@function_tool
def lookup_contact(name: str) -> str:
    """Look up a contact's info by name.

    Args:
        name: The contact's first name, e.g. 'Alice'.
    """
    return json.dumps({"name": name, "email": f"{name.lower()}@example.com"})


class PrintToolCalls(RunHooks):
    """Watches the run and prints each tool call, like our print in qwen-tool-calling."""

    async def on_tool_end(self, context, agent, tool, result):
        # For a function tool, context is a ToolContext: it carries the call's arguments.
        print(f"TOOL: {tool.name}({json.loads(context.tool_arguments)}) -> {result}")


agent = Agent(
    name="Assistant",
    instructions=(
        "You are a helpful assistant. Be concise and friendly. When a question depends on "
        "the weather or outdoor conditions, call get_weather first, then answer in a sentence."
    ),
    # LiteLLM routes the call to Gemini. api_key is unused: Vertex AI uses your gcloud credentials.
    model=LitellmModel(model="vertex_ai/gemini-3.5-flash-lite", api_key="unused"),
    model_settings=ModelSettings(extra_args={"vertex_location": "global"}),
    tools=[get_weather, lookup_contact],
)

# The session replaces our messages list. One process, one conversation, so in memory is enough.
session = SQLiteSession("cli")

while True:
    user_msg = input("USER: ")

    # The Runner is our inner tool loop. It stops after max_turns (default 10),
    # the way our MAX_TOOL_ROUNDS did.
    result = Runner.run_sync(agent, user_msg, session=session, hooks=PrintToolCalls())

    print(f"ASSISTANT: {result.final_output}\n")
