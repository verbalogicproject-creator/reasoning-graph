# Reasoning-Graph → SAG: The Confidence-Lifecycle Contribution

```yaml
document_id: nlke.rg.contribution-to-sag.2026-07-22
status: analysis-draft; contribution-hypothesis awaiting Eyal's gate
created: 2026-07-22
owner: Eyal Nof
author_role: "Claude infers/connects and presents for the gate; Eyal commands/approves"
canonical_root: /root/reasoning-graph
subject_framework: /root/projects/reasoning_graph        # reasoning-graph FRAMEWORK, gates G0–G8 all PASS
target_project: ~/projects/SAG-the-real-build            # SAG "The Real Build" (Termux host)
evidence_ladder: "Proposed → Derived → Implemented → Demonstrated → Independently validated"
one_line_thesis: >
  The reasoning-graph's biggest gift to SAG is not a graph. It is the confidence
  LIFECYCLE — a gate-proven engine in which confidence is earned honestly and
  revoked on drift — which is precisely SAG's own non-negotiable, "Confidence
  cannot create authority," made mechanical.
sources:
  - "~/projects/SAG-the-real-build/SAG-source-of-truth.md        # GCA-INV-001..014, §11 capability map, §13 tiers, §18 gaps, Appendix A claim register"
  - "~/projects/SAG-the-real-build/tech-that-should-integrate.md  # ten slots, §3 per-project verdicts, §5 the seven uncertainties, §7 non-negotiables"
  - "~/projects/SAG-the-real-build/the-Aider-approach-roadmap-2026-07-22.ngf.md  # v1 milestone, seven properties, three tiers"
  - "~/projects/SAG-the-real-build/planning-outputs-2026-07-22.md # claim register, tier definitions"
  - "/root/projects/reasoning_graph/ (SoT 2026-07-19 + gates run_all.py G0–G8)  # the framework this doc speaks for"
authority: "analysis + recommendation only — not a build order; the §7 open calls are Eyal's to resolve"
```

---

## 0. What this document is (and is not)

**Is:** a single, gated hypothesis — *which one thing in the reasoning-graph framework most helps SAG reach its goal*, argued in SAG's own vocabulary (its ten integration slots, its seven funding-uncertainties, its fourteen invariants, its non-negotiables).

**Is not:** a merge proposal, a build order, or a claim that reasoning-graph is SAG-ready. The two live in different domains — the reasoning-graph reasons over **reasoning chains**; SAG governs **runtime effects**. **The transfer proposed here is at the level of discipline and architecture, not a library drop-in.** Every claim below is labeled on the shared evidence ladder, and the honest headline status is: **Demonstrated inside the reasoning-graph's own domain; Derived as a SAG contribution** (a port is required before it is Implemented in SAG).

---

## 1. The one contribution, in one sentence

> **The reasoning-graph is the only working, gate-proven machine in the fleet for the principle SAG itself names as a non-negotiable — "Confidence cannot create authority" — and it enforces that principle as one two-stroke engine: _certify-don't-claim_ (nothing is ever labeled above its evidence) and _retire-on-drift_ (trust decays the moment observation contradicts it).**

Those two strokes are not two contributions. They are the same principle pointed in opposite directions: confidence **rising** only as far as evidence permits, and confidence **falling** when reality disagrees. Together they are a full confidence *lifecycle* — and a lifecycle is exactly what turns "confidence cannot create authority" from a slogan into a mechanism.

---

## 2. Why this is ONE thing, not two (the interlock)

SAG says the same sentence in three places, and means it as law:

- `SAG-source-of-truth.md` novelty discipline — *"an accepted request is not an observed effect… success requires a bounded receipt grounded in the runtime outcome"* (GCA-INV-006).
- `tech-that-should-integrate.md §7` non-negotiables — ***"Confidence cannot create authority."*** … *"Material drift removes trust faster than it creates hidden breakage."*
- Authorized-Reconstruction charter — *"Confidence is not permission. Observation is not authority."*

The reasoning-graph is the fleet's most rigorous embodiment of that law, and it embodies it in both directions at once:

| Stroke | What it enforces | In the reasoning-graph, concretely |
|---|---|---|
| **A — certify-don't-claim** | confidence never rises above its evidence | Refuses rather than emit an unsupported answer (`REFUSE(no_frozen_support)` + drafts the gap-stub). Nothing is labeled `measured:` unless it is a real token count. `path_product_score` is declared a **ranking, not a probability**. A claim cannot be labeled above its evidence without a gate refusing the build. |
| **B — retire-on-drift** | confidence falls when observation contradicts it | A frozen rule carries outcome counters (`times_used / confirmed / contradicted`); when its contradiction ratio crosses the policy line it is **demoted to dormant — never deleted, always with the evidence attached**. Trust is revocable. |

