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
