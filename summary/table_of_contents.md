# Architecture Summary — Table of Contents

This summary covers the **Event-Driven Agentic Swarm Framework** for enterprise e-commerce.
Each document is written for a project management audience and is self-contained.

---

## Documents

| # | Document | Description |
|---|----------|-------------|
| 1 | [High-Level Architecture](high_level_architecture.md) | Problem statement, key components, architecture diagram, end-to-end flows, roadmap |
| 2 | [Communication Patterns & Integration Paths](communication.md) | Agent collaboration patterns, tool invocation paths, streaming protocol |
| 3 | [Components Considerations](components_considerations.md) | Per-component architectural decisions (event taxonomy through agent registry) |
| 4 | [Buy vs Build — Stack Selection](buy_vs_build_consideration.md) | Build-or-buy analysis for every major infrastructure component |
| 5 | [Glossary](glossary.md) | Canonical vocabulary used across all documents |

---

## Detailed Contents

### 1. [High-Level Architecture](high_level_architecture.md)

- [1. Problem Statement](high_level_architecture.md#1-problem-statement)
- [2. Target Outcomes](high_level_architecture.md#2-target-outcomes)
- [3. Key Components](high_level_architecture.md#3-key-components)
- [4. Architecture Diagram](high_level_architecture.md#4-architecture-diagram)
- [5. End-to-End Request Flow](high_level_architecture.md#5-end-to-end-request-flow)
- [6. Task Routing — How the Coordinator Finds Specialists](high_level_architecture.md#6-task-routing--how-the-coordinator-finds-specialists)
- [7. Communication Pattern: Hybrid Model](high_level_architecture.md#7-communication-pattern-hybrid-model)
- [8. Streaming Protocol](high_level_architecture.md#8-streaming-protocol)
- [9. Evaluation & Guardrails](high_level_architecture.md#9-evaluation--guardrails)
- [10. Observability & Replay](high_level_architecture.md#10-observability--replay)
- [11. Security & Compliance](high_level_architecture.md#11-security--compliance)
- [12. Incremental Roadmap](high_level_architecture.md#12-incremental-roadmap)
- [13. Key Decisions Summary](high_level_architecture.md#13-key-decisions-summary)
- [Reading List](high_level_architecture.md#reading-list)

---

### 2. [Communication Patterns & Integration Paths](communication.md)

**Part 1 — Agent-to-Agent Collaboration Patterns**
- [1.1 Coordinator / Orchestrator](communication.md#11-coordinator--orchestrator)
- [1.2 Leaderless Swarm (Broadcast + Peer Collaboration)](communication.md#12-leaderless-swarm-broadcast--peer-collaboration)
- [1.3 Blackboard / Shared Memory](communication.md#13-blackboard--shared-memory)
- [1.4 Market-Based (Auction / Bidding)](communication.md#14-market-based-auction--bidding)
- [1.5 Hybrid Model (Recommended)](communication.md#15-hybrid-model-recommended)

**Part 2 — Tool Invocation & External Integration Paths**
- [2.1 Agent → Internal Tool (Tool Gateway only)](communication.md#21-agent--internal-tool-tool-gateway-only)
- [2.2 Agent → External MCP Tool (Tool Gateway + Protocol Gateway)](communication.md#22-agent--external-mcp-tool-tool-gateway--protocol-gateway)
- [2.3 Agent ↔ External A2A Agent (Protocol Gateway only)](communication.md#23-agent--external-a2a-agent-protocol-gateway-only-no-tool-gateway)

**Part 3 — Streaming Protocol**
- [Chunk-Framed Streaming](communication.md#part-3--streaming-protocol)
- [Gateway Involvement Summary](communication.md#gateway-involvement-summary)

---

### 3. [Components Considerations](components_considerations.md)

- [1. Event Taxonomy](components_considerations.md#1-event-taxonomy)
- [2. Agent Runtime & Lifecycle](components_considerations.md#2-agent-runtime--lifecycle)
- [3. Message Schema & Contracts](components_considerations.md#3-message-schema--contracts)
- [4. Streaming, Chunking & Multimodal Sync](components_considerations.md#4-streaming-chunking--multimodal-sync)
- [5. Memory Architecture & Shared State](components_considerations.md#5-memory-architecture--shared-state)
- [6. Tooling & Integrations (Tool Gateway)](components_considerations.md#6-tooling--integrations-tool-gateway)
- [7. Evaluation, Reflection & Guardrails](components_considerations.md#7-evaluation-reflection--guardrails)
- [8. Observability, Tracing & Replay](components_considerations.md#8-observability-tracing--replay)
- [9. Scaling, Deployment & Isolation](components_considerations.md#9-scaling-deployment--isolation)
- [10. Security, Privacy & Compliance](components_considerations.md#10-security-privacy--compliance)
- [11. Prompt Management & Versioning](components_considerations.md#11-prompt-management--versioning)
- [12. Protocol Wrappers (MCP / A2A)](components_considerations.md#12-protocol-wrappers-mcp--a2a)
- [13. Testing, Simulation & Load](components_considerations.md#13-testing-simulation--load)
- [14. Cost, Latency & SLOs](components_considerations.md#14-cost-latency--slos)
- [15. Agent Registry & Discovery](components_considerations.md#15-agent-registry--discovery)

---

### 4. [Buy vs Build — Stack Selection](buy_vs_build_consideration.md)

- [Decision Drivers](buy_vs_build_consideration.md#decision-drivers)
- [Event Bus — BUY → NATS JetStream](buy_vs_build_consideration.md#event-bus--buy--nats-jetstream)
- [Agent Runtime — BUILD → Python asyncio](buy_vs_build_consideration.md#agent-runtime--build--python-asyncio)
- [Session Memory — BUY → Redis](buy_vs_build_consideration.md#session-memory--buy--redis)
- [Long-term Memory — BUY → PostgreSQL + pgvector](buy_vs_build_consideration.md#long-term-memory--buy--postgresql--pgvector)
- [Observability — BUY → OpenTelemetry stack](buy_vs_build_consideration.md#observability--buy--opentelemetry-stack)
- [Evaluation Layer — BUILD → Python framework](buy_vs_build_consideration.md#evaluation-layer--build--python-framework)
- [Protocol Gateway — BUILD (thin adapters) + BUY (SDKs)](buy_vs_build_consideration.md#protocol-gateway--build-thin-adapters--buy-sdks)
- [Trajectory Store — BUILD (schema) + BUY (PostgreSQL)](buy_vs_build_consideration.md#trajectory-store--build-schema--buy-postgresql)
- [Prompt Registry — BUILD → Git-based service](buy_vs_build_consideration.md#prompt-registry--build--git-based-service)
- [Decision Summary](buy_vs_build_consideration.md#decision-summary)

---

### 5. [Glossary](glossary.md)

Canonical definitions for: Agent, AgentSpec, Agent Registry, Agent Runtime, Agent Capability, Blackboard, Budget Envelope, Capability Registry, Channel Gateway, Chunk-framed Protocol, Coordinator Agent, Evaluation Layer, Event Bus, Event Envelope, Long-term Memory, Prompt Registry, Protocol Gateway, Reflection Loop, Session Memory, Shared Memory, Specialist Agent, Stigmergy, Tool Gateway, Trajectory, Trajectory Store.
