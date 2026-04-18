# Jart-OS — Canonical Roadmap

> **Source of truth for project maturity.**  
> Every component tracked. Every status visible. Every dependency clear.  
> Last updated: 2026-04-18

---

## How to Read This

### Maturity Levels

| Level | Icon | Meaning | What the gatekeeper does |
|-------|------|---------|--------------------------|
| **Stable** | ✅ | Decided, implemented, validated, unchanged | **BLOCKS** if you break it |
| **Draft** | 🟡 | Designed, may be partially implemented, subject to change | **WARNS** but doesn't block |
| **Planned** | ⬜ | Identified need, not yet designed | Does nothing |

### Escalón (Step) Model

Jart-OS is built in **8 escalones**. Each escalón depends on ALL previous escalones.  
You cannot build agents (E5) without messaging (E2). You cannot distribute (E6) without specs (E0).

```
E0 Canon        ← The rules (everything depends on this)
E1 Infrastructure ← The base services
E2 Framework    ← The reusable code
E3 MCP Ecosystem ← The backpack servers
E4 Security     ← Protection + governance
E5 Agents       ← Running autonomous entities + observability
E6 Distribution ← Getting it to users (CLI)
E7 Federation   ← Connecting multiple instances
```

### Progress Summary

| Escalón | ✅ Stable | 🟡 Draft | ⬜ Planned | Progress |
|---------|-----------|----------|-----------|----------|
| E0 Canon & Conventions | 7 | 3 | 2 | 58% |
| E1 Infrastructure | 5 | 1 | 1 | 71% |
| E2 Framework & Protocols | 10 | 3 | 1 | 69% |
| E3 MCP Ecosystem | 6 | 2 | 3 | 55% |
| E4 Security & Governance | 5 | 5 | 4 | 33% |
| E5 Agents & Observability | 5 | 6 | 5 | 31% |
| E6 Distribution | 1 | 1 | 7 | 11% |
| E7 Federation & Integration | 0 | 0 | 6 | 0% |
| **TOTAL** | **39** | **21** | **29** | **** |

---

## E0 — Canon & Conventions

> **The rules that define what IS and IS NOT Jart-OS.**  
> Everything else depends on these being decided first.

| # | Component | Status | Spec file | Evidence | Notes |
|---|-----------|--------|-----------|----------|-------|
| E0.1 | 10-tier directory structure | ✅ | `spec/tier-structure.json` | Mac Mini running, all 10 tiers created | Core identity of Jart-OS |
| E0.2 | Port convention (1XXYY) | ✅ | `spec/port-convention.json` | All 16 services follow it | XX=tier, YY=sequence |
| E0.3 | Entity naming (`{TYPE}-{name}`, no suffixes) | ✅ | `spec/naming-schema.json` | TAXONOMY.md v2.0, 9 entities | Industry-standard: type as namespace, name as function |
| E0.4 | `.jart-manifest` schema | ✅ | `spec/manifest-schema.json` | All 4 repos have valid manifests | version, category, stack, compliance |
| E0.5 | Entity taxonomy (9 entities, 0 suffixes) | ✅ | `spec/taxonomy-schema.json` | TAXONOMY.md ratified | MCP, AGENT, CLI, PIPELINE, SKILL, HOOK, RULE, TEMPLATE, SPEC |
| E0.6 | Docker Compose `include:` pattern | ✅ | `spec/docker-schema.json` | Root compose includes 16 services | Each service self-contained |
| E0.7 | `jart-os` GitHub topic for membership | ✅ | `spec/taxonomy-schema.json` | All repos tagged | No topic = not Jart-OS |
| E0.8 | Semantic versioning process | 🟡 | `spec/versioning-schema.json` | VERSION files exist, CHANGELOG exists | No formal release automation yet |
| E0.9 | Conventional commits | 🟡 | `spec/commits-schema.json` | Some commits follow it | Not enforced, not documented as rule |
| E0.10 | Release process definition | 🟡 | `spec/release-schema.json` | CHANGELOG.md exists | No automated releases |
| E0.11 | ROADMAP maturity model | ⬜ | `spec/roadmap-schema.json` | This file | Needs spec schema |
| E0.12 | Dual-account mirror convention | ⬜ | `spec/mirror-schema.json` | 4 repos mirroring | Not formalized as spec |

---

## E1 — Infrastructure

> **The base services that must be running before anything else works.**

