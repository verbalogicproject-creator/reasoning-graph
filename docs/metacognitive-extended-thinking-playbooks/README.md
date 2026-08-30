# Metacognitive extended-thinking playbooks

These playbooks connect provider-native extended-thinking APIs to Reasoning
Graph's observable control loop. They do not expose private chain-of-thought,
make reasoning summaries factual evidence, or prove that a model is
metacognitive.

The engineering loop is narrower and testable:

```text
request → provider response/tool outcome → normalized observable record
        → optional memory proposal → evidence/conflict review → human approval
```

## Shared contract

- `ProviderProfile` describes API-family capabilities; support still depends on
  the configured model and account.
- Request builders return ordinary dictionaries and never import an SDK or call
  a network.
- Normalizers retain final text, tool calls, token usage, errors, and stop state.
- `continuity_payload()` returns a defensive copy of complete provider-native
  replay items or steps for immediate continuation.
- `to_persistable_dict()` excludes opaque signed/encrypted material and, by
  default, reasoning summaries.
- Signatures are opaque, provider-consumed continuity artifacts; this client
  does not independently verify them, and they do not make a statement true.
- Reasoning summaries are generated interpretations, not raw chain-of-thought,
  confidence measurements, or evidence for activating memory.

The examples under `examples/provider_*.py` only print request dictionaries.
Live calls are deliberately outside the default test suite and require the
operator to select a current model, provide credentials through the provider's
normal environment mechanism, and approve cost/network use.

## Selection guide

| Need | Playbook |
|---|---|
| Responses API conversation state or encrypted stateless replay | [OpenAI](openai.md) |
| First-class thought steps and stateful Interactions | [Gemini](gemini.md) |
| Adaptive/manual thinking and signed blocks in tool loops | [Anthropic](anthropic.md) |

Official behavior changes. The linked provider documentation—not these
examples—is authoritative for model availability and wire compatibility.
