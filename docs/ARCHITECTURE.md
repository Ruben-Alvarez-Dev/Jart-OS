# Jart-OS — Consolidated Architecture
## Single Source of Truth

**Version:** 2.0.0
**Date:** 2026-04-09
**Status:** CANONICAL

---

## 0. Principles

```
P1 — Make it work first, make it perfect later.
P2 — This document is the single source of truth.
P3 — Only build what gets used.
P4 — Nothing in production without tests.
P5 — Document decisions with why, not just what.
P6 — Every app is autocontained. No shared services, no shared volumes.
     If it breaks, the neighbour doesn't burn. 
```

---

## 1. Hardware

| Resource | Available | Impact |
|----------|-----------|--------|
| Mac Mini M1 | 16GB RAM, macOS | Everything runs here |
| Disk | ~55GB free of 228GB | Bind mounts, no external disk |
| Docker | v29.3.1, Compose v5.1.1 | Orchestration |

---

## 2. Goal

> Ruben Alvarez Diaz passes the civil service exam for hospitality professor.
> Specialty 598010, BOJA 2026, exam June 2026.

---

## 3. The 10 Tiers

```
 ┌───────────────────────────────────────────────────────────────────────┐
 │   TIER-00 — METAL            Host-level. No Docker.                    │
 │   TIER-01 — SECURITY         fail2ban, reverse proxy, antivirus       │
 │   TIER-02 — GATEWAY          Proxies, bridges, MCP servers, in-out    │
 │   TIER-03 — SERVICES         Redis, NATS. Comms inside Docker          │
 │   TIER-04 — AGENTS           Professors, tri-units                     │
 │   TIER-05 — FRAMEWORKS       Hermes, OpenClaw runtime                  │
 │   TIER-06 — PROCESSES        Pipelines, workflows, automations         │
 │   TIER-07 — INTERFACES       Self-hosted apps with UI                  │
 │   TIER-08 — KNOWLEDGE        RAG, LlamaIndex, Obsidian, Affine        │
 │   TIER-09 — CONTROL          Metrics, alerts, Prometheus               │
 │                                                                   │
 │   00 ─ ─ host ─ ─ → ─ ─ → ─ ─ Docker ─ ─ → ─ ─ wrap ─ ─ 09  │
 └───────────────────────────────────────────────────────────────────────┘
```

### Boundary Rules
- TIER-00 is OUTSIDE Docker. Host puro. Port monitor, llama.cpp.
- Docker boundary is between TIER-00 and TIER-01.
- TIER-01 defends it. TIER-09 wraps it.
- Each app = one folder. Its own compose, image, config, data.
- No shared services. No shared volumes. Isolation absolute.

---

## 4. Directory Pattern

```
TIERS/
└── TIER-XX-NAME/
    └── PPORT-category-appname/
        ├── docker-compose.yml    # Self-contained
        ├── Dockerfile           # If custom image
        ├── config/              # App configs
        ├── engine/              # Subservices outside container (models, etc.)
        ├── db/                  # Subservice data (bind mount INSIDE app)
        ├── data/                # App own data (bind mount)
        └── logs/                # App logs
```

Port format: `1XXYY` where XX = tier number, YY = sequence.

---

## 5. Professors (TIER-04)

### Active

| Professor | Code | Domains | Why |
|-----------|------|---------|-----|
| CKO | `CKO` | `/oposiciones`, `/academico` | Exams = knowledge |
| CEngO | `CEngO` | `/dev`, `/infra` | Someone maintains Jart-OS |
| COO | `COO` | `/hosteleria` | Practical exam |

### Dormant (YAML only, zero RAM)

| Professor | Code | Domains | Wake when |
|-----------|------|---------|-----------|
| CCO | `CCO` | `/idiomas` | Active language study |
| CHO | `CHO` | `/fitness` | Health integration |
| CSRO | `CSRO` | `/crypto` | Finance management |

---

## 6. Domain /oposiciones

### 5 Functional Blocks

