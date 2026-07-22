# 00 — Mental model

**Graph = frozen reasoning.** A knowledge graph is reasoning done once: you pay inference to declare a confidence-weighted edge, then retrieve it forever by traversal. Multi-step reasoning becomes path composition.

**The lowering ladder.** Work sits on a rung: rung 3 prose (re-derived every call), rung 2 code, rung 1 data/declared, rung 0 precomputed/graph. This framework is rung-0 applied to *reasoning itself* — don't re-derive at run time what you can settle ahead of time and look up.

**A reasoning step is an edge.** TRAVERSAL belongs to Python (shortest/highest-confidence path, pagerank, cycle detection). EDGE-CREATION is the frontier's residue — the judgment a model still has to do. The *extract-vs-decide law* routes which is which: what can be extracted freezes; what needs judgment is minted (and only after a validation gate).

**DECLARE · INDEX · RETRIEVE.** One `GraphSchema` declares node/edge kinds and their confidence rules; the store indexes; `resolve` retrieves. Everything downstream is derived from the declaration — the core knows nothing corpus-specific.

**The residue stays prose.** Irreducible judgment is *supposed* to stay un-declared; over-declaring it is brittleness. That is why the framework refuses rather than fabricates, and why a gap the corpus genuinely lacks is logged, not invented.

**The metric.** As reasoning migrates model→graph, the *frontier-call rate* (new gap-shape classes per N logged misses) falls. That, plus an A/B token+accuracy comparison, is the proof.
