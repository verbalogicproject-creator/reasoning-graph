# 07 — The historical A/B evaluation

The archived experiment used N=30 tasks in three subsets: 12 fixture (the engine was tuned on these, so they measure token cost rather than generalization), 10 organic, and 8 corpus-private.

Two arms, matched protocol (arXiv:2502.11371): arm A gets the task + only the graph slice; arm B gets the task alone. Both run as external headless `claude` subprocesses (measurement spends no build-session tokens), serialized and checkpointed (phone-hardened). Tokens come from usage metadata — the one legitimate `measured:` label. Scoring is deterministic (string / refusal-check); the report splits by subset (no blended headline) with Wilson intervals and McNemar's exact paired test.

Result: on corpus-private facts the graph arm answered 100% vs 50% (chance) at ~55% fewer output tokens; on organic 100% vs 70%; on fixture parity. The claim is fixed: **PoC evidence on this corpus (N=30); not a generalizable benchmark** — the small-N intervals and non-significant p-values are reported honestly. `ab_variants.py` is the road to hundreds later.
