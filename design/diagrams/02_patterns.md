# Diagram: Multi-agent Collaboration Patterns (Event-driven)

Each pattern below is documented with two complementary views:
- **DataFlow** diagram (Mermaid `flowchart`) showing structural data movement.
- **Activity** diagram (Mermaid `sequenceDiagram`) showing message/event ordering.

## Coordinator / Orchestrator pattern (event-driven)

### DataFlow

```mermaid
flowchart TD
  U[User] --> C[Coordinator Agent]
  C --> EB[(Event Bus)]
  EB --> A1[Specialist Agent A]
  EB --> A2[Specialist Agent B]
  A1 --> EB
  A2 --> EB
  EB --> C
  C --> E[Evaluation Layer]
  E --> C
  C --> U
```

### Activity

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

### DataFlow

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

### Activity

```mermaid
sequenceDiagram
  autonumber
  participant User
  participant Disp as Dispatcher
  participant Bus as Event Bus
  participant A as Agent A
  participant B as Agent B
  participant C as Agent C
  participant SM as Shared Memory / Stigmergy
  participant F as Finalizer / Response Agent

  User->>Disp: User request
  Disp->>Bus: Publish TaskBroadcast
  Bus-->>A: TaskBroadcast
  Bus-->>B: TaskBroadcast
  Bus-->>C: TaskBroadcast

  par Peer collaboration
    A->>Bus: Publish Msg(A->B/C)
    B->>Bus: Publish Msg(B->A/C)
    C->>Bus: Publish Msg(C->A/B)
  end

  A->>SM: Write intermediate findings
  B->>SM: Read/write intermediate findings
  C->>SM: Read/write intermediate findings

  C->>F: Candidate answer / synthesis
  F-->>User: Response (stream)
```

## Blackboard (shared memory + opportunistic agents)

### DataFlow

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

### Activity

```mermaid
sequenceDiagram
  autonumber
  participant BB as Blackboard / Shared Memory
  participant A1 as Agent 1
  participant A2 as Agent 2
  participant A3 as Agent 3

  A1->>BB: Post hypothesis / partial result
  A2->>BB: Post observation / evidence
  A3->>BB: Post candidate solution

  BB-->>A1: Notify update / allow read
  BB-->>A2: Notify update / allow read
  BB-->>A3: Notify update / allow read

  A1->>BB: Read latest state
  A2->>BB: Read latest state
  A3->>BB: Read latest state
```

## Market-based (auction/bidding)

### DataFlow

```mermaid
flowchart TD
  R[Request Source] --> Auction[Auctioneer / Market Maker]
  Auction -->|request bids| A[Agent A]
  Auction -->|request bids| B[Agent B]
  Auction -->|request bids| C[Agent C]
  A -->|bid| Auction
  B -->|bid| Auction
  C -->|bid| Auction
  Auction -->|assign task| W[Winning Agent]
  W -->|result| Auction
  Auction --> R
```

### Activity

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
