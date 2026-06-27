# HANDOFF — Build the MasteryOS Report Variant

**Resume cue:** *"Resume the report platform — start the engine sprint (synthesis emits structured data)."*
**Date:** 2026-06-27 · **Full context/ledger:** `~/.claude/projects/G--COWORK/memory/report-platform-substrate-architecture.md` (13+ row open-loops ledger, premortem, all decisions). Read it first.

## The goal
Build the **MasteryOS variant** of the AI Strategy Factory report: a structured-data, branded, **interactive knowledge object** — graph view + grounded chat + principle boxes + teaching overlay — categorically different from a static Deloitte-style deck or the clean client deliverable.

## The architecture — 3 orthogonal dials
**report-type** (strategy · intelligence_brief · idea_validator) × **view** (A Dossier · B Visual · C Decision · D Traditional · **G Graph**) × **variant** (client · MasteryOS).
Pipeline: `L0 intake → L1 engine (Perplexity+Gemini) → L2 SUBSTRATE → L3 report-type → L4 view → L5 brand → L6 publish (NowPage/Reveal)`.
The **Substrate** (L2) is the keystone: one typed contract every view + report-type + variant shares. Decouples engine from presentation.

## DONE + verified (this session)
| What | Where |
|---|---|
| Substrate contract + entity-resolution gate (proven BLOCK/WARN/PASS) | ai-strategy-factory `strategy_factory/substrate.py` · branch `cc/substrate/contract-and-entity-gate` |
| HTML renderer: View D + collapsibles + diagram-detect fix + zoom | `strategy_factory/generation/html_generator.py` |
| substrate.json bridge (+ `Section.body_html`) | `html_generator` writes it |
| React renderer: View D, collapsibles, click-zoom diagrams, entity-gate banner, graceful diagram fallback | folio-saas branch `cc/substrate/react-renderer`: `app/report/preview/`, `components/report/views/ViewTraditional.tsx`, `components/report/DiagramOverlay.tsx`, `types/substrate.ts` — verified at `/report/preview` |
| Specs | `docs/intelligence-brief-spec.md`, `docs/view-structural-dna.md` (Anti-Recolor Test) |
| Floor-test fixes (PPTX swallow + mermaid) | Jason's parallel branch `cc/82da8c/...` (commit bf18499) |

## THE ENGINE SPRINT — the gating prerequisite (one coherent change)
**"Synthesis emits STRUCTURED DATA, not prose."** These are all the *same* change and should ship together:
- **RP-16 citations** → per-claim citations into `Substrate.citations` (url + claim text) + inline footnote markers.
- **RP-26 structured diagrams** → nodes+edges JSON in `Substrate.diagrams` (kills LLM-mermaid fragility; render with react-flow). Mermaid+detection-fix is the working STOPGAP.
- **RP-29 primitive knowledge graph** → run the `primitive-decomposition` skill on the report findings → nodes (L1 primitive → L2 sub → L3 checkpoint → L4 shared-dep) + typed edges (hierarchy / what-must-be-true / mapping) → new `Substrate.graph`.
- **RP-18 principle boxes** → tag blocks: timely / asymmetric / forcing-functions / primitives (FORGE manifest + Jason's principles).
- **RP-19 paste-prompts** → generated copyable prompt blocks.
- **RP-17 fact-check** → cheap claim-vs-cited-source string check FIRST → Codex contrarian ONLY on flagged claims (mirror the entity gate's cheap-structural-first pattern). Token-efficient.
Files (per `intelligence-brief-spec.md` checklist): `research/query_templates.py`, `research/result_processor.py`, `synthesis/prompts/`, `config.py`, `substrate.py`, `substrate.from_state()`, intake.
**Also fold in RP-3b:** wire `report_type=intelligence_brief` (spec is ready, no schema change).

## THE RENDERER WORK (folio-saas — after the engine emits structured substrate)
- **View G (Graph):** **REUSE the Priestley graph renderer** at `plan.jasondmacdonald.com/priestley-primitive-graph` (extract the component — react-flow, molten/house-amber styling, layered nodes + typed edges + click-to-lock detail cards + family toggles). Feed it `Substrate.graph`.
- **Grounded chat (RP-20):** retrieval over substrate sections/citations; **graph nodes = retrieval anchors**; system-prompt "answer ONLY from these sections, cite the section"; no hallucination. Gate = **email-to-unlock via PDF delivery** (verify lazily by emailing the PDF); **BYOK relief valve** for heavy use (mirror NowPage BYOK). Uses folio-saas Supabase auth (already exists).
- **Principle boxes (RP-18) + paste-prompts (RP-19)** → React components consuming substrate tags.
- **Inline citation markers + sources (RP-16).**
- **Download tabs (RP-27):** PDF (view is print-styled) + DOCX (engine output `output/<slug>/documents/*.docx`). Gated per RP-28.
- **Variant toggle (RP-21):** client (clean) vs MasteryOS (teaching overlay: principle boxes + prompts + graph + chat ON).
- **RunConfig (RP-25):** pre-run "confirm or change" of dependencies (producer brand, subject name/title, seed URL, accent, logo, view, report-type, variant); defaults per project.

## Gating / value-ladder (RP-28) — recommended v1
Read = free · **Download + Chat = email-to-unlock (PDF-delivery verification)** · Save/baseline = free account (Supabase) · Heavy chat = BYOK or paid. Start with ONE gate (email-to-unlock-chat). Don't hard-force anything. The chat is the monetization surface.

## REUSE — don't rebuild
Priestley graph renderer · folio-saas Supabase auth (gate/accounts) · `mcp-nowpage` `publish_to_nowpage` (L6) · `primitive-decomposition` skill (RP-29 graph data) · the existing engine DOCX output (RP-27).

## Open decisions Jason owes
1. Gate v1 = email-to-unlock-chat (PDF delivery) — confirm.
2. Download tabs ungated for now — confirm.
3. Producer brand left-corner = "ASAP AI" — confirm or change.
4. **WIP≤3 reconciliation** — this is effectively a NEW active thread; decide what it displaces.

## Branches — NOT pushed (human gate per git discipline)
- ai-strategy-factory: `cc/substrate/contract-and-entity-gate`
- folio-saas: `cc/substrate/react-renderer`
Pull-before-push; Jason reviews + merges.
