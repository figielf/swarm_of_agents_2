---
applyTo: "summary/**"
---

## Purpose

The `summary/` folder is a **condensed, standalone summary** of the architecture design
for a **project management audience**. It must be readable without prior technical context
and without navigating into `design/`.

## Golden source

- `design/` is the **single source of truth** for all architecture information.
- `summary/` is a **derived artifact** — never treat it as a source of new information.
- If `summary/` contradicts `design/`, `design/` wins — fix `summary/` to match.

## When to update summary/

After **any** change to files under `design/` that affects content reflected in `summary/`,
cascade the change into the corresponding `summary/` file(s) in the same task.
Specifically watch for changes in:
- `design/high_level_architecture.md` → `summary/high_level_architecture.md`
- `design/considerations/12_buy_vs_build_stack_selection.md` → `summary/buy_vs_build_consideration.md`
- `design/diagrams/02_patterns.md` → `summary/communication.md` (Part 1)
- `design/diagrams/04_communication_and_tool_paths.md` → `summary/communication.md` (Part 2)
- `design/considerations/07_tooling_and_integrations.md` → `summary/communication.md` (Part 2)
- `design/considerations/14_protocol_wrappers_mcp_a2a.md` → `summary/communication.md` (Parts 2–3)
- `design/considerations/05_streaming_chunking_and_multimodal_sync.md` → `summary/communication.md` (Part 3)
- `design/considerations/*` (any) → `summary/components_considerations.md`
- `design/glossary.md` → `summary/glossary.md`
- Terminology changes in any design doc → all `summary/` files (terms must stay consistent)

## File inventory (summary/)

| File | Summarizes |
|------|-----------|
| `glossary.md` | `design/glossary.md` — canonical vocabulary |
| `high_level_architecture.md` | `design/high_level_architecture.md` — architecture overview with embedded diagrams and reading list |
| `buy_vs_build_consideration.md` | `design/considerations/12_buy_vs_build_stack_selection.md` — buy/build analysis per component |
| `communication.md` | `design/diagrams/02_patterns.md` + `design/diagrams/04_communication_and_tool_paths.md` — agent collaboration patterns, tool invocation & gateway paths, streaming protocol |
| `components_considerations.md` | All other `design/considerations/*.md` — one section per component |

## Writing rules

1. **Standalone & self-sufficient** — `summary/` files must NOT contain links or references
   to any files outside `summary/`. No references to ADRs, no `design/` paths, no `../` links.
2. **Cross-link within summary/** — files inside `summary/` may reference each other.
3. **No low-level details** — omit implementation specifics (code snippets, Pydantic models,
   exact config values) unless they are essential for understanding the architecture.
4. **Audience: project management** — write for readers who need to understand scope,
   decisions, trade-offs, timelines, and component responsibilities — not implementation.
5. **Diagrams: Mermaid only** — use Mermaid diagrams inline. Keep them simpler than the
   `design/` versions — focus on data flow and key interactions, not every edge case.
6. **Use glossary terms** — use the canonical terms from `summary/glossary.md` consistently.
   When a glossary term appears for the first time in a file, bold it.
7. **Concise** — each file should be readable in under 5 minutes.
   Prefer tables and bullet points over long prose.
8. **No ADR references** — do not mention ADR numbers, ADR file names, or link to ADR documents.

## HTML export (Confluence)

After **every** update to any file under `summary/`, regenerate the corresponding HTML files
in `summary/html/` by running:

```
.venv\Scripts\python.exe scripts/md_to_html.py
```

This script converts all `summary/*.md` files to Confluence-ready HTML under `summary/html/`.
The HTML files are the **canonical export** for Confluence — always keep them in sync with the
Markdown source.
