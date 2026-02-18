# Diagram: Architecture Overview

This topic is documented with two complementary views:
- **DataFlow** diagram (Mermaid `flowchart`) showing structural data movement.
- **Activity** diagram (Mermaid `sequenceDiagram`) showing message/event ordering for a typical request.

Sources: [high_level_architecture.md](../high_level_architecture.md), [reading_list.md](../references/reading_list.md)

## DataFlow

```mermaid
flowchart LR
  U[User / Channel] -->|HTTP / WebSocket| CGW[Channel Gateway]

  subgraph Platform["Agentic Swarm Platform"]
    CGW -->|Publish request event| EB[(Event Bus\nNATS JetStream)]

    EB --> COORD[Coordinator Agent]
    COORD -->|Delegate tasks| EB
    EB --> SA1[Specialist Agent A]
    EB --> SA2[Specialist Agent B]
    EB --> SAN[Specialist Agent N]

    subgraph Runtime["Agent Runtime (Python asyncio)"]
      COORD
      SA1
      SA2
      SAN
    end

    Runtime -->|tool.call events| TG[Tool Gateway]
    Runtime -->|eval.request| EV[Evaluation Layer]
    Runtime -->|read/write| SM[(Session Memory\nRedis)]
    Runtime -->|read/write| LTM[(Long-term Memory\nPostgreSQL + pgvector)]
    Runtime -->|read/write| BB[(Blackboard\nRedis pub/sub)]
    Runtime -->|append| TS[(Trajectory Store\nPostgreSQL)]
    EV -->|eval.result| TS
    TG -->|tool.result| EB

    PR[Prompt Registry\ngit-based] -->|load prompt| Runtime

    PGW[Protocol Gateway] -->|MCP / A2A ↔ native events| EB
  end

  TG --> EXT[External Systems / APIs]
  PGW --> EXTAG[External Agents / MCP Clients]
  CGW -->|SSE stream| U
```

Notes:
- All inter-agent communication flows through the **Event Bus** (NATS JetStream pub/sub).
- The **Trajectory Store** captures every event for replay, audit, and evaluation.
- The **Protocol Gateway** translates MCP / A2A at the boundary; internal agents remain protocol-agnostic.
- The **Prompt Registry** is a git-based store loaded at agent startup; prompts are versioned and CI-tested.

## Activity

A typical end-to-end request flow through the platform:

```mermaid
sequenceDiagram
  autonumber
  participant User
  participant CGW as Channel Gateway
  participant Bus as Event Bus (NATS JetStream)
  participant Coord as Coordinator Agent
  participant SA as Specialist Agent
  participant TG as Tool Gateway
  participant Eval as Evaluation Layer
  participant Mem as Memory (Redis / PG)
  participant TS as Trajectory Store

  User->>CGW: HTTP request
  CGW->>Bus: Publish task.requested
  Bus-->>Coord: task.requested

  Coord->>Mem: Load session context
  Mem-->>Coord: Context
  Coord->>TS: Append trajectory event

  Coord->>Bus: Publish task.delegated (to Specialist)
  Bus-->>SA: task.delegated

  SA->>Bus: Publish tool.call.requested
  Bus-->>TG: tool.call.requested
  TG->>TG: Execute tool (rate-limit, retry, idempotent)
  TG->>Bus: Publish tool.call.completed
  Bus-->>SA: tool.call.completed

  SA->>Mem: Write intermediate result
  SA->>Bus: Publish task.completed (result)
  Bus-->>Coord: task.completed

  Coord->>Eval: Evaluate synthesized response
  Eval-->>Coord: eval.result (pass/fail)
  Eval->>TS: Append eval event

  alt Eval PASS
    Coord->>Bus: Publish stream.begin
    loop N chunks
      Coord->>Bus: Publish stream.chunk (seq_no, payload)
      Bus-->>CGW: stream.chunk
      CGW-->>User: SSE chunk
    end
    Coord->>Bus: Publish stream.end
  else Eval FAIL (reflection)
    Coord->>Coord: Revise output (max 2 rounds)
    Coord->>Eval: Re-evaluate
  end

  Coord->>TS: Append final trajectory event
```
