"""CLI — the full declared surface. The argparse tree IS the contract (docs/09);
gates drive everything through it. Every subcommand supports --json (single JSON
object on stdout).

Exit codes (frozen; gates depend on them):
  0 — success (including status=REFUSE results: refusal is a result, not an error)
  1 — error (bad args, missing files, adapter failure)
  3 — NOT-IMPLEMENTED: the handler is an Opus-phase stub. gates translate 3 into
      their own NOT-BUILT verdict.

IMPLEMENTED THIS SESSION: the tree, --json plumbing, `schema validate`.
OPUS-FILLS: every handler currently returning _not_implemented().
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

NOT_IMPLEMENTED_EXIT = 3


def _emit(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for k, v in payload.items():
            print(f"{k}: {v}")


def _not_implemented(args, phase: str) -> int:
    _emit({"error": "NOT-IMPLEMENTED",
           "detail": f"stub — OPUS-FILLS in {phase}; see the module docstring contract and the SoT phase plan",
           "command": getattr(args, "_cmdpath", "?")}, getattr(args, "json", False))
    return NOT_IMPLEMENTED_EXIT


def _cmd_schema_validate(args) -> int:
    from .schema import load_instance
    inst = load_instance(args.instance)  # raises loudly on any structural problem
    _emit({"ok": True, "instance": inst.name, "schema": inst.schema.name,
           "node_kinds": len(inst.schema.node_kinds),
           "edge_kinds": len(inst.schema.edge_kinds),
           "floor": inst.schema.floor,
           "promotion_threshold": inst.schema.promotion_threshold,
           "db_path": str(inst.db_path)}, args.json)
    return 0


def _cmd_migrate(args) -> int:
    from .migrations import m001_edge_confidence
    from .schema import load_instance
    inst = load_instance(args.instance)
    report = m001_edge_confidence(inst, dry_run=args.dry_run, backup=not args.no_backup)
    _emit(report, args.json)
    return 0


def _cmd_resolve(args) -> int:
    from .resolver import resolve
    from .schema import load_instance
    inst = load_instance(args.instance)
    ans = resolve(inst, start=args.start, end=args.end, text=args.text,
                  weighted=not args.unweighted, include_dormant=args.include_dormant,
                  hard=args.hard)
    _emit(ans, args.json)
    return 0   # REFUSE is a result, not an error — exit 0


def _cmd_analytics(args) -> int:
    from .resolver import cycles, pagerank
    from .schema import load_instance
    inst = load_instance(args.instance)
    result = pagerank(inst, top=args.top) if args.action == "pagerank" else cycles(inst)
    _emit({"action": args.action, "result": result}, args.json)
    return 0


def _cmd_loop(args) -> int:
    from .schema import load_instance
    from .loop import fcl, promote, mint, verify, freeze, retire
    inst = load_instance(args.instance)
    act = args.action
    if act == "scan":
        _emit({"entries": fcl.parse_log(inst)}, args.json)
    elif act == "promote":
        if args.entry:
            promote.promote(inst, args.entry)
            _emit({"promoted": args.entry}, args.json)
        else:
            _emit(promote.detect(inst), args.json)
    elif act == "mint":
        matcher = json.loads(Path(args.matcher).read_text())
        _emit(mint.stage(inst, args.entry, matcher), args.json)
    elif act == "verify":
        _emit(verify.verify(inst, Path(args.staged)), args.json)
    elif act == "freeze":
        _emit(freeze.freeze(inst, args.staged, approve=args.approve), args.json)
    elif act == "retire":
        _emit(retire.retire_pass(inst, approve=args.approve, fixture=args.fixture), args.json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="reasoning-graph",
                                description="Declared, confidence-weighted reasoning graphs.")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, help_, parent=sub):
        sp = parent.add_parser(name, help=help_)
        sp.add_argument("--instance", required=name != "demo",
                        help="path to an instance.json descriptor")
        sp.add_argument("--json", action="store_true", help="emit one JSON object")
        return sp

    # schema
    sp = add("schema", "validate a GraphSchema declaration")
    sp.add_argument("action", choices=["validate"])
    sp.set_defaults(fn=_cmd_schema_validate)

    # migrate
    sp = add("migrate", "run m001_edge_confidence (additive, idempotent)")
    sp.add_argument("--dry-run", action="store_true")
    sp.add_argument("--no-backup", action="store_true")
    sp.set_defaults(fn=_cmd_migrate)

    # resolve
    sp = add("resolve", "resolve a path (--start/--end) or a typed query (--text)")
    sp.add_argument("--start")
    sp.add_argument("--end")
    sp.add_argument("--text")
    sp.add_argument("--unweighted", action="store_true", help="fewest-hop instead of highest-confidence")
    sp.add_argument("--include-dormant", action="store_true")
    sp.add_argument("--hard", action="store_true", help="sub-floor results REFUSE instead of WEAK_ANSWER")
    sp.set_defaults(fn=_cmd_resolve)

    # analytics
    sp = add("analytics", "pagerank | cycles")
    sp.add_argument("action", choices=["pagerank", "cycles"])
    sp.add_argument("--top", type=int, default=20)
    sp.set_defaults(fn=_cmd_analytics)

    # loop
    sp = add("loop", "scan | promote | mint | verify | freeze | retire")
    sp.add_argument("action", choices=["scan", "promote", "mint", "verify", "freeze", "retire"])
    sp.add_argument("--entry", help="FCL entry id (promote/mint)")
    sp.add_argument("--matcher", help="matcher JSON path (mint): the machine-block fields")
    sp.add_argument("--staged", help="staged matcher path (verify/freeze)")
    sp.add_argument("--fixture", help="retire only: declared counter-state JSON applied to a "
                                      "scratch instance before the pass (test/gate use)")
    sp.add_argument("--approve", action="store_true",
                    help="required for freeze/retire writes on a real instance")
    sp.set_defaults(fn=_cmd_loop)

    # measure
    sp = add("measure", "frontier-rate | ab-build-tasks | ab-variants | ab-run | ab-judge | ab-report")
    sp.add_argument("action", choices=["frontier-rate", "ab-build-tasks", "ab-variants",
                                       "ab-run", "ab-judge", "ab-report"])
    sp.add_argument("--out", help="output directory (ab-*)")
    sp.add_argument("--tasks", help="frozen ab-tasks.json path")
    sp.add_argument("--model", help="model id for ab-run")
    sp.add_argument("--arm", choices=["A", "B", "both"], default="both")
    sp.add_argument("--k", type=int, default=2, help="variants per task (ab-variants)")
    sp.set_defaults(fn=lambda a: _not_implemented(a, "Phase 5/6 (measure/*)"))

    # demo
    sp = add("demo", "deterministic demo over the tiny fixture; ends 'Verify your build: ok'")
    sp.set_defaults(fn=lambda a: _not_implemented(a, "Phase 7 (demo.py)"))

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    args._cmdpath = args.cmd + (f" {getattr(args, 'action', '')}".rstrip())
    try:
        return args.fn(args)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        _emit({"error": type(exc).__name__, "detail": str(exc)}, getattr(args, "json", False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
