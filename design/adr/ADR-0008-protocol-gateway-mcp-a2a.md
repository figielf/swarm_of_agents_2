# ADR-0008: Protocol Gateway for MCP and A2A — Centralized Adapter Service

- Status: Accepted
- Date: 2026-02-18
- Decision owners: Platform Architecture Team
- Related requirements: R10 (MCP/A2A gateway support)
- Related docs: [considerations/14](../considerations/14_protocol_wrappers_mcp_a2a.md)

## Context

The framework must interoperate with external systems through two emerging protocols:
- **Model Context Protocol (MCP)**: Anthropic's standard for connecting LLMs to external tools and data sources.
- **Agent-to-Agent Protocol (A2A)**: Google's standard for inter-agent communication across organizational boundaries.

Internal agents communicate via the Event Bus (NATS JetStream) using the framework's native event schema. External interactions must be translated at the boundary so that internal agents remain protocol-agnostic.

## Decision

Deploy a **centralized Protocol Gateway** service that:
1. Terminates MCP and A2A connections from external clients.
2. Translates inbound protocol messages into the framework's native event schema and publishes them to the Event Bus.
3. Translates outbound events into the appropriate protocol response format.
4. Enforces authentication, authorization, rate limiting, and payload validation at the boundary.

The Protocol Gateway exposes:
- **MCP endpoint** (`/mcp`): JSON-RPC 2.0 over HTTP+SSE, supporting `tools/list`, `tools/call`, `resources/read`, and `prompts/get`.
- **A2A endpoint** (`/a2a`): JSON-RPC 2.0 over HTTP, supporting `tasks/send`, `tasks/get`, `tasks/cancel`, and streaming via SSE.

Adapters implement a common `ProtocolAdapter` interface:
```python
class ProtocolAdapter(ABC):
    async def translate_inbound(self, raw: dict) -> EventEnvelope: ...
    async def translate_outbound(self, event: EventEnvelope) -> dict: ...
    async def capabilities(self) -> dict: ...
```

## Options considered

### Option A — Sidecar adapters per agent
- **Pros**: Decentralized. Agent-specific protocol handling.
- **Cons**: Duplicated logic. Inconsistent security enforcement. Harder to audit.
- **Risks**: Protocol version drift across agents.

### Option B — Centralized Protocol Gateway — chosen
- **Pros**: Single point of protocol enforcement. Consistent security. Easy to upgrade when MCP/A2A specs evolve.
- **Cons**: Single point of failure; mitigated by replication.
- **Risks**: Latency overhead (~2–5ms per translation).

### Option C — Direct protocol support in Agent Runtime
- **Pros**: Lowest latency.
- **Cons**: Protocol coupling in every agent. Massive maintenance burden when specs evolve.
- **Risks**: Unacceptable — violates protocol-agnostic agent design.

## Rationale

Centralization is the right trade-off for protocol boundary concerns:
1. **Security**: authentication, authorization, rate limiting, and input validation must be enforced consistently at a single point.
2. **Evolvability**: MCP and A2A specs are rapidly evolving (~monthly updates). A centralized gateway minimizes the blast radius of spec changes.
3. **Agent simplicity**: internal agents should not carry protocol translation logic. They publish and consume native events only.

The ~2–5ms translation latency is acceptable given our end-to-end SLO (p95 < 2s for simple tasks).

## Consequences

**Easier:**
- Internal agents remain fully protocol-agnostic.
- Single place to add new protocol support (future standards).
- Centralized security and compliance enforcement for external interactions.
- Protocol spec version upgrades affect only the Gateway.

**Harder:**
- Must build and maintain the Gateway service (HTTP server, SSE streaming, protocol adapters).
- Must ensure high availability (replicated deployment, health checks, auto-restart).
- Gateway capacity planning must account for peak external protocol traffic.

## Follow-ups

- Implement `ProtocolGateway` HTTP service with `/mcp` and `/a2a` endpoints.
- Implement `MCPAdapter` for MCP JSON-RPC 2.0.
- Implement `A2AAdapter` for A2A JSON-RPC 2.0 with SSE streaming.
- Implement `AgentCard` endpoint for A2A agent discovery.
- Configure mutual TLS for external A2A federation.
- Define rate limiting and authentication policies for external callers.
- Add Protocol Gateway to the Kubernetes deployment (replicated, with HPA).
