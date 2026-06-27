"""
Adversarial gauntlet for the entity-resolution gate (`resolve_entity`).

This is the FIRST regression suite in the repo. It stress-tests the proven
`strategy_factory/substrate.py::resolve_entity` against the corpus a Codex
red-team specified (Mercury/Pilot/Linear/Apollo/Browser-Co + the two real
floor-test cases Steve & Joel), plus the gate's known false-positive /
false-negative edges.

Design:
- CONTRACT cases assert the gate's required behavior. Any CONTRACT failure
  fails the suite (exit 1) — this is the "don't touch it again" insurance.
- KNOWN-GAP cases document where the gate is intentionally not yet sufficient
  (alias domains, domain-string≠identity, claim-level bleed). They assert the
  CURRENT behavior and are reported but do NOT fail the suite — they are the
  empirical case for the un-built result-filter (GAP 2 in the seam handoff).

Run:  python tests/gauntlet_entity_gate.py
"""
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from strategy_factory.substrate import resolve_entity, MatchStatus, from_state  # noqa: E402

M, W, X = MatchStatus.MATCH, MatchStatus.WEAK, MatchStatus.MISMATCH

# ─────────────────────────────────────────────────────────────────────────────
# Each case: (id, kind, seed_name, seed_url, resolved_name, resolved_desc,
#             sources, expect_status, note)
#   kind = "contract"  → must hold; failure fails the suite
#   kind = "known_gap" → documents a current limitation; reported, never fails
# ─────────────────────────────────────────────────────────────────────────────
CASES = [
    # ── BUCKET 1 — MUST BLOCK: same-name collision, seed domain absent ────────
    ("steve-impostor", "contract", "Steve Cunningham", "stevecunningham.ai",
     "Steve Cunningham & Associates Limited",
     "Steve Cunningham & Associates Limited was set up on 11 June 1990. Registered office in Galway.",
     ["https://find-and-update.company-information.service.gov.uk/company/123",
      "https://opencorporates.com/companies/gb/123"],
     X, "1990 UK registry record, seed domain never sourced → BLOCK"),

    ("mercury-marine", "contract", "Mercury", "mercury.com",
     "Mercury Marine",
     "Mercury Marine manufactures outboard boat motors; founded 1939 in Wisconsin.",
     ["https://www.mercurymarine.com/", "https://www.boats.com/mercury"],
     X, "boat-motor namesake, mercury.com absent → BLOCK"),

    ("pilot-flyingj", "contract", "Pilot", "pilot.com",
     "Pilot Flying J",
     "Pilot Flying J operates truck stops and travel centers across North America.",
     ["https://pilotflyingj.com/", "https://en.wikipedia.org/wiki/Pilot_Flying_J"],
     X, "truck-stop namesake, pilot.com absent → BLOCK"),

    ("apollo-pe", "contract", "Apollo", "apollo.io",
     "Apollo Global Management",
     "Apollo Global Management is a private equity firm; founded 1990.",
     ["https://www.apollo.com/", "https://www.sec.gov/apollo"],
     X, "PE namesake, 1990 founding, apollo.io absent → BLOCK"),

    ("linear-tech", "contract", "Linear", "linear.app",
     "Linear Technology",
     "Linear Technology, a semiconductor company, was incorporated in 1981 and acquired by Analog Devices.",
     ["https://www.analog.com/linear", "https://en.wikipedia.org/wiki/Linear_Technology"],
     X, "semiconductor namesake, 'incorporated', linear.app absent → BLOCK"),

    # ── BUCKET 2 — MUST PASS: legit entity, seed domain present in sources ────
    ("mercury-fintech", "contract", "Mercury", "mercury.com",
     "Mercury",
     "Mercury is a banking platform built for startups and founders.",
     ["https://mercury.com/", "https://techcrunch.com/mercury-banking"],
     M, "real fintech, mercury.com sourced → PASS"),

    ("joel-real", "contract", "Joel Erway", "joelerway.com",
     "Joel Erway",
     "Joel Erway is the founder of High Ticket Courses and host of Experts Unleashed; creator of the Power Offer.",
     ["https://joelerway.com/", "https://highticketcourses.com/"],
     M, "real Joel, joelerway.com sourced → PASS"),

    ("steve-corrected", "contract", "Steve Cunningham", "stevecunningham.ai",
     "Steve Cunningham",
     "Steve Cunningham is an AI business-transformation advisor; founder of Simple Academy and Humans+Agents.",
     ["https://stevecunningham.ai/", "https://www.linkedin.com/in/stevecunningham"],
     M, "correct Steve, stevecunningham.ai sourced → PASS (discrimination check)"),

    ("browserco-arc", "contract", "The Browser Company", "arc.net",
     "Arc",
     "Arc is a web browser developed by The Browser Company of New York.",
     ["https://arc.net/", "https://thebrowser.company/"],
     M, "legal-name≠brand: name overlap ~0 but arc.net sourced carries it → PASS"),

    # ── BUCKET 3 — KNOWN GAPS: document the gate's current edges ──────────────
    ("joel-alias-domain", "known_gap", "Joel Erway", "joelerway.com",
     "Joel Erway",
     "Joel Erway runs High Ticket Courses, teaching consultants to sell high-ticket programs.",
     ["https://highticketcourses.com/", "https://www.powerofferworkshop.com/"],
     X, "FALSE POSITIVE: real Joel BLOCKED because content sits on a sibling domain, "
        "not the seed. Fix = alias/related-domains in the seed (Codex rec)."),

    ("mercury-domain-coincidence", "known_gap", "Mercury", "mercury.com",
     "Mercury Insurance",
     "Mercury Insurance offers auto and home insurance. See listing referencing mercury.com.",
     ["https://www.mercuryinsurance.com/", "https://directory.example.com/mercury.com-listing"],
     M, "FALSE NEGATIVE: wrong entity PASSES because the seed-domain STRING appears "
        "in a source URL. Domain-string match ≠ identity proof (Codex vector #5)."),

    ("joel-claim-bleed", "known_gap", "Joel Erway", "joelerway.com",
     "Joel Erway",
     "Joel Erway, founder of High Ticket Courses. In a recent project she built a tool for "
     "schema discovery over clinical trial databases. Industry growth was 12.02% annually.",
     ["https://joelerway.com/", "https://highticketcourses.com/"],
     M, "GAP 2 PROOF: correct entity PASSES, yet a foreign-bio claim ('she'/clinical "
        "trials) and a fabricated 12.02% stat ride through untouched. The entity gate "
        "structurally cannot see claim-level bleed → needs the upstream result-filter."),

    ("no-website", "known_gap", "Acme Advisors", "",
     "Acme Advisors",
     "Acme Advisors is a boutique consulting firm.",
     ["https://example.com/acme", "https://acmeadvisors.example/"],
     W, "NO-URL: without a seed domain the gate can only WARN, never BLOCK. "
        "'Name only but careful' is exactly the failed mode (capture the URL)."),
]


