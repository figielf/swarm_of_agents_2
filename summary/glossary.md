# Glossary

Canonical vocabulary used across this architecture summary.

| Term | Definition |
|------|-----------|
| **Agent** | An autonomous unit of work that consumes events, reasons (typically via an LLM), and produces events. Fully described by an AgentSpec document. |
| **Agent Capability** | A discrete ability an agent declares it can perform (e.g., `product.search`, `order.cancel`). Defined with name, description, and input/output schemas. Capabilities are listed in the agent's AgentSpec and used by the Coordinator for task routing via the Capability Registry. |
| **Agent Registry** | The authoritative store of all AgentSpec documents. Backed by a NATS JetStream key-value bucket. Each agent registers its spec at startup and deregisters on shutdown. Supports heartbeat-based liveness detection (auto-deregister after 90 s of missed heartbeats). |
| **Agent Runtime** | The lightweight Python asyncio execution environment and lifecycle manager for agents. Handles event consumption, retries (exponential backoff with jitter), timeouts, health probes, reflection loops, graceful shutdown, and Agent Registry lifecycle (register/heartbeat/deregister). |
| **AgentSpec** | A declarative Pydantic model that fully describes an agent: type, version, capabilities, NATS subject, consumer group, supported patterns, runtime config, evaluators, tools, owner team, tenant scope, and lifecycle metadata. Stored in the Agent Registry. |
| **Blackboard** | A shared-memory collaboration pattern where agents read and write intermediate results to a common store (Redis pub/sub + hash maps). Agents are notified of updates via pub/sub. |
| **Budget Envelope** | A constraint object (`max_tokens`, `max_turns`, `timeout_ms`) attached to task delegations to prevent runaway costs and latency. |
| **Capability Registry** | A read-only projection of the Agent Registry that maps Agent Capabilities to NATS subjects. Rebuilt on every AgentSpec change. Used by the Coordinator Agent to dynamically route tasks to the correct specialist without hard-coding. |
| **Channel Gateway** | The edge service that accepts user requests (HTTP/WebSocket), translates them into platform events, and streams chunk-framed responses back as SSE. |
| **Chunk-framed Protocol** | The streaming contract where all agent responses are represented as `stream.begin` → `stream.chunk[1..N]` → `stream.end`. A "single message" is N=1. |
| **Coordinator Agent** | A special agent that receives user tasks, plans execution, delegates sub-tasks to specialist agents, synthesizes results, and manages the evaluation/reflection cycle. |
| **Evaluation Layer** | Built-in quality gates (rule-based, LLM-as-judge, classifier) that assess agent outputs at tool-call, agent-output, and system-response boundaries. |
| **Event Bus** | The NATS JetStream pub/sub messaging backbone used for all inter-agent communication. |
| **Event Envelope** | The canonical JSON message wrapper containing `event_type`, `source`, `target`, `correlation_id`, `trace_id`, `payload`, and `metadata`. |
| **Long-term Memory** | PostgreSQL + pgvector store for persistent knowledge, semantic search (RAG), and conversation history beyond session TTL. |
| **Prompt Registry** | A git-based versioned store of prompt templates loaded by agents at startup. Versions are CI-tested via regression runs. |
| **Protocol Gateway** | A centralized service that translates MCP and A2A protocol messages at the platform boundary. Internal agents remain protocol-agnostic. |
| **Reflection Loop** | An optional post-processing phase where an agent evaluates its own output and revises it (bounded by `max_reflection_rounds`, default 2). |
| **Session Memory** | Redis-backed short-lived memory (TTL-bounded) for in-flight conversation context and working state. |
| **Shared Memory** | Logical umbrella term for all memory tiers: Session Memory (Redis), Long-term Memory (PostgreSQL + pgvector), and Blackboard (Redis pub/sub). |
| **Specialist Agent** | A domain-focused agent (e.g., ProductAgent, OrderAgent) that handles a specific capability and is delegated tasks by the Coordinator. |
| **Stigmergy** | Indirect coordination through the shared environment (Blackboard). Agents leave signals for others without direct messaging. |
| **Tool Gateway** | A centralized service providing standardized access to external tools/APIs with authorization, rate limiting, circuit breaking, idempotency, and audit logging. |
| **Trajectory** | The ordered sequence of events (including tool calls, LLM interactions, evaluation results, and delegations) that occurred during a single run/session across one or more agents. |
| **Trajectory Store** | An append-only PostgreSQL table that durably records every event in a Trajectory for audit, debugging, replay, and governance. |
