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

### Options Considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — Flat event namespace** | Single `event_type` string (e.g., `"task.assigned"`) with routing based on string matching | Simple to implement; easy to grep in logs | Name collisions at scale; no structural grouping; brittle string-based routing rules |
| **B — Hierarchical event taxonomy** | Events organized as `{category}.{action}` with centrally governed categories and team-extensible actions | Clear governance and ownership; easy category-level subscriptions (`eval.*`); schema registry enforces per-category schemas | Requires upfront design and governance process; risk of over-categorization |
| **C — Schema-first (Avro/Protobuf)** | Each event type defined as Avro/Protobuf schema with auto-generated typed event classes | Strong compile-time guarantees; built-in schema evolution rules | Weak Python tooling compared to JSON Schema; code generation adds build complexity; slower iteration |

**Chosen: Option B — Hierarchical event taxonomy with JSON Schema validation.**

- The `{category}.{action}` hierarchy gives the platform team clear ownership over the category list while allowing product teams to extend actions via PR review — a governance model that scales with the organization.
- Unlike flat namespaces (Option A), which inevitably devolve into naming chaos as the agent roster grows, hierarchical naming provides structural grouping and prevents collisions.
- Category-level subscriptions (e.g., `eval.*`) dramatically simplify consumer routing and monitoring without fragile string parsing.
- JSON Schema was preferred over Avro/Protobuf (Option C) because our messages are small (<10 KB avg), making binary serialization savings negligible.
- JSON provides superior log readability and native Pydantic integration — both critical for a Python-centric team that iterates rapidly on event shapes.
- Schema evolution is enforced via backward-compatible-only rules (new optional fields allowed; required field additions, removals, and type changes forbidden), with validation at publish time ensuring malformed events never reach consumers.

**Schema evolution:** Backward-compatible only — new optional fields allowed; new required fields, field removal, and type changes forbidden. Validation at publish time (fail-fast).

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

### Options Considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — Adopt existing framework** (LangGraph, AutoGen, CrewAI) | Use a third-party agent framework for the runtime | Faster time to first prototype; community support and pre-built patterns | Imposes foreign execution models (graph/conversation/role-based) conflicting with event-driven design; limited retry/timeout/streaming control; deep vendor lock on fast-moving OSS; none integrate natively with NATS JetStream |
| **B — Build lightweight Agent Runtime** | Thin Python runtime on `asyncio` with configurable lifecycle, retries, health probes, and Event Bus integration | Full control aligned with event-driven architecture; thin layer keeps complexity in business logic; easy to test with mocked Event Bus; no external dependency | Must build and maintain lifecycle management, retry logic, health probes; ~2–3 weeks initial engineering; ~0.5 FTE maintenance first year |
| **C — Container-per-invocation** (Knative / FaaS) | Each agent invocation runs as a separate container | Perfect isolation; auto-scaling to zero when idle | Cold starts (1–5 s) unacceptable for interactive e-commerce chat; every invocation re-fetches context; higher cost at sustained load |

**Chosen: Option B — Build a lightweight Agent Runtime.**

- Existing agent frameworks (Option A) impose their own execution models — LangGraph is graph-centric, AutoGen is conversation-loop-centric, CrewAI is role-centric — none of which align with our Event Bus–driven, pub/sub architecture built on NATS JetStream.
- The wrapping effort needed to shoehorn any of these frameworks into our event-driven paradigm would negate the "buy" advantage and create a fragile dual-abstraction layer.
- Serverless (Option C) was rejected outright because cold-start latency of 1–5 seconds is incompatible with interactive chatbot SLOs (p95 < 5 s).
- Building our own thin runtime gives us first-class integration with NATS JetStream consumer groups (competing consumers, push-based subscription with zero CPU when idle).
- Configurable retry policies with exponential backoff and jitter, per-agent concurrency limits, and graceful shutdown with connection draining are all tailored precisely to our architecture.
- Automatic AgentSpec registration/deregistration with the Agent Registry and reflection loop support are built-in from day one.
- The estimated 2–3 week investment is modest compared to the months of integration pain that framework adoption would create.

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

