# Codebase report

## What this project actually is

Reasoning Graph is a local Python engineering prototype for governed reasoning
memory. A declared schema describes typed nodes, typed relationships, confidence
bases, and endpoint constraints. The engine retrieves inspectable support paths
and returns `ANSWER`, `WEAK_ANSWER`, or `REFUSE` instead of filling an
unsupported gap.

Around that core, the repository now provides:

- a portable repaired Claude Code tools graph;
- append-only observations and a human-approved MemoryLog;
- CLI and MCP agent interfaces;
- a localhost review workbench;
- offline provider contracts for OpenAI, Gemini, and Anthropic;
- historical measurement code and a current research/adoption ledger.

It is not a model, an autonomous learner, a chain-of-thought recorder, or
scientific proof of metacognition.

## Runtime flow

```text
InstanceDescriptor + GraphSchema
  -> SQLite Store + integrity inspection
  -> resolver / primitive adapter
  -> ANSWER | WEAK_ANSWER | REFUSE
  -> optional bounded observation
  -> candidate or typed memory proposal
  -> evidence and conflict review
  -> explicit human approval
  -> active rule/memory or dispute/supersession/retirement
```

Provider-native thinking remains outside graph truth:

```text
provider request -> observable response/tool outcome -> normalized turn record
                 -> transient exact replay payload
                 -> scrubbed persistence (no signatures/encrypted reasoning)
```

## Module map

| Surface | Responsibility |
|---|---|
| `reasoning_graph/schema.py` | Instance descriptor, graph vocabulary, endpoint and confidence contracts |
| `reasoning_graph/store.py` | Read-mostly profile-driven SQLite access and integrity inspection |
| `reasoning_graph/resolver.py` / `refusal.py` | Weighted path composition, contradictions, weak answers, and refusal |
| `reasoning_graph/primitives.py` / `query.py` | Corpus-specific query adapter and portable legacy compatibility interface |
| `reasoning_graph/loop/` | Scan, promote, stage, verify, human freeze, and retire lifecycle |
| `reasoning_graph/observations.py` | Append-only observable task outcomes |
| `reasoning_graph/memory.py` | Typed, append-only MemoryLog and active-only orientation snapshot |
| `reasoning_graph/providers/` | Offline OpenAI, Gemini, and Anthropic request/normalization contracts |
| `reasoning_graph/cli.py` | Scriptable command-line interface |
| `reasoning_graph/mcp_server.py` | Agent tools; memory proposal allowed, approval forbidden |
| `reasoning_graph/workbench/` | Local inspection, observations, candidates, and typed human approvals |
| `scripts/repair_instance_db.py` | Deterministic source-to-clean Instance 0 repair |
| `instances/claude_code_tools/` | Immutable source DB, clean DB, manifest, declarations, and portable descriptor |

## Data and trust boundaries

- The immutable source database is preserved under
  `instances/claude_code_tools/source/`.
- Repair produces a byte-stable clean database with 660 nodes and 853 typed
  relationships.
- Confidence is a declared path-ranking value, not a calibrated probability.
- Graph support is inspectable but is not authority by itself.
- Memory facts require a cited-evidence object with a nonblank source, a
  nonblank validation statement, acknowledgement, and explicit human approval.
  Decisions, preferences, procedures, and hypotheses retain their type.
- Observations and MemoryLog events are append-only runtime ledgers and are
  ignored by Git for the bundled instance.
- Provider signatures and encrypted reasoning exist only in transient replay
  payloads. Reasoning summaries are excluded from persistence by default.

## Practical uses

1. Give a coding agent inspectable, reusable tool/workflow guidance.
2. Carry explicitly agreed project context between sessions.
3. Review why a recommendation is supported, weak, or refused.
4. Collect successes, failures, contradictions, and gaps for later evaluation.
5. Compare provider-native reasoning controls without treating private thinking
   artifacts as evidence.

## Evidence boundary

The test suite establishes repository-scoped engineering properties such as
schema validation, deterministic repair, refusal behavior, append-only
lifecycle rules, provider redaction, and human approval controls. Historical
small-N A/B results are retained as experimental context only; they are not a
generalizable benchmark or proof of metacognition.
