# High-level architecture — Event-Driven Agentic Swarm Framework (E-commerce)

> This file is the executive summary. Deep dives live in `design/considerations/` and decisions in `design/adr/`.

## 1. Motivation and problem statement

### 1.1 Why move beyond the previous LangGraph “static workflow graph” approach?
**Limitations observed in static graph workflows (with conditional edges):**
- TODO: List concrete limitations (rigidity, graph sprawl, limited dynamism, brittle condition logic, poor decoupling, etc.)
- TODO: Explain why event-driven / asynchronous designs reduce coupling and improve scaling.

### 1.2 Target outcomes
- Production-grade event-driven multi-agent framework for e-commerce products.
- Easy for product teams to compose agent swarms from shared “platform agents”.
- Supports both coordinator-driven and leaderless collaboration modes.

## 2. Architecture overview

### 2.1 Key components
- **Agent Runtime** (Python-first): lifecycle, concurrency, retries, timeouts.
- **Event Bus**: pub/sub backbone for inter-agent messaging.
- **Message Contracts**: schemas, versioning, validation, governance.
- **Shared Memory**:
  - short-term (session),
  - long-term (cross-session),
  - specialized stores (vector/graph/relational) behind tools.
- **Tool Gateway**: consistent tool calling, permissions, audit.
- **Evaluation Layer**: per-agent and system-level evaluation, reflection loops.
- **Trajectory Store**: full message/event history + replay support.
- **Observability**: tracing, metrics, logs, cost tracking.
- **Protocol Gateway**: wrappers for MCP/A2A and other interop.

### 2.2 Architecture diagram
See: `design/diagrams/01_overview.md`

## 3. Communication patterns: coordinator vs leaderless swarm vs hybrid

### 3.1 Coordinator / orchestrator-managed collaboration
- When it fits (structured workflows, routing, control, compliance).
- Risks (bottlenecks, coupling, model-call amplification).
- See: `design/considerations/01_communication_patterns.md`

### 3.2 Leaderless / swarm collaboration
- When it fits (ambiguous problems, debate, creative synthesis).
- Risks (non-convergence, unbounded chatter, cost).
- Requires explicit exit conditions.
- See: `design/considerations/01_communication_patterns.md`

### 3.3 Hybrid model (recommended)
- TODO: Provide final recommended hybrid approach and link to ADR(s).

## 4. Streaming + multimodal-ready response pipeline

- Explicit **chunk begin/end markers**
- Ordering & correlation IDs
- Partial aggregation rules
- See: `design/considerations/05_streaming_chunking_and_multimodal_sync.md`

## 5. Evaluation, reflection, and guardrails

- Built-in evaluation hooks at:
  - tool-call boundaries,
  - agent output boundaries,
  - system-level final response boundaries.
- Planning–reflection loops with parameterization.
- See: `design/considerations/08_evaluation_reflection_and_guardrails.md`

## 6. Replayability and observability

- Full event log + trace correlation across agents
- Deterministic replay where possible; best-effort replay otherwise
- See: `design/considerations/09_observability_tracing_replay.md`

## 7. Conclusions and recommendations

### 7.1 Final recommendations (must link to ADRs)
- TODO: Summarize final decisions with links to ADRs.

### 7.2 Next steps
- TODO: Outline an incremental roadmap: PoC -> pilot -> production hardening.

