# Event-Driven Agentic Swarm Framework — Architecture Design Workspace

This repository is a **documentation-first** VSCode project used to generate and maintain an architecture design for an **in-house, event-driven agentic swarm framework** for e-commerce.

It is optimized for **GitHub Copilot Chat** using **Claude Sonnet 4.5** and **Claude Opus 4.6**.

## What you get

- `design/high_level_architecture.md` — the final “one-pager” architecture summary (with links to deeper docs).
- `design/considerations/` — deeper component and decision considerations (buy vs build, pros/cons, risks).
- `design/adr/` — Architecture Decision Records (ADRs) for every critical decision.
- `design/diagrams/` — Mermaid diagrams (easy to render in VSCode / GitHub).
- `prompts/` — copy-paste prompts to drive Copilot to generate/update the docs.

## How to generate the architecture docs (Copilot + Claude)

1. Open this folder in **VSCode**.
2. Open **Copilot Chat**.
3. Select model:
   - Use **Claude Sonnet 4.5** for fast iteration and broad generation.
   - Use **Claude Opus 4.6** for “deep thinking” (trade-offs, edge cases, hard decisions).
4. **Run the initial prompt**:
   - Open `prompts/00_initial_copilot_prompt.md`
   - Copy the whole prompt into Copilot Chat and send.
5. Then iterate with the follow-ups:
   - `prompts/10_followup_prompts.md`

## How to use “thinking vs writing” modes effectively

A practical pattern:
- **Opus**: ask it to propose *decision options + trade-offs + risks* and to draft ADRs.
- **Sonnet**: ask it to *apply changes to files*, update diagrams, and keep docs consistent.

## Rules of engagement for Copilot (important)

Copilot should:
- Treat this as a **real architecture project** and maintain internal consistency across all docs.
- Use **Mermaid diagrams** (not screenshots).
- Use **ADRs** for decisions; link from `high_level_architecture.md` to ADRs and to detailed considerations.
- Prefer **event-driven** patterns (pub/sub) and **asynchronous communication**; explicitly address *streaming chunks* and *multimodal synchronization*.

See:
- `CLAUDE.md` — project context + strict generation rules.
- `.github/copilot-instructions.md` — repository-level Copilot instructions.

## Suggested workflow for updates

When you change requirements:
1. Update `design/high_level_architecture.md` first (the “contract”).
2. Update affected `design/considerations/*.md`.
3. Add / update ADRs in `design/adr/`.
4. Ensure diagrams in `design/diagrams/` still reflect reality.

---

Generated scaffolding date: 2026-02-18.
