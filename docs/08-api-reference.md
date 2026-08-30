# 08 — API reference

Public surface (`import reasoning_graph`):

- `GraphSchema`, `EdgeKind`, `ConfidenceRule`, `Profile`, `RetirementPolicy` — the declaration types.
- `load_instance(path) -> Instance` — load a descriptor + its `graphschema.py`.
- `is_valid_basis(label) -> bool`, `CLOSED_BASIS_EXACT`, `CLOSED_BASIS_PREFIXES`.

Modules:
- `store.Store.open(instance)` → `.nodes(kind=)`, `.edges(kind=)`, `.edge_confidence(s,t,kind)`, `.neighbors(id, direction)`, `.writer()`; `store.MissingConfidence`.
- `store.inspect_integrity(instance)` → a non-mutating report for kinds, endpoint references/types, confidence bases, exact typed duplicates, and SQLite foreign keys.
- `observations.record_observation(instance, ...)` / `read_observations(instance)` → bounded append-only feedback; these functions have no graph writer.
- `memory.propose/review/approve/dispute/supersede/retire` → append-only typed
  memory lifecycle; `memory.snapshot` returns full state and
  `memory.orientation` returns active session context.
- `providers.build_*_request` / `normalize_*_response` → offline native
  provider contracts and scrubbed `ProviderTurnRecord` observability.
- `workbench.create_app(instance_path)` → localhost-oriented FastAPI review UI.
- `mcp_server.create_server(instance_path)` → an instance-bound official-SDK MCP server.
- `migrations.m001_edge_confidence(instance, dry_run=, backup=)` → report dict.
- `resolver.resolve(instance, start=, end=, text=, weighted=, include_dormant=, hard=)` → Answer; `resolver.pagerank`, `resolver.cycles`, `resolver.dormant_mint_ids`.
- `refusal.draft_fcl_stub`, `refusal.REFUSAL_REASONS`.
- `primitives.adapter_for(instance)` → `SubprocessAdapter` | `GenericAdapter`.
- `loop.fcl` / `promote` / `mint` / `verify` / `freeze` / `retire`.
- `measure.frontier_rate.compute`, `measure.ab_tasks.build`, `ab_variants.generate`, `ab_run.run`, `ab_judge.judge`, `ab_report.report`.

The Answer JSON shape is backward-compatible and now includes
`{status, answer, path[], confidence, confidence_kind, path_class, support_kind, provenance[], refusal}`.
`support_kind` is `documented`, `derived`, or `minted`; provenance retains each
edge's confidence basis, synthesis chain, and evidence list.