### Options Considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — JSON Schema + Pydantic** with git-based registry | Pydantic models auto-generate JSON Schemas; schemas versioned in git; CI validates backward compatibility | Excellent Python support; JSON is lingua franca with zero serialization overhead; schema files are reviewable in PRs; Pydantic models auto-generate schemas | JSON Schema lacks built-in compatibility checking (must be tooled); no binary efficiency (larger than Avro/Protobuf) |
| **B — Avro + Confluent Schema Registry** | Events serialized as Avro with Confluent Schema Registry enforcing compatibility | Battle-tested compatibility checking (backward/forward/full); compact binary format; widely used in Kafka ecosystems | Not using Kafka (NATS is our bus); Avro Python tooling less ergonomic than Pydantic; running Confluent Registry adds operational burden; binary format harder to inspect in logs |
| **C — Protobuf + buf.build** | Events defined as Protobuf messages with buf.build for linting and breaking-change detection | Strong typing with code generation; efficient binary serialization; modern buf.build tooling | Protobuf C extension compilation issues in Python; code generation adds build steps; binary format reduces log/trajectory readability |

**Chosen: Option A — JSON Schema with Pydantic models and a git-based schema registry.**

- Our messages average under 10 KB, which means the binary efficiency advantage of Avro (Option B) or Protobuf (Option C) is negligible — payload sizes don't justify the operational cost of a dedicated schema registry service or the DX friction of code generation pipelines.
- JSON's readability is a massive operational advantage: engineers can read event payloads directly in logs, the Trajectory Store viewer, and NATS monitoring tools without deserialization tooling.
- Pydantic's `model_json_schema()` auto-generates schemas from the same models used in code, eliminating schema drift by construction.
- The git-based registry means schema changes go through the same PR review process as code, with CI enforcing backward compatibility rules (additive-only changes).
- No Confluent Schema Registry to run (Option B) and no Protobuf compilation chain to maintain (Option C) — minimal operational footprint.
- Publish-time validation rejects malformed events before they ever reach a consumer.

**Design choice:** JSON over binary formats (Avro/Protobuf) because messages are small (<10 KB avg), and JSON provides superior log readability and Python developer experience.

---

## 4. Streaming, Chunking & Multimodal Sync

**Protocol:** Chunk-framed streaming on the Event Bus + SSE at the edge.

| Event | Fields |
|---|---|
| `stream.begin` | `message_id`, `trace_id`, `modality` (text/image/carousel), `expected_chunks` |
| `stream.chunk` | `seq_no` (1-based), `payload`, `is_partial` |
| `stream.end` | `message_id`, `checksum` (SHA-256), `final`, `total_chunks` |

### Options Considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — Raw byte streaming** (SSE/WebSocket passthrough) | Agents produce raw byte streams passed directly to the UI | Simple; no framing overhead | No explicit begin/end markers; no multimodal correlation; replay requires byte-level reconstruction; incompatible with discrete-event pub/sub bus |
| **B — Chunk-framed protocol on Event Bus** | Each response is `stream.begin → stream.chunk[1..N] → stream.end` as discrete events on the Event Bus | Unified protocol for streamed and non-streamed responses (`N=1`); natural fit for Event Bus; full trajectory capture; multimodal alignment via `correlation_group` and `modality` | Slightly higher overhead (event envelope per chunk); requires sequence-number tracking and checksum validation |
| **C — SSE at gateway, events internally** | SSE between Channel Gateway and UI, chunk-framed events internally | SSE is well-supported by browsers; good for incremental rendering | Not mutually exclusive with Option B — SSE is a transport concern at the edge, not an internal protocol alternative |

**Chosen: Option B — Chunk-framed streaming on the Event Bus + SSE at the Channel Gateway edge.**

