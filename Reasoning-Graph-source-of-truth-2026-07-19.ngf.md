---
kind: ngf_source_of_truth
id: reasoning-graph-framework-sot-2026-07-19
name: "Reasoning-Graph framework — concept + implementation source of truth"
authored: "2026-07-19"
author: eyal_nof (declarations) + claude-fable-5 planning session (synthesis)
status: "locked-for-build — the Opus 4.8 build session implements against this; changes only via Eyal"
thesis: >
  Reasoning retrieved by traversal of a declared, confidence-weighted graph
  instead of re-derived in prose. Misses ("frontier calls") feed a mechanized
  mint→verify→freeze→retire loop; minted rules freeze back into the graph in
  the same format as extracted ones. Proof: an A/B token+accuracy comparison
  (traversal arm vs prose arm, matched protocol) plus a computed, falling
  frontier-call rate. This is rung-0 lowering applied to reasoning itself.
consumers: [opus-4.8-build-session, eyal]
public_interfaces: ["reasoning-graph CLI (every subcommand --json)", "GraphSchema declaration", "PrimitiveAdapter", "gates/run_all.py"]
sources:
  - "/root/reasoning-graph/reasoning-graph-context-datapacket-2026-07-12.ngf.md (v1.6 — §2 throughline, §4 declared calls, §5 field notes)"
  - "/root/reasoning-graph/implementation-plan-reasoning-graph-v2-2026-07-13.md (P0–P2 historical record)"
  - "/root/reasoning-graph/status-report-2026-07-14.ngf.md (the P0–P2 milestone evidence)"
  - "/root/reasoning-graph/frontier-call-log.ngf.md (11 entries, FCL-001..011)"
  - "/root/reasoning-graph/Distillation-workflow-formalization-2026-07-14.ngf.md (the loop recipe)"
  - "/root/reasoning-graph/synthesis-rules/minted/TOOL-COMBO-INFERENCE-MINTED.md (matcher-v1 exemplar)"
  - "lowering-ladder/PRIMITIVE-ARCHITECTURE-formalization.ngf.md + SKILL-LOWERING-PIPELINE-SoT.ngf.md (the WHY)"
  - "arXiv: 2509.21743 (RoT) · 2310.07064 (HtT) · 2605.16045 (RecMem) · 2605.13716 (SkillOps) · 2606.06240 (TOKI) · 2601.11956 (DoublyCal) · 2502.11371 (RAG-vs-GraphRAG) · 2505.23495 (KGQAGen) · 2604.15877 (Compression Spectrum) · 2310.01061 (RoG) · 2406.04271 (BoT) · 2409.07429 (AWM)"
edges:
  - "instantiates: the lowering ladder's rung 0 (reasoning axis)"
  - "adopts: Distillation-workflow-formalization (Phase A/B) as the loop's operating recipe"
  - "sibling-of: declared_core / frontmatter_rag / project_memory (the RAG codifications; same house recipe)"
  - "instance-0: /root/reasoning-graph (never edited except via migrate/freeze/retire + append-only logs)"
---

# Reasoning-Graph — source of truth (2026-07-19)

> **What this doc is.** The build contract for the Opus 4.8 implementation
> session (hard budget: 1M tokens). Everything below is either DECLARED (by
> Eyal, dated) or EVIDENCE-POINTED (a real file/DB probe you can re-run);
> nothing is aspirational. The executable gate harness — `gates/run_all.py`,
> hash-manifested, immutable to the build session — decides "done," not this
> doc and not the builder's narration. Detailed per-module contracts live in
> the skeleton's module docstrings; they are NORMATIVE and this doc does not
> duplicate them.

## ⭐ ORIGIN + DECISIONS LOCKED + BUILD PLAN

### The origin

