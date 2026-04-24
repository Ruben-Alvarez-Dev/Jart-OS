# Jart-OS — Status, Progress & Action Plan

**Version:** 5.1.1
**Date:** 2026-04-15
**Status:** WORKING DOCUMENT — Updated as project progresses
**Canonical Reference:** [JART-OS-CANONICAL-SPEC.md](JART-OS-CANONICAL-SPEC.md)

---

## Executive Summary

Jart-OS is an AI agent system running on a Mac Mini M1 (16GB) for exam preparation of domain subject teacher (Specialty, regulatory framework 2026, exam June 2026).

**Current Status: Infrastructure SECURED. 4 agents operational with NATS+Redis. Pipelines in skeleton. Study domain running.**

---

## What is Jart-OS?

An agentic operating system with 10 layers (TIERS) where each application is self-contained — its own Docker, its own config, its own data. If something fails, it doesn't take down its neighbor.

Agents work in **tri-units** (Director plans → Executor generates → Guardian validates) and communicate via **NATS**. The **LiteLLM** gateway unifies LLM providers with intelligent routing per task.

---

## Timeline — What has been done

```
April 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Day 8   ████████  Project starts. 8 variants in $STUDY_DATA_DIR/.
                  Repo evaluation: mission-control,
                  lacp, hermes-agent, opencode-multiagent.

Day 9   ████████████████  TIERS structure created.
                  Root Docker compose (include: pattern).
                  6 services started: Redis, NATS,
                  LiteLLM, MC, Grafana, Prometheus.
                  boot.sh operational.
                  ARCHITECTURE.md v2 written.
                  AgentBase (Python) created — 175 lines.
                  Folders for 4 agents and 4 pipelines.

Day 10  ██████████████  LiteLLM fixed:
                  - Z.AI GLM-5 and GLM-4.7 confirmed OK
                  - phi3-local (Ollama) confirmed OK
                  - OpenRouter and MiMo: keys expired
                  - .env populated with real API keys

Day 11  ████████████████████  CANONICAL SPEC written:
                  - 1,108 lines, 25 sections
                  - 8 architectural decisions resolved
                  - 5-phase roadmap defined

Day 12  ██████████████████  Agent framework grown:
                  - AgentBase → 525 lines (HTTP, NATS,
                    Redis, LLM, metrics, audit, envelope)
                  - 4 agent containers dockerized
                  - runtime/main.py with NATS-only runtime
                  - Policy gate YAMLs created
                  - Study domain service (:10500)
                  - 4 pipe services (pdf, photos, video, rag)
                  - LACP framework + pipeline scripts

Day 15  ████████████████████████  SECURITY HARDENED:
                  - TIER-01 audit complete
                  - All internal ports bound to 127.0.0.1
                  - Redis requirepass, NATS auth token,
                    LiteLLM master_key
                  - Service passwords rotated (32-char secure)
                  - Security audit report created
                  - CHANGELOG.md started (v5.1.0)
                  - .dockerignore added

Day 15  ██████████████  NATS BUG FIXED:
                  - nats-py 2.14.0 param rename:
                    max_reconnects → max_reconnect_attempts
                  - NATS auth fix: token via connect() param,
                    not URL credentials
                  - All 4 agents connect NATS+Redis ✓
                  - Version pinned nats-py>=2.14.0,<3.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Current Status — What works NOW

### General Status Overview

```
TIER-00 METAL        ⬜  Ollama runs on host outside Docker
TIER-01 SECURITY     🟢  Ports bound, auth configured, passwords rotated
TIER-02 GATEWAY      🟡  LiteLLM OK (3 of 9 models). OpenClaw pending
TIER-03 SERVICES     🟢  Redis (requirepass) + NATS (auth token) stable
TIER-04 AGENTS       🟢  4 agents UP with NATS+Redis+HTTP
TIER-05 FRAMEWORKS   ⬜  .hermes/ and .openclaw/ empty
TIER-06 PROCESSES    🟡  Pipe-pdf and pipe-rag UP (skeleton). Photos/video restart
TIER-07 INTERFACES   🟡  Static MC + Grafana OK. Study domain UP. Real MC pending
TIER-08 KNOWLEDGE    ⬜  Empty — RAG not installed
TIER-09 CONTROL      🟢  Prometheus collecting metrics
```

### Docker Services (15 containers — 13 UP, 2 restarting)

| Container | TIER | Port | Status | Notes |
|-----------|------|------|--------|-------|
| jart-os-redis | 03 SERVICES | 127.0.0.1:10301 | ✅ Healthy | requirepass auth |
| jart-os-nats | 03 SERVICES | 127.0.0.1:10302-04 | ✅ Up | auth token, JetStream |
| jart-os-litellm | 02 GATEWAY | 127.0.0.1:10201 | ✅ Up | master_key auth |
| jart-os-director-study | 04 AGENTS | 127.0.0.1:10401 | ✅ Up | NATS+Redis connected |
| jart-os-executor-study | 04 AGENTS | 127.0.0.1:10402 | ✅ Up | NATS+Redis connected |
| jart-os-guardian | 04 AGENTS | 127.0.0.1:10403 | ✅ Up | NATS+Redis connected |
| jart-os-council | 04 AGENTS | 127.0.0.1:10404 | ✅ Up | NATS+Redis connected |
| jart-os-pipe-pdf | 06 PROCESSES | 127.0.0.1:10601 | ✅ Up | Skeleton code |
| jart-os-pipe-rag | 06 PROCESSES | 127.0.0.1:10604 | ✅ Up | Skeleton code |
| jart-os-pipe-photos | 06 PROCESSES | — | 🔄 Restart | No code yet |
| jart-os-pipe-video | 06 PROCESSES | — | 🔄 Restart | No code yet |
| jart-os-mc | 07 INTERFACES | 0.0.0.0:10701 | ✅ Up | Static nginx |
| jart-os-grafana | 07 INTERFACES | 0.0.0.0:10702 | ✅ Up | Password rotated |
| jart-os-prometheus | 09 CONTROL | 127.0.0.1:10901 | ✅ Up | Scraping agents |
| jart-os-study-domain | 07 INTERFACES | 0.0.0.0:10500 | ✅ Up | Study domain service |

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

### Agent Framework Code

| File | Lines | Status | What it does |
|------|-------|--------|--------------|
| `agents/core/base.py` | 525 | ✅ Operational | AgentBase: HTTP, NATS, Redis, LLM, metrics, audit, envelope |
| `agents/core/requirements.txt` | 4 | ✅ Pinned | nats-py>=2.14.0,<3.0.0, redis>=5.0.0, requests>=2.31.0 |
| `agents/runtime/main.py` | ~285 | ✅ NATS-only | 4 agent classes: Director, Executor, Guardian, Council |
| `agents/Dockerfile.agent` | 22 | ✅ Multi-stage | Python 3.12-slim, shared image |
| `agents/policies/quality-gate.yaml` | ~20 | ✅ Created | Quality thresholds |
| `agents/policies/spec-gate.yaml` | ~20 | ✅ Created | Spec validation gates |
| `scripts/boot.sh` | ~50 | ✅ OK | start/stop/status/logs/restart |
| `.dockerignore` | 22 | ✅ NEW | Excludes .secrets/ from build context |

### Security Measures (TIER-01)

| Measure | Status | Details |
|---------|--------|---------|
| Internal port binding | ✅ Done | All internal services on 127.0.0.1 |
| User-facing binding | ✅ Done | MC, Grafana, Study on 0.0.0.0 |
| Redis requirepass | ✅ Done | 32-char rotated password |
| NATS auth token | ✅ Done | 32-char rotated token |
| LiteLLM master_key | ✅ Done | 32-char rotated key |
| Service password rotation | ✅ Done | All 5 passwords rotated Apr 15 |
| .dockerignore | ✅ Done | .secrets/ excluded from builds |
| TLS/SSL | ⬜ Pending | For user-facing services |

### Project Size

```
Total on disk:   ~620 MB (mostly Grafana data + Prometheus)
Own code:        ~850 lines (base.py + main.py + policies + scripts)
Compose files:   15 operational (13 docker-compose + root + agents)
Containers:      15 (13 UP, 2 restart)
```

---

## What is DONE vs. What is PENDING

### Done

| # | What | Date | Details |
|---|------|------|---------|
| 1 | External repo evaluation | Apr 8 | mission-control, lacp, hermes, opencode-multiagent |
| 2 | 10 TIERS structure | Apr 9 | Folders with self-contained pattern |
| 3 | Root Docker Compose | Apr 9 | `include:` pattern, shared network |
| 4 | Redis operational | Apr 9 | :10301, requirepass, healthy |
| 5 | NATS JetStream operational | Apr 9 | :10302-04, auth token, persistence |
| 6 | LiteLLM proxy operational | Apr 10 | :10201, master_key, 3 models working |
| 7 | Grafana operational | Apr 9 | :10702, password rotated |
| 8 | Prometheus operational | Apr 9 | :10901, scraping agent metrics |
| 9 | Mission Control (static) | Apr 9 | :10701, nginx |
| 10 | boot.sh | Apr 9 | start/stop/status/logs/restart |
| 11 | AgentBase Python | Apr 10-15 | 525 lines, NATS+Redis+HTTP+LLM+metrics |
| 12 | .env with API keys | Apr 10 | Z.AI active, rest pending renewal |
| 13 | Canonical spec | Apr 11 | 1,108 lines, 25 sections, 8 decisions |
| 14 | Unified conventions | Apr 11 | IDs, ports, NATS subjects, directories |
| 15 | pf firewall | Apr 9 | Rules for Jart-OS ports via Tailscale |
| 16 | 4 Agent containers | Apr 12 | Director, Executor, Guardian, Council — all UP |
| 17 | NATS-only runtime | Apr 12 | main.py migrated from Redis PubSub to NATS |
| 18 | Policy gates | Apr 12 | spec-gate.yaml + quality-gate.yaml |
| 19 | Study domain service | Apr 12 | :10500 operational |
| 20 | Pipe services | Apr 12 | 4 pipe containers (pdf, rag UP; photos, video skeleton) |
| 21 | LACP framework | Apr 12 | Pipeline architecture + scripts |
| 22 | TIER-01 Security hardening | Apr 15 | All ports bound, auth configured, audit report |
| 23 | Password rotation | Apr 15 | All 5 service passwords rotated to 32-char |
| 24 | NATS bug fix | Apr 15 | nats-py param + auth token fix |
| 25 | .dockerignore | Apr 15 | Prevents secrets in build context |
| 26 | CHANGELOG.md | Apr 15 | v5.1.0 started |
| 27 | Security audit report | Apr 15 | SECURITY-AUDIT-2025-04-15.md |

### Pending — By Phase

#### PHASE 1: Agent Core (NEAR COMPLETE — items 1.1-1.3 DONE)

| # | What | Where | Status | Notes |
|---|------|-------|--------|-------|
| 1.1 | Migrate AgentBase to NATS | `agents/core/base.py` | ✅ DONE | NATS-only since Apr 12 |
| 1.2 | Policy gate: spec-gate | `agents/policies/` | ✅ DONE | YAML created |
| 1.3 | Policy gate: quality-gate | `agents/policies/` | ✅ DONE | YAML created |
| 1.4 | Director Agent (study) | `TIER-04/10401-agent-director/` | ✅ RUNNING | NATS+Redis connected |
| 1.5 | Executor Agent (study) | `TIER-04/10402-agent-executor/` | ✅ RUNNING | NATS+Redis connected |
| 1.6 | Guardian Agent | `TIER-04/10403-agent-guardian/` | ✅ RUNNING | NATS+Redis connected |
| 1.7 | Council Agent | `TIER-04/10404-agent-council/` | ✅ RUNNING | NATS+Redis connected |
| 1.8 | NATS subject schema deploy | Creation script | ⬜ Pending | Subjects defined, not deployed |
| 1.9 | Renew OpenRouter + MiMo keys | `.env` | ⬜ Pending | Rubén — 15min |
| 1.10 | Agent functional testing | Integration test | ⬜ Pending | Send real NATS commands |

#### PHASE 2: Knowledge Pipeline

| # | What | Where | Estimate | Dependencies |
|---|------|-------|----------|-------------|
| 2.1 | PDF Pipeline (PyMuPDF + Vision) | `TIER-06/10601-pipe-pdf/` | 8h | Phase 1 |
| 2.2 | CEDE Photos Pipeline (Vision API) | `TIER-06/10602-pipe-photos/` | 6h | Phase 1 |
| 2.3 | Video Pipeline (ffmpeg + Whisper) | `TIER-06/10603-pipe-video/` | 6h | Phase 1 |
| 2.4 | RAG Pipeline (LlamaIndex + Qdrant) | `TIER-06/10604-pipe-rag/` | 8h | 2.1, 2.2, 2.3 |
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

## Immediate Next Steps

```
PRIORITY 1 ─── Renew OpenRouter + Xiaomi API keys
                → Unlocks 6 additional models
                → 15 min — Rubén

