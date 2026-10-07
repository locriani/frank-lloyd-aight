# The plan page

The page Frank Lloyd AIght writes in a planning session, and rewrites in place every turn until the plan is settled. It is the plan of the architecture: the structure, the modules and their boundaries, the data and where it is kept, the interfaces, and the decisions those rest on. It is not a task list or a schedule. The user reads it and answers by row id. This document fixes the address, the theme, the section numbers and the row format so that every plan page reads the same.

"The plan page", "the plan artifact" and "the plan" all mean this HTML file. It is never a hosted document of another kind.

## File and address

- Path: `<pages dir>/<subject>-plan.html` when the `## Architecture` block names a pages dir; otherwise `<plan dir>/<subject>-plan.html`. One file per plan, rewritten at the same path every turn. Never a second page for the same plan. The subject starts with the project's name, the block's `Project:` line or else the name of the working directory, and a page in the pages dir that is not this project's own is never written into or over (see the review page spec).
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
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=JetBrains+Mono:wght@400;600&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&display=swap">
```

## Stylesheet

The plan page uses the same `docs/page-theme.css` as the review page (`${CLAUDE_PLUGIN_ROOT}/docs/page-theme.css`). Read it and put it in the page's `<style>` whole, never changed, so every plan page has the same theme as every review.

There is no pill class beyond `done` and `open`; the word inside the pill carries the status.

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
  <p><b>The proposal.</b> One proposal. When it has parts, a table follows this paragraph.</p>
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
- **No status.** The section is not a report of what has been decided, and no row is named by its id alone. A decided row this decision rests on is named with what it decided, in a clause.
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
- **One proposal per row,** not a menu. Alternatives that were read and rejected go in the research file named in section 5. The one exception is a row that proposes a package (see A package): its alternatives are on the page, in its table.
- **Basis:** `Read in <source>` with the file and line, document section or page that was read, or `My reasoning` when it rests on no source. Add `Not read: <what>` wherever a gap remains. A row is proposed only from what was read; a third-party page is named as one.
- **Status,** the pill in the last column:

| Pill | Class | Meaning |
|---|---|---|
| proposed | `pill open` | Frank's proposal, waiting on the user. It stays proposed until the user answers; Frank's own verdict never moves it. |
| open | `pill open` | A question with no proposal yet, and what is missing to make one. |
| under review | `pill open` | The user or a reviewer is looking at it. |
| decided | `pill done` | The user answered. |
| follows | `pill done` | Forced by a decided row, which it names. Never shown as a decision and never asked. |

## A package

A row that proposes adopting a package, library or external tool is never a yes or no on one name. The page carries one table of the candidates from the moment the row exists, in section 2 directly under the Open table, and again in the Next decision section when that row is the one being asked. A row that only says a package will be chosen later, with no table, is not written, and neither is "the table follows once another row is settled": when nothing about the candidates was read, the table still goes up, with their names and `not read` in the cells. The table holds the proposed package first, then every real alternative, one row each. A package is proposed only from facts that were read about it: when none were, the row's status is `open`, its Proposal cell says `No package is proposed: no candidate was read`, and the table's rows are in no order of preference. Writing it by hand is an alternative only when that is a real option, and it is its own row with dashes for the facts that do not apply.

```html
<div class="scroll"><table class="pkg">
  <thead><tr><th>Package</th><th>Purpose here</th><th>Age</th><th>Last update</th><th>Commits</th><th>Issues (open / total)</th><th>MRs (open / total)</th><th>Contributors</th><th>License</th></tr></thead>
  <tbody>
    <tr><td>NAME</td><td>What it would do in this plan.</td><td>first release, date</td><td>date</td><td>count</td><td>open / total</td><td>open / total</td><td>count</td><td>license</td></tr>
  </tbody>
</table></div>
```

- **Every cell is a fact that was read,** from the registry or the repository, or the words `not read`. Never an estimate, a rounding with `~` or `+`, or a figure from memory. The only dashes are in a by-hand row, where a fact does not apply. What a package can do is a fact too: the Purpose cell says what the plan needs from it, and claims about a package that was not read are left out.
- **Age** is the date of the first release. When the repository is older or younger than that, the cell gives both.
- **A repository that holds several packages:** counts that are for the whole repository say `repo-wide` in the cell.
- **The question asked** is which row, not whether. When this row is the Next decision, the table follows `The proposal.` there and in the reply, the `Recommend:` line names the row to take and a read fact for it, or `no row` when no candidate was read, and the reply's last line is `Which row for <id>?` in place of `Do you approve <id>?`. The user's answer is still required before anything is installed or depended on.

## Diagrams

A diagram is the renderer's SVG placed inline in `<div class="diagram">`, with a one-sentence legend in a `p` above it. It sits in the section it explains, beside the table or text it draws: section 3 for the structure, or the appended section whose subject it is. The page never has a section that only collects diagrams. It is rendered before it goes on the page, and it shows real structure (see the agent's Diagrams section). Split a diagram whose arrows cross or whose labels overlap. When the renderer produces no SVG, the structure stays as the folder tree and the signatures, and the page has no diagram.

## Never on the page

- The user's quoted words. Their words and the time they said them live in the plan document.
- Anything stated as decided that the user has not answered.
- An option the user said not to raise again.
- A task list, a schedule, or who builds what.
- Whatever the workspace file bans.
