# Components Considerations Summary

This document summarizes architectural considerations for each framework component. Communication patterns, buy-vs-build, and high-level architecture are covered in separate documents.

---

## 1. Event Taxonomy

All events follow a hierarchical naming convention: `{category}.{action}` (e.g., `task.delegated`, `stream.chunk`).

**14 event categories:** `session`, `task`, `task.bid`, `agent`, `message`, `stream`, `tool`, `eval`, `memory`, `prompt`, `prompt_run`, `protocol`, `registry`, `system`.

**Event Envelope** — canonical JSON wrapper (Pydantic model):
- `event_id` (UUID v7), `event_type`, `version` (semver)
- `source`, `target`, `correlation_id`, `trace_id`, `span_id`
- `payload`, `metadata`, `pii_flag`
- `timestamp`, `idempotency_key`

**Schema evolution:** Backward-compatible only — new optional fields allowed; new required fields, field removal, and type changes forbidden. Validation at publish time (fail-fast). JSON Schema chosen over Avro/Protobuf for Python ergonomics and log readability.

---

## 2. Agent Runtime & Lifecycle

**Technology:** Custom lightweight runtime built on Python `asyncio`.

**Lifecycle states:** `INITIALIZING → READY → PROCESSING → (REFLECTING) → DRAINING → STOPPED`

| Config | Default |
|---|---|
| `max_concurrent_tasks` | 10 |
| Retry policy | Exponential backoff with jitter (base 1 s, max 30 s, max 3 retries) |
| Heartbeat interval | 30 s |
| Auto-deregistration | After 90 s of missed heartbeats |

**Key behaviors:**
- Auto-registration with Agent Registry on startup; deregistration on graceful shutdown.
- Dead-letter queue for events that fail after max retries.
- Idempotency via `event_id` deduplication in Redis.
- Kubernetes liveness/readiness probes.
- Events consumed from NATS JetStream queue groups (competing consumers, push-based — zero CPU when idle).

---

## 3. Message Schema & Contracts

**Technology:** Pydantic models + JSON Schema + git-based schema registry.

- All messages use the Event Envelope Pydantic model.
- Validation at publish time — malformed events never reach consumers.
- Large payloads use object-storage references (S3/GCS); gzip compression on NATS for messages over threshold.
- CI backward-compatibility checks on every schema change.

**Design choice:** JSON over binary formats (Avro/Protobuf) because messages are small (<10 KB avg), and JSON provides superior log readability and Python developer experience.

---

## 4. Streaming, Chunking & Multimodal Sync

**Protocol:** Chunk-framed streaming on the Event Bus + SSE at the edge.

| Event | Fields |
|---|---|
| `stream.begin` | `message_id`, `trace_id`, `modality` (text/image/carousel), `expected_chunks` |
| `stream.chunk` | `seq_no` (1-based), `payload`, `is_partial` |
| `stream.end` | `message_id`, `checksum` (SHA-256), `final`, `total_chunks` |

**Design invariant:** Single message = `Begin(N=1) → Chunk(seq_no=1) → End`. Protocol is identical for streamed and non-streamed responses.

**Multimodal:** Multiple modalities within the same turn are correlated by `message_id` and differentiated by `modality` tag. Cross-modality streams are independent (no cross-modality ordering dependency). The Channel Gateway translates `stream.*` events to SSE for browsers.

---

## 5. Memory Architecture & Shared State

**Architecture:** Tiered — accessed through a unified `MemoryClient` API.

| Tier | Technology | Use | Retention |
|---|---|---|---|
| **Session Memory** | Redis | In-flight conversation context, working state | TTL = session duration + 1 hour |
| **Blackboard** | Redis pub/sub + hash maps | Leaderless swarm collaboration (Stigmergy) | TTL per task |
| **Long-term Memory** | PostgreSQL + pgvector | Persistent knowledge, semantic search (RAG), history | Configurable; PII per GDPR/CCPA |

**Design decisions:**
- pgvector sufficient for Phase 1–2; dedicated vector DB (Qdrant/Weaviate) deferred to Phase 3+.
- Blackboard notifications via Redis pub/sub enable reactive agent behavior without polling.
- PII stored encrypted with per-user keys (supports GDPR right-to-deletion by key destruction).

---

## 6. Tooling & Integrations (Tool Gateway)

**Architecture:** Centralized Tool Gateway service between agents and external systems.

