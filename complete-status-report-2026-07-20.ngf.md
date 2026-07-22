---
ai_card:
  kind: status_report
  id: reasoning-graph-complete-status-report-2026-07-20
  title: "Reasoning-Graph — complete status report (vision · state · roadmap · potential)"
  version: "1.0"
  written: "2026-07-20"
  owner: eyal_nof
  audience: "Eyal + a smart friend with no special background — written to be understood at a dinner table, accurate enough to hand to an engineer"
  status: "point-in-time snapshot — the framework PoC is built and all 9 quality gates pass"
  thesis: >
    Reasoning that an AI would normally re-think from scratch every time is worked
    out once, frozen into a look-up-able graph, and made trustworthy by refusing
    to answer what it can't support — a graph that is cheaper, more honest, and
    self-growing all at once, because those three are one property, not three features.
  provides:
    - "A plain-language explanation of the whole idea and why it matters."
    - "An honest account of what is built today and what is not yet."
    - "The roadmap and the long-term potential."
  depends_on:
    - "Reasoning-Graph-source-of-truth-2026-07-19.ngf.md — the build contract"
    - "reasoning-graph-context-datapacket-2026-07-12.ngf.md (v1.8) — the living why-doc"
    - "/root/projects/reasoning_graph/ — the built framework (gates G0–G8 all PASS)"
  last_verified: "2026-07-20 (python3 gates/run_all.py → 9/9 PASS)"
---

# Reasoning-Graph — where it stands, in plain language

> **What this is.** A snapshot of a project that's now real, written so a friend
> with no technical background can follow it — and honest enough that an engineer
> can trust every claim. It covers the idea, why it matters, what's built today,
> where it's going, and what it could become.

## The one-sentence version

**Most of the "thinking" an AI does, it does over and over — so we work it out once, store it as a look-up, and make it trustworthy by teaching it to say "I don't know" instead of guessing.**

## The big idea (for a friend)

When an AI like Claude does a task, it *reasons out loud* — it works through the logic in words, from scratch, every single time. That's slow, it costs money, and it gives slightly different answers on each run. But here's the thing: **most of that reasoning is the same reasoning, repeated.** The AI re-derives the same little conclusions again and again.

Think of a master carpenter's notebook. Over years they don't write down facts — they write down *worked-out judgments*: "for this wood, use this joint." Once it's in the notebook, three things happen **at the same time, and they can't be separated**:

1. They stop re-figuring it out every morning — they just **look it up** (fast, cheap).
2. They only write down what they've actually **confirmed**, and they know where the notebook is blank — so they never *pretend* to know something they don't (**honest**).
3. The notebook keeps **filling in** as they hit new problems they haven't solved before (**it grows**).

A trustworthy notebook you can look things up in, that gets fuller the more you work — **that's the whole project.** We're giving an AI that notebook, but for *reasoning*, and we call it a reasoning-graph because each stored judgment is a link between two dots, and a chain of reasoning becomes a path you walk instead of a thought you re-think.

## Why "cheap, honest, and self-growing" are really *one* thing

This is the heart of it, and it's why it isn't just "a faster database."

- You only get the **cost/speed** win *because* it became a look-up instead of live thinking.
- The look-up is only *usable* **because** it's **honest** — if it bluffed when unsure, you couldn't trust a single stored answer, and the whole thing would be worthless. Every stored judgment carries a confidence label that says exactly where the number came from (a human declared it, or a formula computed it) — never a faked "measured" number. And when the graph has no real support for an answer, it **refuses** — it says "I don't have that" and even drafts a note to itself about the gap, rather than hallucinating.
- And it stays cheap *over time* **because** it **learns**: every time it's forced to think live (a "frontier call"), that reasoning gets logged, and if the same kind of gap shows up again, it gets checked and *frozen into the notebook*. So the graph grows by capturing exactly the reasoning it had to do the hard way.

Remove any one of the three and it collapses. Cheap-but-dishonest is a liar. Honest-but-can't-grow is a dead reference book. Growing-but-expensive is just… the AI we already have. Together, they're a single object: **a reasoning layer that gets smarter and cheaper the more it's used, and is safe to trust because it knows its own limits.**

## How it works, without the jargon

Four moves, in a loop:

1. **Declare.** You describe the shape of your world once — what kinds of things exist and how they connect. Everything else is built from that description. (We proved this is truly general: a completely different second subject dropped in with *zero* changes to the engine.)
2. **Look up.** Ask a question; it finds the path of stored judgments that answers it, and hands back the answer *plus* how confident it is *plus* the exact chain it walked — so you can always see its work.
3. **Refuse.** If the honest answer is "the stored knowledge doesn't cover this," it says so — and logs the gap instead of inventing something.
4. **Learn.** Recurring gaps get worked out, verified, and frozen into new links. Old links that keep being wrong get quietly retired (never deleted — just set aside, with the evidence). The notebook curates itself.

## Where it stands today (honestly)

