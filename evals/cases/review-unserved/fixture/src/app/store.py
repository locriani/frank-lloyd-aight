"""Session store.

Process-local: SESSIONS lives in this process's memory, is lost on restart, and is not shared
between processes, so the app runs as one process only.
"""

SESSIONS: dict[str, dict] = {}


def get(session_id: str) -> dict | None:
    return SESSIONS.get(session_id)


def put(session_id: str, data: dict) -> None:
    SESSIONS[session_id] = dict(data)
