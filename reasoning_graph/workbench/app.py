"""FastAPI workbench. Reads graph evidence; mutations are explicit and bounded."""

from __future__ import annotations

import argparse
import hashlib
import secrets
from pathlib import Path
from typing import Any
from starlette.requests import Request

from ..loop.fcl import parse_log
from ..measure.frontier_rate import compute as frontier_compute
from .. import memory
from ..observations import read_observations, record_observation
from ..resolver import resolve
from ..schema import load_instance
from ..store import inspect_integrity


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _candidate_files(instance) -> list[dict[str, str]]:
    """Expose only declared staged files, never arbitrary host paths."""
    staged = instance.staged_dir
    if not staged or not staged.exists():
        return []
    return [
        {"name": p.name, "path": p.name, "bytes": str(p.stat().st_size)}
        for p in sorted(staged.iterdir())
        if p.is_file() and p.suffix.lower() == ".md"
    ]


def _safe_staged_file(instance, supplied: str) -> Path:
    if not instance.staged_dir:
        raise ValueError("this instance does not declare a staging directory")
    root = instance.staged_dir.resolve()
    candidate = (root / supplied).resolve()
    if (
        candidate.parent != root
        or candidate.suffix.lower() != ".md"
        or not candidate.is_file()
    ):
        raise ValueError(
            "staged_path must name an existing Markdown file directly in staged_dir"
        )
    return candidate


def _overview(instance) -> dict[str, Any]:
    integrity = inspect_integrity(instance)
    try:
        frontier = frontier_compute(instance)
    except (OSError, ValueError) as exc:
        frontier = {"error": str(exc)}
    try:
        observations = read_observations(instance)
    except ValueError as exc:
        observations = []
        observation_error = str(exc)
    else:
        observation_error = None
    return {
        "instance": instance.name,
        "db_path": str(instance.db_path),
        "db_sha256": _sha256(instance.db_path),
        "integrity": integrity,
        "frontier": frontier,
        "gap_count": len(parse_log(instance)),
        "observation_count": len(observations),
        "observation_error": observation_error,
        "memory_count": len(memory.snapshot(instance)["memories"]),
        "mutation_policy": "human approval is required; graph writes are restricted to declared staging paths",
    }


