# Security and privacy

Reasoning Graph is an experimental local engineering prototype. Do not expose
its workbench, MCP server, or data files to untrusted networks without adding
authentication, authorization, transport security, and deployment hardening.

The workbench binds to loopback and protects every POST with strict JSON,
loopback Host validation, same-origin validation, and a per-process CSRF token.
Typed confirmation is an additional local operator gate, not authenticated
identity. The token is transient and must not be persisted or logged. These
controls do not make the workbench suitable for network exposure.

Run it through its bundled localhost entry point; do not place it behind a
proxy or change the bind address without a separate threat model.

## Provider credentials and reasoning artifacts

- Provider examples and tests make no network calls and need no credentials.
- Supply API keys only through the provider SDK's supported environment or
  secret manager. Never commit keys, bearer tokens, request dumps, or `.env`
  files.
- Encrypted reasoning items and signed thought/thinking blocks are transient
  continuity material. Do not persist them to MemoryLog, observations, graph
  evidence, telemetry, exceptions, fixtures, or debug logs.
- Reasoning summaries can contain sensitive prompt context. Persistence is off
  by default in `ProviderTurnRecord.to_persistable_dict()`.
- Redact user content and tool results before sharing diagnostic receipts.

## Local memory data

MemoryLog and observation ledgers may contain private project or user context.
Bundled runtime ledger paths are ignored by Git, but operators remain
responsible for filesystem permissions, backups, retention, and deletion.
Review entries before exporting a snapshot or diagnostic receipt.

## Reporting

Report suspected vulnerabilities privately to the repository owner. Include a
minimal reproduction, affected version/commit, impact, and whether credentials
or private data may have been exposed. Do not include live secrets in a report.
