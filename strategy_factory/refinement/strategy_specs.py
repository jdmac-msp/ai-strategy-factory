"""
Strategy Factory field specs — *consumer #1* of the refinement engine.

These describe the inputs the factory actually needs, organised across the three
tiers we aligned on (Subject / Intent / Scope) and wired into a dependency graph
so the engine resolves them in the right order. The engine itself is generic;
all the domain knowledge lives here.

Adding depth to any one of these — a deep dive — yields a better, more grounded
run without forcing that depth on every field every time.
"""

from __future__ import annotations

from typing import List

from .engine import InputField


def strategy_fields() -> List[InputField]:
    return [
        # -- Subject: what is this company? ---------------------------------
        InputField(
            key="name",
            label="Company name",
            required=True,
            light_default="",
        ),
        InputField(
            key="industry",
            label="Industry",
            depends_on=["name"],
            required=True,  # decided up front, kept light
            light_default="Unknown / general",
            research_query="What industry and sub-sector does {name} operate in?",
            extract_prompt="State {name}'s primary industry and sub-sector in a few words.",
            clarify_focus="the company's industry and sub-sector",
            clarify_questions=3,
        ),
        InputField(
            key="company_size",
            label="Company size",
            depends_on=["name"],
            required=True,
            light_default="medium",
            research_query="Approximately how many employees does {name} have?",
            extract_prompt="Classify {name} as small, medium, large, or enterprise.",
            clarify_focus="company size band (small / medium / large / enterprise)",
            clarify_questions=2,
        ),
        InputField(
            key="tech_stack",
            label="Technology stack",
            depends_on=["name", "industry"],
            light_default=[],
            research_query="What core technologies and platforms does {name} use, "
            "typical for {industry}?",
            extract_prompt="List {name}'s likely core technologies as a short list.",
            clarify_focus="the current technology stack",
            clarify_questions=4,
        ),
        InputField(
            key="challenges",
            label="Pain points / challenges",
            depends_on=["industry", "company_size"],
            light_default=[],
            research_query="What are the top operational pain points for a "
            "{company_size} {industry} company like {name}?",
            extract_prompt="List the top 3-5 likely pain points.",
            clarify_focus="the most pressing business challenges",
            clarify_questions=5,
        ),

        # -- Intent: for whom, and to what end? -----------------------------
        InputField(
            key="objective",
            label="Strategic objective",
            depends_on=["challenges"],
            required=True,
            light_default="Identify high-ROI AI opportunities",
            clarify_focus="the single strategic outcome this engagement must drive",
            clarify_questions=3,
        ),
        InputField(
            key="audience",
            label="Primary audience",
            required=True,
            light_default="CEO",
            clarify_focus="the primary reader (CEO / CTO / board / investor)",
            clarify_questions=2,
        ),

        # -- Scope: what should the run produce? ----------------------------
        InputField(
            key="deliverables",
            label="Deliverable package",
            depends_on=["objective", "audience"],
            required=True,
            # Light default: the full factory. A deep dive narrows it to a
            # bundle matched to objective + audience.
            light_default="full",
            clarify_focus="which deliverables matter most given the objective and audience",
            clarify_questions=4,
        ),
        InputField(
            key="research_mode",
            label="Research depth",
            depends_on=["deliverables"],
            required=True,
            light_default="quick",
        ),
    ]
