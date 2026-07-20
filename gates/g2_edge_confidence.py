#!/usr/bin/env python3
"""G2 — edge confidence. Verifies m001's result on the LIVE instance-0 DB cell
by cell against the SoT derivation table (this gate carries its own copy — it
does not trust the package's declaration), then re-runs G0 to prove the
migration broke nothing.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (CLI_NOT_IMPLEMENTED, INSTANCE0, INSTANCE0_DB, GATES_DIR,  # noqa: E402
                     Gate, basis_ok, cli, parse_json, run)

# The SoT edge-confidence derivation table — the gate's own copy.
STRUCTURAL = {"tool_has_use_case", "tool_has_limitation", "tool_has_combination",
              "tool_has_example", "tool_has_prerequisite", "tool_has_configuration",
              "workflow_includes_tool", "has_workaround", "limitation_needs_workaround",
              "limitation_has_workaround", "combines_with"}
VERBATIM = {"extracted_from", "same_as", "tool_enables_capability",
            "tool_enhances_technique", "tool_primary_for_capability",
            "tool_supports_capability"}
INHERITED = {"tool_requires_tool", "tool_similar_to", "tool_complements",
             "tool_alternative_to", "tool_conflicts_with"}
INHERITED_DEFAULT = 0.90   # must match the approval artifact — checked in main()
MINT_001_CONFIDENCE = 0.85     # declared in TOOL-COMBO-INFERENCE-MINTED.md
CORPUS_MIN = 0.70
KNOWN_CHAIN = [("dep_003_tool_execution_requires_error_handling", "anti_001_infinite_tool_loops"),
               ("anti_001_infinite_tool_loops", "constr_002_max_iterations_safety")]


def main() -> int:
    g = Gate("g2_edge_confidence", as_json="--json" in sys.argv)

    # Approval artifact FIRST (council 2026-07-20): the 0.90 backfill is Eyal's
    # declaration, not the build session's — Phase 2 is BLOCKED without it,
    # mirroring the loop-freeze --approve pattern.
    approval = GATES_DIR / "eyal-approvals" / "edge-confidence-0.90.json"
    if not approval.is_file():
        return g.not_built(f"blocked on approval artifact: {approval} — the inherited-"
                           "curation default is a human declaration (SoT lock #21)")
    decl = json.loads(approval.read_text())
    if not g.check("approval artifact matches the gate's constant",
                   decl.get("value") == INHERITED_DEFAULT and decl.get("approved_by"),
                   f"artifact value={decl.get('value')} gate={INHERITED_DEFAULT}"):
        return g.finish()

    con = sqlite3.connect(f"file:{INSTANCE0_DB}?mode=ro", uri=True)
    cols = {r[1] for r in con.execute("PRAGMA table_info(edges)")}
    if "confidence" not in cols:
        code, out, err = cli(["migrate", "--instance", str(INSTANCE0), "--dry-run", "--json"])
        con.close()
        return g.not_built("confidence column absent; migrate "
                           + ("is a stub" if code == CLI_NOT_IMPLEMENTED else f"exists but not applied (exit {code})"))

    q = lambda sql, *p: con.execute(sql, p).fetchall()  # noqa: E731

    # 1. Coverage + range.
    nulls = q("SELECT COUNT(*) FROM edges WHERE confidence IS NULL")[0][0]
    bad = q("SELECT COUNT(*) FROM edges WHERE confidence <= 0 OR confidence > 1")[0][0]
    total = q("SELECT COUNT(*) FROM edges")[0][0]
    g.check("zero NULL confidence", nulls == 0, f"nulls={nulls}/{total}")
    g.check("all confidence in (0,1]", bad == 0, f"out-of-range={bad}")

    # 2. Basis labels: present + closed vocabulary.
    missing_basis, bad_basis = 0, []
    for (props,) in q("SELECT properties FROM edges"):
        try:
            basis = json.loads(props or "{}").get("confidence_basis")
        except json.JSONDecodeError:
            basis = None
        if not basis:
            missing_basis += 1
        elif not basis_ok(basis):
            bad_basis.append(basis)
    g.check("every edge carries confidence_basis", missing_basis == 0, f"missing={missing_basis}")
    g.check("every basis in closed vocabulary", not bad_basis, "; ".join(sorted(set(bad_basis))[:5]))

    # 3. Derivation table, cell by cell.
    def kinds_check(kinds, expect_conf, expect_basis, chain_null_only=False):
        ph = ",".join("?" * len(kinds))
        extra = " AND synthesis_chain IS NULL" if chain_null_only else ""
        rows = q(f"SELECT edge_type, confidence, properties FROM edges WHERE edge_type IN ({ph}){extra}", *kinds)
        wrong = [f"{k}={c}" for k, c, p in rows
                 if abs((c or 0) - expect_conf) > 1e-9
                 or json.loads(p or "{}").get("confidence_basis", "") != expect_basis]
        return rows, wrong

    rows, wrong = kinds_check(STRUCTURAL, 1.0, "declared:structural_extraction")
    g.check(f"structural kinds = 1.0 ({len(rows)} edges)", not wrong, "; ".join(wrong[:4]))
    rows, wrong = kinds_check(VERBATIM, 1.0, "declared:verbatim_extraction")
    g.check(f"verbatim-extraction kinds = 1.0 ({len(rows)} edges)", not wrong, "; ".join(wrong[:4]))
    rows, wrong = kinds_check(INHERITED, INHERITED_DEFAULT,
                              "declared:inherited_curation_default", chain_null_only=True)
    g.check(f"inherited kinds (no chain) = {INHERITED_DEFAULT} ({len(rows)} edges)",
            not wrong, "; ".join(wrong[:4]))

    minted = q("SELECT confidence, properties FROM edges WHERE synthesis_chain LIKE 'mint_001%'")
    wrong = [str(c) for c, p in minted
             if abs(c - MINT_001_CONFIDENCE) > 1e-9
             or not json.loads(p or "{}").get("confidence_basis", "").startswith("declared:matcher:")]
    g.check(f"mint_001 edges = {MINT_001_CONFIDENCE}, matcher basis ({len(minted)} edges)",
            len(minted) == 11 and not wrong, "; ".join(wrong[:4]))

    # rule_related_to: edge confidence == source rule's declared confidence,
    # else corpus_min fallback — verified by JOIN, not by trusting the report.
    rr = q("""SELECT e.source_node_id, e.confidence, e.properties,
                     json_extract(n.metadata, '$.confidence')
              FROM edges e JOIN nodes n ON n.node_id = e.source_node_id
              WHERE e.edge_type = 'rule_related_to'""")
    wrong, fallback_count = [], 0
    for src, conf, props, src_conf in rr:
        basis = json.loads(props or "{}").get("confidence_basis", "")
        if src_conf is not None:
            if abs(conf - float(src_conf)) > 1e-9 or basis != "derived:source_rule_confidence":
                wrong.append(src)
        else:
            fallback_count += 1
            if abs(conf - CORPUS_MIN) > 1e-9 or not basis.startswith("derived:corpus_min("):
                wrong.append(src)
    g.check(f"rule_related_to derived from source rules ({len(rr)} edges, {fallback_count} fallback)",
            not wrong, "; ".join(wrong[:4]))

    # 4. Independent product recomputation vs resolver (SKIP if Phase 3 pending).
    product = 1.0
    ok_chain = True
    for s, t in KNOWN_CHAIN:
        row = q("SELECT confidence FROM edges WHERE source_node_id=? AND target_node_id=? "
                "AND edge_type='rule_related_to' LIMIT 1", s, t)
        if not row:
            ok_chain = False
            break
        product *= row[0][0]
    g.check("known 2-hop chain has confidences", ok_chain, "chain edges missing")
    code, out, err = cli(["resolve", "--instance", str(INSTANCE0),
                          "--start", KNOWN_CHAIN[0][0], "--end", KNOWN_CHAIN[-1][1], "--json"])
    if code == CLI_NOT_IMPLEMENTED:
        g.skip("resolver product cross-check", "Phase 3 pending — re-verified by G3")
    else:
        payload = parse_json(out)
        rc = payload.get("confidence") if payload else None
        g.check("resolver path confidence == independent product (1e-9)",
                rc is not None and abs(rc - product) < 1e-9, f"resolver={rc} sql={product}")
    con.close()

    # 5. Full G0 re-run — the migration must not have broken the substrate.
    code, out, err = run([sys.executable, str(GATES_DIR / "g0_substrate_intact.py")])
    g.check("G0 re-run PASS post-migration", code == 0, out[-300:] if code else "")

    return g.finish()


if __name__ == "__main__":
    sys.exit(main())
