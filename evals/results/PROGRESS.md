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
