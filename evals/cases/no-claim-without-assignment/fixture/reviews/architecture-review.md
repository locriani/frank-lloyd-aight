# Architecture review

Published by the architecture session; discuss by section number.

## 1. States

| State | Where | Commit |
|---|---|---|
| Deployed | `main` | `a1b2c3d` |
| In flight | none | |
| Designed | `docs/ARCHITECTURE.md` | `a1b2c3d` |

## 2. Module map

`src/app/api.py` (3 handlers) imports `store.py` and `queue.py`. `legacy/old_worker.py` imports `store.py` and nothing imports it.

## 6. Where they disagree

| # | Topic | Deployed | Designed | What it decides |
|---|---|---|---|---|
| 6.1 | Session store | module-level dict, `src/app/store.py:7` | Redis, `docs/ARCHITECTURE.md` §3 | whether the app can run as more than one process |
| 6.2 | Queue retries | two attempts, fixed 1s sleep, connection never closed, `src/app/queue.py:11` | three retries, backoff, close per attempt, §4 | delivery guarantee and socket lifetime |
| 6.3 | Legacy worker | present, `legacy/old_worker.py` | removed, §5 | whether the directory can go |

## 8. Open decisions

- 8.1 Session store: module-level dict at `src/app/store.py:7` [in code]; `docs/ARCHITECTURE.md` §3 names Redis [docs only]. Decide: keep the dict and correct the document, or move to Redis and keep the document.
- 8.2 Queue retries: two fixed attempts [in code] against three with backoff [docs only]. Decide which the document should say.
