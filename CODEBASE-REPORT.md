# CODEBASE-REPORT

## The one call graph

```
cli.py ──┬─ schema.py           (GraphSchema, ConfidenceRule, Profile, load_instance)
         ├─ store.py            (Store: profile-driven reads, MissingConfidence, writer)
         ├─ migrations.py       (m001_edge_confidence)
         ├─ resolver.py ── refusal.py   (resolve/pagerank/cycles → Answer)
         │        └─ primitives.py       (SubprocessAdapter / GenericAdapter)
         ├─ loop/  fcl · promote · mint · verify · freeze · retire
         └─ measure/ frontier_rate · ab_tasks · ab_variants · ab_run · ab_judge · ab_report
```

## Module table

| Module | Responsibility | Key symbols |
|---|---|---|
| `schema.py` | the one declaration object; closed basis vocab | `GraphSchema`, `EdgeKind`, `ConfidenceRule`, `Profile`, `RetirementPolicy`, `load_instance` |
| `store.py` | sqlite reads via the profile; refuse on missing confidence | `Store`, `MissingConfidence` |
| `migrations.py` | additive edge-confidence backfill | `m001_edge_confidence` |
| `resolver.py` | traversal, path-product, pagerank, cycles | `resolve`, `pagerank`, `cycles`, `dormant_mint_ids` |
| `refusal.py` | the refusal boundary + FCL stub drafting | `REFUSAL_REASONS`, `draft_fcl_stub` |
| `primitives.py` | typed-query adapters | `adapter_for`, `SubprocessAdapter`, `GenericAdapter` |
| `loop/*` | mint→verify→freeze→retire, mechanized | `parse_log`, `detect`, `stage`, `verify`, `freeze`, `retire_pass` |
| `measure/*` | frontier-rate + the A/B proof | `frontier_rate.compute`, `ab_tasks.build`, `ab_run.run`, `ab_report.report` |

## Data shapes

- **Answer** — `{status, answer, path[], confidence, confidence_kind, path_class, refusal}`.
- **FCL entry** — `### <ID> — <one-line> [<status>]` + `- key: value` lines + `- gap_shape:`.
- **matcher-v2** — human sections + a fenced ```yaml block (JSON body: `mint_id`, `provenance`, `confidence`, `signature_sql`, `confirm[]`, `fix{edge_kind, pairs_sql, properties_template}`).
- **edge confidence** — `confidence REAL` column + `confidence_basis` in `properties` JSON.

## Where to change things

| Want to… | Touch |
|---|---|
| support a new corpus | a new `instances/<name>/` (schema + instance.json) — **no core edits** (G7) |
| change retrieval/traversal math | `resolver.py` (core; never instance vocabulary) |
| add a confidence-derivation rule | the instance's `graphschema.py` `ConfidenceRule`s + `migrations.py` if a new basis |
| add a loop stage | `loop/` + the CLI dispatch |
