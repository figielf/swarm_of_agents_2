# Event taxonomy for e-commerce agent swarms

## 1. Context and problem statement

An event-driven multi-agent system needs a well-defined **event taxonomy** — a classification of all event types that flow through the Event Bus. Without a taxonomy, teams create ad-hoc event shapes, leading to inconsistency, schema drift, and integration friction.

**Constraints:**
- Events must be self-describing (consumers can route/filter without external lookups).
- Schema must support backward-compatible evolution (new fields are additive; old consumers tolerate unknown fields).
- Events carry tracing metadata for end-to-end observability.
- Must handle both synchronous request-reply patterns (via correlation IDs) and fire-and-forget patterns.
- E-commerce domain requires PII-awareness (events may contain customer data).

## 2. Requirements coverage

| Requirement | Coverage |
|---|---|
| R1 — Production-ready event-driven | Core: defines the event vocabulary. |
| R4 — Multiple communication patterns | Event types must support coordinator dispatch, peer messages, broadcasts, and bids. |
| R5 — Async with streaming | Streaming events (`ChunkBegin`, `Chunk`, `ChunkEnd`) are first-class event types. |
| R8 — Trajectory capture/replay | Every event is recorded; taxonomy determines what is captured. |
| R9 — Automated prompt runs | `PromptRun.*` events enable CI-driven batch execution. |

## 3. Options

### Option A — Flat event namespace

All events share a single `event_type` string field (e.g., `"task.assigned"`, `"agent.response"`). Routing is based on string matching or prefix filters.

**Pros:**
- Simple to implement; no hierarchical complexity.
- Easy to grep in logs.

**Cons:**
- Name collisions as the system grows.
- No structural grouping; hard to enforce governance.
- Routing rules become fragile string comparisons.

### Option B — Hierarchical event taxonomy (recommended)

Events are organized into a **category → action** hierarchy. Each event has a structured `event_type` composed of `{category}.{action}` and an optional `sub_action`. Categories are governed centrally; actions can be extended by teams.

**Proposed taxonomy:**

| Category | Events | Description |
|---|---|---|
| `session` | `session.started`, `session.ended`, `session.timeout` | User session lifecycle. |
| `task` | `task.created`, `task.assigned`, `task.completed`, `task.failed`, `task.timeout` | Task lifecycle (coordinator dispatching work). |
| `task.bid` | `task.bid.requested`, `task.bid.submitted`, `task.bid.accepted` | Market-based bidding. |
| `agent` | `agent.started`, `agent.heartbeat`, `agent.stopped`, `agent.error` | Agent lifecycle. |
| `message` | `message.sent`, `message.received`, `message.broadcast` | Inter-agent communication. |
| `stream` | `stream.begin`, `stream.chunk`, `stream.end` | Chunk-framed streaming. |
| `tool` | `tool.invoked`, `tool.result`, `tool.error` | Tool Gateway calls. |
| `eval` | `eval.requested`, `eval.passed`, `eval.failed`, `eval.reflection` | Evaluation Layer events. |
| `memory` | `memory.read`, `memory.write`, `memory.evict` | Shared Memory operations. |
| `prompt` | `prompt.loaded`, `prompt.version_changed` | Prompt Registry events. |
| `prompt_run` | `prompt_run.started`, `prompt_run.completed`, `prompt_run.failed` | CI/batch prompt runs. |
| `protocol` | `protocol.mcp.request`, `protocol.mcp.response`, `protocol.a2a.request`, `protocol.a2a.response` | Protocol Gateway events. |
| `registry` | `registry.agent.registered`, `registry.agent.deregistered`, `registry.agent.heartbeat`, `registry.capability.changed` | Agent Registry lifecycle and Capability Registry change events. See [considerations/17](17_agent_registry_and_discovery.md). |
| `system` | `system.health`, `system.config_changed`, `system.rate_limited` | Platform-level events. |

**Pros:**
- Clear governance: categories are owned by the platform team.
- Easy to add new event types within existing categories.
- Routing can use category-level subscriptions (e.g., subscribe to `eval.*`).
- Schema registry can enforce per-category schemas.

**Cons:**
- Requires upfront design effort and governance process.
- Over-categorization can lead to deep hierarchies.

### Option C — Schema-first (Avro/Protobuf) with auto-generated types

Each event type is defined as an Avro or Protobuf schema. Code generation produces typed event classes.

**Pros:**
- Strong compile-time guarantees (in statically typed languages).
- Schema evolution handled by Avro/Protobuf compatibility rules.

**Cons:**
- Python-first ecosystem has weaker Avro/Protobuf tooling compared to JSON Schema.
- Code generation adds build complexity.
- Overhead for a team that iterates quickly on event shapes.

## 4. Decision drivers

| Driver | Weight | Favors |
|---|---|---|
| Developer experience (Python) | High | Hierarchical + JSON Schema |
| Governance at scale | High | Hierarchical taxonomy |
| Schema evolution safety | High | JSON Schema with registry |
| Build simplicity | Medium | Hierarchical + JSON Schema |
| Tooling maturity | Medium | JSON Schema over Avro/Protobuf in Python |

## 5. Recommendation

**Recommended: Option B — Hierarchical event taxonomy with JSON Schema validation**

- Event types follow `{category}.{action}` naming.
- Each event type has a registered JSON Schema in the schema registry.
- Schema evolution follows **backward-compatible** rules (additive fields only; no required field removal).
- The platform team owns the category list; product teams can propose new actions within existing categories via PR review.

**Canonical envelope:**

```json
{
  "event_id": "uuid-v7",
  "event_type": "task.completed",
  "timestamp": "2026-02-18T12:00:00Z",
  "trace_id": "trace-uuid",
  "span_id": "span-uuid",
  "parent_span_id": "parent-span-uuid",
  "session_id": "session-uuid",
  "agent_id": "product-search-agent",
  "version": "1.2.0",
  "payload": { ... },
  "metadata": {
    "correlation_id": "request-uuid",
    "tenant_id": "acme-corp",
    "pii_flag": false
  }
}
```

**Risks / mitigations:**
| Risk | Mitigation |
|---|---|
| Teams create events outside the taxonomy | Schema validation at publish time rejects unregistered event types. |
| Event sprawl (too many event types) | Quarterly taxonomy review; deprecation process for unused events. |
| Schema changes break consumers | Backward-compatibility enforced by the schema registry; breaking changes require a new version. |

## 6. Required ADRs

- [ADR-0001: Messaging backbone](../adr/ADR-0001-messaging-backbone.md) — the bus that carries these events.
- [ADR-0005: Streaming chunk protocol](../adr/ADR-0005-streaming-chunk-protocol.md) — defines `stream.*` events.

## 7. Diagrams

See [design/diagrams/01_overview.md](../diagrams/01_overview.md) — events flow through the Event Bus between all components.

## 8. References

- Confluent: [Event-Driven Multi-Agent Systems](https://www.confluent.io/blog/event-driven-multi-agent-systems/) — event-driven backbone patterns.
- Google Cloud: [Choose your agentic AI architecture components](https://docs.cloud.google.com/architecture/choose-agentic-ai-architecture-components) — component interaction models.
