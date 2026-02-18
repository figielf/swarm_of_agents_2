# Glossary (draft)

- **Agent Runtime**: The execution environment and lifecycle manager for agents (scheduling, concurrency, retries, timeouts).
- **Event Bus**: Pub/sub messaging backbone used for inter-agent communication (topics/subjects/streams).
- **Trajectory**: The ordered sequence of events/messages (including tool calls and responses) that occurred during a single run/session across one or more agents; the unit you can inspect and replay.
- **Trajectory Store**: Durable record of every event/message (for audit, debugging, replay).
- **Shared Memory**: Logical “knowledge space” agents read/write (session memory, long-term memory, stigmergy/blackboard).
- **Tool Gateway**: Standardized interface for tools (APIs/DB queries), with authZ, audit, and rate limiting.
