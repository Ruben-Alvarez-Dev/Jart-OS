# Jart-OS v5.0 — Agentic OS

> **Build the machine that builds the machine.**

## Architecture — 10-Tier System

> **Canonical reference:** [JART-OS-CANONICAL-SPEC.md](JART-OS-CANONICAL-SPEC.md) overrides all other docs.

| Tier | Layer | Port Range | Status |
|------|-------|-----------|--------|
| TIER-00 | METAL | — | 🟡 Bare metal host (Ollama) |
| TIER-01 | SECURITY | 10101-10199 | 🟡 Planned (fail2ban, reverse proxy) |
| TIER-02 | GATEWAY | 10201-10299 | ✅ LiteLLM proxy running |
| TIER-03 | SERVICES | 10301-10399 | ✅ Redis + NATS JetStream |
| TIER-04 | AGENTS | 10401-10499 | 🟡 AgentBase created, agents pending |
| TIER-05 | FRAMEWORKS | 10501-10599 | 🟡 Hermes downloaded, not integrated |
| TIER-06 | PROCESSES | 10601-10699 | 🟡 Pipelines planned |
| TIER-07 | INTERFACES | 10701-10799 | ✅ Mission Control + Grafana |
| TIER-08 | KNOWLEDGE | 10801-10899 | 🟡 RAG planned (Qdrant, LlamaIndex) |
| TIER-09 | CONTROL | 10901-10999 | ✅ Prometheus collecting metrics |

## Running Services

| Container | Port | Purpose |
|-----------|------|---------|
| jart-os-litellm | 10201 | LLM proxy (GLM-5, GLM-4.7, phi3-local) |
| jart-os-redis | 10301 | Cache + state |
| jart-os-nats | 10302-10304 | Messaging (JetStream) |
| jart-os-mc | 10701 | Mission Control dashboard |
| jart-os-grafana | 10702 | Metrics visualization |
| jart-os-prometheus | 10901 | Metrics collection |

## Directory Structure

```
Jart-OS/
├── docker-compose.yml          # Infrastructure orchestration
├── agents/
│   ├── core/base.py            # AgentBase (175 lines)
│   └── runtime/main.py         # Runtime skeleton (285 lines)
├── TIERS/                      # 10-tier self-contained services
│   └── TIER-XX-NAME/
│       └── PPORT-category-app/
│           ├── docker-compose.yml
│           ├── config/
│           ├── data/
│           └── logs/
├── control/                    # Mission control configs
├── documentation/              # Technical documentation
├── docs/                       # Project documentation (legacy)
├── pipelines/                  # Data pipelines
├── scripts/
│   └── boot.sh                 # start|stop|status|logs|restart
└── .env                        # Secrets (not tracked)
```

## Quick Start

```bash
cd $JART_OS_HOME/Jart-OS
./scripts/boot.sh start
```

## Governance (Council)

Every agent output validated through 3-aspect review:
- **REGULATORY** — Valid regulatory framework references
- **PEDAGOGICAL** — Complete and well-structured content
- **TECHNICAL** — No errors in model response
- 3/3 PASS = ✅ Approved | Any FAIL = ❌ Rejected

## Scrum System

- **Sprint cadence**: Weekly
- **Product Owner**: AI agent (backlog, user stories, prioritization)
- **Scrum Master**: AI agent (ceremonies, DoD, sprint reports)
- **Board**: GitHub Projects v2 (7-column Kanban)
- **DoD**: 15 criteria checklist

## Rules

1. **ZERO MANUAL WORK** — Agents do everything
2. **DAILY CHECK** at 22:00
3. **FAILSAFE**: 3 failures → restart
4. **ABSOLUTE FOCUS**: Active domain = P0
5. **GUARDIAN KILLS DRIFT**

## License

Private repository — All rights reserved.
