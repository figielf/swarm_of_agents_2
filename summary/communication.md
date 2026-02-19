# Communication Patterns & Integration Paths

This document covers all communication in the framework: how agents collaborate with each other, how they invoke tools, how they reach external systems, and how responses stream back to users.

The **hybrid model** (Coordinator-first with swarm delegation) is the recommended default.

---

## Part 1 — Agent-to-Agent Collaboration Patterns

### 1.1 Coordinator / Orchestrator

A central **Coordinator Agent** plans execution, delegates sub-tasks to **Specialist Agents** via the **Event Bus**, and synthesizes results.

**When to use:** Structured workflows with well-defined steps (search → filter → recommend → checkout), compliance-sensitive flows, deterministic cost budgets.

```mermaid
flowchart TD
  U[User] --> C[Coordinator Agent]
  C --> EB[(Event Bus)]
  EB --> A1[Specialist Agent A]
  EB --> A2[Specialist Agent B]
  A1 --> EB
  A2 --> EB
  EB --> C
  C --> E[Evaluation Layer]
  E --> C
  C --> U
```

```mermaid
sequenceDiagram
  autonumber
  participant User
  participant Coord as Coordinator Agent
  participant Bus as Event Bus
  participant A1 as Specialist Agent A
  participant A2 as Specialist Agent B
  participant Eval as Evaluation Layer

  User->>Coord: User request
  Coord->>Bus: Publish Task(A)
  Coord->>Bus: Publish Task(B)
  Bus-->>A1: Task(A)
  Bus-->>A2: Task(B)
  A1->>Bus: Result(A)
  A2->>Bus: Result(B)
  Coord->>Eval: Synthesize + Evaluate
  Eval-->>Coord: Pass/Fail + feedback
  Coord-->>User: Response (stream)
```

**Risks:** Coordinator bottleneck; every interaction doubles LLM calls.
**Mitigations:** Stateless Coordinator with Event Bus-backed state recovery. Coordinator prompt auto-generated from **Capability Registry**.

---

### 1.2 Leaderless Swarm (Broadcast + Peer Collaboration)

A Dispatcher broadcasts a task to all participating agents. Agents collaborate via peer messages on the Event Bus and the **Blackboard** (Shared Memory). A Finalizer assembles the response.

**When to use:** Ambiguous problems requiring multi-perspective debate, creative synthesis, resilience-critical paths.

```mermaid
flowchart TD
  U[User] --> D[Dispatcher]
  D --> EB[(Event Bus)]
  EB --> A[Agent A]
  EB --> B[Agent B]
  EB --> C[Agent C]
  A <--> B
  B <--> C
  A <--> C
  A -->|writes| SM[(Blackboard)]
  B -->|reads/writes| SM
  C -->|reads/writes| SM
  C --> F[Finalizer]
  F --> U
```

```mermaid
sequenceDiagram
  autonumber
  participant User
  participant Disp as Dispatcher
  participant Bus as Event Bus
  participant A as Agent A
  participant B as Agent B
  participant C as Agent C
  participant SM as Blackboard
  participant F as Finalizer

  User->>Disp: User request
  Disp->>Bus: Publish TaskBroadcast
  Bus-->>A: TaskBroadcast
  Bus-->>B: TaskBroadcast
  Bus-->>C: TaskBroadcast

  par Peer collaboration
    A->>Bus: Msg(A→B/C)
    B->>Bus: Msg(B→A/C)
    C->>Bus: Msg(C→A/B)
  end

  A->>SM: Write intermediate findings
  B->>SM: Read/write intermediate findings
  C->>SM: Read/write intermediate findings

  C->>F: Candidate answer
  F-->>User: Response (stream)
```

**Risks:** Non-convergence; unbounded chatter; cost unpredictability.
**Mitigations:** Turn limits and message-count budgets (**Agent Runtime**). Convergence detectors. Per-session token **Budget Envelopes** enforced at Event Bus level.

---

### 1.3 Blackboard / Shared Memory

Opportunistic agents post observations to a shared store; other agents react to updates. Used for progressive knowledge assembly without direct orchestration (**Stigmergy**).

```mermaid
flowchart LR
  BB[(Blackboard)]
  A1[Agent 1] -->|post| BB
  A2[Agent 2] -->|post| BB
  A3[Agent 3] -->|post| BB
  BB -->|notify + read| A1
  BB -->|notify + read| A2
  BB -->|notify + read| A3
```

---

### 1.4 Market-Based (Auction / Bidding)

An auctioneer broadcasts a task; agents bid based on confidence, cost, or capability. The winning agent executes.

**When to use:** Dynamic routing when agent capabilities overlap; optimize for cost, latency, or confidence.

```mermaid
flowchart TD
  R[Request Source] --> Auction[Auctioneer]
  Auction -->|request bids| A[Agent A]
  Auction -->|request bids| B[Agent B]
  Auction -->|request bids| C[Agent C]
  A -->|bid| Auction
  B -->|bid| Auction
  C -->|bid| Auction
  Auction -->|assign task| W[Winning Agent]
  W -->|result| Auction
  Auction --> R
```

