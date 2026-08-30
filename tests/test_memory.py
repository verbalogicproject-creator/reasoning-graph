import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from reasoning_graph import memory
from reasoning_graph.schema import load_instance


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_memory_kinds_lifecycle_and_deterministic_snapshot(tiny_instance):
    inst = load_instance(tiny_instance)
    before = _hash(inst.db_path)
    ids = []
    for kind in ("decision", "preference", "procedure", "hypothesis"):
        event = memory.propose(
            inst, kind=kind, content=kind, agreement="user agreed", memory_id=kind
        )
        ids.append(event["memory_id"])
        assert (
            next(
                m for m in memory.snapshot(inst)["memories"] if m["memory_id"] == kind
            )["status"]
            == "reviewable"
        )
        memory.approve(inst, kind)
    fact = memory.propose(
        inst,
        kind="fact",
        content="verified",
        evidence={"source": "test"},
        validation="checked",
        agent_acknowledged=True,
        memory_id="fact",
    )
    memory.approve(inst, fact["memory_id"])
    memory.dispute(inst, "fact", "new evidence")
    memory.retire(inst, "fact", "obsolete")
    first, second = memory.snapshot(inst), memory.snapshot(inst)
    assert first == second and {m["status"] for m in first["memories"]} >= {
        "active",
        "retired",
    }
    assert _hash(inst.db_path) == before


def test_fact_requirements_conflicts_and_read_only_review(tiny_instance):
    inst = load_instance(tiny_instance)
    with pytest.raises(ValueError, match="fact requires"):
        memory.propose(inst, kind="fact", content="x")
    active = memory.propose(
        inst, kind="decision", content="a", agreement="yes", memory_id="a"
    )
    memory.approve(inst, active["memory_id"])
    proposed = memory.propose(
        inst,
        kind="decision",
        content="b",
        agreement="yes",
        conflicts_with=["a"],
        memory_id="b",
    )
    with pytest.raises(ValueError, match="conflict"):
        memory.approve(inst, proposed["memory_id"])
    before = (inst.root / "memory-log.jsonl").read_bytes()
    assert memory.review(inst)["review"]
    assert (inst.root / "memory-log.jsonl").read_bytes() == before


def test_memory_rejects_malformed_duplicate_and_provider_private_text(tiny_instance):
    inst = load_instance(tiny_instance)
    memory.propose(
        inst, kind="preference", content="x", agreement="yes", event_id="once"
    )
    with pytest.raises(ValueError, match="already exists"):
        memory.propose(
            inst, kind="preference", content="y", agreement="yes", event_id="once"
        )
    with pytest.raises(ValueError, match="thought text"):
        memory.propose(
            inst,
            kind="fact",
            content="x",
            evidence={"source": "test", "thought": "private"},
            validation="v",
            agent_acknowledged=True,
        )
    with pytest.raises(ValueError, match="thought text"):
        memory.propose(
            inst,
            kind="fact",
            content="x",
            evidence={"source": "test", "encrypted_content": "opaque"},
            validation="v",
            agent_acknowledged=True,
        )


def test_orientation_contains_only_active_memory(tiny_instance):
    inst = load_instance(tiny_instance)
    memory.propose(
        inst,
        kind="decision",
        content="active choice",
        agreement="user and agent agree",
        memory_id="active",
    )
    memory.approve(inst, "active")
    memory.propose(
        inst,
        kind="hypothesis",
        content="still pending",
        agreement="shared hypothesis",
        memory_id="pending",
    )

    assert memory.orientation(inst) == {
        "memorylog_version": 1,
        "active": [
            {
                "memory_id": "active",
                "kind": "decision",
                "content": "active choice",
                "agreement": "user and agent agree",
            }
        ],
    }


@pytest.mark.parametrize(
    ("evidence", "validation"),
    [
        (True, "checked"),
        (["source"], "checked"),
        ({}, "checked"),
        ({"source": "   "}, "checked"),
        ({"source": "test"}, "   "),
    ],
)
def test_fact_requires_cited_evidence_schema(tiny_instance, evidence, validation):
    inst = load_instance(tiny_instance)
    with pytest.raises(ValueError, match="nonblank source"):
        memory.propose(
            inst,
            kind="fact",
            content="x",
            evidence=evidence,
            validation=validation,
            agent_acknowledged=True,
        )


def test_declared_conflicts_are_symmetric_during_activation(tiny_instance):
    inst = load_instance(tiny_instance)
    memory.propose(inst, kind="decision", content="a", agreement="yes", memory_id="a")
    memory.propose(
        inst,
        kind="decision",
        content="b",
        agreement="yes",
        conflicts_with=["a"],
        memory_id="b",
    )
    memory.approve(inst, "b")
    with pytest.raises(ValueError, match="conflict"):
        memory.approve(inst, "a")


def test_concurrent_activation_cannot_create_an_active_conflict_pair(tiny_instance):
    inst = load_instance(tiny_instance)
    memory.propose(inst, kind="decision", content="c", agreement="yes", memory_id="c")
    memory.propose(
        inst,
        kind="decision",
        content="d",
        agreement="yes",
        conflicts_with=["c"],
        memory_id="d",
    )
    barrier = threading.Barrier(2)

    def activate(memory_id):
        barrier.wait()
        try:
            memory.approve(inst, memory_id)
            return "active"
        except ValueError:
            return "blocked"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(activate, ("c", "d")))

    assert sorted(outcomes) == ["active", "blocked"]
    active = [
        item["memory_id"]
        for item in memory.snapshot(inst)["memories"]
        if item["status"] == "active"
    ]
    assert active in [["c"], ["d"]]


def test_duplicate_memory_ids_are_rejected_without_corrupting_log(tiny_instance):
    inst = load_instance(tiny_instance)
    memory.propose(
        inst, kind="decision", content="first", agreement="yes", memory_id="same"
    )
    before = (inst.root / "memory-log.jsonl").read_bytes()
    with pytest.raises(ValueError, match="memory_id already exists"):
        memory.propose(
            inst, kind="decision", content="second", agreement="yes", memory_id="same"
        )
    assert (inst.root / "memory-log.jsonl").read_bytes() == before
    assert [item["memory_id"] for item in memory.snapshot(inst)["memories"]] == ["same"]


def test_concurrent_duplicate_memory_ids_allow_exactly_one_proposal(tiny_instance):
    inst = load_instance(tiny_instance)
    barrier = threading.Barrier(2)

    def propose_duplicate(content):
        barrier.wait()
        try:
            memory.propose(
                inst,
                kind="decision",
                content=content,
                agreement="yes",
                memory_id="same",
            )
            return "accepted"
        except ValueError:
            return "blocked"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(propose_duplicate, ("first", "second")))

    assert sorted(outcomes) == ["accepted", "blocked"]
    snapshot = memory.snapshot(inst)["memories"]
    assert len(snapshot) == 1
    assert snapshot[0]["memory_id"] == "same"