| # | Component | Status | Spec file | Evidence | Notes |
|---|-----------|--------|-----------|----------|-------|
| E1.1 | Redis (state, cache, locks) | ✅ | `spec/redis-schema.json` | Running :10301, requirepass auth | Key patterns defined in API-REFERENCE.md |
| E1.2 | NATS JetStream (messaging) | ✅ | `spec/nats-schema.json` | Running :10302-04, auth token | Decision D3: NATS for messaging, Redis for state only |
| E1.3 | LiteLLM proxy (LLM routing) | ✅ | `spec/litellm-schema.json` | Running :10201, master_key auth | 3 models active: GLM-5, GLM-4.7, phi3-local |
| E1.4 | Docker bridge network (`jart-os-net`) | ✅ | `spec/docker-schema.json` | All services connected | External network, shared |
| E1.5 | Boot manager (`boot.sh`) | ✅ | `spec/operations-schema.json` | start/stop/status/logs/restart | 50 lines, operational |
| E1.6 | TIER-00 METAL host bridge | 🟡 | `spec/metal-schema.json` | Ollama runs on host (:11434) | No formal REST API to container world |
| E1.7 | Secrets management | ⬜ | `spec/secrets-schema.json` | .env files, GitHub Secrets | No formal strategy (1Password `op` CLI planned) |

---

## E2 — Framework & Protocols

> **The reusable code and communication standards.**  
> This is what developers use to build Jart-OS components.

| # | Component | Status | Spec file | Evidence | Notes |
|---|-----------|--------|-----------|----------|-------|
| E2.1 | AgentBase class (614 lines) | ✅ | `spec/agent-schema.json` | agents/core/base.py v3.0 | NATS+Redis+HTTP+metrics+Discord+shutdown |
| E2.2 | Agent lifecycle (boot→run→shutdown) | ✅ | `spec/agent-schema.json` | Implemented in AgentBase | INIT→CONNECT→SUBSCRIBE→RUN→SHUTDOWN |
| E2.3 | NATS subject taxonomy | ✅ | `spec/nats-schema.json` | COMMUNICATION-FLOWS.md 600 lines | `jart-os.<tier>.<domain>.<role>.<action>` |
| E2.4 | Message envelope format | ✅ | `spec/message-schema.json` | COMMUNICATION-FLOWS.md | task_id, from, to, timestamp, payload, metadata |
| E2.5 | Agent HTTP endpoints (/health, /metrics, /state) | ✅ | `spec/agent-schema.json` | AgentHTTPHandler in base.py | Prometheus-format metrics |
| E2.6 | LLM call abstraction | ✅ | `spec/llm-schema.json` | call_llm() in AgentBase | Via LiteLLM proxy, model routing |
| E2.7 | Spec gate (pre-execution validation) | ✅ | `spec/policy-schema.json` | spec-gate.yaml (108 lines, 8 rules) | task_id, objective, success_criteria, no ambiguity |
| E2.8 | Quality gate (post-execution validation) | ✅ | `spec/policy-schema.json` | quality-gate.yaml (74 lines) | completeness≥0.8, accuracy≥0.9, format=1.0 |
| E2.9 | Agent Dockerfile pattern | ✅ | `spec/docker-schema.json` | agents/Dockerfile.agent | Multi-stage, Python 3.12-slim |
| E2.10 | Core modules (10 modules) | ✅ | `spec/core-modules-schema.json` | Published to GitHub from Mac Mini | id_generator(331), cache(118), alerts(130), auth(120), batch(104), encryption(76), rbac(59), autoscaler(136), blockchain(183), base(614) |
| E2.11 | Retry and error handling protocol | 🟡 | `spec/error-schema.json` | Defined in COMMUNICATION-FLOWS.md | max 3 retries, backoff, dead letter, timeout cascade |
| E2.12 | Redis state patterns | 🟡 | `spec/redis-schema.json` | Defined in API-REFERENCE.md | Key naming, TTL, pub/sub channels |
| E2.13 | LLM routing strategy (THINK/DO/VALIDATE) | 🟡 | `spec/llm-schema.json` | Defined in ARCHITECTURE.md | 3-layer routing, cost optimization |
| E2.14 | Agent notification protocol | ⬜ | `spec/notification-schema.json` | Discord webhook in AgentBase | Only Discord, needs abstraction |

---

## E3 — MCP Ecosystem

> **The backpack servers that extend agent capabilities.**

