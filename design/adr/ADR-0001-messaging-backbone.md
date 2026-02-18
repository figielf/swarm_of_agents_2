# ADR-0001: Messaging Backbone — NATS JetStream

- Status: Accepted
- Date: 2026-02-18
- Decision owners: Platform Architecture Team
- Related requirements: R1 (production-ready), R3 (horizontal scaling), R4 (multiple comm patterns), R5 (async + streaming), R8 (trajectory capture)
- Related docs: [considerations/01](../considerations/01_communication_patterns.md), [considerations/12](../considerations/12_buy_vs_build_stack_selection.md)

## Context

The event-driven agentic swarm framework requires a pub/sub messaging backbone that supports:
- Topic-based routing with consumer groups (for load-balanced agent pools).
- Persistent streams (messages must survive broker restarts for trajectory capture).
- Ordered delivery per partition/subject (for streaming chunk sequencing).
- Dead-letter queues (for failed message handling).
- High throughput at moderate scale (target: 10K events/sec peak).
- Excellent Python async client support.

The system must avoid the operational heavyweight of Apache Kafka while still providing persistence and delivery guarantees.

## Decision

Use **NATS JetStream** as the Event Bus backbone.

## Options considered

### Option A — NATS JetStream
- **Summary**: Lightweight, high-performance messaging system with built-in persistence (JetStream), consumer groups (queue groups), and subject-based routing. Single binary deployment.
- **Pros**: Simple operations (single binary, no ZooKeeper). Excellent Python client (`nats-py` with asyncio support). Sub-millisecond latency. Persistent streams with replay capability. Built-in consumer groups and dead-letter queues.
- **Cons**: Smaller community than Kafka. No built-in schema registry (we use a git-based schema registry instead). Fewer ecosystem integrations.
- **Risks**: If we outgrow NATS JetStream's throughput (unlikely at our scale), migration to Kafka would be a significant effort.

### Option B — Apache Kafka
- **Summary**: Industry-standard distributed streaming platform. Battle-tested at extreme scale.
- **Pros**: Massive community. Confluent ecosystem (Schema Registry, ksqlDB, Flink). Proven at >100K events/sec.
- **Cons**: Operationally heavy (brokers + ZooKeeper/KRaft). Python client (`confluent-kafka`) requires C library (`librdkafka`). Overkill for our expected volume (<10K events/sec). Higher infrastructure cost.
- **Risks**: Over-engineering; team spends more time operating Kafka than building the framework.

### Option C — Redis Streams
- **Summary**: Redis Streams provides a log-based data structure with consumer groups.
- **Pros**: Already in the stack (session memory). Simple API.
- **Cons**: Limited durability guarantees. Consumer group support is basic compared to NATS/Kafka. Not designed as a primary messaging backbone. Mixing message bus and cache in one Redis instance causes capacity planning issues.
- **Risks**: Redis Streams at scale requires careful memory management; not intended for high-volume event streaming.

### Option D — RabbitMQ
- **Summary**: Mature message broker with queue-based semantics.
- **Pros**: Well-understood. Good Python support (`aio-pika`). Flexible routing (exchanges, bindings).
- **Cons**: Queue-based (not log-based); messages are consumed once — replay requires separate mechanisms. No native persistent streams. Higher latency than NATS for pub/sub patterns.
- **Risks**: Replay/trajectory capture requires a separate event store; adds architectural complexity.

## Rationale

NATS JetStream provides the best balance of:
1. **Operational simplicity**: single binary, no external dependencies. Team can operate it without dedicated messaging expertise.
2. **Persistence**: JetStream streams retain messages for trajectory capture and replay.
3. **Python support**: `nats-py` is async-native, well-maintained, and lightweight.
4. **Performance**: sub-millisecond publish latency; handles 10K+ events/sec on modest hardware.
5. **Consumer groups**: built-in queue groups for load-balanced agent pools.

Kafka was rejected because its operational overhead is disproportionate to our scale. Redis Streams and RabbitMQ lack the persistent stream semantics we need for trajectory capture.

## Consequences

**Easier:**
- Agent-to-agent communication via simple publish/subscribe.
- Trajectory capture: all messages are retained in JetStream streams.
- Operational burden is low (single binary, simple configuration).

**Harder:**
- No built-in schema registry; we build a git-based one (lightweight).
- If we ever need Kafka-scale throughput (>100K events/sec), migration would be significant.
- Team must learn NATS-specific concepts (subjects, streams, consumers, ack policies).

## Follow-ups

- Configure NATS JetStream streams: retention policy (time + size), replication factor (3 for production), subject hierarchy per event taxonomy.
- Implement dead-letter queue pattern using NATS advisory subjects.
- Set up monitoring (NATS Prometheus exporter + Grafana dashboards).
- Document subject naming convention aligned with event taxonomy.
