# API Reference

Base URL when running locally: `http://127.0.0.1:8000`

Interactive Swagger docs are available at `/docs` while the server runs.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/search` | Search with query parameters |
| POST | `/api/search` | Search with a JSON body |
| GET | `/health` | Service status and index size |
| GET | `/api` | Short JSON description of the API |
| GET | `/` | Web UI |

## Search parameters

| Name (GET) | Name (POST body) | Type | Required | Default | Rules |
|---|---|---|---|---|---|
| `q` | `query` | string | yes | none | 1 to 100 characters after cleaning, at least one letter or digit |
| `limit` | `limit` | integer | no | 5 | 1 to 50 |

### How the query is cleaned

Before matching, the query is:

1. Converted with Unicode NFKC normalization.
2. Stripped of control characters.
3. Lower-cased, trimmed, and internal whitespace collapsed to single spaces.

So `"  Credti   CARD "` becomes `"credti card"`. The original text is returned in `query` and the cleaned text in `normalized_query`.

## Response format

Every endpoint returns the same envelope, for both success and error cases. The schema is in [`schema/response.schema.json`](../schema/response.schema.json).

| Field | Type | Meaning |
|---|---|---|
| `success` | boolean | `true` for a completed search, `false` for an error |
| `query` | string or null | Query exactly as sent, or `null` if none was sent |
| `normalized_query` | string or null | Cleaned query. `null` on errors |
| `results` | array | Ranked matches. Empty on errors and when nothing matches |
| `total_results` | integer | Length of `results` |
| `meta` | object or null | Search settings and timing. `null` on errors |
| `error` | object or null | `null` on success, otherwise `{code, message}` |

### Result item

| Field | Type | Meaning |
|---|---|---|
| `rank` | integer | 1 is the best match |
| `term` | string | The indexed term that matched (a title or keyword) |
| `score` | number | Similarity from 0.0 to 1.0. Only an identical string scores 1.0 |
| `match_quality` | string | `very_high` (0.90 or more), `high` (0.75 or more), `medium` (0.70 or more) |
| `source` | string | Dataset name, currently `sample_dataset` |
| `metadata` | object | `document_id`, `title`, `category`, `keywords` of the matched document |

Each document appears at most once. When several of its terms match, the best one is shown.

### Meta object

| Field | Meaning |
|---|---|
| `limit` | Limit applied to this search |
| `min_score` | Minimum score for a result to be returned (0.70) |
| `engine` | `bigram-index+levenshtein+soundex` |
| `elapsed_ms` | Server-side time for the search |

## Examples

Response bodies below are real output from the sample dataset. `elapsed_ms` varies by machine.

### 1. Search with GET

```bash
curl "http://127.0.0.1:8000/api/search?q=credti%20card&limit=2"
```

```json
{
  "success": true,
  "query": "credti card",
  "normalized_query": "credti card",
  "results": [
    {
      "rank": 1,
      "term": "credit card",
      "score": 0.9166,
      "match_quality": "very_high",
      "source": "sample_dataset",
      "metadata": {
        "document_id": "doc-01",
        "title": "Credit Card",
        "category": "Finance",
        "keywords": ["credit card", "banking", "payment", "card limit"]
      }
    },
    {
      "rank": 2,
      "term": "debit card",
      "score": 0.825,
      "match_quality": "high",
      "source": "sample_dataset",
      "metadata": {
        "document_id": "doc-02",
        "title": "Debit Card",
        "category": "Finance",
        "keywords": ["debit card", "banking", "atm", "account"]
      }
    }
  ],
  "total_results": 2,
  "meta": {
    "limit": 2,
    "min_score": 0.7,
    "engine": "bigram-index+levenshtein+soundex",
    "elapsed_ms": 0.8
  },
  "error": null
}
```

### 2. Search with POST

```bash
curl -X POST "http://127.0.0.1:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "ransomwar", "limit": 1}'
```

```json
{
  "success": true,
  "query": "ransomwar",
  "normalized_query": "ransomwar",
  "results": [
    {
      "rank": 1,
      "term": "ransomware",
      "score": 0.99,
      "match_quality": "very_high",
      "source": "sample_dataset",
      "metadata": {
        "document_id": "doc-04",
        "title": "Ransomware",
        "category": "Cybersecurity",
        "keywords": ["ransomware", "malware", "encryption", "threat"]
      }
    }
  ],
  "total_results": 1,
  "meta": {
    "limit": 1,
    "min_score": 0.7,
    "engine": "bigram-index+levenshtein+soundex",
    "elapsed_ms": 0.8
  },
  "error": null
}
```

### 3. A short misspelling

`GET /api/search?q=grom` returns `brom` at 0.75 (`high`). The letters differ by one and the Soundex codes match.

```json
{
  "success": true,
  "query": "grom",
  "normalized_query": "grom",
  "results": [
    {
      "rank": 1,
      "term": "brom",
      "score": 0.75,
      "match_quality": "high",
      "source": "sample_dataset",
      "metadata": {
        "document_id": "doc-05",
        "title": "Brom",
        "category": "Science",
        "keywords": ["brom", "bromine", "chemical", "element"]
      }
    }
  ],
  "total_results": 1,
  "meta": {"limit": 5, "min_score": 0.7, "engine": "bigram-index+levenshtein+soundex", "elapsed_ms": 0.8},
  "error": null
}
```

### 4. No match (not an error)

`GET /api/search?q=banana` returns HTTP 200 with an empty list.

```json
{
  "success": true,
  "query": "banana",
  "normalized_query": "banana",
  "results": [],
  "total_results": 0,
  "meta": {"limit": 5, "min_score": 0.7, "engine": "bigram-index+levenshtein+soundex", "elapsed_ms": 0.8},
  "error": null
}
```

### 5. Health check

```bash
curl "http://127.0.0.1:8000/health"
```

```json
{
  "status": "healthy",
  "index": {"documents": 8, "indexed_terms": 34, "bigrams": 115}
}
```

Note: `/health` returns its own small format, not the search envelope.

## Errors

Errors use the same envelope with `success: false`, an empty `results` list, and an `error` object.

| HTTP | Code | Cause |
|---|---|---|
| 400 | `MISSING_QUERY` | No query was sent |
| 400 | `EMPTY_QUERY` | Query is empty or only whitespace |
| 400 | `QUERY_TOO_LONG` | Query is over 100 characters |
| 400 | `INVALID_QUERY` | Query has no letter or digit (for example `!!!`) |
| 400 | `INVALID_LIMIT` | `limit` is not an integer from 1 to 50 |
| 400 | `INVALID_REQUEST` | Body or parameters have the wrong type |
| 404 | `NOT_FOUND` | Unknown path |
| 405 | `METHOD_NOT_ALLOWED` | Wrong HTTP method for the path |
| 500 | `INTERNAL_ERROR` | Unexpected server error. No internal details are exposed |

### Empty query

`GET /api/search?q=%20%20`

```json
{
  "success": false,
  "query": "  ",
  "normalized_query": null,
  "results": [],
  "total_results": 0,
  "meta": null,
  "error": {"code": "EMPTY_QUERY", "message": "Query cannot be empty or whitespace only"}
}
```

### Missing query

`GET /api/search`

```json
{
  "success": false,
  "query": null,
  "normalized_query": null,
  "results": [],
  "total_results": 0,
  "meta": null,
  "error": {"code": "MISSING_QUERY", "message": "Provide a query, for example ?q=grom"}
}
```

### Invalid limit

`GET /api/search?q=grom&limit=0`

```json
{
  "success": false,
  "query": "grom",
  "normalized_query": null,
  "results": [],
  "total_results": 0,
  "meta": null,
  "error": {"code": "INVALID_LIMIT", "message": "limit must be an integer between 1 and 50"}
}
```

### Symbols only

`GET /api/search?q=!!!`

```json
{
  "success": false,
  "query": "!!!",
  "normalized_query": null,
  "results": [],
  "total_results": 0,
  "meta": null,
  "error": {"code": "INVALID_QUERY", "message": "Query must contain at least one letter or digit"}
}
```

### Unknown path

`GET /nope`

```json
{
  "success": false,
  "query": null,
  "normalized_query": null,
  "results": [],
  "total_results": 0,
  "meta": null,
  "error": {"code": "NOT_FOUND", "message": "Not Found"}
}
```

## Client code

### Python

```python
import requests

resp = requests.get(
    "http://127.0.0.1:8000/api/search",
    params={"q": "firwall", "limit": 3},
    timeout=5,
)
data = resp.json()

if data["success"]:
    for item in data["results"]:
        print(item["rank"], item["term"], item["score"], item["match_quality"])
else:
    print("Error:", data["error"]["code"], data["error"]["message"])
```

Output:

```
1 firewall 0.9833 very_high
```

### JavaScript

```javascript
async function search(q, limit = 5) {
  const url = `/api/search?limit=${limit}&q=${encodeURIComponent(q)}`;
  const res = await fetch(url);
  const data = await res.json();
  if (!data.success) throw new Error(data.error.message);
  return data.results;
}

search("pasport").then(r => console.log(r[0].term)); // "passport"
```

### Handling responses

| Situation | What to check |
|---|---|
| Search worked | `success === true`, read `results` |
| Nothing matched | `success === true` and `total_results === 0` |
| Bad input | `success === false`, read `error.code` |
| Server fault | HTTP 500 and `error.code === "INTERNAL_ERROR"` |

Always URL-encode the query. Use `encodeURIComponent` in JavaScript, or pass `params=` in Python `requests`.