---

### 1.5 Hybrid Model (Recommended)

**Coordinator-first, swarm-when-needed.**

- Default to Coordinator-managed flows for predictable workflows.
- Coordinators may **delegate sub-problems** to leaderless swarms when multi-perspective synthesis is needed.
- The Coordinator sets a **Budget Envelope** (max tokens, max turns, timeout) for any swarm delegation.

**Routing mechanism:** The Coordinator does not hard-code specialist references. Instead:

1. **Capability Registry lookup** — maps capability names → NATS subjects.
2. **LLM-driven planning** — the LLM receives user intent + capability list, decomposes into sub-tasks tagged with `target_capability`.

```mermaid
sequenceDiagram
  autonumber
  participant Coord as Coordinator Agent
  participant Reg as Capability Registry
  participant Bus as Event Bus
  participant PA1 as ProductAgent replica 1
  participant PA2 as ProductAgent replica 2
  participant OA as OrderAgent

  Coord->>Coord: LLM plans sub-tasks from user intent
  Coord->>Reg: Lookup capability → subject
  Reg-->>Coord: product.search → tasks.product, order.status → tasks.order

  Coord->>Bus: task.delegated → "tasks.product"
  Coord->>Bus: task.delegated → "tasks.order"

  Note over Bus: Queue group delivers to one replica
  Bus-->>PA1: task.delegated (product.search)
  Note over PA2: PA2 idle — not selected

  Bus-->>OA: task.delegated (order.status)

  PA1->>Bus: task.completed (product results)
  OA->>Bus: task.completed (order status)

  Bus-->>Coord: task.completed (product results)
  Bus-->>Coord: task.completed (order status)
  Coord->>Coord: Synthesize final response
```

Specialist agents subscribe via NATS JetStream **queue groups** — exactly one replica picks up each message, providing automatic load balancing. In swarm mode, tasks are published to a **broadcast subject** without a queue group so every agent receives every message.

---

## Part 2 — Tool Invocation & External Integration Paths

**Key distinction:**
- **Tool Gateway** — governance layer for all tool calls (authZ, rate limits, idempotency, audit).
- **Protocol Gateway** — wire-format translator for external protocols (MCP, A2A). Internal agents never see these protocols.

### 2.1 Agent → Internal Tool (Tool Gateway only)

Tool calls to platform-owned APIs pass through the **Tool Gateway** for governance. No Protocol Gateway involved.

```mermaid
sequenceDiagram
  autonumber
  participant SA as Agent
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

  Note over SA,API: Tool Gateway only — no Protocol Gateway
```

---

### 2.2 Agent → External MCP Tool (Tool Gateway + Protocol Gateway)

When a tool is backed by an external MCP server, the request flows through **both** gateways in sequence:
- **Tool Gateway** handles governance (authZ, rate limits, audit)
- **Protocol Gateway** handles wire-format translation (MCP)

```mermaid
sequenceDiagram
  autonumber
  participant SA as Agent
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

  Note over TG,PGW: Tool Gateway = governance<br/>Protocol Gateway = wire-format translation
```

---

### 2.3 Agent ↔ External A2A Agent (Protocol Gateway only, NO Tool Gateway)

Agent-to-agent delegation to an external agent uses only the **Protocol Gateway**. This is agent delegation, not a tool call — the Tool Gateway is **not** involved.

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

  Note over Coord,EA: NO Tool Gateway —<br/>Protocol Gateway only
```

---

## Part 3 — Streaming Protocol

All communication paths deliver responses using the **Chunk-framed Protocol**:

```mermaid
sequenceDiagram
  autonumber
  participant Agent
  participant Bus as Event Bus
  participant UI as Channel / UI

  Agent->>Bus: stream.begin (message_id, modality=text)
  loop N chunks (N ≥ 1)
    Agent->>Bus: stream.chunk (seq_no, payload)
    Bus-->>UI: Forward chunk
  end
  Agent->>Bus: stream.end (checksum, final=true)
  Note over UI: Single message = N=1 (Begin + Chunk + End)
```

Multimodal responses use the same `message_id` with different `modality` tags (text, image, carousel). The UI aligns rendering by `(message_id, modality, seq_no)`.

---

## Gateway Involvement Summary

| Communication Path | Event Bus | Tool Gateway | Protocol Gateway |
|---|:---:|:---:|:---:|
| **Agent → Agent** (internal) | ✅ | — | — |
| **Agent → Internal Tool** | ✅ | ✅ | — |
| **Agent → External API Tool** (non-MCP) | ✅ | ✅ | — |
| **Agent → External MCP Tool** | ✅ | ✅ | ✅ |
| **Agent → External A2A Agent** | ✅ | — | ✅ |
