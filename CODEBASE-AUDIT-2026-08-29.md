# Reasoning Graph codebase audit

**Audit date:** 2026-08-29  
**Scope:** `/root/reasoning-graph` only  
**Method:** source and documentation review, SQLite integrity queries, CLI smoke tests, focused acceptance tests, inherited subsystem tests, and the existing 100-query retrieval benchmark.

## Executive finding

This repository is best understood as a **research lab and instance dataset for a reasoning-graph idea**, not as one finished application.

The central idea is sound and unusually concrete: represent reusable reasoning as typed, confidence-weighted graph edges, answer by traversing those edges, and log unsupported questions so recurring gaps can later be verified and frozen. In plain language, it tries to replace repeated AI re-reasoning with inspectable lookup paths.

A small, useful part of that idea works today:

- `kgs/reasoning-graph.db` contains a real combined graph of Claude Code tools, limitations, use cases, workflow relations, synthesis rules, and handbook-derived capabilities.
- `query.py` provides a practical natural-language-like CLI over that graph.
- `systems/nai` provides generic hybrid search and graph analytics over several SQLite KG schemas.
- The focused 20-query acceptance fixture passes 20/20, including all three canonical examples.

However, the repository as a whole is not production-ready. It has no package manifest, install instructions that reflect the current environment, repository-wide test command, CI, or Git metadata. It also contains a large inherited `eco-system`, relic scripts, copied databases, historical reports, stale device paths, duplicated trees, and a 596 MB log. The inherited ecosystem's advertised full test runner does not work; when its tests are invoked directly, 3 fail and 35 error out of 220.

The honest product statement is therefore:

> **A working proof-of-concept query and traversal layer over a domain-specific reasoning graph, surrounded by a much larger experimental archive.**

It is not yet a general reasoning engine, a self-updating autonomous learner, or a deployable end-user application.

## What is actually here

### 1. The focused reasoning-graph instance

`kgs/reasoning-graph.db` is the current usable center of the repository.

Observed database contents:

| Item | Count |
|---|---:|
| Nodes | 639 |
| Edge rows | 856 |
| Tools | 14 |
| Synthesis rules | 33 |
| Handbook capability nodes | 17 |
| Tool use cases | 144 |
| Tool limitations | 121 |
| Tool combinations | 90 |
| Historical synthesis facts | 67 |
| Historical fact validations | 214 |
| Historical insights | 444 |
| Evolution-log records | 7 |

All 856 edge rows now have a numeric confidence from 0.70 to 1.0. The database passes SQLite's basic `PRAGMA integrity_check`.

This graph currently describes a narrow domain: **Claude Code tools and agent/tool-design rules**. It knows about tools such as Read, Edit, Grep, Bash, WebFetch, Task, and TodoWrite; their use cases and limitations; documented compositions; and a selected set of synthesis/agent-design rules.

### 2. The focused query interface

`query.py` is a standalone Python CLI and library. It supports 17 operations:

- Core: `want_to`, `can_it`, `compose_for`, `trace`, `why_not`, `similar_to`, and `alternatives`.
- Extensions: optimization, learning paths, recommendations, compatibility, debugging help, exploration, and roadmaps.

It uses deterministic keyword mapping, SQL lookups, graph traversal, Jaccard-like structural similarity, and hand-authored workflow patterns. It does not call a language model and does not require network access.

Live examples confirmed during this audit:

```sh
python3 query.py --compose-for "fix a bug found via search" --json
```

returns the compatible workflow:

```text
Grep -> Read -> Edit
```

```sh
python3 query.py --can-it "access the internet" --json
```

returns `can: true` with WebFetch and WebSearch.

```sh
python3 query.py \
  --trace dep_003_tool_execution_requires_error_handling \
          constr_002_max_iterations_safety \
  --json
```

returns a two-edge rule path through the infinite-tool-loop rule.

### 3. NAI: the reusable graph workbench

`systems/nai` is a separate but working graph-native CLI/REPL. It auto-detects several SQLite KG schemas and offers:

- BM25/text retrieval combined with graph and intent scores;
- shortest and highest-confidence paths;
- PageRank;
- degree-role classification;
- cycle discovery;
- interactive graph navigation.

Live search, path, PageRank, roles, and cycle commands all ran successfully against `kgs/reasoning-graph.db`.

