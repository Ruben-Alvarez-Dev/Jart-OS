# Jart-OS Taskboard

**Last updated:** 2026-04-11
**Canonical ref:** docs/JARTOS-CANONICAL-SPEC.md

## En curso

| Who | Task | File/Dir | Status | Updated |
|-----|------|----------|--------|---------|
| LobeChat-jarvis | Migrate AgentBase to NATS | agents/core/base.py | ⬜ Queued | Apr 11 |
| LobeChat-jarvis | Deploy Mission Control real | TIER-07/10701-web-mission_control/ | ⬜ Queued | Apr 11 |

## Pendiente (reasignar)

| # | Task | Priority | Dependencies |
|---|------|----------|-------------|
| T1 | Agente Director oposiciones | Alta | base.py NATS migration |
| T2 | Agente Executor oposiciones | Alta | base.py NATS migration |
| T3 | Agente Guardian | Alta | Policy gates |
| T4 | Agente Council voting | Media | T1 + T2 + T3 |
| T5 | Validar pipeline end-to-end | Media | T1-T4 |

## Bloqueado

| Task | Razón |
|------|-------|
| OpenRouter keys | Esperando renovar API key |
| MiMo keys | Esperando renovar API key |

## Completado

| Who | Task | Date |
|-----|------|------|
| LobeChat-jarvis | CANONICAL-SPEC v3 | Apr 11 |
| LobeChat-jarvis | STATUS-AND-PROGRESS | Apr 11 |
| LobeChat-jarvis | Policy gates YAML | Apr 11 |
| LobeChat-jarvis | TASKBOARD + agent-lock + protocol | Apr 11 |
| LobeChat-jarvis | Rebrand jartos → jart-os | Apr 11 |
