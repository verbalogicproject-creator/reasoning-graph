"""Governed, append-only MemoryLog for reusable metacognitive artifacts."""

import fcntl
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

MEMORY_KINDS = frozenset({"fact", "decision", "preference", "procedure", "hypothesis"})
MEMORY_STATUSES = frozenset(
    {"proposed", "reviewable", "active", "disputed", "superseded", "retired"}
)
_TERMINAL = frozenset({"superseded", "retired"})


def _path(instance) -> Path:
    return instance.root / "memory-log.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _reject_private(value) -> None:
    """Memory is declared evidence, never provider chain-of-thought/signatures."""
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower()
            if (
                "thought" in normalized
                or "signature" in normalized
                or normalized == "encrypted_content"
            ):
                raise ValueError(
                    "MemoryLog does not store provider thought text or signatures"
                )
            _reject_private(child)
    elif isinstance(value, list):
        for child in value:
            _reject_private(child)


def _read(instance) -> list[dict]:
    path = _path(instance)
    if not path.exists():
        return []
    events = []
    with path.open(encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_SH)
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"malformed MemoryLog event at {path}:{number}"
                ) from exc
            if (
                not isinstance(event, dict)
                or not event.get("event_id")
                or not event.get("memory_id")
            ):
                raise ValueError(f"invalid MemoryLog event at {path}:{number}")
            events.append(event)
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    return events