The dot-3 migration: move reasoning from something a frontier model re-derives
in prose every call into a traversable, confidence-weighted graph it looks up.
Staged and proven in `/root/reasoning-graph` (2026-07-12 → 07-14): P0 tool
graph, P0.5 frozen-rule extraction, P1 nai read side, P2 typed query unit —
all live-verified; the P3–P5 loop specified and run 4 times as *manual
discipline*. This framework codifies that proven substrate the same way
declared_core/frontmatter_rag/project_memory codified RAG — and the build
session's job is precisely the part that has never existed as code:
**mechanize the loop, weight the edges, measure the proof.**

### Decisions LOCKED

| # | Dimension | Decision (date · grounds) |
|---|---|---|
| 1 | Relic reuse | Assess-reuse: live systems (nai, eco-system patterns); `python/` is a parts bin (2026-07-13) |
| 2 | Rule extraction scope | Lane A = the 17 rules with declared `Related Rules`; the other 92 route to the mint queue (2026-07-13) |
| 3 | Store | folded into #6 |
| 4 | Mint scope | tool→tool edges only for the initial pass (2026-07-13) |
| 5 | Read side | nai adopted as the read side (2026-07-13) |
| 6 | Store shape | fresh DB in the claude-code-tools-kg schema = `kgs/reasoning-graph.db` (2026-07-13) |
| 7 | P2 path | adapt `intent_query.py` → `query.py`, done, fixture 20/20 (2026-07-13/14) |
| 8 | Loop surface | local CLI/files against #6's store; live nlke MCP untouched, reference-only (2026-07-13) |
| 9 | Deliverable shape | SoT + executable gate harness + repo skeleton; gates decide done (2026-07-19) |
| 10 | Proof | A/B headline (tokens+accuracy, matched protocol) + frontier-call rate secondary (2026-07-19) |
| 11 | Generality | corpus-agnostic core from day one; claude-code-tools = instance 0; 2nd corpus = stretch gate (2026-07-19) |
| 12 | Framework home | `/root/projects/reasoning_graph`; instance 0 stays in `/root/reasoning-graph`, untouched (2026-07-19) |
| 13 | Retirement | FULL mechanism in PoC: outcome counters on every minted rule + demote-to-dormant (never delete) + bounded active cap; fixture-proven (2026-07-19 · SkillOps 2605.13716) |
| 14 | A/B scale | N=30 now + parametric variant generator (auto-scale harness); claim scope fixed: "PoC evidence on this corpus, not a generalizable benchmark" (2026-07-19 · KGQAGen 2505.23495) |
| 15 | Docs bar | final docs at the house bar (declared_core-level); NON-NEGOTIABLE — the abort ladder never trims docs (2026-07-19) |
| 16 | Edge-confidence storage | additive `confidence REAL` column + `confidence_basis` in properties JSON; derivation per §4's table (2026-07-19) |
| 17 | Confidence honesty | closed basis vocabulary, `declared:*`/`derived:*` only; NULL confidence = refusal-grade, never a silent 1.0; the ONLY `measured:` label in the system is A/B api-usage tokens (2026-07-19) |
| 18 | Path confidence | product of edge confidences (Dijkstra over −log w for best route), reported as `confidence_kind: path_product_score` — a ranking score, NOT a calibrated probability (2026-07-19 · DoublyCal 2601.11956) |
| 19 | Contradictions | typed: only `cycle_class='contradiction'` edge kinds refuse; contradiction edges are non-traversable for answer paths; cycles per se are NOT contradictions (2026-07-19 · TOKI 2606.06240 + FCL field notes) |
| 20 | Promotion gate | declared `gap_shape` recurrence ≥ 2, never NLP-inferred similarity; single-occurrence promotion only by explicit human approval, recorded (2026-07-19 · RecMem 2605.16045; FCL-001 precedent) |
| 21 | Inherited-edge default | 0.90 `declared:inherited_curation_default` — **CONFIRMED by Eyal 2026-07-20** during the Scientifix Council review; recorded in `gates/eyal-approvals/edge-confidence-0.90.json`, which G2 requires before Phase 2 may write anything (the council found the prior draft let the build session enact this by fiat) |
| 22 | No-confidence rules | rules lacking a declared confidence derive `derived:corpus_min(0.70)` — the observed corpus minimum (2026-07-19) |
| 23 | nai lift | vendor-adapt (VENDORED.json provenance); originals never edited; the vendored store KILLS the default-1.0 edge-weight behavior (2026-07-19) |
| 24 | query.py | frozen at instance level, reached via SubprocessAdapter; any edit fails G0's hash check (2026-07-19) |
| 25 | Council amendments | the 2026-07-20 Scientifix Council's full resolution set is ADOPTED and already applied to this repo: 3-way gate integrity (manifest + external anchor at instance-0 root + git-clean), CORE-LOCK git-anchored, Phase-2 approval artifact, A/B phone-hardening (spike-first · serialized · checkpointed · logged retries · ==30 unique), per-subset-only stats w/ Wilson+McNemar (no blended headline, G6-enforced), INFRA-FLAKE verdict + run_all --resume, path_class disclosure, record_outcome wired to arm-A minted edges, itemized 120K contingency (2026-07-20) |
| 26 | Lock #8 clarified | a local PostToolUse hook MAY auto-append resolver-drafted REFUSE stubs to the FCL log — the boundary is WHAT writes (local CLI/files, unchanged), not what triggers it; transcription only, `gap_shape` stays human-declared (lock #20 untouched); ships as Phase 8b additive with its own smoke test, manual path stays primary and G4-tested (Eyal, 2026-07-20) |

