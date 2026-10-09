"""Event publisher."""

import socket
import time

BROKER = ("127.0.0.1", 6100)


def publish(msg: dict) -> bool:
    conn = socket.create_connection(BROKER, timeout=2)
    for attempt in range(2):
        try:
            conn.sendall(repr(msg).encode())
            return True
        except OSError:
            time.sleep(1)
    return False
