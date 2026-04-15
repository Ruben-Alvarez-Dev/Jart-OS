# SPEC: Integración LACP-First en Jart-OS

**Estado:** DRAFT  
**Fecha:** 2026-04-15  
**Decisión:** Opción B — LACP como control plane principal  
**Herramientas:** LACP v0.9.0 + Builderz Mission Control (prebuilt)

---

## Resumen (para humanos cansados)

Hoy: 4 agentes (Director, Executor, Guardian, Council) se hablan por NATS y cada uno hace lo suyo.

Después: LACP es el jefe que controla cómo y cuándo trabajan los agentes. Mission Control es la pantalla linda donde ves todo. NATS sigue existiendo como mensajería interna.

---

## Decisiones tomadas

| ID | Decisión | Detalle |
|----|----------|---------|
| D9 | LACP manda | LACP controla ejecución de agentes con quality gates |
| D10 | MC prebuilt | `ghcr.io/builderz-labs/mission-control:latest`, no fork |
| D11 | Nuke old MC | Se borra todo `TIER-07/10701-web-mission_control/` |
| D12 | LACP en TIER-09 | Container en `TIER-09-CONTROL/10902-control-lacp/` |
| D13 | Agentes como LACP tasks | Cada agente se ejecuta via LACP harness |

---

## Mapeo de roles

Los 4 agentes de Jart-OS mapean a las etapas del workflow de LACP:

```
Director  → planner     (planifica, descompone)
Executor  → developer   (ejecuta, genera resultado)
Guardian  → verifier    (valida, verifica calidad)
Council   → reviewer    (revisión tri-unit, consenso)
```

---

## Estado actual (ANTES)

```
agents/core/base.py      — 560 líneas (NATS + Redis + LLM + HTTP)
agents/runtime/main.py   — 411 líneas (4 agentes)
docker-compose.yml       — include pattern, 13 servicios
TIER-07/10701-mc/        — MC custom (A ELIMINAR)
TIER-09/                 — solo Prometheus
```

---

## Estado final (DESPUÉS)

```
agents/core/base.py           — MODIFICADO (agrega LACP harness)
agents/core/lacp_client.py    — NUEVO (adaptador Python ↔ LACP CLI)
agents/runtime/main.py        — MODIFICADO (agentes usan LACP)
docker-compose.yml            — MODIFICADO (agrega MC + LACP)
TIER-07/10701-mc/             — ELIMINADO
TIER-07/10701-web-mc-builderz/— NUEVO (MC prebuilt)
TIER-09/10902-control-lacp/   — NUEVO (LACP container)
```

---

## Fases de implementación

### Fase 0: Limpieza y setup (sin romper nada)

**Qué:** Preparar el terreno sin tocar agentes existentes.

1. **Backup** del repo actual (git branch `feature/lacp-first`)
2. **Nuke old MC**: eliminar `TIER-07/10701-web-mission_control/`
3. **Crear** `TIER-07/10701-web-mc-builderz/docker-compose.yml` con MC prebuilt
4. **Crear** `TIER-09/10902-control-lacp/docker-compose.yml` con LACP container
5. **Actualizar** root `docker-compose.yml` con los nuevos includes
6. **Verificar** que MC y LACP levantan con `docker compose up`

**Criterio de aceptación:**
- `docker compose up` levanta todos los servicios
- MC responde en `http://localhost:PUERTO` con dashboard vacío
- LACP responde a `lacp status` dentro del container

**Archivos que cambian:** 0 archivos existentes, ~4 archivos nuevos, docker-compose.yml

---

### Fase 1: Adaptador LACP

**Qué:** Crear el puente entre Python (agentes) y LACP (CLI).

LACP es un CLI (comandos de terminal). Nuestros agentes son Python. Necesitamos un adaptador.

1. **Crear** `agents/core/lacp_client.py`
   - `harness_validate(task_manifest)` → validar tarea antes de ejecutar
   - `harness_run(task_manifest, agent_fn)` → ejecutar con quality gates
   - `workflow_advance(stage)` → avanzar etapa del workflow
   - `quality_check(output)` → pasar por stop_quality_gate
