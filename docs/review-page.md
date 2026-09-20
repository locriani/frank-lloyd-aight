# The review page

The page Frank Lloyd AIght publishes when the user asks for a review of the existing architecture. One html file, one publish, and then the user discusses it by section number. This document fixes the layout, the numbering, and the encoding so that every review looks the same and section 6 means the same thing next week.

## File and publish

- Path: `<review dir>/<subject>-review.html`, where the review dir comes from the `## Architecture` block and the subject is the directory or service reviewed (`agent-review.html`, `api-review.html`).
- Publish by passing that path to the tool the block names. Never pass html text to the tool, never paste the html into the reply.
- `<title>` is the subject. No external script. Fonts: the stylesheet below names Google fonts with a system fallback stack; the page renders without them.
- Light and dark: the tokens below define the light palette on `:root`, redefine it under `prefers-color-scheme: dark` guarded as `:root:not([data-theme="light"])`, and again under `:root[data-theme="dark"]`. Keep all three blocks.
- Phone width: one column under 900px, 16px side gutter under 480px. Figures and tables scroll sideways inside their own wrapper; the body never does.

## Layout

```
div.shell
  nav.index            sticky on the left: div.doc-id (subject · date), ol of <a href="#sN"><span>N</span>Title</a>
  main
    header.top         div.eyebrow (what is reviewed · what is out of scope), h1 (subject), p.lede (one sentence naming the three states and where each lives)
    div.legend         printed once: one row per encoding, a 74x30 svg swatch beside <b>name</b> · meaning
    section#s1 … section#s9
    footer.src-list    every commit, branch, worktree, and document the page was built from, and the clock time it was built
```

## Sections

Every section is `<section id="sN">` with `<h2><span class="num">N</span>Title</h2>`. A section that shows one state carries that state's chip in its h2. The numbers 1, 6, 7, 8, and 9 are fixed, because the user points at them across reviews; 2 to 5 are the subject's own views, in this order, as many as the subject has (a missing one is left out and the numbering of 6 to 9 does not move).

| # | Title | Body |
|---|---|---|
| 1 | Three states of the code | `div.states` with one `div.state` per state, in the order deployed, in flight, designed. Each: `h4` with the chip, one sentence, a `dl` of `commit` and measured counts (files, lines, tests). A state with nothing in it is still a card: "In flight: none". |
| 2 | Module map, as built | `figure`: the import graph of the deployed code with line counts on the nodes. Modules carrying too much are `n-hot`. |
| 3 | One request end to end, as built | `figure`: a sequence, lifelines per module, solid calls and dashed returns, loops and branches as `frame` boxes. May be followed by `div.obs`, "noticed while mapping": `<b>title</b>` one sentence `<span class="loc">file:line</span>`. |
| 4 | The in-flight package | `figure` of what the branch or worktree changes, `n-inflight` nodes, with the couplings it still has to the deployed code marked `n-hot`. |
| 5 | The designed layers | `figure` of the design documents' structure, `n-designed` nodes, import direction drawn. |
| 6 | Where they disagree | `div.table-wrap > table`: columns Topic, one per state present (header text plus its chip), What it decides. Rows: `<th scope="row"><span class="tag">6.N</span>Topic</th>`, one `td` per state, last cell `td.why` with one sentence. |
| 7 | Migration roadmap | `div.table-wrap > table.roadmap`: #, step, status (a chip: `done`, `inflight`, `designed`, or `hot` for waiting on a decision), green when. |
| 8 | Open decisions | `ol.decisions` of `li`: `<span class="did">8.N</span>`, `<div><h4>title</h4><p>one paragraph: the choice, what each side costs</p><div class="src">where it comes from: 6.N, a file, a document section</div></div>`. Every undecided row of section 6 appears here. |
| 9 | Where the code departs from the specification | `div.table-wrap > table`: columns #, Section, Severity, Specified, Built, Where. Rows `<th scope="row"><span class="tag">9.N</span>§M</th>`, then the severity as `<span class="chip hot">high</span>` for a gap that breaks what the section exists to guarantee and plain text otherwise, one sentence of what the document specifies, one of what the code does, and `file:line`. Always present: with nothing to report it reads "No gaps: every section of the specification is met by the code as built." |

