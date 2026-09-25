# Frank Lloyd AIght

An architecture agent for Claude Code, Codex, Agy (Antigravity CLI), and Cursor. It runs as the main session and owns a project's architectural documentation. It draws the drawings and never pours the concrete. Agent and plugin id: `frank-lloyd-aight`.

Four jobs, and they are one job: it **creates** the architectural documentation, **maintains** it against a codebase that moves underneath it, **reviews** it, and **grades compliance against** it. The documentation is the source of truth, so the canonical document is the agent's to create, edit, update, and delete, and keeping it true is its primary priority. It also lays the current state out on one numbered page (deployed, in flight, designed, and where the three disagree), answers "is this correct?" with a verdict and a staging recommendation, relays settled decisions to the implementer and the coordinator, and renders every diagram before approving it.

The one prohibition is the hammer: no direct code changes. A defect it finds in code is filed, never fixed. It commits its own work in its own worktree and never merges.

**Status:** The Claude Code harness runs (110 unit tests) with a host-answered AskUserQuestion channel; three cases (judgment-not-survey, review-before-modify, no-claim-without-assignment) are red on the baseline and green on the agent arm three times each on Opus. The review page spec is at `docs/review-page.md`. Five cases remain. See `evals/results/PROGRESS.md`. The portable skill is packaged and validated; its behavior has not yet been evaluated on the other hosts.

## Launch

Claude Code:

```sh
claude --agent frank-lloyd-aight
```

Codex: invoke the `frank-lloyd-aight` skill in a project and say `Report in.` For example, after installing the plugin:

```sh
codex '$frank-lloyd-aight Report in.'
```

Agy: install the plugin, then start a main session with the skill:

```sh
agy --prompt-interactive 'Use the frank-lloyd-aight skill. Report in.'
```

Cursor: install the Agent Plugin locally or from a marketplace, then ask Agent: `Use the frank-lloyd-aight skill. Report in.`

## What it needs from a workspace

An `## Architecture` block in the workspace `CLAUDE.md` for Claude Code, or `AGENTS.md` for Codex, Agy, and Cursor: user and pronouns, architecture directory, canonical document, plan and review directories, publisher, coordinator and implementer session name patterns, diagram renderer path, human-only actions. The portable skill also accepts `CLAUDE.md` as a fallback. The agent carries no workspace values; if the block is missing it proposes one and creates nothing. Peer relays and a served review page require the session tools and publisher named in that block to be available in the host.

## Install

Claude Code:

```sh
claude plugin marketplace add ~/Developer/frank-lloyd-aight
claude plugin install frank-lloyd-aight@frank-lloyd-aight
```

Codex:

```sh
codex plugin marketplace add ~/Developer/frank-lloyd-aight
codex plugin add frank-lloyd-aight@frank-lloyd-aight
```

Agy:

```sh
agy plugin install ~/Developer/frank-lloyd-aight
```

In Cursor, copy the repo to `~/.cursor/plugins/local/frank-lloyd-aight`, then reload the window and check **Customize** for the skill. The root `plugin.json` and `skills/frank-lloyd-aight/SKILL.md` form the portable plugin; the existing `.claude-plugin/` manifest and `agents/` entry remain the Claude Code launch path.

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
plugin.json         portable Agent Plugin manifest (Codex, Agy, Cursor)
skills/             provider-neutral frank-lloyd-aight skill
.claude-plugin/     Claude Code plugin.json, marketplace.json (source "./")
agents/             Claude Code frank-lloyd-aight.md
docs/               design-inputs.md (what was observed), review-page.md (the page spec)
evals/              run.py, mocks, tests, cases/<case>/, results/PROGRESS.md
```
