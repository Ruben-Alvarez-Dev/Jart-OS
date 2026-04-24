# Jart-OS v5 — Agentic Operating System

> **Build the machine that builds the machine.**

Jart-OS is a production-grade agentic operating system that orchestrates autonomous AI agents through a 10-tier architecture. Each agent carries a **backpack** of MCP servers that extend its capabilities — memory, search, governance, documents, notifications — all validated and monitored by a central governance system.

---

## The MCP Ecosystem

Jart-OS is powered by a modular ecosystem of MCP (Model Context Protocol) servers. Every server follows a strict naming convention and taxonomy:

```
MCP-{domain}[-{subdomain}]-{suffix}
```

### Active Repositories

| Repository | Category | Stack | Description |
|---|---|---|---|
| [**MCP-memory-server**](https://github.com/Ruben-Alvarez-Dev/MCP-memory-server) | `-server` | Python | 7 servers, 39 tools. Hierarchical memory L0–L5 with AutoMem, VK-Cache, Engram, and Obsidian vault integration |
| [**MCP-search-server**](https://github.com/Ruben-Alvarez-Dev/MCP-search-server) | `-server` | TypeScript | 11 providers, 7 tools. Unified search with Gemini grounding, dedup, caching, and health tracking |
| [**MCP-core-lib**](https://github.com/Ruben-Alvarez-Dev/MCP-core-lib) | `-lib` | TypeScript | UUID v7, enriched types, `createMcpServer()` factory, tracing — shared foundation for all MCP servers |
| [**MCP-blueprint-template**](https://github.com/Ruben-Alvarez-Dev/MCP-blueprint-template) | `-template` | Python | Canonical scaffolding for new MCP servers with MCP + A2A + MCP Apps boilerplate |

### Planned Repositories

| Repository | Category | Stack | Description |
|---|---|---|---|
| `MCP-gateway-bridge` | `-bridge` | TypeScript | HTTP ↔ stdio protocol proxy for remote MCP access |
| `MCP-governance-server` | `-server` | Python | Central audit, compliance validation, risk control for all backpacks |
| `MCP-infrastructure-server` | `-server` | TypeScript | SSH, filesystem, Docker operations — agent control over infrastructure |
| `MCP-documents-server` | `-server` | Python | Document production pipeline (PDF, Markdown, presentations) |
| `MCP-notifications-server` | `-server` | TypeScript | Push alerts via Discord, Telegram, email |

### Taxonomy Rules

- **4 categories only**: `-server` (runtime + backpack), `-lib` (shared code), `-template` (scaffolding), `-bridge` (protocol translator)
- **`jart-os` GitHub topic** = ecosystem membership. No topic = personal project, no obligations.
- **Dual-account mirror**: `Ruben-Alvarez-Dev` (source of truth) → `Jart-OS` (auto-mirror via GitHub Actions)

> Full specification: [MCP Repository Taxonomy](documentation/MCP-REPOSITORY-TAXONOMY.md)

---

## The Backpack Model

Every AI agent in Jart-OS carries a **backpack** — a curated set of MCP servers that define what it can do:

```
┌─────────────────────────────────────────────────────┐
│                     AGENT                            │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Memory   │  │ Search   │  │ Governance       │  │
│  │ Server   │  │ Server   │  │ Server           │  │
│  │          │  │          │  │ (audit + policy) │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│                                                      │
│  Every server:                                       │
│  ✅ Reports identity to governance                   │
│  ✅ Follows Jart-OS Canon                            │
│  ✅ Has .jart-os-manifest                               │
│  ✅ Health-checked by control tier                   │
└─────────────────────────────────────────────────────┘
```

A Director agent gets memory + search for planning. An Executor gets infrastructure + documents for execution. A Guardian gets governance for validation. The backpack defines the agent's capabilities.

---

## Architecture — 10-Tier System

```
 ┌────────────────────────────────────────────────────────────────────┐
 │                                                                    │
 │   TIER-00 — METAL          Host-level. No Docker.                  │
 │                              Ollama, LM Studio, drivers.           │
 │                                                                    │
 │   TIER-01 — SECURITY       fail2ban, pf firewall, Tailscale VPN.  │
 │                                                                    │
 │   TIER-02 — GATEWAY        LiteLLM proxy (:10201), MCP bridges.   │
 │                                                                    │
 │   TIER-03 — SERVICES       Redis (:10301), NATS JetStream (:10302)│
 │                                                                    │
 │   TIER-04 — AGENTS         Tri-units (Director → Executor →        │
 │                              Guardian), Council, domain agents.    │
 │                                                                    │
 │   TIER-05 — FRAMEWORKS     Hermes runtime, OpenClaw gateway.       │
 │                                                                    │
 │   TIER-06 — PROCESSES      Pipelines: OCR, RAG, video, documents. │
 │                                                                    │
 │   TIER-07 — INTERFACES     Mission Control, Grafana dashboards.   │
 │                                                                    │
 │   TIER-08 — KNOWLEDGE      Qdrant vectors, Obsidian vault, RAG.   │
 │                                                                    │
 │   TIER-09 — CONTROL        Prometheus metrics, audit logs.        │
 │                                                                    │
 │   00 ─ host ──→ ── Docker boundary ──→ ── wrap ── 09              │
 └────────────────────────────────────────────────────────────────────┘
```

### Agent Tri-Unit Pattern

Every specialist domain operates through a tri-unit:

```
  DIRECTOR ────→ EXECUTOR ────→ GUARDIAN
  (GLM-5)        (GLM-4.7)      (MiMo/phi3)
  Plans          Executes       Validates
  Decomposes     Generates      Approves/Rejects
  Supervises     Reports
```

1. Task arrives via NATS → Director plans and decomposes
2. Executor generates output per spec
3. Guardian validates (completeness ≥ 0.8, accuracy ≥ 0.9)
4. 3 PASS = ✅ Approved | Any FAIL = ❌ Retry (max 3)

### LLM Routing

| Layer | Purpose | Models | Cost |
|---|---|---|---|
| **THINK** | Architecture, specs, review | GLM-5 | ~$160/month |
| **DO** | Execute specs, TDD, bulk generation | OpenRouter free tier, phi3 fallback | $0 |
| **VALIDATE** | Pass/fail tests, quick checks | MiMo Flash, phi3-local | ~$0 |

---

## Infrastructure — Running Services

| Container | Port | Tier | Purpose |
|---|---|---|---|
| jart-os-litellm | 10201 | 02 | LLM proxy (GLM-5, GLM-4.7, phi3-local) |
| jart-os-redis | 10301 | 03 | Cache, state, locks, rate-limiting |
| jart-os-nats | 10302-304 | 03 | JetStream messaging (agent backbone) |
| jart-os-mc | 10701 | 07 | Mission Control dashboard |
| jart-os-grafana | 10702 | 07 | Metrics visualization |
| jart-os-prometheus | 10901 | 09 | Metrics collection |

---

## Quick Start

### Prerequisites

- macOS (Apple Silicon) or Linux
- Docker Compose v5.1.1+
- 16GB RAM minimum
- Python 3.11+ and/or Node.js 20+

### Start the OS

```bash
cd $JART_OS_HOME
./scripts/boot.sh start    # docker compose up -d
./scripts/boot.sh status   # show all services + health
./scripts/boot.sh logs     # follow logs
```

### Add an MCP Server to Your Backpack

```bash
# Clone the memory server
git clone https://github.com/Ruben-Alvarez-Dev/MCP-memory-server.git
cd MCP-memory-server
./scripts/install.sh

# Or create a new one from the blueprint
git clone https://github.com/Ruben-Alvarez-Dev/MCP-blueprint-template.git my-new-server
cd my-new-server
./scripts/generate.sh
```

### Create a New MCP Server

Use the blueprint template to scaffold a new server following Jart-OS conventions:

```bash
# From MCP-blueprint-template
./scripts/generate.sh --name MCP-documents-server --stack python --category server
```

Every generated server includes: MCP protocol, A2A handshake, `.jart-os-manifest`, `install.sh`, directory structure, and tests.

---

## Directory Structure

```
Jart-OS/
├── docker-compose.yml          # Root compose (include: pattern)
├── .env                        # Secrets (not tracked)
├── agents/
│   ├── core/base.py            # AgentBase (all agents inherit)
│   └── runtime/main.py         # Runtime skeleton
├── TIERS/                      # 10-tier self-contained services
│   └── TIER-XX-NAME/
│       └── 1XXYY-category-app/
│           ├── docker-compose.yml
│           ├── config/
│           ├── data/
│           └── logs/
├── documentation/              # Technical documentation
│   ├── JART-OS-CANONICAL-SPEC.md    # Single source of truth
│   ├── MCP-REPOSITORY-TAXONOMY.md  # MCP naming + categories
│   └── ...
├── control/                    # Mission control configs
├── pipelines/                  # Data pipelines (RAG, OCR, etc.)
├── scripts/
│   └── boot.sh                 # start|stop|status|logs|restart
└── tests/                      # Integration tests
```

---

## Documentation

| Document | Description |
|---|---|
| [Canonical Spec](documentation/JART-OS-CANONICAL-SPEC.md) | **Source of truth**. Overrides all prior docs. |
| [MCP Taxonomy](documentation/MCP-REPOSITORY-TAXONOMY.md) | Naming convention, 4 categories, `.jart-os-manifest` schema |
| [Architecture](documentation/ARCHITECTURE.md) | System architecture overview |
| [API Reference](documentation/API-REFERENCE.md) | Agent and service APIs |
| [Contributing](documentation/CONTRIBUTING.md) | How to contribute to Jart-OS |
| [Deployment](documentation/DEPLOYMENT.md) | Deployment procedures |
| [Testing](documentation/TESTING.md) | Testing strategy and guidelines |
| [Development](documentation/DEVELOPMENT.md) | Development setup and workflows |

---

## Implementation Roadmap

### Phase 0 — Infrastructure ✅
- [x] 10-tier autocontained architecture
- [x] LiteLLM proxy with GLM-5/GLM-4.7
- [x] Redis + NATS running stable
- [x] Prometheus + Grafana monitoring
- [x] AgentBase class
- [x] Canonical Spec document
- [x] MCP ecosystem taxonomy and naming

### Phase 1 — Agent Core (Current)
- [ ] Migrate AgentBase from Redis PubSub to NATS
- [ ] Director, Executor, Guardian, Council agents
- [ ] Policy gates (spec-gate, quality-gate)
- [ ] NATS subject schema deployment
- [ ] Governance MCP server

### Phase 2 — Knowledge Pipeline
- [ ] LlamaIndex pipeline (872 PDFs)
- [ ] Vision API pipeline (1,695 photos)
- [ ] Whisper pipeline (18 videos)
- [ ] Qdrant vector collections

### Phase 3 — Study Domain
- [ ] Content pipeline, syllabus generator
- [ ] Exam simulator (theory + practical + oral)

### Phase 4 — Mission Control
- [ ] Real dashboard deployment
- [ ] Telegram integration
- [ ] Personal assistant workflows

---

## Governance

Every agent output is validated through 3-aspect review:

| Aspect | Validates |
|---|---|
| **REGULATORY** | Valid regulatory framework references |
| **PEDAGOGICAL** | Complete and well-structured content |
| **TECHNICAL** | No errors in model response |

3/3 PASS = ✅ Approved | Any FAIL = ❌ Rejected + Retry

---

## Hardware

| Item | Value |
|---|---|
| Server | Mac Mini M1, 16GB RAM |
| Second machine | MacBook Pro M1 Max, 32GB |
| VPN | Tailscale mesh between Macs |
| LLM Gateway | LiteLLM proxy (:10201) |
| Local models | Ollama (phi4, phi3:mini, qwen2.5) |

---

## License

MIT License — See [LICENSE](LICENSE).

---

*Jart-OS is built by [Rubén Álvarez Dianez](https://github.com/Ruben-Alvarez-Dev).*
*Canonical specification: [JART-OS-CANONICAL-SPEC.md](documentation/JART-OS-CANONICAL-SPEC.md) — overrides all other documents.*
