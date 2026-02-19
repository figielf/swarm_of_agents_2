# ADR-0010: Agent Registry and AgentSpec — NATS KV-backed Dynamic Discovery

- Status: Accepted
- Date: 2026-02-19
- Decision owners: Platform Architecture Team
- Related requirements: R2 (easy agent composition), R3 (horizontal scaling), R4 (multiple comm patterns)
- Related docs: [considerations/17](../considerations/17_agent_registry_and_discovery.md), [diagrams/01](../diagrams/01_overview.md), [glossary](../glossary.md)

## Context

The Coordinator Agent must discover available specialist agents and their capabilities at runtime without hard-coding. Agents are deployed independently as Kubernetes Deployments and may scale up/down or be added/removed at any time.

The framework needs:
1. A formal **AgentSpec** schema that declaratively describes every agent.
2. An **Agent Registry** that stores AgentSpec documents with registration, deregistration, and heartbeat operations.
3. A **Capability Registry** projection that maps capabilities to NATS subjects for task routing.

## Decision

- Define **AgentSpec** as a Pydantic model containing: identity (`agent_type`, `version`), capabilities (list of `AgentCapability`), routing (`nats_subject`, `consumer_group`, `supported_patterns`), runtime config (timeouts, retries, reflection), evaluators, tools, and ownership metadata.
- Store AgentSpecs in a **NATS JetStream KV bucket** (`agent-registry`) as the primary runtime registry. Async mirror to PostgreSQL for audit.
- Build the **Capability Registry** as a read-only projection rebuilt on every AgentSpec change.
- Agents register on startup, heartbeat every 30s, and deregister on graceful shutdown. Stale agents (missed 3 heartbeats) are auto-deregistered.
- The Coordinator **watches** the registry for changes and regenerates its planning prompt dynamically.

## Options considered

### Option A — Static configuration (YAML/Helm values)
- **Pros**: Simple; no runtime dependency.
- **Cons**: Requires redeployment to add/remove agents. No dynamic scaling awareness. Coordinator prompt is stale during rolling updates.
- **Risks**: Configuration drift between deployed agents and declared capabilities.

### Option B — NATS JetStream KV-backed dynamic registry — chosen
- **Pros**: Native to the Event Bus stack. Watch API enables real-time Coordinator updates. Built-in replication. Lightweight.
- **Cons**: Limited query capabilities vs. a database. Must build the Capability Registry projection.
- **Risks**: NATS KV availability is coupled to the Event Bus; mitigated by NATS cluster replication (factor 3).

### Option C — Dedicated service discovery (Consul, etcd)
- **Pros**: Feature-rich service discovery with health checking, DNS integration.
- **Cons**: Additional infrastructure component. Operational overhead. Not native to the NATS stack.
- **Risks**: Over-engineering for the current scale.

## Rationale

Option B aligns with the existing NATS JetStream stack (no new infrastructure), provides real-time change notifications, and is operationally simple. The Capability Registry projection is a lightweight in-memory structure rebuilt on change events.

## Consequences

**Easier:**
- Adding a new agent type is a declarative act: define an AgentSpec, deploy the agent, and it auto-registers.
- Coordinator prompt stays current as agents register/deregister.
- Multi-tenancy: tenant-scoped agents filter naturally through `tenant_scope` in the AgentSpec.
- A2A `AgentCard` generation can be derived from the AgentSpec.

**Harder:**
- Must implement the registration/heartbeat/deregistration lifecycle in the Agent Runtime.
- Must handle race conditions during rolling updates (old version deregisters, new version registers).
- Capability Registry must handle duplicate capabilities (two agents declaring the same capability) — use priority or error.

## Follow-ups

- Implement `AgentSpec` Pydantic model in the Agent Runtime SDK.
- Implement `AgentRegistry` client for NATS KV CRUD + watch.
- Implement `CapabilityRegistry` projection builder.
- Add registry lifecycle (register/heartbeat/deregister) to the Agent Runtime startup/shutdown hooks.
- Implement stale agent detection (missed heartbeat eviction).
- Update Coordinator Agent to watch the Capability Registry and regenerate its planning prompt.
- Add `registry.*` events to the event taxonomy schema registry.
- Mirror AgentSpec changes to PostgreSQL for audit queries.
- Document "How to add a new agent" developer guide referencing the AgentSpec schema.
