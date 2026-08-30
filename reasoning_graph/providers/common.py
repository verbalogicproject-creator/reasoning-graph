"""Shared provider contracts with an explicit persistence boundary."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


_OPAQUE_KEYS = frozenset({
    "encrypted_content", "signature", "thought_signature", "thoughtsignature",
})


def _scrub_opaque(value: Any) -> Any:
    """Return a JSON-safe copy without provider continuity secrets."""

    if isinstance(value, Mapping):
        return {
            key: _scrub_opaque(child)
            for key, child in value.items()
            if str(key).lower() not in _OPAQUE_KEYS
        }
    if isinstance(value, (list, tuple)):
        return [_scrub_opaque(child) for child in value]
    return deepcopy(value)


@dataclass(frozen=True)
class ProviderProfile:
    """A provider capability description, not a promise for every model ID."""

    provider: str
    api_family: str
    reasoning_controls: tuple[str, ...]
    stateful_continuation: str | None
    supports_stateless_replay: bool
    continuity_rule: str
    summary_is_raw_chain_of_thought: bool = False


@dataclass(frozen=True)
class ProviderTurnRecord:
    """Observable result plus private, transient continuity material.

    ``replay_artifacts`` deliberately has no public dataclass field.  Callers
    can retrieve a defensive copy with :meth:`continuity_payload`, while the
    default serializable form excludes it and reasoning summaries.  Neither is
    evidence for a Reasoning Graph edge or a MemoryLog fact.
    """

    provider: str
    response_id: str | None
    model: str | None
    status: str
    text: str
    tool_calls: tuple[Mapping[str, Any], ...] = ()
    usage: Mapping[str, int] = field(default_factory=dict)
    error: Mapping[str, Any] | None = None
    stop_reason: str | None = None
    reasoning_summaries: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    _replay_artifacts: tuple[Mapping[str, Any], ...] = field(
        default=(), repr=False, compare=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "tool_calls", tuple(MappingProxyType(deepcopy(dict(x))) for x in self.tool_calls))
        object.__setattr__(self, "usage", MappingProxyType(dict(self.usage)))
        if self.error is not None:
            object.__setattr__(self, "error", MappingProxyType(deepcopy(dict(self.error))))
        object.__setattr__(self, "metadata", MappingProxyType(deepcopy(dict(self.metadata))))
        object.__setattr__(self, "_replay_artifacts", tuple(deepcopy(dict(x)) for x in self._replay_artifacts))

    def continuity_payload(self) -> list[dict[str, Any]]:
        """Return exact opaque blocks for immediate provider-native replay."""

        return deepcopy([dict(x) for x in self._replay_artifacts])

    def to_persistable_dict(self, *, include_reasoning_summaries: bool = False) -> dict[str, Any]:
        """Return JSON-ready observability data with opaque artifacts removed."""

        data: dict[str, Any] = {
            "provider": self.provider,
            "response_id": self.response_id,
            "model": self.model,
            "status": self.status,
            "text": self.text,
            "tool_calls": [_scrub_opaque(dict(x)) for x in self.tool_calls],
            "usage": dict(self.usage),
            "error": _scrub_opaque(dict(self.error)) if self.error is not None else None,
            "stop_reason": self.stop_reason,
            "metadata": _scrub_opaque(dict(self.metadata)),
        }
        if include_reasoning_summaries:
            data["reasoning_summaries"] = list(self.reasoning_summaries)
        return data


def content_text(blocks: Any) -> str:
    """Extract text from common content-block lists without assuming presence."""

    if isinstance(blocks, str):
        return blocks
    if not isinstance(blocks, list):
        return ""
    values: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        value = block.get("text")
        if isinstance(value, str):
            values.append(value)
    return "".join(values)


def integer_usage(usage: Any, aliases: Mapping[str, tuple[str, ...]]) -> dict[str, int]:
    """Normalize provider token counters while ignoring malformed values."""

    if not isinstance(usage, dict):
        return {}
    result: dict[str, int] = {}
    for target, keys in aliases.items():
        for key in keys:
            value = usage.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                result[target] = value
                break
    return result
