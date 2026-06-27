"""
substrate.py — the report-platform keystone.

The Substrate is a typed, view-agnostic, report-type-agnostic Intermediate
Representation that sits BETWEEN the engine (Perplexity research + Gemini
synthesis) and the presentation layer (views).

    L1 ENGINE  ──►  L2 SUBSTRATE  ──►  L3 REPORT TYPE  ──►  L4 VIEW  ──►  L5 BRAND  ──►  L6 PUBLISH

Why it exists (from the premortem):
  * It is the quality gate: `resolve_entity()` blocks "substrate rot" (research
    that resolved the wrong entity) before any view renders it.
  * It makes views STRUCTURAL not cosmetic: a view is a pure function of
    substrate fields. A visual view pulls `diagrams`/`metrics`; a dense view
    pulls `sections`/tables; a decision brief pulls `verdict` + top findings.
  * It is the generalization seam: "for anybody" == anybody's Substrate; a new
    report type == a new section schema feeding the SAME Substrate shape.
  * It keeps generation FAST: the Substrate is produced once and cached. Views
    are pure templates over it — no re-generation, no extra API calls.

This module is intentionally dependency-light (pydantic only) and pure: it does
no network I/O. `from_state()` builds a Substrate from an EXISTING run's
state.json + markdown, so it can be validated with zero re-runs.
"""
from __future__ import annotations
import re, json, pathlib
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────
class SubjectType(str, Enum):
    COMPANY = "company"
    EXPERT = "expert"       # intelligence-brief vertical
    IDEA = "idea"           # idea-validator vertical


class ReportType(str, Enum):
    AI_STRATEGY = "ai_strategy"
    INTELLIGENCE_BRIEF = "intelligence_brief"
    IDEA_VALIDATOR = "idea_validator"


class MatchStatus(str, Enum):
    MATCH = "match"         # confident the research is about the right entity
    WEAK = "weak"           # plausible but unverified — warn, allow with flag
    MISMATCH = "mismatch"   # research is about a DIFFERENT entity — BLOCK


# ─────────────────────────────────────────────────────────────────────────────
# Sub-models
# ─────────────────────────────────────────────────────────────────────────────
class Brand(BaseModel):
    """Per-client override layer (L5). One-token reskin on the house system."""
    name: str = ""                       # sticky highlighted subject name
    title: str = ""                      # sticky highlighted subject title/role
    accent: Optional[str] = None         # replaces the house signature color
    accent_2: Optional[str] = None
    logo_url: Optional[str] = None       # embedded client logo
    seed_url: Optional[str] = None       # the canonical source-of-truth URL


class EntityResolution(BaseModel):
    """Output of the entity-resolution gate — the anti-substrate-rot guard."""
    status: MatchStatus = MatchStatus.WEAK
    confidence: float = 0.0              # 0..1
    resolved_name: str = ""
    seed_name: str = ""
    seed_domain: str = ""
    seed_domain_in_sources: bool = False
    name_overlap: float = 0.0
    evidence: List[str] = Field(default_factory=list)   # human-readable reasons
    blocking: bool = False               # True => do not render/publish


class Section(BaseModel):
    """A generic content block. Report type decides which sections exist."""
    id: str
    order: int = 0
    kicker: str = ""                     # short mono label (e.g. "ASSESSMENT")
    title: str = ""
    body_md: str = ""                    # markdown body (tables live inline)
    severity: Optional[str] = None       # for findings: high|med|low|positive


class Diagram(BaseModel):
    id: str
    title: str = ""
    kind: str = "mermaid"
    source: str = ""                     # raw diagram source
    valid: Optional[bool] = None         # set by a sanitize/parse pass


class Metric(BaseModel):
    label: str
    value: str
    unit: str = ""
    source: str = ""


class Citation(BaseModel):
    url: str
    source: str = ""
    claim: str = ""


class SubstrateMeta(BaseModel):
    subject_name: str = ""
    subject_type: SubjectType = SubjectType.COMPANY
    report_type: ReportType = ReportType.AI_STRATEGY
    generated_at: str = ""
    research_model: str = ""
    synth_model: str = ""
    total_cost: float = 0.0
    mode: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# The Substrate
