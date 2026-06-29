"""
Input Refinement Engine
=======================

A small, dependency-free engine for turning a set of *input fields* (which may
depend on one another) into a resolved configuration. Each field can be filled
two ways:

* **Light** (the default): a cheap, assumed value so the machine can always run
  immediately. Required fields are always resolved this way up front.
* **Deep dive** (opt-in, per field): a scoped research + extraction pass plus a
  short, pre-answered clarifying Q&A that promotes the field from an assumption
  to a confirmed value.

The engine knows nothing about "company strategy" — it operates on a declarative
list of ``InputField`` specs and an injected ``Provider``. That is deliberate:
the strategy factory is simply *consumer #1*. Swap the specs + provider and the
same engine refines inputs for any domain — which is what lets it become its own
reusable widget later.

This module imports nothing from ``strategy_factory`` and depends only on the
standard library, so it can be lifted out wholesale.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional, Protocol


# ---------------------------------------------------------------------------
# Value source provenance
# ---------------------------------------------------------------------------

class Source:
    """How a resolved value came to be — its 'layer of abstraction'."""
    ASSUMED = "assumed"        # light prefill / default — cheap guess
    RESEARCHED = "researched"  # produced by a deep-dive research+extract pass
    CONFIRMED = "confirmed"    # user accepted/edited the value in the Q&A subloop


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class InputField:
    """Declarative spec for a single input. Mostly data, so it is portable."""
    key: str
    label: str
    depends_on: List[str] = field(default_factory=list)
    # Required fields are always resolved (light) up front so a run never blocks.
    required: bool = False
    # Cheap fallback used by the light pass when no research has run.
    light_default: Any = None
    # Templates consumed by a Provider during a deep dive. ``{key}`` placeholders
    # are filled from the current resolved values + the run context.
    research_query: Optional[str] = None
    extract_prompt: Optional[str] = None
    # What the clarifying Q&A should pin down. If None, no questions are asked.
    clarify_focus: Optional[str] = None
    # How many clarifying questions to propose during a deep dive.
    clarify_questions: int = 3


@dataclass
class ResolvedField:
    """A field's current value plus the provenance envelope."""
    key: str
    value: Any
    source: str = Source.ASSUMED
    confidence: float = 0.3
    evidence: List[str] = field(default_factory=list)
    # True when an upstream dependency changed after this field was resolved,
    # signalling the value may be out of date and could be re-prefilled.
    stale: bool = False


@dataclass
class Question:
    """One clarifying question, pre-answered with the engine's best guess."""
    text: str
    suggested_answer: str = ""


@dataclass
class DeepDiveProposal:
    """The result of a deep dive on a field, awaiting user confirmation."""
    key: str
    proposed_value: Any
    confidence: float
    evidence: List[str]
    questions: List[Question]


# ---------------------------------------------------------------------------
# Provider contract
# ---------------------------------------------------------------------------

class Provider(Protocol):
    """Pluggable research/LLM backend. The real one wraps Perplexity + Gemini;
    the stub one runs fully offline for tests and dry runs."""

    def research(self, query: str, context: Dict[str, Any]) -> "ResearchResult":
        """Run a scoped research pass for a single question."""
        ...

    def extract(self, prompt: str, evidence: str, context: Dict[str, Any]) -> Any:
        """Turn raw evidence into a concrete field value."""
        ...

    def propose_questions(
        self, focus: str, context: Dict[str, Any], n: int
    ) -> List[Question]:
        """Generate up to ``n`` clarifying questions, each pre-answered."""
        ...


@dataclass
class ResearchResult:
    summary: str
    sources: List[str] = field(default_factory=list)
    confidence: float = 0.6


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class DependencyError(ValueError):
    """Raised when the field specs do not form a valid DAG."""


