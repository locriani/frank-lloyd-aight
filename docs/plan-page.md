# The plan page

The page Frank Lloyd AIght writes in a planning session, and rewrites in place every turn until the plan is settled. It is the plan of the architecture: the structure, the modules and their boundaries, the data and where it is kept, the interfaces, and the decisions those rest on. It is not a task list or a schedule. The user reads it and answers by row id. This document fixes the address, the theme, the section numbers and the row format so that every plan page reads the same.

"The plan page", "the plan artifact" and "the plan" all mean this HTML file. It is never a hosted document of another kind.

## File and address

- Path: `<pages dir>/<subject>-plan.html` when the `## Architecture` block names a pages dir; otherwise `<plan dir>/<subject>-plan.html`. One file per plan, rewritten at the same path every turn. Never a second page for the same plan.
- If the block names a URL where the pages dir is served, the address is `<url>/<subject>-plan.html`. Without one, give the file path and say the page is not served. Never paste the HTML into the reply, and never open a browser at it: the user decides when to look.
- This file is the page of record. A copy published anywhere else is made only when the user asks for one, and from this file.
- The file is a whole document, because nothing adds a skeleton when it is served. Its first lines are exactly the five under Head.
- No external script. A paragraph is one line in the source, and nothing caps the width of the page or its text (see the agent's Writing section).

## Head

```html
<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SUBJECT Plan</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">
```

## Stylesheet

Copied whole and never changed: every plan page has the same theme. There is no pill class beyond `done` and `open`; the word inside the pill carries the status.

```html
<style>
:root{
  --bg:#f2f5f1; --paper:#fbfcfa; --ink:#17211c; --muted:#5b6a62; --rule:#cfd9d2;
  --accent:#1c6a49; --accent-soft:#dcebe2; --open:#8a5a00; --open-soft:#f5e9cf;
  --display:"IBM Plex Sans Condensed","Arial Narrow",system-ui,sans-serif;
  --body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --bg:#101613; --paper:#161e1a; --ink:#e4ece7; --muted:#93a39a; --rule:#2b3831;
  --accent:#6fcf9f; --accent-soft:#1c3328; --open:#e3b65a; --open-soft:#3a2e12; color-scheme:dark } }
:root[data-theme="dark"]{
  --bg:#101613; --paper:#161e1a; --ink:#e4ece7; --muted:#93a39a; --rule:#2b3831;
  --accent:#6fcf9f; --accent-soft:#1c3328; --open:#e3b65a; --open-soft:#3a2e12; color-scheme:dark }

body{background:var(--bg);color:var(--ink);font-family:var(--body);font-size:15px;line-height:1.55;padding-inline:clamp(16px,5vw,72px);padding-block:28px 56px}
main{display:flex;flex-direction:column;gap:36px}
h1,h2{font-family:var(--display);font-weight:600;text-wrap:balance;margin:0}
h1{font-size:2rem;line-height:1.15}
h2{font-size:1.25rem;padding-bottom:6px;border-bottom:2px solid var(--ink)}
p{margin:0}
section{display:flex;flex-direction:column;gap:14px}
.eyebrow{font-family:var(--mono);font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
header{display:flex;flex-direction:column;gap:10px}
.facts{display:flex;flex-wrap:wrap;gap:8px 28px;font-size:.9rem;color:var(--muted)}
.facts b{color:var(--ink);font-weight:600}
.next{background:var(--accent-soft);border-left:4px solid var(--accent);padding:12px 16px}

.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.9rem}
th,td{text-align:left;vertical-align:top;padding:8px 12px 8px 0;border-bottom:1px solid var(--rule)}
th{font-family:var(--mono);font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:500}
td.id{font-family:var(--mono);white-space:nowrap;color:var(--muted)}
td.num,th.num{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap;padding-right:0;padding-left:12px}
tr.total td{border-top:2px solid var(--ink);border-bottom:none;font-weight:600}
q{color:var(--muted);font-style:italic}
.pill{display:inline-block;font-family:var(--mono);font-size:.7rem;letter-spacing:.05em;text-transform:uppercase;padding:1px 7px;border-radius:3px;white-space:nowrap}
.pill.done{background:var(--accent-soft);color:var(--accent)}
.pill.open{background:var(--open-soft);color:var(--open)}
.next{background:var(--accent-soft);border-left:4px solid var(--accent);padding:12px 16px}
pre{margin:0;font-family:var(--mono);font-size:.85rem;line-height:1.6;background:var(--paper);border:1px solid var(--rule);padding:14px 16px;overflow-x:auto}
.note{font-size:.85rem;color:var(--muted)}
ul{margin:0;padding-left:1.1em;display:flex;flex-direction:column;gap:4px}
.diagram{background:#fff;border-radius:8px;padding:12px;overflow-x:auto;margin:12px 0}.diagram svg{display:block;margin:0 auto;height:auto}
</style>
```

## Header

```html
<main>
<header>
  <div class="eyebrow">Plan · turn N · YYYY-MM-DD</div>
  <h1>SUBJECT</h1>
  <p>The lead: three or four sentences on what is being planned, what is settled, and what waits on the user.</p>
  <div class="facts">
    <span><b>Open</b> 7</span>
    <span><b>Decided</b> 0</span>
    <span><b>Code</b> none yet</span>
  </div>
</header>
```

`turn N` counts the turns of this planning session, from 1. `Open` is the number of rows whose pill reads proposed, open or under review. Other facts are the plan's own, each one measured or read.

## Next decision

The first thing under the header, before section 1, and it has no number. It holds the one decision the user is asked to make now, written so that it can be read cold: someone who has not read the rest of the page, or the conversation, can answer it.

```html
<section id="next" class="next">
  <h2>Next decision: K1, the question in plain words</h2>
  <p><b>The problem.</b> What is unsettled and why it has to be settled now, in two or three sentences, with no id standing in for an explanation.</p>
  <p><b>The proposal.</b> One proposal. A table when it has parts.</p>
  <p><b>What it costs.</b> What the proposal gives up or makes harder.</p>
  <p><b>Basis.</b> Read in SOURCE. Not read: WHAT.</p>
  <p><b>What it does not decide.</b> The neighbouring questions this answer leaves open.</p>
  <h3>Waiting behind it</h3>
  <div class="scroll"><table>
    <tr><th>ID</th><th>The question</th></tr>
    <tr><td class="id">K2</td><td>The row's question as one full sentence.</td></tr>
  </table></div>
</section>
```

- **One decision.** One row's id in the heading and one proposal in the body. Several changes are never put under one id: each change the user could accept or refuse on its own is its own row, and the others wait behind this one.
- **No status.** Nothing already decided is retold here, and no row is named by its id alone.
- **Checked first.** Before a proposal goes here it is checked against the Decided table and against what the brief asks for and rules out. A proposal that contradicts either is not made.
- **Waiting behind it** lists the other open rows in the order they should be settled, each as a full-sentence question. When nothing else is open, the table is replaced by one sentence saying so.
- When no row is open, the section says that nothing waits on the user.

## Sections

Every numbered section is `<section id="sN">` with `<h2>N. Title</h2>` on the line after it. Sections 1 to 5 are fixed. A subject the plan grows (the data model, the deployment, one module in depth) is appended as section 6, 7 and so on, in the order it arrived. A section is never inserted and never renumbered, because the user points at the numbers across turns.

| # | Title | Body |
|---|---|---|
| 1 | Decided | A short table: ID, Topic, What was decided. Only what the user has answered in this plan. No trivialities, and none of the user's words. Before the first answer the body is one sentence: nothing is decided yet. |
| 2 | Open | The rows waiting on the user, in the order they should be settled, in the row format below. |
| 3 | Structure | The architecture as proposed, as real structure: the folder tree in a `pre`, each module or class with its fields and functions, and the signature at each boundary with parameters and types. What exists today is marked as existing with its file and line; what the plan adds is marked as new. A diagram goes here when the renderer produced one. |
| 4 | What the brief asks for | A table: Requirement (the brief's own id or a short quote of the brief), Where the plan meets it (a section or row id), Status. A requirement the plan does not yet meet says so. |
| 5 | Files | What was read to build the page, each with its path; what was not read; the plan document; the research file holding the alternatives that were read and rejected. |

Anything with two or more attributes is a table inside `<div class="scroll">`, and prose stays short. A rule with conditions is a small `pre` formula beside one plain sentence, never symbols alone.

## Rows

```html
<div class="scroll"><table>
  <tr><th>ID</th><th>Topic</th><th>Proposal</th><th>Basis</th><th>Status</th></tr>
  <tr><td class="id">K1</td><td>Topic</td><td>One proposal, in a sentence or two.</td><td>Read in <code>src/app/queue.py:13</code>. Not read: the broker's own documentation.</td><td><span class="pill open">proposed</span></td></tr>
</table></div>
```

- **ID:** one or two capital letters for the row's subject and a number (`D1`, `K7`, `M3`). An id is never reused and never renumbered, and a row keeps its id when it moves from Open to Decided.
- **One proposal per row,** not a menu. Alternatives that were read and rejected go in the research file named in section 5.
- **Basis:** `Read in <source>` with the file and line, document section or page that was read, or `My reasoning` when it rests on no source. Add `Not read: <what>` wherever a gap remains. A row is proposed only from what was read; a third-party page is named as one.
- **Status,** the pill in the last column:

| Pill | Class | Meaning |
|---|---|---|
| proposed | `pill open` | Frank's proposal, waiting on the user. It stays proposed until the user answers; Frank's own verdict never moves it. |
| open | `pill open` | A question with no proposal yet, and what is missing to make one. |
| under review | `pill open` | The user or a reviewer is looking at it. |
| decided | `pill done` | The user answered. |
| follows | `pill done` | Forced by a decided row, which it names. Never shown as a decision and never asked. |

## Diagrams

A diagram is the renderer's SVG placed inline in `<div class="diagram">`, with a one-sentence legend in a `p` above it. It is rendered before it goes on the page, and it shows real structure (see the agent's Diagrams section). Split a diagram whose arrows cross or whose labels overlap. When the renderer produces no SVG, the structure stays as the folder tree and the signatures, and the page has no diagram.

## Never on the page

- The user's quoted words. Their words and the time they said them live in the plan document.
- Anything stated as decided that the user has not answered.
- An option the user said not to raise again.
- A task list, a schedule, or who builds what.
- Whatever the workspace file bans.
