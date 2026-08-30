"""Append-only observation ledger for metacognitive feedback.

Observations can nominate recurring gaps, but this module has no graph writer
and cannot activate, freeze, retire, or otherwise alter a reasoning rule.
"""
from __future__ import annotations

import fcntl
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

RESOLUTION_STATUSES = frozenset({"ANSWER", "WEAK_ANSWER", "REFUSE", "ERROR"})
MAX_DETAILS_BYTES = 16_384
OUTCOMES = frozenset({"success", "failure", "contradiction", "gap", "unknown"})


def _clean_optional(value: str | None, field: str, limit: int = 4096) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if len(value) > limit:
        raise ValueError(f"{field} exceeds {limit} characters")
    return value


def _event_time(value: str | None) -> str | None:
    value = _clean_optional(value, "event_time", 100)
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("event_time must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("event_time must include a timezone")
    return value


def read_observations(instance) -> list[dict]:
    """Read valid JSONL records. A malformed line is refusal-grade."""
    path = Path(instance.observations_path or (instance.root / "observations.jsonl"))
    if not path.exists():
        return []
    records = []
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"malformed observation at {path}:{number}") from exc
            if not isinstance(value, dict) or not value.get("event_id"):
                raise ValueError(f"invalid observation at {path}:{number}")
            records.append(value)
    return records


def record_observation(
    instance,
    *,
    query: str,
    resolution_status: str,
    outcome: str,
    event_id: str | None = None,
    event_time: str | None = None,
    path_signature: str | None = None,
    source_ref: str | None = None,
    gap_classification: str | None = None,
    details: dict | None = None,
) -> dict:
    """Validate and append one event without touching graph storage."""
    query = query.strip()
    if not query:
        raise ValueError("query is required")
    if len(query) > 10000:
        raise ValueError("query exceeds 10000 characters")
    if resolution_status not in RESOLUTION_STATUSES:
        raise ValueError(f"resolution_status must be one of {sorted(RESOLUTION_STATUSES)}")
    if outcome not in OUTCOMES:
        raise ValueError(f"outcome must be one of {sorted(OUTCOMES)}")
    if details is not None and not isinstance(details, dict):
        raise ValueError("details must be a JSON object")
    try:
        details_json = json.dumps(details or {}, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise ValueError("details must be JSON-serializable") from exc
    if len(details_json.encode("utf-8")) > MAX_DETAILS_BYTES:
        raise ValueError(f"details exceeds {MAX_DETAILS_BYTES} UTF-8 bytes")

    event_id = _clean_optional(event_id, "event_id", 200) or str(uuid.uuid4())
    record = {
        "event_id": event_id,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "event_time": _event_time(event_time),
        "query": query,
        "resolution_status": resolution_status,
        "outcome": outcome,
        "path_signature": _clean_optional(path_signature, "path_signature"),
        "source_ref": _clean_optional(source_ref, "source_ref"),
        "gap_classification": _clean_optional(gap_classification, "gap_classification"),
        "details": details or {},
    }

    path = Path(instance.observations_path or (instance.root / "observations.jsonl"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        stream.seek(0)
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                existing = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"malformed observation at {path}:{number}") from exc
            if existing.get("event_id") == event_id:
                raise ValueError(f"observation event_id already exists: {event_id}")
        stream.seek(0, os.SEEK_END)
        stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    return record
