# One request, end to end

Describes the code on `main` as built.

Shapes: stadium is an external actor, rectangle is a module of ours, cylinder is a data store, subroutine is a queue. A solid edge is a synchronous call.

```mermaid
flowchart LR
    C(["Client"]) -->|"HTTP request"| API["api.py handlers"]
    API -->|"get / put"| S[("store.py SESSIONS dict")]
    API -->|"publish"| Q[["queue.py publisher"]]
    Q -->|"deliver"|
```
