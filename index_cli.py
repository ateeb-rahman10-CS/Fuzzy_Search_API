"""P3 - run the search index on its own, no API/FastAPI required.

For teammates who only need the index/matching layer (P2/P3/P4/P5) and
don't want to stand up the HTTP service. Uses the same dataset and the
same scoring/ranking code as the API, so results are identical to what
/api/search returns.

Usage:
    python index_cli.py grom
    python index_cli.py "credti card" --limit 3
    python index_cli.py --stats
"""
from __future__ import annotations

import argparse
import json

from app.index import SearchIndex
from app.ranking import rank_results
from app.scoring import interpret, score_term


def search_index_only(index: SearchIndex, query: str, limit: int = 5) -> list[dict]:
    q = query.strip().lower()
    scored = []
    for entry in index.candidates(q):
        s = score_term(q, entry["term"])
        if s.score < 0.70:
            continue
        scored.append({
            "term": entry["term"],
            "score": s.score,
            "match_quality": interpret(s.score),
            "document_id": entry["document"]["id"],
        })
    # de-dupe: best score per document
    best: dict[str, dict] = {}
    for item in scored:
        cur = best.get(item["document_id"])
        if cur is None or item["score"] > cur["score"]:
            best[item["document_id"]] = item
    return rank_results(list(best.values()), limit=limit, query=q)


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the fuzzy search index directly (P3, no API).")
    parser.add_argument("query", nargs="?", help="Search query, e.g. grom")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--stats", action="store_true", help="Print index stats and exit")
    parser.add_argument("--dataset", default=None, help="Path to an alternate dataset.json")
    args = parser.parse_args()

    index = SearchIndex(dataset_path=args.dataset)

    if args.stats or not args.query:
        print(json.dumps(index.stats(), indent=2))
        if not args.query:
            return

    results = search_index_only(index, args.query, args.limit)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
