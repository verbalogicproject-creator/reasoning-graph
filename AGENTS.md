# AGENTS.md

## Repository purpose

This repository is the lab and instance-0 dataset for the **reasoning-graph** idea: lower recurring reasoning from model-generated prose into typed, confidence-weighted graph relationships that can be retrieved and traversed deterministically.

Do not describe the entire repository as one production application. The currently supported proof-of-concept surface is:

- `query.py`
- `p2_fixture_runner.py`
- `p2-acceptance-fixture.json`
- `kgs/reasoning-graph.db`
- `systems/nai/`
- `claude-code-tools/`
- `synthesis-rules/`

`systems/eco-system/`, most of `python/`, copied KGs, indexes, reports, and lowering-ladder documents are inherited research material, donors, or historical context unless a task explicitly places them in scope.

## Required read order

Before making a material change, read:

1. `reasoning-graph-context-datapacket-2026-07-12.ngf.md`
2. `implementation-plan-reasoning-graph-v2-2026-07-13.md`
3. `CLAUDE.md`
4. `CODEBASE-AUDIT-2026-08-29.md` for the current verified health baseline

When working under `systems/nai/` or `systems/eco-system/`, read that subsystem's `CLAUDE.md` before its source.

The July documents refer to a separate generalized framework at `/root/projects/reasoning_graph/`. Do not treat claims or test results from that external project as current proof for this repository unless the task explicitly includes it and it is reverified.

## Current verified baseline

- The focused P2 fixture passes 20/20 and all 3 canonical queries.
- `query.py` can recommend tool workflows and traverse the current graph.
- NAI search, path, PageRank, roles, and cycles run against `kgs/reasoning-graph.db`.
- SQLite page integrity passes, but the DB currently has 44 foreign-key violations representing 21 missing target nodes.
- NAI currently collapses parallel relationships in its simple directed-graph projection.
- The eco-system's full runner is broken; explicit invocation runs 220 tests with 3 failures and 35 errors as of 2026-08-29.
- The workspace is not currently a Git checkout.

Do not silently update these claims. Re-run the relevant command and record new evidence.

## Commands

Run commands from the repository root unless noted.

```sh
# Focused acceptance suite
python3 p2_fixture_runner.py

# Focused CLI examples
python3 query.py --list
python3 query.py --compose-for "fix a bug found via search" --json
python3 query.py --can-it "access the internet" --json

# Compile the focused Python surfaces
python3 -m compileall -q query.py p2_fixture_runner.py python systems/nai

# NAI (run from systems/)
cd systems
python3 -m nai --db ../kgs/reasoning-graph.db --query "search caching" --json
python3 -m nai --db ../kgs/reasoning-graph.db \
  --query "path dep_003_tool_execution_requires_error_handling constr_002_max_iterations_safety" \
  --json

# Read-only DB validation
sqlite3 -readonly kgs/reasoning-graph.db "PRAGMA integrity_check;"
sqlite3 -readonly kgs/reasoning-graph.db "PRAGMA foreign_key_check;"

# Relic test; one stale-path failure is part of the baseline
python3 python/test_agent_pattern_analyzer.py

# Eco-system advertised runner (currently broken; run only when in scope)
cd systems/eco-system
python3 tests/run_tests.py
```

There is no repository-wide build, lint, or reliable full-test command yet. Do not claim repository-wide success from only the focused fixture.

## Graph and database rules

- Treat source files, provenance, tests, and receipts as stronger authority than generated graph output.
- Never infer that a confidence score is a calibrated probability or grants authority.
- Preserve distinct relationship types between the same node pair.
- Do not delete dangling edges or synthesize missing nodes without tracing their source provenance.
- Enable and verify foreign keys for any writer.
- Back up a material database before an approved migration; name the exact database and migration in the backup.
- Use read-only SQLite access for audits and reports.
- Do not write through the out-of-repository NLKE MCP surface. The declared local store for this instance is `kgs/reasoning-graph.db`.
- Recurrence may nominate a new rule, but verification and provenance are required before freezing it.
- Retire contradicted knowledge with evidence; do not silently erase history.

## Code conventions

- Python is the implementation language for the supported surface.
- Keep `query.py` deterministic and offline unless a separately approved design changes that contract.
- Keep schema-specific DB handling inside `systems/nai/kg_manager.py`; commands and retrieval code consume its normalized interface.
- Keep NAI `do_*` methods thin: parse, delegate, render.
- Preserve JSON output compatibility when changing CLI behavior.
- Replace device-specific absolute paths with `Path`-based configuration, CLI flags, fixtures, or environment variables.
- Add regression evidence for every bug fix.
- Prefer focused changes over broad cleanup of relic code.
- Do not update living status documents merely to make implementation status look newer; claims must be backed by observed evidence.

## Legacy and generated content

- `systems/eco-system/` contains an outer tree and a nested duplicate with drift. Never edit both mechanically; establish the canonical target first.
- `python/` is a parts bin. A successful `--help` command does not prove a tool's full behavior.
- `indexes/` contains relic pointers to source paths not fully present here.
- Large logs, embeddings, DB backups, and bytecode are artifacts, not product source.
- A malformed zero-byte filename currently exists at repository root and breaks UTF-8 inventory tooling. Do not remove or rename it without explicit approval.

## Decision boundaries

The user owns product and scope decisions. Surface unresolved choices rather than silently deciding them, especially:

- what becomes the supported v0.1 product;
- whether eco-system is rehabilitated, archived, or split out;
- whether and how the external generalized framework is ported back;
- which missing graph concepts are legitimate versus stale edges;
- any destructive cleanup, database migration, publication, deployment, or external write.

Diagnosis and reporting are read-only except for normal temporary test artifacts. A request to diagnose does not authorize a fix. A request to fix should name or clearly imply the target scope; keep unrelated historical surfaces untouched.

<!-- in-the-loop:codex-team:begin -->
## In the Loop native Codex team

Repository-local `AGENTS.md`, `.codex/config.toml`, skills, permissions, and explicit user instructions remain authoritative.

- Use `sprinter` only when exact targets, a concrete reversible change, and named validation are all provided.
- Use `analyst` for clear, read-heavy extraction or review; use `operator` for integrated implementation and verification.
- Use `architect` for material ambiguity, architecture, security, or repeated failure. Use the requested `planner` (documented `gpt-5.6-sol`, `xhigh`) for an isolated, closed-context plan.
- The core four inherit the session model; built-in `default`, `worker`, and `explorer` remain valid fallbacks.
- Parent retains user questions, approvals, graph control, waiting, and consolidation. Retry a role once only for malformed or transient output, then route or escalate.
- Any resumed session, goal, checkpoint, conversation, or repository-state recovery is read-only until the parent obtains fresh, active-session approval for the exact protected effect and target. A bare `continue` or `resume` is not that approval.

Every delegation includes `objective:`, `context_and_inputs:`, `scope:`, `constraints:`, `authority:`, `deliverable:`, `acceptance_evidence:`, `budget:`, and `escalate_when:`.

Every result includes `status: complete | partial | blocked`, `summary:`, `evidence:`, `artifacts_or_changed_files:`, `verification:`, `risks_or_unknowns:`, and `recommended_next_route:`.

Context does not grant authority. Treat dispatch and model output as claims until independently observed through tests, state, screenshots, receipts, or equivalent evidence.
<!-- in-the-loop:codex-team:end -->
