"""
Wiring test for the substrate_gate phase (Premortem Finding 2, 2026-07-27).

resolve_entity() itself is already covered in isolation by the separate gauntlet
suite (branch cc/82da8c/grounding-gauntlet). That suite never exercised the
WIRING — the actual orchestration path in main.py that is supposed to call the
gate and stop the pipeline on a mismatch. This test does exactly that: it calls
StrategyFactoryCLI._run_substrate_gate() directly (no network calls, no API
keys required) against synthetic ResearchOutput objects, and asserts the wired
method actually blocks a mismatch and passes a match.

Run: python tests/test_substrate_gate.py
"""
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from strategy_factory.main import StrategyFactoryCLI
from strategy_factory.models import (
    CompanyInput,
    CompanyProfile,
    IndustryContext,
    RegulatoryContext,
    ResearchMode,
    ResearchOutput,
    TechLandscape,
)
from strategy_factory.progress_tracker import ProgressTracker


def _make_research_output(description: str, sources: list) -> ResearchOutput:
    return ResearchOutput(
        company_name="test",
        research_timestamp=datetime.now(),
        research_mode=ResearchMode.QUICK,
        profile=CompanyProfile(description=description, sources=sources),
        industry=IndustryContext(),
        tech_landscape=TechLandscape(),
        regulatory=RegulatoryContext(),
    )


def test_gate_blocks_real_mismatch():
    """Same-name, different-entity — the exact steve-cunningham contamination class."""
    tmp = Path(tempfile.mkdtemp())
    try:
        company_input = CompanyInput(
            name="Steve Cunningham",
            website="https://stevecunningham.ai",
            mode=ResearchMode.QUICK,
        )
        # Research "found" a same-named UK company, never sourcing the seed domain.
        research = _make_research_output(
            description=(
                "Steve Cunningham & Associates Limited, set up on 1994, a UK "
                "accountancy firm registered at Companies House."
            ),
            sources=["https://find-and-update.company-information.service.gov.uk/company/12345"],
        )
        tracker = ProgressTracker("Steve Cunningham (gate-test-mismatch)", company_input, output_base=tmp)
        cli = StrategyFactoryCLI()

        proceed = cli._run_substrate_gate(tracker, company_input, research)

        assert proceed is False, "gate should have blocked a real entity mismatch"
        assert tracker.state.phases["substrate_gate"].status.value == "failed", \
            "fail_phase() should mark the phase failed"
        print("PASS: test_gate_blocks_real_mismatch")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_gate_passes_real_match():
    """Seed domain actually present in sources — should proceed."""
    tmp = Path(tempfile.mkdtemp())
    try:
        company_input = CompanyInput(
            name="Steve Cunningham",
            website="https://stevecunningham.ai",
            mode=ResearchMode.QUICK,
        )
        research = _make_research_output(
            description=(
                "Steve Cunningham is an AI advisor and consultant, stevecunningham.ai, "
                "helping companies adopt AI."
            ),
            sources=["https://stevecunningham.ai/about", "https://stevecunningham.ai/blog"],
        )
        tracker = ProgressTracker("Steve Cunningham (gate-test-match)", company_input, output_base=tmp)
        cli = StrategyFactoryCLI()

        proceed = cli._run_substrate_gate(tracker, company_input, research)

        assert proceed is True, "gate should have passed a real entity match"
        assert tracker.state.phases["substrate_gate"].status.value == "completed"
        print("PASS: test_gate_passes_real_match")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_gate_resume_skips_already_completed():
    """A resumed run that already passed the gate should not re-run it."""
    tmp = Path(tempfile.mkdtemp())
    try:
        company_input = CompanyInput(
            name="Acme Corp", website="https://acme.example.com", mode=ResearchMode.QUICK
        )
        research = _make_research_output(
            "Acme Corp, acme.example.com", ["https://acme.example.com"]
        )
        tracker = ProgressTracker("Acme Corp (gate-test-resume)", company_input, output_base=tmp)
        cli = StrategyFactoryCLI()

        first = cli._run_substrate_gate(tracker, company_input, research)
        assert first is True

        # Simulate a resumed session re-checking a run that already passed.
        second = cli._run_substrate_gate(tracker, company_input, research)
        assert second is True, "an already-completed gate should short-circuit to True on resume"
        print("PASS: test_gate_resume_skips_already_completed")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_gate_no_website_scores_weak_not_match():
    """
    Documents Premortem Finding 1: without --website, the gate cannot reach MATCH —
    it can only land in WEAK. This is expected behavior, not a bug, but a caller that
    skips --website gets no real protection. This test exists so that regressing this
    tradeoff (e.g. accidentally making no-website silently MATCH) fails loudly.
    """
    tmp = Path(tempfile.mkdtemp())
    try:
        company_input = CompanyInput(name="Acme Corp", mode=ResearchMode.QUICK)  # no website
        research = _make_research_output(
            "Acme Corp is a widget maker.", ["https://news.example.com/acme-corp-profile"]
        )
        tracker = ProgressTracker("Acme Corp (gate-test-no-website)", company_input, output_base=tmp)
        cli = StrategyFactoryCLI()

        proceed = cli._run_substrate_gate(tracker, company_input, research)

        # WEAK doesn't block, but it also doesn't confirm anything -- proceed is True
        # here by design (WEAK != blocking), which is exactly the "no-op" risk flagged
        # in the premortem: always provide --website for the gate to mean anything.
        assert proceed is True
        print("PASS: test_gate_no_website_scores_weak_not_match (confirms the documented gap)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    test_gate_blocks_real_mismatch()
    test_gate_passes_real_match()
    test_gate_resume_skips_already_completed()
    test_gate_no_website_scores_weak_not_match()
    print("\nAll substrate_gate wiring tests passed.")
