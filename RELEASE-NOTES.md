# Release notes

## 0.2.0 — unified engineering prototype

This release unifies the corpus-independent engine with the repaired,
portable Claude Code tools instance.

### Added

- Deterministic Instance 0 repair with an immutable source database and manifest.
- Governed append-only MemoryLog with typed entries, conflict handling,
  explicit human approval, and an active-only orientation snapshot.
- Offline OpenAI Responses, Gemini Interactions, and Anthropic Messages
  request/normalization contracts.
- A local workbench for graph inspection, observations, and memory review.
- Provider playbooks and a GitHub/arXiv practical-possibilities ledger.

### Safety and claim boundary

- MCP may propose memory but cannot approve or activate it.
- Provider reasoning summaries, signatures, and encrypted replay artifacts are
  not graph evidence and are excluded from durable records by default.
- Confidence remains a declared path-ranking score, not a calibrated
  probability.
- The software demonstrates mechanisms and tests; it is not scientific proof of
  metacognition, consciousness, or access to private chain-of-thought.

Historical gates and benchmark outputs tied to an old machine-specific checkout
remain available in Git history but are not release acceptance criteria. The
portable checks are documented in `AGENTS.md` and `CONTRIBUTING.md`.