2. **Configurar** LACP con los policies de Jart-OS
   - `sandbox-policy.json` adaptado a nuestros tiers
   - `risk-policy-contract.json` con nuestros criterios

**Criterio de aceptación:**
- Un test simple: `lacp_client.harness_validate({"task": "test"})` responde OK o FAIL
- Los quality gates responden sin error

**Archivos nuevos:** `agents/core/lacp_client.py`, `TIER-09/10902-control-lacp/config/`

---

### Fase 2: Agentes usan LACP

**Qué:** Modificar los 4 agentes para pasar por LACP.

1. **Modificar** `agents/core/base.py`
   - Agregar `self.lacp` (LACP client) al `__init__`
   - Agregar `boot_lacp()` al boot sequence
   - Modificar `call_llm()` para que pase por quality gates de LACP
2. **Modificar** `agents/runtime/main.py`
   - Cada agente: recibir comando → crear task manifest → `harness_run()` → evidence manifest
   - Director: `harness_validate()` antes de delegar
   - Executor: `harness_run()` wrap en toda ejecución
   - Guardian: usar LACP `stop_quality_gate` en vez de LLM custom para validar
   - Council: quality check de LACP como input para las 3 votaciones

**Criterio de aceptación:**
- `docker compose up` levanta 4 agentes
- Cada agente se registra en LACP
- Un comando enviado por NATS pasa por LACP harness
- Quality gate aprueba/rechaza según resultado

**Archivos que cambian:** `base.py`, `main.py`

---

### Fase 3: Mission Control ve todo

**Qué:** Conectar agentes y LACP con MC para visualización.

1. **Agentes se registran** en MC via REST al arrancar
   - `POST /api/agents/register` con nombre, rol, capabilities
2. **LACP reporta** resultados de ejecución a MC
   - Task outcomes (pass/fail/score) via REST
3. **MC muestra**:
   - Agentes activos y su estado
   - Kanban con tareas en progreso
   - Quality scores de LACP
   - Cost tracking (tokens LLM usados)

**Criterio de aceptación:**
- MC dashboard muestra los 4 agentes registrados
- Una tarea completada aparece en el kanban de MC
- Quality scores de LACP son visibles en MC

**Archivos que cambian:** `base.py` (agrega registro MC), `lacp_client.py` (agrega reporte MC)

---

### Fase 4: Memoria y calidad (opcional / futuro)

**Qué:** Activar features avanzadas de LACP.

1. SMS Memory — agentes "recuerdan" experiencias pasadas
2. Obsidian vault — conocimiento persistente
3. Sandbox routing — tareas críticas van a sandbox remoto
4. Incident response — SEV1/2/3 handling

**Estado:** Se define después de Fase 3 completa y funcionando.

---

## Rollback plan

Si algo rompe:
1. **Git branch** `feature/lacp-first` — todos los cambios están ahí
2. Si LACP no funciona: `git revert` al branch anterior, agentes vuelven a NATS-only
3. Si MC no funciona: agentes siguen funcionando sin MC (es solo visualización)
4. Old MC: backup en git history, `git checkout main -- TIER-07/10701-web-mission_control/`

---

## Riesgos (honestos)

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| LACP alpha rompe API | ALTA | ALTO | Branch separado, rollback fácil |
| LACP CLI no se integra bien con Python | MEDIA | ALTO | Adaptador con fallback a NATS directo |
| Quality gates rechazan todo | MEDIA | MEDIO | Config thresholds permisivos al inicio |
| LACP container pesa mucho | BAJA | BAJO | LACP son scripts, no es pesado |
| MC prebuilt no se conecta | BAJA | BAJO | MC es solo dashboard, agentes funcionan sin él |

---

## Dependencias

- **LACP container** debe levantar antes de que agentes arranquen
- **MC container** puede levantar independientemente
- **NATS + Redis + LiteLLM** siguen siendo necesarios (no se eliminan)

---

## Qué NO cambia

- NATS sigue siendo la mensajería interna entre agentes
- Redis sigue siendo el state/cache
- LiteLLM sigue siendo el gateway a LLMs
- El subject taxonomy de NATS no cambia
- Los HTTP endpoints de health/metrics no cambian
