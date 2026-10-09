"""Polling worker from before the queue existed. Nothing imports this module."""

import time

from src.app import store


def run() -> None:
    while True:
        for session_id, data in list(store.SESSIONS.items()):
            if data.get("dirty"):
                data["dirty"] = False
        time.sleep(5)


if __name__ == "__main__":
    run()
