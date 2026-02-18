# ADR-0002: Hybrid Communication Pattern (Coordinator-First, Swarm-When-Needed)

- Status: Accepted
- Date: 2026-02-18
- Decision owners: Platform Architecture Team
- Related requirements: R2 (easy agent composition), R4 (multiple comm patterns), R3 (horizontal scaling)
- Related docs: [considerations/01](../considerations/01_communication_patterns.md), [diagrams/02](../diagrams/02_patterns.md)

## Context

The framework must support multiple agent collaboration patterns. The two primary modes are:
1. **Coordinator-managed**: a central coordinator dispatches tasks to specialists, aggregates results, and controls the workflow.
2. **Leaderless swarm**: agents collaborate peer-to-peer via shared memory and direct messaging, without a central coordinator.

Each mode has trade-offs in predictability, cost, resilience, and flexibility. Product teams need a clear default pattern while retaining the ability to use advanced patterns for complex problems.

## Decision

Adopt a **hybrid model: coordinator-first with swarm delegation** as the default communication pattern.

- **Default**: All workflows start with a coordinator-managed pattern.
- **Opt-in swarm**: Coordinators can delegate sub-problems to a leaderless swarm by publishing a `task.broadcast` event with a **budget envelope** (`max_tokens`, `max_turns`, `timeout`).
- **Additional patterns**: Blackboard and market-based patterns are available as building blocks within either mode.

## Options considered

### Option A — Coordinator-only
- **Summary**: All workflows are coordinator-managed.
- **Pros**: Simple, predictable, cost-controlled, compliance-friendly.
- **Cons**: Poor fit for ambiguous problems requiring debate or creative synthesis. Coordinator is a bottleneck and single point of failure.
- **Risks**: Over-centralization; coordinator prompt becomes a maintenance burden.

### Option B — Leaderless swarm-only
- **Summary**: All workflows use peer-to-peer collaboration.
- **Pros**: Resilient, flexible, no central bottleneck.
- **Cons**: Non-convergence risk, unbounded cost, poor fit for structured workflows, hard to debug.
- **Risks**: Cost explosions; difficulty onboarding product teams.

### Option C — Hybrid (coordinator-first + swarm delegation) — chosen
- **Summary**: Default to coordinator; delegate to swarm for complex sub-problems.
- **Pros**: Predictable default for product teams. Flexibility for complex reasoning. Budget envelopes prevent cost explosions.
- **Cons**: Higher implementation complexity. Requires clear guidelines for when to use swarm delegation.
- **Risks**: Teams may overuse swarm delegation (mitigated by explicit opt-in and budget requirements).

## Rationale

- Product teams (our primary users) need a simple, predictable pattern. The coordinator model provides clear control flow, deterministic cost, and easy debugging.
- Some e-commerce problems genuinely benefit from multi-perspective synthesis (product comparisons, dispute resolution, review authenticity). Swarm delegation addresses these without forcing the swarm model onto simple workflows.
- Budget envelopes (max_tokens, max_turns, timeout) ensure swarm delegations are bounded.
- The framework supports both patterns in the same Agent Runtime, reducing operational complexity.

## Consequences

**Easier:**
- Product teams onboard with the coordinator pattern (familiar, well-documented).
- Complex problems get better solutions via swarm delegation.
- Cost is predictable (budget envelopes).

**Harder:**
- Agent Runtime must support both coordinator and swarm modes.
- Monitoring must surface swarm delegation metrics alongside coordinator metrics.
- Documentation must clearly explain when to use swarm delegation.

## Follow-ups

- Implement coordinator pattern in Phase 1 (PoC).
- Implement leaderless swarm delegation in Phase 2 (Pilot).
- Build convergence detector for swarm mode.
- Write guidelines for product teams: "When to use swarm delegation."
