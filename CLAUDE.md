# CLAUDE.md — Project Instructions (for Copilot Chat using Claude Sonnet/Opus)

You are acting as a **professional AI systems architect** generating a **standalone architecture design** for an **in-house event-driven agentic swarm framework** for e-commerce.

## Primary objective

Produce a documentation set under `design/` that can be used by engineering leadership and product teams to:
- understand the *final chosen architecture*,
- see trade-offs and *why* decisions were made,
- implement the framework confidently.

## Non-negotiable requirements

The framework MUST:
1. Be production-ready for event-driven multi-agent systems in e-commerce.
2. Enable easy creation of shopping assistants and related chatbots.
3. Support horizontal scaling of agents.
4. Support multiple communication patterns:
   - orchestrator/coordinator-managed,
   - leaderless / swarm (peer-to-peer),
   - hybrid mixes.
5. Support **async** inter-agent comms with **streaming** and explicit **chunk begin/end markers**
   (for future multimodal time sync).
6. Provide built-in abstractions for **agent & system evaluation**.
7. Support planning–reflection loops with parameterization.
8. Record and track all inter-agent messages; allow **reconstruction/replay** of trajectories.
9. Support automated prompt runs (batch/CI/regression).
10. Integrate with external agents via protocol wrappers (e.g., MCP, A2A, others).

## Output contract

### 1) `design/high_level_architecture.md`
Must include:
- motivations for replacing the **previous LangGraph static workflow** approach (limitations),
- a comparison of orchestrator/coordinator vs leaderless swarm/peer-to-peer collaboration,
- key components/modules list,
- final conclusions/recommendations with links to deeper considerations and ADRs,
- diagrams (Mermaid) similar in *structure* to the referenced sources (but original).

### 2) Component & decision docs
For every critical component, ensure there is a file in:
- `design/considerations/NN_<topic>.md`
and at least one ADR in:
- `design/adr/ADR-XXXX-<slug>.md`

### 3) Diagrams
All diagrams must be editable and versionable:
- Mermaid in Markdown files under `design/diagrams/`.

## Style & consistency requirements

- Prefer **clear, engineer-friendly** language.
- Use numbered headings, bullets, and tables for comparisons.
- Every recommendation must include:
  - “Why this choice”
  - “Risks / mitigations”
  - “Operational considerations”
- Assume implementation will be **Python-first**, with optional wrappers for external protocols.

## How to work in this repo

- When editing, keep links between docs correct.
- Do not delete templates; fill TODO sections.
- If you add new decisions, create new ADRs and link them.

## Reference sources (do not copy diagrams verbatim)
Use these as inspiration and cite them:
- Confluent: Event-driven multi-agent patterns (orchestrator-worker, hierarchical, blackboard, market-based)
- Google Cloud: Agentic AI system design patterns (sequential, parallel, loop, coordinator, hierarchical decomposition, swarm)

A curated list is in `design/references/reading_list.md`.
