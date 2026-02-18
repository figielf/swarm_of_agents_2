# Diagram: Multi-agent Collaboration Patterns (Event-driven)

## Coordinator / Orchestrator pattern (event-driven)

```mermaid
sequenceDiagram
  autonumber
  participant User
  participant Coord as Coordinator Agent
  participant Bus as Event Bus
  participant A1 as Specialist Agent A
  participant A2 as Specialist Agent B
  participant Eval as Evaluation Layer

  User->>Coord: User request
  Coord->>Bus: Publish Task(A)
  Coord->>Bus: Publish Task(B)
  Bus-->>A1: Task(A)
  Bus-->>A2: Task(B)
  A1->>Bus: Result(A)
  A2->>Bus: Result(B)
  Coord->>Eval: Synthesize + Evaluate
  Eval-->>Coord: Pass/Fail + feedback
  Coord-->>User: Response (stream)
```

## Leaderless Swarm (dispatcher + all-to-all)

```mermaid
flowchart TD
  U[User] --> D[Dispatcher]
  D --> EB[(Event Bus)]
  EB --> A[Agent A]
  EB --> B[Agent B]
  EB --> C[Agent C]
  A <--> B
  B <--> C
  A <--> C
  A -->|writes| SM[(Shared Memory / Stigmergy)]
  B -->|reads/writes| SM
  C -->|reads/writes| SM
  C --> F[Finalizer / Response Agent]
  F --> U
```

## Blackboard (shared memory + opportunistic agents)

```mermaid
flowchart LR
  BB[(Blackboard / Shared Memory)]
  A1[Agent 1] -->|post| BB
  A2[Agent 2] -->|post| BB
  A3[Agent 3] -->|post| BB
  BB -->|read| A1
  BB -->|read| A2
  BB -->|read| A3
```

## Market-based (auction/bidding)

```mermaid
sequenceDiagram
  autonumber
  participant Req as Request Source
  participant Auction as Auctioneer / Market Maker
  participant A as Agent A
  participant B as Agent B
  participant C as Agent C

  Req->>Auction: New Task
  Auction-->>A: Request bids
  Auction-->>B: Request bids
  Auction-->>C: Request bids
  A-->>Auction: Bid (cost/latency/confidence)
  B-->>Auction: Bid (cost/latency/confidence)
  C-->>Auction: Bid (cost/latency/confidence)
  Auction->>B: Assign task to winner
  B-->>Auction: Result
  Auction-->>Req: Final result
```