class RefinementEngine:
    """Resolves a set of ``InputField`` specs into a config of ``ResolvedField``s."""

    def __init__(self, fields: List[InputField], provider: Provider):
        self.fields: Dict[str, InputField] = {f.key: f for f in fields}
        if len(self.fields) != len(fields):
            raise DependencyError("Duplicate field keys in spec.")
        self.provider = provider
        self._order = self._topo_order()  # validates the DAG eagerly

    # -- dependency graph ---------------------------------------------------

    def order(self) -> List[str]:
        """Field keys in dependency order (parents before children)."""
        return list(self._order)

    def _topo_order(self) -> List[str]:
        """Kahn's algorithm with cycle + dangling-dependency detection."""
        indegree = {k: 0 for k in self.fields}
        children: Dict[str, List[str]] = {k: [] for k in self.fields}
        for k, f in self.fields.items():
            for dep in f.depends_on:
                if dep not in self.fields:
                    raise DependencyError(
                        f"Field '{k}' depends on unknown field '{dep}'."
                    )
                indegree[k] += 1
                children[dep].append(k)

        # Stable: process ready nodes in spec order for deterministic output.
        ready = [k for k in self.fields if indegree[k] == 0]
        ordered: List[str] = []
        while ready:
            node = ready.pop(0)
            ordered.append(node)
            for child in children[node]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)

        if len(ordered) != len(self.fields):
            cyclic = sorted(k for k in self.fields if k not in ordered)
            raise DependencyError(f"Dependency cycle among fields: {cyclic}")
        return ordered

    def dependents_of(self, key: str) -> List[str]:
        """All fields that (transitively) depend on ``key``."""
        result: List[str] = []
        frontier = [key]
        while frontier:
            current = frontier.pop()
            for k, f in self.fields.items():
                if current in f.depends_on and k not in result:
                    result.append(k)
                    frontier.append(k)
        # Return in dependency order for predictable re-prefill sequencing.
        return [k for k in self._order if k in result]

    # -- resolution ---------------------------------------------------------

    def resolve_light(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, ResolvedField]:
        """Cheap, assumed-only pass. Every field gets a value so a run never
        blocks; this is the 'decided up front, kept light' path."""
        context = context or {}
        state: Dict[str, ResolvedField] = {}
        for key in self._order:
            spec = self.fields[key]
            default = spec.light_default
            if callable(default):
                default = default(self._values(state), context)
            state[key] = ResolvedField(
                key=key,
                value=default,
                source=Source.ASSUMED,
                confidence=0.3,
            )
        return state

    def deep_dive(
        self,
        key: str,
        state: Dict[str, ResolvedField],
        context: Optional[Dict[str, Any]] = None,
    ) -> DeepDiveProposal:
        """Run the research + extract + clarify subloop for one field. Returns a
        proposal; nothing is committed until ``apply_answer`` is called."""
        context = context or {}
        if key not in self.fields:
            raise KeyError(key)
        spec = self.fields[key]
        scope = self._scope(state, context)

        evidence: List[str] = []
        proposed: Any = state[key].value if key in state else spec.light_default
        confidence = 0.6

        if spec.research_query:
            result = self.provider.research(self._fmt(spec.research_query, scope), scope)
            evidence = list(result.sources)
            confidence = result.confidence
            if spec.extract_prompt:
                proposed = self.provider.extract(
                    self._fmt(spec.extract_prompt, scope), result.summary, scope
                )
            else:
                proposed = result.summary

        questions: List[Question] = []
        if spec.clarify_focus:
            questions = self.provider.propose_questions(
                self._fmt(spec.clarify_focus, scope), scope, spec.clarify_questions
            )

        return DeepDiveProposal(
            key=key,
            proposed_value=proposed,
            confidence=confidence,
            evidence=evidence,
            questions=questions,
        )

    def apply_answer(
        self,
        key: str,
        value: Any,
        state: Dict[str, ResolvedField],
        confirmed: bool = True,
    ) -> Dict[str, ResolvedField]:
        """Commit a value for ``key`` and mark every dependent field stale, since
        their assumptions may now be out of date. Returns the updated state."""
        if key not in self.fields:
            raise KeyError(key)
        prior = state.get(key)
        state[key] = ResolvedField(
            key=key,
            value=value,
            source=Source.CONFIRMED if confirmed else Source.RESEARCHED,
            confidence=0.95 if confirmed else max(0.6, prior.confidence if prior else 0.6),
            evidence=prior.evidence if prior else [],
        )
        for dep_key in self.dependents_of(key):
            state[dep_key] = replace(state[dep_key], stale=True)
        return state

    # -- helpers ------------------------------------------------------------

    def _values(self, state: Dict[str, ResolvedField]) -> Dict[str, Any]:
        return {k: v.value for k, v in state.items()}

    def _scope(self, state: Dict[str, ResolvedField], context: Dict[str, Any]) -> Dict[str, Any]:
        """Flat namespace a provider/template can read: resolved values + context.
        Empty resolved values (None / "") do not shadow a context value, so a
        not-yet-filled field falls back to whatever context provides."""
        scope = dict(context)
        for k, v in self._values(state).items():
            if v is None or v == "":
                continue
            scope[k] = v
        return scope

    @staticmethod
    def _fmt(template: str, scope: Dict[str, Any]) -> str:
        try:
            return template.format(**scope)
        except (KeyError, IndexError):
            # Missing placeholders shouldn't crash a research pass; leave as-is.
            return template
