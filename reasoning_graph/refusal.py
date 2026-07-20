"""The refusal boundary — the framework's first-class differentiator.

A reasoning graph that answers everything is lying about something. This module
decides Answer.status and, on REFUSE, drafts the FCL stub that turns the miss
into loop input. Unminted edges are dropped, never inferred.

Contract, frozen by this docstring + gate G3:

REFUSAL_REASONS = (
  "no_frozen_support",        # no path/result exists in the frozen graph
  "contradiction",            # contradiction-class edges are NON-TRAVERSABLE for
                              # answer paths: an assertion of incompatibility is
                              # not a reasoning step. REFUSE when every route to
                              # the target crosses an edge whose kind declares
                              # cycle_class='contradiction' (detail lists the
                              # contradicting pair). Benign reciprocal cycles
                              # NEVER refuse (visited-set discipline, not edges)
  "below_floor",              # only when the caller demands hard answers
                              # (resolve(..., hard=True)); default sub-floor
                              # behavior is WEAK_ANSWER, not REFUSE
  "unminted_edge_required",   # resolution would require an edge no rule ever
                              # declared/minted — the classic frontier call
  "missing_confidence",       # store raised MissingConfidence (an unweighted
                              # edge post-migration = data corruption; refuse loudly)
)

draft_fcl_stub(instance, query, reason, detail) -> str
  Returns a ready-to-append frontier-call-log entry in the FCL §1 schema
  (### <next-id> — <one-line> [LOGGED] + query/category/gap/root_cause/
  reasoning_conclusion/verified_by/pattern + gap_shape: <UNDECLARED — human fills>).
  It NEVER writes the log itself — appending is the caller's explicit act.

Refusal is a first-class result, not an error: CLI exits 0 with status=REFUSE.
"""
from __future__ import annotations

import re

REFUSAL_REASONS = (
    "no_frozen_support",
    "contradiction",
    "below_floor",
    "unminted_edge_required",
    "missing_confidence",
)

_ID_RE = re.compile(r"^###\s+([A-Za-z]+-\d+)\b")


def _next_id(instance) -> str:
    """Next id in the log's own prefix-NNN sequence, or a neutral placeholder if
    the log is absent/empty. Never invents a scheme the log doesn't already use."""
    fcl = getattr(instance, "fcl_path", None)
    if not fcl or not fcl.exists():
        return "<NEXT>"
    prefix, hi = None, 0
    for line in fcl.read_text().splitlines():
        m = _ID_RE.match(line)
        if m:
            pfx, num = m.group(1).rsplit("-", 1)
            prefix = prefix or pfx
            if pfx == prefix:
                hi = max(hi, int(num))
    return f"{prefix}-{hi + 1:03d}" if prefix else "<NEXT>"


def draft_fcl_stub(instance, query: str, reason: str, detail: str) -> str:
    """A ready-to-append FCL entry (LOGGED). gap_shape is left for a human —
    lock #20 forbids NLP-inferring it; this drafts the transcription only."""
    eid = _next_id(instance)
    return "\n".join([
        f"### {eid} — refused ({reason}): {query}   [LOGGED]",
        f"- query: {query}",
        "- category: (human fills — the graph area this touches)",
        f"- gap: {detail}",
        f"- root_cause: resolver refused with reason={reason} (unminted/unsupported edge)",
        "- reasoning_conclusion: (human fills — what a frontier call derived to bridge this)",
        "- verified_by: (filled at PROMOTED->MINTED, when a validation formula fires)",
        "- pattern: (human fills — the generalizable lesson -> candidate rule)",
        "- gap_shape: <UNDECLARED — human fills; never NLP-inferred (lock #20)>",
    ]) + "\n"
