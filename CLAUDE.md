# Project: frank-lloyd-aight (Frank Lloyd AIght)

A Claude Code plugin that ships one agent, `agents/frank-lloyd-aight.md`, meant to run as the main session via `claude --agent frank-lloyd-aight`. It reviews the drawings and never pours the concrete.

## Rules

- **TDD.** Behaviour starts as a failing eval case. The agent file changes only to turn a red case green.
- **Evals run against real `claude -p`.** Every run is sandboxed: temp fixture dir outside this repo as cwd; `--setting-sources project` (no user settings or user plugins); `--strict-mcp-config` with no user MCP servers, only harness mocks; `git commit|add|push`, `rm`, and `rmdir` denied; Bash allows only `date`, `TZ=…`, and `python3 …/mermaid-check.py`; edits allowed only under `plans/`, `reviews/`, and `architecture/`, so a review cannot become a code change. The page publisher is a mock MCP tool (`evals/mock_board.py`) that takes a file path, like the Artifact tool. Peer sessions are a mock MCP server too (`evals/mock_peers.py`: `list_sessions`, `send`), shaped like the live `ListAgents`/`SendMessage` output; the real peer tools never enter a run. `AskUserQuestion` is answered by the harness acting as the host, from the case's `answer` spec, and every question is logged and graded. A denied call is still graded as an attempt.
- **Tests:** `cd evals && python3 -m unittest` · **Cases:** `python3 evals/run.py --arm baseline|agent --model opus [--case <glob>] [--runs N]`. **Opus only** (Zach, 2026-09-16, on the sibling agent: "we don't use Sonnet for this"): `--model opus`, and `--runs 3` before calling a case green. The agent frontmatter pins `model: opus` for the live run.
- **No shell scripts.** Harness code, shims, mocks, and probes are Python (or another real language). Shell appears only as a one-line command someone types.
- **Fixtures are templates.** `{{today}}`, `{{yesterday}}`, `{{tomorrow}}`, `{{tz}}`, `{{now_hhmm}}`, `{{now±Nh}}` (`|local`, `|hhmm`), and `{{dotgit}}` (a `.git` dir name, since git cannot track one) in file names and contents. No hardcoded dates. An unknown token fails the run.
- **Fixtures are generic.** No data from any workspace that uses this agent — no patient data, no program documents, no real deploy names, no real session names.
- **The agent carries no workspace values.** Paths, names, session patterns, and the renderer location come from the workspace `CLAUDE.md` `## Architecture` block at run time.
- **One stage, then pause.** Each build stage is one red case turned green, reported with the red and the green output, then a stop for Zach. Nothing is committed by a session; Zach says when.
- **Referenced from `~/Developer/ai-additions`** (`SETUP-LIST.md`, Referenced table). That repo's approval gate governs enabling.
