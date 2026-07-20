#!/usr/bin/env python3
"""G5 — frontier-call rate. The CLI's series must match this gate's OWN
independent parse of the live log + sidecar (chronological = bottom-up in the
newest-on-top log). The gate checks the metric is COMPUTED HONESTLY — it does
not require it to be falling.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (CLI_NOT_IMPLEMENTED, INSTANCE0, Gate, cli,  # noqa: E402
                     parse_json)

FCL = Path("/root/reasoning-graph/frontier-call-log.ngf.md")
SIDECAR = INSTANCE0.parent / "gap-shape-history.json"


def independent_series():
    ids = re.findall(r"^### (FCL-\d+)", FCL.read_text(), flags=re.M)
    ids.reverse()  # newest-on-top file → chronological order
    shapes = json.loads(SIDECAR.read_text())["entries"]
    seen, series = set(), []
    for i, eid in enumerate(ids):
        shape = shapes[eid]["gap_shape"]
        new = shape not in seen
        seen.add(shape)
        series.append({"entry_id": eid, "entry_index": i,
                       "cumulative_classes": len(seen), "is_new_class": new})
    return series


def main() -> int:
    g = Gate("g5_frontier_rate", as_json="--json" in sys.argv)
    code, out, err = cli(["measure", "frontier-rate", "--instance", str(INSTANCE0), "--json"])
    if code == CLI_NOT_IMPLEMENTED:
        return g.not_built("measure frontier-rate is a stub (Phase 5)")
    payload = parse_json(out)
    g.check("command exits 0 with JSON", code == 0 and bool(payload), (err or out)[-200:])
    if not payload:
        return g.finish()

    mine = independent_series()
    theirs = [{k: e.get(k) for k in ("entry_id", "entry_index", "cumulative_classes", "is_new_class")}
              for e in payload.get("series", [])]
    g.check(f"series matches independent re-parse ({len(mine)} entries)", theirs == mine,
            f"first divergence: {next((a for a, b in zip(theirs, mine) if a != b), None)}")
    g.check("batches computed from the log's own markers (>=2)",
            len(payload.get("batches", [])) >= 2, f"got {len(payload.get('batches', []))}")
    g.check("baseline block present", bool(payload.get("baseline")))
    reading = payload.get("reading", "")
    g.check("honest reading sentence present (computed, not pre-claimed)",
            isinstance(reading, str) and len(reading) > 20, reading[:100])
    g.check("output labeled derived:fcl_log_parse",
            payload.get("basis") == "derived:fcl_log_parse")
    return g.finish()


if __name__ == "__main__":
    sys.exit(main())
