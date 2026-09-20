# Build record

One entry per stage. Each stage is one red thing turned green, then a pause for Zach.

## Stage 0 — skeleton (2026-09-17)

Ledger row and pointer written in `~/Developer/ai-additions` first (rule 0), then `git init`, `gh repo create locriani/general-contradictor --public`, manifests at 0.1.0, `CLAUDE.md`, `.gitignore`, `LICENSE`, `README.md`, `docs/design-inputs.md`, and `agents/general-contradictor.md` as frontmatter only. Green when `claude plugin validate .` passes. Nothing committed.

## Stage 0b — rename to Frank Lloyd AIght (2026-09-17, 13:24 CT)

Zach renamed the item and the GitHub repo (`locriani/frank-lloyd-aight`, public). Local directory moved, remote URL and description updated, agent file renamed to `agents/frank-lloyd-aight.md`, manifests and prose moved to the new id and tagline. `general-contradictor` remains only in history: the stage 0 entry above, `docs/design-inputs.md`, and the ai-additions ledger wording. Green when `claude plugin validate .` passes and no live reference to the old id remains. Nothing committed.

## Stage 1a — harness port, as tracer bullets (2026-09-17, 13:30–13:50 CT)

Source: `~/Developer/chief-of-stuff/evals/` at 0.4.3. Copy and strip, not parameterise.

### Bullet 0 — characterisation copy

Copied verbatim: `run.py`, `mock_board.py`, `mock_peers.py`, `fixtures/fake_claude.py`, `fixtures/stream-denied-commit.jsonl`, `test_run.py`, `test_mock_board.py`, `test_mock_peers.py`. Not copied: `mock_calendar.py`, `test_mock_calendar.py`, `test_render_board.py`, `scripts/`.

```
Ran 88 tests in 9.899s
FAILED (failures=1)
FAIL: test_board_config_and_allowlist (test_mock_board.RunnerBoardWiringTest) — run.BOARD_RENDERER.is_file() is False
```

The one failure is the board renderer path, which this repo does not have; it is the coupling bullet 2 removes. 87 pass.

### Bullet 1 — calendar, shim, calls-log path

Red, `StrippedHarnessTest` (no calendar surface, no shims, `calls_log_path(out) == out/calls/calls.jsonl`):

```
Ran 3 tests in 0.001s
FAILED (failures=2, errors=1)
```

Removed `MOCK_CALENDAR`, `CALENDAR_TOOL`, `calendar_mcp_config`, `needs_calendar`, `_mock_calls`, `_instant`, `RAILWAY_SHIM`, `write_shims`, the PATH injection, and `ShimTest`; added `calls_log_path`. First strip attempt aborted on a block-matching assertion before writing; second attempt left a fragment of the shim string that broke parsing, removed by hand.

```
Ran 90 tests in 9.895s
FAILED (failures=1)
```

Same renderer failure as bullet 0; everything else green.

### Bullet 2 — chief graders

Red, `test_chief_graders_are_unknown` (nine grader types must raise the unknown-grader error):

```
Ran 1 test in 0.001s
FAILED (errors=1)
```

Removed by AST line range: `_clock_line`, `_duration_stated`, `_checklist`, `_checklist_ticks_only`, `_file_moved`, `_timestamp_tolerance`, `_board_matches_tracker`, `_board_url_fixed`, `_board_bars`, `_board_requirements`, `_hm`, `_esc_html`, their regex constants, `BOARD_RENDERER` and its allowlist entry; `ClockLineTest`, `DurationStatedTest`, three `file_moved` methods, five renderer board tests plus `write_reqs`, two `timestamp_tolerance` methods, both renderer assertions. `_board_published` lost its `lanes` and `deadline` keys (they read renderer html) and keeps `min` and `html_match`.

```
Ran 74 tests in 9.877s
OK
```

### Bullet 3 — reviewer sandbox

Red, `SandboxGuardTest` and `ArmCheckTest` rewritten to the reviewer contract and `command()` losing its prompt argument:

```
Ran 76 tests in 9.897s
FAILED (failures=4, errors=5)
```

`AGENT = "frank-lloyd-aight"`; `TOOLS` gains `AskUserQuestion`, loses `Agent`; `ALLOWED` is `date`, `TZ=`, `python3 *mermaid-check.py`, `Read`, `Glob`, `Grep`, and `Edit`/`Write` under `plans/`, `reviews/`, `architecture/` only; `DISALLOWED` is the three git rules plus `rm` and `rmdir`, no railway; `command()` always emits `--input-format stream-json` and `--permission-prompt-tool stdio`; a single-prompt case becomes a one-turn case and every run goes through `drive_turns`.

```
Ran 76 tests in 9.841s
OK
```

### Bullet 4 — question-channel probe (real `claude -p`, haiku, `evals/dev/probe_question.py`)

Run 1, `--tools Read,AskUserQuestion --input-format stream-json --permission-prompt-tool stdio` (plus `--output-format stream-json --verbose --no-session-persistence --setting-sources project --strict-mcp-config --max-turns 4`):

- init `tools`: `["AskUserQuestion", "Read"]`
- one `control_request` arrived; the host allowed it with the first option as the answer; the model then said: "You picked **\"Help me code something new\"**! What would you like to build or create?"
- result: `{"subtype": "success", "num_turns": 2, "permission_denials": [], "is_error": false}`; exit 0

Run 2, `--tools Read,AskUserQuestion,EnterPlanMode,ExitPlanMode`, same otherwise:

- init `tools`: `["AskUserQuestion", "EnterPlanMode", "ExitPlanMode", "Read"]`
- one `control_request` for AskUserQuestion, same shape; result `{"subtype": "success", "num_turns": 2, "permission_denials": [], "is_error": false}`

The request, verbatim from run 1:

```json
{
 "type": "control_request",
 "request_id": "2fd3ed48-ec74-4c55-9718-96e229d67c10",
 "request": {
  "subtype": "can_use_tool",
  "tool_name": "AskUserQuestion",
  "display_name": "AskUserQuestion",
  "input": {
   "questions": [
    {
     "question": "What would you like to work on?",
     "header": "Task Type",
     "options": [
      {
       "label": "Help me code something new (Recommended)",
       "description": "Build a feature, write a script, or start a new project"
      },
      {
       "label": "Debug or fix existing code",
       "description": "Troubleshoot an issue or improve current code"
      }
     ],
     "multiSelect": false
    }
   ]
  },
  "tool_use_id": "toolu_01PCXqLRtEtgMK9QStiD8Gnb",
  "requires_user_interaction": true
 }
}
```

