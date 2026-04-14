# Jart-OS — Status, Progress & Action Plan

**Version:** 1.0.0
**Date:** 2026-04-11
**Status:** WORKING DOCUMENT — Updated as project progresses
**Canonical Reference:** [JART-OS-CANONICAL-SPEC.md](JART-OS-CANONICAL-SPEC.md)

---

## Executive Summary

Jart-OS is an AI agent system that runs on a Mac Mini M1 (16GB) for exam preparation of domain subject teacher (Specialty, regulatory framework 2026, exam June 2026).

**Current Status: Base infrastructure operational. Agents, pipelines, and domain not yet implemented.**

---

## What is Jart-OS?

An agentic operating system with 10 layers (TIERS) where each application is self-contained — its own Docker, its own config, its own data. If something fails, it doesn't take down its neighbor.

Agents work in **tri-units** (Director plans → Executor generates → Guardian validates) and communicate via **NATS**. The **LiteLLM** gateway unifies 3 LLM providers with intelligent routing per task.

---

## Timeline — What has been done

```
April 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Day 8   ████████  Project starts. 8 variants in /simba/.
                  Repo evaluation: mission-control,
                  lacp, hermes-agent, opencode-multiagent.

Day 9   ████████████████  TIERS structure created.
                  Root Docker compose (include: pattern).
                  6 services started: Redis, NATS,
                  LiteLLM, MC, Grafana, Prometheus.
                  boot.sh operational.
                  ARCHITECTURE.md v2 written.
                  AgentBase (Python) created — 175 lines.
                  Folders for 4 agents and 4 pipelines
                  created (empty).

Day 10  ██████████████  LiteLLM fixed:
                  - Endpoint changed from open.bigmodel.cn
                    → api.z.ai/api/coding/paas/v4
                  - .env populated with real API keys
                  - docker-compose corrected (--config flag)
                  - Z.AI GLM-5 and GLM-4.7 confirmed OK
                  - phi3-local (Ollama) confirmed OK
                  - OpenRouter and MiMo: keys expired
                  - simba/jarvis permissions issue resolved
                    (sudo for writes in /jarvis/)
                  
Day 11  ████████████████████  CANONICAL SPEC written:
                  - 1,108 lines, 25 sections
                  - Unifies 8+ previous documents
                  - 8 architectural decisions resolved
                  - 5-phase roadmap defined
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Current Status — What works NOW

### 🔴🟡🟢 General Status Overview

```
TIER-00 METAL        ⬜  Empty — Ollama runs on host outside Docker
TIER-01 SECURITY     ⬜  Empty — pf firewall active but not managed
TIER-02 GATEWAY      🟡  LiteLLM OK (3 of 9 models). OpenClaw pending
TIER-03 SERVICES     🟢  Redis + NATS stable 45+ hours
TIER-04 AGENTS       ⬜  Folders created, NO functional code
TIER-05 FRAMEWORKS   ⬜  Hermes-agent downloaded, not integrated
TIER-06 PROCESSES    ⬜  Folders created, NO pipelines
TIER-07 INTERFACES   🟡  Static MC + Grafana OK. Real MC pending
TIER-08 KNOWLEDGE    ⬜  Empty — RAG not installed
TIER-09 CONTROL      🟢  Prometheus collecting metrics
```

### Docker Services (6/6 UP)

| Container | TIER | Port | Uptime | Health |
|-----------|------|------|--------|--------|
| jart-os-redis | 03 SERVICES | 10301 | 45h | ✅ Healthy |
| jart-os-nats | 03 SERVICES | 10302-04 | 45h | ✅ Up |
| jart-os-litellm | 02 GATEWAY | 10201 | 33h | ✅ Up |
| jart-os-mc | 07 INTERFACES | 10701 | 45h | ✅ 200 OK |
| jart-os-grafana | 07 INTERFACES | 10702 | 45h | ✅ 200 OK |
| jart-os-prometheus | 09 CONTROL | 10901 | 45h | ✅ 200 OK |

### LLM Models via LiteLLM

| Model | Provider | Status | Use |
|-------|----------|--------|-----|
| glm-5 | Z.AI | ✅ Working | Think — specs, architecture |
| glm-4.7 | Z.AI | ✅ Working | Do — spec execution |
| phi3-local | Ollama | ✅ Working | Validate — offline checks |
| free-gemma4-31b | OpenRouter | 🔴 Key expired | Do — bulk |
| free-llama33-70b | OpenRouter | 🔴 Key expired | Do — bulk |
| free-nemotron-super | OpenRouter | 🔴 Key expired | Do — bulk |
| free-qwen3-coder | OpenRouter | 🔴 Key expired | Do — bulk |
| mimo-flash | Xiaomi | 🔴 Key expired | Validate |
| mimo-plan | Xiaomi | 🔴 Key expired | Do |

### Existing Code

| File | Lines | Status | What it does |
|------|-------|--------|--------------|
| `agents/core/base.py` | 175 | ✅ Functional | AgentBase class: HTTP, LLM, Redis PubSub, metrics |
| `agents/runtime/main.py` | 285 | 🟡 Skeleton | Agent runner, needs migration to NATS |
| `agents/Dockerfile.agent` | ~15 | ✅ OK | Generic Python image for agents |
| `scripts/boot.sh` | ~50 | ✅ OK | start/stop/status/logs/restart |
| `docs/JART-OS-CANONICAL-SPEC.md` | 1,108 | ✅ OK | Single source of truth |
| `docs/ARCHITECTURE.md` | ~130 | ⚠️ Outdated | Replaced by CANONICAL-SPEC |

### Project Size

```
Total on disk:   610 MB (mostly = Grafana data + Prometheus)
Files:           27,636 (mostly = static MC assets)
Own code:        460 lines (base.py + main.py)
Compose files:   7 operational
```

---

## What is DONE vs. What is PENDING

### ✅ Done

| # | What | Date | Details |
|---|------|------|---------|
| 1 | External repo evaluation | Apr 8 | mission-control, lacp, hermes, opencode-multiagent |
| 2 | 10 TIERS structure | Apr 9 | Folders with self-contained pattern |
| 3 | Root Docker Compose | Apr 9 | `include:` pattern, shared network |
| 4 | Redis operational | Apr 9 | :10301, healthy, bind mount |
| 5 | NATS JetStream operational | Apr 9 | :10302-04, persistence active |
| 6 | LiteLLM proxy operational | Apr 10 | :10201, 9 models (3 working) |
| 7 | Grafana operational | Apr 9 | :10702, admin/jart-os2026 |
| 8 | Prometheus operational | Apr 9 | :10901, scrape targets |
| 9 | Mission Control (static) | Apr 9 | :10701, nginx |
| 10 | boot.sh | Apr 9 | start/stop/status/logs/restart |
| 11 | AgentBase Python | Apr 10 | 175 lines, inheritable by all agents |
| 12 | .env with API keys | Apr 10 | Z.AI key active, rest pending renewal |
| 13 | Canonical spec | Apr 11 | 1,108 lines, 25 sections, 8 decisions closed |
| 14 | Unified conventions | Apr 11 | IDs, ports, NATS subjects, directories |
| 15 | pf firewall | Apr 9 | Rules for Jart-OS ports via Tailscale |

### ⬜ Pending — By Phase

#### PHASE 1: Agent Core (Next)

| # | What | Where | Estimate | Dependencies |
|---|------|-------|----------|-------------|
| 1.1 | Migrate AgentBase to NATS | `agents/core/base.py` | 2h | None |
| 1.2 | Policy gate YAML: spec-gate | `agents/policies/` | 30min | None |
| 1.3 | Policy gate YAML: quality-gate | `agents/policies/` | 30min | None |
| 1.4 | Director Agent (study) | `TIER-04/10401-agent-director/` | 4h | 1.1 |
| 1.5 | Executor Agent (study) | `TIER-04/10402-agent-executor/` | 4h | 1.1 |
| 1.6 | Guardian Agent | `TIER-04/10403-agent-guardian/` | 4h | 1.1, 1.2, 1.3 |
| 1.7 | Council Agent | `TIER-04/10404-agent-council/` | 3h | 1.4, 1.5, 1.6 |
| 1.8 | NATS subject schema deploy | Creation script | 1h | None |
| 1.9 | Renew OpenRouter + MiMo keys | `.env` | 15min | Rubén |

#### PHASE 2: Knowledge Pipeline

| # | What | Where | Estimate | Dependencies |
|---|------|-------|----------|-------------|
| 2.1 | PDF Pipeline (PyMuPDF + Vision) | `pipelines/pdf/` | 8h | Phase 1 |
| 2.2 | CEDE Photos Pipeline (Vision API) | `pipelines/photos/` | 6h | Phase 1 |
| 2.3 | Video Pipeline (ffmpeg + Whisper) | `pipelines/video/` | 6h | Phase 1 |
| 2.4 | RAG Pipeline (LlamaIndex + Qdrant) | `pipelines/rag/` | 8h | 2.1, 2.2, 2.3 |
| 2.5 | Ingest 872 PDFs | — | ~12h process | 2.1 |
| 2.6 | Ingest 1,695 CEDE photos | — | ~8h process | 2.2 |
| 2.7 | Transcribe 18 videos | — | ~18h process | 2.3 |
| 2.8 | Deploy RAGFlow (exploration UI) | `TIER-08/10801-rag-ragflow/` | 3h | 2.4 |

#### PHASE 3: Study Domain

| # | What | Block | Dependencies |
|---|------|-------|-------------|
| 3.1 | Functional content pipeline | Block 1 | Phase 2 |
| 3.2 | Teaching Programming Generator | Block 2 | 3.1, Director + Executor |
| 3.3 | Theoretical exam simulator (34 topics) | Block 3 | 3.1, Director + Examiner |
| 3.4 | Practical exam protocols | Block 4 | 3.1, Tri-unit Domain Subject |
| 3.5 | Oral board simulator | Block 5 | 3.2, Director + Oral Coach |

#### PHASE 4: Real Mission Control + Integrations

| # | What | Where | Dependencies |
|---|------|-------|-------------|
| 4.1 | Deploy builderz-labs/mission-control | `TIER-07/10701-web-mission_control/` | None |
| 4.2 | Configure study workflows | Mission Control | 4.1 |
| 4.3 | Email/calendar integration | Mission Control | 4.1 |
| 4.4 | Telegram Bot via OpenClaw | `TIER-02/10202-proxy-openclaw/` | OpenClaw deploy |
| 4.5 | Deploy OpenClaw Gateway | `TIER-02/10202-proxy-openclaw/` | None |
| 4.6 | Integrate 1Password `op` CLI | `scripts/boot.sh` | None |
| 4.7 | Notifications and personal assistant | OpenClaw + Telegram | 4.4, 4.5 |

#### PHASE 5: Scale

| # | What | Dependencies |
|---|------|-------------|
| 5.1 | Additional domains (/dev, /infra) | Phase 1 complete |
| 5.2 | PostgreSQL for audit trail | When needed |
| 5.3 | Backup strategy | When there is critical data |
| 5.4 | CI/CD if project grows | Optional |
| 5.5 | LM Studio + LM Link in LiteLLM | More local models |

---

## Visual Map — What exists vs. What is missing

```
                    EXISTS ✅              SKELETON 🟡           MISSING ⬜
                    ──────────             ───────────           ──────────