Figures: `figure > div.fig-scroll > svg` with `role="img"`, an `aria-label` that says in one sentence what the figure shows, and a `viewBox` around 960 wide. `figcaption` opens with the state chip, then `chip hot` when anything is marked, then one sentence of what is not drawn. Arrowheads come from one `<marker>` per figure; text that crosses a line gets `class="halo"`.

## Encoding

One encoding for code state, everywhere on the page, as classes. The legend prints it once; the reader never has to infer it.

| Class | Meaning | Look |
|---|---|---|
| `deployed` (`chip.deployed`, `svg .n`) | on the default branch, or what the block names as deployed | solid outline |
| `inflight` (`chip.inflight`, `svg .n-inflight`) | in a worktree or an unmerged branch | amber, dashed |
| `designed` (`chip.designed`, `svg .n-designed`) | in a design document only | blue, dotted |
| `hot` (`chip.hot`, `svg .n-hot`) | a module carrying too much, a coupling to remove, or a step waiting on a decision | red |
| `ext` (`svg .ext`) | a system not ours | grey, rounded |
| `done` (`chip.done`) | a roadmap step that is finished | filled |
| `svg .e` / `.e-ret` / `.e-designed` | a call or import / a return / an edge that exists only in the design | solid / dashed / blue |
| `svg .frame` / `.life` / `.strip` | a loop or branch box / a lifeline / a footnote band | dotted box / dashed line / grey band |
| text: `.t .ts .tl .tm .tb .th` | node title / small title / label / mono / body / heading | see the stylesheet |

A node is a noun; a verb goes on the edge label. A figure never mixes states without chips on the nodes that differ.

## Facts

