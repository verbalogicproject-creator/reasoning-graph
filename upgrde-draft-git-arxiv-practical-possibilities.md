# Upgrade draft: GitHub, arXiv, and practical possibilities

**Research date:** 2026-08-29  
**Project:** Reasoning Graph  
**Purpose:** connect the experimental code to relevant research and reusable open-source designs without adopting large systems merely because they are graph-based.

## Restored product mental model

Reasoning Graph is a **governed metacognitive memory for coding agents**.

“Metacognitive” means the system observes how reasoning was performed, recognizes recurring useful fragments, turns those fragments into compact named behaviors or typed graph relations, and later retrieves an inspectable support path instead of paying to rediscover the same reasoning. The graph is not authority by itself: provenance, verification, confidence basis, contradictions, and explicit refusal determine whether a path may be used.

```text
task -> resolve from verified graph -> ANSWER / WEAK_ANSWER / REFUSE
     -> append bounded observation -> recurring candidate -> verify
     -> human approve -> active rule -> outcome evidence -> retain, supersede, or retire
```

This is more specific than a generic knowledge graph and deliberately narrower than GraphRAG. It remembers reusable reasoning procedures and their evidence, not hidden chain-of-thought or arbitrary facts.

### Practical v0.1 uses

1. Claude Code tool and workflow advisor.
2. Local reasoning cache exposed through Python, CLI, and MCP.
3. Inspectable rule-path explanations with confidence composition and provenance.
4. Honest refusal plus gap capture where verified support is absent.
5. Benchmark harness comparing graph-backed reuse with simpler non-graph baselines.

### Practical v0.2 uses

1. Local workbench for paths, provenance, parallel relationships, and contradictions.
2. Human review of candidate behaviors and the evidence that produced them.
3. Lifecycle-health, frontier-rate, and retrieval-quality views.
4. Optional graph-retrieval experiments which are retained only if they beat simpler baselines.

### Non-goals

- Generic document question answering.
- Storage or exposure of private chain-of-thought.
- Autonomous activation of learned rules.
- Treating confidence as a calibrated probability or authority score.
- Adopting a large GraphRAG stack before a controlled benchmark proves its value.

## Candidate matrix

The source descriptions below are attributable facts. The adoption verdicts are project-specific engineering judgments.