NAI is closer to a reusable engineering component than most of the repository, but it still has no package manifest or its own automated test suite.

### 4. Raw material and relic tools

- `claude-code-tools/` contains structured source records for tool definitions.
- `synthesis-rules/` contains authored rules and larger handbook/insight documents.
- `python/` contains 18 older standalone code-analysis, generation, retrieval, and agent utilities. Every non-test script successfully opened its `--help` CLI during this audit, and the directory compiled successfully.
- These scripts are best treated as a parts bin. They are not integrated into one product and many solve unrelated code-generation or analysis tasks.

### 5. The inherited eco-system

`systems/eco-system` is a much larger earlier Natural Language Knowledge Engineering experiment. It includes hybrid retrieval, corpus ingestion, playbook generation, local-model adapters, visualization, Termux features, copied databases, embeddings, and a duplicated nested source tree.

This subsystem has substantial code and useful design donors, but it should not be presented as healthy production code in its current checkout. Its documentation describes multiple generations at once, several defaults still point at old Android storage locations, its outer and nested copies have drifted, and its schema-v2 code is not correctly migrated in fresh test databases.

### 6. A second framework is referenced but not contained here

The July status documents say a generalized framework was later built at `/root/projects/reasoning_graph/`, with its own gates and tests. That is a different filesystem project and was outside this audit's workspace scope. Claims about that framework are documented here, but its source and current gate status should not be confused with what this repository itself proves.

## What it can be used for now

### Practical use 1: a Claude Code tool/workflow advisor

Given a task such as “refactor Python files,” “search for a bug,” or “access the internet,” the focused CLI can recommend tools, construct a small workflow, explain limitations, and show documented compatibility.

This is the most immediately useful application because the graph's data is actually about those tools.

### Practical use 2: inspectable agent-design guidance

The graph can retrieve and traverse rules about caching, error handling, iteration limits, tool descriptions, documentation synchronization, and agent architecture. Unlike a prose-only answer, it can show the nodes and edges used.

This could support an agent prompt builder, a code-review checklist, or a design-review assistant, provided the UI clearly distinguishes authored rules from empirical facts.

### Practical use 3: a local KG exploration tool

NAI can serve as a local workbench for SQLite-backed knowledge graphs: search a graph, inspect central nodes, find paths, classify graph roles, and discover cycles. It is useful for dataset exploration even without adopting the full reasoning-graph thesis.

### Practical use 4: a research harness for “reasoning as retrieval”

The repository contains the raw corpus, a focused graph, acceptance fixtures, frontier-call logs, historical measurements, and multiple retrieval variants. It is suitable for experiments comparing:

- live model reasoning versus graph-backed lookup;
- keyword/BM25 retrieval versus graph-aware retrieval;
- path-confidence policies;
- how recurring query misses should become reviewed rules.

### What it should not be used for yet

- General factual question answering outside the tool/agent-rule corpus.
- Automated decisions where a confidence score is treated as a calibrated probability.
- Unattended graph mutation or autonomous rule freezing.
- A public or multi-user production service.
- A claim that the entire 819 MB workspace is one coherent, tested application.

## Verification results

| Check | Result | Meaning |
|---|---|---|
| Focused P2 fixture | **20/20 pass; 3/3 canonical pass** | The narrow query contract works on the current DB. |
| Focused live queries | **Pass** | Composition, capability, and rule traversal return sensible results. |
| NAI live commands | **Pass** | Search, path, PageRank, roles, and cycles execute on the current DB. |
| Core Python compile | **Pass** | `query.py`, fixture runner, `python/`, and `systems/nai` compile. |
| Relic CLI discovery | **18/18 pass** | Each non-test `python/*.py` script responds to `--help`; this does not prove deeper behavior. |
| Agent-pattern test | **6 pass, 1 fail** | Integration test contains a stale absolute Android path. |
| SQLite basic integrity | **Pass** | Database pages are structurally readable. |
| SQLite foreign-key check | **44 violations** | 44 edge rows point to 21 target IDs absent from `nodes`. |
| NAI 100-query benchmark | **Runs** | Best result: Recall@1 42%, Recall@5 73%, Recall@10 78%, MRR 0.540. |
| Benchmark weak areas | **Failing coverage** | Cross-domain Recall@10 is 0%; debugging Recall@10 is 0%. |
| Eco-system quick runner | **9 tests pass, with 2 advertised classes skipped by import warnings** | Quick result is not a full health signal. |
| Eco-system advertised full runner | **Crashes before suite completion** | Root and `tests/` both contain `test_ecosystem.py`, causing an import collision. |
| Eco-system tests invoked explicitly | **220 run: 3 failures, 35 errors** | Current code, schema initialization, tests, and defaults have drifted. |
| Project Atlas inventory | **Blocked** | A malformed non-UTF-8 filename at repository root breaks deterministic inventory encoding. |

