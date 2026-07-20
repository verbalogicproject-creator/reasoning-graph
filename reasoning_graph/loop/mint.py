"""Mint — stage a matcher file for a PROMOTED/promotable class. Contract (gate G4):

stage(instance, entry_id, matcher: dict) -> {"staged_path", "mint_id"}
  Writes <staged_dir>/<mint_id>-STAGED.md in matcher-v2 format: the proven
  matcher-v1 human shape PLUS one fenced ```yaml machine block (JSON body — valid
  YAML, stdlib-parseable, no pyyaml dep) carrying mint_id / provenance /
  confidence / signature_sql / confirm / fix. Human text and machine block agree
  (verify.py cross-checks). Staging NEVER writes the DB.
"""
from __future__ import annotations

import json
import re

_FENCE = re.compile(r"```yaml\s*\n(.*?)\n```", re.S)


def parse_machine_block(staged_path) -> dict:
    text = staged_path.read_text() if hasattr(staged_path, "read_text") else open(staged_path).read()
    m = _FENCE.search(text)
    if not m:
        raise ValueError(f"no ```yaml machine block in {staged_path}")
    return json.loads(m.group(1))


def _human_sections(m: dict) -> str:
    confirm_lines = "\n".join(f"  {i+1}. {c.get('kind')}: {c.get('sql') or c.get('_why','')}"
                              for i, c in enumerate(m.get("confirm", [])))
    fix = m.get("fix", {})
    return "\n".join([
        f"## {m['mint_id']}: staged matcher (P4 candidate)",
        "",
        f"**Rule ID**: {m['mint_id']}",
        "**Category**: Mint (P3, staged — awaiting verify+freeze at P4/P5)",
        f"**Confidence**: {m['confidence']} — declared by the matcher, dual-grounded",
        f"**Source**: frontier-call-log entries {', '.join(m.get('provenance', []))}",
        f"**Statement**: {m.get('statement','')}",
        f"**Signature** (cheap triage): `{m.get('signature_sql','')}`",
        "**Confirm** (anti-false-positive — ALL must hold):",
        confirm_lines,
        f"**Fix**: mint a `{fix.get('edge_kind')}` edge per `{fix.get('pairs_sql','')}`",
        "**Validation Formula**: confirmed candidates >= 1 AND provenance fired",
        "**Related Rules**: (declared per instance)",
        f"**Provenance**: {', '.join(m.get('provenance', []))}",
    ]) + "\n"


def stage(instance, entry_id: str, matcher: dict):
    from . import promote
    d = promote.detect(instance)
    if entry_id not in d["promotable"] and entry_id not in d["recurring"]:
        raise ValueError(f"{entry_id} is neither promotable nor recurring — nothing to mint")
    mint_id = matcher["mint_id"]
    staged_dir = instance.staged_dir or (instance.fcl_path.parent / "staged")
    staged_dir.mkdir(parents=True, exist_ok=True)
    path = staged_dir / f"{mint_id}-STAGED.md"
    machine = {k: matcher[k] for k in matcher if not k.startswith("_")}
    body = (_human_sections(matcher) + "\n---\n\n"
            "<!-- machine block (JSON body inside a yaml fence — stdlib-parseable) -->\n"
            "```yaml\n" + json.dumps(machine, indent=2) + "\n```\n")
    path.write_text(body)
    return {"staged_path": str(path), "mint_id": mint_id}
