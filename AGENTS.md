# AGENTS.md

## Repository purpose

Reasoning Graph is an Apache-2.0 engineering prototype for governed, typed,
confidence-weighted reasoning memory. It retrieves inspectable support paths,
records bounded observations, and requires evidence plus human approval before
candidate memory or rules become active.

Do not describe it as scientific proof of metacognition, a general reasoning
engine, an autonomous learner, or a system that exposes private chain-of-thought.

## Supported surfaces

- `reasoning_graph/`: corpus-independent Python engine, CLI, MCP server, and workbench.
- `instances/claude_code_tools/`: bundled, portable Instance 0 and immutable source DB.
- `scripts/repair_instance_db.py`: deterministic Instance 0 repair.
- `synthesis-rules/`: curated rule sources; historical bulk archives are excluded.
- `docs/metacognitive-extended-thinking-playbooks/`: provider-specific contracts.
- `tests/`: repository acceptance evidence.

## Required checks

Run commands from the repository root:

```sh
python3 scripts/repair_instance_db.py
python3 -m pytest -q
python3 -m reasoning_graph.cli schema integrity \
  --instance instances/claude_code_tools/instance.json --json
python3 p2_fixture_runner.py
```

Optional MCP, workbench, and provider dependencies must remain extras. Offline
tests are authoritative; live provider tests must be explicit, credentialed,
and skipped by default.

## Memory and evidence rules

- Facts require cited evidence, validation, agent acknowledgement, and explicit
  human approval before activation.
- Decisions, preferences, procedures, and hypotheses must keep their type and
  must never be relabeled as verified facts.
- The phrase “update my memorylog” opens review; it never silently writes.
- MCP may read and propose memory but must never approve or activate it.
- Preserve append-only history. Supersede, dispute, or retire; do not rewrite.
- Provider reasoning summaries, encrypted reasoning, thought signatures, token
  counts, and confidence-like fields are continuity/telemetry artifacts, not
  evidence and not durable memory.
- Confidence is a declared ranking score, not a calibrated probability or grant
  of authority.
- Missing support and contradictions are refusal-grade outcomes.

## Repository hygiene

- No absolute device paths, credentials, session-local receipts, copied KGs,
  generated embeddings, logs, database backups, or legacy checkout bodies.
- Keep the immutable source DB; derived DBs must be deterministic and checked by
  manifests/tests.
- Preserve parallel relationship types and provenance.
- Add regression tests for behavior changes.
- Do not make provider SDKs required runtime dependencies.
- Do not commit, push, publish, deploy, create a PR, or contact an external
  service without fresh explicit user approval for that exact effect.

<!-- in-the-loop:codex-team:begin -->
## In the Loop native Codex team

- Use sprinter only for exact reversible micro-edits with named validation.
- Use analyst for read-heavy extraction, operator for integrated implementation,
  and architect for material ambiguity, safety, or repeated failure.
- Parent retains approvals, graph control, waiting, and consolidation.
- Every delegation states objective, context, scope, constraints, authority,
  deliverable, evidence, numeric budget, and escalation conditions.
- Treat model reports as claims until independently verified.
<!-- in-the-loop:codex-team:end -->