def _read_stream(stream, path: Path) -> list[dict]:
    """Read a locked MemoryLog stream from the beginning."""
    stream.seek(0)
    events = []
    for number, line in enumerate(stream, 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed MemoryLog event at {path}:{number}") from exc
        if (
            not isinstance(event, dict)
            or not event.get("event_id")
            or not event.get("memory_id")
        ):
            raise ValueError(f"invalid MemoryLog event at {path}:{number}")
        events.append(event)
    return events


def _append_proposal(instance, event: dict) -> dict:
    """Validate proposal identity/conflicts and append under one exclusive lock."""
    _reject_private(event)
    path = _path(instance)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        events = _read_stream(stream, path)
        event_ids = {old["event_id"] for old in events}
        memory_ids = {
            old["memory_id"] for old in events if old.get("type") == "propose"
        }
        if event["event_id"] in event_ids:
            raise ValueError(f"MemoryLog event_id already exists: {event['event_id']}")
        if event["memory_id"] in memory_ids:
            raise ValueError(
                f"MemoryLog memory_id already exists: {event['memory_id']}"
            )
        unknown = sorted(set(event.get("conflicts_with") or []) - memory_ids)
        if unknown:
            raise ValueError(f"conflicts_with references unknown memory ids: {unknown}")
        stream.seek(0, os.SEEK_END)
        stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    return event


def _snapshot_events(events: list[dict]) -> dict:
    memories: dict[str, dict] = {}
    for event in events:
        eid, typ = event["memory_id"], event.get("type")
        if typ == "propose":
            if eid in memories:
                raise ValueError(f"duplicate MemoryLog proposal for {eid}")
            memories[eid] = {
                k: event.get(k)
                for k in (
                    "memory_id",
                    "kind",
                    "content",
                    "evidence",
                    "validation",
                    "agent_acknowledged",
                    "agreement",
                    "conflicts_with",
                )
            }
            memories[eid]["status"] = (
                "reviewable" if _is_reviewable(memories[eid]) else "proposed"
            )
            memories[eid]["events"] = [event["event_id"]]
        elif eid not in memories:
            raise ValueError(
                f"MemoryLog event {event['event_id']} references unknown memory {eid}"
            )
        else:
            memory = memories[eid]
            memory["events"].append(event["event_id"])
            if typ == "approve":
                memory["status"] = "active"
            elif typ in {"dispute", "supersede", "retire"}:
                memory["status"] = {
                    "dispute": "disputed",
                    "supersede": "superseded",
                    "retire": "retired",
                }[typ]
                memory["reason"] = event.get("reason")
    return {"memories": [memories[key] for key in sorted(memories)]}


def snapshot(instance) -> dict:
    """Deterministic compact current state, sorted by memory id."""
    return _snapshot_events(_read(instance))


def orientation(instance) -> dict:
    """Compact deterministic session context containing active memory only."""
    active = []
    for item in snapshot(instance)["memories"]:
        if item["status"] != "active":
            continue
        active.append(
            {
                key: item.get(key)
                for key in (
                    "memory_id",
                    "kind",
                    "content",
                    "evidence",
                    "validation",
                    "agreement",
                )
                if item.get(key) is not None
            }
        )
    return {"memorylog_version": 1, "active": active}


def _is_reviewable(memory: dict) -> bool:
    if memory["kind"] == "fact":
        evidence = memory.get("evidence")
        validation = memory.get("validation")
        return bool(
            isinstance(evidence, dict)
            and isinstance(evidence.get("source"), str)
            and evidence["source"].strip()
            and isinstance(validation, str)
            and validation.strip()
            and memory.get("agent_acknowledged") is True
        )
    return bool(memory.get("agreement"))


def propose(
    instance,
    *,
    kind: str,
    content: str,
    evidence=None,
    validation=None,
    agent_acknowledged: bool = False,
    agreement: str | None = None,
    conflicts_with: list[str] | None = None,
    memory_id: str | None = None,
    event_id: str | None = None,
) -> dict:
    if not isinstance(kind, str) or kind not in MEMORY_KINDS:
        raise ValueError(f"kind must be one of {sorted(MEMORY_KINDS)}")
    if not isinstance(content, str):
        raise ValueError("content must be a string")
    content = content.strip()
    for field, value in (("memory_id", memory_id), ("event_id", event_id)):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{field} must be a nonblank string when supplied")
    if agreement is not None and not isinstance(agreement, str):
        raise ValueError("agreement must be a string when supplied")

    if not content or len(content) > 10000:
        raise ValueError("content is required and must be at most 10000 characters")
    fact_candidate = {
        "kind": kind,
        "evidence": evidence,
        "validation": validation,
        "agent_acknowledged": agent_acknowledged,
    }
    if kind == "fact" and not _is_reviewable(fact_candidate):
        raise ValueError(
            "fact requires evidence as an object with a nonblank source, "
            "a nonblank validation string, and agent_acknowledged=true before review"
        )
    if kind != "fact" and (not isinstance(agreement, str) or not agreement.strip()):
        raise ValueError(f"{kind} requires explicit agreement before review")
    if not isinstance(conflicts_with or [], list) or not all(
        isinstance(x, str) for x in conflicts_with or []
    ):
        raise ValueError("conflicts_with must be a list of memory ids")
    event = {
        "event_id": event_id or str(uuid.uuid4()),
        "recorded_at": _now(),
        "type": "propose",
        "memory_id": memory_id or str(uuid.uuid4()),
        "kind": kind,
        "content": content,
        "evidence": evidence,
        "validation": validation,
        "agent_acknowledged": agent_acknowledged,
        "agreement": agreement.strip() if agreement else None,
        "conflicts_with": sorted(set(conflicts_with or [])),
    }
    return _append_proposal(instance, event)


def review(instance) -> dict:
    """Read-only update trigger: open review candidates but do not append events."""
    memories = snapshot(instance)["memories"]
    return {
        "review": [
            m for m in memories if m["status"] in {"proposed", "reviewable", "disputed"}
        ]
    }


def _transition(
    instance,
    memory_id: str,
    typ: str,
    *,
    reason: str | None = None,
    event_id: str | None = None,
) -> dict:
    event = {
        "event_id": event_id or str(uuid.uuid4()),
        "recorded_at": _now(),
        "type": typ,
        "memory_id": memory_id,
        "reason": reason,
    }
    _reject_private(event)
    path = _path(instance)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        events = _read_stream(stream, path)
        state = {m["memory_id"]: m for m in _snapshot_events(events)["memories"]}
        memory = state.get(memory_id)
        if not memory:
            raise KeyError(f"unknown memory_id: {memory_id}")
        if memory["status"] in _TERMINAL:
            raise ValueError(f"cannot {typ} {memory_id}: status is {memory['status']}")
        if typ == "approve":
            if not _is_reviewable(memory) or memory["status"] != "reviewable":
                raise ValueError("memory is not reviewable")
            conflicts = set(memory.get("conflicts_with") or [])
            if any(
                other["status"] == "active"
                and (
                    other_id in conflicts
                    or memory_id in set(other.get("conflicts_with") or [])
                )
                for other_id, other in state.items()
                if other_id != memory_id
            ):
                raise ValueError("cannot activate while declared conflict is active")
        if typ == "supersede" and not reason:
            raise ValueError("supersede requires replacement memory id as reason")
        if event["event_id"] in {old["event_id"] for old in events}:
            raise ValueError(f"MemoryLog event_id already exists: {event['event_id']}")
        stream.seek(0, os.SEEK_END)
        stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    return event


def approve(instance, memory_id: str, *, event_id: str | None = None) -> dict:
    return _transition(instance, memory_id, "approve", event_id=event_id)


def dispute(
    instance, memory_id: str, reason: str, *, event_id: str | None = None
) -> dict:
    if not reason.strip():
        raise ValueError("dispute requires a reason")
    return _transition(
        instance, memory_id, "dispute", reason=reason.strip(), event_id=event_id
    )


def supersede(
    instance, memory_id: str, replacement_id: str, *, event_id: str | None = None
) -> dict:
    state = {m["memory_id"] for m in snapshot(instance)["memories"]}
    if replacement_id not in state:
        raise KeyError(f"unknown replacement memory_id: {replacement_id}")
    return _transition(
        instance, memory_id, "supersede", reason=replacement_id, event_id=event_id
    )


def retire(
    instance, memory_id: str, reason: str, *, event_id: str | None = None
) -> dict:
    if not reason.strip():
        raise ValueError("retire requires a reason")
    return _transition(
        instance, memory_id, "retire", reason=reason.strip(), event_id=event_id
    )
