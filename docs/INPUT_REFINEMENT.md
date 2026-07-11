# Input Refinement Engine

> A reusable, headless component for resolving inter-dependent inputs, with an
> optional per-field **deep dive** that adds depth on demand — without forcing
> that depth on every run.

## Why

Today the AI Strategy Factory has essentially three knobs (company name, a
free-text context blob, a quick/comprehensive toggle) and always emits the same
15 deliverables. It behaves like one static widget. The `CompanyInput` model even
declares seven structured fields (`industry`, `employee_count`, `tech_stack`,
`goals`, `challenges`, …) that nothing collects — the input layer was anticipated
but never built.

The refinement engine is that missing layer. The design goal is **progressive
depth**: keep the simple, nimble default, but let any single input be enriched
through a short research + clarification subloop when it matters.

## Core idea

Every input is a field that can be filled two ways:

- **Light (default).** A cheap, *assumed* value so a run never blocks. Required
  fields are always resolved this way up front — "decided up front, kept light."
- **Deep dive (opt-in, per field).** A scoped research/extraction pass plus a
  short, pre-answered clarifying Q&A (3–10 questions) that promotes the field
  from an assumption to a *confirmed* value. This is the factory dogfooding its
  own research→synthesize loop, recursed down to one field.

Refinement happens **pre-run** — the pipeline itself is never paused. You refine
the fields you care about, lock the config, then run.

## The three input tiers

The strategy factory's fields (`strategy_specs.py`) span the tiers we aligned on,
wired into a dependency DAG so they resolve in order:

| Tier | Fields | Question answered |
|------|--------|-------------------|
| **Subject** | `name`, `industry`, `company_size`, `tech_stack`, `challenges` | What is this company? |
| **Intent** | `objective`, `audience` | For whom, and to what end? |
| **Scope** | `deliverables`, `research_mode` | What should the run produce? |

Inputs have dependencies just like deliverables do (e.g. `tech_stack` depends on
`industry`; `challenges` on `industry` + `company_size`). The engine
topologically orders them and detects cycles / dangling deps eagerly.

## The provenance envelope

Each resolved field is not a bare value but an envelope — this *is* the "layer of
abstraction" that lets each input be independently shallow or deep:

```
ResolvedField { value, source, confidence, evidence[], stale }
  source ∈ { assumed, researched, confirmed }
```

When a field is confirmed/changed, every field that (transitively) depends on it
is marked `stale`, signalling its assumption may be out of date and offering a
re-prefill. The run config is complete and usable at every step.

## Lifecycle

```
resolve_light(context)        → all fields assumed (nimble default)
deep_dive(key, state)         → research + extract + pre-answered questions  (a proposal)
apply_answer(key, value)      → commit as confirmed; mark dependents stale
```

See `demo.py` for the full walkthrough (`python -m strategy_factory.refinement.demo`).

## Architecture / reusability

```
refinement/
├── engine.py          # InputField, ResolvedField, RefinementEngine, Provider protocol
│                      #   — imports NOTHING from strategy_factory (extractable as-is)
├── providers.py       # StubProvider (offline, deterministic) + PerplexityGeminiProvider sketch
├── strategy_specs.py  # the factory's field specs — CONSUMER #1
└── demo.py            # offline end-to-end walkthrough
```

The engine is domain-agnostic: it operates on a declarative `InputField` list and
an injected `Provider`. The strategy factory is simply the first consumer. Swap
the spec list + provider and the same engine refines inputs for any
inputs-with-dependencies problem — which is the path to turning it into its own
standalone widget.

- **`Provider`** is the seam between the engine and the outside world.
  `StubProvider` runs fully offline (tests, dry runs); `PerplexityGeminiProvider`
  wraps the existing `PerplexityClient` (research) and Gemini (extraction /
  question generation). Swapping stub → production is a one-line change.

## Status

- [x] Headless engine: DAG ordering, light resolution, deep dive, staleness
      (`propagate=False` on `apply_answer` for seeding a baseline without a
      false staleness cascade — see engine.py)
- [x] Offline stub provider + deterministic demo
- [x] Unit tests (`python -m unittest tests.test_refinement`, 11 passing)
- [x] Strategy-factory field specs (consumer #1)
- [x] Web UI: `/refine` page with provenance badges + `⚡ Deep dive` per field,
      `/refine/<rid>/deep-dive` and `/refine/<rid>/apply` routes. Verified live
      in Chromium (screenshots in this session's transcript). Uses
      `StubProvider` — no live research yet.
- [ ] Real `PerplexityGeminiProvider` wiring (parse model output → values/questions)
- [ ] Feed the resolved `/refine` config into the existing pipeline (`/start`
      currently still uses the old 3-knob form; `/refine` is not yet connected
      to it)
- [ ] Scope → deliverable subset: make `deliverables` field actually select a
      subset of `config.DELIVERABLES`, reusing that dict's `dependencies` to
      pull in required upstream docs

## Open loops / next session

**Unanswered design question** (asked, no answer yet — resolve before building
deliverable selection): should deliverable **Scope** be:
(a) a few named presets ("Board readout", "Roadmap only", "Full factory"),
(b) fully à-la-carte checkboxes, or
(c) both (presets that expand into editable checkboxes)?

**Planned next chunk** (offline-verifiable, no API keys needed — safe to do in
any environment): in priority order —
1. Config→run wiring: map `/refine` resolved state (`ResolvedField` dict) into
   `CompanyInput`/a RunConfig, hand off to the existing pipeline. Currently
   `/refine` and `/start` are two disconnected surfaces.
2. Scope→deliverable-subset logic against `config.DELIVERABLES`, with unit
   tests — this is what makes the Scope tier actually change pipeline output.
   Depends on the open question above.
3. Harden `PerplexityGeminiProvider` parsing against *mocked* Perplexity/Gemini
   clients (deterministic fixtures, no live calls) so the shape is locked
   before anyone plugs in real keys.
4. A `HANDOFF.md`-style note for whoever has live API keys: what to paste in,
   what "good" output looks like, where prompt-tuning happens
   (`strategy_specs.py` templates + `providers.py`), what's already covered by
   tests vs. what needs human judgment on real output quality.

**What genuinely needs a human with live keys** (not deferrable to any agent
without credentials): running `/refine` end-to-end against real Perplexity +
Gemini and judging whether the deep-dive research, extracted values, and
clarifying questions are actually good — that's a taste call on live model
output that no amount of mock-based work here can substitute for.

## Roadmap notes

- Once a `RunConfig` object exists, optional behaviours (e.g. publishing a runner
  report to a NOW page, the machine-readable pricing page) become **flags on the
  config** rather than hardwired — optionality is just more fields.
- `Scope.deliverables` should resolve to a subset of `config.DELIVERABLES`, reusing
  that dict's existing dependency graph to run only the chosen documents.
