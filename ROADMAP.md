# ROADMAP

Near-term, evidence-driven (each cites the prior art from the SoT §9):
- Reward/outcome-weighted traversal once FCL outcomes accumulate — beyond confidence-product Dijkstra (Retrieval-of-Thought, arXiv:2509.21743).
- Scale the A/B to hundreds of tasks via `measure/ab_variants.py` (contamination-resistant), independently audited (KGQAGen discipline, arXiv:2505.23495).
- Separate evidence-confidence from reasoning-confidence and split the single scalar into orthogonal fields (Double-Calibration, arXiv:2601.11956).
- Adaptive promotion threshold (RecMem flags fixed thresholds, arXiv:2605.16045).
- Adaptive compression-level selection per mined experience (arXiv:2604.15877, the "missing diagonal").
- Reuse `project_memory`'s synthesis-mud contradiction classifier for the typed `contradicts` channel.
- FCL auto-append hook (SoT lock #26): a local PostToolUse hook transcribing REFUSE stubs (gap_shape stays human).

## Explicitly out of scope
- No learned or opaque rankers — declared > inferred is the thesis; a learned signal here is a bug.
- No bundled model, no server, no network in the core (the A/B's model calls are an external, unbudgeted phase).
- No editing of instance-0 sources except through `migrate` / `loop freeze` / `loop retire`.
- No silent contradiction merging — REFUSE is the contract.
- No claim beyond "PoC evidence on this corpus" at N=30.
