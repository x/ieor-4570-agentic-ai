"""Index the magic item markdown files into ChromaDB. Run once, offline, before app.py."""

import re
from pathlib import Path

import chromadb

HERE = Path(__file__).parent
ITEMS_DIR = HERE / "magic_items"
CHROMA_PATH = HERE / "chroma_data"

H1_PATTERN = re.compile(r"^#\s+\[?([^\]\n]+)\]?")
TAG_PATTERN = re.compile(r"#(\w+)")
ITEM_TYPES = {"weapon", "armor", "wondrous", "potion", "ring", "rod", "scroll", "staff", "wand"}
RARITIES = {"common", "uncommon", "rare", "veryrare", "legendary", "artifact"}


def parse_item(path: Path) -> dict | None:
    """Parse one item file into an id, the text to embed, and metadata."""
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return None  # a few files in the dataset are empty
    lines = text.strip().split("\n")

    # Most files open with "# [Flame Tongue](https://...)". Fall back to the filename.
    name = path.stem
    for line in lines:
        if m := H1_PATTERN.match(line.strip()):
            name = m.group(1).split("](")[0].strip()
            break

    # The first tag line looks like: #Weapon *(Any Melee Weapon),* #Rare *(Requires Attunement)*
    item_type, rarity, attunement = "", "", False
    for line in lines[:5]:
        tags = TAG_PATTERN.findall(line)
        if tags:
            for tag in tags:
                if tag.lower() in ITEM_TYPES:
                    item_type = tag
                elif tag.lower() in RARITIES:
                    rarity = tag
            attunement = "attunement" in line.lower()
            break

    return {
        "id": path.stem,
        "document": text,  # the full markdown is what gets embedded
        "metadata": {"name": name, "item_type": item_type, "rarity": rarity, "attunement": attunement},
    }


def main():
    # No embedding function given, so ChromaDB uses its default: all-MiniLM-L6-v2,
    # run locally. Whatever embeds the items must also embed the queries; ChromaDB
    # stores the choice with the collection so tools.py gets the same one.
    collection = chromadb.PersistentClient(path=str(CHROMA_PATH)).get_or_create_collection(
        "magic_items",
        configuration={"hnsw": {"space": "cosine"}},  # so 1 - distance is cosine similarity
    )

    items = [item for path in sorted(ITEMS_DIR.glob("*.md")) if (item := parse_item(path))]

    # upsert, not add, so re-running is safe. Batched to stay under request size limits.
    for i in range(0, len(items), 200):
        batch = items[i : i + 200]
        collection.upsert(
            ids=[item["id"] for item in batch],
            documents=[item["document"] for item in batch],
            metadatas=[item["metadata"] for item in batch],
        )

    print(f"Indexed {len(items)} items into {CHROMA_PATH.name}/")


if __name__ == "__main__":
    main()
