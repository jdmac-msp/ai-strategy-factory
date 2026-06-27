# Expert Intelligence Brief — Report-Type Spec

> Reverse-engineered from Jason MacDonald's $1,500 "Expert Intelligence Brief"
> (https://jasondmacdonald.com/intelligence-brief) into a second `report_type`
> for the ai-strategy-factory engine.
>
> **Identity:** `subject_type = SubjectType.EXPERT`, `report_type = ReportType.INTELLIGENCE_BRIEF`
> (both already exist in `strategy_factory/substrate.py`).
>
> **Subject is a PERSON/brand**, not a company. The deliverable is the same
> Substrate → view → brand → publish pipeline, but the *rubric* feeding the
> Substrate is the 5-module expert IP analysis below, and one module
> (Partnership Viability Score) populates `Substrate.verdict` with a go/no-go.
>
> Source product = 5 modules: (1) IP Extraction Map, (2) Monetization Gap
> Analysis, (3) AI Deployment Blueprint, (4) Competitive Landscape,
> (5) Partnership Viability Score. Deliverable = branded interactive HTML brief,
> 48–72h turnaround.

---

## 0. How this wires into the engine (orientation)

The engine has three stages that map to the Substrate's L1→L2 flow:

1. **Research (Perplexity)** — `research/query_templates.py` renders a set of
   `QueryTemplate`s (category + recency + priority), `research/orchestrator.py`
   runs them, `research/result_processor.py` shapes them into `research_output`
   (the `profile / industry / competitors / tech_landscape / regulatory` nodes
   in `state.json`).
2. **Synthesis (Gemini)** — one prompt module per deliverable in
   `synthesis/prompts/*.py`, each a fixed section skeleton; `synthesis/context_builder.py`
   feeds the relevant research nodes + prior deliverables in as context.
3. **Substrate assembly** — `substrate.from_state()` reads `state.json` + the
   generated `markdown/*.md` into `Substrate(meta, brand, entity, sections,
   diagrams, metrics, citations, verdict)`. Views render purely off that.

To add `intelligence_brief` we add: (a) a subject-aware query set, (b) 5 synthesis
prompt modules, (c) a report-type-aware section ID list, and (d) a verdict
extractor for Module 5. **No Substrate schema change is required** — the contract
already carries `subject_type=expert`, `report_type=intelligence_brief`,
`severity`, and `verdict`.

---

## 1. Module → Substrate Section map

Each module becomes one `Section` (`substrate.py` `Section` model:
`id, order, kicker, title, body_md, severity`). Module 5 *also* writes
`Substrate.verdict` and exposes a `Metric` (projected revenue).

| # | Section `id` | `order` | `kicker` | `title` | Contains | `severity` / verdict |
|---|---|---|---|---|---|---|
| 01 | `ip_extraction_map` | 1 | `IP MAP` | IP Extraction Map | Methodology decomposed into modular components; unique-mechanism identification (the named, defensible "how"); per-component **extraction feasibility score** (how cleanly it can be deployed without the expert in the room). | `severity` per component = `high`/`med`/`low` extractability (reuse as a "deploy-readiness" flag) |
| 02 | `monetization_gap` | 2 | `GAP` | Monetization Gap Analysis | Current vs. potential revenue; **missing pricing tiers** (entry → mid → partnership/licensing); recurring-revenue pathways latent in existing IP. | `severity` = size of the gap (`high` = large unrealized revenue) |
| 03 | `ai_deployment_blueprint` | 3 | `DEPLOY` | AI Deployment Blueprint | Domain-tailored agent architecture; **automation candidates ranked by leverage impact**; build-vs-buy call per candidate. Pairs with a `Diagram` (agent architecture, mermaid). | `severity` optional (per-candidate leverage) |
| 04 | `competitive_landscape` | 4 | `MARKET` | Competitive Landscape | Positioning + pricing map of comparable experts/offers; **differentiation gaps available for capture**; market-timing assessment. | `severity` = vulnerability/urgency of each gap |
| 05 | `partnership_viability` | 5 | `VERDICT` | Partnership Viability Score | Viability score with **factor breakdown**; **revenue-projection model**; recommendation = one of `GO` / `DEVELOP` / `PASS`. | **Writes `Substrate.verdict`** (see §1.1); `severity = positive` on GO |

Optional 0th section `expert_profile` (`order: 0`, kicker `PROFILE`) carries the
resolved profile summary (mirrors how the strategy report opens with an exec
summary). It maps to `Substrate.profile_summary` rather than a numbered module.

### 1.1 Partnership Viability Score → `Substrate.verdict`

`Substrate.verdict` is a free-text decision headline. The synthesizer emits a
machine-parseable first line so the verdict extractor (a small post-synthesis
step, analogous to how `from_state` derives metrics) can populate it:

```
VERDICT: GO | score=82/100 | projected_12mo_revenue=$240,000 | confidence=high
```

- `verdict` string = that line (rendered by decision-brief views as the hero).
- Recommendation enum lives at the front: **`GO`** (pursue partnership now),
  **`DEVELOP`** (viable but needs IP/offer work first), **`PASS`** (no-go).
- Also emit two `Metric`s: `Metric(label="Viability score", value="82/100")`
  and `Metric(label="Projected 12-mo revenue", value="$240,000")` so visual
  views can pull them without parsing prose.
- `severity` on the section = `positive` for GO, `med` for DEVELOP, `high` for PASS
  (high = "stop / risk flag"), keeping the existing severity color semantics.

---

## 2. Research plan (Perplexity)

**Key difference from the strategy report:** the subject is a *person/brand*, so
queries seed off the expert's **name + site/handle + offer language**, not a
corporate registry. We add an `EXPERT_*` template group paralleling the existing
`COMPANY_*` group. Reuse the same `QueryTemplate` dataclass
(`name, category, template, recency_filter, priority, required_for_quick_mode`).
Add `QueryCategory` members: `EXPERT_PROFILE`, `EXPERT_IP`, `EXPERT_OFFERS`,
`EXPERT_AUDIENCE`, `EXPERT_COMPETITORS`, `EXPERT_MONETIZATION`.

Placeholders: `{expert_name}`, `{seed_domain}`, `{niche}` (their domain/topic),
`{handle}` (primary social handle), plus the existing temporal injectors.

### Per-module query set

**Profile / entity-resolution seed (always run first — feeds the gate):**

| name | category | template | recency | priority | quick |
|---|---|---|---|---|---|
| `expert_overview` | EXPERT_PROFILE | `{expert_name} {seed_domain} bio background expertise what they are known for {current_year}` | year | 1 | yes |
| `expert_presence` | EXPERT_PROFILE | `{expert_name} site:{seed_domain} OR {handle} podcast YouTube newsletter books speaking` | year | 1 | yes |

**Module 01 — IP Extraction Map:**

| name | category | template | recency | priority | quick |
|---|---|---|---|---|---|
| `expert_frameworks` | EXPERT_IP | `{expert_name} framework methodology model system named process signature approach` | year | 1 | yes |
| `expert_content_body` | EXPERT_IP | `{expert_name} {niche} core teachings book chapters course modules key concepts` | year | 2 | yes |
| `expert_unique_mechanism` | EXPERT_IP | `{expert_name} what makes their approach different proprietary unique mechanism vs generic {niche} advice` | year | 2 | no |

**Module 02 — Monetization Gap Analysis:**

| name | category | template | recency | priority | quick |
|---|---|---|---|---|---|
| `expert_offers` | EXPERT_OFFERS | `{expert_name} {seed_domain} products services pricing courses coaching consulting offer ladder` | year | 1 | yes |
| `expert_revenue_model` | EXPERT_MONETIZATION | `{expert_name} how they make money revenue streams subscription membership licensing` | year | 2 | no |
| `niche_pricing_benchmarks` | EXPERT_MONETIZATION | `{niche} expert coach consultant typical pricing tiers high-ticket recurring revenue models {current_year}` | year | 2 | yes |

**Module 03 — AI Deployment Blueprint:**

| name | category | template | recency | priority | quick |
|---|---|---|---|---|---|
| `niche_ai_automation` | AI_INITIATIVES | `{niche} AI agents automation use cases for solo experts coaches creators {current_year}` | month | 1 | yes |
| `expert_workflow_surface` | EXPERT_OFFERS | `{expert_name} delivery model how they deliver coaching content fulfillment workflow` | year | 2 | no |

**Module 04 — Competitive Landscape:**

| name | category | template | recency | priority | quick |
|---|---|---|---|---|---|
| `expert_competitors` | EXPERT_COMPETITORS | `{expert_name} alternatives similar experts {niche} thought leaders competitors who else teaches {niche}` | year | 1 | yes |
| `niche_positioning` | EXPERT_COMPETITORS | `{niche} market crowded saturated positioning differentiation white space gaps {current_year}` | month | 2 | yes |
| `competitor_pricing` | EXPERT_COMPETITORS | `top {niche} experts pricing offers programs how they package and price {current_year}` | year | 2 | no |

**Module 05 — Partnership Viability Score:**

| name | category | template | recency | priority | quick |
|---|---|---|---|---|---|
| `expert_audience_signal` | EXPERT_AUDIENCE | `{expert_name} audience size followers email list reach engagement {handle} {current_year}` | month | 1 | yes |
| `expert_traction` | EXPERT_AUDIENCE | `{expert_name} testimonials results case studies credibility proof recent {current_month_year}` | month | 2 | yes |

> Mode behaviour mirrors the strategy report: `quick` runs only
> `required_for_quick_mode=True`; `comprehensive` runs all + escalates to
> `sonar-deep-research` per `RESEARCH_MODE_MODELS`. Result-processor maps these
> into research nodes: `profile` ← expert_overview/presence; a new `ip` node ←
> frameworks/content/mechanism; `offers` node ← offers/revenue/pricing;
> `competitors` node ← competitor queries; `audience` node ← audience/traction.

---

## 3. Synthesis plan (Gemini)

Five new prompt modules under `synthesis/prompts/` (one file each), wired into a
report-type-aware `DELIVERABLES` registry keyed by `report_type`. Each prompt
follows the existing house pattern (fixed `## Required Sections` skeleton,
markdown tables, explicit output-format rules — see `prompts/quick_wins.py`).
`context_builder.py` injects the named research nodes as the model's context.

### 01 — `ip_extraction_map.py`
- **Inputs:** `profile`, `ip` research node (frameworks/content/mechanism).
- **Asked to produce:** decompose the expert's body of work into a modular IP
  inventory; name the unique mechanism; score each component for extraction
  feasibility.
- **Output structure:**
  1. Executive Summary (what IP exists, how extractable overall)
  2. IP Inventory table — `| Component | What it is | Modular? | Extraction Feasibility (High/Med/Low) | Why |`
  3. Unique Mechanism — the named, defensible "how," 1 paragraph + a one-line trademark-able phrasing
  4. Extraction Roadmap — which components to productize first (ranked by feasibility × value)
  5. A `mermaid` IP dependency map (→ `Substrate.diagrams`)
- **Severity:** set per IP component → `high/med/low` extractability.

### 02 — `monetization_gap.py`
- **Inputs:** `offers`, `monetization`/`pricing` nodes, plus Module 01 output (the IP inventory).
- **Asked to produce:** current vs. potential revenue, the missing rungs of the
  offer ladder, and recurring-revenue pathways latent in the IP.
- **Output structure:**
  1. Executive Summary (headline gap $ figure)
  2. Current Monetization Map — existing offers + price points
  3. Pricing-Tier Gap table — `| Tier | Exists? | Suggested Offer | Price Range | IP Source |` (entry → mid → high-ticket → partnership/licensing)
  4. Recurring-Revenue Pathways — subscriptions/memberships/licensing the IP could support
  5. Quantified Gap — current vs. potential annual revenue with assumptions
- **Severity:** size of unrealized revenue (`high` = large gap).

### 03 — `ai_deployment_blueprint.py`
- **Inputs:** Module 01 (IP inventory), `niche_ai_automation`, `expert_workflow_surface`.
- **Asked to produce:** a domain-tailored agent architecture and a ranked list of
  automation candidates with build-vs-buy calls.
- **Output structure:**
  1. Executive Summary (top leverage automation)
  2. Agent Architecture (`mermaid` diagram → `Substrate.diagrams`) — agents that
     could deliver/scale the expert's IP
  3. Automation Candidate Ranking table — `| Candidate | Leverage Impact (High/Med/Low) | Effort | Build vs Buy | Recommended Tool |`
  4. Build-vs-Buy Rationale per top-3 candidate
  5. Deployment sequence (what to ship first)

### 04 — `competitive_landscape.py`
- **Inputs:** `competitors` node, `niche_positioning`, Module 02 (pricing context).
- **Asked to produce:** a positioning/pricing map of comparable experts and the
  differentiation gaps open for capture, plus timing.
- **Output structure:**
  1. Executive Summary (where the white space is)
  2. Competitor Map table — `| Expert/Offer | Positioning | Price Point | Strength | Vulnerability |`
  3. Differentiation Gaps — open positions the expert could own (ranked)
  4. Market-Timing Assessment — is the niche heating/saturating; window
  5. Positioning Recommendation — the lane to claim
- **Severity:** per-gap urgency/vulnerability.

### 05 — `partnership_viability.py`  *(writes the verdict)*
- **Inputs:** ALL prior module outputs (01–04) + `audience` node. This is the
  synthesizing/decision module — depends on everything, like
  `final_strategy_report` depends on `ALL_MARKDOWN`.
- **Asked to produce:** a viability score with a transparent factor breakdown, a
  revenue projection model, and a GO/DEVELOP/PASS recommendation.
- **Output structure:**
  1. **`VERDICT:` machine line first** (see §1.1) — recommendation, score,
     projected 12-mo revenue, confidence.
  2. Viability Score Breakdown table — `| Factor | Weight | Score | Notes |`
     (factors: IP extractability, monetization upside, audience/traction,
     competitive position, AI-leverage fit)
  3. Revenue Projection Model — conservative / base / aggressive 12-mo scenarios
     with the assumption stack
  4. Recommendation & Rationale — GO / DEVELOP / PASS + the 3 conditions that
     would flip a DEVELOP to a GO
  5. Next Steps (if GO: the first partnership move)
- **Post-synthesis:** verdict extractor reads the `VERDICT:` line → sets
  `Substrate.verdict`, emits the two `Metric`s, sets section `severity`.

---

## 4. What structurally differs from the AI Strategy report

| Dimension | AI Strategy (`ai_strategy`) | Intelligence Brief (`intelligence_brief`) |
|---|---|---|
| **Subject** | Company (`SubjectType.COMPANY`) | Person/expert/brand (`SubjectType.EXPERT`) |
| **Seed** | Company name + website (corporate identity) | Expert name + personal site/handle (`brand.seed_url` = their domain) |
| **Research focus** | Tech stack, org maturity, departments, industry market, regulatory | Their **IP/frameworks, offers & pricing, audience, competitor experts, monetization model** — no tech-inventory, no department pain-matrix |
| **Core analytic lens** | Maturity model (where are you on the AI curve) + readiness gaps | **Value-extraction lens** (what IP exists, what revenue is left on the table, is this person worth partnering with) |
| **Deliverable count** | 15 markdown + decks + SOW | 5 modules (5 `Section`s + 1–2 diagrams) — lean, single branded HTML |
| **Decision output** | None (advisory roadmap) | **A go/no-go verdict** populating `Substrate.verdict` (GO/DEVELOP/PASS) + revenue projection — this is a *decision brief*, not just a report |
| **Primary view** | Dense/sectioned report view | Decision-brief view: leads with `verdict` + viability metrics, then the 5 modules |
| **Severity semantics** | Maturity gaps | Extraction feasibility / gap size / competitive vulnerability |
| **Entity-resolution risk** | Two companies sharing a name | A person sharing a name with another person/company (the exact `Steve Cunningham` case the gate was built for) |

The biggest structural addition is the **verdict**: the strategy report never
populates `Substrate.verdict`, but the intelligence brief's Module 5 makes it the
headline. Views that key off `verdict` (the decision-brief view described in
`substrate.py`'s docstring) light up only for this report type.

---

## 5. Entity-resolution note (person subject)

`resolve_entity(seed_name, seed_url, resolved_name, resolved_description, sources)`
in `substrate.py` already works for people **unchanged** — it was literally
designed against the `Steve Cunningham` (advisor at `stevecunningham.ai`) vs.
`Steve Cunningham & Associates Limited` (a 1990 UK company) collision. For the
intelligence brief:

- **Seed = the expert's site/handle.** Set `Brand.seed_url` and the input
  `website` field to the expert's personal domain (e.g. `https://stevecunningham.ai/`).
  `seed_name` = the expert's name. The **decisive signal is unchanged**: does the
  seed domain actually appear in the research sources? A shared *person* name is
  exactly the false-match the gate discounts (`name_overlap` is the weak signal;
  domain-in-sources is the strong 0.6-weight signal).
- **Wire-up:** when assembling from a run, pass the expert's domain as `seed_url`
  and aggregate sources across the new expert research nodes (`profile, ip,
  offers, competitors, audience`) into the `sources` list — mirror the loop in
  `from_state()` but over the expert node names instead of
  `profile/industry/tech_landscape/regulatory`.
- **Red-flag heuristics still apply and are if anything *more* relevant:** the
  existing flags catch "incorporated / companies house / historical founding
  year" — i.e. when a *person* query resolves onto a *company* registry record.
  That is the single most likely failure mode for an expert subject (name
  collides with an incorporated entity), so the gate's corporate-registry flag is
  the right guard. No new heuristics required for v1.
- **Handle-only experts (no domain):** if the expert leads with a social handle
  and has no canonical site, `seed_url` may be empty → the gate skips the domain
  check and falls to name-overlap (the "no seed URL" branch, capped lower
  confidence → `WEAK`, render-with-flag). **Recommendation:** require a seed URL
  (site *or* a canonical profile URL such as the LinkedIn/YouTube channel) at
  intake so the domain check stays armed; treat a verified platform URL as the
  seed domain. This is the one place a person-subject benefits from a small intake
  rule beyond the company flow.
- **Blocking behaviour unchanged:** `MISMATCH` (score < 0.4) sets `blocking=True`
  → do not render/publish. Same anti-substrate-rot guarantee.

---

## 6. Implementation checklist (to wire `report_type=intelligence_brief`)

1. `research/query_templates.py` — add `EXPERT_*` `QueryCategory` members + the
   ~16 templates in §2; add `{expert_name}/{seed_domain}/{niche}/{handle}`
   placeholders to `render_query`.
2. `research/result_processor.py` — map expert queries into research nodes
   (`profile, ip, offers, competitors, audience`).
3. `synthesis/prompts/` — add the 5 modules in §3
   (`ip_extraction_map, monetization_gap, ai_deployment_blueprint,
   competitive_landscape, partnership_viability`).
4. `config.py` — add a report-type-aware deliverable set (5 IDs in §1, dependency
   order 01→04, with 05 depending on `ALL_MODULES`).
5. `substrate.py` `from_state()` — branch on `meta.report_type`: use expert node
   names for the `sources` aggregation, set section `id/order/kicker` from §1,
   and add the **verdict extractor** (parse the `VERDICT:` line from the Module 05
   markdown → `Substrate.verdict` + two `Metric`s + section `severity`).
6. Intake — collect `expert_name`, `seed_url` (site/canonical profile), `niche`,
   `handle`; set `subject_type=expert`, `report_type=intelligence_brief`.

No schema migration: `SubjectType.EXPERT`, `ReportType.INTELLIGENCE_BRIEF`,
`Section.severity`, and `Substrate.verdict` already exist in the contract.
