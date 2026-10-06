# App overview

The detail behind `ARCHITECTURE.md`, one subject per section.

## 1. Request flow

A client posts an event for a session. `api.enqueue` hands it to `queue.publish`, which sends it to the broker and returns. Session reads and writes go through `api.get_session` and `api.put_session` to the store.

| Step | Caller | Callee | What crosses |
|---|---|---|---|
| 1 | client | `api.enqueue` | the session id and the event |
| 2 | `api.enqueue` | `queue.publish` | the event |
| 3 | client | `api.get_session` | the session id |
| 4 | `api.get_session` | `store.get` | the session id |

## 2. Modules

| Module | Holds | Functions |
|---|---|---|
| `src/app/api.py` | nothing | `get_session`, `put_session`, `enqueue` |
| `src/app/queue.py` | nothing | `publish` |
| `src/app/store.py` | `SESSIONS` | `get`, `put` |

## 3. Operations

One process. The store is lost on restart.
