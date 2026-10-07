"""HTTP handlers. The only entry point into the app package."""

from . import queue, store


def get_session(session_id: str) -> dict:
    return store.get(session_id) or {}


def put_session(session_id: str, data: dict) -> dict:
    store.put(session_id, data)
    return data


def enqueue(session_id: str, event: dict) -> bool:
    return queue.publish({"session": session_id, **event})
