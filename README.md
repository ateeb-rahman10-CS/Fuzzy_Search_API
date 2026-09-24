# Fuzzyfind: Fuzzy Search Prototype

A typo-tolerant search service with a pastel web interface. Type a misspelled query such as `grom` or `credti card` and get ranked matches with a similarity score from 0.0 to 1.0.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)
![Tests](https://img.shields.io/badge/tests-75%20passing-3fbf8f)
![Status](https://img.shields.io/badge/status-prototype-8c7ae6)

![Fuzzyfind web UI](docs/images/results.png)

## Features

- Fuzzy matching with a bigram inverted index, Levenshtein distance and a Soundex boost
- One scoring scale (0.0 to 1.0) and a match-quality label: `very_high`, `high` or `medium`
- Deterministic ranking with fair tie-breaking
- Web UI with live search, example chips, score rings and category tags
- REST API with interactive docs at `/docs`
- One JSON response schema for both success and error cases
- 75 automated tests and 500 labelled example queries

## Quick start

Requires Python 3.10 or newer.

```bash
git clone https://github.com/<your-username>/fuzzy-search-prototype.git
cd fuzzy-search-prototype
pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:8000 for the web UI, or http://127.0.0.1:8000/docs for the API docs.

## Demo in 2 minutes

```bash
pip install -r requirements.txt
python run.py
```

1. Open http://127.0.0.1:8000 and type `credti card`. Expect **Credit Card** at 92% and **Debit Card** at 83%.
2. Type `banana`. Expect no matches, because nothing scores 0.70 or higher.
3. In a second terminal run `curl "http://127.0.0.1:8000/api/search?q=firwall&limit=1"`. Expect `firewall` at `0.9833`.
4. Run `python demo.py` to see every pipeline stage, and `python -m pytest -q` to run 75 tests.

The full presentation script, expected outputs and troubleshooting are in [docs/DEMO.md](docs/DEMO.md).

## Documentation

| Document | Contents |
|---|---|
| [docs/DEMO.md](docs/DEMO.md) | Step-by-step demo script with expected outputs and troubleshooting |
| [docs/API.md](docs/API.md) | Endpoints, parameters, response fields, error codes, request and response examples, Python and JavaScript clients |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Request flow diagram, components, index, scoring rules, ranking, error handling, configuration |
| [docs/DESIGN_NOTES.md](docs/DESIGN_NOTES.md) | Integration decisions and approach comparison |

## How it works

```
User query
  -> Search API        app/main.py       request validation in app/normalize.py
  -> Search index      app/index.py      bigram inverted index over data/dataset.json
  -> Similarity score  app/scoring.py    Levenshtein ratio + Soundex, 0.0 to 1.0
  -> Result ranking    app/ranking.py    score, then length closeness, then alphabetical
  -> JSON response     app/schemas.py    schema in schema/response.schema.json
```

`app/pipeline.py` runs the whole chain in one function, and the API only calls `pipeline.search()`.

### Scoring rules

1. Edit-distance ratio from `rapidfuzz`, on lower-cased text.
2. Add 0.05 when the Soundex codes match.
3. For multi-word terms, average the best word-level score. Partial matches (`web` for `web browser`) are multiplied by 0.90.
4. A query that starts a word (`ca` for `card`, 2+ letters) scores 0.70.
5. Only an identical string scores 1.0. Everything else is capped at 0.99, and scores under 0.70 are dropped.

## API

| Method | Path | Input |
|---|---|---|
| GET | `/api/search?q=grom&limit=5` | `q` required, `limit` optional (1 to 50, default 5) |
| POST | `/api/search` | JSON body `{"query": "grom", "limit": 5}` |
| GET | `/health` | Returns index size |
| GET | `/docs` | Interactive Swagger docs |

### Example

```bash
curl "http://127.0.0.1:8000/api/search?q=credti%20card&limit=2"
```

```json
{
  "success": true,
  "query": "credti card",
  "normalized_query": "credti card",
  "results": [
    {"rank": 1, "term": "credit card", "score": 0.9166, "match_quality": "very_high",
     "source": "sample_dataset",
     "metadata": {"document_id": "doc-01", "title": "Credit Card", "category": "Finance",
                  "keywords": ["credit card", "banking", "payment", "card limit"]}},
    {"rank": 2, "term": "debit card", "score": 0.825, "match_quality": "high",
     "source": "sample_dataset",
     "metadata": {"document_id": "doc-02", "title": "Debit Card", "category": "Finance",
                  "keywords": ["debit card", "banking", "atm", "account"]}}
  ],
  "total_results": 2,
  "meta": {"limit": 2, "min_score": 0.7, "engine": "bigram-index+levenshtein+soundex", "elapsed_ms": 1.1},
  "error": null
}
```

A valid query with no match is not an error. It returns HTTP 200 with `results: []`.

Error codes: `MISSING_QUERY`, `EMPTY_QUERY`, `QUERY_TOO_LONG` (over 100 characters), `INVALID_QUERY`, `INVALID_LIMIT`, `INVALID_REQUEST`, `NOT_FOUND`, `METHOD_NOT_ALLOWED`, `INTERNAL_ERROR`.

## Sample queries

| You type | Best match |
|---|---|
| `credti card` | credit card |
| `firwall` | firewall |
| `ransomwar` | ransomware |
| `pasport` | passport |
| `databse` | database |
| `brwoser` | browser |

These run against the 8-document sample dataset. A separate set of 500 labelled misspelling examples is in [`data/examples.json`](data/examples.json) and [`data/examples.csv`](data/examples.csv).

## Testing

```bash
python -m pytest -q          # 75 tests
python demo.py               # prints every pipeline stage for 5 queries
python generate_report.py    # rewrites TEST_REPORT.md (22 cases)
```

- `tests/test_units.py`: normalization, scoring, ranking, index
- `tests/test_api.py`: endpoints, errors, schema validation of every response
- `tests/test_p6_cases.py`: 22 cases through the full pipeline

## Configuration

All tunable values live in `app/config.py`.

| Setting | Default | Purpose |
|---|---|---|
| `MIN_SCORE` | 0.70 | Results below this score are dropped |
| `DEFAULT_LIMIT` | 5 | Default number of results |
| `MAX_LIMIT` | 50 | Largest allowed limit |
| `MAX_QUERY_LENGTH` | 100 | Longest allowed query |
| `DATASET_PATH` | `data/dataset.json` | Override with an environment variable |

## Known limits

- The bigram index only shortlists terms that share a two-letter pair with the query, so `a` and `ps` return nothing.
- Two wrong letters in a 4-letter word score 0.50 and are not returned.
- Prefix matches are fixed at 0.70, so they rank below typo matches of longer words.
- The index loads once at startup. Restart the server after editing `data/dataset.json`.
- `MIN_SCORE` was tuned on an 8-document dataset. Re-tune it when the dataset grows.

## Project layout

```
app/            API, index, scoring, ranking, schemas, pipeline
app/static/     Web UI (index.html)
data/           dataset.json, examples.json, examples.csv
docs/           DEMO.md, API.md, ARCHITECTURE.md, DESIGN_NOTES.md, images/
schema/         response.schema.json
tests/          Unit, API and pipeline tests
demo.py  generate_report.py  index_cli.py  run.py  TEST_REPORT.md
```

See the Documentation section above for the full API reference and architecture notes.

## Tech stack

Python, FastAPI, Uvicorn, Pydantic, RapidFuzz, HTML, CSS and vanilla JavaScript.