# ─────────────────────────────────────────────────────────────────────────────
class Substrate(BaseModel):
    """The single intermediate representation every view + report type shares."""
    meta: SubstrateMeta = Field(default_factory=SubstrateMeta)
    brand: Brand = Field(default_factory=Brand)
    entity: EntityResolution = Field(default_factory=EntityResolution)
    profile_summary: str = ""
    industry: str = ""
    sections: List[Section] = Field(default_factory=list)
    diagrams: List[Diagram] = Field(default_factory=list)
    metrics: List[Metric] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    verdict: str = ""                    # decision-brief headline (go/no-go etc.)

    # convenience for views
    def section(self, sid: str) -> Optional[Section]:
        return next((s for s in self.sections if s.id == sid), None)


# ─────────────────────────────────────────────────────────────────────────────
# Entity-resolution gate  (kills premortem failure #1: substrate rot)
# ─────────────────────────────────────────────────────────────────────────────
_STOP = {"the", "inc", "llc", "ltd", "limited", "co", "company", "associates", "and", "&", "group"}

def _domain(url: str) -> str:
    if not url:
        return ""
    m = re.sub(r"^https?://", "", url.strip().lower())
    m = m.split("/")[0]
    return m[4:] if m.startswith("www.") else m

def _tokens(s: str) -> set:
    return {t for t in re.split(r"[^a-z0-9]+", (s or "").lower()) if t and t not in _STOP}

