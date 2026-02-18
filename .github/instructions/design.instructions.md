---
applyTo: "design/**"
---

When working under design/:
- Always keep docs cross-linked (high_level_architecture.md ↔ considerations ↔ ADRs ↔ diagrams).
- Prefer Mermaid for diagrams.
- Cite sources from design/references/reading_list.md.

Diagram conventions (design/diagrams/):
- For each topic/pattern, include **two** Mermaid diagrams:
	- **DataFlow**: `flowchart` (structural data movement)
	- **Activity**: `sequenceDiagram` (event/message ordering)
