"""
Offline demo of the refinement engine. No API keys required.

    python -m strategy_factory.refinement.demo

Walks the full lifecycle: light up-front resolution, a deep dive on one field,
applying the user's confirmed answer, and the resulting staleness propagation to
dependent fields.
"""

from __future__ import annotations

from .engine import RefinementEngine
from .providers import StubProvider
from .strategy_specs import strategy_fields


def _show(state) -> None:
    for key, rf in state.items():
        flag = "  (STALE)" if rf.stale else ""
        print(f"  - {key:14} = {str(rf.value)!r:40} [{rf.source}, conf={rf.confidence}]{flag}")


def main() -> None:
    engine = RefinementEngine(strategy_fields(), StubProvider())
    context = {"name": "Acme Robotics"}

    print("Dependency order:")
    print("  " + " -> ".join(engine.order()))

    print("\n1) Light up-front resolution (the nimble default):")
    state = engine.resolve_light(context)
    # The one thing a user always provides — seed it so it isn't empty.
    state = engine.apply_answer("name", "Acme Robotics", state)
    _show(state)

    print("\n2) Deep dive on 'industry' (opt-in enrichment):")
    proposal = engine.deep_dive("industry", state, context)
    print(f"   proposed value : {proposal.proposed_value!r}")
    print(f"   confidence     : {proposal.confidence}")
    print(f"   evidence       : {proposal.evidence}")
    print("   clarifying Q&A (pre-answered):")
    for q in proposal.questions:
        print(f"     • {q.text}")
        print(f"       ↳ suggested: {q.suggested_answer}")

    print("\n3) User confirms 'Industrial Automation'; dependents go stale:")
    state = engine.apply_answer("industry", "Industrial Automation", state)
    _show(state)

    print("\nFields now stale (offer to re-prefill):",
          [k for k, v in state.items() if v.stale])


if __name__ == "__main__":
    main()
