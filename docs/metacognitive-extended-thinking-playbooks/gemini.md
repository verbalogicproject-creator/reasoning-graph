# Gemini Interactions API playbook

Official source: [Gemini thinking](https://ai.google.dev/gemini-api/docs/thinking).
Verified for this playbook on 2026-08-30.

## Stateful path

Use `store=true` with `previous_interaction_id`. The service retains thought
steps and signatures. Configure `generation_config.thinking_level` only to a
level supported by the selected model. `thinking_summaries=auto` requests
summaries but code must accept a thought step with no summary.

## Stateless path

Replay every `thought` step exactly as returned. Also preserve signatures on
built-in tool call/result steps. Do not edit, partially extract, or reorder
these steps. A signature is an encrypted reasoning-state continuity mechanism,
not evidence that the summary or answer is true.

## Normalize and evaluate

Record final model output, standard function calls, interaction status/errors,
and `total_input_tokens`, `total_output_tokens`, `total_thought_tokens`, and
`total_tokens`. Use final-answer and tool-result tests for evaluation; do not
turn thought-token count into a confidence or task-complexity score.
