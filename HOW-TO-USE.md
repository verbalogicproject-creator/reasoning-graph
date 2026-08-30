# HOW-TO-USE

Task-oriented recipes. Every block is runnable; `--json` works on every subcommand.

## Declare a graph for your own corpus

A corpus is an instance directory with `instance.json` (paths + adapter) and `graphschema.py` (a module-level `SCHEMA: GraphSchema`). The core reads everything through that declaration. `instances/claude_code_tools/` is the canonical bundled instance; `tests/fixtures/tiny/` is an unrelated weaving domain used to catch hard-coded corpus assumptions.

```bash
reasoning-graph schema validate --instance instances/claude_code_tools/instance.json --json
reasoning-graph schema integrity --instance instances/claude_code_tools/instance.json --json
```

The descriptor resolves the generated clean database. It never falls back to
the immutable source database. Run `scripts/repair_instance_db.py` to
reproduce the clean database and its manifest.

## Query with the refusal boundary

```bash
# a composed multi-hop answer with a path-product confidence
reasoning-graph resolve --instance instances/claude_code_tools/instance.json \
  --start dep_003_tool_execution_requires_error_handling \
  --end constr_002_max_iterations_safety --json
```

`status` is `ANSWER` (≥ floor), `WEAK_ANSWER` (sub-floor, honest), or `REFUSE` with a reason (`no_frozen_support` / `contradiction` / `missing_confidence` / `unminted_edge_required` / `below_floor`). A REFUSE drafts a ready-to-append FCL stub.

## Migrate confidence onto edges

```bash
reasoning-graph migrate --instance instances/claude_code_tools/instance.json --dry-run --json
```

Additive column + per-class backfill from the declared `ConfidenceRule`s. Idempotent; backs up first on a real run.

## Run the loop

```bash
reasoning-graph loop scan    --instance instances/claude_code_tools/instance.json --json
reasoning-graph loop promote --instance instances/claude_code_tools/instance.json --json
```

`scan` parses the frontier-call log; `promote` lists recurring gap-shapes that are not yet disposed. `mint` → `verify` → `freeze` stage, validate, and activate a matcher; `retire` demotes on outcome evidence.

## Measure

```bash
reasoning-graph measure frontier-rate --instance instances/claude_code_tools/instance.json --json
```

The historical A/B evaluation pipeline is: `measure ab-build-tasks` → `ab-run` → `ab-judge` → `ab-report`. Live runs are optional, external, credentialed, and cost-bearing.
