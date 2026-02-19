# ADR-0003: Agent Runtime Model — Lightweight Python asyncio Runtime

- Status: Accepted
- Date: 2026-02-18
- Decision owners: Platform Architecture Team
- Related requirements: R1 (production-ready), R3 (horizontal scaling), R5 (async + streaming), R6 (evaluation), R7 (reflection loops)
- Related docs: [considerations/03](../considerations/03_agent_runtime_and_lifecycle.md), [considerations/12](../considerations/12_buy_vs_build_stack_selection.md)

## Context

Each agent needs an execution environment that manages its lifecycle (startup, event consumption, processing, health, shutdown), concurrency, fault tolerance (retries, timeouts, dead-letter queues), and integration with the Evaluation Layer (reflection loops).

Existing agent frameworks (LangGraph, AutoGen, CrewAI) impose their own execution models that conflict with our event-driven, bus-centric architecture. We need to decide whether to adopt one of these frameworks or build a lightweight runtime.

## Decision

Build a **lightweight Agent Runtime in Python** using `asyncio` as the concurrency foundation.

The runtime is a thin layer that:
1. Subscribes to NATS JetStream subjects (via consumer groups).
2. Deserializes events per the message contract.
3. Invokes the agent's `handle(event)` method.
4. Manages concurrency (`max_concurrent_tasks` per instance).
5. Enforces timeouts and retries (exponential backoff with jitter).
6. Supports optional reflection loops (bounded by `max_reflection_rounds`).
7. Emits lifecycle events to the Trajectory Store.
8. Exposes HTTP health probes for Kubernetes.
9. Handles graceful shutdown on SIGTERM.
10. On startup, registers the agent’s **AgentSpec** with the **Agent Registry** (NATS KV bucket). Sends periodic heartbeats (every 30s). On shutdown, deregisters. See [ADR-0010](ADR-0010-agent-registry-agentspec.md).

Runtime configuration (timeouts, retries, concurrency, evaluators, tools) is read from the agent’s **AgentSpec**. This makes agent behavior declarative and auditable.

## Options considered

### Option A — Adopt LangGraph
- **Pros**: Team familiarity; rich graph patterns.
- **Cons**: Being replaced for the reasons documented in `high_level_architecture.md` (rigidity, poor scaling, no native streaming).
- **Risks**: Continued investment in a model we've already identified as limiting.

### Option B — Adopt AutoGen / CrewAI
- **Pros**: Pre-built multi-agent patterns; faster initial prototype.
- **Cons**: Foreign execution models; no native NATS/Event Bus integration; limited control over retry/timeout policies.
- **Risks**: Deep dependency on fast-moving open-source projects.

### Option C — Build lightweight runtime (asyncio) — chosen
- **Pros**: Full alignment with event-driven architecture. Thin layer. Easy to test. No external framework dependency.
- **Cons**: Must build and maintain (~2–3 weeks initial, ~0.5 FTE ongoing).
- **Risks**: Engineering effort; no community patterns to copy.

## Rationale

The Agent Runtime is the framework's core execution model. It must integrate tightly with NATS JetStream (Event Bus), the Evaluation Layer (reflection loops), and the Streaming Pipeline (chunk-framed protocol). No existing framework provides this integration. The cost of wrapping an external framework (adapting its execution model, working around its limitations) exceeds the cost of building a thin, purpose-built runtime.

## Consequences

**Easier:**
- Perfect alignment with the Event Bus and streaming protocol.
- Full control over lifecycle, concurrency, retries, and timeouts.
- Testing is straightforward (mock the Event Bus, inject test events).

**Harder:**
- Must implement and maintain: event consumption, retry logic, health probes, graceful shutdown, reflection loop orchestration.
- No community best practices to follow; must design lifecycle states and error handling from scratch.

## Follow-ups

- Define the `BaseAgent` interface and `AgentRuntime` class.
- Implement health probes (`/healthz`, `/readyz`).
- Implement retry policy (configurable exponential backoff with jitter).
- Implement reflection loop orchestration.
- Build idempotency deduplication layer (event_id cache in Redis).
- Implement Agent Registry lifecycle: register AgentSpec on startup, heartbeat, deregister on shutdown. See [ADR-0010](ADR-0010-agent-registry-agentspec.md).
- Write developer guide: "How to build a new agent" (including AgentSpec authoring).
