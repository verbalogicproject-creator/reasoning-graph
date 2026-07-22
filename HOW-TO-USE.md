# HOW-TO-USE

Task-oriented recipes. Every block is runnable; `--json` works on every subcommand.

## Declare a graph for your own corpus

A corpus is an instance directory with `instance.json` (paths + adapter) and `graphschema.py` (a module-level `SCHEMA: GraphSchema`). The core reads everything through that declaration — see `instances/claude_code_tools/` and `tests/fixtures/tiny/` (an alien weaving domain with non-default table/column names, proving nothing is hardcoded).

```bash
reasoning-graph schema validate --instance instances/claude_code_tools/instance.json --json
```

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

`scan` parses the frontier-call log; `promote` lists recurring gap-shapes that are not yet disposed. `mint` → `verify` → `freeze` stage, prove, and freeze a matcher; `retire` demotes on outcome evidence.

## Measure

```bash
reasoning-graph measure frontier-rate --instance instances/claude_code_tools/instance.json --json
```

The A/B proof (external, headless, spends no build-session tokens): `measure ab-build-tasks` → `ab-run` → `ab-judge` → `ab-report`.
