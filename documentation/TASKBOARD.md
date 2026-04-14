# Jart-OS Taskboard

**Last updated:** 2026-04-13
**Canonical ref:** JARTOS-CANONICAL-SPEC.md

## In Progress

| Who | Task | File/Dir | Status | Updated |
|-----|------|----------|--------|---------|
| LobeChat-jarvis | Migrate AgentBase to NATS | agents/core/base.py | ⬜ Queued | Apr 13 |
| LobeChat-jarvis | Deploy Mission Control real | TIER-07/10701-web-mission_control/ | ⬜ Queued | Apr 13 |

## Pending (reassign)

| # | Task | Priority | Dependencies |
|---|------|----------|-------------|
| T1 | Director Agent (study domain) | High | base.py NATS migration |
| T2 | Executor Agent (study domain) | High | base.py NATS migration |
| T3 | Guardian Agent | High | Policy gates |
| T4 | Council Agent voting | Medium | T1 + T2 + T3 |
| T5 | Validate pipeline end-to-end | Medium | T1-T4 |

## Blocked

| Task | Reason |
|------|--------|
| OpenRouter keys | Waiting for API key renewal |
| MiMo keys | Waiting for API key renewal |

## Completed

| Who | Task | Date |
|-----|------|------|
| LobeChat-jarvis | CANONICAL-SPEC v3 | Apr 11 |
| LobeChat-jarvis | STATUS-AND-PROGRESS | Apr 11 |
| LobeChat-jarvis | Policy gates YAML | Apr 11 |
| LobeChat-jarvis | TASKBOARD + agent-lock + protocol | Apr 11 |
| LobeChat-jarvis | Rebrand jartos → jart-os | Apr 11 |
| LobeChat-jarvis | Initial repo push | Apr 13 |
