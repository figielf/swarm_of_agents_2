# ADR-0005: Streaming Chunk Protocol — Begin/End Framed Events

- Status: Accepted
- Date: 2026-02-18
- Decision owners: Platform Architecture Team
- Related requirements: R5 (async + streaming with chunk begin/end markers)
- Related docs: [considerations/05](../considerations/05_streaming_chunking_and_multimodal_sync.md), [diagrams/03](../diagrams/03_streaming_chunks.md)

## Context

Agent responses must be streamed incrementally to the UI for low-latency rendering. E-commerce UIs combine multiple modalities (text, product cards, carousels) that must be synchronized. The streaming protocol must:
- Work identically for single-message and multi-chunk responses (unified contract).
- Support multimodal synchronization (multiple concurrent streams within one turn).
- Be compatible with the Event Bus (discrete events, not byte streams).
- Enable full trajectory capture and replay of streamed responses.

## Decision

Adopt a **chunk-framed streaming protocol** on the Event Bus with three event types:

1. `stream.begin` — Opens a stream (`message_id`, `trace_id`, `modality`, `expected_chunks`).
2. `stream.chunk` — Carries payload (`seq_no`, `payload`, `is_partial`, `content_type`).
3. `stream.end` — Closes the stream (`total_chunks`, `checksum`, `final`).

**Design invariant**: A single-message response uses this same protocol with N=1: `Begin → Chunk(seq_no=1) → End`. Consumers never need special handling for non-streamed responses.

At the edge (Channel Gateway → browser), these events are translated into **Server-Sent Events (SSE)**.

## Options considered

### Option A — Raw byte streaming (SSE/WebSocket passthrough)
- **Pros**: Simple; no framing overhead.
- **Cons**: No explicit begin/end markers. No multimodal correlation. Incompatible with Event Bus (needs discrete events). Replay requires raw byte reconstruction.
- **Risks**: Consumers cannot distinguish stream boundaries.

### Option B — Chunk-framed protocol on Event Bus — chosen
- **Pros**: Unified protocol. Event Bus compatible. Full trajectory capture. Multimodal alignment via `correlation_group` and `modality` tags. Checksum validation.
- **Cons**: Slight overhead (event envelope per chunk). Requires seq_no tracking.
- **Risks**: Chunk loss (mitigated by `total_chunks` and `checksum`).

## Rationale

The Event Bus requires discrete messages; raw streaming is incompatible. The chunk-framed protocol provides:
1. **Unified handling**: N=1 is the same as N>1.
2. **Multimodal sync**: `correlation_group` + `modality` tags enable UI alignment.
3. **Replay**: every chunk is a stored event; trajectory replay reconstructs the exact stream.
4. **Integrity**: `checksum` in `stream.end` detects data corruption or loss.

SSE at the gateway edge is a thin translation layer, not a protocol decision.

## Consequences

**Easier:**
- UI receives a uniform stream protocol regardless of agent response type.
- Trajectory replay includes full streaming behavior.
- Multimodal rendering is built into the protocol.

**Harder:**
- Agent SDK must produce chunk-framed events (not raw text).
- Consumers must handle seq_no tracking and checksum validation.
- Agent crashes mid-stream require synthetic `stream.end` events (runtime handles this).

## Follow-ups

- Implement chunk-framing in the Agent Runtime SDK.
- Implement SSE translation in the Channel Gateway.
- Define default chunk size guidelines per modality.
- Implement synthetic `stream.end` on agent crash/timeout.
- Build UI rendering logic for multimodal stream alignment.
