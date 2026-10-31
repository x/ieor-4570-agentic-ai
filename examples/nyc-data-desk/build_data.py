"""Build each analyst's database and schema mappings. Run once, offline, before app.py.

The same build as nyc-311-agent-improved and subway-survey-text2sql-improved, for both datasets:
1. Load the raw data into data/<name>.duckdb, which app.py opens read-only.
2. Describe every column: its type, and either its valid values (enums) or samples.
3. Ask the model for a one-sentence description of each column.
4. Write it all to data/<name>_mappings.json, the context each analyst retrieves.
"""

import json
from pathlib import Path

import duckdb
import litellm

DATA = Path(__file__).parent / "data"

DATASETS = {
    "311": {
        "table": "requests",
        "about": "NYC 311 service requests (2020-2025)",
        "load": f"SELECT * FROM '{DATA / '311-sample.parquet'}'",
        # complaint_type has ~240 values, and questions filter on it most. descriptor (~1,000) is too many.
        "max_enum_values": 300,
    },
    "survey": {
        "table": "survey",
        "about": "a 2019 NYC subway rider survey",
        # Cleaned on the way in: 'NA' and '' become NULL, complaints become a list, timestamps become timestamps.
        "load": f"""
            SELECT * REPLACE (
                json_extract_string(top_three_complaints, '$[*]')::VARCHAR[] AS top_three_complaints,
                strptime(submitted_at, '%m/%d/%Y @ %I:%M %p') AS submitted_at
            )
            FROM read_csv('{DATA / 'subway_rider_survey_2019.csv'}', nullstr = ['NA', ''],
                          types = {{'zip_code': 'VARCHAR', 'subway_line_used_most_often': 'VARCHAR'}})""",
        "max_enum_values": 50,
    },
}

for name, dataset in DATASETS.items():
    table, db_path = dataset["table"], DATA / f"{name}.duckdb"

    # --- 1. The database ---
    db_path.unlink(missing_ok=True)
    db = duckdb.connect(str(db_path))
    db.execute(f"CREATE TABLE {table} AS {dataset['load']}")

    # --- 2. Describe each column ---
    columns = []
    for column_name, dtype, *_ in db.execute(f"DESCRIBE {table}").fetchall():
        # List columns (top_three_complaints) take their values from the unnested items.
        values = f"unnest({column_name})" if dtype.endswith("[]") else column_name
        distinct = f"SELECT DISTINCT {values} AS v FROM {table} WHERE {column_name} IS NOT NULL"
        count = db.execute(f"SELECT count(*) FROM ({distinct})").fetchone()[0]
        column = {"name": column_name, "type": dtype}
        if count <= dataset["max_enum_values"] and dtype.startswith("VARCHAR"):
            column["enum_values"] = [row[0] for row in db.execute(f"{distinct} ORDER BY v").fetchall()]
        else:
            column["samples"] = [row[0] for row in db.execute(f"{distinct} LIMIT 5").fetchall()]
        columns.append(column)
    db.close()

    # --- 3. Describe each column, with the model ---
    prompt = (
        f"These are the columns of {dataset['about']}, with their types and either their valid values "
        "or samples. Write a concise one-sentence description of what each column represents. Don't just "
        "list the values. Return a JSON object mapping each column name to its description.\n\n"
        + json.dumps(columns, default=str)[:60000]
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
    (DATA / f"{name}_mappings.json").write_text(json.dumps({"table": table, "columns": columns}, indent=2, default=str))
    print(f"Built {db_path.name} and {name}_mappings.json ({len(columns)} columns)")
