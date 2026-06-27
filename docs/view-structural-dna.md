# View Structural DNA — How One Substrate Renders as Genuinely Different Documents

**Purpose.** This document defines the *structural* grammar of each report **view** so that two views built from the **same Substrate** read as different artifacts — not the same report recolored. The prior attempt failed precisely because the three designs were "the same report, just different colors." Color is OUT of scope here: all views share the NowPage house system (cream `#EDE8DF` + ink `#1A1612` + amber `#B85C18`, Bebas Neue / DM Sans / DM Mono). The difference between views is **layout, density, component mix, and which Substrate fields they foreground vs. suppress.**

> A view is a **pure function of the Substrate**. Per `substrate.py`: "a view is a pure function of substrate fields. A visual view pulls `diagrams`/`metrics`; a dense view pulls `sections`/tables; a decision brief pulls `verdict` + top findings." This file makes that function concrete and prescriptive.

---

## The Substrate Contract (what views consume)

From `strategy_factory/substrate.py`, the `Substrate` exposes these foreground-able fields:

| Field | Type | What it carries | Which view is built FOR it |
|---|---|---|---|
| `meta` | `SubstrateMeta` | subject name/type, report type, models, cost, timestamp | (cover/footer of all) |
| `brand` | `Brand` | name, title, accent override, logo, seed_url | (L5 reskin — all) |
| `entity` | `EntityResolution` | match status, confidence, evidence, **blocking** | gate (all); surfaced as a trust chip in C |
| `profile_summary` | `str` | ≤600-char subject description | A (lead-in), C (one-liner) |
| `industry` | `str` | primary industry label | A, B |
| `sections[]` | `List[Section]` | id, order, **kicker**, title, `body_md` (tables inline), `severity` | **A foregrounds** (the dense one) |
| `diagrams[]` | `List[Diagram]` | id, title, kind, source, valid | **B foregrounds** (the visual one) |
| `metrics[]` | `List[Metric]` | label, value, unit, source | A (stat band) + B (big-number nodes) |
| `citations[]` | `List[Citation]` | url, source, claim | A foregrounds (sources appendix + footnotes); C suppresses to a count |
| `verdict` | `str` | go/no-go decision-brief headline | **C foregrounds** (verdict-first) |

The three reference HTML pages map onto this contract as follows:
- `nowpage-deloitte-v2.html` → **View A — Consulting Dossier** (consulting/data treatment)
- `nowpage-zeus-jones-v1.html` → **View B — Visual Briefing** (editorial/diagram treatment)
- `nowpage-sales-validation-v1.html` → **View C — Decision Brief** (conversion/scannable treatment)

---

## View A — Consulting Dossier
*(reference: `nowpage-deloitte-v2.html` — the consulting/data treatment)*

### Foreground / Suppress
- **Foregrounds:** `sections[]` (every one, in `order`), the inline tables inside `body_md`, `metrics[]` (as stat bands AND table cells), `citations[]` (footnote superscripts + a full Sources & Methodology appendix), `severity` (rendered as risk pills).
- **Suppresses:** nothing — this is the maximal view. `diagrams[]` are demoted to small inline figures (value-chain strip, scorecard bars) rather than hero objects. `verdict` is buried inside the Executive Summary rather than standing alone.

### Structural signature
- **Section count:** HIGH — 12 numbered sections + Executive Summary + 2 appendices (Decisions, Sources). ~15 distinct `<Section>` blocks.
- **Section opener:** `Section NN` mono kicker → Bebas heading → DM Sans subtitle. Alternates `white` / `ink (dark)` background per section to chunk a long scroll.
- **Diagram-load:** LOW-MEDIUM (diagrams are supporting, not the point).
- **Density:** VERY HIGH (text-heavy + table-heavy). `font-size:15px`, `max-width:1000px` content column (widest of the three).
- **Target length:** ~3,500–5,000 words. The longest artifact. Designed to be *referenced*, not read in one sitting.

### Component mix (the dense kit)
`AnimatedStat` counters (stat bands) · `DataTable` (the workhorse — TAM tables, feature-comparison matrices, margin tables, financial scenarios) · `Matrix2x2` (positioning quadrants) · `StrengthBar` (scorecards) · `Tabs` (Top-Down / Bottom-Up / Growth Drivers — lets one section hold 3 datasets) · `Expandable` (technical deep-dives, pricing options, risks) · `RiskCell` pills (severity) · `TimelineItem` (phased roadmap) · `PricingCard` ×4 tiers · `Insight` callouts · footnote `Fn` refs → Sources appendix.

### When to choose it
When the reader is an analyst, investor, or operator who will **scrutinize the evidence** and wants every claim sourced. When the Substrate is rich (`sections` ≥ 8, `citations` ≥ 10, `metrics` ≥ 6). When the report's job is **defensible completeness**, not a fast yes/no.

---

## View B — Visual Briefing
*(reference: `nowpage-zeus-jones-v1.html` — the editorial/diagram treatment)*

