# Anthropic Messages API playbook

Official source: [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking).
Verified for this playbook on 2026-08-30.

## Adaptive path

Use `thinking.type=adaptive` on a supporting model. `output_config.effort`
steers work across the response; it is not a confidence value. Adaptive
thinking can interleave between tool calls on supported models. Model support
and defaults vary, so keep the model ID configurable.

## Manual path

Older/specific models may use `thinking.type=enabled` with `budget_tokens`.
Manual mode has additional tool-choice and interleaving restrictions. Follow
the current per-model documentation rather than inferring support from a model
name.

## Tool-loop continuity

When returning a tool result inside a thinking-enabled turn, replay the
complete original assistant content in its original order, including every
`thinking`, `redacted_thinking`, and associated `tool_use` block. The
`signature` is opaque. Visible thinking text is a summary, never raw
chain-of-thought; `display=omitted` can return an empty thinking field while
preserving the signature.

Record final text, tool-use blocks, stop reason, errors, and usage. Evaluate
observable outcomes; never promote a thinking block directly into active
memory.
