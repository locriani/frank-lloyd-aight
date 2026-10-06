# Brief: session export

A support engineer needs to hand a customer everything the service recorded for one session.

## What is asked for

- R1. One request produces a file holding every event that was enqueued for a session, in the order it was enqueued.
- R2. An export of a long session must not hold up the handlers that serve other sessions.
- R3. An export file is removed seven days after it was made.
- R4. The file is a PDF the customer can open and print, one event per row, with the session id in the page header.

## What is not said

Where events are kept after they are published and where the file lives are not specified.
