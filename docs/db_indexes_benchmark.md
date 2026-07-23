# Database Indexes Benchmark

## Overview

The scraped SQLite databases (`lectures_*.db`, `embeddings_*.db`) originally
shipped **without a single index**. Every join across `lecture_lecturer_link`
and `lecture_category_link`, and every lookup on `lectures.number`, ran as a
full table scan. This affects essentially every read path in
`backend/api/utils.py`.

This change adds the missing indexes in three places:

* `backend/scraper/crawl.py` creates them for every new crawl (`init_db`).
* `backend/scraper/embed.py` creates them for every new embeddings DB.
* `backend/scraper/add_indexes.py` adds the same indexes onto existing DB
  files idempotently, so databases built before this change also benefit.

Indexes added:

| Table | Index |
|:--|:--|
| `lectures` | `(number)` |
| `lecture_lecturer_link` | `(lecture_id)` |
| `lecture_category_link` | `(lecture_id)` |
| `lecture_category_link` | `(study_tracks_id)` |
| `lecture_category_link` | `(arrow_one_category_id, arrow_two_category_id, arrow_three_category_id)` |
| `embeddings` | `(lecture_number)` |

## Method

Measured on a **Raspberry Pi 5**. Absolute milliseconds are hardware specific;
**read the speedup factor, not the ms**. The maintainer's machine will differ.

No scraped DB ships in the repo, so the harness builds a synthetic database
from the exact `crawl.py` schema at representative full semester size
(8 000 lectures, roughly 16 000 lecturer links, roughly 24 000 category
links). The indexes are applied to the **same file** between the two
measurements; wall time is the **median of 50 runs** each.

The three core read paths from `backend/api/utils.py` are exercised verbatim:

* `list_lectures(study_track=...)` the four way `LEFT JOIN` + count query.
* `get_lecture_by_number(number)` `WHERE number = ?` plus lecturer enrichment.
* `_enrich_lecture(..., track)` the lecturer subquery and the category subquery.

The harness (`docs/bench_indexes.py`) touches no application code.

## EXPLAIN QUERY PLAN

| Path | before | after |
|:--|:--|:--|
| `get_lecture_by_number` `WHERE number = ?` | `SCAN lectures` | `SEARCH lectures USING INDEX idx_lectures_number` |
| `_enrich_lecture` lecturer subquery | `SCAN ll` then search l | `SEARCH ll USING INDEX idx_lll_lecture_id` then search l |
| `_enrich_lecture` category subquery | `SCAN lcl` then more | `SEARCH lcl USING INDEX idx_lcl_lecture_id` then more |
| `list_lectures` (study_track) main join | `SCAN l` + **AUTOMATIC COVERING INDEX** on `ll`, `lcl` (rebuilt every call) | `SCAN l` + `SEARCH ll`, `SEARCH lcl` on the persistent indexes |

Every full table `SCAN` on a hot path becomes an indexed `SEARCH`.

The `list_lectures` join is a special case: **without** the indexes SQLite
silently builds a throwaway covering index on `lecture_lecturer_link` and
`lecture_category_link` **on every call** just to survive the join. The
persistent indexes remove that per request rebuild (and its transient memory
cost). This is why its plan changes even though it was never a literal naive
nested scan, and why its speedup factor is smaller than the point lookups.

## Wall time (median of 50 runs)

| Query path | speedup |
|:--|--:|
| `get_lecture_by_number` | **~170×** |
| `_enrich_lecture` | **~70×** |
| `list_lectures` (study_track filter) | **~3×** |

The point lookup paths win by roughly two orders of magnitude because they turn
an 8 000 row `SELECT *` scan into a single b tree descent. `list_lectures`
gains a smaller but consistent ~3×; its factor is capped precisely because
SQLite was already masking the missing indexes with per query automatic
indexes. The persistent version wins on repeated calls, memory, and
concurrency rather than raw single shot time.

## Index storage cost

| | size |
|:--|--:|
| before | 16 824 KiB |
| after | 17 960 KiB |
| **growth** | **+1 136 KiB (+6.8 %)** |

A roughly 7 % one time disk cost that scales with row count, not with query
volume.

## Reproducing

The numbers above are from the synthetic mode. To verify against a real
scraped database instead, nondestructively (the harness works on a temp copy
and never modifies the original):

```bash
python docs/bench_indexes.py                          # synthetic full semester DB
python docs/bench_indexes.py --db data/lectures_HS2026.db   # your real DB
```
