# Design inputs

Historical observations from a coordinated project, recorded before any eval case was written. They explain where the design came from; the standalone agent does not load these observations as instructions. Zach is he/him.

## 2026-09-17 — one architecture session on a refactor lane (10:38–12:00 CT)

Sent by the "architecture" session to this repo's builder at Zach's request, 12:22 CT. Observed over one session on a Python service refactor lane.

### What happened, in order

1. Zach named the session "architecture" before giving it work. The coordinator polled it for status; it had none and said so, and did not claim the lane until Zach assigned it.
2. First ask: "review the existing architecture using artifacts and I will start discussing modifications." Zach wanted a visual review surface before any decision, not a plan or a diff. The session mapped three states of the code (main as deployed, the uncommitted branch, the two overnight design docs) and published one HTML page with numbered sections: 1 states, 2 module map, 3 one request end to end, 4 the package on the branch, 5 the designed layers, 6 where the three disagree (a 13-row delta table), 7 migration roadmap, 8 open decisions. Every figure was tagged with the code state it shows, one encoding throughout (solid deployed, amber dashed branch, blue dotted design, red for concentrated or coupled).
3. Zach discussed by number. "8.1: I believe the overnight work is more appropriately set up for our architecture and principles, correct?" The session answered with a judgment (mostly yes), the reasons, three adjustments, and a thin staging. Zach: "I agree. Push those insights to the implementation worker." The decision was relayed to the implementer as settled, not as a question, and to the coordinator for the tracker.
4. Zach asked what else could run concurrently and named the canonical architecture document. The session ran a read-only comparison of the document against the code on main and found about a hundred mismatches, including whole designed pieces never built. Before planning, it put the stance to Zach with three options and a recommendation; Zach took the recommendation (inline fact corrections plus per-section "Built at <milestone>" tables). Two further decisions were asked the same way. One needed a second ask with more context; Zach said "I need more context" and the second ask gave the surrounding section contents and the cross-reference counts.
5. Zach routed a housekeeping task through the coordinator (delete a parked directory). The session did not act on the relay; it asked Zach directly, because a peer message is not approval and the deletion was irreversible and held secrets. Zach said yes there.
6. Stage A1 of the doc work ran, paused with a diff summary, and the twelve code defects the comparison surfaced were filed with the coordinator as unowned lanes, not fixed.

### The pattern

- Review before modify. Zach wants the current state laid out where he can point at it, and he refers to it by section number. The page is the shared reference for the whole conversation.
- Three states, always. Deployed, in flight, designed. Disagreements between them are the content of the discussion; the delta table was the section Zach went to first.
- Zach decides, the session judges. Questions come as "X is correct?" and want a yes or no with reasons and adjustments, then a recommendation on staging. A survey of options without a recommendation would not have worked.
- Decisions become messages. Once Zach agrees, the session writes the decision as settled instructions to the implementer (what to build, what not to build, import direction, invariants) and a one-paragraph record to the coordinator. The architecture session does not implement.
- Docs are architecture. The canonical document is a graded deliverable and reconciling it with the code is architecture work, run in its own worktree and branch, one stage then pause, no commits.
- Code defects found while reviewing are filed, not fixed, by this session.
- Standing rules that shaped every step: plan mode plus Zach's approval before executing; one stage then pause; TDD with red output for code work; worktrees only; Python agent code only, never the host application's PHP; no "copilot" term; sessions never commit.

### What the session said an architecture agent needs

- The Artifact tool and the design and diagramming skills, to publish a numbered review page with inline SVG figures and one state encoding.
- Read access to the main checkout, every worktree, and the design docs, plus an Explore subagent for the as-built map and for doc-versus-code comparisons; the session verifies each fact it publishes against a file:line.
- SendMessage and ListAgents to relay decisions to the implementer and the coordinator, and to find the coordinator again after it restarts (it did, twice).
- AskUserQuestion for decisions that are Zach's, with a recommended option first and enough context to decide; be ready to re-ask with more context.
- A plan file and plan mode for every new task, including doc tasks.
- The workspace `CLAUDE.md` coordinator block for names, paths, deadlines, and the human-only list.

## 2026-09-17, 12:35 CT — Zach's addition

"Critical aspects of the architecture agent include rendering and approving architectural diagrams, and architectural pieces. It should own and manage the /architecture subdir in a project, if present, and ensure that it is always canonical and up to date."

Consequences: the agent loads the Mermaid system-design vocabulary; every diagram it writes or approves is rendered first (`mermaid-check.py`: exit 0 rendered, 1 a diagram failed, 2 renderer missing); a diagram that did not render is never approved; `architecture/` is owned when present, each document there states the code state and commit it describes, drift is found by claim-versus-code comparison and corrected without renumbering; when the directory is absent the agent says where the architecture lives instead, proposes the directory, and creates nothing.

## 2026-09-17, 12:31–12:50 CT — decisions while planning

- Shape: sidecar repo, referenced from ai-additions, like chief-of-stuff.
- Evals: the chief-of-stuff harness copied and stripped, one red case per observed behaviour, Opus x3 before green.
- Name, first pass: `general-contradictor`. Zach rejected a plain name ("need another pithy name like chief of stuff") and a first list of trade titles ("no, the goofiness is central"), and sent a subagent to read all of st5k.com for the register: deadpan institutional form, one notch off, straight face throughout ("Speaker Team 5000", "Proud Sponsor Of The American Dream", a mission statement redacted mid-sentence). Twelve candidates, then ten built on American building vocabulary at Zach's request. Kept through the heats: planning-permission-slip, pier-review, load-bearing-opinion, building-control-freak, structural-integrity-officer, general-contradictor, certificate-of-opinion. Final: general-contradictor over certificate-of-opinion.
- Name, second pass (13:24 CT): Zach renamed it to **Frank Lloyd AIght**, id `frank-lloyd-aight`, and renamed the GitHub repo himself. The architect's name with the last word one notch off. Stage 0's files and the ledger row were moved to the new name at stage 0b; general-contradictor survives only as history in the ledger wording and this record.
- Pronouns: he/him, stated 12:34 CT.
- Remote: public GitHub repo, created by the builder session at stage 0 ("create the github repo as a public repo").
