"""Demo: walks each example query through every stage, then calls the real HTTP endpoint.
Run:  python demo.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient  # noqa: E402

from app import config  # noqa: E402
from app.main import app  # noqa: E402
from app.normalize import normalize_query  # noqa: E402
from app.pipeline import get_index  # noqa: E402
from app.ranking import rank_results  # noqa: E402
from app.scoring import score_term  # noqa: E402

QUERIES = ["grom", "credti card", "ransomare", "passpord", "banana"]


def stages(raw):
    print(f"\n=== Query: {raw!r}")
    q = normalize_query(raw)
    print(f"1. Search API / normalize   -> {q.normalized!r}")
    cands = get_index().candidates(q.normalized)
    print(f"2. Search index             -> {len(cands)} candidate terms")
    scored = [(e, score_term(q.normalized, e["term"])) for e in cands]
    kept = [(e, s) for e, s in scored if s.score >= config.MIN_SCORE]
    print(f"3. Fuzzy match + 4. Score   -> {len(kept)} of {len(cands)} score >= {config.MIN_SCORE}")
    ranked = rank_results([{"term": e["term"], "score": s.score} for e, s in kept], limit=5, query=q.normalized)
    print("5. Ranking                  -> " + (", ".join(f"{r['term']} {r['score']}" for r in ranked) or "nothing"))


def main():
    client = TestClient(app)
    for raw in QUERIES:
        stages(raw)
    print("\n\n##### 6. JSON response from GET /api/search?q=grom")
    print(json.dumps(client.get("/api/search", params={"q": "grom"}).json(), indent=2))
    print("\n##### Error response from GET /api/search?q=%20%20")
    print(json.dumps(client.get("/api/search", params={"q": "  "}).json(), indent=2))


if __name__ == "__main__":
    main()