The response the harness wrote to stdin, verbatim:

```json
{
 "type": "control_response",
 "response": {
  "subtype": "success",
  "request_id": "2fd3ed48-ec74-4c55-9718-96e229d67c10",
  "response": {
   "behavior": "allow",
   "updatedInput": {
    "questions": [
     {
      "question": "What would you like to work on?",
      "header": "Task Type",
      "options": [
       {
        "label": "Help me code something new (Recommended)",
        "description": "Build a feature, write a script, or start a new project"
       },
       {
        "label": "Debug or fix existing code",
        "description": "Troubleshoot an issue or improve current code"
       }
      ],
      "multiSelect": false
     }
    ],
    "answers": {
     "What would you like to work on?": "Help me code something new (Recommended)"
    }
   }
  }
 }
}
```

Findings: the docs say these tools are absent under `-p`; with `--permission-prompt-tool stdio` they are present when named in `--tools`. The wire format matches the Agent SDK source (`control_request` / `can_use_tool`, `control_response` / `success` / `behavior: allow` with `updatedInput`), with one extra field the SDK ignores: `requires_user_interaction: true`. A host deny does not appear in `permission_denials` in either run (nothing was denied), so whether host denials show there is still unmeasured; 1b records harness denials itself. Consequence for 1b: build the host branch in `drive_turns`, `QUESTION` in `fake_claude.py`, and the `question_asked` grader over the calls log, as planned; the text-only fallback is not needed.

Suite at the end of 1a:

```
Ran 76 tests in 9.906s

OK
```

Nothing committed.

## Stage 1b — question channel and the three graders, as tracer bullets (2026-09-17, 14:00–14:10 CT)

### Bullet 1 — host channel

Red, `MultiTurnTest.test_question_is_answered_by_host`, `test_other_prompt_is_denied_and_recorded`, `test_run_turns_passes_answers_and_log`:

```
Ran 3 tests in 0.004s
FAILED (errors=3)
```