def run():
    print("=" * 78)
    print("ENTITY-GATE GAUNTLET — adversarial regression suite")
    print("=" * 78)
    contract_fail = 0
    rows = []
    for cid, kind, sn, su, rn, rd, src, expect, note in CASES:
        er = resolve_entity(sn, su, rn, rd, src)
        ok = er.status == expect
        if kind == "contract" and not ok:
            contract_fail += 1
        mark = "PASS" if ok else "FAIL"
        if kind == "known_gap":
            mark = "DOC " if ok else "DRIFT"  # gap behavior changed = worth a look
        rows.append((mark, kind, cid, er.status.value, expect.value,
                     f"{er.confidence:.2f}", "BLOCK" if er.blocking else "", note))

    w = max(len(r[2]) for r in rows)
    print(f"\n{'res':5} {'kind':9} {'case':{w}}  got→exp        conf  blk")
    print("-" * 78)
    for mark, kind, cid, got, exp, conf, blk, note in rows:
        print(f"{mark:5} {kind:9} {cid:{w}}  {got:8}→{exp:8} {conf:>4} {blk:5}")
    print("\nNotes:")
    for mark, kind, cid, *_rest, note in rows:
        print(f"  [{cid}] {note}")

    # ── Real-data cases via from_state (zero API cost) ────────────────────────
    print("\n" + "=" * 78)
    print("REAL-DATA CASES — from_state() on actual floor-test runs")
    print("=" * 78)
    real_dirs = {
        "steve-cunningham": r"G:\COWORK\Projects\ai-strategy-factory\runs\steve-cunningham",
        "joel-erway": r"G:\COWORK\Projects\ai-strategy-factory\runs\joel-erway",
    }
    for label, d in real_dirs.items():
        if not pathlib.Path(d).exists():
            print(f"  {label}: run dir not found ({d}) — skipped")
            continue
        try:
            sub = from_state(d)
            e = sub.entity
            print(f"  {label}: {e.status.value.upper()} (conf {e.confidence:.2f}, "
                  f"blocking={e.blocking}) seed_domain_in_sources={e.seed_domain_in_sources}")
            print(f"     → {'; '.join(e.evidence[:2])}")
        except Exception as ex:  # noqa: BLE001
            print(f"  {label}: from_state error → {ex!r}")
    print("  (Both real runs were generated WITHOUT a captured seed URL — so the gate "
          "can only WARN, not BLOCK. This is the live evidence for GAP 1 / RP-8: "
          "the seed URL must be first-class input.)")

    # ── Verdict ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 78)
    n_contract = sum(1 for c in CASES if c[1] == "contract")
    n_gap = sum(1 for c in CASES if c[1] == "known_gap")
    if contract_fail == 0:
        print(f"GAUNTLET PASS — {n_contract}/{n_contract} contract cases hold; "
              f"{n_gap} known-gap cases documented.")
    else:
        print(f"GAUNTLET FAIL — {contract_fail}/{n_contract} contract cases regressed.")
    print("=" * 78)
    return 1 if contract_fail else 0


if __name__ == "__main__":
    sys.exit(run())
