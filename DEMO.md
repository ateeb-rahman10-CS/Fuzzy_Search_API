# Demo Guide

A step-by-step script to run and present the prototype end to end. It takes about 5 minutes.

The prototype: a misspelled query goes in, and ranked matches with similarity scores come out, through a web page and a REST API.

## 1. Setup (once)

You need Python 3.10 or newer.

**macOS / Linux**

```bash
cd fuzzy_search_prototype
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell)**

```powershell
cd fuzzy_search_prototype
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Start the server

```bash
python run.py
```

Expected output ends with:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Leave this terminal open. Open a second terminal for the API and CLI steps.

## 3. Web demo

Open http://127.0.0.1:8000 in your browser.

![Home page](images/home.png)

Check the top bar first. The green badge should read **API online**, and the stat cards should show **8** documents, **34** terms and **115** bigrams.

Now type each query below (or click the colored chips) and compare with the expected result.

| Type | Expected top result | Score | Label | Shows |
|---|---|---|---|---|
| `grom` | Brom (Science) | 75% | High match | A short word with one wrong letter |
| `credti card` | Credit Card (Finance), then Debit Card | 92%, 83% | Very high, High | Swapped letters and several results |
| `firwall` | Firewall (Cybersecurity) | 98% | Very high match | A missing letter |
| `ransomwar` | Ransomware (Cybersecurity) | 99% | Very high match | A truncated word |
| `pasport` | Passport (Identity) | 98% | Very high match | A dropped letter |
| `Credti   CARD` | Same as `credti card` | 92%, 83% | | Case and extra spaces are cleaned |
| `web` | Web Browser (Software) | 90% | Very high match | A partial word |
| `banana` | No matches found | | | Low-similarity queries are rejected, not forced |

![Results for credti card](images/results.png)

Points to mention while demoing:

- Results update as you type, with a short delay.
- The ring shows the similarity score, and the colored tag shows the category.
- The tags above the cards show the minimum score (0.7), the search time in milliseconds and the engine used.
- The **Last query (ms)** stat card updates after each search.
- Clearing the box returns the page to its start state.

## 4. API demo

In the second terminal:

```bash
curl "http://127.0.0.1:8000/api/search?q=credti%20card&limit=2"
```

Expected: `"success": true`, two results, `credit card` at `0.9166` and `debit card` at `0.825`.

Try a POST request:

```bash
curl -X POST "http://127.0.0.1:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "ransomwar", "limit": 1}'
```

Expected: one result, `ransomware` at `0.99`.

Show an error response:

```bash
curl "http://127.0.0.1:8000/api/search?q=%20%20"
```

Expected: HTTP 400 with `"success": false` and error code `EMPTY_QUERY`.

Show a valid query with no match:

```bash
curl "http://127.0.0.1:8000/api/search?q=banana"
```

Expected: HTTP 200, `"success": true` and `"results": []`.

Check service health:

```bash
curl "http://127.0.0.1:8000/health"
```

Expected: `{"status":"healthy","index":{"documents":8,"indexed_terms":34,"bigrams":115}}`

Open http://127.0.0.1:8000/docs to show the interactive Swagger page. Use **Try it out** on `GET /api/search`.

More request and response examples are in [API.md](API.md).

## 5. Pipeline walkthrough (no server needed)

```bash
python demo.py
```

This prints each stage for five queries. Expected output for the first two:

```
=== Query: 'grom'
1. Search API / normalize   -> 'grom'
2. Search index             -> 7 candidate terms
3. Fuzzy match + 4. Score   -> 1 of 7 score >= 0.7
5. Ranking                  -> brom 0.75

=== Query: 'credti card'
1. Search API / normalize   -> 'credti card'
2. Search index             -> 11 candidate terms
3. Fuzzy match + 4. Score   -> 3 of 11 score >= 0.7
5. Ranking                  -> credit card 0.9166, card limit 0.825, debit card 0.825
```

It then prints a full JSON success response and an error response. The `credti card` run shows why the index matters: 11 of 34 terms are scored, not all of them.

Note: the ranking line lists terms, and the API keeps only the best term per document, so `card limit` (from the Credit Card document) does not appear as a separate API result.

## 6. Command-line search (index only)

```bash
python index_cli.py grom
python index_cli.py --stats
```

Expected for `grom`:

```json
[{"term": "brom", "score": 0.75, "match_quality": "high", "document_id": "doc-05"}]
```

Expected for `--stats`: 8 documents, 34 indexed terms, 115 bigrams.

## 7. Run the tests

```bash
python -m pytest -q
```

Expected: `75 passed`.

To regenerate the 22-case report:

```bash
python generate_report.py
```

## 8. Stop the server

Press `Ctrl+C` in the terminal that runs `python run.py`.

## Suggested talk track (2 minutes)

1. State the problem: users misspell words, and exact search returns nothing.
2. Type `credti card` in the web page and show the ranked results with scores.
3. Type `banana` to show that unrelated input returns no match instead of a wrong answer.
4. Run the `curl` request to show the same result as JSON.
5. Show `python demo.py` to explain the pipeline: normalize, bigram index, score, rank.
6. Finish with the test run and mention the 500 labelled examples in `data/`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'fastapi'` | Activate the virtual environment and run `pip install -r requirements.txt` |
| `Address already in use` on port 8000 | Stop the other program, or edit `port=8000` in `run.py` and use the new port in the URLs |
| The badge shows **API offline** | The server is not running or uses another port. Restart with `python run.py` |
| The page shows a plain font | The page loads Google Fonts. Offline, it uses your system font and still works |
| A query returns nothing | Scores under 0.70 are dropped by design. Try the sample queries above |
| `python` not found on macOS or Linux | Use `python3` |
