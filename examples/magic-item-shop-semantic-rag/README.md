# magic-item-shop-semantic-rag

`agents-sdk-web` with `get_weather` swapped for `search_magic_items`, a semantic RAG tool over 1,029 D&D magic items. `index_items.py` embeds every item into ChromaDB once, offline, with ChromaDB's default local embedding model (`all-MiniLM-L6-v2`). At runtime the model decides when to search and writes its own query; the tool embeds that query and returns the 3 nearest items. Run `gcloud auth application-default login` and `uv run index_items.py` once, then `uv run app.py` and open http://localhost:8000. Try: "Do you have anything that sets a sword on fire?"
