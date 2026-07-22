# 08 — API reference

Public surface (`import reasoning_graph`):

- `GraphSchema`, `EdgeKind`, `ConfidenceRule`, `Profile`, `RetirementPolicy` — the declaration types.
- `load_instance(path) -> Instance` — load a descriptor + its `graphschema.py`.
- `is_valid_basis(label) -> bool`, `CLOSED_BASIS_EXACT`, `CLOSED_BASIS_PREFIXES`.

Modules:
- `store.Store.open(instance)` → `.nodes(kind=)`, `.edges(kind=)`, `.edge_confidence(s,t,kind)`, `.neighbors(id, direction)`, `.writer()`; `store.MissingConfidence`.
- `migrations.m001_edge_confidence(instance, dry_run=, backup=)` → report dict.
- `resolver.resolve(instance, start=, end=, text=, weighted=, include_dormant=, hard=)` → Answer; `resolver.pagerank`, `resolver.cycles`, `resolver.dormant_mint_ids`.
- `refusal.draft_fcl_stub`, `refusal.REFUSAL_REASONS`.
- `primitives.adapter_for(instance)` → `SubprocessAdapter` | `GenericAdapter`.
- `loop.fcl` / `promote` / `mint` / `verify` / `freeze` / `retire`.
- `measure.frontier_rate.compute`, `measure.ab_tasks.build`, `ab_variants.generate`, `ab_run.run`, `ab_judge.judge`, `ab_report.report`.

The Answer JSON shape: `{status, answer, path[], confidence, confidence_kind, path_class, refusal}`.