| Feature | Detail |
|---|---|
| **AuthZ** | Role-based access per tool; elevated authorization for sensitive tools (refund, payment) |
| **Rate limiting** | Token bucket per tool per tenant |
| **Circuit breaking** | 5 consecutive failures → open for 30 s |
| **Idempotency** | Deduplication via idempotency keys in Redis cache |
| **Side-effect classification** | Tools tagged as read-only or mutating; mutating tools require explicit confirmation |
| **MCP tool servers** | External MCP-exposed tools registered via Protocol Gateway adapter |

All tool calls are logged in the Trajectory Store for audit. The gateway is stateless and horizontally scalable.

---

## 7. Evaluation, Reflection & Guardrails

**Architecture:** Built-in evaluation framework with three boundaries.

| Boundary | Evaluator Examples |
|---|---|
| **Tool-call** | Input validation, SQL safety check, authorization |
| **Agent output** | Relevance, factuality, tone, hallucination detection |
| **System response** | Content policy, toxicity filter, PII leak detection |

**Evaluator types:** Rule-based, LLM-as-judge (GPT-4o-mini for cost efficiency), classifier-based (toxicity, brand-voice).

**Reflection Loop** — optional per-agent self-revision:
- `max_reflection_rounds`: hard cap (default: 2)
- `reflection_criteria`: list of evaluation dimensions
- `reflection_model`: can use a cheaper/faster model for self-critique

**Mandatory system guardrails:** toxicity filter, PII leak detection, content policy enforcement. Low-confidence blocks sent to human review queue instead of hard-blocking.

---

## 8. Observability, Tracing & Replay

**Technologies:** OpenTelemetry (tracing), Jaeger/Tempo (visualization), Prometheus + Grafana (metrics), `structlog` (logging), PostgreSQL (Trajectory Store).

**Tracing:** OTel Python SDK with `trace_id` spanning full user session, `span_id` per agent invocation, `parent_span_id` for delegation chains. 10% production sampling (100% for errors).

**Metrics:** Latency, throughput, error rate, token cost — all per agent, session, and tenant.

**Trajectory Store:** Append-only PostgreSQL table indexed by `trace_id`, `session_id`, `agent_id`. Records every event, tool call, LLM interaction, and evaluation result.

**Replay modes:**

| Mode | Description | Use Case |
|---|---|---|
| **Cost-free** | Read-only viewer, no execution | Audit |
| **Deterministic** | Replay feeds cached tool responses | Regression testing |
| **Best-effort** | Re-invokes LLM (results differ) | Debugging, evaluation |

---

## 9. Scaling, Deployment & Isolation

**Deployment model:** Per-agent-type Kubernetes Deployments.

| Aspect | Approach |
|---|---|
| **Autoscaling** | HPA on NATS JetStream pending message count per consumer group (via KEDA) |
| **Multi-tenancy** | Namespace per large tenant; shared namespace with tenant-ID filtering for small tenants |
| **Deployment strategies** | Canary (10% traffic), blue-green (Coordinator), rolling update (default) |
| **Isolation** | K8s resource limits, NATS subject prefixes, Redis key prefixes, NetworkPolicies |
| **GitOps** | ArgoCD or Flux for declarative deployments via Helm charts |

**Rejected alternative:** Serverless/Knative — cold-start latency incompatible with conversational agent SLOs.

**Flash-sale handling:** Pre-scaling triggered by schedule or traffic prediction. Independent agent-type scaling means only hot agents (e.g., ProductAgent) scale up.

---

## 10. Security, Privacy & Compliance

**Approach:** Defense-in-depth with per-layer controls (8 layers).

| Layer | Controls |
|---|---|
| **Ingress** | JWT/OAuth2 authentication, prompt injection detection |
| **Event Bus** | mTLS between agents, topic ACLs |
| **Tool Gateway** | RBAC per tool, rate limiting, audit logging |
| **Shared Memory** | Encrypted PII fields (AES-256), per-user encryption keys |
| **LLM Gateway** | PII stripping before LLM calls |
| **Evaluation Layer** | PII leak detection in agent outputs |
| **Trajectory Store** | PII redaction in stored events |
| **Egress** | Response sanitization, content safety guardrails |

**Prompt injection defense:** Applied at ingress, inter-agent, and tool-output layers.

**Agent identity:** mTLS certificates; roles from AgentSpec (platform-assigned, not self-declared).

**GDPR right-to-deletion:** Per-user encryption key destruction renders all user data unreadable.

---

## 11. Prompt Management & Versioning