```
BLOCK 1: CONTENT PIPELINE    872 PDFs + 1695 photos + 18 videos -> Qdrant
BLOCK 2: SYLLABUS DESIGN    Guidelines + regulations -> Programme + Units
BLOCK 3: THEORETICAL EXAM    34 topics -> explanations, flashcards, mocks
BLOCK 4: PRACTICAL EXAM     Plating, tables, events -> protocols, checklists
BLOCK 5: ORAL DEFENSE        Panel simulator, timer, feedback
```

### Tri-Units

| Unit | Director | Executor | Archivist |
|------|----------|----------|-----------|
| Writer | Structure | Generate | Validate |
| Researcher | Search | Find | Verify |
| Examiner | Design | Questions | Grade |
| Oral Coach | Plan | Simulate | Evaluate |

### Council (3/3 to pass)

| Reviewer | Checks | Rejects when |
|----------|--------|-------------|
| Legal | LOE/FP/BOJA | Missing regulation |
| Pedagogical | RA/CE | Misaligned curriculum |
| Technical | Hospitality | Factually wrong |

---

## 7. Memory

```
GLOBAL     -> Qdrant "global"  (ADRs, lessons)
DOMAIN     -> Qdrant "opo"     (domain knowledge)
UNIT       -> SQLite           (tri-unit sessions)
AGENT      -> LanceDB/Hermes   (individual context)
```

Query order: Agent -> Domain -> Global -> RAG -> Native LLM

---

## 8. ID Format

```
LLL-DDD-TTT-SSS-name
```
LLL = Level (SIS/JEF/ESP/SUB), DDD = Domain, TTT = Type, SSS = Seq, name = descriptive

---

## 9. Port Map

| Port | TIER | App | Status |
|------|------|-----|--------|
| 10201 | 02 GATEWAY | proxy-litellm | Running |
| 10301 | 03 SERVICES | msg-redis | Running |
| 10302-04 | 03 SERVICES | msg-nats | Running |
| 10701 | 07 INTERFACES | web-mission_control | Running |
| 10702 | 07 INTERFACES | web-grafana | Running |
| 10901 | 09 CONTROL | metrics-prometheus | Running |

---

## 10. Stack

| Component | Technology |
|-----------|------------|
| Orchestration | Docker Compose |
| Cache/PubSub | Redis 7 Alpine |
| Events | NATS JetStream |
| Vectors | Qdrant (inside RAG apps) |
| Gateway | OpenClaw |
| Runtime | Hermes Agent v0.7 |
| LLM primary | z.ai GLM-5 (via LiteLLM) |
| LLM validation | GLM-4.7 temp 0.1 |
| LLM local | Ollama phi-3-mini |
| Observability | Prometheus |
| Dashboard | Grafana + Mission Control |

---

## 11. Roadmap

### PHASE 1 — Infrastructure (Week 1)

| # | Task | Status |
|---|------|--------|
| 1.1 | TIER structure + autocontained apps | Done |
| 1.2 | LiteLLM proxy | Running |
| 1.3 | .env API keys | Pending |
| 1.4 | Tailscale firewall | Done |
| 1.5 | boot.sh scripts | Pending |

### PHASE 2 — Agents (Week 2)

| 2.1 | Agent base class | Pending |
| 2.2 | Tri-unit pattern | Pending |
| 2.3 | Council 3/3 | Pending |
| 2.4 | LLM integration | Pending |

### PHASE 3 — Content Pipeline (Week 3-4)

| 3.1 | PDF pipeline (872) | Pending |
| 3.2 | Photos OCR (1695) | Pending |
| 3.3 | Video transcription (18) | Pending |
| 3.4 | RAG pipeline | Pending |

### PHASE 4 — Exam Prep (Week 5-8)

| 4.1 | Writer + Council | Pending |
| 4.2 | Researcher | Pending |
| 4.3 | Examiner | Pending |
| 4.4 | Oral Coach | Pending |
| 4.5 | All 34 topics in Qdrant | Pending |

### PHASE 5 — Interface (Week 9-10)
### PHASE 6 — Expansion (Post-exam)

---

## 12. Agents

| Type | Count |
|------|-------|
| Active professors | 3 |
| Tri-units x 3 | 12 |
| Council | 3 |
| **Total active** | **18** |
