# CONTRIBUTING

Reasoning Graph welcomes focused changes that preserve its evidence and privacy
boundaries. Read `AGENTS.md` before editing.

## Development setup

```sh
python3 -m pip install -e .
python3 scripts/repair_instance_db.py
python3 -m pytest -q
```

Install `.[mcp]` or `.[workbench]` only when working on those optional
surfaces. Provider contract tests are offline and must not require credentials.

## Engineering contracts

- Keep `reasoning_graph/` corpus-independent. Schema vocabulary and corpus
  facts belong in an `InstanceDescriptor` and `instances/<name>/`.
- Preserve parallel relationship types, provenance, and the declared confidence
  basis. Missing confidence and declared contradictions must remain visible and
  may require refusal.
- Treat confidence as a ranking score, not a calibrated probability.
- Keep the bundled source database immutable. The repair script must produce a
  byte-stable clean database and matching manifest.
- Add a regression test for every behavior change.

## Memory and provider safety

- A MemoryLog fact needs evidence, validation, agent acknowledgement, and
  explicit human approval. Other memory kinds need explicit agreement and must
  retain their type.
- Review is read-only. MCP clients may propose memory but may never approve it.
- Correct append-only records by disputing, superseding, or retiring them.
- Never store private chain-of-thought, reasoning summaries, thought signatures,
  encrypted reasoning, credentials, or raw provider replay blocks as graph
  evidence or MemoryLog content.
- Provider adapters should preserve native continuity requirements while
  returning only observable outputs and scrubbed telemetry for persistence.
- Keep provider SDKs optional and avoid hard-coded model IDs.

## Documentation and claims

Describe tested mechanisms precisely. The project is an engineering prototype;
it is not scientific proof of metacognition, consciousness, introspection, or
general reasoning ability. Link primary sources for changing API behavior and
record the research date.

## Before submitting a change

```sh
python3 scripts/repair_instance_db.py
python3 -m pytest -q
python3 -m reasoning_graph.cli schema integrity \
  --instance instances/claude_code_tools/instance.json --json
python3 p2_fixture_runner.py
git diff --check
```

Do not include absolute machine paths, credentials, session receipts, copied
knowledge graphs, generated caches, or local logs. Opening a pull request,
publishing, deploying, or contacting a provider requires the repository owner's
explicit approval.
