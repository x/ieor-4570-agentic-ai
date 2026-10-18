"""Recompute every sample's target in evals/dataset.jsonl by running its gold SQL against a Parquet file.

    uv run evals/update_targets.py data/311-full.parquet
"""
import json
import sys
from pathlib import Path

import duckdb

DATASET = Path(__file__).parent / "dataset.jsonl"


def to_text(value):
    # 21.80 -> "21.8", 366 -> "366"
    return f"{value:g}" if isinstance(value, float) else str(value)


def main(data):
    db = duckdb.connect()
    db.sql(f"CREATE VIEW requests AS SELECT * FROM '{data}'")

    samples = [json.loads(line) for line in DATASET.read_text().splitlines()]
    for sample in samples:
        rows = db.sql(sample["metadata"]["gold_sql"]).fetchall()
        sample["target"] = to_text(rows[0][0])

    DATASET.write_text("".join(json.dumps(s) + "\n" for s in samples))
    print(f"Updated {len(samples)} targets in {DATASET} from {data}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/311-sample.parquet")