- Every fact on the page resolves to a file and line, a commit, or a document section, and the footer names the sources. The user will quote the page back; a wrong line number costs the whole page its standing.
- Counts are measured (`wc -l`, `git log --oneline | wc -l`, the test runner's own summary), never estimated. A count that was not measured is left out.
- Nothing on the page is a recommendation. The page is the shared reference; verdicts come when the user asks by number. The words "recommend" and "should" do not appear on it.
- A design document that contradicts itself gets both readings in section 6 and a row in section 8.
- Section 9 carries **code defects only**: the document specifies something and the code does not do it. A document that has gone stale — it describes what was built once, or what was planned and never built — is not a compliance gap, and belongs in section 6 with the other disagreements, and in section 8 if it needs settling. The specification is the fixed point; a section 9 row says the code is wrong, and saying that about a stale document launders the defect.

## The reply after publishing

The URL on the first line, then the section list with numbers (one line each), then the one sentence from section 6 that matters most, and the count of section 9's rows when it is not zero ("9: three gaps"). No recommendation, no question. The user reads, then discusses by number.

## Stylesheet

Copy this block into the page's `<style>` whole. Do not restyle; a review that looks different reads as a different kind of document.

```css
:root {
  --ground: #eef1f5;
  --ground-2: #e2e7ee;
  --paper: #fbfcfd;
  --ink: #18212c;
  --ink-2: #3b4757;
  --muted: #5f6b7b;
  --rule: #cfd6df;
  --deployed: #2b3542;
  --inflight: #a8660f;
  --inflight-soft: #f6ead6;
  --designed: #2c58a0;
  --designed-soft: #dfe8f6;
  --warn: #b23a2a;
  --warn-soft: #f7e1dc;
  --f-head: "IBM Plex Sans Condensed", "Arial Narrow", "Helvetica Neue", Arial, sans-serif;
  --f-body: "Source Sans 3", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  --f-mono: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ground: #10151c;
    --ground-2: #19202a;
    --paper: #161d26;
    --ink: #e4e9ef;
    --ink-2: #c1cad5;
    --muted: #93a0b0;
    --rule: #2c3644;
    --deployed: #cfd7e1;
    --inflight: #e3a84e;
    --inflight-soft: #2e2415;
    --designed: #86aef0;
    --designed-soft: #1a2638;
    --warn: #ec8a74;
    --warn-soft: #33201c;
  }
}
:root[data-theme="dark"] {
  --ground: #10151c;
  --ground-2: #19202a;
  --paper: #161d26;
  --ink: #e4e9ef;
  --ink-2: #c1cad5;
  --muted: #93a0b0;
  --rule: #2c3644;
  --deployed: #cfd7e1;
  --inflight: #e3a84e;
  --inflight-soft: #2e2415;
  --designed: #86aef0;
  --designed-soft: #1a2638;
  --warn: #ec8a74;
  --warn-soft: #33201c;
}

* { box-sizing: border-box; }
body {
  background: var(--ground);
  color: var(--ink);
  font-family: var(--f-body);
  font-size: 16px;
  line-height: 1.55;
  padding-inline: 20px;
  padding-block: 0 64px;
}
.shell {
  max-width: 1180px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 190px minmax(0, 1fr);
  gap: 48px;
}
nav.index {
  position: sticky;
  top: 0;
  align-self: start;
  padding-block: 40px 16px;
  font-family: var(--f-head);
}
nav.index .doc-id {
  font-family: var(--f-mono);
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 0.02em;
  margin-bottom: 14px;
}
nav.index ol { list-style: none; margin: 0; padding: 0; display: grid; gap: 2px; }
nav.index a {
  display: grid;
  grid-template-columns: 22px 1fr;
  gap: 6px;
  padding: 5px 8px;
  border-radius: 4px;
  color: var(--ink-2);
  text-decoration: none;
  font-size: 14.5px;
  line-height: 1.25;
}
nav.index a span { font-variant-numeric: tabular-nums; color: var(--muted); }
nav.index a:hover { background: var(--ground-2); color: var(--ink); }
nav.index a:focus-visible, a:focus-visible { outline: 2px solid var(--designed); outline-offset: 2px; }

main { min-width: 0; padding-block: 40px 0; }
header.top { max-width: 72ch; margin-bottom: 36px; }
.eyebrow {
  font-family: var(--f-mono);
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
}
h1 {
  font-family: var(--f-head);
  font-weight: 700;
  font-size: clamp(2rem, 4vw, 2.75rem);
  line-height: 1.05;
  letter-spacing: -0.01em;
  margin: 8px 0 14px;
  text-wrap: balance;
}
.lede { font-size: 18px; color: var(--ink-2); margin: 0; }

section { margin-top: 56px; scroll-margin-top: 16px; }
h2 {
  font-family: var(--f-head);
  font-weight: 600;
  font-size: 26px;
  line-height: 1.15;
  margin: 0 0 6px;
  display: flex;
  gap: 12px;
  align-items: baseline;
  flex-wrap: wrap;
  text-wrap: balance;
}
h2 .num {
  font-family: var(--f-mono);
  font-size: 15px;
  font-weight: 600;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
h3 {
  font-family: var(--f-head);
  font-weight: 600;
  font-size: 18px;
  margin: 28px 0 8px;
}
.prose { max-width: 72ch; }
.prose p { margin: 0 0 12px; }
.prose ul { margin: 0 0 12px; padding-left: 20px; }
.prose li { margin-bottom: 4px; }
code, .mono {
  font-family: var(--f-mono);
  font-size: 0.86em;
  background: var(--ground-2);
  padding: 1px 5px;
  border-radius: 3px;
  overflow-wrap: anywhere;
}
td code, .chip code { background: transparent; padding: 0; }

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--f-mono);
  font-size: 11.5px;
  line-height: 1;
  padding: 4px 8px;
  border-radius: 3px;
  white-space: nowrap;
  vertical-align: 2px;
}
.chip.deployed { border: 1.5px solid var(--deployed); color: var(--deployed); }
.chip.inflight { border: 1.5px dashed var(--inflight); color: var(--inflight); background: var(--inflight-soft); }
.chip.designed { border: 1.5px dotted var(--designed); color: var(--designed); background: var(--designed-soft); }
.chip.hot { border: 1.5px solid var(--warn); color: var(--warn); background: var(--warn-soft); }
.chip.done { border: 1.5px solid var(--deployed); color: var(--paper); background: var(--deployed); }

.legend { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 10px 20px; margin-top: 22px; padding: 14px 16px; background: var(--paper); border: 1px solid var(--rule); border-radius: 6px; max-width: 900px; }
.legend div { display: grid; grid-template-columns: 74px 1fr; gap: 10px; align-items: center; font-size: 14px; color: var(--ink-2); }
.legend svg { width: 74px; height: 30px; display: block; color: var(--muted); }
.legend b { font-family: var(--f-head); font-weight: 600; color: var(--ink); }

.states {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0;
  border: 1px solid var(--rule);
  background: var(--paper);
  border-radius: 6px;
  margin-top: 18px;
}
.state { padding: 18px 20px 20px; display: grid; gap: 8px; align-content: start; }
.state + .state { border-left: 1px solid var(--rule); }
.state h4 { margin: 0; font-family: var(--f-head); font-size: 17px; font-weight: 600; }
.state p { margin: 0; font-size: 15px; color: var(--ink-2); }
.state dl { margin: 4px 0 0; display: grid; grid-template-columns: auto 1fr; gap: 3px 12px; font-size: 14px; }
.state dt { color: var(--muted); }
.state dd { margin: 0; font-family: var(--f-mono); font-size: 12.5px; font-variant-numeric: tabular-nums; }

figure {
  margin: 20px 0 0;
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: 6px;
  padding: 16px 16px 12px;
}
.fig-scroll { overflow-x: auto; }
figure svg { display: block; width: 100%; min-width: 760px; height: auto; color: var(--muted); }
figcaption {
  margin-top: 10px;
  font-size: 14.5px;
  color: var(--ink-2);
  max-width: 90ch;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: baseline;
}
figcaption .chip { flex: none; }

/* SVG vocabulary: one encoding for code state across every figure */
svg .n { fill: var(--paper); stroke: var(--deployed); stroke-width: 1.4; }
svg .n-inflight { fill: var(--inflight-soft); stroke: var(--inflight); stroke-width: 1.6; stroke-dasharray: 6 4; }
svg .n-designed { fill: var(--designed-soft); stroke: var(--designed); stroke-width: 1.6; stroke-dasharray: 2 3; }
svg .n-hot { fill: var(--warn-soft); stroke: var(--warn); stroke-width: 2; }
svg .ext { fill: var(--ground-2); stroke: var(--muted); stroke-width: 1.2; }
svg .strip { fill: var(--ground-2); stroke: none; }
svg .frame { fill: none; stroke: var(--muted); stroke-width: 1; stroke-dasharray: 3 3; }
svg .life { stroke: var(--rule); stroke-width: 1.2; stroke-dasharray: 4 4; }
svg .e { stroke: currentColor; stroke-width: 1.4; fill: none; }
svg .e-ret { stroke: currentColor; stroke-width: 1.2; fill: none; stroke-dasharray: 5 4; }
svg .e-hot { stroke: var(--warn); stroke-width: 1.4; fill: none; stroke-dasharray: 5 4; }
svg .e-designed { stroke: var(--designed); stroke-width: 1.4; fill: none; }
svg text { font-family: var(--f-body); fill: var(--ink); }
svg .t { font-family: var(--f-mono); font-size: 13px; font-weight: 600; }
svg .ts { font-family: var(--f-mono); font-size: 12px; font-weight: 600; }
svg .tl { font-size: 12px; fill: var(--muted); }
svg .tm { font-family: var(--f-mono); font-size: 11.5px; fill: var(--ink-2); }
svg .tb { font-size: 12.5px; fill: var(--ink-2); }
svg .th { font-family: var(--f-head); font-size: 15px; font-weight: 600; }
svg .halo { paint-order: stroke; stroke: var(--paper); stroke-width: 5px; stroke-linejoin: round; }
svg .t-inflight { fill: var(--inflight); }
svg .t-designed { fill: var(--designed); }
svg .t-warn { fill: var(--warn); }

.table-wrap { overflow-x: auto; margin-top: 16px; border: 1px solid var(--rule); border-radius: 6px; background: var(--paper); }
table { border-collapse: collapse; width: 100%; min-width: 860px; font-size: 14.5px; }
th, td { text-align: left; vertical-align: top; padding: 10px 14px; border-bottom: 1px solid var(--rule); }
tr:last-child td { border-bottom: none; }
thead th {
  font-family: var(--f-head);
  font-weight: 600;
  font-size: 14px;
  background: var(--ground-2);
  position: sticky;
  top: 0;
}
thead th .chip { margin-left: 4px; }
tbody th { font-family: var(--f-head); font-weight: 600; font-size: 15px; width: 13%; }
td.why { color: var(--ink-2); font-size: 14px; }
td .tag {
  display: inline-block;
  font-family: var(--f-mono);
  font-size: 11px;
  color: var(--muted);
  margin-right: 6px;
  font-variant-numeric: tabular-nums;
}
.roadmap td:first-child { font-family: var(--f-mono); font-weight: 600; white-space: nowrap; font-variant-numeric: tabular-nums; }
.roadmap td:nth-child(3) { white-space: nowrap; }

.obs { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 14px; }
.obs div { background: var(--paper); border: 1px solid var(--rule); border-radius: 6px; padding: 12px 14px; font-size: 14.5px; }
.obs b { font-family: var(--f-head); font-weight: 600; display: block; font-size: 15px; margin-bottom: 2px; }
.obs .loc { font-family: var(--f-mono); font-size: 11.5px; color: var(--muted); display: block; margin-top: 6px; }

.decisions { list-style: none; margin: 16px 0 0; padding: 0; display: grid; gap: 10px; max-width: 90ch; }
.decisions li {
  display: grid;
  grid-template-columns: 52px 1fr;
  gap: 14px;
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: 6px;
  padding: 14px 16px;
}
.decisions .did { font-family: var(--f-mono); font-size: 13px; font-weight: 600; color: var(--muted); padding-top: 2px; }
.decisions h4 { margin: 0 0 4px; font-family: var(--f-head); font-weight: 600; font-size: 16.5px; }
.decisions p { margin: 0; font-size: 15px; color: var(--ink-2); }
.decisions .src { font-family: var(--f-mono); font-size: 11.5px; color: var(--muted); margin-top: 6px; }

footer.src-list { margin-top: 56px; font-size: 13.5px; color: var(--muted); max-width: 90ch; border-top: 1px solid var(--rule); padding-top: 16px; }
footer.src-list code { font-size: 12px; }

@media (max-width: 900px) {
  .shell { grid-template-columns: minmax(0, 1fr); gap: 0; }
  nav.index { position: static; padding-block: 24px 0; }
  nav.index ol { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  main { padding-block: 20px 0; }
  .states { grid-template-columns: minmax(0, 1fr); }
  .state + .state { border-left: none; border-top: 1px solid var(--rule); }
  .obs { grid-template-columns: minmax(0, 1fr); }
}
@media (max-width: 480px) {
  body { padding-inline: 16px; }
  nav.index ol { grid-template-columns: minmax(0, 1fr); }
  .decisions li { grid-template-columns: minmax(0, 1fr); gap: 4px; }
}
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
html { scroll-behavior: smooth; }
```

## Skeleton

```html
<title>SUBJECT</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=JetBrains+Mono:wght@400;600&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&display=swap">
<style>/* the stylesheet above */</style>
<div class="shell">
  <nav class="index" aria-label="Sections">
    <div class="doc-id">SUBJECT · DATE</div>
    <ol>
      <li><a href="#s1"><span>1</span>Three states of the code</a></li>
      <!-- 2–5 as present -->
      <li><a href="#s6"><span>6</span>Where they disagree</a></li>
      <li><a href="#s7"><span>7</span>Migration roadmap</a></li>
      <li><a href="#s8"><span>8</span>Open decisions</a></li>
      <li><a href="#s9"><span>9</span>Where the code departs from the specification</a></li>
    </ol>
  </nav>
  <main>
    <header class="top">
      <div class="eyebrow">Architecture review · WHAT IS REVIEWED · WHAT IS OUT OF SCOPE</div>
      <h1>SUBJECT</h1>
      <p class="lede">ONE SENTENCE: the three states and where each lives.</p>
    </header>
    <svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs><marker id="arL" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L8,4 L0,8 z" fill="currentColor"/></marker></defs></svg>
    <div class="legend" aria-label="Legend">
      <div><svg viewBox="0 0 74 30"><rect class="n" x="2" y="3" width="70" height="24" rx="4"/></svg><span><b>deployed</b> · BRANCH, COMMIT</span></div>
      <div><svg viewBox="0 0 74 30"><rect class="n-inflight" x="2" y="3" width="70" height="24" rx="4"/></svg><span><b>in flight</b> · BRANCH OR WORKTREE, COMMIT, or "none"</span></div>
      <div><svg viewBox="0 0 74 30"><rect class="n-designed" x="2" y="3" width="70" height="24" rx="4"/></svg><span><b>designed</b> · in DOCUMENTS only</span></div>
      <div><svg viewBox="0 0 74 30"><rect class="n-hot" x="2" y="3" width="70" height="24" rx="4"/></svg><span><b>attention</b> · a module carrying too much, a coupling to remove, or a step waiting on a decision</span></div>
      <div><svg viewBox="0 0 74 30"><rect class="ext" x="2" y="3" width="70" height="24" rx="12"/></svg><span><b>external</b> · a system we do not own</span></div>
      <div><svg viewBox="0 0 74 30"><line class="e" x1="4" y1="10" x2="66" y2="10" marker-end="url(#arL)"/><line class="e-ret" x1="66" y1="22" x2="8" y2="22" marker-end="url(#arL)"/></svg><span><b>arrows</b> · solid is a call or import, dashed is a return</span></div>
    </div>

    <section id="s1">
      <h2><span class="num">1</span>Three states of the code</h2>
      <div class="prose"><p>Every figure and table row below is tagged with the state it describes; the legend above applies to all of them.</p></div>
      <div class="states">
        <div class="state"><h4><span class="chip deployed">deployed</span></h4><p>ONE SENTENCE</p><dl><dt>commit</dt><dd>HASH</dd><dt>FILE</dt><dd>N lines</dd></dl></div>
        <div class="state"><h4><span class="chip inflight">in flight</span></h4><p>ONE SENTENCE, or "None."</p><dl>…</dl></div>
        <div class="state"><h4><span class="chip designed">designed</span></h4><p>ONE SENTENCE</p><dl>…</dl></div>
      </div>
    </section>

    <section id="s2">
      <h2><span class="num">2</span>Module map, as built <span class="chip deployed">deployed HASH</span></h2>
      <div class="prose"><p>ONE OR TWO SENTENCES</p></div>
      <figure>
        <div class="fig-scroll"><svg viewBox="0 0 960 400" role="img" aria-label="ONE SENTENCE">…</svg></div>
        <figcaption><span class="chip deployed">deployed</span><span>WHAT IS NOT DRAWN</span></figcaption>
      </figure>
    </section>

    <section id="s6">
      <h2><span class="num">6</span>Where they disagree</h2>
      <div class="prose"><p>ONE SENTENCE</p></div>
      <div class="table-wrap"><table>
        <thead><tr><th scope="col">Topic</th><th scope="col">Deployed <span class="chip deployed">built</span></th><th scope="col">Designed <span class="chip designed">designed</span></th><th scope="col">What it decides</th></tr></thead>
        <tbody><tr><th scope="row"><span class="tag">6.1</span>TOPIC</th><td>…</td><td>…</td><td class="why">ONE SENTENCE</td></tr></tbody>
      </table></div>
    </section>

    <section id="s7">
      <h2><span class="num">7</span>Migration roadmap</h2>
      <div class="table-wrap"><table class="roadmap">
        <thead><tr><th scope="col">#</th><th scope="col">Step</th><th scope="col">Status</th><th scope="col">Green when</th></tr></thead>
        <tbody><tr><td>1</td><td>…</td><td><span class="chip hot">waiting on 8.1</span></td><td>…</td></tr></tbody>
      </table></div>
    </section>

    <section id="s8">
      <h2><span class="num">8</span>Open decisions</h2>
      <ol class="decisions">
        <li><span class="did">8.1</span><div><h4>TITLE</h4><p>THE CHOICE AND WHAT EACH SIDE COSTS</p><div class="src">6.1 · FILE:LINE · DOCUMENT §N</div></div></li>
      </ol>
    </section>

    <section id="s9">
      <h2><span class="num">9</span>Where the code departs from the specification</h2>
      <div class="prose"><p>ONE SENTENCE: which document was graded against, and at which commit.</p></div>
      <div class="table-wrap"><table>
        <thead><tr><th scope="col">#</th><th scope="col">Section</th><th scope="col">Severity</th><th scope="col">Specified</th><th scope="col">Built</th><th scope="col">Where</th></tr></thead>
        <tbody><tr><th scope="row"><span class="tag">9.1</span>§N</th><td>TOPIC</td><td><span class="chip hot">high</span></td><td>WHAT THE DOCUMENT SAYS</td><td>WHAT THE CODE DOES</td><td><code>FILE:LINE</code></td></tr></tbody>
      </table></div>
    </section>

    <footer class="src-list">Built DATE HH:MM TZ from: COMMIT on BRANCH; WORKTREE at COMMIT; DOCUMENTS.</footer>
  </main>
</div>
```
