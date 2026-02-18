# ADR-0007: Observability and Replay — OpenTelemetry + Trajectory Store

- Status: Accepted
- Date: 2026-02-18
- Decision owners: Platform Architecture Team
- Related requirements: R8 (traceability + replay), R6 (evaluation/reflection loop results)
- Related docs: [considerations/09](../considerations/09_observability_tracing_replay.md)

## Context

Agentic systems are inherently non-deterministic. Debugging multi-agent interactions, reproducing failures, auditing decisions, and demonstrating governance compliance all require a robust observability and replay capability.

Three distinct observability concerns exist:
1. **Infrastructure observability**: standard metrics (CPU, memory, latency, error rates).
2. **Distributed tracing**: request flow across the Event Bus, agents, Tool Gateway, and Memory tiers.
3. **Trajectory replay**: ability to reconstruct the full decision chain of an agent interaction and replay it for debugging, evaluation, or regression testing.

## Decision

Adopt a layered observability strategy:

### Layer 1 — Metrics
**Prometheus** with **Grafana** dashboards. The Agent Runtime exports standard and agent-specific metrics (token usage, tool calls, evaluation scores, queue depth).

### Layer 2 — Distributed tracing
**OpenTelemetry** SDK integrated into the Agent Runtime and Tool Gateway. Traces propagated through NATS JetStream message headers (`traceparent`, `tracestate`). Trace export via OTLP to a collector (Jaeger/Tempo backend).

### Layer 3 — Trajectory Store
A **dedicated append-only table in PostgreSQL** that captures every event in an agent interaction: incoming trigger, LLM calls (request + response), tool invocations, evaluation results, delegation events, and final outputs.

**Replay** is supported in three modes:
- **Read-only replay**: reconstruct the full trajectory from the store.
- **Deterministic replay**: re-inject stored events into a test harness to reproduce an exact execution.
- **Counterfactual replay**: re-run the trajectory with a different prompt version, model, or evaluator to compare outcomes.

## Options considered

### Option A — OpenTelemetry only (no Trajectory Store)
- **Pros**: Simplicity. Industry standard.
- **Cons**: OTEL traces are not designed for full LLM response storage; span payloads are size-limited. No support for counterfactual replay.
- **Risks**: Insufficient for governance audits.

### Option B — OpenTelemetry + Trajectory Store — chosen
- **Pros**: OTEL handles infrastructure tracing; Trajectory Store handles agent-specific deep replay. Full audit trail for governance.
- **Cons**: Two systems to maintain.
- **Risks**: Trajectory Store growth; mitigated by TTL-based archival.

### Option C — Third-party LLM observability platform (LangSmith, Helicone)
- **Pros**: Pre-built dashboards. Quick to start.
- **Cons**: Data privacy. Vendor lock-in. Cost at scale.
- **Risks**: Not acceptable for enterprise e-commerce data.

## Rationale

OpenTelemetry is the industry standard for distributed tracing and integrates with all our infrastructure components (NATS, Redis, PostgreSQL, Kubernetes). However, agentic workloads require storing full LLM payloads (prompts, responses, tool call arguments) and supporting replay — capabilities beyond OTEL's design.

The Trajectory Store complements OTEL by providing an agent-specific audit log. It shares the PostgreSQL instance with the long-term memory tier, minimizing operational overhead.

## Consequences

**Easier:**
- Full request tracing across Event Bus, agents, tools, and memory.
- Governance audit trails.
- Regression testing via counterfactual replay.
- Cost tracking per agent/model/task.

**Harder:**
- Must implement Trajectory Store write path in Agent Runtime (every event must be captured).
- Must implement TTL-based archival and partitioning for Trajectory Store growth.
- Teams must adopt structured logging conventions.

## Follow-ups

- Implement `TrajectoryWriter` in Agent Runtime SDK.
- Define Trajectory Store SQL schema (see [considerations/09](../considerations/09_observability_tracing_replay.md)).
- Build replay CLI tool supporting three replay modes.
- Integrate OpenTelemetry SDK into Agent Runtime and Tool Gateway.
- Configure OTEL collector → Jaeger/Tempo pipeline.
- Build Grafana dashboards for agent-specific metrics.
- Define data retention and archival policy for Trajectory Store.