TIER-00 METAL                              Ollama on host        Port monitor
                                           phi4, phi3            llama.cpp config

TIER-01 SECURITY                                                 fail2ban
                                                                  Infisical/1P
                                                                  Reverse proxy

TIER-02 GATEWAY   LiteLLM :10201                               OpenClaw :10202
                  3 models OK

TIER-03 SERVICES  Redis :10301
                  NATS :10302-04

TIER-04 AGENTS                           Folders 10401-04      4 dockerized agents
                  AgentBase.py                                 Policy gates YAML
                                                               NATS integration
                                                               Tri-unit configs

TIER-05 FRAMEWORKS                       hermes-agent/          Hermes integrated
                                         downloaded             OpenClaw runtime

TIER-06 PROCESSES                        Folders pdf/photos/   Pipeline code
                                         video/rag              Whisper, Vision, LlamaIndex

TIER-07 INTERFACES Static MC :10701                            Real Mission Control
                  Grafana :10702                               Workflows, study

TIER-08 KNOWLEDGE                                               RAGFlow :10801
                                                                  AnythingLLM
                                                                  LlamaIndex deploy
                                                                  Qdrant collection

TIER-09 CONTROL   Prometheus :10901                             Configured alerts
                  Grafana dashboards                            Audit logging
```

---

## Decisions Made

(The 8 resolved in the Apr 11, 2026 session. Full detail in [CANONICAL-SPEC §24](JART-OS-CANONICAL-SPEC.md))

| # | Decision | Resolution |
|---|----------|-----------|
| D1 | API keys | Rubén manages them. Pass when needed |
| D2 | Agent runtime | **Own AgentBase**. OpenClaw/Hermes as SOTA layers |
| D3 | Messaging | **NATS** for EVERYTHING. Redis only for state/cache |
| D4 | RAG engine | **LlamaIndex** (engine) + **RAGFlow** (UI) |
| D5 | Secrets | **1Password** with `op` CLI. Already in use |
| D6 | Team communication | **Telegram** (via OpenClaw) |
| D7 | Number of agents | **12 initial** → scale to 30+ |
| D8 | Mission Control | **Real** (builderz-labs). Replace static |

---

## Immediate Next Steps (This Week)

```
PRIORITY 1 ─── Renew OpenRouter + Xiaomi API keys
                → Unlocks 6 additional models
                → 15 min

