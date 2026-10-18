#!/usr/bin/env bash
# Download every NYC 311 Service Request from 2020-2025 into data/311-full.parquet (~20M rows, ~2.5 hours).
#
# The committed data/311-sample.parquet is the 5% of these rows whose unique_key is divisible by 20.
# Dataset: https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2020-to-Present/erm2-nwe9
set -euo pipefail
cd "$(dirname "$0")"

URL="https://data.cityofnewyork.us/resource/erm2-nwe9.csv"
COLUMNS="unique_key,created_date,closed_date,agency,agency_name,complaint_type,descriptor,location_type,incident_zip,city,borough,community_board,council_district,police_precinct,status,resolution_description,open_data_channel_type"
RAW="data/raw"
OUT="data/311-full.parquet"
mkdir -p "$RAW"

# One request per month keeps each response small enough not to time out.
for year in 2020 2021 2022 2023 2024 2025; do
  for month in 01 02 03 04 05 06 07 08 09 10 11 12; do
    file="$RAW/$year-$month.csv"
    [ -s "$file" ] && continue
    start="$year-$month-01"
    end=$(date -j -v+1m -f %Y-%m-%d "$start" +%Y-%m-%d 2>/dev/null || date -d "$start +1 month" +%Y-%m-%d)
    echo "Downloading $year-$month"
    curl -sfG "$URL" \
      --data-urlencode "\$select=$COLUMNS" \
      --data-urlencode "\$where=created_date >= '$start' AND created_date < '$end'" \
      --data-urlencode "\$order=unique_key" \
      --data-urlencode "\$limit=10000000" \
      -o "$file.tmp"
    mv "$file.tmp" "$file"
  done
done

echo "Writing $OUT"
uv run python - "$RAW" "$OUT" <<'EOF'
import sys
import duckdb

raw, out = sys.argv[1:]
duckdb.sql(f"""
    COPY (
        SELECT * FROM read_csv('{raw}/*.csv', header = true, union_by_name = true,
                               types = {{'incident_zip': 'VARCHAR', 'council_district': 'VARCHAR'}})
        ORDER BY created_date
    ) TO '{out}' (FORMAT parquet, COMPRESSION zstd)
""")
print(duckdb.sql(f"SELECT count(*) AS rows, min(created_date), max(created_date) FROM '{out}'"))
EOF

# The dataset's targets were computed on the 5% sample. The agent uses the full data once it exists.
read -r -p "Update the targets in evals/dataset.jsonl to the full data? [y/N] " reply
if [[ "$reply" =~ ^[Yy] ]]; then
  uv run evals/update_targets.py "$OUT"
fi