def resolve_entity(seed_name: str, seed_url: str, resolved_name: str,
                   resolved_description: str, sources: List[str]) -> EntityResolution:
    """
    Verify the research is about the SAME entity the user seeded.

    The decisive signal is whether the seed DOMAIN actually appears in the
    research sources. A shared name is NOT enough — "Steve Cunningham" (AI
    advisor at stevecunningham.ai) and "Steve Cunningham & Associates Limited"
    (a 1990 UK company) share a name but are different entities. If the engine
    never sourced the seed domain, the profile is about someone else.
    """
    seed_domain = _domain(seed_url)
    blob = " ".join(sources or []) + " " + (resolved_description or "")
    domain_in_sources = bool(seed_domain) and seed_domain in blob.lower()

    sn, rn = _tokens(seed_name), _tokens(resolved_name or resolved_description[:120])
    name_overlap = (len(sn & rn) / len(sn)) if sn else 0.0

    evidence: List[str] = []
    # Domain presence is the strong signal (weight 0.6). When the seed domain is
    # provided but ABSENT from sources, name overlap becomes unreliable (a shared
    # name is exactly what produces a false match) so we heavily discount it.
    score = 0.0
    domain_missing = False
    if seed_domain:
        if domain_in_sources:
            score += 0.6 + 0.3 * name_overlap
            evidence.append(f"✓ seed domain '{seed_domain}' found in research sources")
        else:
            domain_missing = True
            score += 0.1 * name_overlap   # discounted: shared name is unreliable here
            evidence.append(f"✗ seed domain '{seed_domain}' NOT in any research source — research may be about a different entity")
    else:
        score += 0.2 + 0.3 * name_overlap
        evidence.append("• no seed URL provided — domain check skipped (capture the seed URL to enable it)")
    evidence.append(f"• name token overlap {name_overlap:.0%} (weak signal — shared names can collide)")

    # Contradiction red-flags in the resolved description
    flags = []
    if re.search(r"\bset up on\b|\bincorporated\b|\bcompanies house\b", (resolved_description or "").lower()):
        flags.append("description reads like a corporate-registry record, not the seeded site")
    if re.search(r"\b(19\d\d)\b", resolved_description or "") and not domain_in_sources:
        flags.append("a historical founding year with no seed-domain corroboration")
    for f in flags:
        evidence.append(f"⚠ {f}")
    if flags:
        # decisive when the domain is explicitly missing; cautionary otherwise
        score = min(score, 0.30 if domain_missing else 0.45)

    score += 0.1  # base
    score = max(0.0, min(1.0, score))

    if score >= 0.7:
        status = MatchStatus.MATCH
    elif score >= 0.4:
        status = MatchStatus.WEAK
    else:
        status = MatchStatus.MISMATCH

    return EntityResolution(
        status=status, confidence=round(score, 2),
        resolved_name=resolved_name or "", seed_name=seed_name,
        seed_domain=seed_domain, seed_domain_in_sources=domain_in_sources,
        name_overlap=round(name_overlap, 2), evidence=evidence,
        blocking=(status == MatchStatus.MISMATCH),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Adapter: build a Substrate from an EXISTING run (state.json + markdown).
# Zero re-runs — validates the contract on real data, fast.
# ─────────────────────────────────────────────────────────────────────────────
def _strip_frontmatter(text: str) -> tuple[str, str]:
    title = ""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            m = re.search(r'title:\s*"?([^"\n]+)"?', text[3:end])
            if m:
                title = m.group(1).strip()
            text = text[end + 4:]
    return title, text.lstrip("\n")

def from_state(run_dir: str | pathlib.Path) -> Substrate:
    run = pathlib.Path(run_dir)
    state = json.loads((run / "state.json").read_text(encoding="utf-8"))
    ro = state.get("research_output") or {}
    inp = state.get("input_data") or {}
    prof = ro.get("profile") or {}
    ind = ro.get("industry") or {}

    # gather all source URLs across the research output
    sources: List[str] = []
    for key in ("profile", "industry", "tech_landscape", "regulatory"):
        node = ro.get(key) or {}
        sources += node.get("sources") or []
    for c in (ro.get("competitors") or []):
        sources += (c or {}).get("sources") or []

    # entity gate
    entity = resolve_entity(
        seed_name=inp.get("name", state.get("company_name", "")),
        seed_url=inp.get("website", ""),
        resolved_name=prof.get("company_name") or "",
        resolved_description=prof.get("description", ""),
        sources=sources,
    )

    # sections from markdown deliverables (real content, no re-run)
    sections: List[Section] = []
    md_dir = run / "markdown"
    if md_dir.exists():
        for i, f in enumerate(sorted(md_dir.glob("*.md"))):
            title, body = _strip_frontmatter(f.read_text(encoding="utf-8"))
            sections.append(Section(id=f.stem, order=i, title=title or f.stem,
                                    kicker="", body_md=body))

    # diagrams from saved .mmd sources
    diagrams: List[Diagram] = []
    mm_dir = run / "mermaid_images"
    if mm_dir.exists():
        for f in sorted(mm_dir.glob("*.mmd")):
            src = f.read_text(encoding="utf-8")
            src = re.sub(r"^\s*#.*$", "", src, flags=re.M).strip()  # drop comment header
            diagrams.append(Diagram(id=f.stem, title=f.stem.replace("_", " "), source=src))

    metrics: List[Metric] = []
    if ind.get("market_size"):
        metrics.append(Metric(label="Market size", value=ind["market_size"], source="industry"))
    if ind.get("growth_rate"):
        metrics.append(Metric(label="Growth rate", value=ind["growth_rate"], source="industry"))

    citations = [Citation(url=u) for u in dict.fromkeys(sources) if u]

    meta = SubstrateMeta(
        subject_name=state.get("company_name", inp.get("name", "")),
        report_type=ReportType.AI_STRATEGY,
        generated_at=ro.get("research_timestamp", ""),
        total_cost=state.get("total_cost", 0.0),
        mode=inp.get("mode", ""),
    )
    brand = Brand(name=meta.subject_name, seed_url=inp.get("website", ""))

    return Substrate(
        meta=meta, brand=brand, entity=entity,
        profile_summary=prof.get("description", "")[:600],
        industry=ind.get("primary_industry", ""),
        sections=sections, diagrams=diagrams, metrics=metrics, citations=citations,
    )


if __name__ == "__main__":
    import sys
    run_dir = sys.argv[1] if len(sys.argv) > 1 else "output/steve-cunningham"
    sub = from_state(run_dir)
    e = sub.entity
    print(f"\n=== SUBSTRATE: {sub.meta.subject_name} ({sub.meta.report_type.value}) ===")
    print(f"sections={len(sub.sections)} diagrams={len(sub.diagrams)} "
          f"metrics={len(sub.metrics)} citations={len(sub.citations)}")
    print(f"\n=== ENTITY-RESOLUTION GATE ===")
    print(f"status={e.status.value.upper()}  confidence={e.confidence}  blocking={e.blocking}")
    print(f"seed='{e.seed_name}' @ {e.seed_domain}  |  resolved='{e.resolved_name or '(none)'}'")
    for line in e.evidence:
        print(f"   {line}")
    print(f"\nVERDICT: " + (
        "🛑 BLOCK — would have stopped this report before rendering." if e.blocking else
        ("⚠️  WARN — render with a flag." if e.status == MatchStatus.WEAK else
         "✅ PASS — safe to render.")))
