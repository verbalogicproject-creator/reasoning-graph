"""Gemini Interactions API request and response contracts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

from .common import ProviderProfile, ProviderTurnRecord, content_text, integer_usage

GEMINI_PROFILE = ProviderProfile(
    provider="gemini",
    api_family="Interactions API",
    reasoning_controls=("thinking_level", "thinking_summaries"),
    stateful_continuation="previous_interaction_id with store=true",
    supports_stateless_replay=True,
    continuity_rule="In stateless mode replay complete step history, preserving signed steps exactly.",
)


def build_gemini_request(
    *,
    model: str,
    input: str | list[dict[str, Any]],
    thinking_level: str | None = None,
    thinking_summaries: str | None = "auto",
    previous_interaction_id: str | None = None,
    store: bool = True,
    replay_steps: Iterable[Mapping[str, Any]] = (),
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build ``client.interactions.create`` kwargs with continuity validation."""

    prior = [deepcopy(dict(step)) for step in replay_steps]
    if previous_interaction_id and (not store or prior):
        raise ValueError("previous_interaction_id requires stateful store=true without replay_steps")
    request_input: str | list[dict[str, Any]] = input
    if prior:
        current = input if isinstance(input, list) else [{"type": "user", "content": input}]
        request_input = prior + deepcopy(current)
    config: dict[str, str] = {}
    if thinking_level is not None:
        config["thinking_level"] = thinking_level
    if thinking_summaries is not None:
        config["thinking_summaries"] = thinking_summaries
    request: dict[str, Any] = {"model": model, "input": request_input, "store": store}
    if config:
        request["generation_config"] = config
    if previous_interaction_id:
        request["previous_interaction_id"] = previous_interaction_id
    if tools is not None:
        request["tools"] = deepcopy(tools)
    return request


def normalize_gemini_response(response: Mapping[str, Any]) -> ProviderTurnRecord:
    steps = response.get("steps")
    items = steps if isinstance(steps, list) else []
    text_parts: list[str] = []
    summaries: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    replay = [deepcopy(step) for step in items if isinstance(step, dict)]
    for raw in items:
        if not isinstance(raw, dict):
            continue
        kind = str(raw.get("type") or "")
        if kind == "thought":
            summaries.append(content_text(raw.get("summary")))
        elif kind == "model_output":
            text_parts.append(content_text(raw.get("content")))
        elif kind in {"function_call", "tool_call", "google_search_call"}:
            tool_calls.append(deepcopy(raw))
    error = response.get("error") if isinstance(response.get("error"), dict) else None
    return ProviderTurnRecord(
        provider="gemini",
        response_id=_optional_str(response.get("id")),
        model=_optional_str(response.get("model")),
        status=str(response.get("status") or ("failed" if error else "unknown")),
        text="".join(text_parts) or str(response.get("output_text") or ""),
        tool_calls=tuple(tool_calls),
        usage=integer_usage(response.get("usage"), {
            "input_tokens": ("total_input_tokens", "input_tokens"),
            "output_tokens": ("total_output_tokens", "output_tokens"),
            "reasoning_tokens": ("total_thought_tokens", "thought_tokens"),
            "total_tokens": ("total_tokens",),
        }),
        error=error,
        stop_reason=_optional_str(response.get("finish_reason")),
        reasoning_summaries=tuple(x for x in summaries if x),
        metadata={}, _replay_artifacts=tuple(replay),
    )


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None