### The build plan (Opus phases; budgets = total session tokens, declared:planning_estimate)

| Ph | Objective | Gate | Budget | Status |
|---|---|---|---|---|
| 0 | Read this SoT end-to-end; `python3 gates/run_all.py --only g0` → green baseline | G0 | 30K | NOT-STARTED |
| 1 | `schema.py` is done — implement `store.py` (vendor-adapt nai KGManager; MissingConfidence; unknown-kind raises); tiny fixture round-trips | G1 | 90K | NOT-STARTED |
| 2 | `migrations.py` m001 + apply to instance 0 (backup first); vendored profile maps edge_weight→confidence | G2 | 70K | NOT-STARTED |
| 3 | `resolver.py` + `refusal.py` + `primitives.py`; CORE-LOCK written at G3 pass | G3 | 110K | NOT-STARTED |
| 4 | `loop/` (fcl, promote, mint, verify, freeze, retire) — history reproduction + fixture loop + retirement | G4 | 180K | NOT-STARTED |
| 5 | `measure/` — frontier_rate + ab_tasks (freeze!) + ab_variants | G5 | 130K | NOT-STARTED |
| 6 | Execute the A/B arms (external headless CLI), judge, report | G6 | 70K | NOT-STARTED |
| 7 | Tests to INVARIANTS 1:1, docs to the house bar, demo, CHANGELOG hardening pass (RG-n ids, git-backed) | G8 | 120K | NOT-STARTED |
| — | Contingency/debug buffer — G0 re-runs and gate-debug cycles charge here when they exceed a phase's budget (itemized per council 2026-07-20; was silent headroom) | — | 120K | — |
| 8 | STRETCH: lowering-ladder mini-corpus, declaration-only | G7 | 80K (reserve) | NOT-STARTED |
| 8b | STRETCH: FCL auto-append hook (lock #26) — PostToolUse transcription of REFUSE stubs, own smoke test | — | ~20K (reserve) | NOT-STARTED |

Accounting: 800K phases + 120K contingency + 80K stretch = the 1M ceiling; 8b
spends only what remains after 8. These are `declared:planning_estimate` with
NO grounding data — a ceiling with an abort plan, not a forecast; the
BUDGET-LOG's actual-vs-declared column is the dataset that grounds the next
estimate. Abort ladder (declared): drop Phase 8/8b → drop the LLM-judge
fallback → **never** trim docs/tests/gates. Re-run **G0 after every phase** —
the standing regression gate. **Phase 6 entry condition:** `ab-spike-ok.json`
exists (one headless call, usage metadata parsed) — if the spike fails, STOP:
the headline proof is unbuildable as designed on this host. An INFRA-FLAKE
gate verdict (exit 5 — timeout/signal-kill) is re-run, never debugged as code.

**Smallest useful slice: G0–G6 green** — mechanized loop + weighted edges +
both proofs computed. Docs bar (G8) completes the deliverable; G7 is severable.

## 0 · P0–P2 EXIST — DO NOT REBUILD

P0 (tool graph), P0.5 Lane A + partial Lane B (frozen rules/capabilities), P1
(nai read side), P2 (`query.py`, fixture 20/20 + 3/3 canonical) are **done and
live-verified**. Evidence: `kgs/reasoning-graph.db` (639 nodes / 856 edges at
baseline), `status-report-2026-07-14.ngf.md`, and gate G0, which re-proves all
of it in one command and re-runs after every phase. A session that "improves"
any of this and breaks G0 has failed, whatever else it built.

Frozen files (hash-manifested in `gates/FROZEN-MANIFEST.sha256`; never edit):
`/root/reasoning-graph/query.py` · `p2_fixture_runner.py` ·
`p2-acceptance-fixture.json` · `systems/nai/**/*.py` · the 8 top-level
`synthesis-rules/*.md`. Mutable by contract ONLY via this package:
`kgs/reasoning-graph.db` (migrate/freeze/retire), `frontier-call-log.ngf.md`
(append + status-tag advance), `synthesis-rules/staged|minted/` (stage/freeze).

## 1 · Thesis (inherited verbatim in spirit — do not re-derive)

Graph = frozen reasoning: pay inference once to declare an edge, retrieve it
forever by traversal; multi-step reasoning = path composition. A reasoning
step is an edge — TRAVERSAL is Python's, EDGE-CREATION is the frontier's
residue. The extract-vs-decide law routes what freezes (extraction) vs what
must be minted (judgment). The migration metric is the falling frontier-call
rate. In lowering-ladder vocabulary: rungs 3→0 (prose→code→declared→
precomputed), this graph is rung-0 applied to reasoning; the pipeline is
ingest→classify→lower→VERIFY→measure, VERIFY refuses what it can't gate, and
the measure report is the deliverable. The residue — irreducible judgment —
is SUPPOSED to stay prose; over-declaring it is brittleness (that is why
FCL-008 was correctly never fixed: the corpus lacked the content, and minting
it would have been fabrication).

## 2 · Framework/instance boundary

Core (`reasoning_graph/`) carries ZERO instance vocabulary — node/edge kinds,
table/column names, corpus ids arrive only via the `GraphSchema` declaration
(G1 greps core against the live DB's own kind/id list; the tiny weaving
fixture with non-default names for every profile field is the proof-by-
construction). Instance 0 = `instances/claude_code_tools/` — `instance.json`
(absolute paths + SubprocessAdapter to the frozen `query.py`),
`graphschema.py` (13 node kinds, 24 edge kinds incl. the 0-row `contradicts`
channel), `gap-shape-history.json` (the 11 historical FCL entries' declared
shapes/occurrences/dispositions). A second corpus is a new instance directory
and NOTHING else (G7 proves zero core edits via the git-anchored CORE-LOCK —
committed at G3's first PASS, so it can't be silently regenerated).

## 3 · GraphSchema (implemented this session — the one declaration object)

`reasoning_graph/schema.py` is DONE and tested: node kinds; edge kinds each
carrying a `ConfidenceRule` (closed-vocabulary basis + declared value or
derivation note) + `cycle_class`; profile (table/column mapping); floor 0.30;
promotion_threshold 2; `RetirementPolicy` (active_cap / min_uses /
contradiction_ratio / declared utility formula). Unknown kind → raise, never
coerce. Do not widen this module.

## 4 · Edge confidence (the load-bearing retrofit)

Today NO edge carries numeric confidence (verified: the `edges` table has no
such column; nai defaults weights to 1.0 — every historical "confidence 1.0"
path was a product of defaults). m001 (contract: `migrations.py` docstring)
adds the column additively and backfills per this DECLARED table:

| Edge class (instance 0) | Confidence | Basis |
|---|---|---|
| structural P0 kinds (`tool_has_*`, `workflow_includes_tool`, `has_workaround`, `limitation_*`, `combines_with`) | 1.0 | `declared:structural_extraction` |
| `rule_related_to` | source rule node's declared confidence | `derived:source_rule_confidence` |
| — source rule declares none (TASK-CLASSIFIER's 12) | 0.70 | `derived:corpus_min(0.70)` |
| `extracted_from`, `same_as`, `tool_enables_capability`, `tool_enhances_technique`, `tool_primary_for_capability`, `tool_supports_capability` | 1.0 | `declared:verbatim_extraction` |
| any edge with non-NULL `synthesis_chain` (precedence over kind default) | its matcher's declared value (mint_001 = 0.85) | `declared:matcher:<mint_id>` |
| inherited DB-native reasoning kinds (`tool_requires_tool`, `tool_similar_to`, `tool_complements`, `tool_alternative_to`, `tool_conflicts_with`), chain NULL | 0.90 (**flagged, §13**) | `declared:inherited_curation_default` |

G2 verifies every cell by independent SQL (it carries its own copy of this
table), requires `null_remaining == 0`, checks the closed vocabulary, requires
the **approval artifact** (`gates/eyal-approvals/edge-confidence-0.90.json` —
lock #21's confirmation; absent → Phase 2 is BLOCKED, not improvised), and
re-runs G0. The vendored store treats missing confidence as refusal-grade —
the framework never silently pretends certainty. nai's originals keep their
old behavior and stay untouched.

**Disclosed asymmetry (council 2026-07-20):** the product composes two
different kinds of number — extraction-fidelity 1.0s and inferential-trust
<1.0s — so an all-structural walk always outranks any inferential path. The
PoC ships this single scalar deliberately (simplicity), but every Answer
carries `path_class: reasoning | structural_only` so a fact-walk is never
presented as reasoning composition (G3 tests both labels); splitting the two
semantics into orthogonal fields is on the ROADMAP.

## 5 · Resolver + the refusal boundary (the differentiator)

`resolve()` returns the Answer JSON (normative shape in `resolver.py`):
status ANSWER / WEAK_ANSWER (found but sub-floor — honest, never hidden) /
REFUSE with reasons `no_frozen_support · contradiction · below_floor ·
unminted_edge_required · missing_confidence`. Contradiction-class edges are
non-traversable for answer paths; benign reciprocal cycles never refuse (the
instance-0 `tool_similar_to` cycles are data, not defects). Every REFUSE
drafts a ready-to-append FCL stub — a miss becomes loop input, never a guess.
Refusal is a result: CLI exit 0. Analytics: pure-python pagerank with numpy
as a byte-identical booster; cycles reported with per-class counts.

## 6 · The loop, mechanized (P3–P5 + retirement as code)

Contracts in `loop/*.py` docstrings (normative). What "mechanized" means here,
precisely (council 2026-07-20): the pipeline's *administration* — parsing,
counting, staging, verifying, freezing, retiring — is code; the *judgment*
(what counts as the same gap) stays a human-declared `gap_shape`, by lock #20.
G4's real-log half is therefore honestly labeled: **bookkeeping that
reproduces the declared taxonomy** (the historical counting convention is now
stated in the sidecar), not autonomous pattern recognition. Spine: `scan`
parses the FCL log's own schema (11/11 live entries must parse, statuses
mapped) → `promote` detects declared-gap_shape recurrence (G4's ground truth:
recurring exactly {FCL-001, FCL-007, FCL-008, FCL-009}; promotable {} — every
recurring class is human-disposed, and FCL-008's rejection is RESPECTED,
never re-proposed) →
`mint` stages matcher-v2 (the proven mint_001 shape + a machine-checkable YAML
block: signature_sql / confirm predicates / fix pairs_sql) → `verify` must
fire against the matcher's own originating entries (no unreproduced rule) and
compose with COMPOSITION-VALIDATOR → `freeze` writes edges + `synthesis_chain`
provenance + fact-loop rows (`synthesis_facts`/`fact_validations`/
`evolution_log`/`insights` — the tables already live in the store) +
initializes outcome counters, idempotently (second run inserts 0) →
`retire` demotes on evidence (ratio then cap; demote-to-dormant with counters
preserved, NEVER delete; dormant rules' edges excluded from resolve unless
asked; its organic evidence stream is `record_outcome` fed by arm-A judged
rows — see §7). Freeze on a real instance requires `--approve`; fixtures may
self-approve. Per lock #26, a PostToolUse hook may auto-append resolver-
drafted REFUSE stubs (transcription only; `gap_shape` stays human) — Phase 8b
additive; the manual append path remains primary and fixture-tested.

## 7 · Proof harness A — the A/B (the headline)

Contracts in `measure/ab_*.py`. N=30 tasks frozen + hash-stamped BEFORE any
arm runs: 12 fixture (token-cost measurement — the engine was tuned on them,
say so), 10 organic (incl. 2 refusal-expected: honest refusal scores correct,
confident fabrication scores wrong), 8 corpus-private (answerable only from
this graph). **Terminology fixed by the council (2026-07-20):** the G6 grep is
a *prompt-leakage check* (arm-B prompts carry zero graph content — tested);
model-prior contamination is addressed separately by the corpus-private
subset's *novel-fact construction* (facts this project minted post-date any
pretraining corpus — state which tasks rest on minted facts vs extracted
ones). Report the three-way split separately, ALWAYS — the JSON schema has no
blended top-level accuracy field, by gate-enforced contract.

Arms identical except the graph block (matched protocol, 2502.11371): fixed
model, temp 0, one shot, external headless `claude` CLI subprocesses so
measurement never spends build-session tokens — **including the judge calls**;
tokens from usage metadata = the one legitimate `measured:api_usage` label.
**Phone-hardening (the run is the design case, not an edge):** spike-first
entry condition; strictly serialized; per-(task,arm) checkpoints so a
Phantom-Process-Killer kill resumes instead of restarting; fixed timeouts;
retries logged with `retry_count` and excluded from strict one-shot claims;
G6 enforces exactly 30 unique task_ids per arm. Judge: string-match →
refusal-check → blind LLM judge (arm label stripped, responses CANONICALIZED
so style tells don't defeat blindness, a logged blindness spot-check, full
transcript stored), method recorded per row. Judged arm-A rows feed
`record_outcome` for every minted edge on the answer path — retirement's
organic evidence stream. Report: per-task table + per-subset aggregates with
**mandatory Wilson intervals + McNemar's paired test** (at n≤12 per subset
the interval IS the honest story — printed beside every point estimate) +
indexing/storage costs + exploratory path_confidence↔correctness correlation
(labeled exploratory — see lock #18). Claim sentence fixed: **"PoC evidence
on the claude-code-tools corpus (N=30); not a generalizable benchmark."**
`ab_variants.py` (built, sampled at k=2, not used for the headline) is the
road to hundreds later — a command, not a project.

## 8 · Proof harness B — the frontier-call rate

`measure/frontier_rate.py`: per-entry cumulative distinct gap_shape classes +
per-batch new-class rate off the FCL log (chronological = bottom-up), with
the 2 historical organic batches (22 + 26 queries) computed as the baseline.
G5 recomputes the series independently and requires equality. The gate checks
COMPUTED HONESTLY, not "falling" — the reading sentence states what the
numbers say. Output labeled `derived:fcl_log_parse`.

## 9 · Prior art & rigor (why the design is shaped this way)

Validation: **RoT 2509.21743** — reasoning stored as a traversable graph,
retrieved not re-derived: ~40% fewer output tokens / 82% lower latency / 59%
lower cost, accuracy preserved (the thesis, independently demonstrated);
**HtT 2310.07064** — induced rule libraries +10–30% accuracy (mint→verify→
freeze's ancestor); **RecMem 2605.16045** — recurrence-gated consolidation
(our promotion gate), with the caveat that fixed thresholds are non-adaptive
(→ §13). Corrections adopted: **SkillOps 2605.13716** — unmanaged rule
libraries degrade BELOW the no-rule baseline at scale → lock #13; honest
framing (council 2026-07-20): SkillOps measures at 200–2000 rules and this
PoC has 1 minted rule — retirement here is **architected ahead of need**, not
something this PoC's own data demonstrates; **cycles ≠ contradictions** →
lock #19, carried by our own first-party FCL-009 field notes (TOKI 2606.06240
is *thematic precedent only* — it's a bitemporal concurrency-control algebra,
not a cycle-topology result; relabeled per the council's citation audit —
and `project_memory`'s synthesis-mud already implements a worked-example-
tested contradiction classifier this house can reuse, see ROADMAP);
**DoublyCal 2601.11956** — evidence-confidence ≠ reasoning-confidence → lock
#18 + the exploratory correlation in the A/B report;
**RAG-vs-GraphRAG 2502.11371** — matched protocol + costs beyond tokens →
§7; **KGQAGen 2505.23495** — hand-authored KGQA benchmarks average 57%
factual correctness → lock #14's claim scope + variant generator. Roadmap
(not PoC): reward/outcome-weighted traversal (RoT), adaptive thresholds,
compression-level selection (2604.15877).

## 10 · The gate contract

`gates/` is COMPLETE, runnable, and tamper-evident to the build session via
**three independent anchors** (council 2026-07-20 — a manifest alone was
self-referential): (1) `MANIFEST-GATES.sha256` over every gates/ file;
(2) an **external anchor** at `/root/reasoning-graph/.reasoning-graph-gates-anchor.sha256`
— instance-0's root, outside this repo and outside the session's write
mandate — holding the sha256 *of the manifest itself*; (3) **git**: the suite
is committed pre-handoff and `run_all.py` refuses on any dirty gates/ state
(BUDGET-LOG.md exempt; CORE-LOCK is git-committed by G3 at creation, so
regeneration is a visible diff — closing the loophole the council found in
G7's zero-core-edits proof). Any mismatch → exit 4, nothing runs. Verdicts:
0 PASS · 1 FAIL · 2 NOT-BUILT · 5 INFRA-FLAKE (timeout/signal-kill = phone
hiccup; re-run before diagnosing). `--resume` restarts an interrupted suite
at the first not-yet-passed gate. Delivery state (verified 2026-07-19, re-
verified post-amendments 2026-07-20): **G0 PASS**; G1–G8 NOT-BUILT cleanly. G0 substrate-intact (re-run every
phase) · G1 schema+agnosticism (dynamic grep vs the live DB's own kinds) ·
G2 edge-confidence (derivation table cell-by-cell + G0 re-run) · G3
resolver+refusal (planted tiny content, exact products; writes CORE-LOCK) ·
G4 loop (history reproduction + fixture end-to-end ×2 + retirement fixture) ·
G5 frontier-rate (independent re-parse equality) · G6 A/B artifacts
(freeze-before-run mtimes, measured token basis, arm-B contamination grep =
0 hits, subset split, variants sample) · G7 second corpus (stretch;
CORE-LOCK unchanged) · G8 codification bar (pytest green, INVARIANTS↔tests
1:1 both directions, demo verbatim line, numpy byte-identical via import
shim, docs marker-free with required sections, README quickstart EXECUTED,
CHANGELOG hardening pass with RG-n ids, self-verifying examples). The final
arbiter is Eyal re-running `run_all.py`.

## 11 · Build-session protocol

1. Work phase by phase, in order; gate each phase before the next; log
   BUDGET-LOG at every attempt; re-run G0 after every phase.
2. The module docstrings are the contracts — implement to them; where a
   docstring and this doc disagree, STOP and surface it (that is an FCL-shaped
   finding, not a judgment call to make silently).
3. Instance-0 writes only through migrate/freeze/retire with `--approve`
   semantics honored; every DB write transactional; backup before m001.
4. Real bugs found along the way: fix, regression-test, CHANGELOG under the
   hardening pass with an RG-n id, **and a git commit whose message carries
   that RG-n id** — G8 cross-checks CHANGELOG ids against `git log`; a fix
   without a diff trail is narration. Commit at every gate PASS too (the
   council's resume/rollback requirement).
5. Operational, this host: keep Termux foregrounded / hold a wake lock for
   Phase 6's serialized run; an INFRA-FLAKE verdict is re-run, never debugged
   as code; `run_all.py --resume` after any OS interruption.
6. When done: update RELEASE-NOTES ("What's honest about the scope" —
   including any check that ended SKIP/NOT-BUILT), VENDORED.json hashes, and
   leave the repo with `run_all.py` output pasted into the final report.

## 12 · What NOT to do

- Do NOT rebuild or "improve" P0–P2 (§0). G0 breakage = failed session.
- Do NOT edit `gates/**` (tamper-manifested) or the frozen files (§0's list).
- Do NOT infer edges: unminted = dropped; a miss drafts an FCL stub.
- Do NOT default a missing confidence to anything. Refuse.
- Do NOT present path confidence as a probability, or any number as measured
  except A/B api-usage tokens.
- Do NOT mint on first occurrence (except the documented explicit-human-
  approval path), and never re-propose a human-rejected class (FCL-008).
- Do NOT add learned/opaque ranking signals — declared > inferred is the
  thesis; a learned signal here is a bug.
- Do NOT resolve §13's open questions — log and continue.
- Do NOT let the A/B arms share graph content (arm B is grep-audited), and do
  NOT run measurement inside the build session's own token budget.

## 13 · Open questions for your refinement (yours to declare, not mine to infer)

1. ~~**The 0.90 inherited-curation default** (lock #21) — confirm, change the
   value, or demand per-edge review before the migration backfills it.~~
   **DECLARED 2026-07-20 by Eyal: 0.90 confirmed** — recorded in
   `gates/eyal-approvals/edge-confidence-0.90.json`; G2 requires the artifact.
2. **Lane B narrative prose** (handbook2/3, ~190KB) — mine, defer, or drop;
   same judgment family as open call #2 was.
3. **KillShell / SlashCommand** — two real Claude Code tools absent from the
   14-tool P0 corpus; patch in (mint_001 will fire for them) or leave.
4. **FCL-008 / 010 / 011 dispositions** — currently rejected/watching; any
   change is yours.
5. **Second-corpus pick** — lowering-ladder docs proposed, not locked.
6. **A/B judge model** — which model judges the judge-keyed tasks.
7. **Adaptive promotion threshold** — RecMem flags fixed thresholds; ours is
   declared at 2. Revisit after the PoC's frontier-rate data?
8. **Compression-level selection** (2604.15877) — we always compress mined
   gaps to declarative rules; episodic/procedural targets are unexplored.
9. **Retro-apply matcher-v2's machine block** to TOOL-COMBO-INFERENCE-MINTED.md
   (currently v1, human-text only)?
