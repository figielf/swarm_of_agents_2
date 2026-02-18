# ADR-0009: Deployment, Scaling, and Isolation — Kubernetes per-Agent-Type Deployments

- Status: Accepted
- Date: 2026-02-18
- Decision owners: Platform Architecture Team, SRE Team
- Related requirements: R11 (multi-tenancy), R12 (scaling), R13 (resource isolation)
- Related docs: [considerations/10](../considerations/10_scaling_deployment_and_isolation.md), [considerations/11](../considerations/11_security_privacy_compliance.md)

## Context

The framework will run multiple agent types (e.g., ProductAgent, OrderAgent, SupportAgent, RecommendationAgent) with different resource profiles, scaling characteristics, and blast-radius requirements. A deployment model must support:
1. **Independent scaling**: each agent type scales based on its own queue depth and latency.
2. **Resource isolation**: a misbehaving agent type must not starve others.
3. **Multi-tenancy**: logical isolation for different business units or tenants.
4. **Rolling updates**: agent types must be deployable independently.

## Decision

Deploy each agent type as a **separate Kubernetes Deployment** with:
- **Dedicated resource requests/limits** (CPU, memory) per agent type.
- **Horizontal Pod Autoscaler (HPA)** driven by NATS JetStream consumer pending message count (via KEDA or custom metrics adapter).
- **Namespace-based multi-tenancy**: each tenant gets a dedicated Kubernetes namespace with resource quotas, network policies, and RBAC.
- **Pod Disruption Budgets (PDBs)**: ensure minimum availability during rollouts and node drains.
- **Graceful shutdown**: Agent Runtime handles SIGTERM by completing the current event, publishing a `lifecycle.draining` event, and exiting.

Infrastructure services (NATS JetStream, Redis, PostgreSQL, Protocol Gateway) run as shared services in a dedicated `infra` namespace with separate scaling policies.

## Options considered

### Option A — Monolithic deployment (all agents in one Deployment)
- **Pros**: Simple. Low operational overhead.
- **Cons**: No isolation. Scaling couples all agent types. One bad agent affects all.
- **Risks**: Unacceptable for production e-commerce.

### Option B — Per-agent-type Kubernetes Deployments — chosen
- **Pros**: Independent scaling. Resource isolation. Independent rollouts. Fault isolation.
- **Cons**: More Kubernetes objects to manage.
- **Risks**: Operational complexity; mitigated by Helm charts / Kustomize overlays and GitOps.

### Option C — Serverless / FaaS (Lambda, Cloud Run)
- **Pros**: Zero-ops scaling. Pay-per-invocation.
- **Cons**: Cold starts (problematic for latency SLOs). Limited control over runtime. Stateless-only. Vendor lock-in.
- **Risks**: Cold start latency unacceptable for p95 < 2s SLO.

### Option D — VM-based isolation
- **Pros**: Strongest isolation.
- **Cons**: Slow scaling. High cost. Heavy operational burden.
- **Risks**: Not justified for the isolation level needed.

## Rationale

Per-agent-type Kubernetes Deployments provide the best balance of isolation, scaling flexibility, and operational maturity:
1. **Scaling**: HPA on queue depth is the natural scaling signal for event-driven consumers.
2. **Isolation**: Resource limits prevent noisy-neighbor effects. Namespace isolation supports multi-tenancy.
3. **Rollouts**: Each agent type can be updated independently via rolling deployments with canary or blue-green strategies.
4. **Ecosystem**: Kubernetes is the de-facto standard; team expertise exists; tooling (Helm, ArgoCD, KEDA) is mature.

## Consequences

**Easier:**
- Agent types scale independently on their own queue depth.
- Resource isolation via Kubernetes limits and quotas.
- Independent rollouts and canary deployments per agent type.
- Multi-tenancy via namespace isolation with RBAC and network policies.

**Harder:**
- More Kubernetes manifests to maintain (mitigated by templating with Helm/Kustomize).
- Must set up KEDA or custom metrics adapter for NATS-based HPA.
- Must define and maintain resource profiles per agent type.

## Follow-ups

- Create Helm chart / Kustomize base for agent-type Deployments.
- Configure KEDA ScaledObject for NATS JetStream consumer scaling.
- Define resource profiles for each agent type based on load testing.
- Implement namespace provisioning automation for multi-tenancy.
- Set up GitOps pipeline (ArgoCD) for deployment management.
- Define Pod Disruption Budgets for each agent type.
- Implement graceful shutdown in Agent Runtime (SIGTERM handling).
- Configure network policies for namespace-level isolation.
