# Pre-push release receipt — 2026-08-30

Status: **LOCAL RELEASE READY — NOT PUSHED**

- Intended remote: `https://github.com/verbalogicproject-creator/reasoning-graph`
- Intended branch: `main`
- Integration merge commit: `fd2c0c2054d48f1b590ab8b5714bb47adfc6abd8`
- Merge parents: engine `f57b0420eea39f9542b4a23276880865c9dd7507`;
  curated lab source `242ed59ef706efa209d87bf532b8afd56e948201`
- Package version: `0.2.0`
- Remote configured: no
- Push performed: no

## Qualified scope

This candidate unifies the reasoning-graph engine and curated experimental
sources as a governed metacognitive-memory prototype. It includes portable
Instance 0 repair, an append-only typed MemoryLog, local workbench and MCP
surfaces, provider-native extended-thinking continuity contracts, updated
owner documentation, and the research/practical-possibilities draft.

The claim is deliberately bounded: this is a working engineering prototype
with tested invariants. It is not scientific proof of metacognition, access to
private chain-of-thought, or a generalizable benchmark.

## Verification evidence

- Full Python suite: `92 passed`; one non-blocking external
  Starlette/httpx deprecation warning.
- Deterministic repair: two consecutive runs produced identical database and
  manifest hashes.
- Clean database SHA-256:
  `6859163b8259a47cc693d61aea1ec4ea1635a1a3c3968ece11ad2b0c53f1b8b0`.
- Clean manifest SHA-256:
  `8d7da659e52f16f49bb9740e04059b4d88ff929233261ace130fc6f6872aed66`.
- Immutable source SHA-256:
  `08f651490c6c9e0be7523d8e8054624c1277cadcacaf91b8771d8b93f94d3edb`.
- Instance integrity: `ok: true`, 660 nodes, 853 edges, no missing
  endpoints, invalid endpoint kinds, duplicate typed relationships, missing
  confidence, unknown kinds, or foreign-key violations.
- P2 acceptance: `20/20`; canonical queries `3/3`.
- Workbench JavaScript syntax, Python compilation, focused Ruff checks, and
  staged-diff whitespace checks passed.
- Isolated editable installation reported version `0.2.0` and clean instance
  integrity.
- All three provider examples produced valid offline request dictionaries when
  run against this checkout.

## Independent review

A read-only release reviewer reproduced and closed all reported blockers:

- cross-origin, simple-content, and missing-token workbench mutations fail
  closed; a valid same-origin token-bearing request succeeds;
- MemoryLog conflicts are symmetric and cannot both activate concurrently;
- duplicate memory and event identities fail atomically without corrupting the
  append-only ledger;
- OpenAI stateless requests explicitly request encrypted reasoning content,
  preserve complete transient replay, and scrub it from persistence;
- Anthropic thinking-only and tool-only replay fail, while complete
  thinking-plus-tool-use replay is ordered before the tool result;
- fact promotion requires a cited-evidence object with a nonblank source,
  nonblank validation, acknowledgement, and explicit approval;
- repair source/output/manifest paths are pairwise distinct and collision
  failures preserve existing bytes;
- MCP exposes proposal and review, but no approval or activation tool.

Final reviewer verdict: **locally release-ready; no release blocker found**.

## Security, privacy, and portability

- No tracked credentials, private keys, `.env`, cache, or session `.vouch`
  artifacts were found.
- No active tracked source or documentation contains machine-specific
  `/root`, Android-storage, or user-home paths.
- Provider reasoning signatures and encrypted material are transient
  continuity artifacts, excluded from default persistence.
- The workbench is loopback-only. Typed confirmation is a protected local
  operator action, not authenticated human identity.
- Provider contracts were verified offline only; configured model/account
  compatibility remains the operator's responsibility.
- Database and manifest publication are individually atomic, but cannot be one
  cross-file filesystem transaction.

## Release-tree cleanup

Obsolete machine-specific gates, generated historical benchmark dumps, stale
inventory/status reports, session receipts, and the incomplete vendoring
manifest were removed from the release tree. They remain recoverable from Git
history; the curated lab root is also preserved by the local `lab-source`
branch.

## Push checkpoint

This receipt does not authorize or perform a push. The exact final `main`
commit must be reported to the owner, and the owner must explicitly approve
pushing that commit to the intended GitHub repository.
