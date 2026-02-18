# Diagram: Streaming Chunks and Multimodal-ready Markers

This topic is documented with two complementary views:
- **DataFlow** diagram (Mermaid `flowchart`) showing structural data movement.
- **Activity** diagram (Mermaid `sequenceDiagram`) showing message/event ordering.

## Streaming chunks

Canonical contract: all agent responses are represented as a **chunk-framed stream** where the number of chunks $N \ge 1$.
- A “single message” is encoded as `Begin` → `Chunk(seq_no=1)` → `End`.
- A “streamed message” is the same contract with $N > 1$.

### DataFlow

```mermaid
flowchart TD
  A[Agent] --> EB[(Event Bus)]
  EB --> UI[Channel / UI]

  A -->|ResponseChunkBegin| EB
  A -->|ResponseChunk seq_no=1..N| EB
  A -->|ResponseChunkEnd| EB
  EB --> UI

  ASM[Assemble message\nN >= 1] --> RND[Render\nincremental or at end]
  UI --> ASM
  RND --> UI
```

### Activity

```mermaid
sequenceDiagram
  autonumber
  participant Agent
  participant Bus as Event Bus
  participant UI as Channel/UI

  Agent->>Bus: ResponseChunkBegin (message_id, trace_id, modality=text)
  loop N chunks (N >= 1)
    Agent->>Bus: ResponseChunk (seq_no, payload)
    Bus-->>UI: Forward chunk event
  end
  Agent->>Bus: ResponseChunkEnd (message_id, checksum, final=true)

  Note over UI: A “single message” is N=1 (Begin+Chunk+End)
  Note over UI: UI can align modalities by (message_id, modality, seq_no)
```
