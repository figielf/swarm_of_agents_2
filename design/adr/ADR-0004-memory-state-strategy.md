# ADR-0004: Memory and State Strategy — Tiered (Redis + PostgreSQL/pgvector)

- Status: Accepted
- Date: 2026-02-18
- Decision owners: Platform Architecture Team
- Related requirements: R1 (production-ready), R4 (multiple comm patterns — blackboard), R8 (trajectory capture)
- Related docs: [considerations/06](../considerations/06_memory_architecture_shared_state.md), [considerations/12](../considerations/12_buy_vs_build_stack_selection.md)

## Context

Agents require multiple memory tiers:
1. **Session memory**: current conversation context (fast, ephemeral).
2. **Long-term memory**: user history, preferences, past interactions (durable, queryable).
3. **Blackboard**: shared workspace for leaderless swarm collaboration (fast, pub/sub notifications).
4. **Semantic memory**: vector embeddings for RAG (product catalog, FAQs, policies).

We must select technologies that balance performance, durability, operational complexity, and Python client support.

## Decision

Use a **tiered memory architecture**:
- **Redis** for session memory and blackboard (TTL-bounded, sub-ms latency, pub/sub for change notifications).
- **PostgreSQL + pgvector** for long-term memory and semantic memory (durable, SQL-queryable, vector similarity search).

Agents interact with all memory tiers through a unified **MemoryClient** abstraction.

## Options considered

### Option A — Redis for everything
- **Pros**: Single technology. Sub-ms latency.
- **Cons**: Volatile (persistence adds complexity). RediSearch is less mature than pgvector. Expensive for large long-term storage.
- **Risks**: Data loss; RAM costs at scale.

### Option B — Tiered (Redis + PostgreSQL/pgvector) — chosen
- **Pros**: Best tool for each tier. PostgreSQL is enterprise-standard. pgvector handles moderate-scale vector search.
- **Cons**: Two technologies to operate.
- **Risks**: Cross-tier queries require application-level joins.

### Option C — Tiered + dedicated vector DB (Qdrant, Weaviate)
- **Pros**: Superior vector search at large scale (>10M embeddings).
- **Cons**: Third technology. Overkill for Phase 1–2.
- **Risks**: Operational overhead.

## Rationale

Redis excels at session-scoped, high-throughput reads/writes and provides pub/sub for blackboard notifications. PostgreSQL is already a standard enterprise dependency, provides SQL queryability for long-term memory, and pgvector handles moderate-scale vector search without introducing another service. Starting with two well-understood technologies minimizes operational risk. A dedicated vector DB can be adopted later if pgvector performance degrades.

## Consequences

**Easier:**
- Fast session memory and blackboard (Redis).
- Durable long-term memory with SQL queries (PostgreSQL).
- Single MemoryClient API hides tier complexity from agents.

**Harder:**
- Cross-tier data access requires application-level coordination.
- Redis persistence (AOF) must be configured for blackboard durability.
- pgvector performance must be monitored (plan for dedicated vector DB at scale).

## Follow-ups

- Implement MemoryClient abstraction with async drivers (`redis-py`, `asyncpg`).
- Configure Redis AOF persistence for blackboard data.
- Set up pgvector extension and vector indices in PostgreSQL.
- Define data retention policies (session TTL, long-term retention, PII deletion).
- Monitor pgvector query latency; plan vector DB migration if p95 > 50ms.
