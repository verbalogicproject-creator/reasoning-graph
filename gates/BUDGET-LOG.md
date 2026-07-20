# BUDGET-LOG

Opus 4.8 build session: log one row at EVERY gate attempt (pass or fail).
Budgets are total session tokens, `declared:planning_estimate`. Hard ceiling 1M.

Abort ladder (declared; docs bar is NON-NEGOTIABLE per Eyal 2026-07-19):
1. Two consecutive >50% phase overruns → drop Phase 8 (stretch corpus; G7 stays NOT-BUILT).
2. Still over → drop the LLM-judge fallback (string-match + refusal_check only; judge-keyed tasks re-keyed or excluded, recorded in the report).
3. NEVER trim docs/tests/gates — G8 runs in full regardless.

| When (phase/gate) | Verdict | Est. tokens spent so far | Phase budget | Note |
|---|---|---|---|---|
| Phase 0 / G0 | PASS | baseline | 30K | SoT read; G0 10/10 green |
| Phase 1 / G1 | checks 1-3 PASS; check 4 NOT-BUILT | ~within est | 90K | store.py done + smoke-verified (reads/confidence/MissingConfidence/undeclared-raise). G1 check 4 (resolve) is Phase-3-dependent by gate design → G1 reaches full PASS at Phase 3. FLAGGED to Eyal, not a failure. |
| Phase 2 / G2 | PASS | ~within est | 70K | m001 applied to instance-0 (856/856, null_remaining 0, idempotent, backup written). Dry-run counts matched hand-computed table exactly. Finding RG-1: corpus-min fallback (0.70) was prose-only in graphschema; made machine-readable via _RULE_DERIVED.value. Approval artifact honored. resolver cross-check SKIP (Phase 3). G0 re-run PASS. |
| Phase 3 / G3 | PASS | ~within est | 110K | resolver+refusal+primitives done. All 6 tiny scenarios + instance-0 chain product (1e-16 match) + G1 check 4 + G2 resolver cross-check now green. CORE-LOCK written+committed (23 files). FLAG: g3 writes CORE-LOCK at Phase 3, but loop/ + measure/ (core) are built in Phases 4-6 → CORE-LOCK must be REFRESHED at end of Phase 7 before any Phase 8/G7 attempt (transparent, committed). Harmless until then — G7 is stretch-only; G8 does not check CORE-LOCK. |
| Phase 4 / G4 | PASS | ~within est | 180K | loop/ complete (fcl/promote/mint/verify/freeze/retire). History reproduced exactly: recurring={FCL-001,007,008,009}, promotable={} (FCL-008 rejection respected). Fixture loop mint->verify->freeze x2 idempotent; retirement demote-not-delete (ratio before cap). RG-2: fenced §1 schema template was mis-parsed as an entry (fixed: skip code fences). RG-3: freeze deleted staged, breaking the twice-run idempotency check (fixed: copy-to-minted, keep staged). G0-G4 all PASS. |
| Phase 5 / G5 | PASS | ~within est | 130K | frontier_rate.compute done; series matches G5's independent re-parse exactly (11 entries, first divergence None). Frontier-call rate computed as FALLING (0.4091 -> 0.0769 across the 2 organic batches), honestly hedged for small N. G0-G5 all green. ab_tasks/ab_variants deferred to Phase 6 (gated by G6, not G5). |
| Phase 6 / G6 | PASS | ~within est | 70K | SPIKE PASSED (headless claude -p --output-format json returns parseable usage — most-dangerous assumption CLEARED). 60 serialized arm calls (sonnet), 0 retries, checkpointed. Honest result: corpus_private A=1.0 vs B=0.5 (only graph knows), -55% output tokens; organic A=1.0 vs B=0.7; fixture 1.0/1.0 parity. Small-N Wilson+McNemar honestly show directional-not-significant. All 30 deterministic keys (0 judge cost). G6 all 20 checks PASS. **SMALLEST USEFUL SLICE G0-G6 COMPLETE.** |
| Phase 7 / G8 | | | 120K | |
| — Contingency / debug buffer | | | 120K | itemized per council 2026-07-20 (was silent headroom); G0 re-runs + gate-debug cycles charge HERE when they exceed a phase's own budget |
| Phase 8 / G7 (stretch) | | | 80K (reserve) | only if >=150K remains |

Accounting note: 800K phases + 120K contingency + 80K stretch = 1M ceiling. These
are declared:planning_estimate with NO grounding data — treat as a ceiling with
this abort plan, not a forecast; the actual-vs-declared column IS the dataset
that grounds the next project's estimates. INFRA-FLAKE verdicts (exit 5) are
re-run, not debugged — a phone hiccup is not a code regression.
