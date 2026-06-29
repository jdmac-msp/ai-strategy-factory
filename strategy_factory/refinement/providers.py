"""
Providers for the refinement engine.

* ``StubProvider`` — deterministic, fully offline. Used by tests, dry runs, and
  the demo. Produces stable output so behaviour is reproducible without API keys.
* ``PerplexityGeminiProvider`` — sketch of the real backend that wraps the
  project's existing ``PerplexityClient`` (research) and Gemini (extraction /
  question generation). Left intentionally thin; wired up when we move past the
  offline slice.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .engine import Provider, Question, ResearchResult


class StubProvider:
    """Deterministic offline provider. No network, no API keys, no randomness."""

    def research(self, query: str, context: Dict[str, Any]) -> ResearchResult:
        subject = context.get("name", "the subject")
        return ResearchResult(
            summary=f"[stub research] Findings for: {query} (re: {subject}).",
            sources=["https://example.com/stub-source-1", "https://example.com/stub-source-2"],
            confidence=0.7,
        )

    def extract(self, prompt: str, evidence: str, context: Dict[str, Any]) -> Any:
        # Deterministic, human-readable, and clearly synthetic.
        return f"[stub extracted] {prompt[:60]}".strip()

    def propose_questions(self, focus: str, context: Dict[str, Any], n: int) -> List[Question]:
        return [
            Question(
                text=f"Q{i + 1}: To pin down {focus}, can you confirm detail #{i + 1}?",
                suggested_answer=f"[best guess #{i + 1} based on {context.get('name', 'context')}]",
            )
            for i in range(max(0, n))
        ]


class PerplexityGeminiProvider:
    """Real backend sketch. Wraps the existing research client + Gemini.

    Not exercised in the offline slice — kept as a typed seam so swapping the
    stub for production is a one-line change at the call site.
    """

    def __init__(self, perplexity_client: Any, gemini_client: Any):
        self._pplx = perplexity_client
        self._gemini = gemini_client

    def research(self, query: str, context: Dict[str, Any]) -> ResearchResult:
        result = self._pplx.search(query)
        # QueryResult -> ResearchResult; field names per strategy_factory.models.
        sources = [s.url for s in getattr(result, "sources", []) if getattr(s, "url", None)]
        return ResearchResult(
            summary=getattr(result, "content", "") or getattr(result, "answer", ""),
            sources=sources,
            confidence=0.75,
        )

    def extract(self, prompt: str, evidence: str, context: Dict[str, Any]) -> Any:
        return self._gemini.generate(f"{prompt}\n\nEvidence:\n{evidence}")

    def propose_questions(self, focus: str, context: Dict[str, Any], n: int) -> List[Question]:
        raw = self._gemini.generate(
            f"Generate {n} clarifying questions to pin down: {focus}. "
            f"For each, pre-answer with your best guess given: {context}."
        )
        # Parsing of the model output is deferred to the real wiring step.
        return [Question(text=line.strip()) for line in str(raw).splitlines() if line.strip()][:n]


# Static type check: both satisfy the Provider protocol.
_stub: Provider = StubProvider()
