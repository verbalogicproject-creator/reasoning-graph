# CLAUDE.md

Read [AGENTS.md](AGENTS.md) before changing this repository.

Reasoning Graph is a portable engineering prototype for governed reasoning
memory. The bundled Claude Code tools instance is canonical under
`instances/claude_code_tools/`; it no longer depends on a sibling checkout or
an absolute device path.

Use the repository acceptance commands from `AGENTS.md`. In particular:

- Missing confidence and contradictions must refuse rather than be hidden.
- Memory proposals cannot activate without explicit human approval.
- MCP may propose memory but cannot approve it.
- Thinking blocks and signatures must be replayed exactly when the provider
  requires continuity, but they are not evidence and are not durable MemoryLog
  content.
- Do not expose or request private chain-of-thought.
- Do not call the project scientific proof of metacognition.
- Do not push, publish, deploy, or contact providers without fresh explicit
  approval.
