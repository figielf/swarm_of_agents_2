# Diagram: Tool Invocation & Gateway Paths

This document focuses on **tool invocation and external integration paths**, clarifying when the Tool Gateway and Protocol Gateway are involved. For internal agent-to-agent communication patterns, see [02_patterns.md](02_patterns.md).

Each path is documented with two complementary views:
- **DataFlow** diagram (Mermaid `flowchart`) showing structural data movement.
- **Activity** diagram (Mermaid `sequenceDiagram`) showing message/event ordering.

Sources: [high_level_architecture.md](../high_level_architecture.md), [07_tooling_and_integrations.md](../considerations/07_tooling_and_integrations.md), [14_protocol_wrappers_mcp_a2a.md](../considerations/14_protocol_wrappers_mcp_a2a.md)

**Key distinction:**
- **Tool Gateway** — governance layer for all tool calls (authZ, rate limits, idempotency, audit).
- **Protocol Gateway** — wire-format translator for external protocols (MCP, A2A). Internal agents never see these protocols.

---

## 1. Overview

### DataFlow

```mermaid
flowchart TD
  subgraph Platform["Agentic Swarm Platform"]
    SA[Agent]
    EB[(Event Bus\nNATS JetStream)]
    TG[Tool Gateway]
    PGW[Protocol Gateway\nMCP / A2A]
  end

  subgraph External["External Systems"]
    IAPI[Internal API\ne.g., Product Catalog]
    EAPI[External API\ne.g., Payment Provider]
    EMCP[External MCP Tool Server]
    EA2A[External A2A Agent]
  end

  %% Agent → Internal/External tool (Tool Gateway)
  SA -->|tool.call.requested| TG
  TG -->|direct call| IAPI
  TG -->|direct call| EAPI

  %% Agent → External MCP tool (Tool Gateway + Protocol Gateway)
  TG -->|MCP-backed tool| PGW
  PGW -->|MCP tools/call| EMCP
  EMCP -->|MCP response| PGW
  PGW -->|translated result| TG
  TG -->|tool.call.completed| SA

  %% Agent ↔ External A2A agent (Event Bus + Protocol Gateway)
  SA -->|protocol.a2a.request| EB
  EB --> PGW
  PGW -->|A2A task delegation| EA2A
  EA2A -->|A2A result| PGW
  PGW -->|protocol.a2a.response| EB
  EB --> SA
```

---

## 2. Agent → Internal Tool (Tool Gateway only)

  B1->>B1: Process event
  B1->>Bus: Publish reply event
  Bus-->>A: reply event

---

## 2. Agent → Internal Tool (Tool Gateway only)

Tool calls to platform-owned APIs pass through the Tool Gateway for governance. No Protocol Gateway involved.

### DataFlow

```mermaid
flowchart LR
  SA[Specialist Agent] -->|tool.call.requested| TG[Tool Gateway]
  TG -->|validate authZ\nrate limit\nidempotency check| TG
  TG -->|HTTP / gRPC| API[Internal API\ne.g., Product Catalog]
  API -->|response| TG
  TG -->|tool.call.completed| SA
  TG -->|append| TS[(Trajectory Store)]
```

### Activity

```mermaid
sequenceDiagram
  autonumber
  participant SA as Specialist Agent
  participant Bus as Event Bus
  participant TG as Tool Gateway
  participant API as Internal API (Product Catalog)
  participant TS as Trajectory Store

  SA->>Bus: Publish tool.call.requested
  Bus-->>TG: tool.call.requested

  TG->>TG: Validate authZ (role check)
  TG->>TG: Rate limit check (token bucket)
  TG->>TG: Idempotency check (Redis)

  TG->>API: HTTP GET /products?q=jacket
  API-->>TG: 200 OK (product list)

  TG->>TS: Append tool.invoked + tool.result
  TG->>Bus: Publish tool.call.completed
  Bus-->>SA: tool.call.completed (product list)

  Note over SA,API: Tool Gateway only —<br/>no Protocol Gateway needed
```

---

## 3. Agent → External Tool via MCP (Tool Gateway + Protocol Gateway)

