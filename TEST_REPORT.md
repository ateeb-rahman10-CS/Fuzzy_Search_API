# Test report: integrated fuzzy search (P8)

Cases run through the full pipeline (normalize, index, score, rank, JSON): **22**  
Passed: **22**  Failed: **0**

| ID | Category | Input | Expected | Actual (top 3) | Top score | Result |
|---|---|---|---|---|---|---|
| TC01 | Correct spelling | `passport` | top = Passport | Passport (1.0) | 1.0 | PASS |
| TC02 | Correct spelling | `firewall` | top = Firewall | Firewall (1.0) | 1.0 | PASS |
| TC03 | Character substitution | `grom` | top = Brom | Brom (0.75) | 0.75 | PASS |
| TC04 | Character substitution | `credti card` | top = Credit Card | Credit Card (0.9166), Debit Card (0.825) | 0.9166 | PASS |
| TC05 | Missing character | `pasport` | top = Passport | Passport (0.9833) | 0.9833 | PASS |
| TC06 | Missing character | `ransomare` | top = Ransomware | Ransomware (0.99) | 0.99 | PASS |
| TC07 | Extra character | `firewalll` | top = Firewall | Firewall (0.99) | 0.99 | PASS |
| TC08 | Extra character | `ransomwaree` | top = Ransomware | Ransomware (0.99) | 0.99 | PASS |
| TC09 | Unrelated word | `banana` | no results | no results | - | PASS |
| TC10 | Unrelated word | `zzxxqqyy` | no results | no results | - | PASS |
| TC11 | Empty query | `` | error EMPTY_QUERY | error EMPTY_QUERY | - | PASS |
| TC12 | Empty query (spaces) | `   ` | error EMPTY_QUERY | error EMPTY_QUERY | - | PASS |
| TC13 | Very short query | `ca` | top in Credit Card / Debit Card | Debit Card (0.7), Credit Card (0.7) | 0.7 | PASS |
| TC14 | Very short query | `a` | no results | no results | - | PASS |
| TC15 | Multiple possible matches | `card` | contains Credit Card + Debit Card | Debit Card (0.9), Credit Card (0.9) | 0.9 | PASS |
| TC16 | Multiple possible matches | `web` | top in Web Browser | Web Browser (0.9) | 0.9 | PASS |
| TC17 | Typo, phonetic | `passpord` | top = Passport | Passport (0.925) | 0.925 | PASS |
| TC18 | Missing character | `databse` | top = Database Engine | Database Engine (0.9833) | 0.9833 | PASS |
| TC19 | Extra character | `malwaree` | top = Ransomware | Ransomware (0.9833) | 0.9833 | PASS |
| TC20 | Mixed case and spaces | `  FIREWAL ` | top = Firewall | Firewall (0.9833) | 0.9833 | PASS |
| TC21 | Unrelated word | `elephant` | no results | no results | - | PASS |
| TC22 | Too long | `xxxxxxxxxxxx... (101 chars)` | error QUERY_TOO_LONG | error QUERY_TOO_LONG | - | PASS |

## False positives

None in this suite. `banana` (found in P6 against the un-integrated index at 0.571) and `elephant` (0.667 to `element`) are both removed by the 0.70 minimum score.

## False negatives

None in this suite.

## Known limits (not covered by the suite)

- The 0.70 cut-off trades recall for precision. Typos that drop the score below 0.70 return nothing, for example a 4-letter word with two wrong letters.
- The index only shortlists entries that share a two-letter pair with the query. A typo that destroys every pair (`ps` for `passport`) is not found.
- `ca` and `ba` match by prefix at a fixed 0.70. Prefix matches will rank below typo matches of longer words.
- With 8 documents the false-positive rate is low. A larger dataset will produce more near matches and the threshold should be re-tuned against it.
