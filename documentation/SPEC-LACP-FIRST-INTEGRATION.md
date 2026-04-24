# SPEC: LACP-First Integration in Jart-OS

**Status:** DRAFT  
**Date:** 2026-04-15  
**Decision:** Option B — LACP as main control plane  
**Tools:** LACP v0.9.0 + Builderz Mission Control (prebuilt)

---

## Summary (for tired humans)

Today: 4 agents (Director, Executor, Guardian, Council) communicate via NATS and each does their own thing.

After: LACP is the boss that controls how and when agents work. Mission Control is the nice screen where you see everything. NATS continues to exist as internal messaging.

---

## Decisions Made

| ID | Decision | Detail |
|----|----------|---------|
| D9 | LACP is in charge | LACP controls agent execution with quality gates |
| D10 | MC prebuilt | `ghcr.io/builderz-labs/mission-control:latest`, no fork |
| D11 | Nuke old MC | Delete all of `TIER-07/10701-web-mission_control/` |
| D12 | LACP in TIER-09 | Container in `TIER-09-CONTROL/10902-control-lacp/` |
| D13 | Agents as LACP tasks | Each agent executes via LACP harness |

---

## Role Mapping

The 4 Jart-OS agents map to LACP workflow stages:

```
Director  → planner     (plans, decomposes)
Executor  → developer   (executes, generates output)
Guardian  → verifier    (validates, verifies quality)
Council   → reviewer    (tri-unit review, consensus)
```

---

## Current State (BEFORE)

```
agents/core/base.py      — 560 lines (NATS + Redis + LLM + HTTP)
agents/runtime/main.py   — 411 lines (4 agents)
docker-compose.yml       — include pattern, 13 services
TIER-07/10701-mc/        — MC custom (TO BE DELETED)
TIER-09/                 — only Prometheus
```

---

## Final State (AFTER)

```
agents/core/base.py           — MODIFIED (adds LACP harness)
agents/core/lacp_client.py    — NEW (Python ↔ LACP CLI adapter)
agents/runtime/main.py        — MODIFIED (agents use LACP)
docker-compose.yml            — MODIFIED (adds MC + LACP)
TIER-07/10701-mc/             — DELETED
TIER-07/10701-web-mc-builderz/— NEW (prebuilt MC)
TIER-09/10902-control-lacp/   — NEW (LACP container)
```

---

## Implementation Phases

### Phase 0: Cleanup and setup (without breaking anything)

**What:** Prepare the ground without touching existing agents.

1. **Backup** current repo (git branch `feature/lacp-first`)
2. **Nuke old MC**: delete `TIER-07/10701-web-mission_control/`
3. **Create** `TIER-07/10701-web-mc-builderz/docker-compose.yml` with prebuilt MC
4. **Create** `TIER-09/10902-control-lacp/docker-compose.yml` with LACP container
5. **Update** root `docker-compose.yml` with new includes
6. **Verify** MC and LACP start with `docker compose up`

**Acceptance criteria:**
- `docker compose up` starts all services
- MC responds at `http://localhost:PORT` with empty dashboard
- LACP responds to `lacp status` inside the container

**Files that change:** 0 existing files, ~4 new files, docker-compose.yml

---

### Phase 1: LACP Adapter

**What:** Create the bridge between Python (agents) and LACP (CLI).

LACP is a CLI (terminal commands). Our agents are Python. We need an adapter.

1. **Create** `agents/core/lacp_client.py`
   - `harness_validate(task_manifest)` → validate task before executing
   - `harness_run(task_manifest, agent_fn)` → execute with quality gates
   - `workflow_advance(stage)` → advance workflow stage
   - `quality_check(output)` → pass through stop_quality_gate
2. **Configure** LACP with Jart-OS policies
   - `sandbox-policy.json` adapted to our tiers
   - `risk-policy-contract.json` with our criteria

**Acceptance criteria:**
- A simple test: `lacp_client.harness_validate({"task": "test"})` responds OK or FAIL
- Quality gates respond without error

**New files:** `agents/core/lacp_client.py`, `TIER-09/10902-control-lacp/config/`

---

### Phase 2: Agents use LACP

**What:** Modify the 4 agents to go through LACP.

1. **Modify** `agents/core/base.py`
   - Add `self.lacp` (LACP client) to `__init__`
   - Add `boot_lacp()` to boot sequence
   - Modify `call_llm()` to go through LACP quality gates
2. **Modify** `agents/runtime/main.py`
   - Each agent: receive command → create task manifest → `harness_run()` → evidence manifest
   - Director: `harness_validate()` before delegating
   - Executor: `harness_run()` wrap around all execution
   - Guardian: use LACP `stop_quality_gate` instead of custom LLM to validate
   - Council: LACP quality check as input for the 3 votes

**Acceptance criteria:**
- `docker compose up` starts 4 agents
- Each agent registers in LACP
- A command sent via NATS goes through LACP harness
- Quality gate approves/rejects based on result

**Files that change:** `base.py`, `main.py`

---

### Phase 3: Mission Control sees everything

**What:** Connect agents and LACP to MC for visualization.

1. **Agents register** in MC via REST on startup
   - `POST /api/agents/register` with name, role, capabilities
2. **LACP reports** execution results to MC
   - Task outcomes (pass/fail/score) via REST
3. **MC shows**:
   - Active agents and their status
   - Kanban with tasks in progress
   - LACP quality scores
   - Cost tracking (LLM tokens used)

**Acceptance criteria:**
- MC dashboard shows the 4 registered agents
- A completed task appears in MC kanban
- LACP quality scores are visible in MC

**Files that change:** `base.py` (adds MC registration), `lacp_client.py` (adds MC reporting)

---

### Phase 4: Memory and quality (optional / future)

**What:** Activate advanced LACP features.

1. SMS Memory — agents "remember" past experiences
2. Obsidian vault — persistent knowledge
3. Sandbox routing — critical tasks go to remote sandbox
4. Incident response — SEV1/2/3 handling

**Status:** Defined after Phase 3 is complete and working.

---

## Rollback plan

If something breaks:
1. **Git branch** `feature/lacp-first` — all changes are there
2. If LACP doesn't work: `git revert` to previous branch, agents go back to NATS-only
3. If MC doesn't work: agents keep working without MC (it's only visualization)
4. Old MC: backup in git history, `git checkout main -- TIER-07/10701-web-mission_control/`

---

## Risks (honest)

| Risk | Probability | Impact | Mitigation |
|--------|-------------|---------|------------|
| LACP alpha breaks API | HIGH | HIGH | Separate branch, easy rollback |
| LACP CLI doesn't integrate well with Python | MEDIUM | HIGH | Adapter with fallback to direct NATS |
| Quality gates reject everything | MEDIUM | MEDIUM | Permissive config thresholds initially |
| LACP container is heavy | LOW | LOW | LACP is scripts, not heavy |
| Prebuilt MC doesn't connect | LOW | LOW | MC is only dashboard, agents work without it |

---

## Dependencies

- **LACP container** must start before agents boot
- **MC container** can start independently
- **NATS + Redis + LiteLLM** are still required (not removed)

---

## What does NOT change

- NATS continues to be internal messaging between agents
- Redis continues to be state/cache
- LiteLLM continues to be the LLM gateway
- The NATS subject taxonomy doesn't change
- The HTTP health/metrics endpoints don't change