Remove either stroke and the principle collapses. Certify-without-retire is a reference book that rots (trust minted and never revoked — the exact failure SkillOps names, and the exact failure GCA-INV-014 legislates against). Retire-without-certify has nothing honest to revoke. **The contribution is the closed loop, and the loop is the principle.**

---

## 3. Where each stroke lands on YOUR map

Every row below is grounded in SAG's own documents. The right-hand column is the reasoning-graph asset that already exists and passes its gates.

### Stroke A — certify-don't-claim → the evidence-ladder / conformance instrument

| SAG anchor | SAG's own words | Reasoning-graph asset (Demonstrated in-domain) |
|---|---|---|
| **Slot 6** (Conformance / test harnesses) | *"Reproducible falsification suite, RAG eval, integrity audits"* | `gates/run_all.py` (G0–G8): **3-way tamper-evident** (MANIFEST sha256 + external anchor + git), gates **recompute the real value** instead of trusting a flag, and an **INFRA-FLAKE (exit 5)** verdict separates a phone/CI hiccup from a real regression |
| **§5 uncertainty #5** | *"The evidence ladder is written down; the automated instrument that produces `Demonstrated` vs `Independently validated` per claim is **not built**"* (nominates `rag_evaluator` as only the *closest analog*) | The **closed provenance-basis vocabulary** (`declared:*` / `derived:*`) is that per-claim instrument: it is the machine that refuses to let a claim wear a ladder rung its evidence can't carry |
| **The Tnufa credibility bar** | an *"Israeli-counsel-caliber"* reviewer who will note that KG Factory + Codex Aware are **architect-tested** | The A/B protocol's honesty: **Wilson + McNemar, no blended headline number, a corpus-private contamination control**, small-N reported as *directional-not-significant* — the posture that survives a hostile reviewer |
| **The crux move (rehearsal)** | Property **#7** — envelope compatibility across two independently-authored implementations — *"the only property that cannot be self-certified"* | **G7**: the same gate-kit was run against a **second, alien-domain corpus with zero core edits** and passed. This is the *methodological rehearsal* of "one kit certifies a second, differently-shaped instance" |

> **Honest bound on the rehearsal:** G7 proves *the same kit certifies a second, differently-shaped instance without touching the core* — it does **not** prove envelope-compatibility itself, which needs a genuinely independent author (Aider). G7 is the shape of SAG's crux move, not a substitute for it.

### Stroke B — retire-on-drift → the drift → trust-degradation loop

| SAG anchor | SAG's own words | Reasoning-graph asset (Demonstrated in-domain) |
|---|---|---|
| **Slot 9** (Telemetry, drift, cost) | *"Refuse-and-record… drift → trust degradation"* | `loop/retire.py` + `record_outcome()`: outcome-driven **demote-to-dormant**, bounded active cap, contradiction-ratio policy, evolution-log evidence trail |
| **§5 uncertainty #4** | *"Drift-to-trust-degradation… a monitoring loop that actually degrades a promoted adapter when observed traces diverge from the promoted spec. **Not implemented in any of the ~/ubuntu projects.**"* | This is the **only** §5 uncertainty with **no owner anywhere in the fleet** — and the reasoning-graph's retire loop is a working implementation of exactly that decay |
| **GCA-INV-014** | *"Current behavior outranks stale documentation… Documentation drift is recorded, not hidden."* | Demote-not-delete with the contradicting evidence preserved *is* "recorded, not hidden" |
| **§7 non-negotiable #9** | *"Material drift removes trust faster than it creates hidden breakage."* | Trust falls on the *ratio* of contradictions before the cap ever bites — drift removes trust first |

