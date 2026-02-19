# Buy vs Build — Stack Selection Summary

## Decision Drivers

| Driver | Weight | Applies to |
|---|---|---|
| Operational simplicity | High | All components |
| Python ecosystem quality | High | Event Bus, Agent Runtime |
| Differentiation value | High | Agent Runtime, Evaluation Layer (build where we differentiate) |
| Enterprise maturity | High | Event Bus, stores |
| Team size (4–8 engineers) | High | Favor buy for undifferentiated heavy lifting |

## Component Decisions

### Event Bus — BUY → NATS JetStream

| Option | Pros | Cons |
|---|---|---|
| **NATS JetStream** ✅ | Lightweight, fast, persistent streams, consumer groups, subject-based routing, excellent Python client (`nats-py`). Single binary. Low ops burden. | Smaller community than Kafka. No built-in schema registry. |
| Apache Kafka | Industry standard, huge ecosystem (Schema Registry, ksqlDB, Flink). Battle-tested at extreme scale. | Operationally heavy (ZooKeeper/KRaft). Overkill for <10K events/sec. Python client requires C dependency. |
| Redis Streams | Already in stack. Simple API. | Limited durability. Basic consumer groups. Not designed as primary messaging backbone. |
| RabbitMQ | Mature, good Python support. | Queue-based (not log-based); harder to replay. No persistent streams. |
| Build custom | Full control. | Enormous effort. Not viable. |

### Agent Runtime — BUILD → Python asyncio

| Option | Pros | Cons |
|---|---|---|
| **Build lightweight runtime** ✅ | Full alignment with event-driven architecture. Thin layer for agent lifecycle, retries, timeouts. | ~2–3 weeks build + ~0.5 FTE ongoing. |
| LangGraph | Existing familiarity. Rich graph patterns. | Static graph limitations motivate this entire design. |
| AutoGen / CrewAI | Pre-built multi-agent patterns. | Impose foreign execution models. Don't integrate with Event Bus. |

**Rationale:** The Agent Runtime is the framework's core differentiator. It must align with the Event Bus and support specific lifecycle, retry, and streaming requirements.

### Session Memory — BUY → Redis

| Option | Pros | Cons |
|---|---|---|
| **Redis** ✅ | Sub-ms latency. Pub/sub for Blackboard notifications. Widely available as managed service. | Volatile unless persistence configured. |

### Long-term Memory — BUY → PostgreSQL + pgvector

| Option | Pros | Cons |
|---|---|---|
| **PostgreSQL + pgvector** ✅ | Durable, SQL-queryable, vector search. Single DB for long-term memory and Trajectory Store. | Vector search adequate but not SOTA at extreme scale. |
| Dedicated vector DB (Qdrant, Weaviate) | Superior vector search at scale. | Third technology to operate. Overkill for Phase 1–2. |

**Phased approach:** PostgreSQL + pgvector for Phase 1–2. Re-evaluate dedicated vector DB at Phase 3 if retrieval latency demands it.

### Observability — BUY → OpenTelemetry stack

| Option | Pros | Cons |
|---|---|---|
| **OTel + Jaeger/Tempo + Prometheus + Grafana** ✅ | Industry standard. Vendor-neutral. Self-hosted or managed. | Must integrate and operate multiple components. |
| Managed platform (Datadog, New Relic) | Pre-built dashboards. Fully managed. | Cost scales with volume. Cannot serve as Trajectory Store. Data leaves network. |

### Evaluation Layer — BUILD → Python framework

| Option | Pros | Cons |
|---|---|---|
| **Build in-house** ✅ | Full control. Domain-specific evaluators. No data exposure. | Must build and maintain evaluators. |
| External platform (Patronus, Galileo) | Pre-built evaluators. Dashboards. | Data privacy concerns. Cost. Latency. |

**Phased approach:** Build core evaluators in Phase 1–2. Consider hybrid with external platforms at Phase 3+ for specialized safety evaluators.

### Protocol Gateway — BUILD (thin adapters) + BUY (SDKs)

| Option | Pros | Cons |
|---|---|---|
| **Build thin adapters over MCP/A2A SDKs** ✅ | Protocols evolving; thin adapters easy to update. Full control over translation. | Must track protocol spec changes. |
| Adopt MCP SDK as framework | Pre-built protocol handling. | Still requires adaptation to Event Bus envelope. |

### Trajectory Store — BUILD (schema) + BUY (PostgreSQL)

Append-only log in PostgreSQL. Schema is custom; storage engine is off-the-shelf.

### Prompt Registry — BUILD → Git-based service

Git-versioned prompt templates with a lightweight HTTP service. External platforms (Humanloop, LangFuse) rejected for data privacy and integration reasons.

## Decision Summary

| Component | Decision | Technology | Rationale |
|---|---|---|---|
| Event Bus | **Buy** | NATS JetStream | Best simplicity / performance / persistence balance |
| Agent Runtime | **Build** | Python asyncio | Core differentiator; must align with Event Bus |
| Session Memory | **Buy** | Redis | Fast, mature, already needed for Blackboard |
| Long-term Memory | **Buy** | PostgreSQL + pgvector | Durable, queryable, vector search |
| Trajectory Store | **Build** (schema) / **Buy** (PG) | PostgreSQL table | Append-only log; SQL for replay queries |
| Observability | **Buy** | OTel + Prometheus + Grafana | Industry standard; self-hosted |
| Evaluation Layer | **Build** | Python framework | Domain-specific; data privacy |
| Protocol Gateway | **Build** + **Buy** (SDKs) | Thin adapters over MCP/A2A SDKs | Protocols evolving; thin is best |
| Prompt Registry | **Build** | Git-based service | IP stays in-house; CI-testable |