The 100-query benchmark was run from a temporary copy so the checked-in report was not overwritten.

## Important problems

### P0: the product boundary is unclear

The root mixes the focused proof of concept, historical plans, raw source material, live databases, backups, an inherited ecosystem, generated embeddings, logs, and copied predecessor code. A new contributor cannot tell which surface is supported.

There is also no Git repository at this path, no `pyproject.toml` or `requirements.txt`, no CI, and no single authoritative README/command set.

### P0: graph referential integrity is broken

SQLite's page-level integrity passes, but its relationship integrity does not: 44 edge rows target 21 IDs that have no node. Examples include `bug_fixing`, `codebase_exploration`, `implementation_planning`, `task_management`, and `testing`.

These may be intended workflow/capability concepts that were never materialized as nodes. They should be recovered from source provenance or explicitly retired; they should not be silently deleted.

### P0: NAI loses multi-edge detail in its graph projection

The database has 856 edge rows, while NAI reports 798 graph edges and 660 projected nodes. The extra projected nodes are the 21 missing targets; the reduced edge count comes from multiple relationships between the same node pair being collapsed by a simple directed graph.

Multiple edge types between a pair can be meaningful—for example, two tools may be both alternatives and complements in different contexts. The projection should use a multi-edge graph or retain all edge records on the projected pair.

### P1: the focused query semantics are heuristic

The 20/20 fixture is real but narrow and frozen against this exact dataset. `query.py` relies heavily on substring keyword tables and authored compound patterns. It can be useful and deterministic, but it is not broad natural-language understanding. New phrasing and new domains need adversarial evaluation.

### P1: NAI's displayed type information is incomplete

NAI returned `type: "unknown"` for reasoning-graph nodes even though the database stores `node_type`. Its schema profile should map and expose that column so users can distinguish tools, rules, limitations, and capabilities.

### P1: the eco-system has code/schema/test drift

The most repeated error is `sqlite3.OperationalError: table nodes has no column named project_id`. Current code inserts schema-v2 fields, while fresh test databases are created from an older node-table definition or are not migrated. A test also still expects schema version 1 while code reports 2.

Other failures come from stale Android paths and fixtures that expect external databases. The advertised test runner also imports the wrong `test_ecosystem` module.

### P1: stale absolute paths remain widespread

Forty-two Python files contain `/storage/emulated` or `/sdcard` paths. Thirty-seven are in the outer eco-system alone. The focused agent-pattern integration test also hardcodes an old Android working directory.

### P2: repository hygiene blocks deterministic tooling

The root contains a zero-byte filename with invalid UTF-8 bytes. It causes the Project Atlas inventory builder to fail during UTF-8 encoding. The workspace is also 819 MB, of which about 596 MB is one lazy-embedding log.

## How to fix it

The safest strategy is **stabilize the narrow product, then decide what to salvage from the archive**.

### Phase 1 — declare the supported core

Treat these as the first supported surface:

```text
query.py
p2_fixture_runner.py
p2-acceptance-fixture.json
kgs/reasoning-graph.db
systems/nai/
claude-code-tools/
synthesis-rules/
```

Everything else should initially be labeled `legacy`, `research`, `generated`, or `historical`. Do not delete it during stabilization.

Deliverables:

1. Add one root README with the honest product statement and five-minute quickstart.
2. Add `pyproject.toml` with console commands such as `reasoning-graph` and `nai`.
3. Pin the real runtime/test dependencies.
4. Initialize Git, add a focused `.gitignore`, and keep databases/backups under an explicit data policy.
5. Put the focused acceptance fixture and DB integrity checks under one test command.

### Phase 2 — repair the graph contract

