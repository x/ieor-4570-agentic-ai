# nyc-311-agent

An agent that answers questions about [NYC 311 Service Requests](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2020-to-Present/erm2-nwe9) (2020-2025).

_By default, a 5% sample is included in `data/`. The full dataset can be dowloaded with `./download-full.sh`._

`task.py` evaluates the agent with [Inspect](https://inspect.aisi.org.uk/) on the 128 samples in `evals/dataset.jsonl`. Run `gcloud auth application-default login`, then `uv run main.py "Which borough had the most noise complaints in 2024?"`, or `uv run inspect eval task.py` and `uv run inspect view`. For every row instead of the sample, run `./download-full.sh` (~2.5 hours).

## Where the samples came from

Two kinds of questions people have actually asked of this dataset, rewritten to have one answer inside 2020-2025.

**Saved views.** NYC Open Data keeps the queries people save against a dataset: 165 of them for this one, from `https://data.cityofnewyork.us/api/views/erm2-nwe9.json?method=getRelatedViews`. Before:

```json
{
  "id": "23nc-6gja",
  "name": "Taxi Report After February 24",
  "viewCount": 131,
  "queryString": "SELECT `unique_key`, `created_date`, ... WHERE (`created_date` > \"2016-02-24T00:00:00\") and (upper(`complaint_type`) = \"TAXI REPORT\") ORDER BY `created_date` DESC NULL LAST"
}
```

After:

```json
{"id": "sv-23nc-6gja", "input": "What was the most common kind of taxi complaint in 2024?", "target": "Driver Complaint - Passenger", "metadata": {"gold_sql": "SELECT descriptor FROM requests WHERE complaint_type = 'Taxi Complaint' AND year(created_date) = 2024 GROUP BY descriptor ORDER BY count(*) DESC LIMIT 1", "difficulty": "medium", "origin": "saved_view", "source": "https://data.cityofnewyork.us/d/23nc-6gja"}}
```

**Published analyses.** Questions from reports, articles, and analysis repos: the NYC Council Data Team, the NY State Comptroller, the NYC Rat Report, John Jay's Data Collaborative for Justice, CBS, Gothamist, City Journal, and GitHub analyses. Before, from [CBS](https://www.cbsnews.com/newyork/news/nyc-rat-complaints-down/): "How did rat complaints change from 2023 to 2024? (more than -25%)". After:

```json
{"id": "pub-rodent-yoy-2023-2024", "input": "By what percentage did rodent complaints change from 2023 to 2024?", "target": "-3.1", "metadata": {"gold_sql": "SELECT round(100.0 * (count(*) FILTER (WHERE year(created_date) = 2024) - count(*) FILTER (WHERE year(created_date) = 2023)) / count(*) FILTER (WHERE year(created_date) = 2023), 1) FROM requests WHERE complaint_type = 'Rodent'", "difficulty": "hard", "origin": "published", "source": "https://www.cbsnews.com/newyork/news/nyc-rat-complaints-down/"}}
```

The published number is not the target: the sources counted different snapshots and categories. Every target comes from running its `gold_sql`.