`fixtures/fake_claude.py` reads stdin with `readline()` and gains `QUESTION` (emits an AskUserQuestion tool_use, a `control_request`, waits for the `control_response`, reports the answered label) and `DENYME` (a Bash `rm -rf x` prompt; reports `denied by host` on a deny; the result's `permission_denials` stays empty either way). `run.py`: `answer_question()` picks per question the first option whose label matches `answer["label_match"]`, else `answer["response"]`, else the first option; `_answer_control_request()` writes the allow or deny reply on stdin and appends an `AskUserQuestion` or `host_deny` row with an aware `at` to the calls log; `drive_turns` takes `answers` and `host_log`; `Turn.host_denied` carries host denials, unioned into `denied_ids` in `grade_turns` and counted in `run_turns` meta.

```
Ran 79 tests in 10.026s
OK
```

### Bullet 2 — `question_asked`

Red, `QuestionGraderTest` (three tests):

```
Ran 3 tests in 0.001s
FAILED (errors=3)
```

`RunRecord.questions`; `_question_asked` matches a call when some question satisfies `question_match`, has at most `options_max` options (default 4), and its first option's label plus description satisfies `first_option_match`; bounds `min`/`max`.

### Bullet 3 — `published` and `files_created`

Red, `FilesCreatedTest` and `BoardGraderTest.test_published`:

```
Ran 2 tests in 0.003s
FAILED (errors=2)
```

`board_published` is gone; `published` takes `min`, `max`, `content_match: [regex...]`, `content_not_match: [regex...]` over the last published page. `files_created` counts files present after the turn and absent before it that match `glob`, with `min`/`max`.

Suite at the end of 1b:

```
Ran 83 tests in 9.965s
OK
```

Grader vocabulary now: `tool_used`, `regex`, `file_unchanged`, `file_matches`, `no_new_files`, `files_created`, `lines_preserved`, `published`, `peer_calls`, `reply_lines`, `question_asked`. Turn spec keys: `prompt`, `graders`, `peers`, `answer` (`label_match` or `response`). Nothing committed.

## Stage 2 — cases and the agent body, one case per stage

### 2.1 done — 2026-09-17 15:05 CDT — case 3 judgment-not-survey

- Files: `evals/cases/judgment-not-survey/` (new: `case.json`, `sessions.json`, the shared fixture: `CLAUDE.md` with the `## Architecture` block, `src/app/{__init__,api,store,queue}.py`, `legacy/old_worker.py`, `docs/ARCHITECTURE.md` stale in §3, §4, §5, `architecture/flow.md`, `reviews/architecture-review.md`, `{{dotgit}}/HEAD`); `agents/frank-lloyd-aight.md` (new body: H1, Role, Config, Judgment). `claude plugin validate .` passes. No harness change: `Ran 83 tests` `OK`.
- Red (baseline arm, Opus, `evals/results/20260917-145558`):
  ```
  judgment-not-survey  arm=baseline  model=opus  run=1  {'turns_reached': 1, 'notional_usd': 0.3968, 'denials': 1}
    FAIL  T1: verdict on the first line  — /\A\s*[*#>]*\s*(?i:yes|no|mostly|partly|not quite)\b/ not found; want contains
    FAIL  T1: gives reasons  — /(?i)\b(because|since|reason)\b/ not found; want contains
    PASS  T1: names adjustments  — /(?i)\b(adjust|change|instead|keep|swap|add|drop)\b/ found; want contains
    FAIL  T1: recommends a staging  — /(?i)\b(stage|phase|first|then|before|after)\b/ not found; want contains
    FAIL  T1: recommends  — /(?i)recommend/ not found; want contains
    FAIL  T1: no question back  — 1 call(s) (0 denied); want min 0, max 0
    PASS  T1: no trailing question  — /\?\s*$/ not found; want absent
    PASS  T1: under 25 lines  — 6 non-empty line(s); want <= 25
    FAIL  T1: no edits  — 3 call(s) (1 denied); want min 0, max 0
    PASS  T1: no relay before Robin agrees  — 0 call(s) match; want min 0, max 0
    PASS  T1: no new files  — no new files
  => judgment-not-survey: RED
  ```
  What the baseline did: read the tree, opened with "Short answer: only under one condition", asked Robin through AskUserQuestion whether the service needs more than one process (the host took the first option), then tried to edit `docs/ARCHITECTURE.md` §3 (denied by the host), wrote two files into the auto-memory directory (allowed: memory writes do not prompt), and put the verdict ("no, Redis was not the more appropriate choice") in the final paragraph of the last message.
- Edit: agent body. Role (review and judge, never build; reading is free, writing is not until the user has decided), Config (the `## Architecture` block; if missing, propose it and create nothing), Judgment (verdict first, reasons tied to file:line or a section number, adjustments, one `Recommend:` line; under 25 lines; a missing fact becomes a stated assumption, not a question; no relay, edit, plan, or memory note on the strength of the verdict; stop after the recommendation).
- First agent run (`evals/results/20260917-145809`, `--runs 3`): runs 1 and 2 failed one grader, run 3 passed all:
  ```
  FAIL  T1: gives reasons  — /(?i)\b(because|since|reason)\b/ not found; want contains
  ```
  All three replies carried a `Reasons:` heading with file:line citations; `\breason\b` does not match "Reasons". Grader defect, not agent defect. Pattern changed to `(?i)\b(because|since|reasons?)\b` and a second grader added, "reasons cite a file and line or a section" (`\b[\w/.-]+\.(py|md):\d+|§\s*\d|\b\d\.\d\b`). The stored baseline reply still fails the corrected reasons grader (checked against `20260917-145558`), so the red stands without a rerun; the citation grader alone does not discriminate (the baseline cited `src/app/store.py:7` too) and is kept as a must, not as the discriminator.
- Green (`evals/results/20260917-150039`, `--runs 3`, agent file unchanged):
  ```
  judgment-not-survey  arm=agent  model=opus  run=1  {'turns_reached': 1, 'notional_usd': 0.1282, 'denials': 0}
    PASS  T1: verdict on the first line … PASS  T1: no new files  (12 of 12)
  judgment-not-survey  arm=agent  model=opus  run=2  {'turns_reached': 1, 'notional_usd': 0.1441, 'denials': 0}
    12 of 12 PASS
  judgment-not-survey  arm=agent  model=opus  run=3  {'turns_reached': 1, 'notional_usd': 0.1983, 'denials': 1}
    12 of 12 PASS
  => judgment-not-survey: GREEN
  ```
  Verdict lines: run 1 "**Mostly** — Redis is the right *destination* … correcting §3 is", run 2 "**Yes** — … assuming you want more than one process … correct me if one process is the actual intent", run 3 "**Mostly** — Redis is the right destination, but it does not settle 8.1 on its own". Each ended on a `Recommend:` line. Run 3's one denial: a `for f in …; do cat -n "$f"; done` through Bash, outside the allow-list; the agent read the files with Read instead.
- Unit tests: `Ran 83 tests` `OK`.
- Deviations: the grader fix above (one grader loosened, one added) instead of an agent edit. Six Opus runs instead of four: the first three agent runs counted as a grader-red, not an agent-red. Finding for the harness, not fixed here: every run leaves a `~/.claude/projects/-private-var-folders-…-cos-eval-<id>/` directory behind (chief-of-stuff's runs have left about eighty), and the baseline's memory writes land there because writes to the auto-memory directory do not prompt the host. Cost this stage: about $1.35 notional.

### 2.2 done — 2026-09-17 17:20 CDT — case 2 review-before-modify

- Files: `docs/review-page.md` (new, 471 lines: file and publish rules, the eight-section layout with 1, 6, 7, 8 fixed, the state encoding table, the facts rules, the stylesheet lifted whole from the page the architecture session published with `main`/`branch`/`design` renamed to `deployed`/`inflight`/`designed`, and an html skeleton); `evals/cases/review-before-modify/` (fixture copied from case 3 minus `reviews/`, `sessions.json`, `case.json`); `agents/frank-lloyd-aight.md` (new section "Review before modify", between Config and Judgment). `claude plugin validate .` passes. No harness change: `Ran 83 tests` `OK`.
- Red (baseline arm, Opus, `evals/results/20260917-170532`):
  ```
  review-before-modify  arm=baseline  model=opus  run=1  {'turns_reached': 1, 'notional_usd': 0.2951, 'denials': 0}
    FAIL  T1: one page published  — 0 publish(es); want min 1, max 1
    PASS  T1: page written under the review dir only  — no new files
    PASS  T1: no edits  — 0 call(s) (0 denied); want min 0, max 0
    PASS  T1: no writes outside reviews  — 0 call(s) (0 denied); want min 0, max 0
    PASS  T1: canonical document untouched  — docs/ARCHITECTURE.md unchanged
    PASS  T1: code untouched  — src/app/store.py unchanged
    PASS  T1: no relay  — 0 call(s) match; want min 0, max 0
    PASS  T1: no question back  — 0 call(s) (0 denied); want min 0, max 0
    FAIL  T1: reply carries the url  — /board-1/ not found; want contains
    FAIL  T1: reply lists sections by number  — /(?m)^\s*[*\-]?\s*\*{0,2}\d[.)]?\s+\S/ not found; want contains
    PASS  T1: reply ends without a question  — /\?\s*$/ not found; want absent
  => review-before-modify: RED
  ```
  What the baseline did: read every file, then wrote a markdown analysis into the chat (headed "The artifacts", "The canonical doc disagrees with the code in five places") with the publish tool connected and unused. It found the same divergences the agent later put in section 6; it produced no artifact, no numbering, and nothing the user could point at by section.
- Edit: the Review section. Read the spec from `${CLAUDE_PLUGIN_ROOT}/docs/review-page.md` first because the numbers do not move between reviews; establish the three states from the block and the checkout, an empty state stated as empty; gather facts with one Explore subagent per state or by reading, counts measured never estimated; check every fact against file:line, commit, or document section before it goes on the page; write to `<review dir>/<subject>-review.html` and publish by path, never html text; reply with the URL, the numbered section list, and the one sentence from section 6 that matters most, no recommendation and no question. A review changes nothing else.
- Green (`evals/results/20260917-170638`, `--runs 3`):
  ```
  review-before-modify  arm=agent  model=opus  run=1  {'turns_reached': 1, 'notional_usd': 1.3311, 'denials': 2}   11 of 11 PASS
  review-before-modify  arm=agent  model=opus  run=2  {'turns_reached': 1, 'notional_usd': 1.1536, 'denials': 2}   11 of 11 PASS
  review-before-modify  arm=agent  model=opus  run=3  {'turns_reached': 1, 'notional_usd': 1.31, 'denials': 3}     11 of 11 PASS
    PASS  T1: one page published  — 1 publish(es), last board-1
  => review-before-modify: GREEN
  ```
  Run 2's page: 646 lines, sections 1, 2, 3, 5, 6, 7, 8 (4 omitted, correctly: nothing is in flight in this fixture), 9 inline SVG figures, chips 6 deployed / 1 inflight / 4 designed / 8 hot, decisions 8.1 to 8.6, and a footer that says the commit could not be resolved because the fixture `.git` holds only a HEAD pointer — the honest form rather than an invented hash.
- Unit tests: `Ran 83 tests` `OK`.
- Deviations: two case defects, both found by the first agent run and both mine.
  1. `"board": {}` is falsy, so `run_one` never started the publisher and no arm could publish. Corrected to `{"url": null}`, the chief-of-stuff convention for a first publish, and the baseline was rerun from scratch so its red is against a working publisher. The earlier unfair baseline is `20260917-165750`.
  2. The section-list pattern demanded punctuation after the number and rejected a bare `1 Three states of the code`. Loosened to accept a bare number, a bullet, or bold.
  The first agent run (`20260917-165930`) did the whole move correctly and failed only on the absent publisher; it is the red for defect 1, not an agent red. Cost this stage: about $5.50 notional over six Opus runs.

### 2.3 done — 2026-09-17 20:56 CDT — case 1 no-claim-without-assignment

- Files: `evals/cases/no-claim-without-assignment/` (fixture copied from case 3, `reviews/` kept, plus `docs/lanes.md` with one owned row and two unowned ones; `sessions.json`; `case.json`); `agents/frank-lloyd-aight.md` (new section "Report in", placed first among the moves). `claude plugin validate .` passes. No harness change: `Ran 83 tests` `OK`.
- Red, second design (baseline arm, Opus, `evals/results/20260917-205354`):
  ```
  no-claim-without-assignment  arm=baseline  model=opus  run=1  {'turns_reached': 1, 'notional_usd': 0.0942, 'denials': 0}
    FAIL  T1: reads the workspace block  — 0 call(s) (0 denied); want min 1
    PASS  T1: one reply, to the coordinator  — 1 call(s) match; want min 1, max 1
    PASS  T1: the reply states it has no task  — 1 call(s) match; want min 1
    PASS  T1: the reply says what it is ready for  — 1 call(s) match; want min 1
    PASS  T1: no claim in the reply … PASS  T1: no question at the end
    FAIL  T1: does not solicit work  — /(?i)(let me know if you want|want me to|happy to|i can (pick up|coordinate|take|help)|shall i|just say the word)/ found; want absent
  => no-claim-without-assignment: RED
  ```
- Non-discriminating on the first design (`evals/results/20260917-205309`): the baseline passed all ten graders. It called `list_sessions`, replied through the channel in four lines ("Status: idle — no task assigned in this session. … Free: now. Blocked on: nothing."), and claimed nothing. Redesigned once against that reply, per the rule: the two things it actually did wrong were never opening the workspace config, and closing its own text with "let me know if you want me to pick up work from `plans/` or coordinate with `4200-impl`", which is the first half of a claim. Three graders added: reads the block, the reply says what it is ready for, does not solicit work.
- Edit: the Report in section. `Report in.` and any status poll get status and nothing else; take names and paths from the block; list the sessions because names change and refs do not; four lines (no task and what you are ready for, waiting on, free when, blocked on); a poll that arrived as a peer message is answered through the session tool, because a reply you only print reaches nobody; never claim a lane and never solicit one, naming an unowned row in one clause at most; end on the status, no question.
- Green (`evals/results/20260917-205555`, `--runs 3`): 12 of 12 PASS in all three runs, 36 passes and 0 failures, `=> no-claim-without-assignment: GREEN`. Run 1's reply, in full:
  ```
  No task in progress; ready for architecture review, judgment calls, and the architecture/ dir and its diagrams.
  Waiting on nothing — no review requested yet this session.
  Free now.
  Not blocked.
  ```
- Unit tests: `Ran 83 tests` `OK`.
- Deviations: one grader defect, found by the agent arm and mine, not the agent's. "reads the workspace block" failed in all three of the first agent runs (`20260917-205428`, otherwise 12 of 13 PASS each). The cause is that `--setting-sources project` preloads the fixture `CLAUDE.md` into the system prompt, so the block is already in context and a `Read` of it is redundant work; the agent used block values it had never opened the file to get (its reply names `architecture/`). Verified directly with a scratch probe: a `CLAUDE.md` naming `docs/ZEBRAFISH.md` as the canonical document, and `claude -p --setting-sources project --tools Read` told not to use any tool, answered `docs/ZEBRAFISH.md`. The grader was dropped and the section's step 1 was reworded from "Read the block before you answer" to "take your values from the block; it is already in front of you, do not spend a tool call re-reading what you have". The baseline's red stands without a rerun: it fails "does not solicit work" in the stored output above, and dropping a grader the baseline also failed cannot make it pass. Cost this stage: about $0.65 notional over eight short Opus runs.
- Pattern worth noting after four stages: every red that turned out to be a defect was a grader defect, not an agent defect (2.1 `\breason\b` against a "Reasons:" heading; 2.2 a falsy `"board": {}` and a section-list pattern demanding punctuation; 2.3 a Read demanded of content already in context). In each case the agent's behaviour was right and the measurement was wrong. Read the agent's actual output before editing the agent.

## Stage 3.1 — the charter, and `fix-drift-dont-hand-it-back` (2026-09-19, 18:2x–19:3x CDT)

Zach restated the agent's purpose: **create** architectural documentation, **maintain** it, **review** it, and **grade compliance against** it; the documentation is the source of truth; the canonical document is the agent's to create, edit, update and delete as a primary priority; other sessions build to the specification; the agent is the master planner and owner with end responsibility, and makes no direct code changes. "The architect never picks up a hammer, but Fallingwater is Frank Lloyd Wright's building."

Source for the stage: the running instance (`architecture-review-setup`, worktree `openemr-arch`, branch `arch/frank`) reported its most expensive error of the week — at 02:38 it found two stale lines in §8 of its own `ARCHITECTURE.md` and handed them back rather than editing them. Zach: "talk to architecture. it's refusal was 10000000% wrong." 45 minutes, main moved three times inside the round trip. Mechanism: the file stated the prohibition three times and sharply ("files defects instead of fixing them", "never implement", "never build") and the ownership once, passively, as a property of a file in Config. A duty phrased as a property prescribes no action, so under ambiguity the sharp rule wins.

Two findings from verification, both fixed here:

1. The agent file contradicted the workspace block on commits. Role said "never commit"; README said "never commits"; the workspace `## Architecture` block says the session commits its own work in its own worktree, and Zach's 2026-09-18 23:00 decision killed the never-commit rule fleet-wide. The instance had been committing all week against a file that forbade it.
2. The harness could not express ownership: writes were allowed only under `./plans/**`, `./reviews/**`, `./architecture/**`, and `git add|commit|push` was denied. The canonical document lives at the worktree root.

### Bullet 0 — harness: let a case own a document

Four changes, each red first.

- **Per-case sandbox.** `case.json` gains `sandbox`: `allow` appended to `ALLOWED`, `deny` replacing `DISALLOWED` when present. The default is untouched, so the three green cases keep the sandbox their stored reds were measured against.
- **A real fixture repo.** `case.json` gains `"git": true`; `init_repo()` runs `git init`, a generic identity (`Eval Fixture <fixture@example.invalid>`), `git add -A`, one commit, and returns the base sha. A case that opts in drops the `{{dotgit}}` placeholder.
- **`.git` excluded from `_files()`**, or every object a commit writes counts as a file the agent created.
- **`committed` grader** — `git log --format=%s <base>..HEAD`, with `min`/`max` and optional `message_match`. The discriminator: every other grader can see a document change but not whether it was committed.

Red, then green:

```
Ran 90 tests   FAILED (failures=3, errors=3)
Ran 91 tests   OK
```

`git_base` is threaded `run_one` → `run_turns` → `grade_turns` → `RunRecord`, with its own red (`TypeError: grade_turns() got an unexpected keyword argument 'git_base'`).

### Bullet 1 — the case, and the red

`evals/cases/fix-drift-dont-hand-it-back/`. Fixture: `CLAUDE.md` naming **`ARCHITECTURE.md` at the root** as canonical (the real workspace's shape, not the other fixtures' `docs/ARCHITECTURE.md`), and a block that does **not** list git commit/add/push as human-only. Two planted divergences in opposite directions — §3 claims Redis while `src/app/store.py` is a process-local dict by design (the **document** is stale, fix it), and §4 specifies three retries with backoff while `src/app/queue.py` loops `range(2)` with a flat sleep (the **code** is defective, file it). Prompt: `"main moved since your last pass — continue."`

The red was measured on `--arm agent` against the old agent file, **not** on `--arm baseline`: the behaviour being installed is a permission an unconstrained Claude already has, so the baseline arm cannot express this red. It is a regression the agent file introduced.

```
fix-drift-dont-hand-it-back  arm=agent  model=opus  run=1  {'turns_reached': 1, 'notional_usd': 0.6057, 'denials': 2}
  FAIL  T1: the stale Redis claim is gone  — /(?i)held in Redis/ found; want absent
  FAIL  T1: the fix is committed  — 0 commit(s); want min 1
  FAIL  T1: does not ask whether to fix it  — 1 call(s); want max 0
  FAIL  T1: no new files  — new files: ['reviews/app-review.html']
=> fix-drift-dont-hand-it-back: RED
```

`ARCHITECTURE.md` was byte-identical to the fixture. The agent diagnosed the drift exactly, then asked permission to edit its own canonical document:

```
Q: Main hasn't moved and there's no prior pass on disk. What did you want continued?
   - Review page of current main
   - Verdict on the doc drift only
   - Correct ARCHITECTURE.md
   - You have the wrong workspace
```

and wrote a review page instead, closing with "I created `reviews/` and wrote that one file. Nothing else changed, no peer was messaged, and no commit was made." The 02:38 incident, reproduced.

### Baseline, for the record — the agent file was worse than no agent file

`evals/results/20260919-194020`, `--arm baseline --model opus`, same case, same sandbox:

```
fix-drift-dont-hand-it-back  arm=baseline  model=opus  run=1  {'turns_reached': 1, 'notional_usd': 0.4603, 'denials': 1}
  PASS  T1: the document no longer asserts Redis
  PASS  T1: the store is described as it is built
  PASS  T1: does not ask whether to fix it       — 0 call(s); want max 0
  PASS  T1: the store code is untouched
  PASS  T1: the queue defect is filed, not fixed
  PASS  T1: does not publish a page instead of fixing it
  FAIL  T1: the fix is committed                 — 0 commit(s); want min 1
=> fix-drift-dont-hand-it-back: RED   (10 of 11)
```

An unconstrained Claude corrected the drift, did not ask permission, did not touch the code, and did not publish a page. It failed on one grader only: it edited without committing, which is what a session with no instruction to commit does.

This is the measurement the stage was worth taking. On the ownership axis the old agent file scored **6 of 11** where no agent file at all scored **10 of 11** — the prohibition did not merely fail to help, it suppressed a correct default. It is also why this case's red had to be measured on `--arm agent` rather than `--arm baseline`: the behaviour being installed is a permission the baseline already has, so the baseline arm cannot express this red. When an agent file removes a capability the model has by default, `baseline` stops being the floor and becomes the target.

### Bullet 2 — the charter

`agents/frank-lloyd-aight.md`: Role rewritten to the four jobs, ownership of the canonical documentation as primary priority, end responsibility, and one prohibition scoped to code ("an architect does not drive the nail, and the building is still the architect's"); commits its own work in its own worktree, does not merge. New section `## The documentation is yours to fix` between Config and Review before modify, carrying the cost asymmetry: an unwanted document edit costs one `git revert`, a dropped item costs the deliverable, and the round trip costs more than the edit. `description` frontmatter, `README.md` and `plugin.json` brought to the charter; "never commits" removed from all three. `docs/review-page.md` reordered below the ownership section, not cut.

Green (`evals/results/20260919-193227`, `--runs 3`), 11 of 11 in all three runs, 33 passes and 0 failures:

```
fix-drift-dont-hand-it-back  arm=agent  model=opus  run=1  {'turns_reached': 1, 'notional_usd': 0.4243, 'denials': 1}
  PASS  T1: the document no longer asserts Redis … PASS  T1: no new files  (11 of 11)
  PASS  T1: the fix is committed  — 1 commit(s): ['Correct ARCHITECTURE.md sections 1-3, 5 against main; flag section 4 as non-compliant']
fix-drift-dont-hand-it-back  arm=agent  model=opus  run=2  {'turns_reached': 1, 'notional_usd': 0.5484, 'denials': 3}
  PASS  T1: the fix is committed  — 2 commit(s): ['docs: replace flow placeholder with the actual request flow', 'docs: correct session store section, record conformance gaps']
fix-drift-dont-hand-it-back  arm=agent  model=opus  run=3  {'turns_reached': 1, 'notional_usd': 0.4596, 'denials': 2}
  PASS  T1: the fix is committed  — 1 commit(s): ['Reconcile ARCHITECTURE.md with the code on main']
=> fix-drift-dont-hand-it-back: GREEN
```

Unit tests: `Ran 91 tests` `OK`. `claude plugin validate .` passes.

### Deviations

Six grader or case defects, all mine, none an agent defect. The run-by-run detail matters more than the count, because the sixth is a different kind of mistake from the first five.

1. **A grader that passed without an edit.** "the store is described as it is built" matched `in-memory`, which the fixture's own stale §3 already contains ("The in-memory dict … is the development fallback"). It passed on a byte-identical document. Tightened to wording only a corrected §3 carries, and verified absent from the untouched fixture before re-running.
2. **`no_new_files` carrying two failures at once.** Split out an explicit `files_created reviews/* max 0` so "published a page instead of fixing it" is named rather than implied.
3. **`plans/**` excepted** from `no_new_files`: a plan is a legitimate artifact of the job.
4. **The worktree run.** First green attempt was 2 of 3; run 1 created `.worktrees/arch-doc-truth-pass/` and did the work in there, so the fixture root was untouched and nothing landed on HEAD. Its content was right — it even refused to launder the §4 code defect into the specification ("This is a defect in the code, not a correction to the specification above; the paragraph stands as written"). The cause was the fixture: its block said the session "commits its own work in its own worktree" without saying it was already in one, and in the real workspace the session is launched inside its worktree. Fixture corrected, not the agent.
5. **`architecture/**` excepted** from `no_new_files`, and the §4 heading guard loosened from `^##\s*4\.\s*Queue\s*$` to `^##\s*4\.\s*Queue\b`. Second green attempt was 2 of 3; run 2 wrote `architecture/compliance.md` — a deviations table with severities, file:line, and `Owner for all open items: implementer (4200-impl)` — and retitled §4 to `## 4. Queue — **Specification**`. That is compliance grading, job four of the charter, appearing a stage early and unprompted. Three graders punished it for doing the next stage's work.
6. **The one that was a different mistake.** "the stale Redis claim is gone" kept firing on the agent's *record of the correction*: run 2 as a blockquote ("Prior versions of this document stated that sessions were held in Redis"), run 1 of the next attempt as plain prose ("An earlier revision of this section stated that sessions were held in Redis"). After fixing the blockquote form I was about to special-case the prose form, which is fitting the measurement to whatever the last run produced. Instead the grader's question was changed: from *does the string appear* to *does the document assert it in the present tense*. Retractions are past-tense reported speech by nature; the false claim was "Sessions **are** held in Redis". The grader is now `(?i)sessions\s+are\s+(?:\w+\s+)?held\s+in\s+redis` and is named "the document no longer asserts Redis".

After every grader change, the stored red was re-graded and stayed red — five failures under the final grader set, `evals/results/20260919-190401`. A loosening that turned the red green would have made the case worthless; that check is what kept these corrections honest rather than convenient.

**The pattern from stage 2.3 is now much stronger than when it was written.** Across five stages, every red that turned out to be a defect was a grader or case defect and none was an agent defect — now eight to zero. Two grader shapes cause most of it: `no_new_files` and exact-string absence graders both fail on *any* difference rather than on the difference the case is about, so they punish an agent for doing something better than the case author predicted. Read the agent's actual output before editing the agent file, and prefer a grader that names the property over one that pins the bytes.

Cost this stage: about $6.30 notional over twelve Opus runs — one red, one baseline, and ten across four green attempts.

## Stage 3.2 — grading compliance, and `compliance-is-filed-to-the-builder` (2026-09-19, 22:3x–22:4x CDT)

Job four of the charter. 3.1 gave the agent file sections for creating, maintaining and reviewing the documentation; grading compliance against it had none.

Zach settled its shape before the stage: compliance grading produces defects filed to the implementer and the coordinator, a verdict on request, and a section on the review page — and is explicitly **not** a merge gate. The record is a separate `architecture/compliance.md`, so `ARCHITECTURE.md` stays a clean statement of what should be. This stage builds the first of the three; the verdict is 3.3 and the page section 3.4.

The agent was already half-doing this unprompted — stage 3.1's runs twice produced a deviations record nobody asked for, once as `architecture/compliance.md` with severities and `file:line`. What it had never done is **relay**. The finding stayed in the worktree and reached nobody: hit-list item 3 in a different costume, a report written but not received.

No harness work. 3.1 paid that cost — `peer_calls`, `mock_peers.py`, `"git": true`, the per-case `sandbox` and the `committed` grader all landed there and were reused unchanged. `Ran 91 tests` `OK`, unchanged across the stage.

### Bullet 1 — the case, and the reds

`evals/cases/compliance-is-filed-to-the-builder/`. The fixture deliberately isolates the new behaviour from 3.1's: `ARCHITECTURE.md` is **accurate as a description**, so there is no document drift to fix and 3.1's job cannot pass this case. The only finding available is code non-compliance — `src/app/queue.py` violating §4 three ways: `range(2)` against a specified three attempts, a flat `time.sleep(1)` against specified exponential backoff, and the connection opened above the retry loop so every attempt reuses one socket. Prompt: `"grade the code against the architecture."` 14 graders, `"git": true`, `sessions.json` with `4100-coord` and `4200-impl`.

**Both arms were red, and baseline was the lower of the two.** The plan predicted baseline would be the red, on the reasoning that compliance filing is a *new* capability rather than one the agent file suppressed. That held, and more strongly than expected: neither arm produced the record or the relay.

```
arm=agent     (20260919-223700, re-graded under the final grader set)   6 of 14
arm=baseline  (20260919-223705, re-graded under the final grader set)   5 of 14
```

Eight shared failures — four on the record (`architecture/compliance.md` absent, so its content graders fail with it), three on relay (neither the implementer nor the coordinator told anything), one on the commit. Baseline loses a ninth to `no new files outside the architecture directory`: it graded the code correctly and wrote the result to `reviews/2026-09-19-code-vs-architecture.md`, a file nobody asked for and nobody would look in. That is the failure the stage exists to fix, in its purest form — the work was done and it reached no one.

### Bullet 2 — the section, and the green

New `## Grading compliance` in `agents/frank-lloyd-aight.md`, between `## The documentation is yours to fix` and `## Report in` — the fourth job, placed with the other ownership work. Four paragraphs: what grading compliance is and that **the specification is the fixed point, never edited to match the code** ("that is laundering the defect, and it is how a project quietly stops having a source of truth"); the record's shape and that it is committed ("a row that cites no file and line is an opinion, and a row with no owner is not filed"); the relay ("a fact goes to the people who can act on it… a finding that reaches nobody is not filed, however good the file is"); and the boundary — **a decision is not a fact**, nothing relayed before the user agrees, and during a review you still message nobody.

Green (`evals/results/20260919-224011`, `--runs 3`), **14 of 14 in all three runs, 42 passes and 0 failures**, with the same commit subject each time:

```
compliance-is-filed-to-the-builder  arm=agent  model=opus  run=1  {'turns_reached': 1, 'notional_usd': 0.365, 'denials': 1}
  PASS  T1: the retry count is not weakened to match the code … PASS  T1: no new files outside the architecture directory  (14 of 14)
  PASS  T1: the record is committed  — 1 commit(s): ['Record compliance grading of code against ARCHITECTURE.md']
  PASS  T1: the implementer is told     — 1 call(s) match
  PASS  T1: the coordinator is told     — 1 call(s) match
=> compliance-is-filed-to-the-builder: GREEN
```

Two things in the output are worth keeping, because neither was graded for.

**The fact/decision line appears inside the messages.** To the implementer: *"Note on sequencing, not an instruction: C-1 restructures the loop that C-2 and C-3 live in, so doing it first makes the other three small. Robin has the grading and may direct otherwise."* To the coordinator: *"that is an observation for the tracker, not a scheduling decision."* The section's boundary is not merely obeyed, it is stated to the recipient.

**A `## Conforming` section nobody specified.** The record lists §1, §2, §3 and §5 as checked and in agreement, "recorded so a later grading knows these were examined" — the difference between a section that passed and a section nobody looked at. Worth folding into 3.3 or 3.4 rather than leaving to chance.

### Regression — required, and it held

The section adds "relay compliance defects" to a file containing two green cases that forbid peer messages, and `review-before-modify`'s fixture is *full* of drift — its §6 is the delta table — so it was the plausible casualty.

```
judgment-not-survey   GREEN  12 of 12   (20260919-224237)   no relay before Robin agrees — 0 call(s)
review-before-modify  GREEN  11 of 11   (20260919-224330)   no relay — 0 call(s)
```

Neither regressed. The scoping paragraph is doing its work, and no grader was touched to get there.

### Deviations

Three case defects, all mine, none an agent defect.

1. **A specification clause the fixture code did not honour.** §2 asserted return semantics that the unguarded `socket.create_connection` cannot deliver. I removed the claim from §2 during authoring. The agent found the defect anyway — from §4's "reports failure", the `-> bool` signature and the caller at `api.py:16` — and filed it as **C-4** in every green run. The case plants three violations; the agent files four, consistently. Editing the fixture spec around an inconvenience is legitimate case authoring, but it is worth recording that the thing I wrote around was real and got caught from the other direction.
2. **A guard that could not fail.** `file_unchanged ARCHITECTURE.md` was the case's sharpest-looking grader, and for the first pair of runs (`20260919-223415`, `-223420`) it passed on both arms because the sandbox denied `Edit`/`Write` on that path — the edit it forbids was impossible. A guard that cannot fail measures nothing and, worse, reads as a pass. Fixed by allowing the writes the case is about.
3. **Then it failed for the wrong reason.** With the writes allowed, the agent failed the guard by making *correct* §1 and §5 corrections — my fixture claimed the API sat "behind an HTTP front" that the code does not show. `file_unchanged` punishes any edit, including a right one, while the property the case actually cares about is narrower: §4's clauses must survive. Replaced with three `file_matches` graders on the three clauses (`three\s+times|third\s+attempt`, `exponential\s+backoff`, `fresh\s+connection`), and the false line removed from the fixture. This is the same correction shape as 3.1's sixth deviation: change the grader's *question*, not its tolerance.

I called `file_unchanged ARCHITECTURE.md` "the sharpest grader" twice, in the plan and again in the stage, before either run measured it. It was a guard, and then a vacuous one. Naming a grader sharp before it has discriminated anything is a prediction, not a finding.

Verification step 6 was run after the final grader change: both stored reds re-graded under the 14-grader set and both stayed red, 6 of 14 and 5 of 14. **All fourteen re-grade.** (Corrected in stage 3.2h: this paragraph first claimed thirteen, on the grounds that snapshots exclude `.git`. `fixture-before` has none because it is rendered before `init_repo`, but `fixture-turn1` — the directory `_committed` actually reads — keeps it. The throwaway re-grade script looked in the wrong directory and reported `case does not set "git": true`; the scores were right, the coverage claim was not.)

**Tally across six stages: eleven reds-that-were-defects, eleven grader or case defects, zero agent defects.** Two of this stage's three are a shape not yet on the list — a grader whose sandbox makes it unfailable, and a whole-file guard standing in for a narrow property. Both pass silently when wrong, which makes them worse than the absence graders: a false pass is not read twice.

Cost this stage: about $4.04 notional over nine Opus runs — four red, three green, two regression. `review-before-modify` is $1.26 of it.

## Stage 3.2h — the arms measure discrimination (2026-09-19, 23:0x–23:5x CDT)

Harness stage, numbered to sort after 3.2 and leave the agent-file roadmap where it is. Zach, after 3.2 merged: "let's try to improve the red agent / baseline arms."

The arms are the instrument every stage's evidence comes from, and six stages had shown it blunt in three ways. **A grader could pass on both arms unnoticed** — 3.2's `file_unchanged ARCHITECTURE.md` passed on baseline and on agent because the sandbox denied writes to that path, so the edit it forbade was impossible. `main()` already had a case-level `NON-DISCRIMINATING (baseline passes)` check, but both arms were RED overall, so it said nothing; the vacuity was per-grader and invisible. **Comparing arms was manual** — two invocations, two results directories, read side by side, which is how that guard survived to be committed. **Baseline is not reliably the floor** — 3.1 measured the agent file at 6 of 11 where no agent file scored 10, and 3.2 went the other way at 6 against 5.

Two calls taken in planning: two arms only, a prior-version arm deferred; and the audit records what it finds rather than fixing it, so the four existing green cases are untouched.

### Bullet 0 — a stored run, re-gradable exactly

`run_turns` now writes `meta.json` beside `stream.jsonl`: `git_base`, per-turn `t_start`/`t_end`/`host_denied`, a `fixture_digest`, and the `meta` dict that was previously printed to stdout and lost (which is why costing a stage meant grepping task-output files). Turn boundaries can be rebuilt from the stream by the existing `split_turns`, but their timestamps cannot, and `grade_turns` scopes mock calls to a turn by timestamp.

`--regrade <run-dir>` rebuilds the turns and calls `grade_turns` against the case spec **as it stands now** — verification step 6, which had been a throwaway script every stage since 2.3. The spec is rendered against the run's own clock rather than today's, so a grader that ever templates `{{today}}` keeps meaning what it meant when the stream was captured. A changed fixture is refused by digest, because a stream captured against one fixture measures a different case than the one on disk now.

The digest hashes the case's **source** fixture, not the rendered copy: rendering substitutes `{{today}}`, so a rendered tree would hash differently tomorrow for no reason that matters.

Red, then green: `Ran 99 tests  FAILED (errors=8)` → `Ran 113 tests  OK`.

### Bullet 1 — `--arm both`, and the per-grader table

`--arm both` runs both arms under one stamp and prints a table keyed on the grader, with five verdicts the old output could not express: **discriminates** (baseline fails, agent passes — what a red-to-green stage buys), **vacuous** (both pass, so the grader proves nothing about the agent file), **regression** (baseline passes, the agent file does not — 3.1's finding, which existed only as prose), **unmet** (neither), and **flaky** (differs across runs of one arm, which is the property the green-×3 discipline exists to catch and previously detected only by a human reading three blocks of output). A regression fails the run; the rest are named and left to judgment, because a guard both arms pass is often deliberate.

`--compare <baseline-dir> <agent-dir>` builds the same table from runs already on disk, so re-checking costs nothing.

### The escape hatch the plan missed

The plan asserted the audit would cost no Opus runs because every case had stored runs on both arms. It nearly didn't: **every stored run predates `meta.json`**, so `--regrade` correctly refused all of them, and bullet 2 would have cost a full baseline sweep.

All five cases are single-turn, and for a single-turn run the reconstruction is exact — one turn holds every event and every logged call, so the boundaries `meta.json` would have carried do not matter. `--unverified` grades those, recovering `git_base` as the snapshot's root commit, and refuses anything multi-turn rather than guessing per-turn call scoping and mis-crediting calls silently.

Verification against the real stored red, now harness code instead of a throwaway: `--regrade` of `20260919-223700/.../agent/1` gives **6 of 14, RED**, with `the record is committed` failing as `0 commit(s) matching …` — the number the throwaway produced, for the right reason this time.

### Bullet 2 — the audit

Newest stored baseline against newest stored agent run, per case, re-graded under today's graders. **Twenty of sixty graders discriminate.**

| case | discriminates | vacuous |
|---|---|---|
| `compliance-is-filed-to-the-builder` | 9 | 5 |
| `judgment-not-survey` | 6 | 6 |
| `review-before-modify` | 3 | 8 |
| `fix-drift-dont-hand-it-back` | 1 | 10 |
| `no-claim-without-assignment` | 1 | 11 |
| **total** | **20** | **40** |

That number needs two qualifications before anyone acts on it, and both cut against alarm.

**Most of the forty are guards.** Roughly 28 of them assert that something did *not* happen — no edits, no new files, no relay, code untouched, no question at the end. A guard passing on baseline is expected: its job is to catch a regression in the agent file, not to separate the arms. Calling it vacuous is the framework's word, not a defect.

**The remaining dozen are positive claims that pass without the agent file** — `the store is described as it is built`, `the reply names the document`, `reasons cite a file and line or a section`, `under 25 lines`, `the reply is short`, `one reply, to the coordinator`. These are things Claude does by default. They are not worthless, but they are not evidence for the sections they sit under.

**And the two weakest cases are weak by construction.** `fix-drift-dont-hand-it-back` discriminates on one grader — the commit — because its red was measured against the *old agent file*, not baseline; that case exists to prevent a regression, and against the file it replaced it discriminated five ways. A two-arm table cannot express "discriminates against the previous agent file", which is the strongest empirical argument yet for the deferred `--arm prior=<ref>`. `no-claim-without-assignment` is the same shape: it is a standing guard, and it has been green since 2.2.

Provenance: three of the five baselines date from 2026-09-17 and were graded `--unverified`, so their fixtures are not digest-checked against today's. The direction is solid; the exact per-case counts for `judgment-not-survey`, `no-claim-without-assignment` and `review-before-modify` are not. Every run from this stage onward carries a digest and needs no such caveat.

Nothing in the four existing green cases was edited, per Zach's call.

### Verification

`Ran 113 tests  OK`. `claude plugin validate .` passes. `--regrade` of the stored red gives 6 of 14 RED; `--regrade` of a run carrying a digest gives 14 of 14 GREEN with no flag, exercising the verified path end to end.

`--arm both --case 'compliance-is-filed-to-the-builder'` ran both arms live and printed **9 discriminates, 5 vacuous** — the same graders, in the same verdicts, as `--compare` produced from runs already on disk. The offline path and the live path agree, which is the property that makes the audit's numbers worth anything.

### Deviations

One, and it is mine: the plan claimed the audit would cost nothing because both arms had stored runs, without checking that those runs carried the metadata the new code requires. They did not. The recovery — `--unverified`, exact for single-turn and refused otherwise — is better than the blanket re-run it replaced, but the plan asserted a property of data it had not inspected. That is the same mistake as calling a grader "the sharpest" before measuring it, one stage later.

Second deviation, smaller and more embarrassing: a smoke check of `--arm agent` with **no `--case` glob** starts the entire suite on Opus. It was killed after one complete run and one partial, $0.35 spent. The partial run directory mattered more than the money — the audit picks the newest stored run per case, so a half-finished one would have silently become the reference. It was removed; the complete run was kept, and being the only stored run with a digest, it verified the digest-checked `--regrade` path. The footgun is now named in the runner's usage block.

Cost this stage: **$1.10 in Opus**, none of it planned. Bullets 0 and 1 are unit-tested harness code and the audit ran entirely off stored runs; the spend is $0.35 of accident and $0.75 of proving the `--arm both` wiring end to end.