| # | Component | Status | Spec file | Evidence | Notes |
|---|-----------|--------|-----------|----------|-------|
| E3.1 | MCP protocol (JSON-RPC 2.0 over stdio) | ✅ | `spec/mcp-protocol-schema.json` | memory-server, search-server use it | FastMCP (Python) and @modelcontextprotocol/sdk (TS) |
| E3.2 | MCP-core-lib (TypeScript) | ✅ | `spec/core-lib-schema.json` | Published repo: UUID v7, types, createMcpServer | Shared foundation |
| E3.3 | MCP-memory-server (Python) | ✅ | `spec/memory-server-schema.json` | 7 servers, 39 tools, running | L0–L5 hierarchical memory |
| E3.4 | MCP-search-server (TypeScript) | ✅ | `spec/search-server-schema.json` | 11 providers, 7 tools, running | Unified search with caching |
| E3.5 | MCP-blueprint-template (Python) | ✅ | `spec/blueprint-schema.json` | Rewritten with FastMCP + A2A + generate.sh | Canonical scaffolding |
| E3.6 | Entity taxonomy enforcement | ✅ | `spec/taxonomy-schema.json` | 9 entities, TAXONOMY.md v2.0 ratified | No suffixes, type IS classification |
| E3.7 | A2A protocol (Agent-to-Agent) | 🟡 | `spec/a2a-schema.json` | Skeleton in blueprint template | UUID v7, handshake, federation report |
| E3.8 | MCP Apps UI components | 🟡 | `spec/mcp-apps-schema.json` | Directory structure exists in blueprint | @modelcontextprotocol/ext-apps |
| E3.9 | MCP-governance-server | ⬜ | — | Planned, not started | Central audit + compliance |
| E3.10 | MCP-gateway-bridge | ⬜ | — | Planned, not started | HTTP ↔ stdio protocol proxy |
| E3.11 | MCP-documents-server | ⬜ | — | Planned, not started | Document production pipeline |
| E3.12 | MCP-notifications-server | ⬜ | — | Planned, not started | Discord, Telegram, email |

---

## E4 — Security & Governance

> **Protecting the system and ensuring quality of output.**

| # | Component | Status | Spec file | Evidence | Notes |
|---|-----------|--------|-----------|----------|-------|
| E4.1 | Internal port binding (127.0.0.1) | ✅ | `spec/security-schema.json` | All internal services bound | Only MC, Grafana on 0.0.0.0 |
| E4.2 | Redis requirepass authentication | ✅ | `spec/security-schema.json` | 32-char rotated password | |
| E4.3 | NATS auth token | ✅ | `spec/security-schema.json` | 32-char rotated token | |
| E4.4 | LiteLLM master_key | ✅ | `spec/security-schema.json` | 32-char rotated key | |
| E4.5 | .dockerignore for secrets | ✅ | `spec/security-schema.json` | .secrets/ excluded | |
| E4.6 | Council voting (66%/100%) | 🟡 | `spec/governance-schema.json` | Defined in ARCHITECTURE.md, not in code | 66% normal, 100% critical, guardian veto |
| E4.7 | Guardian validation (3-aspect review) | 🟡 | `spec/governance-schema.json` | Quality gate YAML exists, agent basic | regulatory, pedagogical, technical |
| E4.8 | Audit trail format | 🟡 | `spec/audit-schema.json` | Redis keys defined, partially logged | jart-os:audit:<task_id> |
| E4.9 | Escalation procedures | 🟡 | `spec/governance-schema.json` | Defined in COMMUNICATION-FLOWS.md | max retries → council |
| E4.10 | MCP communication security | 🟡 | `spec/mcp-security-schema.json` | Not implemented | Encryption between MCPs |
| E4.11 | TLS for user-facing services | ⬜ | `spec/tls-schema.json` | Not started | Mission Control, Grafana |
| E4.12 | Role-based access control | ⬜ | `spec/rbac-schema.json` | rbac.py exists (59 lines) but not integrated | |
| E4.13 | Secrets rotation strategy | ⬜ | `spec/secrets-schema.json` | Manual rotation done once | Needs automation |
| E4.14 | Compliance validation framework | ⬜ | `spec/compliance-schema.json` | Not started | Automated compliance checks |

---

## E5 — Agents & Observability

> **The running autonomous entities and the systems to watch them.**

