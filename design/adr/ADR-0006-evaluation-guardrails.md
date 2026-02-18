# ADR-0006: Evaluation and Guardrails Approach — Built-in Framework

- Status: Accepted
- Date: 2026-02-18
- Decision owners: Platform Architecture Team
- Related requirements: R6 (built-in evaluation), R7 (planning-reflection loops), R9 (automated prompt runs)
- Related docs: [considerations/08](../considerations/08_evaluation_reflection_and_guardrails.md)

## Context

LLM-based agents produce non-deterministic outputs that may be incorrect, harmful, or off-brand. The framework needs structured quality gates at three boundaries:
1. **Tool-call boundary**: authorization, input validation, output sanity.
2. **Agent output boundary**: per-agent quality (relevance, factuality, tone).
3. **System response boundary**: end-to-end safety and compliance.

Additionally, agents should support **self-reflection loops** where they revise their output before publishing.

External evaluation platforms (Patronus AI, Galileo) were considered but rejected for Phase 1–2 due to data privacy concerns (agent outputs leaving the network), latency (external API calls), and cost.

## Decision

Build a **built-in evaluation framework** with three evaluator types:
1. **Rule-based**: regex, keyword blocklists, PII detectors, SQL injection detectors, price-range validators.
2. **LLM-as-judge**: a separate (cheaper) LLM call that scores output on configurable dimensions.
3. **Classifier-based**: fine-tuned models for toxicity, sentiment, brand-voice compliance.

Evaluators are registered per agent and at the system boundary. All evaluation results are emitted as `eval.*` events to the Trajectory Store.

**Reflection loops** are integrated into the Agent Runtime as an optional post-processing phase with configurable `max_reflection_rounds` (default: 2).

## Options considered

### Option A — External evaluation platform
- **Pros**: Pre-built evaluators. Managed dashboards.
- **Cons**: Data privacy. Latency. Cost. Limited domain-specific evaluation.
- **Risks**: Vendor dependency; SLA alignment.

### Option B — Built-in evaluation framework — chosen
- **Pros**: Full control. Data privacy. Domain-specific evaluators. Low latency (in-process).
- **Cons**: Must build and maintain.
- **Risks**: Engineering effort for evaluator development.

### Option C — Hybrid (built-in + optional external)
- **Pros**: Best of both worlds.
- **Cons**: Integration complexity.
- **Risks**: Acceptable; planned for Phase 3+.

## Rationale

Data privacy is paramount in e-commerce (customer data, business logic). Domain-specific evaluators (product spec accuracy, pricing correctness) cannot be provided by generic external platforms. In-process evaluation avoids the latency of external API calls, critical for meeting our p95 < 500ms evaluation SLO.

Hybrid (Option C) is planned for Phase 3+ to leverage specialized safety evaluators from mature external platforms.

## Consequences

**Easier:**
- Full control over evaluation logic, latency, and data privacy.
- Domain-specific evaluators (e-commerce pricing, inventory, product accuracy).
- Evaluation results are first-class Trajectory Store events.

**Harder:**
- Must build evaluators from scratch (rule-based is low effort; LLM-as-judge requires prompt engineering; classifiers require training data).
- Reflection loop adds complexity to the Agent Runtime.

## Follow-ups

- Implement `Evaluator` interface and `EvaluatorPipeline`.
- Build initial rule-based evaluators: PII detector, SQL injection detector, keyword blocklist.
- Build LLM-as-judge evaluator with configurable criteria and threshold.
- Implement reflection loop in Agent Runtime.
- Define mandatory system-level guardrails (toxicity, PII leak, content policy).
- Plan Phase 3 hybrid integration with external evaluation platforms.
