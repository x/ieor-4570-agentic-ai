"""The tools the harness can run, and the JSON that describes them to the model."""

import json
from pathlib import Path

import chromadb

# index_items.py builds this once, offline. The app only reads it.
CHROMA_PATH = Path(__file__).parent / "chroma_data"
TOP_K = 3

try:
    collection = chromadb.PersistentClient(path=str(CHROMA_PATH)).get_collection("magic_items")
except Exception:
    raise SystemExit("No index found. Run `uv run index_items.py` first.")


def search_magic_items(query: str) -> str:
    """Return the TOP_K items whose embeddings are closest to the query's embedding."""
    results = collection.query(query_texts=[query], n_results=TOP_K)
    documents, distances = results["documents"][0], results["distances"][0]
    return "\n---\n".join(
        f"[relevance: {1 - dist:.2f}]\n{doc}" for doc, dist in zip(documents, distances)
    )


# What the model sees: the "set notes" in the screenplay.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_magic_items",
            "description": (
                "Search the shop's inventory for magic items matching a description. "
                "Use this whenever a customer asks about items, their properties, or "
                "what you have available."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A natural-language description of the items to search for, "
                        "e.g. 'a sword that deals fire damage'",
                    },
                },
                "required": ["query"],
            },
        },
    },
]

# What the harness runs: tool name -> Python function.
TOOL_MAP = {"search_magic_items": search_magic_items}


def run_tool(name: str, args: dict) -> str:
    """Run one tool call. Models invent tool names and arguments; never let that crash the loop."""
    if name not in TOOL_MAP:
        return json.dumps({"error": f"Unknown tool '{name}'. Available: {list(TOOL_MAP)}"})
    try:
        return TOOL_MAP[name](**args)
    except TypeError as e:
        return json.dumps({"error": f"Bad arguments for {name}: {e}"})
