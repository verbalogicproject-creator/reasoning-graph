# Changelog

All notable changes are documented here (Keep a Changelog format).
## [0.2.0] — Unified prototype

### Added

- Portable, deterministic Instance 0 repair and integrity receipt.
- Append-only, typed MemoryLog with explicit human approval.
- Local graph and memory workbench.
- Offline provider-native extended-thinking contracts and playbooks for OpenAI,
  Gemini, and Anthropic.
- Updated GitHub/arXiv research candidate ledger and claim boundary.

### Changed

- Replaced machine-specific acceptance gates with portable pytest, repair,
  integrity, fixture, CLI, MCP, and workbench checks.
- Removed obsolete local checkout paths and historical generated benchmark
  artifacts from the release tree; they remain in Git history.


## [0.1.0] — PoC (Opus 4.8 build session)

### Added
- Corpus-agnostic core: `GraphSchema` declaration, profile-driven `Store`, `m001` edge-confidence migration, `resolve`/refusal boundary, mechanized loop (`scan`/`promote`/`mint`/`verify`/`freeze`/`retire`), measurement (`frontier_rate` + the A/B harness).
- Instance 0 (`claude-code-tools`): confidence backfilled onto all 856 edges; an A/B evaluation ran (N=30); frontier-call rate was computed from the live log.
- Full test suite (1:1 with `tests/INVARIANTS.md`), deterministic `demo`, self-verifying `examples/`, and the house doc set.
- Gates G0–G6 green (smallest useful slice) + G8 (codification bar).

### First debugging / hardening pass
Real bugs found and fixed during the build (each with a regression test):
- **RG-1** — the corpus-min confidence fallback (0.70) was declared only in prose; made it machine-readable on the instance's `ConfidenceRule.value` so `m001` can derive it (Phase 2).
- **RG-2** — the frontier-call log's §1 schema *template* (inside a code fence) was mis-parsed as a real entry; the FCL parser now skips fenced content (Phase 4; `tests/test_fcl.py`).
- **RG-3** — `freeze` deleted the staged matcher, breaking the twice-run idempotency check; it now copies to `minted/` and keeps `staged/` so a re-freeze reports `already_frozen` (Phase 4; `tests/test_freeze.py`).
- **RG-4** — `retire_pass` wrote to `evolution_log` but only created `rule_status`; standalone retirement crashed when no prior `freeze` had created the table. `retire` now creates `evolution_log` IF NOT EXISTS too (Phase 7; `tests/test_retire.py`).