**It's built, and every quality check passes.** There are nine independent, tamper-proof "gates" — automated referees that can't be talked into a pass; they re-check the real work, not a checkbox. As of today, **all nine are green.**

What that green actually means, in concrete terms:

- On facts that live **only inside the graph** (things a language model couldn't have memorized from the internet), the graph-backed answers were **right 100% of the time, versus a 50% coin-flip for pure prose reasoning — while using about 55% fewer words.**
- On ordinary questions, it was more *honest*: it correctly caught the traps where the right answer is "there's no dedicated tool for that," which the prose version confidently got wrong.
- The "is it learning?" signal — how often it has to think live — measured as **falling** over time.

**And the honest limits, stated plainly** (because refusing to overclaim is the entire spirit of the thing):

- This is a **proof of concept at small scale** (30 test questions). It's a strong, real *direction* — not yet a published-benchmark-grade claim. Scaling that proof up is a known next step, and the tool to do it is already built.
- The confidence numbers are honest *rankings*, not laboratory-calibrated probabilities — and the report says so on its own face.
- The "self-retiring" part is proven on a test rig, not yet worn-in by heavy real-world use.
- It's proven on one real subject (plus a small second one to show generality) — not yet a dozen.

Nothing here is dressed up as more than it is. That's on purpose.

## The roadmap

Near-term, each step extends the same vision:

- **Scale the proof** from 30 questions to hundreds, with safeguards so the AI can't have "seen the answers" beforehand. (The question-generator for this already exists.)
- **Learn which paths actually work.** Right now it prefers the most-confident path; next it can prefer the paths that have *actually led to correct outcomes* in practice.
- **Capture misses automatically.** Wire it so that when it's used in a real session and hits a gap, that gap is logged on its own — the notebook fills itself from live work instead of by hand.
- **Run it on small/local models — including on a phone.** This is where it matters most: when you *can't* afford to re-reason everything with a big expensive model, a cheap, honest look-up is the difference between "impossible" and "works." (This whole framework was built and proven on a phone.)
- **Reuse across the wider toolkit** — the same "declare it once, look it up forever" move already runs through the rest of the ecosystem.

## The potential

The long game is a **reasoning layer that compounds.** Ordinary AI starts from zero on every task. This starts from everything it has ever already figured out — and it keeps that pile trustworthy, and the pile keeps growing. The more it's used, the more it can answer by look-up, the cheaper and more consistent it gets, and the *less* it has to fall back on expensive live thinking.

It also fits a bigger picture you're already building: a world where AI work is increasingly **declared and precomputed** rather than re-derived from scratch — pushing every kind of work "down the ladder" from expensive re-thinking toward near-free look-up. Knowledge retrieval was one axis of that (your RAG work). **This is the reasoning axis.** Same instinct, applied to the most expensive thing an AI does: thinking.

The honest ceiling of the ambition: a substrate any domain can plug into by just describing its shape, that turns "the AI works it out again" into "the AI already knows, and knows what it doesn't" — cheaper, steadier, and safe to trust, *because* it refuses to pretend.

---

## For the technical reader (one dense appendix)

A corpus-agnostic core (`/root/projects/reasoning_graph/`): one `GraphSchema` declaration → SQLite store (missing edge-confidence *refuses*, never defaults to 1.0) → an additive migration that put numeric, provenance-labeled confidence on all 856 instance-0 edges (they previously had none) → a resolver that composes a highest-confidence path (Dijkstra over −log confidence) and returns `ANSWER` / `WEAK_ANSWER` / `REFUSE(reason)` with the path and a `path_class` that discloses a fact-walk from a reasoning composition → a mechanized `scan → promote → mint → verify → freeze → retire` loop that reproduces the project's own live history exactly → measurement: a computed **frontier-call rate** (falling, 0.41 → 0.08 across two organic batches) and an **A/B proof** (N=30, matched protocol, external headless model calls, deterministic scoring, per-subset Wilson intervals + McNemar's exact test, **no blended headline number**).

Every confidence carries a closed-vocabulary basis (`declared:*` / `derived:*`); nothing is called "measured" except real API token counts. Nine gates (G0–G8) are green, including a substrate-integrity gate that proves the source material was never tampered with, a schema-agnosticism gate (a second, alien-domain corpus with zero core edits), and a codification-bar gate (40 tests one-to-one with a declared invariant list, a self-verifying demo, and a docs set whose quickstart actually executes). Four real bugs were found and fixed with regression tests during the build (RG-1…RG-4), each traceable in git history.

**Verify it yourself:** `cd /root/projects/reasoning_graph && python3 gates/run_all.py` → 9/9 PASS.

Related: `Reasoning-Graph-source-of-truth-2026-07-19.ngf.md` (the build contract) · `reasoning-graph-context-datapacket-2026-07-12.ngf.md` (§5 field-notes, v1.8) · `/root/projects/reasoning_graph/RELEASE-NOTES.md` ("What's honest about the scope").