| Candidate | Why it was chosen and the connection | What it practically adds | Cost or risk | Smallest useful experiment | Verdict |
|---|---|---|---|---|---|
| [Metacognitive Reuse](https://arxiv.org/abs/2509.13237) | Direct empirical match: recurring reasoning fragments become concise named behaviors; the paper reports up to 46% fewer reasoning tokens while matching or improving accuracy. | A compact `behavior` artifact distinct from raw traces and final facts; a token/accuracy evaluation target. | Model-led distillation is unsafe if promotion lacks evidence and review. | Distill ten recurring frontier-call cases into behavior cards; compare held-out tasks with and without retrieval. | **ADOPT concept now**, human-gated. |
| [ReasoningBank paper](https://arxiv.org/abs/2509.25140) / [official code](https://github.com/google-research/reasoning-bank) | Learns reusable reasoning from both successful and failed trajectories and evaluates on SWE-Bench and WebArena. | Positive and negative outcome records; retrieve strategies rather than entire traces. | The Apache-2.0 repository is small, experiment-specific, and explicitly not production software. | Map its memory record to this project’s observation/candidate model on twenty local traces without importing its stack. | **BORROW** schema and evaluation ideas. |
| [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) | Standard agent-facing protocol with generated schemas, lifecycle handling, transports, and client testing. | Typed `resolve`, `loop_scan`, `frontier_rate`, and `record_observation` tools. | Protocol/API version drift and unnecessary network exposure if deployed carelessly. | Use current stable v2 with local stdio, structured output, and SDK client contract tests. | **ADOPT**. |
| [NetworkX MultiDiGraph](https://networkx.org/documentation/stable/reference/classes/multidigraph.html) | Official directed parallel-edge structure; directly fixes the observed loss of relationships in NAI’s simple `DiGraph`. | Lossless projection and edge-specific path/visualization evidence. | Algorithms need explicit policy when several edges connect the same pair. | Load the repaired DB and assert that projected relationship count equals database relationship count. | **ADOPT**. |
| [Graphiti](https://github.com/getzep/graphiti) | Temporal facts retain source episodes and validity history; outdated facts are invalidated rather than erased. | Recorded time, event time, provenance references, supersession, and retirement history. | The full Apache-2.0 backend and LLM extraction system is far heavier than this local SQLite project. | Add temporal/provenance fields to a local fixture and test supersession without switching backend. | **BORROW model**, not dependency. |
| [LLM-Wiki](https://github.com/WeAgentAI/LLM-Wiki) | Agent-native search/read/link tools, evidence-sufficiency checks, bounded tool budgets, and a persistent Error Book resemble this project’s frontier-call log. | Simpler agent tool ergonomics and an error/gap-book design. | MIT but extremely young at review time, with only two commits and a model-dependent pipeline. | Prototype `graph_search` and `graph_read` over five tasks and compare them with monolithic query output. | **WATCH / BORROW interface only**. |
| [GraphRAG-Bench](https://github.com/GraphRAG-Bench/GraphRAG-Benchmark) | It asks the necessary falsifiable question: when do graphs outperform ordinary retrieval? | Task taxonomy and baseline discipline covering facts, reasoning, summarization, and generation. | Designed for document GraphRAG rather than reusable reasoning memory. | Adapt its taxonomy to the local 100-query fixture and always include keyword/non-graph baselines. | **ADOPT evaluation principles**. |
| [HippoRAG](https://github.com/OSU-NLP-Group/HippoRAG) | Combines entity graphs with Personalized PageRank for associative and multi-hop retrieval. | Optional PPR candidate expansion before deterministic resolution. | Embedding, extraction, and indexing complexity may not help a small typed graph. | Offline ablation: current ranker versus PPR candidates on cross-domain and debugging failures. | **EXPERIMENT only**. |
| [SkillOps](https://arxiv.org/abs/2605.13716) | Treats reusable skill libraries as typed ecosystems with utility, compatibility, risk, and validation health. | Lifecycle-health reporting and explicit behavior prerequisites, outcomes, validation, and failure contracts. | A “skill” does not automatically map to a graph rule; the mapping must be validated. | Add a read-only health report for ten behavior artifacts. | **BORROW for v0.2**. |
| [SkillOpt](https://arxiv.org/abs/2605.23904) | Uses bounded add/delete/replace edits, rejected-edit memory, and held-out improvement gates. | Safer candidate revision which cannot activate unless held-out results improve. | Model-driven optimization can overfit and increases evaluation cost. | Propose bounded edits against copied fixtures and retain accepted/rejected outcomes without changing active rules. | **WATCH**, post-v0.2. |
| [SkillOS](https://arxiv.org/abs/2605.06614) | Separates a frozen executor from a curator that updates an external skill repository. | A possible long-term curator/executor boundary. | Reinforcement learning and delayed reward are far beyond the project’s current evidence and scale. | Documentation comparison only. | **REJECT FOR NOW / WATCH**. |
| [ExpeL paper](https://arxiv.org/abs/2308.10144) / [official code](https://github.com/LeapLabTHU/ExpeL) | Experience gathering, insight extraction, and evaluation are an early precedent for the project’s loop. | Terminology and staged offline evaluation ideas. | Older Python and benchmark-heavy dependencies; natural-language insights are less governed than typed rules. | Map its phases to observation -> candidate -> verification in documentation. | **REFERENCE only**. |
| [Microsoft GraphRAG](https://github.com/microsoft/graphrag) | Strong reference for graph indexing and local/global document queries. | A future document-query comparison lane. | Upstream is research-oriented/maintenance-mode and warns that indexing can be costly; it addresses a different problem. | Tiny-corpus benchmark comparator only if document QA becomes a requirement. | **REJECT dependency for v0.1**. |
| [LightRAG](https://github.com/HKUDS/LightRAG) | Reference for dual graph/vector retrieval and incremental updates. | Optional hybrid-retrieval comparison. | Large overlapping framework with multiple storage and service concerns. | One benchmark adapter after the deterministic baseline is stable. | **WATCH / EXPERIMENT**. |
| [KAG](https://github.com/OpenSPG/KAG) | Schema-constrained and schema-free knowledge plus planned retrieval/reasoning operators resemble typed query plans. | Inspiration for explicit retrieve/traverse/verify operators and knowledge-boundary decisions. | Its OpenSPG, Docker, and model stack is too heavy for this v0.1. | Represent one local query as typed operators without importing KAG. | **BORROW concept later**. |
| [Graph of Thoughts](https://arxiv.org/abs/2308.09687) | Clarifies a terminology trap: it graphs transient thoughts during inference, unlike this persistent governed memory. | A sharper explanation of the product boundary. | Adopting it could blur reusable evidence with transient/private model reasoning. | No code adoption; document the distinction. | **REJECT FOR NOW**. |

## Recommended sequence

1. Adopt integrity/provenance contracts, MultiDiGraph semantics, current stable MCP v2, and explicit baseline evaluation.
2. Add behavior cards and success/failure observations inspired by Metacognitive Reuse and ReasoningBank, with human approval before activation.
3. Borrow Graphiti’s temporal provenance without changing the SQLite backend.
4. Benchmark PPR or hybrid retrieval only after deterministic repair; stop experiments that do not beat a simpler baseline.
5. Revisit automatic skill optimization or curation only after the project contains enough genuine recurring observations to evaluate it.

## The practical full picture

The strongest near-term product is not “an AI that reasons for you.” It is a local subsystem that lets an agent reuse previously verified reasoning without hiding its basis:

```text
coding question
    -> retrieve relevant behavior/rule paths
    -> expose sources, confidence basis, and proof limit
    -> answer weakly or refuse when support is insufficient
    -> record what happened
    -> let a human approve only the patterns that survive verification
```

That gives the experimental code a defensible path from useful tool advisor, to reasoning cache, to governed metacognitive workbench—without pretending the broad research problem is already solved.
