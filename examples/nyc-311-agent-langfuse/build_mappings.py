"""Build the database and its schema mappings. Run once, offline, before app.py.

1. Copy the 311 Parquet file into data/311.duckdb, which app.py opens read-only.
2. Describe every column: its type, and either its valid values (enums) or samples.
3. Ask the model for a one-sentence description of each column.
4. Write it all to data/311_mappings.json, the context app.py retrieves.
"""

import json
from pathlib import Path

import duckdb
import litellm

DATA = Path(__file__).parent / "data"
# Use the full data if download-full.sh has been run, otherwise the committed 5% sample.
PARQUET = DATA / "311-full.parquet" if (DATA / "311-full.parquet").exists() else DATA / "311-sample.parquet"
DB_PATH = DATA / "311.duckdb"
MAPPINGS_PATH = DATA / "311_mappings.json"
# complaint_type has ~240 values, and it's the column questions filter on most. descriptor (~1,000) is too many.
MAX_ENUM_VALUES = 300

# --- 1. The database ---

DB_PATH.unlink(missing_ok=True)
db = duckdb.connect(str(DB_PATH))
db.execute(f"CREATE TABLE requests AS SELECT * FROM '{PARQUET}'")

# --- 2. Describe each column ---

columns = []
for name, dtype, *_ in db.execute("DESCRIBE requests").fetchall():
    distinct = f"SELECT DISTINCT {name} AS v FROM requests WHERE {name} IS NOT NULL"
    count = db.execute(f"SELECT count(*) FROM ({distinct})").fetchone()[0]
    column = {"name": name, "type": dtype}
    if count <= MAX_ENUM_VALUES and dtype == "VARCHAR":
        column["enum_values"] = [row[0] for row in db.execute(f"{distinct} ORDER BY v").fetchall()]
    else:
        column["samples"] = [row[0] for row in db.execute(f"{distinct} LIMIT 5").fetchall()]
    columns.append(column)
db.close()

# --- 3. Describe each column, with the model ---

prompt = (
    "These are the columns of NYC 311 service requests (2020-2025), with their types and either "
    "their valid values or samples. Write a concise one-sentence description of what each column "
    "represents. Don't just list the values. Return a JSON object mapping each column name to its "
    "description.\n\n" + json.dumps(columns, default=str)[:60000]
)
response = litellm.completion(
    model="vertex_ai/gemini-3.5-flash-lite",
    vertex_location="global",
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"},
)
descriptions = json.loads(response.choices[0].message.content)

# --- 4. Write the mappings ---

for column in columns:
    column["description"] = descriptions.get(column["name"], "")
    column.pop("samples", None)  # samples helped the model describe the column; the agent doesn't need them
MAPPINGS_PATH.write_text(json.dumps({"table": "requests", "columns": columns}, indent=2, default=str))
print(f"Built {DB_PATH.name} and {MAPPINGS_PATH.name} ({len(columns)} columns) from {PARQUET.name}")
