"""OpenAI Responses API request and response contracts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

from .common import ProviderProfile, ProviderTurnRecord, content_text, integer_usage

OPENAI_PROFILE = ProviderProfile(
    provider="openai",
    api_family="Responses API",
    reasoning_controls=("effort", "summary", "context"),
    stateful_continuation="conversation or previous_response_id",
    supports_stateless_replay=True,
    continuity_rule="Replay every response output item unchanged when state is not stored.",
)


def build_openai_request(
    *,
    model: str,
    input: str | list[dict[str, Any]],
    effort: str | None = "medium",
    summary: str | None = "auto",
    reasoning_context: str | None = None,
    previous_response_id: str | None = None,
    conversation: str | None = None,
    store: bool = True,
    replay_items: Iterable[Mapping[str, Any]] = (),
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build SDK-ready kwargs without importing or calling the OpenAI SDK."""

    if previous_response_id and conversation:
        raise ValueError("previous_response_id and conversation are mutually exclusive")
    prior = [deepcopy(dict(item)) for item in replay_items]
    if prior and (previous_response_id or conversation):
        raise ValueError(
            "stateless replay cannot be combined with server-managed continuation"
        )
    request_input: str | list[dict[str, Any]] = input
    if prior:
        current = (
            input if isinstance(input, list) else [{"role": "user", "content": input}]
        )
        request_input = prior + deepcopy(current)
    reasoning: dict[str, Any] = {}
    if effort is not None:
        reasoning["effort"] = effort
    if summary is not None:
        reasoning["summary"] = summary
    if reasoning_context is not None:
        reasoning["context"] = reasoning_context
    request: dict[str, Any] = {"model": model, "input": request_input, "store": store}
    if reasoning:
        request["reasoning"] = reasoning
    if not store:
        request["include"] = ["reasoning.encrypted_content"]
    if previous_response_id:
        request["previous_response_id"] = previous_response_id
    if conversation:
        request["conversation"] = conversation
    if tools is not None:
        request["tools"] = deepcopy(tools)
    return request


def normalize_openai_response(response: Mapping[str, Any]) -> ProviderTurnRecord:
    output = response.get("output")
    items = output if isinstance(output, list) else []
    text_parts: list[str] = []
    summaries: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    replay = [deepcopy(item) for item in items if isinstance(item, dict)]
    for raw in items:
        if not isinstance(raw, dict):
            continue
        item_type = raw.get("type")
        if item_type == "message":
            text_parts.append(content_text(raw.get("content")))
        elif item_type == "reasoning":
            summaries.append(content_text(raw.get("summary")))
        elif item_type in {
            "function_call",
            "custom_tool_call",
            "computer_call",
            "program",
        }:
            tool_calls.append(deepcopy(raw))
    usage = integer_usage(
        response.get("usage"),
        {
            "input_tokens": ("input_tokens",),
            "output_tokens": ("output_tokens",),
            "total_tokens": ("total_tokens",),
        },
    )
    raw_usage = response.get("usage")
    if isinstance(raw_usage, dict):
        details = raw_usage.get("output_tokens_details")
        if isinstance(details, dict) and isinstance(
            details.get("reasoning_tokens"), int
        ):
            usage["reasoning_tokens"] = details["reasoning_tokens"]
    error = response.get("error") if isinstance(response.get("error"), dict) else None
    status = str(response.get("status") or ("failed" if error else "unknown"))
    incomplete = response.get("incomplete_details")
    stop_reason = incomplete.get("reason") if isinstance(incomplete, dict) else None
    return ProviderTurnRecord(
        provider="openai",
        response_id=_optional_str(response.get("id")),
        model=_optional_str(response.get("model")),
        status=status,
        text="".join(text_parts) or str(response.get("output_text") or ""),
        tool_calls=tuple(tool_calls),
        usage=usage,
        error=error,
        stop_reason=_optional_str(stop_reason),
        reasoning_summaries=tuple(x for x in summaries if x),
        metadata={"reasoning_context": _reasoning_context(response.get("reasoning"))},
        _replay_artifacts=tuple(replay),
    )


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _reasoning_context(value: Any) -> str | None:
    return _optional_str(value.get("context")) if isinstance(value, dict) else None
