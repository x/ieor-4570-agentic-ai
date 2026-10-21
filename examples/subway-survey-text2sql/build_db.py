"""Build the database. Run once, offline, before app.py.

Load the survey CSV into data/survey.duckdb, cleaned: 'NA' and '' become NULL, the
complaints column becomes a real list, and timestamps become timestamps.
"""

from pathlib import Path

import duckdb

DATA = Path(__file__).parent / "data"
CSV_PATH = DATA / "subway_rider_survey_2019.csv"
DB_PATH = DATA / "survey.duckdb"

DB_PATH.unlink(missing_ok=True)
db = duckdb.connect(str(DB_PATH))
db.execute(f"""
    CREATE TABLE survey AS
    SELECT * REPLACE (
        json_extract_string(top_three_complaints, '$[*]')::VARCHAR[] AS top_three_complaints,
        strptime(submitted_at, '%m/%d/%Y @ %I:%M %p') AS submitted_at
    )
    FROM read_csv('{CSV_PATH}', nullstr = ['NA', ''], types = {{'zip_code': 'VARCHAR', 'subway_line_used_most_often': 'VARCHAR'}})
""")
rows = db.execute("SELECT count(*) FROM survey").fetchone()[0]
db.close()
print(f"Built {DB_PATH.name} ({rows} rows)")
