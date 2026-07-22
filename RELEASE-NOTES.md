# RELEASE-NOTES

## 0.1.0 — PoC

Built against `Reasoning-Graph-source-of-truth-2026-07-19.ngf.md` by the Opus 4.8 session. Gates **G0–G6 green** (the declared smallest-useful slice); G8 (codification bar) green; G7 (second-corpus stretch) optional.

### What shipped
- Corpus-agnostic core: `GraphSchema` declaration → store → migration → resolver + refusal boundary → mechanized loop (mint/verify/freeze/retire) → measurement (frontier-rate + A/B).
- Instance 0 (`claude-code-tools`): 856 edges carry numeric confidence after `m001` (was zero — the load-bearing retrofit).
- The A/B proof ran (N=30, sonnet, matched protocol) and the frontier-call rate was computed off the live log.

### Headline result (honest)
- **corpus-private subset (facts only the graph holds):** graph arm 100% vs prose arm 50% (chance), at ~55% fewer output tokens — the clean signal.
- **organic:** graph arm 100% vs prose 70% (it caught the zero-coverage refusal cases).
- **fixture (tuned-on):** both 100% at near-parity token cost — measures cost, not generalization.
- **frontier-call rate:** 0.41 → 0.08 across the two historical organic batches (falling).

### What's honest about the scope
- **N=30 is PoC evidence on this corpus, not a generalizable benchmark.** Per-subset Wilson intervals are wide (n≤12) and McNemar p-values (0.125–0.25) are **not statistically significant** — this is a *direction*, not proof. Scaling to hundreds is on the ROADMAP (the parametric variant generator exists).
- **`path_product_score` is a ranking score, not a calibrated probability.** The report's confidence↔correctness correlation is exploratory only.
- **Retirement is fixture-proven, not yet exercised by organic instance-0 usage** — architected ahead of need (SkillOps degradation kicks in at 200–2000 rules; this PoC has 1 minted rule).
- **The 0.90 inherited-curation default** is a declared value confirmed by Eyal (gates/eyal-approvals/), not a measured one.
- **Temperature is not exposed by the `claude` CLI**, so both arms use its default (identical for both — the comparison stays matched, but "temp 0" is aspirational, not enforced).
- **The frontier-rate baseline is 2 batches / 48 queries** — small; a trend, not a law.