| # | Component | Status | Spec file | Evidence | Notes |
|---|-----------|--------|-----------|----------|-------|
| E5.1 | Director agent | ✅ | `spec/agent-director-schema.json` | Container UP, 75 lines, basic | Plans, decomposes, delegates |
| E5.2 | Executor agent | ✅ | `spec/agent-executor-schema.json` | Container UP, basic | Generates, executes sub-tasks |
| E5.3 | Guardian agent | ✅ | `spec/agent-guardian-schema.json` | Container UP, basic | Validates, approves/rejects |
| E5.4 | Council agent | ✅ | `spec/agent-council-schema.json` | Container UP, basic | Consensus voting |
| E5.5 | Prometheus metrics collection | ✅ | `spec/monitoring-schema.json` | Running :10901, scraping agents | Standard metric names defined |
| E5.6 | Tri-unit flow (Director→Executor→Guardian) | 🟡 | `spec/triunit-schema.json` | Defined in docs, basic implementation | Full NATS subscription pending |
| E5.7 | Grafana dashboards | 🟡 | `spec/grafana-schema.json` | Running :10702, default config | Needs custom dashboards |
| E5.8 | Mission Control API (Flask) | 🟡 | `spec/mission-control-schema.json` | 384 lines, real Docker API data | Not published to GitHub |
| E5.9 | Mission Control dashboard | 🟡 | `spec/mission-control-schema.json` | 178 lines HTML, live data | Has personal refs in header |
| E5.10 | Hermes agent framework | 🟡 | `spec/hermes-schema.json` | 69 tools, downloaded | Not integrated with core agents |
| E5.11 | Session manager | 🟡 | `spec/session-schema.json` | session_manager.py exists | Not tested |
| E5.12 | Domain-specific agents (task, etc.) | ⬜ | — | Pattern needs abstraction from personal domains | |
| E5.13 | Real-time agent status grid | ⬜ | `spec/mission-control-schema.json` | Planned | MC API has data, UI not built |
| E5.14 | Agent scaling (1 → 30+) | ⬜ | `spec/scaling-schema.json` | autoscaler.py exists (136 lines) | Not integrated |
| E5.15 | Agent federation between instances | ⬜ | — | Blocked by E7 | |

---

## E6 — Distribution

> **How users discover, install, validate, and update Jart-OS.**

| # | Component | Status | Spec file | Evidence | Notes |
|---|-----------|--------|-----------|----------|-------|
| E6.1 | Jart-OS repo as portal (README) | ✅ | — | Rewritten as ecosystem entry point | MCP servers, backpack model, architecture |
| E6.2 | Complete documentation set | 🟡 | — | 6 new docs ready from Mac Mini | API ref, agent guide, comm flows, pipelines |
| E6.3 | Spec schemas (JSON, machine-readable) | ⬜ | `spec/*.json` | Not started | The schemas referenced throughout this roadmap |
| E6.4 | Validation scripts | ⬜ | — | Not started | Python scripts that read schemas and validate |
| E6.5 | GitHub Actions gatekeeper | ⬜ | — | Not started | The "portero" that blocks non-compliant PRs |
| E6.6 | Branch protection on main | ⬜ | — | Not started | Require PR + status checks |
| E6.7 | CLI tool (`jartos`) | ⬜ | `spec/cli-schema.json` | Not started | init, validate, install, status |
| E6.8 | Release automation | ⬜ | — | Not started | GitHub Releases with artifacts |
| E6.9 | CLI distribution (binary releases) | ⬜ | — | Not started | GitHub Release assets |

---

## E7 — Federation & Integration

> **Connecting Jart-OS instances to each other and to the external world.**

| # | Component | Status | Spec file | Evidence | Notes |
|---|-----------|--------|-----------|----------|-------|
| E7.1 | Agent serialization format | ⬜ | `spec/serialization-schema.json` | Not started | Required for federation |
| E7.2 | Cross-instance communication protocol | ⬜ | `spec/federation-schema.json` | Not started | NATS gateway or HTTP bridge |
| E7.3 | Identity and trust verification | ⬜ | `spec/identity-schema.json` | Not started | auth.py exists (120 lines) |
| E7.4 | OpenClaw gateway | ⬜ | `spec/openclaw-schema.json` | .openclaw/ empty | HTTP gateway for agents |
| E7.5 | Telegram integration | ⬜ | `spec/telegram-schema.json` | Planned in roadmap | Via OpenClaw |
| E7.6 | Calendar/email integration | ⬜ | `spec/external-schema.json` | Planned in roadmap | Via OpenClaw |

---

## Dependency Map

```
E0 Canon ◄────── Everything depends on this
  │
  ├── E1 Infrastructure ◄── Needs E0 conventions
  │     │
  │     ├── E2 Framework ◄── Needs E1 services
  │     │     │
  │     │     ├── E3 MCP Ecosystem ◄── Needs E2 protocols
  │     │     │     │
  │     │     │     ├── E4 Security ◄── Needs E2 + E3
  │     │     │     │     │
  │     │     │     │     ├── E5 Agents ◄── Needs E1+E2+E3+E4
  │     │     │     │     │     │
  │     │     │     │     │     ├── E6 Distribution ◄── Needs ALL above
  │     │     │     │     │     │     │
  │     │     │     │     │     │     └── E7 Federation ◄── Needs E6
```

**Rule:** You cannot mark something as Stable in Escalón N if Escalón N-1 has Draft items it depends on.

---

## Release History

| Release | Date | What became Stable |
|---------|------|--------------------|
| — | — | No formal releases yet |

---

*This roadmap is the single source of truth for Jart-OS project maturity.*  
*Canonical reference: [JART-OS-CANONICAL-SPEC.md](documentation/JART-OS-CANONICAL-SPEC.md)*
