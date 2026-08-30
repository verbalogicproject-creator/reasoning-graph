import hashlib
import json

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from reasoning_graph.schema import load_instance
from reasoning_graph.workbench.app import _safe_staged_file, create_app


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def client(tiny_instance):
    client = TestClient(create_app(tiny_instance), base_url="http://127.0.0.1")
    session = client.get("/api/session")
    assert session.headers["cache-control"] == "no-store"
    client.headers.update({"X-CSRF-Token": session.json()["csrf_token"]})
    return client


def test_workbench_serves_accessible_shell_and_read_apis(client):
    page = client.get("/")
    assert page.status_code == 200
    assert 'for="query"' in page.text
    assert 'aria-live="polite"' in page.text
    assert client.get("/api/health").json()["status"] == "ok"
    overview = client.get("/api/overview").json()
    assert overview["integrity"]["counts"]["nodes"] > 0
    assert "gap_count" in overview
    assert client.get("/api/integrity").status_code == 200
    assert client.get("/api/gaps").status_code == 200
    assert client.get("/api/frontier").status_code == 200
    assert client.get("/api/candidates").status_code == 200
    assert client.get("/api/memory").json() == {"memories": []}


def test_workbench_memory_requires_explicit_human_approval(client):
    created = client.post(
        "/api/memory",
        json={
            "kind": "decision",
            "content": "local only",
            "agreement": "user agreed",
            "memory_id": "m1",
        },
    )
    assert created.status_code == 201
    assert client.get("/api/memory/review").json()["review"][0]["memory_id"] == "m1"
    assert (
        client.post("/api/memory/approve", json={"memory_id": "m1"}).status_code == 403
    )
    assert (
        client.post(
            "/api/memory/approve", json={"approve": True, "memory_id": "m1"}
        ).status_code
        == 403
    )
    approved = client.post(
        "/api/memory/approve",
        json={"approve": True, "memory_id": "m1", "confirmation": "APPROVE MEMORY m1"},
    )
    assert approved.status_code == 200


def test_workbench_mutations_require_same_origin_json_and_csrf(client):
    payload = {
        "kind": "decision",
        "content": "attacker selected",
        "agreement": "claimed agreement",
        "memory_id": "evil",
    }
    before = client.get("/api/memory").json()
    text_plain = client.post(
        "/api/memory",
        content=json.dumps(payload),
        headers={
            "Content-Type": "text/plain",
            "Origin": "https://attacker.example",
            "X-CSRF-Token": "",
        },
    )
    assert text_plain.status_code == 415
    cross_origin = client.post(
        "/api/memory",
        json=payload,
        headers={"Origin": "https://attacker.example"},
    )
    assert cross_origin.status_code == 403
    missing_token = client.post(
        "/api/memory",
        json=payload,
        headers={"X-CSRF-Token": ""},
    )
    assert missing_token.status_code == 403
    assert client.get("/api/memory").json() == before
    valid = client.post(
        "/api/memory", json=payload, headers={"Origin": "http://127.0.0.1"}
    )
    assert valid.status_code == 201


def test_workbench_resolve_and_observation_do_not_change_db(client, tiny_instance):
    instance = load_instance(tiny_instance)
    before = _hash(instance.db_path)
    answer = client.get("/api/resolve", params={"start": "loom_1", "end": "dye_bath_2"})
    assert answer.status_code == 200
    body = answer.json()
    assert body["path"] and body["provenance"]
    created = client.post(
        "/api/observations",
        json={
            "query": "find a supported path",
            "resolution_status": "ANSWER",
            "outcome": "success",
            "event_id": "workbench-test-event",
        },
    )
    assert created.status_code == 201
    assert _hash(instance.db_path) == before
    assert any(
        e["event_id"] == "workbench-test-event"
        for e in client.get("/api/observations").json()["entries"]
    )


def test_workbench_mutations_fail_closed_and_confine_staged_path(client, tiny_instance):
    assert (
        client.post("/api/actions/freeze", json={"staged_path": "x.md"}).status_code
        == 403
    )
    rejected = client.post(
        "/api/actions/freeze", json={"approve": True, "staged_path": "../x.md"}
    )
    assert rejected.status_code == 422
    assert client.post("/api/actions/retire", json={}).status_code == 403
    assert client.post("/api/actions/retire", json={"approve": True}).status_code == 403
    assert (
        client.post("/api/actions/verify", json={"staged_path": "../x.md"}).status_code
        == 422
    )


def test_safe_staging_path_rejects_escape(tiny_instance):
    with pytest.raises(ValueError):
        _safe_staged_file(load_instance(tiny_instance), "../outside.md")


def test_workbench_frontend_has_no_em_dash_or_numbered_section_labels():
    root = (
        __import__("pathlib").Path(__file__).parents[1]
        / "reasoning_graph"
        / "workbench"
        / "static"
    )
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.*"))
    assert "—" not in text
    assert "01 /" not in text and "07 /" not in text
    assert "cytoscape.min.js" in text
    assert "Loading candidates." in text
    assert "No staged candidates." in text
    assert "Workbench data unavailable:" in text
    assert 'id="resolve-state"' in text
