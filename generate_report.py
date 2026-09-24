"""P6 - run every case through the integrated pipeline and write TEST_REPORT.md"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import pipeline  # noqa: E402
from app.normalize import QueryError  # noqa: E402
from app.schemas import error_body  # noqa: E402
from tests.p6_cases import CASES, evaluate  # noqa: E402


def run(query):
    try:
        return pipeline.search(query)
    except QueryError as exc:
        return error_body(exc.code, exc.message, query)


def cell(text):
    return str(text).replace("|", "\\|")


rows, passed, false_pos, false_neg = [], 0, [], []
for case in CASES:
    body = run(case["input"])
    ok, expected = evaluate(case, body)
    passed += ok
    if not body["success"]:
        actual, sc = f"error {body['error']['code']}", "-"
    elif not body["results"]:
        actual, sc = "no results", "-"
    else:
        actual = ", ".join(f"{r['metadata']['title']} ({r['score']})" for r in body["results"][:3])
        sc = body["results"][0]["score"]
    e = case["expect"]
    if not ok:
        if e.get("none") and body["results"]:
            false_pos.append(case)
        elif not body["results"] and "error" not in e:
            false_neg.append(case)
    shown = case["input"] if len(case["input"]) < 30 else case["input"][:12] + "... (%d chars)" % len(case["input"])
    rows.append(f"| {case['id']} | {case['category']} | `{cell(shown)}` | {cell(expected)} | {cell(actual)} | {sc} | {'PASS' if ok else 'FAIL'} |")

lines = ["# Test report: integrated fuzzy search (P8)", "",
         f"Cases run through the full pipeline (normalize, index, score, rank, JSON): **{len(CASES)}**  ",
         f"Passed: **{passed}**  Failed: **{len(CASES) - passed}**", "",
         "| ID | Category | Input | Expected | Actual (top 3) | Top score | Result |",
         "|---|---|---|---|---|---|---|", *rows, "",
         "## False positives", ""]
lines += [f"- {c['id']} `{c['input']}` returned results but should return none." for c in false_pos] or \
         ["None in this suite. `banana` (found in P6 against the un-integrated index at 0.571) and `elephant` (0.667 to `element`) "
          "are both removed by the 0.70 minimum score."]
lines += ["", "## False negatives", ""]
lines += [f"- {c['id']} `{c['input']}` should have matched but returned nothing." for c in false_neg] or \
         ["None in this suite."]
lines += ["", "## Known limits (not covered by the suite)", "",
          "- The 0.70 cut-off trades recall for precision. Typos that drop the score below 0.70 return nothing, "
          "for example a 4-letter word with two wrong letters.",
          "- The index only shortlists entries that share a two-letter pair with the query. A typo that destroys every pair "
          "(`ps` for `passport`) is not found.",
          "- `ca` and `ba` match by prefix at a fixed 0.70. Prefix matches will rank below typo matches of longer words.",
          "- With 8 documents the false-positive rate is low. A larger dataset will produce more near matches and the "
          "threshold should be re-tuned against it.", ""]
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "TEST_REPORT.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print(f"{passed}/{len(CASES)} passed -> TEST_REPORT.md")