def create_app(instance_path: str | Path):
    """Return a localhost-oriented application bound to exactly one instance."""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import HTMLResponse, JSONResponse
        from fastapi.staticfiles import StaticFiles
    except ImportError as exc:  # pragma: no cover - import environment only
        raise RuntimeError(
            "workbench support requires: pip install 'reasoning-graph[workbench]'"
        ) from exc

    instance = load_instance(instance_path)
    app = FastAPI(title="Reasoning Graph Workbench", docs_url=None, redoc_url=None)
    static = Path(__file__).with_name("static")
    app.mount("/static", StaticFiles(directory=static), name="static")
    csrf_token = secrets.token_urlsafe(32)

    async def protected_json(request: Request) -> dict[str, Any]:
        """Accept local same-origin JSON requests carrying the session token."""
        media_type = (
            request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        )
        if media_type != "application/json":
            raise HTTPException(415, "mutations require Content-Type: application/json")
        if request.url.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise HTTPException(403, "workbench mutations require a loopback Host")
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
            raise HTTPException(403, "cross-origin workbench mutations are forbidden")
        supplied = request.headers.get("x-csrf-token", "")
        if not supplied or not secrets.compare_digest(supplied, csrf_token):
            raise HTTPException(403, "missing or invalid workbench CSRF token")
        data = await request.json()
        if not isinstance(data, dict):
            raise ValueError("body must be a JSON object")
        return data

    @app.get("/api/session")
    def session() -> JSONResponse:
        return JSONResponse(
            {"csrf_token": csrf_token},
            headers={"Cache-Control": "no-store"},
        )

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return (static / "index.html").read_text(encoding="utf-8")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "instance": instance.name, "bind": "127.0.0.1"}

    @app.get("/api/overview")
    def overview() -> dict[str, Any]:
        return _overview(instance)

    @app.get("/api/integrity")
    def integrity() -> dict[str, Any]:
        return inspect_integrity(instance)

    @app.get("/api/resolve")
    def resolve_api(
        start: str | None = None,
        end: str | None = None,
        text: str | None = None,
        weighted: bool = True,
        include_dormant: bool = False,
        hard: bool = False,
    ) -> dict:
        if bool(text) == bool(start and end):
            raise HTTPException(422, "provide text, or both start and end")
        try:
            return resolve(
                instance,
                start=start,
                end=end,
                text=text,
                weighted=weighted,
                include_dormant=include_dormant,
                hard=hard,
            )
        except (OSError, ValueError, KeyError) as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.get("/api/gaps")
    def gaps() -> dict[str, Any]:
        return {"entries": parse_log(instance)}

    @app.get("/api/frontier")
    def frontier() -> dict[str, Any]:
        return frontier_compute(instance)

    @app.get("/api/observations")
    def observations() -> dict[str, Any]:
        try:
            return {"entries": read_observations(instance)}
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/api/memory")
    def memory_list() -> dict[str, Any]:
        return memory.snapshot(instance)

    @app.get("/api/memory/review")
    def memory_review() -> dict[str, Any]:
        return memory.review(instance)

    @app.post("/api/memory", status_code=201)
    async def memory_propose(request: Request) -> dict[str, Any]:
        try:
            data = await protected_json(request)
            if not isinstance(data, dict):
                raise ValueError("body must be a JSON object")
            return memory.propose(instance, **data)
        except (ValueError, TypeError, KeyError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/api/memory/approve")
    async def memory_approve(request: Request) -> dict[str, Any]:
        try:
            data = await protected_json(request)
            if not isinstance(data, dict) or data.get("approve") is not True:
                raise PermissionError("memory approval requires explicit approve: true")
            memory_id = str(data.get("memory_id", ""))
            if data.get("confirmation") != f"APPROVE MEMORY {memory_id}":
                raise PermissionError(
                    "memory approval requires typed confirmation: APPROVE MEMORY <memory_id>"
                )
            return memory.approve(instance, memory_id)
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        except (ValueError, KeyError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/api/observations", status_code=201)
    async def append_observation(request: Request) -> dict[str, Any]:
        try:
            data = await protected_json(request)
            if not isinstance(data, dict):
                raise ValueError("body must be a JSON object")
            return record_observation(instance, **data)
        except (ValueError, TypeError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get("/api/candidates")
    def candidates() -> dict[str, Any]:
        return {
            "staged_dir": str(instance.staged_dir) if instance.staged_dir else None,
            "entries": _candidate_files(instance),
        }

    @app.post("/api/actions/freeze")
    async def freeze_action(request: Request) -> dict[str, Any]:
        """Fail closed: true boolean approval and a direct staged child are mandatory."""
        try:
            data = await protected_json(request)
            if not isinstance(data, dict) or data.get("approve") is not True:
                raise PermissionError("freeze requires explicit approve: true")
            staged = _safe_staged_file(instance, str(data.get("staged_path", "")))
            if data.get("confirmation") != f"FREEZE {staged.name}":
                raise PermissionError(
                    "freeze requires typed confirmation: FREEZE <staged filename>"
                )
            from ..loop.freeze import freeze

            return freeze(instance, staged, approve=True)
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        except (ValueError, OSError, KeyError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/api/actions/verify")
    async def verify_action(request: Request) -> dict[str, Any]:
        """Verification is read-only but its path is still tightly scoped."""
        try:
            data = await protected_json(request)
            if not isinstance(data, dict):
                raise ValueError("body must be a JSON object")
            staged = _safe_staged_file(instance, str(data.get("staged_path", "")))
            from ..loop.verify import verify

            return verify(instance, staged)
        except (ValueError, OSError, KeyError) as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/api/actions/retire")
    async def retire_action(request: Request) -> dict[str, Any]:
        try:
            data = await protected_json(request)
            if not isinstance(data, dict) or data.get("approve") is not True:
                raise PermissionError("retire requires explicit approve: true")
            if data.get("confirmation") != "RETIRE RULES":
                raise PermissionError(
                    "retire requires typed confirmation: RETIRE RULES"
                )
            from ..loop.retire import retire_pass

            return retire_pass(instance, approve=True)
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        except (ValueError, OSError) as exc:
            raise HTTPException(422, str(exc)) from exc

    return app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Serve a local reasoning-graph workbench."
    )
    parser.add_argument("--instance", required=True, help="path to instance.json")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        choices=["127.0.0.1"],
        help="local-only bind address",
    )
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "workbench support requires: pip install 'reasoning-graph[workbench]'"
        ) from exc
    uvicorn.run(create_app(args.instance), host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
