# Initial Copilot Prompt — Generate the Architecture Documentation Set

You are in a VSCode repo that is **documentation-first**. Your job is to generate the complete architecture design for an **in-house event-driven agentic swarm framework** for e-commerce.

## Step 0 — Read project instructions
Before writing, read:
- `CLAUDE.md`
- `.github/copilot-instructions.md`
- `design/index.md`
- `design/references/reading_list.md`

## Step 1 — Produce/complete the required documentation
Fill in (do not leave TODOs) and ensure everything links correctly:

1) `design/high_level_architecture.md`
   - include motivations + limitations of the previous LangGraph static workflow approach,
   - include comparison: orchestrator/coordinator vs leaderless swarm/peer-to-peer,
   - list key components/modules,
   - include final conclusions + recommendations,
   - link to each relevant `design/considerations/*.md` and ADRs.

2) All files under `design/considerations/`
   - complete each template with concrete options, pros/cons, and recommendation.
   - include buy-vs-build analysis and operational implications.

3) `design/adr/`
   - create ADRs (use the ADR template) for every critical decision across:
     - messaging backbone,
     - agent runtime model,
     - memory/state strategy,
     - streaming chunk protocol,
     - evaluation/guardrails approach,
     - observability + replay,
     - protocol gateway for MCP/A2A,
     - deployment + scaling + isolation.

4) `design/diagrams/`
   - provide clear Mermaid diagrams:
     - architecture overview,
     - orchestrator/coordinator event-driven pattern,
     - leaderless swarm pattern,
     - blackboard/shared memory pattern,
     - market-based (auction/bidding) pattern,
     - message flow + streaming chunks.

## Step 2 — Enforce cross-document consistency
- Use a consistent vocabulary:
  - “Agent Runtime”, “Event Bus”, “Shared Memory”, “Tool Gateway”, “Evaluation Layer”, “Trajectory Store”, etc.
- Ensure every claim is backed by reasoning or references in `design/references/`.

## Step 3 — Produce a “done” checklist
At the end of `design/index.md`, update the checklist with:
- which files were completed,
- which ADRs were added,
- what open questions remain.

## Quality bar
- This is intended for production use in an enterprise e-commerce setting.
- Be explicit about failure modes, retries, timeouts, rate limits, idempotency, schema evolution, and governance.