### Foreground / Suppress
- **Foregrounds:** `diagrams[]` as **hero objects** (flywheel, positioning map), `metrics[]` as large standalone numbers inside diagram nodes, a SMALL curated set of `sections[]` (one idea per section), the framework spine (`Section` titles → a label/value framework grid).
- **Suppresses:** `citations[]` (no footnotes, no sources appendix — claims are asserted, not foot­noted), dense `DataTable`s (only ONE editorial 2-col "Never/Always" table appears), and most `body_md` prose is cut to a `lead` paragraph + card grid.

### Structural signature
- **Section count:** MEDIUM — ~9 sections, each a single concept (Thesis, Audit, Tensions, Positioning, Flywheel, Map, Voice, Growth, Recs).
- **Section opener:** `Section 0N` Bebas kicker → oversized Bebas `h2` (`clamp(36px,5vw,56px)`) → one `lead` paragraph. Generous whitespace; one big idea per scroll-screen.
- **Diagram-load:** HIGH — this is the only view with a **hand-built flywheel** (5 nodes on a ring) and a **custom positioning map** (x/y axes, zones, dots). Diagrams ARE the content.
- **Density:** LOW / whitespace-forward. `font-size:17px` (largest body), `line-height:1.7`, `max-width:900px`. Fewer words per section than A by ~3×.
- **Target length:** ~1,200–1,800 words. Read top-to-bottom in one pass.

### Component mix (the visual kit)
Flywheel (circular `diagram`) · positioning map (2-axis `diagram` with zones) · `framework-grid` (label → value spine, the "positioning architecture") · `card-grid` of principle/tension cards · ONE editorial 2-column voice table · `growth-priority` bars · `rec-card`s · `tension-card`s · oversized pull-quote footer. No counters-as-dashboards, no footnotes, no expandables.

### When to choose it
When the reader is an **executive or partner being briefed**, not audited — they want the *shape* of the argument fast. When the Substrate has strong `diagrams[]` (≥ 2 valid) and a clear narrative spine. When the report's job is **persuasion-by-clarity / memorability**, and citation rigor can live in a linked companion (View A).

---

## View C — Decision Brief
*(reference: `nowpage-sales-validation-v1.html` — the conversion/scannable treatment)*

### Foreground / Suppress
- **Foregrounds:** `verdict` as the **hero headline** (the whole page is organized around one decision), the top 3–5 `metrics[]` as a proof band, `entity` confidence as a trust chip ("0% hallucination / verified"), a linear `Step`/`TimelineItem` spine, ONE decision table (the pricing/tier escalation), and a single conversion `form`.
- **Suppresses:** the long tail of `sections[]` (only the load-bearing 6–9 are kept, each compressed to a `Step` or `Callout`), `citations[]` (collapsed to a count / "verified" claim, no appendix), and complex `diagrams[]` (replaced by ONE simple horizontal pipeline strip).

### Structural signature
- **Section count:** MEDIUM-LOW — ~9 short sections, each ending in a forward push (callout or CTA). Sections are *beats in an argument toward a decision*, not chapters.
- **Section opener:** pill-style `NN` chip + uppercase Bebas label → `h2` (`clamp(32px,5vw,46px)`) → short framing line. Tighter rhythm than B; momentum-driven.
- **Diagram-load:** LOW — one horizontal pipeline (`Transcript → Analysis → Verification → Generation → Live URL`). No flywheels, no maps.
- **Density:** MEDIUM, but *scannable* — short paragraphs, big stat row, lots of single-line `Rule`/`AntiItem` lists. `font-size:15–16px`, `max-width:860px` (narrowest). Animated scarcity counter for urgency.
- **Target length:** ~1,000–1,500 words, but front-loaded — the decision is legible in the **first screen** (hero verdict + stat band). It's a one-pager in spirit even when it scrolls.

### Component mix (the conversion kit)
Hero `verdict` block + animated scarcity counter · `Stat` proof row (100% verified / 4 layers / <60s / 0% hallucination) · horizontal `pipeline` strip · numbered `Step` list (how it works) · `Rule` list + `AntiItem` ("who this is NOT for") · ONE decision/pricing `table` with status states · `Callout` italic pull-quotes · live `form` (FormInput + select + submit + success state). No matrices, no scorecards, no footnotes, no expandables.

### When to choose it
When the reader must make **one call now** (go/no-go, buy/skip, shortlist/drop) and wants the answer first with just enough proof to trust it. When `verdict` is populated and non-trivial. When the report's job is **a decision or an action**, not a reference document.

---

## View D — "Traditional" *(PENDING — reference from Jason: "Mark's")*

> **SLOT RESERVED.** Jason will supply a reference artifact ("Mark's" traditional report). Do not invent its structure. When the reference arrives, fill the same spec used above. Provisional hypothesis only (to be confirmed/overwritten by the real reference):

