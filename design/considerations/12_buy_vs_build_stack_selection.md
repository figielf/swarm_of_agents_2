# Buy vs build: core stack selection (bus, runtime, stores)

## 1. Context and problem statement

The framework requires selecting specific technologies for its core infrastructure components. For each component, we must decide whether to adopt an existing solution ("buy") or build in-house ("build"). This document consolidates the buy-vs-build analysis for the major infrastructure decisions.

**Constraints:**
- Python-first; all libraries/services must have excellent Python client support.
- Enterprise e-commerce: must be battle-tested, not experimental.
- Team size assumption: 4–8 engineers for the platform team.
- Prefer managed services where the operational burden is high and the differentiation is low.

## 2. Requirements coverage

This document covers technology selection for all framework requirements (R1–R10) from `CLAUDE.md`.

## 3. Component-by-component analysis

### 3.1 Event Bus

| Option | Type | Pros | Cons |
|---|---|---|---|
| **NATS JetStream** | Buy (OSS) | Lightweight, fast, persistent streams, consumer groups, subject-based routing, excellent Python client (`nats-py`). Single binary. Low operational burden. | Smaller community than Kafka. Less ecosystem tooling (no built-in schema registry). |
| **Apache Kafka** | Buy (OSS/managed) | Industry standard, huge community, Confluent ecosystem (Schema Registry, ksqlDB, Flink). Battle-tested at extreme scale. | Operationally heavy (ZooKeeper/KRaft, brokers, partitions). Overkill for expected event volume (<10K events/sec). Python client (`confluent-kafka`) requires librdkafka C dependency. |
| **Redis Streams** | Buy (OSS) | Already in the stack (session memory). Simple API. | Limited durability guarantees compared to NATS/Kafka. Consumer group support is basic. Not designed as a primary messaging backbone. |
| **RabbitMQ** | Buy (OSS) | Mature, well-understood. Good Python support (`aio-pika`). | Queue-based (not log-based); harder to replay. No native persistent streams. |
| **Build custom (WebSocket/gRPC)** | Build | Full control. | Enormous effort to build a reliable, persistent, ordered pub/sub system. Not viable. |

**Recommendation:** **NATS JetStream** — best balance of simplicity, performance, persistence, and Python support. Avoids Kafka's operational overhead for our scale. See [ADR-0001](../adr/ADR-0001-messaging-backbone.md).

### 3.2 Agent Runtime

| Option | Type | Pros | Cons |
|---|---|---|---|
| **Build lightweight runtime** | Build | Full alignment with event-driven architecture. Thin layer (agent lifecycle, retries, timeouts). | Must build and maintain (~2–3 weeks initial, ~0.5 FTE ongoing). |
| **LangGraph** | Buy (OSS) | Existing familiarity. Rich graph-based patterns. | Being replaced (see motivation in `high_level_architecture.md`). |
| **AutoGen / CrewAI** | Buy (OSS) | Pre-built multi-agent patterns. | Impose foreign execution models. Do not integrate with our Event Bus. |

**Recommendation:** **Build** — the runtime is the framework's core differentiator. It must align with the Event Bus and support our specific lifecycle, retry, and streaming requirements. See [ADR-0003](../adr/ADR-0003-agent-runtime-model.md).

### 3.3 Memory / State Stores

| Option | Type | Pros | Cons |
|---|---|---|---|
| **Redis (session + blackboard)** | Buy (OSS/managed) | Sub-ms latency. Pub/sub for blackboard notifications. Widely available as managed service. | Volatile unless persistence configured. |
| **PostgreSQL + pgvector (long-term + semantic)** | Buy (OSS/managed) | Durable, SQL-queryable, vector search. Single DB for long-term memory and Trajectory Store. | Vector search performance is adequate but not SOTA. |
| **Dedicated vector DB (Qdrant, Weaviate)** | Buy (OSS/managed) | Superior vector search at scale. | Third technology to operate. Overkill for Phase 1–2. |

**Recommendation:** **Redis + PostgreSQL/pgvector** for Phase 1–2. Re-evaluate dedicated vector DB at Phase 3. See [ADR-0004](../adr/ADR-0004-memory-state-strategy.md).

