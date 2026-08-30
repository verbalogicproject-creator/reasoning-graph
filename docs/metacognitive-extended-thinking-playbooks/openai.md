# OpenAI Responses API playbook

Official sources: [Reasoning models](https://developers.openai.com/api/docs/guides/reasoning),
[Create a response](https://developers.openai.com/api/reference/resources/responses/methods/create),
and [current model guidance](https://developers.openai.com/api/docs/guides/latest-model).
Verified for this playbook on 2026-08-30.

## Stateful path

Use one server-managed mechanism: `conversation` or `previous_response_id`.
They are mutually exclusive. `reasoning.effort` controls reasoning effort;
`reasoning.summary` requests a provider-generated summary; and
`reasoning.context` controls prior reasoning relevance where the selected model
supports it.

## Stateless/ZDR path

Set `store=false` and replay complete response output items exactly with the
next input. Explicitly request `reasoning.encrypted_content` through
`include` so reasoning items carry the opaque material needed for the next
stateless turn. Treat it as transient continuity data. Never put it into
MemoryLog, logs, graph provenance, or an evidence packet.

## Normalize and evaluate

Record the response ID/status, final output text, tool calls, errors,
incomplete reason, total usage, and reasoning-token usage. A reasoning summary
may help debug prompt or tool behavior, but does not validate its own claims.
Evaluate the final answer and tool outcome against task-specific tests.