- **Likely foreground:** `sections[]` in linear order with conventional report furniture — title page, table of contents, numbered headings, prose body, a conclusion, references. Probably citation-bearing like A but **without** the dashboard/matrix instrumentation.
- **Likely structural signature (UNCONFIRMED):** linear single-column document; section opener = number + plain heading (no mono kicker, no dark/light alternation); diagram-load LOW; density MEDIUM-HIGH prose; length unknown.
- **Likely component mix (UNCONFIRMED):** running prose, simple tables, a contents list, footnotes/endnotes, an executive summary box. Few-to-no interactive components (no tabs, no expandables, no animated counters).
- **Distinguishing axis vs A/B/C (HYPOTHESIS):** "Traditional" likely differs by being **document-paginated and print-like** (TOC + page rhythm) rather than scroll-instrumented — i.e., it competes with A on completeness but trades A's dashboard density for conventional report formality.

**TODO when reference lands:** capture (1) does it paginate / have a TOC? (2) section opener convention, (3) diagram-load, (4) prose density + target length, (5) exact component list, (6) which Substrate fields it foregrounds/suppresses, (7) the one axis that makes it visibly NOT View A.

---

## Comparison Matrix (view × structural dimension)

| Structural dimension | **A — Consulting Dossier** | **B — Visual Briefing** | **C — Decision Brief** | **D — Traditional (pending)** |
|---|---|---|---|---|
| **Reference file** | `nowpage-deloitte-v2.html` | `nowpage-zeus-jones-v1.html` | `nowpage-sales-validation-v1.html` | TBD ("Mark's") |
| **Substrate field foregrounded** | `sections[]` + tables + `citations[]` | `diagrams[]` + `metrics[]` | `verdict` + top `metrics[]` | `sections[]` (prose) *(hyp.)* |
| **Substrate field suppressed** | none (maximal) | `citations[]`, dense tables | long-tail `sections[]`, `citations[]` | dashboards/instrumentation *(hyp.)* |
| **Section count** | HIGH (~15) | MEDIUM (~9) | MED-LOW (~9 beats) | TBD |
| **Section opener** | `Section NN` mono kicker, dark/light alternation | Bebas `0N` + oversized h2 + lead | pill chip + uppercase label, momentum rhythm | number + plain heading *(hyp.)* |
| **Diagram-load** | LOW-MED (supporting) | **HIGH** (flywheel + map = the content) | LOW (1 pipeline strip) | LOW *(hyp.)* |
| **Density** | **VERY HIGH** (text + table) | **LOW** / whitespace-forward | MEDIUM but scannable | MED-HIGH prose *(hyp.)* |
| **Body font size / column** | 15px / 1000px (widest) | 17px / 900px | 15–16px / 860px (narrowest) | TBD |
| **Signature components** | DataTable, Matrix2x2, StrengthBar, Tabs, Expandable, RiskCell, PricingCard, Fn footnotes | Flywheel, positioning map, framework-grid, card-grid, 2-col voice table | hero verdict, scarcity counter, Stat row, pipeline strip, Step/Rule/AntiItem lists, form | TOC, prose, endnotes *(hyp.)* |
| **Target length** | 3,500–5,000 w | 1,200–1,800 w | 1,000–1,500 w (front-loaded) | TBD |
| **Reading mode** | reference / scrutinize | brief / one pass | decide / first-screen | read-through *(hyp.)* |
| **Report's job** | defensible completeness | persuasion-by-clarity | a decision / an action | conventional formality *(hyp.)* |
| **Choose when reader is** | analyst / investor | executive being briefed | decision-maker acting now | reader expecting a "normal report" |

---

## The Anti-Recolor Test (acceptance criteria)

Two views built from the **same Substrate** pass only if, with color stripped to greyscale, a reader can still tell them apart by structure alone:

1. **Field-foreground divergence:** A shows a *Sources appendix*; B shows a *flywheel*; C shows a *verdict headline + form*. These objects come from **different Substrate fields** (`citations` vs `diagrams` vs `verdict`) — so they cannot exist in all three. If all three show the same hero object, the views collapsed into recolors. ❌
2. **Section-count divergence:** A has ~15 sections; B and C have ~9 but B is one-idea-per-screen (low density) while C is momentum-beats (forward CTAs). Counting sections and measuring words-per-section must yield three different profiles.
3. **Diagram-load divergence:** exactly one view (B) treats `diagrams[]` as hero. A and D demote them; C replaces them with a single strip.
4. **Component-kit disjointness:** the signature component of each view (A: `DataTable`+`Matrix2x2`; B: flywheel+map; C: scarcity counter+form) must NOT appear in the others. Shared atoms (Bebas headings, amber divider) are fine; shared *load-bearing components* are the failure mode.
5. **First-screen test:** A's first screen = stat dashboard; B's = a thesis + card grid; C's = the verdict. If the first screen is interchangeable across views, they are recolors. ❌

A build that satisfies 1–5 produces three documents that look structurally distinct even in black and white — which is the whole point of the Substrate-to-view architecture.