**Contribution status for both strokes:** *Derived as a SAG contribution* (Demonstrated only inside the reasoning-graph's own domain; a port is the work that would move it to Implemented-in-SAG).

---

## 4. Why this is the BIGGEST — the argument, honestly bounded

1. **On-path to the goal.** SAG's whole v1 is a single ladder move: **Demonstrated → Independently validated**. Stroke A is the machine that makes ladder moves *un-bluffable* — a referee that recomputes the truth and cannot be argued into a pass. That is the most load-bearing thing anyone can hand a project whose entire deliverable is one credibility upgrade.
2. **Fills the one empty slot.** Stroke B is, by your own audit, the single §5 uncertainty **no other project owns**. Maximum *marginal* contribution: nothing else can do it.
3. **Aligned, not in tension.** SAG deliberately forbids confidence and knowledge-graphs from becoming *authority*. This contribution is not a smuggled reasoning layer — **it is the enforcement of that very prohibition.** The reasoning-graph is the fleet's proof that a confidence-bearing graph can refuse to let its own confidence become truth.
4. **Bounded honestly.** It is a **pattern / design / gate-scaffold donor**, not a drop-in — and the reasoning-graph's own evidence is honest small-N. This document claims *architectural fit*, not production-readiness.

---

## 5. What this is NOT (killing the tempting overclaim)

- **NOT "wire reasoning-graph in as SAG's NLKE / knowledge / reasoning layer."** SAG makes NLKE an **optional, null-by-default sidecar** and *explicitly rejected* forcing a KG on adopters (batch-3 Q7: *"Rejected: null-graph adapter — forces the KG shape on non-KG adopters"*). The graph-as-reasoning-substrate thesis must **not** be pitched into SAG. The contribution is the *discipline*, which is corpus-agnostic and imposes no graph on anyone.
- **NOT a claim that reasoning-graph code runs SAG's conformance kit today.** Different domain (reasoning chains vs. runtime effects). What transfers is the *shape* of the harness and the *vocabulary* of the labels.
- **NOT independent validation of anything.** The reasoning-graph's proof is a small-N PoC. Importing it does not import a benchmark.

---

## 6. Concrete transfer surface (what actually moves, and how much work)

If Eyal decides this is a *code/scaffold* donor rather than a *design-only* donor, this is the honest itemization:

| Reasoning-graph piece | SAG target | Donor tag |
|---|---|---|
| `gates/run_all.py` 3-way integrity pattern (manifest + external anchor + git) | the conformance kit's **anti-tamper** property — a certified party cannot fake a pass | **Adapt** (pattern ports; the hashed targets are SAG's) |
| gate discipline: *recompute the real value, never trust a self-reported flag* | each of the seven checkable properties as a gate | **Adapt** |
| `INFRA-FLAKE` (exit 5) verdict | a certification run that flaked on transport vs. one that genuinely failed conformance | **Donor** (drop-in concept) |
| closed basis vocabulary + "nothing `measured:` unless truly measured" | the per-claim **ladder verdict labels** (Demonstrated vs Independently validated) | **Donor** (vocabulary) |
| `loop/retire.py`: outcome counters → contradiction-ratio → demote-to-dormant (evidence kept) | the **drift monitor** that degrades a promoted adapter when traces diverge from the promoted spec (§5 #4) | **Adapt** (the decay policy ports; the "observed trace" is SAG's receipt stream) |
| `resolver.py` / `refusal.py` decision tree (`ANSWER` / `WEAK_ANSWER` / `REFUSE`) | the receipt's `awaiting_consumer → success` gate — refuse to advance without observation | **Rebuild** on the pattern (closest *conceptual* twin to GCA-INV-006) |

---

## 7. Open calls for Eyal (surfaced, not sealed)

- **OC-1 — Re-rate `reasoning_graph`?** `tech-that-should-integrate.md §3.5` currently rates it **"DONOR (probably) — 56 files, 4.8K LOC, unclear README… do not depend on it now."** That rating reads like a cursory survey and predates/underweights the finished framework (gates G0–G8 all PASS, retire loop + tamper-evident harness built). A re-rating toward **INTEGRATE for slots 6 and 9** is defensible — but it is **your** ruling, not mine to make.
- **OC-2 — Donor type?** Is this a **code/scaffold** donor (port `gates/` + `retire.py` into the SAG conformance kit) or a **design/discipline** donor (reference architecture only)? This decides whether it is a Tnufa line-item or a background principle.
- **OC-3 — Sibling compiler.** The Authorized-Reconstruction product needs a *decomposed confidence model* (structural / behavioral / semantic / identity / effect / safety / freshness — its required output #7). The closed-basis vocabulary is a clean **design donor** there too. Fold in, or keep this doc runtime-only?
- **OC-4 — Corpus-agnostic guarantee.** If wired at all, does the contribution stay driven by one `GraphSchema` declaration so it **never forces the KG shape on a non-KG adopter** — honoring SAG's batch-3 Q7 rejection? (My recommendation: yes, non-negotiably.)

---

## 8. One-line summary

**The reasoning-graph's biggest contribution to SAG is not a graph — it is the confidence lifecycle: a gate-proven engine in which confidence is earned honestly (certify-don't-claim) and revoked on drift (retire-on-drift), which is exactly SAG's own "Confidence cannot create authority," made mechanical.** Stroke A lands on the v1 critical path (the conformance / evidence-ladder instrument); Stroke B fills the one slot no other project in the fleet owns (drift → trust degradation).

---

*Provenance: analysis authored 2026-07-22 against `~/projects/SAG-the-real-build/SAG-source-of-truth.md` (v1.0.1) and `tech-that-should-integrate.md`, speaking for the reasoning-graph framework at `/root/projects/reasoning_graph/` (Reasoning-Graph-source-of-truth-2026-07-19.ngf.md; gates G0–G8 verified PASS). Claim discipline follows SAG's ladder: this document is Derived, not Demonstrated — it argues architectural fit, and the port is the work that would test it.*
