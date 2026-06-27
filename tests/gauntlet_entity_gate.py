"""
Adversarial gauntlet for the entity-resolution gate (`resolve_entity`).

First regression suite in the repo. Stress-tests
`strategy_factory/substrate.py::resolve_entity` against the corpus a Codex
red-team specified + a Codex cross-model audit of this suite (2026-06-27).

Case kinds:
- "contract"  → required behavior; any failure fails the suite (exit 1).
- "known_gap" → a CURRENT limitation of the gate, asserted at its present
  behavior and reported, never fatal. Drift on a known_gap is printed loudly
  (a fix may have landed upstream — review it).

Run:  python tests/gauntlet_entity_gate.py
      GAUNTLET_RUNS_DIR=/path/to/runs python tests/gauntlet_entity_gate.py
"""
import os, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from strategy_factory.substrate import resolve_entity, MatchStatus, from_state  # noqa: E402

M, W, X = MatchStatus.MATCH, MatchStatus.WEAK, MatchStatus.MISMATCH

# (id, kind, seed_name, seed_url, resolved_name, resolved_desc, sources, expect, note)
CASES = [
    # ── MUST BLOCK: same-name collision, seed domain absent ───────────────────
    ("steve-impostor", "contract", "Steve Cunningham", "stevecunningham.ai",
     "Steve Cunningham & Associates Limited",
     "Steve Cunningham & Associates Limited was set up on 11 June 1990. Registered office in Galway.",
     ["https://find-and-update.company-information.service.gov.uk/company/123",
      "https://opencorporates.com/companies/gb/123"],
     X, "1990 UK registry record, seed domain never sourced → BLOCK"),
    ("mercury-marine", "contract", "Mercury", "mercury.com", "Mercury Marine",
     "Mercury Marine manufactures outboard boat motors; founded 1939 in Wisconsin.",
     ["https://www.mercurymarine.example/", "https://www.boats.example/mercury"],
     X, "boat-motor namesake, mercury.com absent → BLOCK"),
    ("pilot-flyingj", "contract", "Pilot", "pilot.com", "Pilot Flying J",
     "Pilot Flying J operates truck stops and travel centers across North America.",
     ["https://pilotflyingj.example/", "https://en.wikipedia.org/wiki/Pilot_Flying_J"],
     X, "truck-stop namesake, pilot.com absent → BLOCK"),
    ("apollo-pe", "contract", "Apollo", "apollo.io", "Apollo Global Management",
     "Apollo Global Management is a private equity firm; founded 1990.",
     ["https://www.apollo-pe.example/", "https://www.sec.gov/apollo"],
     X, "PE namesake, 1990 founding, apollo.io absent → BLOCK"),
    ("linear-tech", "contract", "Linear", "linear.app", "Linear Technology",
     "Linear Technology, a semiconductor company, was incorporated in 1981 and acquired by Analog Devices.",
     ["https://www.analog.example/linear", "https://en.wikipedia.org/wiki/Linear_Technology"],
     X, "semiconductor namesake, 'incorporated', linear.app absent → BLOCK"),

    # ── MUST PASS: legit entity, seed domain present in sources ───────────────
    ("mercury-fintech", "contract", "Mercury", "mercury.com", "Mercury",
     "Mercury is a banking platform built for startups and founders.",
     ["https://mercury.com/", "https://techcrunch.com/mercury-banking"],
     M, "real fintech, mercury.com sourced → PASS"),
    ("joel-real", "contract", "Joel Erway", "joelerway.com", "Joel Erway",
     "Joel Erway is the founder of High Ticket Courses and host of Experts Unleashed; creator of the Power Offer.",
     ["https://joelerway.com/", "https://highticketcourses.com/"],
     M, "real Joel, joelerway.com sourced → PASS"),
    ("steve-corrected", "contract", "Steve Cunningham", "stevecunningham.ai", "Steve Cunningham",
     "Steve Cunningham is an AI business-transformation advisor; founder of Simple Academy and Humans+Agents.",
     ["https://stevecunningham.ai/", "https://www.linkedin.com/in/stevecunningham"],
     M, "correct Steve, stevecunningham.ai sourced → PASS (discrimination check)"),
    ("browserco-arc", "contract", "The Browser Company", "arc.net", "Arc",
     "Arc is a web browser developed by The Browser Company of New York.",
     ["https://arc.net/", "https://thebrowser.company/"],
     M, "legal-name≠brand: name overlap ~0 but arc.net sourced carries it (0.70) → PASS"),
    ("joel-claim-bleed", "contract", "Joel Erway", "joelerway.com", "Joel Erway",
     "Joel Erway, founder of High Ticket Courses. In a recent project she built a tool for "
     "schema discovery over clinical trial databases. Industry growth was 12.02% annually.",
     ["https://joelerway.com/", "https://highticketcourses.com/"],
     M, "Gate CORRECTLY passes (right entity). The foreign-bio claim ('she'/clinical trials) "
        "and fabricated 12.02% stat are INVISIBLE to identity resolution by design — that is "
        "GAP 2's job (upstream result-filter), not a gate defect. Kept as a contract MATCH "
        "so a regression that BLOCKS the right entity here gets caught."),
    ("empty-inputs", "contract", "", "", "", "", [],
     X, "robustness: empty seed/resolved/sources must not crash; no signal → MISMATCH"),

    # ── KNOWN GAPS: document the gate's current edges (not fatal) ──────────────
    ("host-boundary-substring", "known_gap", "Mercury", "mercury.com", "Notmercury Corp",
     "A different company entirely, unrelated to the fintech.",
     ["https://notmercury.com/", "https://mercury.com.evil.example/"],
     M, "GAP 3 / VULN: 'mercury.com' SUBSTRING-matches 'notmercury.com' and "
        "'mercury.com.evil.example' → false MATCH. Domain check must be host-boundary "
        "(registrable domain / exact host), not `seed_domain in blob`."),
    ("desc-only-domain", "known_gap", "Mercury", "mercury.com", "Mercury Insurance",
     "Mercury Insurance (auto/home). This blurb happens to mention mercury.com in passing.",
     [],
     M, "FALSE NEGATIVE: zero real sources, but the seed domain in the DESCRIPTION text "
        "satisfies the blob check → MATCH. Domain evidence should come from source URLs, not prose."),
    ("registry-cap-falsepos", "known_gap", "Acme Labs", "acmelabs.example", "Acme Labs",
     "Acme Labs, a modern AI software company, was incorporated in 1998. See acmelabs.example.",
     ["https://acmelabs.example/", "https://www.linkedin.com/company/acme-labs"],
     W, "FALSE POSITIVE demotion: a LEGIT company whose own site is sourced is capped to WEAK "
        "because 'incorporated' + a 19xx year trip the registry red-flag even with the domain "
        "present. The year/registry flag should only fire when the domain is ABSENT."),
    ("joel-alias-domain", "known_gap", "Joel Erway", "joelerway.com", "Joel Erway",
     "Joel Erway runs High Ticket Courses, teaching consultants to sell high-ticket programs.",
     ["https://highticketcourses.com/", "https://www.powerofferworkshop.com/"],
     X, "FALSE POSITIVE: real Joel BLOCKED because content sits on a sibling domain, not the "
        "seed. Fix = alias/related-domains in the seed (Codex rec)."),
    ("no-website", "known_gap", "Acme Advisors", "", "Acme Advisors",
     "Acme Advisors is a boutique consulting firm.",
     ["https://example.com/acme", "https://acmeadvisors.example/"],
     W, "NO-URL is UNRELIABLE (not safe): the strong domain signal is gone, so the verdict "
        "rides on weak name-overlap. Here 100% overlap → WEAK; a LOW-overlap no-URL case would "
        "MISMATCH (can wrongly block a legit entity). Capture the seed URL."),
]