When a tool is backed by an external MCP server, the request flows through **both** gateways in sequence.

### DataFlow

```mermaid
flowchart LR
  SA[Specialist Agent] -->|tool.call.requested| TG[Tool Gateway]
  TG -->|validate authZ\nrate limit\nidempotency| TG
  TG -->|MCP-backed tool| PGW[Protocol Gateway]
  PGW -->|MCP tools/call| EMCP[External MCP Server]
  EMCP -->|MCP response| PGW
  PGW -->|translated result| TG
  TG -->|tool.call.completed| SA
  TG -->|append| TS[(Trajectory Store)]
```

### Activity

```mermaid
sequenceDiagram
  autonumber
  participant SA as Specialist Agent
  participant Bus as Event Bus
  participant TG as Tool Gateway
  participant PGW as Protocol Gateway
  participant EMCP as External MCP Server
  participant TS as Trajectory Store

  SA->>Bus: Publish tool.call.requested
  Bus-->>TG: tool.call.requested

  TG->>TG: Validate authZ + rate limit
  TG->>TG: Detect tool is MCP-backed

  TG->>PGW: Forward tool invocation
  PGW->>PGW: Translate to MCP tools/call
  PGW->>PGW: Strip PII from outbound payload
  PGW->>EMCP: MCP tools/call (external network)
  EMCP-->>PGW: MCP tool result
  PGW->>PGW: Sanitize inbound response
  PGW->>PGW: Translate MCP response → Event Envelope
  PGW-->>TG: Translated tool result

  TG->>TS: Append tool.invoked + tool.result
  TG->>Bus: Publish tool.call.completed
  Bus-->>SA: tool.call.completed

  Note over TG,PGW: Tool Gateway = governance (authZ, rate limit, audit)<br/>Protocol Gateway = wire-format translation (MCP)
```

---

## 4. Agent ↔ External Agent via A2A (Event Bus + Protocol Gateway, NO Tool Gateway)

Agent-to-agent delegation to an external agent uses only the Protocol Gateway. The Tool Gateway is **not** involved — this is agent delegation, not a tool call.

### DataFlow

```mermaid
flowchart LR
  COORD[Coordinator Agent] -->|protocol.a2a.request| EB[(Event Bus)]
  EB --> PGW[Protocol Gateway]
  PGW -->|A2A task delegation| EA[External A2A Agent]
  EA -->|A2A result| PGW
  PGW -->|protocol.a2a.response| EB
  EB --> COORD
```

### Activity

```mermaid
sequenceDiagram
  autonumber
  participant Coord as Coordinator Agent
  participant Bus as Event Bus
  participant PGW as Protocol Gateway
  participant EA as External A2A Agent
  participant TS as Trajectory Store

  Coord->>Bus: Publish protocol.a2a.request (task delegation)
  Bus-->>PGW: protocol.a2a.request

  PGW->>PGW: Translate Event Envelope → A2A task format
  PGW->>PGW: Strip PII from outbound payload
  PGW->>PGW: Attach OAuth2 credentials
  PGW->>EA: A2A task delegation (external network)

  EA-->>PGW: A2A task result
  PGW->>PGW: Sanitize inbound response
  PGW->>PGW: Translate A2A result → Event Envelope

  PGW->>TS: Append protocol.a2a.request + response
  PGW->>Bus: Publish protocol.a2a.response
  Bus-->>Coord: protocol.a2a.response (result)

  Note over Coord,EA: NO Tool Gateway —<br/>Protocol Gateway only (agent delegation, not tool call)
```

---

## Summary: Which gateway is involved?

| Communication Path | Event Bus | Tool Gateway | Protocol Gateway |
|---|:---:|:---:|:---:|
| **Agent → Agent** (internal) | ✅ | — | — |
| **Agent → Internal Tool** | ✅ | ✅ | — |
| **Agent → External API Tool** (non-MCP) | ✅ | ✅ | — |
| **Agent → External MCP Tool** | ✅ | ✅ | ✅ |
| **Agent → External A2A Agent** | ✅ | — | ✅ |
