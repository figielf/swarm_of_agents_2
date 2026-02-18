# Follow-up Copilot Prompts (use as iterative improvements)

## Prompt 1 — Decide orchestration strategy + hybrid model
Propose a final recommendation for when to use:
- coordinator/orchestrator pattern,
- leaderless swarm,
- hybrid (dispatcher + partial coordination).
Add/Update ADRs and ensure `design/high_level_architecture.md` reflects the final decision.

## Prompt 2 — Event taxonomy for e-commerce
Design an event taxonomy oriented around:
- user interaction,
- product search & retrieval,
- cart/checkout,
- payments,
- user preference learning,
- long/short-term memory updates,
- upsell/cross-sell,
- evaluation/guardrails events,
- operational/system events.
Update `design/considerations/02_event_taxonomy.md` and add diagrams.

## Prompt 3 — Streaming chunk protocol (multimodal-ready)
Define:
- message envelope,
- chunk begin/end markers,
- correlation IDs,
- ordering guarantees,
- partial aggregation rules,
- retry/idempotency strategy.
Update docs + ADRs.

## Prompt 4 — Trajectory replay + observability
Design:
- trace IDs/span IDs propagation,
- message log retention and privacy,
- deterministic replay strategy (where possible),
- “flight recorder” approach for incidents.
Update `design/considerations/09_observability_tracing_replay.md` + ADRs.

## Prompt 5 — Buy vs build: runtime + messaging + state
Compare options:
- Kafka / Redpanda / Pulsar / NATS / cloud-managed equivalents,
- stream processing (Flink / Kafka Streams) vs custom workers,
- state store options (Redis, Postgres, event store, vector DB, graph DB),
- Python runtime frameworks (Ray, Celery, Temporal SDK, custom asyncio).
Update `design/considerations/12_buy_vs_build_stack_selection.md` and ADRs.

## Prompt 6 — Security + compliance + guardrails
Threat model and controls:
- per-agent permissions and tool access,
- PII handling,
- audit trails,
- prompt injection defenses,
- policy checks.
Update `design/considerations/11_security_privacy_compliance.md` + ADRs.

## Prompt 7 — Minimal PoC roadmap
Define a minimal Python PoC plan (no code required yet):
- which agents,
- which events,
- which stores,
- how to demo scaling + replay + evaluation.
Add to `design/high_level_architecture.md` and create a new consideration doc.
