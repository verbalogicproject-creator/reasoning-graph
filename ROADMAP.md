# ROADMAP

<!-- OPUS-FILLS: near-term items. Seed items (literature-grounded, from the SoT's prior-art section): -->
- Reward/outcome-weighted traversal policy once FCL outcomes accumulate (Retrieval-of-Thought, arXiv:2509.21743) — beyond confidence-product Dijkstra.
- Scale the A/B task set to hundreds via the parametric variant generator (`measure/ab_variants.py`), independently audited (KGQAGen discipline, arXiv:2505.23495).
- Separate evidence-confidence from reasoning-confidence (Double-Calibration, arXiv:2601.11956).
- Adaptive promotion threshold (RecMem flags fixed thresholds as non-adaptive, arXiv:2605.16045).
- Adaptive compression-level selection per mined experience — episodic vs procedural vs declarative rule (arXiv:2604.15877, the "missing diagonal").
- P0.5 Lane B narrative-prose mining (handbook2/3) — pending Eyal's scope call.
- Post-freeze A/B regression slice: re-run the 12 frozen fixture tasks (external headless CLI only) after every `loop freeze`, catching a minted edge that degrades tokens/accuracy before it's trusted (council 2026-07-20, Outside-the-Box).
- Reuse project_memory's synthesis-mud compatibility matrices for `contradicts`-edge classification instead of a third from-scratch contradiction assessor (council 2026-07-20).
- `provenance_column` on Profile: any edge kind claiming declared:structural/verbatim_extraction must point at its source record — "prove it's structural" (council 2026-07-20, Steelman).
- Split confidence semantics: extraction_fidelity vs inferential_trust as orthogonal fields, so ranking minimizes only over inferential trust (council 2026-07-20, Adversarial; PoC ships the disclosed single-scalar + path_class instead).
- Harvest this repo's own frontmatter `edges:` into project_memory's portfolio-edges.yaml (the framework as a node in the house graph).

## Explicitly out of scope

<!-- OPUS-FILLS — required section, house pattern. Seed: no learned rankers; no bundled model; no server; no editing instance-0 sources; no silent contradiction merging (REFUSE is the contract). -->
