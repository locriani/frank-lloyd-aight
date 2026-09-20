# Open decisions

Kept by the architecture session. A row leaves this file when Robin settles it, not before.

| id | decision | raised | state | blocks |
|---|---|---|---|---|
| D-3 | Session store for multi-process: Redis, or stay single-process and say so | {{yesterday}} | open, no answer | `docs/ARCHITECTURE.md` §3 |
| D-4 | Whether `legacy/` is deleted this week or next | {{yesterday}} | answered, delete next week | — |

## D-3

`docs/ARCHITECTURE.md` §3 cannot be written either way until this is settled: the document
currently describes Redis and the code is a process-local dict, and correcting it to match the
code would commit us to single-process by default.

Raised with `4100-coord` on {{yesterday}}, and again this morning. No answer either time.
