"""
Input refinement engine — a reusable, headless component for resolving
inter-dependent inputs, with optional per-field "deep dive" enrichment.

The strategy factory is consumer #1 (see ``strategy_specs``); the engine itself
(``engine``) has no app dependencies and can be extracted as its own widget.
"""

from .engine import (
    DeepDiveProposal,
    DependencyError,
    InputField,
    Provider,
    Question,
    RefinementEngine,
    ResearchResult,
    ResolvedField,
    Source,
)
from .providers import PerplexityGeminiProvider, StubProvider
from .strategy_specs import strategy_fields

__all__ = [
    "DeepDiveProposal",
    "DependencyError",
    "InputField",
    "Provider",
    "Question",
    "RefinementEngine",
    "ResearchResult",
    "ResolvedField",
    "Source",
    "PerplexityGeminiProvider",
    "StubProvider",
    "strategy_fields",
]