def run():
    print("=" * 80)
    print("ENTITY-GATE GAUNTLET — adversarial regression suite (Codex-audited)")
    print("=" * 80)
    contract_fail, drift = 0, 0
    rows = []
    for cid, kind, sn, su, rn, rd, src, expect, note in CASES:
        er = resolve_entity(sn, su, rn, rd, src)
        status_ok = er.status == expect
        blocking_ok = er.blocking == (expect == X)        # blocking must track MISMATCH
        ok = status_ok and blocking_ok
        if kind == "contract":
            if not ok:
                contract_fail += 1
            mark = "PASS" if ok else "FAIL"
        else:
            if not ok:
                drift += 1
            mark = "DOC" if ok else "DRIFT"
        rows.append((mark, kind, cid, er.status.value, expect.value,
                     f"{er.confidence:.2f}", "BLOCK" if er.blocking else ""))

    w = max(len(r[2]) for r in rows)
    print(f"\n{'res':5} {'kind':9} {'case':{w}}  got→exp           conf  blk")
    print("-" * 80)
    for mark, kind, cid, got, exp, conf, blk in rows:
        print(f"{mark:5} {kind:9} {cid:{w}}  {got:8}→{exp:8} {conf:>5} {blk}")
    print("\nNotes:")
    for c in CASES:
        print(f"  [{c[0]}] {c[8]}")

    # ── Real-data cases via from_state (zero API cost) ────────────────────────
    print("\n" + "=" * 80)
    print("REAL-DATA CASES — from_state() on actual floor-test runs")
    print("=" * 80)
    runs_base = pathlib.Path(os.environ.get(
        "GAUNTLET_RUNS_DIR", r"G:\COWORK\Projects\ai-strategy-factory\runs"))
    real = {"steve-cunningham": W, "joel-erway": W}   # both: no seed URL captured → WEAK
    ran = 0
    for label, expect in real.items():
        d = runs_base / label
        if not d.exists():
            print(f"  {label}: run dir not found ({d}) — skipped")
            continue
        try:
            e = from_state(str(d)).entity
            ran += 1
            verdict = "OK" if e.status == expect else "DRIFT"
            if e.status != expect:
                drift += 1
            print(f"  [{verdict}] {label}: {e.status.value.upper()} (conf {e.confidence:.2f}, "
                  f"blocking={e.blocking}, domain_in_sources={e.seed_domain_in_sources}) — expected {expect.value}")
        except Exception as ex:  # noqa: BLE001
            drift += 1
            print(f"  [DRIFT] {label}: from_state error → {ex!r}")
    if ran:
        print("  → Both real runs were generated WITHOUT a captured seed URL, so the gate can only "
              "WARN here. Live evidence for GAP 1 / RP-8: make the seed URL first-class input.")

    # ── Verdict ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    n_contract = sum(1 for c in CASES if c[1] == "contract")
    n_gap = sum(1 for c in CASES if c[1] == "known_gap")
    if drift:
        print(f"⚠ {drift} known-gap/real-data case(s) DRIFTED — a fix may have landed upstream; review.")
    if contract_fail == 0:
        print(f"GAUNTLET PASS — {n_contract}/{n_contract} contract cases hold; "
              f"{n_gap} known-gaps + {ran} real-data cases checked.")
    else:
        print(f"GAUNTLET FAIL — {contract_fail}/{n_contract} contract cases regressed.")
    print("=" * 80)
    return 1 if contract_fail else 0


if __name__ == "__main__":
    sys.exit(run())