PRIORITY 2 ─── Agent functional testing
                → Send real NATS commands to agents
                → Verify Director→Executor→Guardian flow
                → ~2h

PRIORITY 3 ─── PDF Pipeline (Phase 2.1)
                → PyMuPDF + Vision API
                → Unlocks document ingestion
                → ~8h

PRIORITY 4 ─── Deploy real Mission Control
                → builderz-labs/mission-control
                → Replace static MC
                → ~3h

PRIORITY 5 ─── OpenClaw Gateway
                → Telegram bot integration
                → Notifications, personal assistant
                → ~4h
```

---

## Known Gotchas

| Issue | Details | Workaround |
|-------|---------|------------|
| Docker BuildKit xattr on .secrets | BuildKit fails with xattr errors on restricted macOS dirs | Build from temp context: rsync agents/ to /tmp, build from there |
| Redis dump.rdb + requirepass | Old dump without password + new requirepass = crash | Delete dump.rdb + appendonlydir/ before restart |
| Grafana/Prometheus data dirs | macOS Docker Desktop needs chmod 777 | `sudo chmod -R 777 data/` on first setup |
| NATS stale jetstream dir | FTL `mkdir /data/jetstream: file exists` | `sudo rm -rf data/jetstream` |
| Docker disk full (92%) | Redis can't persist | `docker builder prune -a` |
| .git/index owned by root | From sudo git operations | `sudo chown $JART_OS_USER:staff .git/index` |
| git rebase --continue opens Vim | Non-interactive context | `GIT_EDITOR=true git rebase --continue` |

---

## Decisions Made

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

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Disk full (~55GB free) | Medium | High | Bind mounts, regular cleanup, no Docker volumes |
| Limited RAM (16GB) | Medium | Medium | Agents start on demand, dormant = 0 RAM |
| Keys expire | High | Low | 1Password + renew when they fail |
| Exam June 2026 | Certain | Critical | Prioritize Blocks 2-5 over optimization |
| Over-engineering | Medium | Medium | P3: "Only build what gets used" |
| nats-py API changes | Medium | High | Pin versions in requirements.txt |

---

## Contact and References

| Concept | Where |
|---------|-------|
| Canonical spec | `$JART_OS_HOME/documentation/JART-OS-CANONICAL-SPEC.md` |
| This document | `$JART_OS_HOME/documentation/STATUS-AND-PROGRESS.md` |
| Security audit | `$JART_OS_HOME/documentation/SECURITY-AUDIT-2025-04-15.md` |
| Changelog | `$JART_OS_HOME/CHANGELOG.md` |
| Historical docs | `$STUDY_DATA_DIR/PROJECT-Jart-OS/` |
| Boot manager | `./scripts/boot.sh start` |
| Dashboard | http://localhost:10701 |
| Grafana | http://localhost:10702 |
| Study domain | http://localhost:10500 |
| NATS monitor | http://localhost:10304 |
| Prometheus | http://localhost:10901 |

---

*Last updated: 2026-04-15*
*Next review: When Phase 1 functional testing is complete*
