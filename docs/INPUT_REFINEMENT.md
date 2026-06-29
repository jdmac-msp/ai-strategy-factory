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
- [x] Offline stub provider + deterministic demo
- [x] Unit tests (`python -m unittest tests.test_refinement`)
- [x] Strategy-factory field specs (consumer #1)
- [ ] Real `PerplexityGeminiProvider` wiring (parse model output → values/questions)
- [ ] Web UI: collapsible fields with a `⚡ Deep dive` affordance + Q&A
- [ ] Feed the resolved config into the existing pipeline (replace the 3-knob form)

## Roadmap notes

- Once a `RunConfig` object exists, optional behaviours (e.g. publishing a runner
  report to a NOW page, the machine-readable pricing page) become **flags on the
  config** rather than hardwired — optionality is just more fields.
- `Scope.deliverables` should resolve to a subset of `config.DELIVERABLES`, reusing
  that dict's existing dependency graph to run only the chosen documents.