- The chunk-framed protocol is the only option that satisfies all three critical requirements simultaneously: multimodal synchronization, full-fidelity trajectory replay, and Event Bus compatibility.
- Raw byte streaming (Option A) fundamentally breaks our event-driven architecture — the Event Bus operates on discrete, self-describing messages, not raw byte streams, and byte-level replay is impractical for debugging multi-agent interactions.
- The unified protocol means even single-message responses follow `Begin(N=1) → Chunk(seq_no=1) → End`, eliminating special-case handling that plagues systems with separate streamed and non-streamed code paths.
- Multimodal e-commerce responses (text + product cards + image carousels from different agents) are correlated via `correlation_group` and `modality` tags, with each modality rendered independently — no cross-modality ordering dependency keeps the UI responsive.
- SSE at the Channel Gateway edge (Option C's contribution) provides a thin, browser-friendly translation layer without polluting the internal protocol.
- Every chunk is a discrete Trajectory Store event — replay is trivial (re-sequence the events and render).

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

### Options Considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — Redis for everything** | Use Redis for session, blackboard, and long-term storage (with RediSearch for vectors) | Single technology to operate; sub-millisecond reads/writes; Redis pub/sub supports blackboard notifications | Volatile by default (RDB/AOF adds complexity); RediSearch less mature than pgvector; long-term history is expensive in RAM; poor support for complex queries (joins, aggregations) |
| **B — Tiered: Redis + PostgreSQL/pgvector** | Redis for session memory and blackboard; PostgreSQL with pgvector for long-term and semantic memory | Best tool for each tier; PostgreSQL is a common enterprise dependency; pgvector handles moderate-scale vector search; Redis excels at high-throughput ephemeral data | Two technologies to operate; cross-tier queries require application-level joins |
| **C — Tiered + dedicated vector DB** (Qdrant/Weaviate) | Same as Option B but with a dedicated vector database instead of pgvector | Better performance at very large vector scales (>10M embeddings); advanced vector search features (filtering, HNSW tuning) | Third technology to operate; overkill for Phase 1–2 (typical catalog <1M products) |

**Chosen: Option B — Tiered (Redis + PostgreSQL/pgvector).**

- The tiered architecture applies the right tool to each memory tier's unique access pattern, while minimizing operational overhead with only two well-understood, widely-deployed technologies.
- Redis is the natural fit for session memory and the blackboard: sub-millisecond latency meets the sub-10ms read requirement, TTL support provides automatic cleanup, and pub/sub enables reactive blackboard notifications without polling.
- PostgreSQL handles long-term memory, audit history, and semantic search via pgvector — it provides durability, complex query support, and compliance-ready data management (GDPR right-to-deletion, configurable retention policies) that Redis fundamentally cannot.
- Using Redis for everything (Option A) would force long-term history into expensive RAM and sacrifice rich query capabilities needed for historical analysis and compliance reporting.
- A dedicated vector DB (Option C) was explicitly deferred: with a typical e-commerce catalog under 1M products, pgvector comfortably handles ANN search within SLO.
- If p95 vector search latency degrades beyond 50ms at scale, the unified `MemoryClient` API makes migrating the vector tier to Qdrant or Weaviate a backend swap transparent to agents — a Phase 3+ consideration.

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

### Options Considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — Direct tool invocation** (no gateway) | Agents call external tools directly via HTTP/SDK | Simplest implementation; no additional latency | No centralized authZ, rate limiting, or audit; each agent implements its own retry/circuit-breaker logic; tool changes require updating every consuming agent; no idempotency enforcement |
| **B — Centralized Tool Gateway** | Dedicated service that validates, rate-limits, circuit-breaks, and audits all tool calls | Centralized security, audit, and governance; tool changes isolated from agents; idempotency keys prevent duplicate side effects; rate limiting protects downstream systems | Adds one extra network hop of latency; gateway is a critical-path component requiring high availability |
| **C — Sidecar / middleware pattern** | Tool gateway logic runs as a sidecar in each agent pod | No extra network hop; distributed with no single point of failure | Inconsistent policy enforcement across agents; updates require redeploying all agents; audit log aggregation is more complex |

**Chosen: Option B — Centralized Tool Gateway service.**

- Tool invocations in e-commerce are security-critical operations — placing orders, issuing refunds, accessing customer PII — where centralized policy enforcement is non-negotiable.
- Direct invocation (Option A) scatters authZ, rate limiting, and audit across every agent, creating an ungovernable surface area where a single misconfigured agent can issue unauthorized refunds or exhaust a downstream API's rate limit.
- The sidecar approach (Option C) introduces consistency risks: updating authorization policies requires redeploying every agent pod, and audit log aggregation becomes a distributed systems problem.
- The centralized gateway provides a single chokepoint where every tool call is authenticated against the agent's AgentSpec role, rate-limited per tool per tenant via token bucket, protected by circuit breakers (5 failures → 30s open), and logged to the Trajectory Store.
- The extra network hop adds minimal latency (typically <5ms in-cluster) and is dwarfed by tool execution time itself (100ms–5s for external APIs).
- The gateway is stateless and horizontally scalable, making high availability straightforward.
- For MCP tool servers, the gateway integrates with the Protocol Gateway adapter, keeping agents protocol-agnostic.

All tool calls are logged in the Trajectory Store for audit. The gateway is stateless and horizontally scalable.

---

## 7. Evaluation, Reflection & Guardrails

**Architecture:** Built-in evaluation framework with three boundaries.

| Boundary | Evaluator Examples |
|---|---|
| **Tool-call** | Input validation, SQL safety check, authorization |
| **Agent output** | Relevance, factuality, tone, hallucination detection |
| **System response** | Content policy, toxicity filter, PII leak detection |

### Options Considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — External evaluation service** (Patronus AI, Galileo, Arthur AI) | Third-party evaluation platform called post-generation | Pre-built evaluators for hallucination, toxicity, relevance; managed service with dashboards | External API latency per evaluation; per-invocation cost at scale; data privacy concerns (agent outputs leave network); limited domain-specific customization |
| **B — Built-in evaluation framework** | In-house evaluator interface with rule-based, LLM-as-judge, and classifier-based evaluator types | Full control over logic, latency, and data privacy; domain-specific evaluators (price accuracy, inventory checks); no external data exposure; evaluation results are first-class Trajectory Store events | Must build and maintain evaluators; LLM-as-judge adds LLM cost (mitigated by fast/cheap models) |
| **C — Hybrid (built-in + optional external)** | Build framework in-house with plugin support for external evaluators | Best of both worlds: domain-specific in-house + specialized third-party for general safety | Integration complexity with external APIs; increased surface area |

**Chosen: Option B — Built-in evaluation framework, with Option C extensibility for Phase 3+.**

- Evaluation is a core competency in an agentic system, not a peripheral concern that can be outsourced.
- External evaluation services (Option A) introduce three unacceptable trade-offs: network latency (threatens the 500ms p95 guardrail budget), data privacy exposure (agent outputs leave the network in an e-commerce context handling PII and payment data), and limited domain-specific coverage (cannot check pricing accuracy, inventory consistency, or promotional rules).
- Building in-house maintains full control over the evaluation pipeline with zero data leaving the network.
- Domain-specific evaluators can directly query session memory and the product catalog for ground-truth validation.
- LLM-as-judge cost is mitigated by using GPT-4o-mini, running LLM judges selectively (only at agent output and system boundaries, not every tool call), and caching evaluations for identical outputs.
- The three-boundary design (tool-call, agent output, system response) ensures defense-in-depth without over-evaluating.
- Plugin extensibility (Option C) is explicitly planned for Phase 3+ to allow future integration with specialized safety platforms.

**Evaluator types:** Rule-based, LLM-as-judge (GPT-4o-mini for cost efficiency), classifier-based (toxicity, brand-voice).

**Reflection Loop** — optional per-agent self-revision:
- `max_reflection_rounds`: hard cap (default: 2)
- `reflection_criteria`: list of evaluation dimensions
- `reflection_model`: can use a cheaper/faster model for self-critique

**Mandatory system guardrails:** toxicity filter, PII leak detection, content policy enforcement. Low-confidence blocks sent to human review queue instead of hard-blocking.

---

## 8. Observability, Tracing & Replay

**Technologies:** OpenTelemetry (tracing), Jaeger/Tempo (visualization), Prometheus + Grafana (metrics), `structlog` (logging), PostgreSQL (Trajectory Store).

### Options Considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — Managed observability platform** (Datadog, New Relic, Honeycomb) | Use a third-party managed platform for tracing, metrics, and logging | Pre-built dashboards, alerting, AIOps, anomaly detection; managed storage and retention; team familiarity | Cost scales linearly with high-cardinality event volume; cannot serve as Trajectory Store for replay (data model mismatch); limited custom replay queries |
| **B — OpenTelemetry + custom Trajectory Store** | OTel for tracing/metrics export; append-only PostgreSQL table for trajectory capture and replay | Industry-standard vendor-neutral tracing; full-fidelity replay (not just trace visualizations); clear separation of live observability and audit/replay; PostgreSQL already in stack | Must build Trajectory Store schema and replay engine; OTel instrumentation requires wrapping every agent and tool call |
| **C — Event sourcing with NATS log** | Use the Event Bus itself (NATS JetStream retention) as the event log | No separate Trajectory Store; natural event sourcing pattern | NATS retention is time/size-based (long-term audit requires external archival); querying NATS for replay less ergonomic than PostgreSQL SQL; mixing operational and audit data complicates capacity planning |

**Chosen: Option B — OpenTelemetry + custom Trajectory Store in PostgreSQL.**

- Our system has two fundamentally different observability needs that no single solution addresses: live operational monitoring and full-fidelity event replay.
- Live observability demands the vendor-neutral OpenTelemetry ecosystem — it instruments every agent, tool call, and Event Bus interaction with distributed traces (`trace_id` spanning full sessions, `span_id` per agent invocation, `parent_span_id` for delegation chains).
- Replay and regression testing require full-fidelity event capture where every event envelope with its complete payload is stored, queryable by `trace_id`, `session_id`, and `agent_id`, and replayable in three modes (cost-free audit, deterministic regression, best-effort prompt evaluation).
- Managed platforms (Option A) cannot serve as a Trajectory Store — their data models are optimized for trace visualization, not event replay, and per-event pricing at 1000+ events/second would be prohibitive.
- Event sourcing on NATS (Option C) lacks the SQL query ergonomics needed for complex replay queries and the long-term retention guarantees needed for compliance (90+ day audit trails).
- PostgreSQL is already in our stack for long-term memory, making the Trajectory Store a natural extension with zero additional operational burden.

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

### Options Considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — Monolithic deployment** | All agents in one process/container | Simplest deployment; single container | No independent scaling; one agent failure crashes all; cannot allocate different resources per agent type |
| **B — Per-agent-type K8s Deployments** | Each agent type is a separate Kubernetes Deployment with own replica count, resources, and HPA | Independent scaling (hot agents scale without scaling everything); fault isolation; independent deployments; per-agent resource tuning | More Kubernetes objects to manage; must standardize agent packaging (Docker image, Helm chart) |
| **C — Serverless / Knative** (scale to zero) | Each agent invocation runs as a separate container with auto-scaling to zero | True scale-to-zero for idle agents; automatic scaling based on request volume | Cold start latency (1–5 s) unacceptable for interactive chat; less control over scaling behavior; complex Event Bus networking |

**Chosen: Option B — Per-agent-type Kubernetes Deployments.**

- E-commerce traffic is inherently spiky and unevenly distributed across agent types, making independent scaling a hard requirement.
- During a flash sale, ProductSearchAgent may need to scale from 5 to 50 pods while OrderTrackingAgent remains at 2 — monolithic deployment (Option A) would force scaling the entire system 10x, wasting resources on idle agents.
- Serverless (Option C) was rejected because cold-start latency of 1–5 seconds fundamentally violates interactive chatbot SLOs, and Knative + NATS JetStream networking introduces unnecessary operational fragility.
- Per-agent-type Deployments provide fault isolation (a crashing ProductSearchAgent doesn't take down the Coordinator) and independent deployment cadence (teams ship agent updates independently).
- Per-agent resource tuning: memory-heavy RAG agents get more RAM; CPU-bound coordinator agents get more CPU.
- Autoscaling uses KEDA watching NATS JetStream pending message count per consumer group — a direct measure of agent backlog — rather than CPU/memory metrics that correlate poorly with LLM-bound workloads.
- Operational complexity of managing many Deployments is mitigated by standardized Helm chart templates and GitOps (ArgoCD/Flux).

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

### Options Considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — Perimeter-only security** | Secure at the API gateway; trust all internal components | Simplest implementation; lowest engineering effort | Internal compromise is unrestricted (no defense in depth); prompt injection bypasses perimeter; not PCI-DSS compliant (requires internal segmentation) |
| **B — Defense-in-depth** with per-layer controls | Security controls at every layer: ingress, Event Bus, Tool Gateway, Memory, LLM Gateway, Evaluation, Trajectory Store, and egress | Defense in depth — compromise of one layer doesn't expose the system; compliance-ready (GDPR/CCPA/PCI-DSS); full audit trail with PII controls | Higher implementation and operational complexity; performance overhead from encryption, validation, and scanning at each layer |

**Chosen: Option B — Defense-in-depth with per-layer controls.**

- An e-commerce agentic system handles the trifecta of sensitive data — customer PII, payment information, and business-critical operations — making perimeter-only security (Option A) fundamentally inadequate and non-compliant with PCI-DSS.
- The multi-agent architecture introduces unique attack vectors: prompt injection at ingress (user input), inter-agent (compromised agent output becomes another agent's input), and tool-output (external API responses containing injected content) — all three require dedicated detection.
- The eight-layer model ensures that breaching one layer does not expose the system: mTLS on the Event Bus, RBAC at the Tool Gateway, PII encryption in Shared Memory, PII stripping at the LLM Gateway, PII leak detection at the Evaluation Layer, PII redaction in the Trajectory Store, and response sanitization at egress.
- Agent identity is established at startup via mTLS certificates with roles platform-assigned from the AgentSpec — agents cannot self-declare elevated permissions.
- GDPR right-to-deletion is supported via per-user encryption key destruction, rendering all user data across all stores unreadable without record-by-record deletion.

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

### Options Considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — Prompts in code** (hardcoded strings) | Prompts checked into source code as string literals | Simple; version-controlled via git; no additional infrastructure | Prompt changes require full code deployments; no A/B testing or dynamic rollback; hard to run automated regression suites against prompt-only changes |
| **B — Dedicated prompt platform** (Humanloop, PromptLayer, LangFuse) | Third-party prompt management platform with versioning and analytics | Pre-built versioning, A/B testing, analytics; UI for non-engineers | External dependency with data leaving network; cost at scale; integration complexity with Event Bus and Evaluation Layer |
| **C — Git-based Prompt Registry** with CI regression | Prompts as versioned files in git; lightweight HTTP service for runtime delivery; CI pipeline runs regression suites on changes | Version history via git with PR-based review; CI regression blocks merges if quality degrades; no external dependency; rollback = revert version | Must build Prompt Registry service and CI pipeline; A/B testing requires feature-flag integration |

**Chosen: Option C — Git-based Prompt Registry with CI-driven regression pipeline.**

- Prompts are the most frequently changed artifact in an agentic system and simultaneously the most dangerous — a bad prompt can silently degrade all agent responses — making automated quality gates and auditability paramount.
- Hardcoded prompts (Option A) conflate prompt changes with code deployments, preventing rapid iteration and making A/B testing or rollback impossible without full redeployment.
- External prompt platforms (Option B) introduce unacceptable data privacy risks — prompts encode proprietary business logic, pricing strategies, and competitive positioning that should not leave the network.
- The git-based registry treats prompts as first-class versioned artifacts: changes go through PRs with team review, CI replays golden test datasets, the Evaluation Layer scores outputs, and merges are blocked if any metric degrades.
- Each regression test runs 3x with median scoring to handle LLM non-determinism.
- At runtime, the Prompt Registry service serves templates by `(agent_id, version)` with in-memory caching and instant version rollback via API call — no redeployment required.
- A/B testing is layered on top via feature flags that select prompt versions per session, with automatic promotion after statistical significance.

**Rejected alternatives:** External prompt platforms (Humanloop, LangFuse) — data privacy and integration concerns.

---

## 12. Protocol Wrappers (MCP / A2A)

**Architecture:** Centralized Protocol Gateway service.

| Protocol | Direction | Purpose |
|---|---|---|
| **MCP** | Inbound + Outbound | Expose tools as MCP servers; consume external MCP tool servers |
| **A2A** | Inbound + Outbound | Expose agents as A2A endpoints; delegate tasks to external A2A agents |

### Options Considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — Embed protocol handling in each agent** | Each agent implements protocol handling (MCP/A2A) directly in its code | No additional service | Protocol logic scattered across agents; inconsistent implementations; security enforcement is per-agent with no centralized policy; protocol updates require changing every affected agent |
| **B — Centralized Protocol Gateway** | Dedicated service for all protocol translation (MCP ↔ Event Bus, A2A ↔ Event Bus) | Single point of protocol translation (easy to update); centralized security (authZ, rate limits, validation); internal agents remain protocol-agnostic | Additional service to operate; single point of failure for protocol interactions (mitigated by replication) |
| **C — Sidecar protocol adapters** | Each agent pod runs a sidecar handling protocol translation | Distributed with no central bottleneck | Sidecar updates require bouncing all pods; harder to enforce centralized security; more resource overhead (one sidecar per agent pod) |

**Chosen: Option B — Centralized Protocol Gateway service.**

- Protocol interoperability is an evolving, cross-cutting concern that must be managed as a single responsibility rather than scattered across the agent fleet.
- Embedding handling directly in agents (Option A) means every protocol spec update requires coordinated changes across every participating agent — an update bottleneck that worsens as the roster grows.
- The sidecar approach (Option C) multiplies resource consumption (one sidecar per agent pod) and makes centralized security enforcement difficult.
- The centralized Protocol Gateway provides a clean abstraction: internal agents interact only with the Event Bus and remain entirely protocol-agnostic.
- For MCP, it registers external tool servers, translates `tool.invoked` events into MCP requests (outbound), and exposes internal tools as MCP servers (inbound).
- For A2A, it translates `protocol.a2a.request` events into A2A task delegations (outbound) and maps incoming A2A requests to `task.created` events (inbound).
- A2A AgentCards are auto-generated from AgentSpec entries, keeping external discovery in sync with internal capabilities automatically.
- Security is enforced at the gateway boundary: API key/OAuth2 for inbound, PII stripping for outbound, and response sanitization before entering the Event Bus.
- Build is deferred to Phase 3 (MCP) and Phase 4 (A2A) to focus initial effort on core platform capabilities.

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

### Options Considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — Manual testing only** | No automated tests; rely on human QA | None meaningful for production systems | Unacceptable for enterprise e-commerce; non-repeatable, slow, error-prone; emergent multi-agent failures invisible until production |
| **B — Comprehensive automated testing pyramid** | 7-level pyramid (unit → contract → integration → regression → load → chaos → simulation) with MockLLM for cost control | Comprehensive coverage across all failure modes; cost-efficient (most tests use mocked LLMs); CI-friendly cadence (per-PR / nightly / weekly); simulation tests catch emergent swarm behaviors | Significant upfront investment to build the testing framework; mocked LLM may not catch LLM-specific regressions (mitigated by golden tests with real LLM) |

**Chosen: Option B — Comprehensive automated testing pyramid.**

- Multi-agent systems exhibit emergent failure modes that are fundamentally invisible to manual testing — circular delegation loops, blackboard contention, cascading timeout propagation across delegation chains.
- The seven-level pyramid catches failures at every level of abstraction: individual agent logic (unit tests), message contract conformance (JSON Schema validation), real infrastructure integration (Docker Compose with NATS/Redis/PG), prompt quality regression (golden tests with real LLM), production-scale performance (Locust/k6), infrastructure resilience (Litmus chaos), and emergent swarm behavior (scripted multi-agent simulations).
- The MockLLM service — returning pre-recorded responses by input fingerprint — is the key cost-control mechanism, enabling unit, integration, load, and chaos tests at zero LLM cost.
- Real LLM calls are reserved for the nightly golden regression suite where non-determinism is handled by running each test 3x and taking the median score.
- Statistical assertions (e.g., "relevance > 0.7 in 90% of runs") acknowledge LLM non-determinism without sacrificing test reliability.

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

### Options Considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — No explicit controls** | Let agents run unconstrained; monitor after the fact | Simplest implementation; zero engineering effort | Cost overruns on complex workflows (swarm delegation with no budget cap); latency violations for deep agent chains; no per-tenant fairness; no pre-emptive cost alerts |
| **B — Framework-enforced budgets and SLOs** | Session token budgets, per-agent latency budgets, per-tenant rate limits, and cost attribution built into Agent Runtime and Event Bus | Cost predictability via enforceable token budgets; latency guarantees via time-slice allocation; per-tenant fairness through rate limits; granular cost attribution for business intelligence | More controls to configure and tune; budget settings need calibration based on real traffic data |

**Chosen: Option B — Framework-enforced budgets and SLOs.**

- In a multi-agent system, cost and latency compound multiplicatively — a single user request can trigger 5–10 agent invocations, each making 1–3 LLM calls, with no ceiling if unconstrained.
- Running unconstrained (Option A) is untenable for production e-commerce where LLM costs are the dominant expense (>70% of total system cost) and chatbot latency directly impacts conversion rates.
- **Session token budgets:** the Coordinator declares a max token budget per session, tracked in Redis and enforced by the Agent Runtime before every LLM call — when exhausted, agents return best-effort results without additional LLM calls.
- **Per-agent latency budgets:** the Coordinator allocates time slices to each sub-task (with 50% buffer for LLM variability) — if exceeded, the circuit breaker returns a cached or degraded response.
- **Per-tenant rate limits** at both the Event Bus (events/second) and LLM Gateway (tokens/minute) ensure one tenant's flash-sale traffic cannot starve others.
- Cost attribution records every LLM call with (model, input_tokens, output_tokens, cost_usd, agent_id, session_id, tenant_id) and exports to Prometheus → Grafana dashboards for granular visibility.

**Budget enforcement:**
- Session token budget tracked in Redis; enforced by Agent Runtime before each LLM call.
- Per-agent latency budget allocated by Coordinator (includes 50% buffer for LLM variability).
- Per-tenant rate limits at Event Bus and LLM Gateway.

**Cost attribution:** Every LLM call records model, token counts, `cost_usd`, agent, session, tenant → Prometheus → Grafana dashboards.

**Capacity baseline:** 500 concurrent sessions → 1K events/sec, 200 LLM calls/sec. Flash sale (10x): 5K sessions, 10K events/sec, 2K LLM calls/sec.

---

## 15. Agent Registry & Discovery

**Architecture:** NATS JetStream KV bucket as primary registry with async PostgreSQL mirror for audit.

### Options Considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| **A — Hardcoded routing table** | Coordinator has a static mapping of capabilities to agent NATS subjects | Simplest; no registry service needed | Adding a new agent requires code change and redeployment; no dynamic discovery; no runtime health awareness; impossible to scale agent roster |
| **B — NATS JetStream KV registry** | AgentSpec stored in NATS KV bucket with async PostgreSQL mirror; Capability Registry as read-only projection | Sub-millisecond reads from NATS KV (in-process); dynamic registration/deregistration on agent startup/shutdown; already running NATS; PostgreSQL mirror for audit and history | Must build registry service and Capability Registry projection; NATS KV is eventually consistent (mitigated by heartbeat protocol) |
| **C — Dedicated service registry** (Consul, etcd, ZooKeeper) | Use an established service discovery platform | Battle-tested; rich query and health-check features | Additional infrastructure to operate; capabilities are not first-class in generic service registries; must be adapted for AgentSpec semantics |

**Chosen: Option B — NATS JetStream KV bucket as primary registry.**

- We already run NATS JetStream as the Event Bus — using its built-in KV store means zero additional services to operate and zero additional network hops for capability lookups (sub-millisecond reads from the same connection used for event consumption).
- Dedicated service registries like Consul or etcd (Option C) are battle-tested but generic — they treat service instances as network endpoints, not capability-bearing agents.
- Our Coordinator needs to answer "which agent can handle `product.search` with the highest confidence?" — this requires a first-class Capability Registry mapping capabilities to agent types and NATS subjects, a projection rebuilt on every AgentSpec change.
- Building this projection on Consul would add operational complexity (another service to deploy, monitor, upgrade) without meaningful advantage over NATS KV.
- Hardcoded routing (Option A) was rejected because it creates deployment coupling between the Coordinator and every specialist agent — every new agent type requires a Coordinator code change and redeployment.
- The async PostgreSQL mirror provides durable audit history and enables complex lifecycle queries that NATS KV cannot support (e.g., "agents that deregistered >3 times in the last 24 hours").

**AgentSpec** — comprehensive Pydantic model declaring:
- Identity: `agent_type`, `version`, `owner_team`, `tenant_scope`
- Capabilities: list of Agent Capability objects with I/O schemas
- Routing: `nats_subject`, `consumer_group`, `supported_patterns`
- Runtime config: `max_concurrent_tasks`, timeouts, retries, Reflection Loop settings
- Evaluators, tools, lifecycle metadata (`status`, `registered_at`, `last_heartbeat`)

**Capability Registry** — read-only projection mapping `capability → agent_type + NATS subject`. Rebuilt on every AgentSpec change. Used by Coordinator for LLM-driven task planning.

**Lifecycle:** Heartbeat every 30 s; auto-deregistration after 90 s missed. Registry rejects duplicate capabilities or routes by `confidence_hint` for market bidding.

**A2A integration:** AgentCards auto-generated from AgentSpec entries.