PRIORITY 2 ─── Migrate AgentBase to NATS
                → base.py uses Redis PubSub, needs NATS
                → Unlocks all agents
                → ~2h

PRIORITY 3 ─── Policy Gate YAMLs
                → spec-gate.yaml + quality-gate.yaml
                → Unlocks Guardian
                → ~1h

PRIORITY 4 ─── First agent: Director Study
                → Plans, decomposes, delegates
                → The brain of the system
                → ~4h

PRIORITY 5 ─── Deploy real Mission Control
                → builderz-labs/mission-control
                → Replace static
                → ~3h
```

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Disk full (55GB free) | Medium | High | Bind mounts, regular cleanup, no Docker volumes |
| Limited RAM (16GB) | Medium | Medium | Agents start on demand, dormant = 0 RAM |
| Keys expire | High | Low | 1Password + renew when they fail |
| Exam June 2026 | Certain | Critical | Prioritize Blocks 2-5 over optimization |
| Over-engineering | Medium | Medium | P3: "Only build what gets used" |

---

## Contact and References

| Concept | Where |
|---------|-------|
| Canonical spec | `/Users/jarvis/Jart-OS/docs/JART-OS-CANONICAL-SPEC.md` |
| This document | `/Users/jarvis/Jart-OS/docs/STATUS-AND-PROGRESS.md` |
| Historical docs | `/Users/simba/Documents/PROJECT-Jart-OS/` |
| Boot manager | `./scripts/boot.sh start` |
| Dashboard | http://localhost:10701 |
| Grafana | http://localhost:10702 (admin / jart-os2026) |
| LiteLLM models | `curl -H "Authorization: Bearer sk-jart-os2026" http://localhost:10201/models` |
| NATS monitor | http://localhost:10304 |

---

*Last updated: 2026-04-11 18:30*
*Next review: When Phase 1 is complete*
