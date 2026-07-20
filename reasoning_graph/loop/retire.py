"""Retire — outcome-driven demotion. The SkillOps gap (arXiv:2605.13716), closed:
unmanaged rule libraries degrade below their no-rule baseline at scale; this
module demotes — it NEVER deletes (house append-only/supersede discipline).

OPUS-FILLS (Phase 4). Contract (gate G4):

record_outcome(instance, mint_id, outcome: "used"|"confirmed"|"contradicted") -> None
  Increments the minted rule's counters (freeze.py initialized them).

retire_pass(instance, approve: bool = False, fixture: str | None = None) -> dict
  fixture (CLI --fixture; test/gate use ONLY): path to a declared counter-state
  JSON (tests/fixtures/retire-fixture.json shape). Loads those minted-rule
  counter states into the instance's rule metadata BEFORE the pass — legal only
  on a self_approve instance; refuse otherwise (real counters are never faked).
  Applies instance.schema.retirement:
    demote when times_used >= min_uses AND
                times_contradicted / times_used >= contradiction_ratio
    over active_cap: demote lowest utility first
                (utility = times_confirmed - times_contradicted, declared formula)
  Demotion = rule metadata status: "active" → "dormant" + retired_reason +
  retired_at + the counter evidence, recorded in evolution_log. Edges minted by
  a dormant rule stay in the DB but are EXCLUDED by resolve() unless
  include_dormant=True. Counters are never reset; a dormant rule can be
  re-activated by a human (recorded), never automatically.
  Return: {"demoted": [{mint_id, reason, evidence}], "active": int, "dormant": int}
  Gate G4 proves this on the retirement fixture (a rule with declared counters
  that genuinely earns demotion), never on live instance-0 data.
"""
from __future__ import annotations


def record_outcome(instance, mint_id: str, outcome: str) -> None:
    raise NotImplementedError("OPUS-FILLS: Phase 4 — see module docstring + SoT")


def retire_pass(instance, approve: bool = False, fixture: str | None = None) -> dict:
    raise NotImplementedError("OPUS-FILLS: Phase 4 — see module docstring + SoT")
