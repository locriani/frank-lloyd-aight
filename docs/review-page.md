# The review page

The page Frank Lloyd AIght writes when the user asks for a review of the existing architecture. One HTML file, served when the workspace has a publisher, and then the user discusses it by section number. This document fixes the layout, the numbering, and the encoding so that every review looks the same and section 6 means the same thing next week.

## File and address

- Path: `<pages dir>/<subject>-review.html` when the `## Architecture` block names a pages dir; otherwise `<review dir>/<subject>-review.html`. The subject is the project's name: the block's `Project:` line when it has one, otherwise the name of the session's working directory, and then the reply says in one line that the name came from the directory because the block has no `Project:` line. When only a part is reviewed, the part follows the project (`ledger-api-review.html`). The subject is never a generic noun on its own (`architecture-review.html`, `agent-review.html`, `api-review.html`): a pages dir is shared between projects, and a generic name is sooner or later another project's page. Read a page that already exists before writing into it. Whose it is depends on its content, never on its name: a page about another project is never written into or over, whatever the user called the page they asked for. Write this project's page at its own name, and say in one line which page was left alone and why. A page of this project's own under a generic name is not updated either: the review goes to the page with the project's name, and the reply says the older page is still there.
- If the block names a URL where the pages dir is served, the page address is `<url>/<subject>-review.html`. Writing the file alone does not establish that a server is running. Without a served URL, give the file path and say the page is not served. Never paste the HTML into the reply.
- `<title>` is the subject. No external script. Fonts: the stylesheet in `docs/page-theme.css` names Google fonts with a system fallback stack; the page renders without them.
- Light and dark: the tokens in `docs/page-theme.css` define the light palette on `:root`, redefine it under `prefers-color-scheme: dark` guarded as `:root:not([data-theme="light"])`, and again under `:root[data-theme="dark"]`. Keep all three blocks.
- Phone width: one column under 900px, 16px side gutter under 480px. Figures and tables scroll sideways inside their own wrapper; the body never does.
- Width: nothing caps it. No `max-width` on the shell, the prose, or any other block, in pixels, characters or ems, so text runs the width of the window. In the page source a paragraph is one line: never break a line inside a sentence, because the browser lays the text out.

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
| 9 | Where the code departs from the specification | `div.table-wrap > table`: columns #, Section, Severity, Specified, Built, Where. Rows `<th scope="row"><span class="tag">9.N</span>§M</th>`, then the severity as `<span class="chip hot">high</span>` for a gap that breaks what the section exists to guarantee and plain text otherwise, one sentence of what the document specifies, one of what the code does, and `file:line`. Always present: with nothing to report it reads "No gaps: every section of the specification that is not left out below is met by the code as built." A section left out as stale has one line of `p.note` under the table: `§N is not a row: DECISION (FILE:LINE) records that its claim was dropped.` |

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
- Section 9 carries **code defects only**: the document specifies something and the code does not do it. A document that has gone stale — it describes what was built once, or what was planned and never built — is not a compliance gap, and belongs in section 6 with the other disagreements, and in section 8 if it needs settling. The specification is the fixed point; a section 9 row says the code is wrong, and saying that about a stale document launders the defect. The test, before a row is written: is there a decision recorded in the architecture directory, with its file and line, that the document's claim was dropped or changed? Then the document went stale and the section gets no row, however large the difference. Code that states the difference as its design corroborates such a decision and is never enough alone, because the code is what is graded. Every other difference is a row, wording that can be read two ways included (the row says which reading was taken). One line under the table names each section left out and the decision that took it out.

## The reply after writing

The page's URL or file path on the first line, then the section list with numbers (one line each, written `N. Title`, never `- N: Title`), then the one sentence from section 6 that matters most, and the count of section 9's rows when it is not zero ("9: three gaps"). State when the file is not served. No recommendation, no question. The user reads, then discusses by number.

## Stylesheet

The stylesheet is the file `docs/page-theme.css` in this plugin (`${CLAUDE_PLUGIN_ROOT}/docs/page-theme.css`). Read it and put it in the page's `<style>` whole.

Do not restyle, because a review that looks different reads as a different kind of document.

The file also carries the plan page's components.

## Skeleton

```html
<title>SUBJECT</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=JetBrains+Mono:wght@400;600&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&display=swap">
<style>/* the whole of docs/page-theme.css */</style>
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
      <p class="note">§N is not a row: DECISION (FILE:LINE) records that its claim was dropped. (Only when a section was left out.)</p>
    </section>

    <footer class="src-list">Built DATE HH:MM TZ from: COMMIT on BRANCH; WORKTREE at COMMIT; DOCUMENTS.</footer>
  </main>
</div>
```