### 3.4 Observability

| Option | Type | Pros | Cons |
|---|---|---|---|
| **OpenTelemetry + Jaeger/Tempo + Prometheus + Grafana** | Buy (OSS) | Industry standard. Vendor-neutral. Self-hosted or managed options. | Must integrate and operate multiple components. |
| **Managed platform (Datadog, New Relic)** | Buy (SaaS) | Pre-built dashboards, alerting. Managed. | Cost scales with volume. Cannot serve as Trajectory Store. Data leaves the network. |

**Recommendation:** **OpenTelemetry stack** for tracing and metrics. Supplements (not replaces) the Trajectory Store. See [ADR-0007](../adr/ADR-0007-observability-replay.md).

### 3.5 Evaluation Layer

| Option | Type | Pros | Cons |
|---|---|---|---|
| **Build in-house** | Build | Full control. Domain-specific evaluators. No data exposure. | Must build and maintain evaluators. |
| **External platform (Patronus, Galileo)** | Buy (SaaS) | Pre-built evaluators. Dashboards. | Data privacy. Cost. Latency. |

**Recommendation:** **Build** for Phase 1–2 (core evaluators). Consider hybrid with external platforms at Phase 3+ for specialized safety evaluators. See [ADR-0006](../adr/ADR-0006-evaluation-guardrails.md).

### 3.6 Protocol Gateway (MCP/A2A)

| Option | Type | Pros | Cons |
|---|---|---|---|
| **Build thin adapters** | Build | Protocols are still evolving; thin adapters are easier to update. Full control over translation. | Must track protocol spec changes. |
| **Adopt an MCP SDK** | Buy (OSS) | Pre-built protocol handling. | Still requires adaptation to our Event Bus envelope. |

**Recommendation:** **Build thin adapters** using official MCP/A2A SDKs as libraries (not frameworks). See [ADR-0008](../adr/ADR-0008-protocol-gateway-mcp-a2a.md).

## 4. Decision drivers

| Driver | Weight | Applies to |
|---|---|---|
| Operational simplicity | High | All components |
| Python ecosystem quality | High | Event Bus, runtime |
| Differentiation value | High | Runtime, evaluation (build where we differentiate) |
| Enterprise maturity | High | Event Bus, stores |
| Team size | High | Favor buy for undifferentiated heavy lifting |

## 5. Recommendation summary

| Component | Decision | Technology | Rationale |
|---|---|---|---|
| Event Bus | **Buy** | NATS JetStream | Best simplicity/performance/persistence balance. |
| Agent Runtime | **Build** | Python asyncio | Core differentiator; must align with Event Bus. |
| Session Memory | **Buy** | Redis | Fast, mature, already needed for blackboard. |
| Long-term Memory | **Buy** | PostgreSQL + pgvector | Durable, queryable, vector search. |
| Trajectory Store | **Build** (schema) / **Buy** (PostgreSQL) | PostgreSQL table | Append-only log; SQL for replay queries. |
| Observability | **Buy** | OTel + Prometheus + Grafana | Industry standard; self-hosted. |
| Evaluation Layer | **Build** | Python framework | Domain-specific; data privacy. |
| Protocol Gateway | **Build** + **Buy** (SDKs) | Thin adapters over MCP/A2A SDKs | Protocols evolving; thin is best. |

## 6. Required ADRs

All ADRs linked above. No additional ADR needed for this document; it is a consolidated view.

## 7. Diagrams

See [design/diagrams/01_overview.md](../diagrams/01_overview.md) — the architecture overview shows all selected technologies.

## 8. References

- Confluent: [Event-Driven Multi-Agent Systems](https://www.confluent.io/blog/event-driven-multi-agent-systems/) — Kafka-centric but informative for bus selection.
- Google Cloud: [Choose your agentic AI architecture components](https://docs.cloud.google.com/architecture/choose-agentic-ai-architecture-components) — component selection guidance.
- NATS documentation: [JetStream](https://docs.nats.io/nats-concepts/jetstream) — persistence, consumer groups.
