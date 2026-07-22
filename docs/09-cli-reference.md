# 09 — CLI reference

`reasoning-graph <command> [--json]`. Every subcommand supports `--json` (one JSON object on stdout). Exit codes: 0 success (including `status=REFUSE` — a result), 1 error, 3 not-implemented stub.

- `schema validate --instance P` — validate a declaration.
- `migrate --instance P [--dry-run] [--no-backup]` — run m001.
- `resolve --instance P (--start A --end B | --text Q) [--unweighted] [--include-dormant] [--hard]` — traverse/answer.
- `analytics (pagerank|cycles) --instance P [--top N]`.
- `loop (scan|promote|mint|verify|freeze|retire) --instance P [--entry ID] [--matcher F] [--staged F] [--fixture F] [--approve]`.
- `measure (frontier-rate|ab-build-tasks|ab-variants|ab-run|ab-judge|ab-report) --instance P [--out DIR] [--tasks F] [--model M] [--arm A|B|both] [--k N]`.
- `demo` — the deterministic self-check.
