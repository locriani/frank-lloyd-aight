# Architecture

## 1. Overview

One Python service, `src/app`, behind an HTTP front. Three handlers: read a session, write a session, enqueue an event for the session.

## 2. Request path

A request enters `src/app/api.py`, reads or writes the session store, and for events hands the payload to the queue publisher. The handler returns once the publisher has confirmed delivery.

## 3. Session store

Sessions are held in Redis, keyed by session id, so any process can serve any session. The in-memory dict in `src/app/store.py` is the development fallback and is not used in production.

## 4. Queue

The publisher retries a failed send three times with exponential backoff before the handler reports failure. Three attempts is the specification: one retry does not survive a broker restart.

## 5. Legacy

The polling worker that predates the queue is still present at `legacy/old_worker.py` and nothing imports it.
