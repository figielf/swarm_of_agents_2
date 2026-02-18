# Glossary

Canonical vocabulary used across all design documents. If you rename a term here, update all references.

| Term | Definition |
|------|-----------|
| **Agent** | An autonomous unit of work that consumes events, reasons (typically via an LLM), and produces events. Each agent has a declared capability, input/output schema, and lifecycle. |
| **Agent Runtime** | The lightweight Python asyncio execution environment and lifecycle manager for agents. Handles event consumption, retries (exponential backoff with jitter), timeouts, health probes, reflection loops, and graceful shutdown. See [ADR-0003](adr/ADR-0003-agent-runtime-model.md). |
| **Blackboard** | A shared-memory collaboration pattern where agents read and write intermediate results to a common store (Redis pub/sub + hash maps). Agents are notified of updates via pub/sub. See [considerations/06](considerations/06_memory_architecture_shared_state.md). |
| **Budget Envelope** | A constraint object (`max_tokens`, `max_turns`, `timeout_ms`) attached to task delegations to prevent runaway costs and latency. |
| **Channel Gateway** | The edge service that accepts user requests (HTTP/WebSocket), translates them into platform events, and streams chunk-framed responses back as SSE. |
| **Chunk-framed Protocol** | The streaming contract where all agent responses are represented as `stream.begin` → `stream.chunk[1..N]` → `stream.end`. A "single message" is N=1. See [ADR-0005](adr/ADR-0005-streaming-chunk-protocol.md). |
| **Coordinator Agent** | A special agent that receives user tasks, plans execution, delegates sub-tasks to specialist agents, synthesizes results, and manages the evaluation/reflection cycle. |
| **Evaluation Layer** | Built-in quality gates (rule-based, LLM-as-judge, classifier) that assess agent outputs at tool-call, agent-output, and system-response boundaries. See [ADR-0006](adr/ADR-0006-evaluation-guardrails.md). |
| **Event Bus** | The NATS JetStream pub/sub messaging backbone used for all inter-agent communication. See [ADR-0001](adr/ADR-0001-messaging-backbone.md). |
| **Event Envelope** | The canonical JSON message wrapper containing `event_type`, `source`, `target`, `correlation_id`, `trace_id`, `payload`, and `metadata`. See [considerations/04](considerations/04_message_schema_and_contracts.md). |
| **Long-term Memory** | PostgreSQL + pgvector store for persistent knowledge, semantic search (RAG), and conversation history beyond session TTL. |
| **Prompt Registry** | A git-based versioned store of prompt templates loaded by agents at startup. Versions are CI-tested via regression runs. See [considerations/13](considerations/13_prompt_management_and_versioning.md). |
| **Protocol Gateway** | A centralized service that translates MCP and A2A protocol messages at the platform boundary. Internal agents remain protocol-agnostic. See [ADR-0008](adr/ADR-0008-protocol-gateway-mcp-a2a.md). |
| **Reflection Loop** | An optional post-processing phase where an agent evaluates its own output and revises it (bounded by `max_reflection_rounds`, default 2). |
| **Session Memory** | Redis-backed short-lived memory (TTL-bounded) for in-flight conversation context and working state. |
| **Shared Memory** | Logical umbrella term for all memory tiers: session memory (Redis), long-term memory (PostgreSQL + pgvector), and blackboard (Redis pub/sub). See [ADR-0004](adr/ADR-0004-memory-state-strategy.md). |
| **Specialist Agent** | A domain-focused agent (e.g., ProductAgent, OrderAgent, RecommendationAgent) that handles a specific capability and is delegated tasks by the Coordinator. |
| **Stigmergy** | Indirect coordination through the shared environment (blackboard). Agents leave signals for others without direct messaging. |
| **Tool Gateway** | A centralized service providing standardized access to external tools/APIs with authorization, rate limiting, circuit breaking, idempotency, and audit logging. See [considerations/07](considerations/07_tooling_and_integrations.md). |
| **Trajectory** | The ordered sequence of events/messages (including tool calls, LLM interactions, evaluation results, and delegations) that occurred during a single run/session across one or more agents. The unit you can inspect and replay. |
| **Trajectory Store** | An append-only PostgreSQL table that durably records every event in a trajectory for audit, debugging, replay, and governance. See [ADR-0007](adr/ADR-0007-observability-replay.md). |
