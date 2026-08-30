"""Anthropic Messages API request and response contracts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

from .common import ProviderProfile, ProviderTurnRecord, integer_usage

ANTHROPIC_PROFILE = ProviderProfile(
    provider="anthropic",
    api_family="Messages API",
    reasoning_controls=(
        "thinking.type",
        "thinking.display",
        "thinking.budget_tokens",
        "output_config.effort",
    ),
    stateful_continuation=None,
    supports_stateless_replay=True,
    continuity_rule="Within tool-use turns replay the complete original assistant content, "
    "including thinking and tool-use blocks, complete and unmodified.",
)


def build_anthropic_request(
    *,
    model: str,
    messages: list[dict[str, Any]],
    max_tokens: int = 16_000,
    thinking_mode: str = "adaptive",
    display: str | None = "summarized",
    effort: str | None = None,
    budget_tokens: int | None = None,
    replay_content: Iterable[Mapping[str, Any]] = (),
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build ``client.messages.create`` kwargs for adaptive or manual thinking."""

    if thinking_mode not in {"adaptive", "enabled", "disabled"}:
        raise ValueError("thinking_mode must be adaptive, enabled, or disabled")
    if thinking_mode == "enabled" and budget_tokens is None:
        raise ValueError("manual thinking requires budget_tokens")
    if thinking_mode != "enabled" and budget_tokens is not None:
        raise ValueError("budget_tokens is only valid with manual enabled thinking")
    if display not in {None, "summarized", "omitted"}:
        raise ValueError("display must be summarized, omitted, or None")
    if thinking_mode == "enabled" and (
        isinstance(budget_tokens, bool) or budget_tokens < 1024
    ):
        raise ValueError("manual thinking budget_tokens must be at least 1024")
    if thinking_mode == "disabled" and display is not None:
        raise ValueError("display is invalid when thinking is disabled")
    replay = [deepcopy(dict(block)) for block in replay_content]
    replay_types = {block.get("type") for block in replay}
    if replay and (
        "tool_use" not in replay_types
        or not replay_types.intersection({"thinking", "redacted_thinking"})
    ):
        raise ValueError(
            "replay_content must be complete assistant content including thinking/redacted_thinking and tool_use"
        )
    request_messages = deepcopy(messages)
    if replay:
        # Replay is the complete original assistant content. Place it immediately
        # before the latest user tool-result message when present; otherwise
        # append it after the caller's existing user turn.
        insert_at = len(request_messages)
        for index in range(len(request_messages) - 1, -1, -1):
            message = request_messages[index]
            content = message.get("content") if isinstance(message, dict) else None
            if (
                isinstance(message, dict)
                and message.get("role") == "user"
                and isinstance(content, list)
                and any(
                    isinstance(block, dict) and block.get("type") == "tool_result"
                    for block in content
                )
            ):
                insert_at = index
                break
        request_messages.insert(insert_at, {"role": "assistant", "content": replay})
    thinking: dict[str, Any] = {"type": thinking_mode}
    if display is not None:
        thinking["display"] = display
    if budget_tokens is not None:
        thinking["budget_tokens"] = budget_tokens
    request: dict[str, Any] = {
        "model": model,
        "messages": request_messages,
        "max_tokens": max_tokens,
        "thinking": thinking,
    }
    if effort is not None:
        request["output_config"] = {"effort": effort}
    if tools is not None:
        request["tools"] = deepcopy(tools)
    return request


def normalize_anthropic_response(response: Mapping[str, Any]) -> ProviderTurnRecord:
    content = response.get("content")
    blocks = content if isinstance(content, list) else []
    text_parts: list[str] = []
    summaries: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    replay: list[dict[str, Any]] = []
    for raw in blocks:
        if not isinstance(raw, dict):
            continue
        kind = raw.get("type")
        if kind == "text" and isinstance(raw.get("text"), str):
            text_parts.append(raw["text"])
        elif kind in {"thinking", "redacted_thinking"}:
            if isinstance(raw.get("thinking"), str) and raw["thinking"]:
                summaries.append(raw["thinking"])
            replay.append(deepcopy(raw))
        elif kind == "tool_use":
            tool_calls.append(deepcopy(raw))
    error = response.get("error") if isinstance(response.get("error"), dict) else None
    if tool_calls:
        replay = [deepcopy(raw) for raw in blocks if isinstance(raw, dict)]
    stop_reason = _optional_str(response.get("stop_reason"))
    status = str(
        response.get("status")
        or ("failed" if error else "completed" if stop_reason else "unknown")
    )
    return ProviderTurnRecord(
        provider="anthropic",
        response_id=_optional_str(response.get("id")),
        model=_optional_str(response.get("model")),
        status=status,
        text="".join(text_parts),
        tool_calls=tuple(tool_calls),
        usage=integer_usage(
            response.get("usage"),
            {
                "input_tokens": ("input_tokens",),
                "output_tokens": ("output_tokens",),
            },
        ),
        error=error,
        stop_reason=stop_reason,
        reasoning_summaries=tuple(summaries),
        metadata={},
        _replay_artifacts=tuple(replay),
    )


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None
