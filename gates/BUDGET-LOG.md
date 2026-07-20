# BUDGET-LOG

Opus 4.8 build session: log one row at EVERY gate attempt (pass or fail).
Budgets are total session tokens, `declared:planning_estimate`. Hard ceiling 1M.

Abort ladder (declared; docs bar is NON-NEGOTIABLE per Eyal 2026-07-19):
1. Two consecutive >50% phase overruns → drop Phase 8 (stretch corpus; G7 stays NOT-BUILT).
2. Still over → drop the LLM-judge fallback (string-match + refusal_check only; judge-keyed tasks re-keyed or excluded, recorded in the report).
3. NEVER trim docs/tests/gates — G8 runs in full regardless.

| When (phase/gate) | Verdict | Est. tokens spent so far | Phase budget | Note |
|---|---|---|---|---|
| Phase 0 / G0 | | | 30K | |
| Phase 1 / G1 | | | 90K | |
| Phase 2 / G2 | | | 70K | blocked until gates/eyal-approvals/edge-confidence-0.90.json exists (it does, 2026-07-20) |
| Phase 3 / G3 | | | 110K | on PASS: CORE-LOCK written AND git-committed |
| Phase 4 / G4 | | | 180K | |
| Phase 5 / G5 | | | 130K | |
| Phase 6 / G6 | | | 70K | ENTRY CONDITION: ab-spike-ok.json (one headless call, usage metadata parsed). Keep Termux foregrounded / wake lock for the run. |
| Phase 7 / G8 | | | 120K | |
| — Contingency / debug buffer | | | 120K | itemized per council 2026-07-20 (was silent headroom); G0 re-runs + gate-debug cycles charge HERE when they exceed a phase's own budget |
| Phase 8 / G7 (stretch) | | | 80K (reserve) | only if >=150K remains |

Accounting note: 800K phases + 120K contingency + 80K stretch = 1M ceiling. These
are declared:planning_estimate with NO grounding data — treat as a ceiling with
this abort plan, not a forecast; the actual-vs-declared column IS the dataset
that grounds the next project's estimates. INFRA-FLAKE verdicts (exit 5) are
re-run, not debugged — a phone hiccup is not a code regression.