1. Produce a provenance report for the 21 missing target IDs.
2. Materialize legitimate concept/workflow nodes from their original sources; tombstone or remove only edges proven invalid.
3. Enable foreign-key enforcement for every writer and add `PRAGMA foreign_key_check` to CI.
4. Add a uniqueness rule for exact `(source, target, edge_type)` duplicates while preserving distinct edge types between the same pair.
5. Change NAI's projection to a `MultiDiGraph` or an equivalent edge-list-preserving representation.
6. Report both `database_edge_rows` and `projected_relationships` so counts cannot be confused.
7. Expose `node_type` in the reasoning-graph schema profile.

Exit criterion: zero dangling edges, no unintended duplicate triples, and lossless round-trip counts through NAI.

### Phase 3 — turn the focused proof into a reliable product

1. Convert the 20-query fixture into normal unit/integration tests with explicit exit codes.
2. Add paraphrase, negative, ambiguous, and out-of-domain cases.
3. Test refusal behavior, not just successful retrieval.
4. Separate exact documented relations from heuristic recommendations in the output schema.
5. Add provenance to every answer: node IDs, edge IDs/types, source file, confidence basis, and proof limit.
6. Make the CLI return nonzero on malformed DBs or failed acceptance checks.

Exit criterion: one clean install command, one test command, and a CLI whose output states whether a result is documented, inferred, weak, or unsupported.

### Phase 4 — quarantine and rehabilitate the eco-system separately

Do not let eco-system failures block the focused product.

1. Mark `systems/eco-system` as legacy/experimental or move it to a separate archive repository while preserving history.
2. Remove the outer/nested duplicate ambiguity by choosing one canonical tree.
3. Implement a real v1-to-v2 SQLite migration that adds `project_id`, updates the schema version, and is tested against both fresh and existing databases.
4. Rename the root `test_ecosystem.py` or change discovery to package-qualified imports so the full runner works.
5. Replace every device-specific path with `EcoConfig`, CLI flags, fixtures, or environment variables.
6. Split tests into hermetic unit tests and explicitly opted-in integration tests requiring external models/databases.
7. Decide which components are real versus simulated and label their output accordingly.

Exit criterion: the advertised full test command discovers the intended suite and passes without external personal paths.

### Phase 5 — reconnect the learning loop only after the read side is trustworthy

The documents describe a stronger mint/verify/freeze/retire framework in another project. If that loop is to become part of this repository, port it deliberately after Phases 1–3 rather than rebuilding it from historical notes.

Required safeguards:

- graph misses are logged, not automatically treated as truth;
- recurrence only nominates a rule;
- verification and provenance are mandatory before freezing;
- confidence is a ranking/basis, not authority or probability;
- contradicted rules are demoted with evidence, not silently erased.

## Recommended immediate next build

A bounded first repair should cover only:

1. package/README/test entry point for the focused core;
2. a read-only database audit command;
3. repair of the 21 missing targets and exact duplicate triples;
4. lossless multi-edge projection plus correct node types in NAI;
5. regression tests for all of the above.

That would turn the strongest existing slice into a credible v0.1 without getting trapped in the 743 MB inherited subsystem.

## Useful commands today

```sh
# Focused acceptance suite
python3 p2_fixture_runner.py

# Recommend a tool workflow
python3 query.py --compose-for "fix a bug found via search"

# Ask a capability question
python3 query.py --can-it "access the internet"

# List the 14 current tools
python3 query.py --list

# Generic NAI query (run from systems/)
cd systems
python3 -m nai --db ../kgs/reasoning-graph.db --query "search caching" --json

# Multi-hop path through rules
python3 -m nai --db ../kgs/reasoning-graph.db \
  --query "path dep_003_tool_execution_requires_error_handling constr_002_max_iterations_safety" \
  --json

# SQLite checks
sqlite3 -readonly kgs/reasoning-graph.db "PRAGMA integrity_check;"
sqlite3 -readonly kgs/reasoning-graph.db "PRAGMA foreign_key_check;"
```

## Bottom line

The valuable invention is not the large archive. It is the compact loop implied by the focused slice:

```text
documented tools/rules -> typed graph -> deterministic query/traversal
                                        -> honest miss -> reviewed new rule
```

The left half works today for one useful domain. The right half is documented and reportedly implemented in a separate framework, but it is not a clean, supported feature of this repository. The next move should be to make the working left half installable, lossless, and trustworthy before expanding scope.
