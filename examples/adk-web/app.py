import json
import os
import uuid
from pathlib import Path

import requests
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types
from pydantic import BaseModel

# ADK talks to Gemini natively, no LiteLLM. These point it at Vertex AI (Agent Platform):
# your gcloud credentials and default project, in the `global` location Gemini 3 needs.
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")

# --- Tools ---

# ADK wraps a plain function as a tool: the name, docstring, and type hints become its JSON.
# Open-Meteo is free and needs no API key.
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather(location: str) -> dict:
    """Get the current weather (temperature, humidity, wind) for a city.

    Args:
        location: City name, e.g. 'New York'.
    """
    try:
        places = requests.get(GEOCODE_URL, params={"name": location, "count": 1}, timeout=10).json()
        if not places.get("results"):
            return {"error": f"City '{location}' was not found."}
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
        return {"error": f"Weather service failed: {e}"}

    return {
        "location": place["name"],
        "temp_f": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "wind_mph": current["wind_speed_10m"],
    }


def lookup_contact(name: str) -> dict:
    """Look up a contact's info by name.

    Args:
        name: The contact's first name, e.g. 'Alice'.
    """
    return {"name": name, "email": f"{name.lower()}@example.com"}


# --- The Agent ---

root_agent = Agent(
    name="assistant",
    model="gemini-3.5-flash-lite",
    instruction=(
        "You are a helpful assistant. Be concise and friendly. When a question depends on "
        "the weather or outdoor conditions, call get_weather first, then answer in a sentence."
    ),
    tools=[get_weather, lookup_contact],
)

# --- Session Store ---

# Every session lives in one SQLite file. On Cloud Run the filesystem is in memory, so this
# lasts as long as the instance. Each instance has its own copy.
session_service = DatabaseSessionService(db_url="sqlite+aiosqlite:///./conversations.db")

# The Runner is our run_agent() loop. It creates a session the first time it sees an id.
runner = Runner(
    app=App(name="adk_web", root_agent=root_agent),
    session_service=session_service,
    auto_create_session=True,
)

# --- FastAPI App ---

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: list[dict]


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    message = types.Content(role="user", parts=[types.Part(text=request.message)])

    response, tool_calls, tool_args = "", [], {}
    try:
        # Every model reply, tool call, and tool result arrives as an Event
        async for event in runner.run_async(user_id=session_id, session_id=session_id, new_message=message):
            for call in event.get_function_calls():
                tool_args[call.id] = call.args
            for result in event.get_function_responses():
                tool_calls += [{"name": result.name, "args": tool_args[result.id], "result": json.dumps(result.response)}]
            if event.is_final_response() and event.content and event.content.parts:
                response = "".join(part.text or "" for part in event.content.parts)
    except Exception as e:
        # Auth, billing, a model that is not running: show it in the chat, not as a 500.
        response = f"Model call failed: {type(e).__name__}: {str(e)[:300]}"

    return ChatResponse(response=response, session_id=session_id, tool_calls=tool_calls)


@app.post("/clear")
async def clear(session_id: str | None = None):
    if session_id:
        await session_service.delete_session(app_name="adk_web", user_id=session_id, session_id=session_id)
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
