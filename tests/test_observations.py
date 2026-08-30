from __future__ import annotations

import hashlib

import pytest

from reasoning_graph.observations import read_observations, record_observation
from reasoning_graph.schema import load_instance


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_observation_is_append_only_and_does_not_change_graph(tiny_instance):
    inst = load_instance(tiny_instance)
    before = _hash(inst.db_path)
    first = record_observation(
        inst, event_id="event-1", query="Can this path be trusted?",
        resolution_status="REFUSE", outcome="gap",
        event_time="2026-08-29T20:00:00+00:00",
        gap_classification="missing-provenance",
        details={"source": "test"})
    second = record_observation(
        inst, event_id="event-2", query="The later outcome contradicted it",
        resolution_status="ANSWER", outcome="contradiction")

    assert _hash(inst.db_path) == before
    assert [row["event_id"] for row in read_observations(inst)] == ["event-1", "event-2"]
    assert first["event_time"] == "2026-08-29T20:00:00+00:00"
    assert second["details"] == {}


def test_observation_rejects_duplicates_unbounded_or_invalid_data(tiny_instance):
    inst = load_instance(tiny_instance)
    kwargs = dict(query="q", resolution_status="REFUSE", outcome="gap")
    record_observation(inst, event_id="same", **kwargs)
    with pytest.raises(ValueError, match="already exists"):
        record_observation(inst, event_id="same", **kwargs)
    with pytest.raises(ValueError, match="ISO-8601"):
        record_observation(inst, event_time="yesterday", **kwargs)
    with pytest.raises(ValueError, match="timezone"):
        record_observation(inst, event_time="2026-08-29T20:00:00", **kwargs)
    with pytest.raises(ValueError, match="JSON-serializable"):
        record_observation(inst, details={"bad": object()}, **kwargs)
    with pytest.raises(ValueError, match="16384"):
        record_observation(inst, details={"large": "x" * 17000}, **kwargs)
