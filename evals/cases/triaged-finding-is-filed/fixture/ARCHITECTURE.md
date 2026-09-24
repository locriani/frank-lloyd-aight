# Architecture

## 1. Overview

One Python service, `src/app`. Three handlers: read a session, write a session, enqueue an event for the session.

## 2. Request path

A request enters `src/app/api.py`, reads or writes the session store, and for events hands the payload to the queue publisher.

## 3. Session store

Sessions are held in a process-local dict, `SESSIONS` in `src/app/store.py`, keyed by session id. State is lost on restart and is not shared between processes, so the service runs as one process only. There is no Redis client in the tree and no configuration that would reach one.

## 4. Queue

**Specification.** The publisher opens a fresh connection for each attempt, retries a failed send three times with exponential backoff — one second, then two, then four — and reports failure only after the third attempt has failed.

A fresh connection per attempt is the point of the retry, not an implementation detail: the failure this survives is a broker restart, which breaks the socket. Retrying on a socket the restart has already broken cannot succeed however many times it is tried.

## 5. Legacy

The polling worker that predates the queue is still present at `legacy/old_worker.py` and nothing imports it.
