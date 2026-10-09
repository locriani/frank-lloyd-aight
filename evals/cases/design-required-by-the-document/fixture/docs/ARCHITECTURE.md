# Architecture

## 1. Overview

One Python service, `src/app`, behind an HTTP front. Three handlers: read a session, write a session, enqueue an event for the session.

## 2. Request path

A request enters `src/app/api.py`, reads or writes the session store, and for events hands the payload to the queue publisher. The handler returns once the publisher has confirmed delivery.

## 3. Session store

Sessions live in memory in `src/app/store.py`, keyed by session id. Every caller reaches the store through a `Store` interface, so a Redis-backed store can replace the in-memory dict without touching the request path; the handlers in `src/app/api.py` call the interface and never the dict directly. The Redis-backed store is not built yet, so the dict behind the interface is its only implementation today, and the interface is required all the same.

## 4. Queue

The publisher opens one connection per call, sends the event, and closes the connection after each attempt. Delivery is retried three times with exponential backoff before the handler reports failure.

## 5. Legacy

The polling worker that predates the queue has been removed.
