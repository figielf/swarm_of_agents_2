# Design Documentation Index

This folder contains the architecture design for the **event-driven agentic swarm framework** for enterprise e-commerce.

## Entry point

- [high_level_architecture.md](high_level_architecture.md) — Executive summary, key decisions, component overview, and incremental roadmap.

## Subfolders

| Folder | Purpose |
|--------|---------|
| [considerations/](considerations/) | Deep-dive trade-off analyses for each architectural concern |
| [adr/](adr/) | Architecture Decision Records — one per major decision |
| [diagrams/](diagrams/) | Mermaid diagrams (DataFlow + Activity per topic) |
| [references/](references/) | Curated reading list and external references |

## Completion checklist

- [x] `high_level_architecture.md` completed
- [x] All `considerations/*.md` completed (16 files)
- [x] ADRs created for all major decisions (9 ADRs)
- [x] Diagrams updated and consistent with text (3 files, each with DataFlow + Activity)
- [x] Glossary updated with all canonical terms
- [x] Open questions tracked (see below)

## Considerations

| # | Topic | File |
|---|-------|------|
| 01 | Communication Patterns | [01_communication_patterns.md](considerations/01_communication_patterns.md) |
| 02 | Event Taxonomy | [02_event_taxonomy.md](considerations/02_event_taxonomy.md) |
| 03 | Agent Runtime & Lifecycle | [03_agent_runtime_and_lifecycle.md](considerations/03_agent_runtime_and_lifecycle.md) |
| 04 | Message Schema & Contracts | [04_message_schema_and_contracts.md](considerations/04_message_schema_and_contracts.md) |
| 05 | Streaming, Chunking & Multimodal Sync | [05_streaming_chunking_and_multimodal_sync.md](considerations/05_streaming_chunking_and_multimodal_sync.md) |
| 06 | Memory Architecture & Shared State | [06_memory_architecture_shared_state.md](considerations/06_memory_architecture_shared_state.md) |
| 07 | Tooling & Integrations | [07_tooling_and_integrations.md](considerations/07_tooling_and_integrations.md) |
| 08 | Evaluation, Reflection & Guardrails | [08_evaluation_reflection_and_guardrails.md](considerations/08_evaluation_reflection_and_guardrails.md) |
| 09 | Observability, Tracing & Replay | [09_observability_tracing_replay.md](considerations/09_observability_tracing_replay.md) |
| 10 | Scaling, Deployment & Isolation | [10_scaling_deployment_and_isolation.md](considerations/10_scaling_deployment_and_isolation.md) |
| 11 | Security, Privacy & Compliance | [11_security_privacy_compliance.md](considerations/11_security_privacy_compliance.md) |
| 12 | Buy vs Build & Stack Selection | [12_buy_vs_build_stack_selection.md](considerations/12_buy_vs_build_stack_selection.md) |
| 13 | Prompt Management & Versioning | [13_prompt_management_and_versioning.md](considerations/13_prompt_management_and_versioning.md) |
| 14 | Protocol Wrappers (MCP / A2A) | [14_protocol_wrappers_mcp_a2a.md](considerations/14_protocol_wrappers_mcp_a2a.md) |
| 15 | Testing, Simulation & Load | [15_testing_simulation_and_load.md](considerations/15_testing_simulation_and_load.md) |
| 16 | Cost, Latency & SLOs | [16_cost_latency_and_slo.md](considerations/16_cost_latency_and_slo.md) |
| 17 | Agent Registry, AgentSpec & Discovery | [17_agent_registry_and_discovery.md](considerations/17_agent_registry_and_discovery.md) |

## Architecture Decision Records

| ADR | Decision | File |
|-----|----------|------|
| ADR-0001 | Messaging backbone → NATS JetStream | [ADR-0001](adr/ADR-0001-messaging-backbone.md) |
| ADR-0002 | Communication pattern → Hybrid coordinator + swarm | [ADR-0002](adr/ADR-0002-hybrid-communication-pattern.md) |
| ADR-0003 | Agent Runtime → Lightweight Python asyncio | [ADR-0003](adr/ADR-0003-agent-runtime-model.md) |
| ADR-0004 | Memory & state → Tiered Redis + PostgreSQL/pgvector | [ADR-0004](adr/ADR-0004-memory-state-strategy.md) |
| ADR-0005 | Streaming → Chunk-framed begin/end protocol | [ADR-0005](adr/ADR-0005-streaming-chunk-protocol.md) |
| ADR-0006 | Evaluation & guardrails → Built-in framework | [ADR-0006](adr/ADR-0006-evaluation-guardrails.md) |
| ADR-0007 | Observability & replay → OpenTelemetry + Trajectory Store | [ADR-0007](adr/ADR-0007-observability-replay.md) |
| ADR-0008 | Protocol Gateway → Centralized MCP/A2A adapter | [ADR-0008](adr/ADR-0008-protocol-gateway-mcp-a2a.md) |
| ADR-0009 | Deployment & scaling → K8s per-agent-type Deployments | [ADR-0009](adr/ADR-0009-deployment-scaling-isolation.md) |
| ADR-0010 | Agent Registry & AgentSpec → NATS KV-backed dynamic discovery | [ADR-0010](adr/ADR-0010-agent-registry-agentspec.md) |

## Diagrams

| # | Topic | File |
|---|-------|------|
| 01 | Architecture Overview (DataFlow + Activity) | [01_overview.md](diagrams/01_overview.md) |
| 02 | Multi-agent Collaboration Patterns | [02_patterns.md](diagrams/02_patterns.md) |
| 03 | Streaming Chunks & Multimodal Markers | [03_streaming_chunks.md](diagrams/03_streaming_chunks.md) |
| 04 | Agent Communication & Tool Invocation Paths | [04_communication_and_tool_paths.md](diagrams/04_communication_and_tool_paths.md) |

## Other

- [Glossary](glossary.md) — Canonical vocabulary (Agent Runtime, Event Bus, Shared Memory, etc.)
- [Reading List](references/reading_list.md) — Papers, specs, and reference architectures

## Open questions

1. **NATS JetStream cluster sizing**: Exact stream/consumer configuration and replication factor for production. Depends on load-test results.
2. **LLM provider strategy**: Primary vs fallback model selection, cost optimization across providers.
3. **Multi-tenancy data isolation**: Whether to use separate PostgreSQL schemas or databases per tenant (currently namespace-level Kubernetes isolation).
4. **A2A federation trust model**: Mutual TLS certificate management for cross-organization agent communication.
5. **Prompt regression test corpus**: Initial golden dataset for CI prompt regression runs.
6. ~~**Agent capability discovery**: Whether to build a dynamic agent registry or rely on static configuration.~~ **Resolved:** [ADR-0010](adr/ADR-0010-agent-registry-agentspec.md) — NATS KV-backed Agent Registry with AgentSpec and Capability Registry projection.
7. **Cost attribution granularity**: Per-request vs per-agent vs per-tenant token cost tracking and chargeback.
