#!/usr/bin/env python3
"""Build the tiny fixture DB — deterministic, stdlib-only, runnable today.

The tiny corpus is a WEAVING domain (looms/spindles/dye-baths) with NON-DEFAULT
table and column names for every profile field. If any core module works on
instance 0 but breaks here, it hardcoded something (gate G1's proof).

Planted content the gates assert against:
  clean 2-hop chain     loom_1 -feeds(1.0)-> spindle_a -tunes(0.95)-> dye_bath_2
                        → ANSWER, path_product_score exactly 0.95
  below-floor chain     loom_1 -weak_link(0.20)-> pattern_card_1
                        → WEAK_ANSWER (floor 0.30)
  benign reciprocal     spindle_a <-rivals-> spindle_b (cycle, NOT a contradiction)
  contradiction cycle   guild_rule_x -contradicts-> guild_rule_y
                        -governed_by-> loom_2 -tunes-> ... any path crossing it
                        → REFUSE(contradiction)
  no-support target     dye_bath_3 is an island → REFUSE(no_frozen_support)

Usage:
  python3 build_tiny.py <out_dir> [--bare]
    --bare: write NULL trust + no basis (the unmigrated variant, for m001 tests)
Writes <out_dir>/tiny.db and prints one line: "tiny.db built: 10 strands, 9 ties".
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

STRANDS = [
    # (strand_id, strand_kind, label, blurb)
    ("loom_1", "loom", "Great Loom", "primary warp-weighted loom"),
    ("loom_2", "loom", "Small Loom", "band loom for trims"),
    ("spindle_a", "spindle", "Drop Spindle A", "fast whorl"),
    ("spindle_b", "spindle", "Drop Spindle B", "slow whorl"),
    ("dye_bath_2", "dye_bath", "Madder Bath", "red dye bath"),
    ("dye_bath_3", "dye_bath", "Woad Bath", "isolated blue bath — no ties at all"),
    ("pattern_card_1", "pattern_card", "Diamond Twill Card", "weak provenance"),
    ("guild_rule_x", "guild_rule", "Rule of Even Tension", "declared guild rule"),
    ("guild_rule_y", "guild_rule", "Rule of Loose Weft", "conflicts with even tension"),
    ("pattern_card_2", "pattern_card", "Herringbone Card", "reached only through the contradiction"),
]

TIES = [
    # (tie_from, tie_to, tie_kind, trust, basis, chain_tag)
    ("loom_1", "spindle_a", "feeds", 1.0, "declared:structural_extraction", None),
    ("spindle_a", "dye_bath_2", "tunes", 0.95, "declared:verbatim_extraction", None),
    ("loom_1", "pattern_card_1", "weak_link", 0.20, "declared:initial_guess", None),
    ("spindle_a", "spindle_b", "rivals", 0.90, "declared:inherited_curation_default", None),
    ("spindle_b", "spindle_a", "rivals", 0.90, "declared:inherited_curation_default", None),
    ("guild_rule_x", "guild_rule_y", "contradicts", 0.85, "declared:initial_guess", None),
    ("guild_rule_y", "pattern_card_2", "governed_by", 1.0, "declared:structural_extraction", None),
    ("loom_2", "guild_rule_x", "governed_by", 1.0, "declared:structural_extraction", None),
    ("spindle_b", "loom_2", "feeds", 0.80, "declared:inherited_curation_default", None),
]


def build(out_dir: Path, bare: bool = False) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    db = out_dir / "tiny.db"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE strands (
            strand_id   TEXT PRIMARY KEY,
            strand_kind TEXT NOT NULL,
            label       TEXT,
            blurb       TEXT,
            extra       TEXT
        );
        CREATE TABLE ties (
            tie_from   TEXT NOT NULL,
            tie_to     TEXT NOT NULL,
            tie_kind   TEXT NOT NULL,
            trust      REAL,
            extra_json TEXT,
            chain_tag  TEXT
        );
    """)
    con.executemany(
        "INSERT INTO strands VALUES (?,?,?,?,?)",
        [(sid, kind, label, blurb, "{}") for sid, kind, label, blurb in STRANDS])
    rows = []
    for f, t, k, trust, basis, chain in TIES:
        if bare:
            rows.append((f, t, k, None, "{}", chain))
        else:
            rows.append((f, t, k, trust, json.dumps({"confidence_basis": basis}), chain))
    con.executemany("INSERT INTO ties VALUES (?,?,?,?,?,?)", rows)
    con.commit()
    con.close()
    print(f"tiny.db built: {len(STRANDS)} strands, {len(TIES)} ties"
          + (" (bare — NULL trust, for m001 tests)" if bare else ""))
    return db


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: build_tiny.py <out_dir> [--bare]")
    build(Path(sys.argv[1]), bare="--bare" in sys.argv[2:])
