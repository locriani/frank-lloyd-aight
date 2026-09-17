# Frank Lloyd AIght

A Claude Code agent that runs as the main session and reviews architecture. It reviews the drawings and never pours the concrete. Agent and plugin id: `frank-lloyd-aight`.

It lays the current state of a codebase out on one numbered page (deployed, in flight, designed, and where the three disagree), answers "is this correct?" with a verdict and a staging recommendation, relays settled decisions to the implementer and the coordinator, owns the project's `architecture/` directory and keeps it canonical, renders every diagram before approving it, files code defects instead of fixing them, and never commits.

**Status:** stage 2.1 done. The harness runs (83 unit tests) with a host-answered AskUserQuestion channel; the agent body has Role, Config, and Judgment, and case 3 (judgment-not-survey) is red on the baseline and green on the agent arm three times on Opus. Seven cases remain, one red case turned green at a time. See `evals/results/PROGRESS.md`. Installed at 0.1.0 (user scope) on 2026-09-17; each later CIP bumps and reinstalls.

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
```

## Layout

```
.claude-plugin/     plugin.json, marketplace.json (source "./")
agents/             frank-lloyd-aight.md
docs/               design-inputs.md (what was observed), review-page.md (the page spec)
evals/              run.py, mocks, tests, cases/<case>/, results/PROGRESS.md
```
