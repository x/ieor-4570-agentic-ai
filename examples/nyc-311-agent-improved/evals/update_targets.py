"""Recompute every sample's target in evals/dataset.jsonl by running its gold SQL against a Parquet file.

    uv run evals/update_targets.py data/311-full.parquet
    uv run evals/update_targets.py data/311-sample.parquet evals/neighborhoods.jsonl
"""
import json
import sys
from pathlib import Path

import duckdb



def to_text(value):
    # 21.80 -> "21.8", 366 -> "366"
    return f"{value:g}" if isinstance(value, float) else str(value)


def main(data, dataset=Path(__file__).parent / "dataset.jsonl"):
    db = duckdb.connect()
    db.sql(f"CREATE VIEW requests AS SELECT * FROM '{data}'")

    samples = [json.loads(line) for line in Path(dataset).read_text().splitlines()]
    for sample in samples:
        rows = db.sql(sample["metadata"]["gold_sql"]).fetchall()
        sample["target"] = to_text(rows[0][0])

    Path(dataset).write_text("".join(json.dumps(s) + "\n" for s in samples))
    print(f"Updated {len(samples)} targets in {dataset} from {data}")


if __name__ == "__main__":
    main(*(sys.argv[1:] or ["data/311-sample.parquet"]))
