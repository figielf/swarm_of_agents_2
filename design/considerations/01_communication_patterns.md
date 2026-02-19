# Communication patterns: Orchestrator/Coordinator vs Swarm/Leaderless vs Hybrid

## 1. Context and problem statement

Multi-agent systems require a communication topology that governs how agents discover tasks, exchange information, and converge on a final answer. The choice of pattern directly impacts latency, cost, reliability, and developer experience.

**Constraints:**
- Must support both structured e-commerce workflows (search → recommend → checkout) and open-ended collaborative reasoning.
- Python-first implementation; must integrate with `asyncio`.
- Enterprise SLOs: p95 response latency < 5s for common workflows.
- Cost sensitivity: LLM call amplification must be bounded.
- Compliance: certain workflows (payments, returns) require auditable ordering guarantees.

## 2. Requirements coverage

| Requirement | Coverage |
|---|---|
| R1 — Production-ready event-driven multi-agent | Core: this decision defines the communication structure. |
| R2 — Easy creation of shopping assistants | Coordinator pattern provides a clear "recipe" model for product teams. |
| R3 — Horizontal scaling | All patterns decouple agents via the Event Bus; each scales independently. |
| R4 — Multiple communication patterns | This decision explicitly supports coordinator, leaderless, and hybrid. |
| R5 — Async with streaming | Event Bus is inherently async; streaming is orthogonal to the topology. |
| R8 — Trajectory capture/replay | All patterns route through the Event Bus → Trajectory Store pipeline. |
| R10 — Protocol wrappers | External agents plug in via the Protocol Gateway regardless of internal pattern. |

## 3. Options

### Option A — Coordinator-only (orchestrator-managed)

A central **Coordinator Agent** receives all user requests, decomposes them into sub-tasks, dispatches to specialist agents via the Event Bus, aggregates results, and returns the final response. The Coordinator uses the **Capability Registry** (a read-only projection of the **Agent Registry**) to discover available specialists and their NATS subjects at runtime, rather than hard-coding agent references. Each specialist is described by an **AgentSpec** that declares its capabilities, routing, and input/output schemas. See [considerations/17](17_agent_registry_and_discovery.md).

**Pros:**
- Clear control flow; easy to reason about and debug.
- Deterministic cost: coordinator controls how many specialists are invoked.
- Natural fit for step-by-step workflows (search → filter → recommend).
- Compliance-friendly: single point of authorization enforcement.

**Cons:**
- Single point of failure; coordinator crash halts the workflow.
- LLM call amplification: every interaction requires coordinator + specialist calls.
- Coordinator prompt complexity grows linearly with the number of specialists.
- Poor fit for problems requiring multi-perspective debate or creative synthesis.

**Operational implications:**
- Coordinator must be highly available (replicated, stateless with state in Event Bus).
- Coordinator prompt maintenance is a bottleneck; requires Prompt Registry integration.

### Option B — Leaderless swarm (peer-to-peer)

All agents receive a broadcast of the user request. They coordinate via **Shared Memory** (blackboard/stigmergy) and direct peer messages on the Event Bus. A **Finalizer Agent** or quorum rule assembles the response.

**Pros:**
- Resilient: losing one agent does not block the workflow.
- Better for ambiguous, creative, or adversarial reasoning tasks.
- No coordinator bottleneck.

**Cons:**
- Non-convergence risk: agents may loop without consensus.
- Unbounded message volume and cost without explicit budgets.
- Harder to debug: no single agent owns the control flow.
- Poor fit for workflows requiring strict ordering (e.g., payment authorization).

**Operational implications:**
- Requires turn limits, message budgets, and convergence detectors.
- Cost ceilings enforced at the Event Bus level.

### Option C — Hybrid (coordinator-first, swarm-when-needed)

Default to coordinator-managed flows. Allow coordinators to **delegate sub-problems** to leaderless swarms with explicit budget envelopes (max tokens, max turns, timeout).

**Pros:**
- Best of both worlds: predictable control for standard workflows, flexibility for complex sub-problems.
- Product teams start with the simpler coordinator pattern; swarm is opt-in.
- Budget envelopes prevent cost explosions in swarm delegations.

**Cons:**
- Higher implementation complexity: must support both modes in the Agent Runtime.
- Requires clear guidelines for when to use swarm delegation vs. additional specialist agents.

**Operational implications:**
- Agent Runtime must support both coordinator and peer messaging modes.
- Monitoring must surface swarm delegation metrics (convergence time, budget utilization).

### Option D — Market-based (auction/bidding)

An auctioneer publishes tasks; agents bid based on self-assessed confidence, estimated cost, or latency. The winning bidder executes the task.

**Pros:**
- Dynamic routing: best agent for the task is selected at runtime.
- Naturally load-balances across agents with overlapping capabilities.

**Cons:**
- Bidding adds latency (collect all bids before proceeding).
- Agents must reliably self-assess — overconfident agents win too often.
- Complex to tune bid evaluation criteria.

**Operational implications:**
- Works best as a routing sub-pattern within a coordinator flow (not as the primary topology).

## 4. Decision drivers

| Driver | Weight | Favors |
|---|---|---|
| **Predictability for product teams** | High | Coordinator / Hybrid |
| **Scalability** | High | All (Event Bus decoupling) |
| **Cost control** | High | Coordinator / Hybrid (budget enforcement) |
| **Flexibility for complex reasoning** | Medium | Swarm / Hybrid |
| **Operational simplicity** | Medium | Coordinator |
| **Resilience** | Medium | Swarm / Hybrid |

## 5. Recommendation

**Recommended: Option C — Hybrid (coordinator-first, swarm-when-needed)**

**Why:**
- Product teams get the simple, predictable coordinator pattern by default.
- For complex sub-problems (product comparisons, review authenticity, dispute resolution), coordinators can delegate to swarms with bounded budgets.
- Market-based routing is available as an optional sub-pattern for dynamic agent selection.

**Risks / mitigations:**
| Risk | Mitigation |
|---|---|
| Teams overuse swarm delegation for simple tasks → cost increase | Swarm delegation requires explicit opt-in and budget declaration. Default is coordinator-only. |
| Swarm non-convergence | Turn limits + convergence detector + hard timeout. Coordinator receives a partial/failed result and can fall back to its own synthesis. |
| Implementation complexity | Phase the rollout: coordinator in Phase 1, swarm in Phase 2. |

## 6. Required ADRs

- [ADR-0001: Messaging backbone](../adr/ADR-0001-messaging-backbone.md) — bus technology selection.
- [ADR-0002: Hybrid communication pattern](../adr/ADR-0002-hybrid-communication-pattern.md) — this decision.

## 7. Diagrams

See [design/diagrams/02_patterns.md](../diagrams/02_patterns.md) for:
- Coordinator/orchestrator pattern (DataFlow + Activity)
- Leaderless swarm pattern (DataFlow + Activity)
- Blackboard/shared memory pattern (DataFlow + Activity)
- Market-based auction/bidding pattern (DataFlow + Activity)

## 8. References

- Confluent: [Four Design Patterns for Event-Driven, Multi-Agent Systems](https://www.confluent.io/blog/event-driven-multi-agent-systems/) — orchestrator-worker, hierarchical, blackboard, market-based.
- Google Cloud: [Choose a design pattern for your agentic AI system](https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system) — sequential, parallel, loop, coordinator, hierarchical, swarm.
- De Nicola et al.: [Multi-agent systems with virtual stigmergy](https://www.sciencedirect.com/science/article/pii/S016764231930139X) — indirect coordination via shared state.
