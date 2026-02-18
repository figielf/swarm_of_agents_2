# Diagram: Streaming Chunks and Multimodal-ready Markers

This topic is documented with two complementary views:
- **DataFlow** diagram (Mermaid `flowchart`) showing structural data movement.
- **Activity** diagram (Mermaid `sequenceDiagram`) showing message/event ordering.

## Streaming chunks

### DataFlow

```mermaid
flowchart TD
  A[Agent] --> EB[(Event Bus)]
  EB --> UI[Channel / UI]
  A -->|ResponseChunkBegin| EB
  A -->|ResponseChunk seq_no=1..N| EB
  A -->|ResponseChunkEnd| EB
  EB -->|Forward chunks| UI
  UI -->|Render incrementally| UI
```

### Activity

```mermaid
sequenceDiagram
  autonumber
  participant Agent
  participant Bus as Event Bus
  participant UI as Channel/UI

  Agent->>Bus: ResponseChunkBegin (message_id, trace_id, modality=text)
  loop chunks
    Agent->>Bus: ResponseChunk (seq_no, payload)
    Bus-->>UI: Forward chunk
  end
  Agent->>Bus: ResponseChunkEnd (message_id, checksum, final=true)

  Note over UI: UI can align modalities by (message_id, modality, seq_no)
```