**Architecture:** Git-based Prompt Registry with CI regression pipeline.

| Feature | Detail |
|---|---|
| **Storage** | Versioned files in git (`prompts/agents/{agent_type}/{version}/`) |
| **Service** | Lightweight HTTP service serves templates by `(agent_id, version)` with in-memory caching |
| **CI pipeline** | Replay golden dataset → evaluate with Evaluation Layer → block merge if quality degrades |
| **A/B testing** | Feature flags (LaunchDarkly or in-house); promote winning prompt after statistical significance |
| **Non-determinism** | Each regression test runs 3x; median score used for pass/fail |

**Rejected alternatives:** External prompt platforms (Humanloop, LangFuse) — data privacy and integration concerns.

---

## 12. Protocol Wrappers (MCP / A2A)

**Architecture:** Centralized Protocol Gateway service.

| Protocol | Direction | Purpose |
|---|---|---|
| **MCP** | Inbound + Outbound | Expose tools as MCP servers; consume external MCP tool servers |
| **A2A** | Inbound + Outbound | Expose agents as A2A endpoints; delegate tasks to external A2A agents |

**Design:** `ProtocolAdapter` abstract base class with `MCPAdapter` and `A2AAdapter` implementations. Internal agents remain protocol-agnostic — they only interact with the Event Bus. A2A AgentCards are auto-generated from AgentSpec entries in the Agent Registry.

**Security:** API key/OAuth2 at ingress, PII stripping for outbound, response sanitization for inbound.

**Timeline:** Build deferred to Phase 3 (MCP: Phase 3, A2A: Phase 4).

---

## 13. Testing, Simulation & Load

**Strategy:** Automated testing pyramid with 7 levels.

| Level | Technology | Cadence |
|---|---|---|
| **Unit** | pytest + mocked LLM | Per PR |
| **Contract** | JSON Schema validation (schemathesis) | Per PR |
| **Integration** | Docker Compose (real NATS/Redis/PG + mocked LLM) | Per PR |
| **Regression** | Golden tests with real LLM | Nightly |
| **Load** | Locust / k6 | Weekly |
| **Chaos** | Litmus | Weekly |
| **Simulation** | Scripted agent behaviors, multi-agent scenarios | Nightly |

**MockLLM service:** Returns pre-recorded responses by input fingerprint — zero LLM cost for most tests.

**Non-determinism handling:** Statistical assertions (e.g., "relevance > 0.7 in 90% of runs").

---

## 14. Cost, Latency & SLOs

**Service Level Objectives:**

| Metric | Target |
|---|---|
| Simple query latency | p50 < 2 s, p95 < 5 s |
| Complex query latency | p50 < 5 s, p95 < 15 s |
| Agent availability | 99.9% |
| Event Bus availability | 99.99% |

**Budget enforcement:**
- Session token budget tracked in Redis; enforced by Agent Runtime before each LLM call.
- Per-agent latency budget allocated by Coordinator (includes 50% buffer for LLM variability).
- Per-tenant rate limits at Event Bus and LLM Gateway.

**Cost attribution:** Every LLM call records model, token counts, `cost_usd`, agent, session, tenant → Prometheus → Grafana dashboards.

**Capacity baseline:** 500 concurrent sessions → 1K events/sec, 200 LLM calls/sec. Flash sale (10x): 5K sessions, 10K events/sec, 2K LLM calls/sec.

---

## 15. Agent Registry & Discovery

**Architecture:** NATS JetStream KV bucket as primary registry with async PostgreSQL mirror for audit.

**AgentSpec** — comprehensive Pydantic model declaring:
- Identity: `agent_type`, `version`, `owner_team`, `tenant_scope`
- Capabilities: list of Agent Capability objects with I/O schemas
- Routing: `nats_subject`, `consumer_group`, `supported_patterns`
- Runtime config: `max_concurrent_tasks`, timeouts, retries, Reflection Loop settings
- Evaluators, tools, lifecycle metadata (`status`, `registered_at`, `last_heartbeat`)

**Capability Registry** — read-only projection mapping `capability → agent_type + NATS subject`. Rebuilt on every AgentSpec change. Used by Coordinator for LLM-driven task planning.

**Lifecycle:** Heartbeat every 30 s; auto-deregistration after 90 s missed. Registry rejects duplicate capabilities or routes by `confidence_hint` for market bidding.

**A2A integration:** AgentCards auto-generated from AgentSpec entries.
