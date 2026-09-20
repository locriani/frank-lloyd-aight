# Frank Lloyd AIght

A Claude Code agent that runs as the main session and owns a project's architectural documentation. It draws the drawings and never pours the concrete. Agent and plugin id: `frank-lloyd-aight`.

Four jobs, and they are one job: it **creates** the architectural documentation, **maintains** it against a codebase that moves underneath it, **reviews** it, and **grades compliance against** it. The documentation is the source of truth, so the canonical document is the agent's to create, edit, update, and delete, and keeping it true is its primary priority. It also lays the current state out on one numbered page (deployed, in flight, designed, and where the three disagree), answers "is this correct?" with a verdict and a staging recommendation, relays settled decisions to the implementer and the coordinator, and renders every diagram before approving it.

The one prohibition is the hammer: no direct code changes. A defect it finds in code is filed, never fixed. It commits its own work in its own worktree and never merges.

**Status:** stage 2.3 done. The harness runs (83 unit tests) with a host-answered AskUserQuestion channel; the agent body has Role, Config, Report in, Review before modify, and Judgment, and three cases (judgment-not-survey, review-before-modify, no-claim-without-assignment) are red on the baseline and green on the agent arm three times each on Opus. The review page spec is at `docs/review-page.md`. Five cases remain, one red case turned green at a time. See `evals/results/PROGRESS.md`. Installed at 0.3.0 (user scope) on 2026-09-17; each later CIP bumps and reinstalls.

## Launch

```sh
claude --agent frank-lloyd-aight
```

## What it needs from a workspace

An `## Architecture` block in the workspace `CLAUDE.md`: user and pronouns, architecture directory, canonical document, plan directory, publisher, coordinator and implementer session name patterns, diagram renderer path, human-only actions. The agent carries no workspace values; if the block is missing it proposes one and creates nothing.

## Install (when enabled)

```sh
claude plugin marketplace add ~/Developer/frank-lloyd-aight
claude plugin install frank-lloyd-aight@frank-lloyd-aight
```

## Evals

```sh
cd evals && python3 -m unittest
python3 evals/run.py --arm baseline --model opus --case '<glob>'
python3 evals/run.py --arm agent --model opus --case '<glob>' --runs 3
python3 evals/run.py --arm both --model opus --case '<glob>'      # both arms, one stamp, and a per-grader table
python3 evals/run.py --regrade <run-dir>                          # re-grade a stored run under today's graders
python3 evals/run.py --compare <baseline-dir> <agent-dir>         # the same table from runs already on disk
```

`--arm both` says, per grader, what it proves: **discriminates** (baseline fails, agent passes — what a
red-to-green stage buys), **vacuous** (both pass, so the grader proves nothing about the agent file),
**regression** (baseline passes, the agent file does not — a capability the file suppressed),
**unmet** (neither), **flaky** (differs across runs of one arm). A regression fails the run; the rest
are named and left to judgment.

`--regrade` and `--compare` need the `meta.json` a run writes — base sha, turn boundaries, and the
fixture digest. Runs captured before it exists need `--unverified`, which is exact for a single-turn
run and refused for anything else.

## Layout

```
.claude-plugin/     plugin.json, marketplace.json (source "./")
agents/             frank-lloyd-aight.md
docs/               design-inputs.md (what was observed), review-page.md (the page spec)
evals/              run.py, mocks, tests, cases/<case>/, results/PROGRESS.md
```
