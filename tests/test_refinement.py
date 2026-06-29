"""
Offline unit tests for the refinement engine. Standard-library unittest only.

    python -m unittest tests.test_refinement
"""

import unittest

from strategy_factory.refinement.engine import (
    DependencyError,
    InputField,
    RefinementEngine,
    Source,
)
from strategy_factory.refinement.providers import StubProvider
from strategy_factory.refinement.strategy_specs import strategy_fields


def _engine(fields):
    return RefinementEngine(fields, StubProvider())


class TopologyTests(unittest.TestCase):
    def test_parents_precede_children(self):
        engine = _engine(strategy_fields())
        order = engine.order()
        pos = {k: i for i, k in enumerate(order)}
        for f in strategy_fields():
            for dep in f.depends_on:
                self.assertLess(pos[dep], pos[f.key],
                                f"{dep} must come before {f.key}")

    def test_cycle_detected(self):
        fields = [
            InputField(key="a", label="A", depends_on=["b"]),
            InputField(key="b", label="B", depends_on=["a"]),
        ]
        with self.assertRaises(DependencyError):
            _engine(fields)

    def test_dangling_dependency_detected(self):
        fields = [InputField(key="a", label="A", depends_on=["ghost"])]
        with self.assertRaises(DependencyError):
            _engine(fields)

    def test_duplicate_keys_rejected(self):
        fields = [InputField(key="a", label="A"), InputField(key="a", label="A2")]
        with self.assertRaises(DependencyError):
            _engine(fields)


class ResolutionTests(unittest.TestCase):
    def setUp(self):
        self.engine = _engine(strategy_fields())
        self.context = {"name": "Acme Robotics"}

    def test_light_resolves_every_field_as_assumed(self):
        state = self.engine.resolve_light(self.context)
        self.assertEqual(set(state), set(self.engine.order()))
        self.assertTrue(all(rf.source == Source.ASSUMED for rf in state.values()))

    def test_required_fields_always_present(self):
        state = self.engine.resolve_light(self.context)
        for f in strategy_fields():
            if f.required:
                self.assertIn(f.key, state)
                self.assertIsNotNone(state[f.key].value)

    def test_deep_dive_produces_proposal_and_questions(self):
        state = self.engine.resolve_light(self.context)
        proposal = self.engine.deep_dive("industry", state, self.context)
        self.assertEqual(proposal.key, "industry")
        self.assertTrue(proposal.evidence)            # research ran
        self.assertEqual(len(proposal.questions), 3)  # clarify_questions=3
        for q in proposal.questions:
            self.assertTrue(q.suggested_answer)        # pre-answered

    def test_apply_answer_confirms_and_marks_dependents_stale(self):
        state = self.engine.resolve_light(self.context)
        state = self.engine.apply_answer("industry", "Industrial Automation", state)
        self.assertEqual(state["industry"].source, Source.CONFIRMED)
        self.assertFalse(state["industry"].stale)
        # tech_stack and challenges depend (transitively) on industry.
        self.assertTrue(state["tech_stack"].stale)
        self.assertTrue(state["challenges"].stale)
        # name does not depend on industry.
        self.assertFalse(state["name"].stale)

    def test_determinism(self):
        a = self.engine.deep_dive("industry", self.engine.resolve_light(self.context), self.context)
        b = self.engine.deep_dive("industry", self.engine.resolve_light(self.context), self.context)
        self.assertEqual(a.proposed_value, b.proposed_value)
        self.assertEqual([q.text for q in a.questions], [q.text for q in b.questions])


class DependentsTests(unittest.TestCase):
    def test_transitive_dependents(self):
        engine = _engine(strategy_fields())
        deps = engine.dependents_of("name")
        # industry depends on name; tech_stack depends on industry -> transitive.
        self.assertIn("industry", deps)
        self.assertIn("tech_stack", deps)


if __name__ == "__main__":
    unittest.main()
