# Reasoning Graph

Reasoning Graph is a local-first engineering prototype for **governed reasoning
memory**. It stores typed, confidence-weighted relationships, retrieves
inspectable support paths, records what happened, and refuses unsupported or
contradictory claims.

It also contains a governed MemoryLog and provider-specific extended-thinking
contracts for OpenAI, Gemini, and Anthropic. It does not expose private
chain-of-thought and it is not scientific proof that a model is metacognitive.

![required dependencies](https://img.shields.io/badge/required_dependencies-0-blue)
![license](https://img.shields.io/badge/license-Apache--2.0-green)
![status](https://img.shields.io/badge/status-engineering_prototype-orange)

## What it does

```text
question
  → resolve against declared graph evidence
  → ANSWER / WEAK_ANSWER / REFUSE
  → append an observable outcome
  → propose a typed memory or reusable rule
  → evidence and conflict review
  → explicit human approval
  → active memory + compact next-session snapshot
```

Today the repository provides:

- A corpus-independent Python engine, CLI, MCP server, and local FastAPI
  workbench.
- Typed graph traversal with provenance and a confidence basis on every edge.
- First-class weak answers and refusals instead of silently filling gaps.
- An append-only observation ledger and human-gated rule lifecycle.
- A typed MemoryLog for facts, decisions, preferences, procedures, and
  hypotheses.
- Executable, offline provider contracts for current extended-thinking APIs.
- A bundled Claude Code tools instance with a deterministic repair receipt.

This is narrower than GraphRAG and more governed than a prompt history. The
prototype remembers approved external artifacts and evidence—not hidden model
reasoning.

## Quickstart

Python 3.10 or newer is required.

```sh
python3 -m pip install -e .
python3 scripts/repair_instance_db.py
python3 -m pytest -q

python3 -m reasoning_graph.cli schema integrity \
  --instance instances/claude_code_tools/instance.json --json

python3 -m reasoning_graph.demo
```

The bundled repair preserves the immutable source database and deterministically
produces the active clean database. The current verified instance contains 660
nodes and 853 typed relationships with no missing endpoints, endpoint-kind
violations, duplicate typed relationships, or SQLite foreign-key violations.

Optional integrations:

```sh
python3 -m pip install -e '.[mcp]'
python3 -m pip install -e '.[workbench]'

reasoning-graph-mcp \
  --instance instances/claude_code_tools/instance.json

reasoning-graph-workbench \
  --instance instances/claude_code_tools/instance.json
```

The workbench binds to localhost by default. It is a development surface, not a
hardened public service.

## Governed MemoryLog

The MemoryLog design grew from Eyal Nof's original manual method: maintain a
user-owned text record, explicitly supply it at the beginning of a session, and
admit only information the user and AI have agreed is correctly stated. The
original account is preserved in the [OpenAI Community post](https://community.openai.com/t/how-i-simulated-memory-in-free-chatgpt-using-logic-alone-manual-memory-log-method/1286932).

The software version makes the agreement boundary explicit:

- `fact`: requires a cited-evidence object with a nonblank `source`, a
  nonblank validation statement, agent acknowledgement of the exact wording,
  and explicit user approval.
- `decision`, `preference`, `procedure`, and `hypothesis`: require explicit
  agreement and retain their type; they are never presented as verified facts.
- Conflicts block activation.
- Corrections dispute, supersede, or retire entries instead of rewriting history.
- “Update my memorylog” means open the review queue. It never means silent write.
- Session startup uses a compact active snapshot; full evidence remains
  retrievable on demand.

CLI example:

```sh
INSTANCE=instances/claude_code_tools/instance.json

python3 -m reasoning_graph.cli memory propose \
  --instance "$INSTANCE" \
  --kind decision \
  --content "Keep provider calls opt-in." \
  --agreement "User and agent agree." \
  --memory-id provider-calls \
  --json

python3 -m reasoning_graph.cli memory review \
  --instance "$INSTANCE" --json

python3 -m reasoning_graph.cli memory approve \
  --instance "$INSTANCE" \
  --memory-id provider-calls \
  --approve --json

python3 -m reasoning_graph.cli memory snapshot \
  --instance "$INSTANCE" --json
```

MCP clients may read and propose MemoryLog entries. Approval and activation are
deliberately unavailable over MCP.

## Extended-thinking playbooks

The provider adapters build request dictionaries and normalize recorded
responses without importing an SDK or making a network call:

- [OpenAI Responses API](docs/metacognitive-extended-thinking-playbooks/openai.md)
- [Gemini Interactions API](docs/metacognitive-extended-thinking-playbooks/gemini.md)
- [Anthropic Messages API](docs/metacognitive-extended-thinking-playbooks/anthropic.md)
- [Shared contract and selection guide](docs/metacognitive-extended-thinking-playbooks/README.md)

Each provider remains native:

| Provider | Native control and continuity |
|---|---|
| OpenAI | Reasoning effort/context, summaries, conversation or previous-response state, encrypted stateless replay |
| Gemini | Thinking levels/summaries, first-class thought steps, previous-interaction state, exact signature replay |
| Anthropic | Adaptive/manual thinking, effort or token budget, signed block preservation, interleaved tool thinking |

Signed or encrypted reasoning artifacts are preserved only for immediate
provider-native continuity. `ProviderTurnRecord.to_persistable_dict()` excludes
them and excludes reasoning summaries by default. Signatures are
provider-consumed continuity artifacts; this client does not independently
verify them, and they are not truth, confidence, or evidence.

The examples in `examples/provider_*.py` print request shapes only. Model IDs
are supplied by the operator because provider availability changes.

## Architecture

```text
GraphSchema
  ├── declared node/edge kinds and confidence bases
  ├── SQLite store + integrity inspection
  ├── resolver → ANSWER / WEAK_ANSWER / REFUSE
  ├── observation ledger
  ├── scan → promote → mint → verify → human freeze → retire
  ├── governed MemoryLog → review → approve → orientation snapshot
  ├── MCP and local workbench
  └── provider request/normalization contracts
```

Confidence is a declared path-ranking score, not a calibrated probability.
Cycles are not automatically contradictions; only declared contradiction edges
trigger contradiction refusal. Missing confidence is refusal-grade.

## Practical uses

- Give a coding agent a local, inspectable source of reusable tool/workflow
  guidance.
- Carry agreed project context between sessions without relying on a provider's
  private memory implementation.
- Compare provider reasoning controls while collecting only observable outputs,
  tool actions, usage, and outcomes.
- Review why a graph-supported recommendation was made and where its support
  stops.
- Build evaluation datasets from successes, failures, contradictions, and gaps
  before considering automated curation.

## Evidence and claim boundary

This repository demonstrates tested software mechanisms: deterministic repair,
typed traversal, refusal, append-only observations, approval-gated activation,
portable provider contracts, and a local review interface.

It does **not** demonstrate consciousness, introspection, human-like cognition,
general reasoning ability, truth of model-generated summaries, or a scientific
theory of metacognition. Here “metacognitive” names an operational external
loop—observe, evaluate, control, remember—not an assertion about a model's inner
experience.

See [the GitHub/arXiv practical-possibilities ledger](upgrde-draft-git-arxiv-practical-possibilities.md)
for candidate research, connections, risks, smallest experiments, and adoption
verdicts.

## Repository map

- `reasoning_graph/` — reusable engine and integrations.
- `instances/claude_code_tools/` — canonical portable Instance 0.
- `synthesis-rules/` — curated source rules.
- `docs/` — mental model, API/CLI/MCP/workbench, and provider playbooks.
- `tests/` — executable acceptance evidence.

Security and privacy boundaries are documented in [SECURITY.md](SECURITY.md).
Contributions should follow [CONTRIBUTING.md](CONTRIBUTING.md).
