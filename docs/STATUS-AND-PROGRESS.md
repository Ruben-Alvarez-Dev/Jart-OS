# Jart-OS — Estado, Progreso y Plan de Acción

**Version:** 1.0.0
**Date:** 2026-04-11
**Status:** WORKING DOCUMENT — Updated as project progresses
**Canonical Reference:** [JART-OS-CANONICAL-SPEC.md](JART-OS-CANONICAL-SPEC.md)

---

## Resumen Ejecutivo

Jart-OS es un sistema de agentes AI que corre en un Mac Mini M1 (16GB) para preparar las study de profesor de domain subject (Especialidad , regulatory framework 2026, examen junio 2026).

**Estado actual: Infraestructura base operativa. Agentes, pipelines y dominio sin implementar.**

---

## ¿Qué es Jart-OS?

Un sistema operativo agéntico con 10 capas (TIERS) donde cada aplicación es autocontenida — su propio Docker, su propia config, sus propios datos. Si algo falla, no se lleva al vecino.

Los agentes trabajan en **tri-unidades** (Director planifica → Ejecutor genera → Guardián valida) y se comunican por **NATS**. El gateway **LiteLLM** unifica 3 proveedores de LLM con routing inteligente por tarea.

---

## Línea de Tiempo — Qué se ha hecho

```
Abril 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Día 8   ████████  Proyecto arranca. 8 variantes en /simba/.
                   Evaluación de repos: mission-control,
                   lacp, hermes-agent, opencode-multiagent.

Día 9   ████████████████  Estructura TIERS creada.
                   Docker compose raíz (include: pattern).
                   6 servicios levantados: Redis, NATS,
                   LiteLLM, MC, Grafana, Prometheus.
                   boot.sh operativo.
                   ARCHITECTURE.md v2 escrita.
                   AgentBase (Python) creada — 175 líneas.
                   Carpetas para 4 agentes y 4 pipelines
                   creadas (vacías).

Día 10  ██████████████  LiteLLM fixeado:
                   - Endpoint cambiado de open.bigmodel.cn
                     → api.z.ai/api/coding/paas/v4
                   - .env poblado con API keys reales
                   - docker-compose corregido (--config flag)
                   - Z.AI GLM-5 y GLM-4.7 confirmados OK
                   - phi3-local (Ollama) confirmado OK
                   - OpenRouter y MiMo: keys expiradas
                   - Problema permisos simba/jarvis resuelto
                     (sudo para writes en /jarvis/)
                   
Día 11  ████████████████████  SPEC CANÓNICA escrita:
                   - 1.108 líneas, 25 secciones
                   - Unifica 8+ documentos previos
                   - 8 decisiones arquitectónicas resueltas
                   - Roadmap a 5 fases definido
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Estado Actual — Qué funciona AHORA

### 🔴🟡🟢 Semáforo General

```
TIER-00 METAL        ⬜  Vacío — Ollama corre en host fuera de Docker
TIER-01 SECURITY     ⬜  Vacío — pf firewall activo pero no gestionado
TIER-02 GATEWAY      🟡  LiteLLM OK (3 de 9 modelos). OpenClaw pendiente
TIER-03 SERVICES     🟢  Redis + NATS estables 45+ horas
TIER-04 AGENTS       ⬜  Carpetas creadas, SIN código funcional
TIER-05 FRAMEWORKS   ⬜  Hermes-agent descargado, no integrado
TIER-06 PROCESSES    ⬜  Carpetas creadas, SIN pipelines
TIER-07 INTERFACES   🟡  MC estático + Grafana OK. MC real pendiente
TIER-08 KNOWLEDGE    ⬜  Vacío — RAG sin instalar
TIER-09 CONTROL      🟢  Prometheus recolectando métricas
```

### Servicios Docker (6/6 UP)

| Container | TIER | Puerto | Uptime | Salud |
|-----------|------|--------|--------|-------|
| jart-os-redis | 03 SERVICES | 10301 | 45h | ✅ Healthy |
| jart-os-nats | 03 SERVICES | 10302-04 | 45h | ✅ Up |
| jart-os-litellm | 02 GATEWAY | 10201 | 33h | ✅ Up |
| jart-os-mc | 07 INTERFACES | 10701 | 45h | ✅ 200 OK |
| jart-os-grafana | 07 INTERFACES | 10702 | 45h | ✅ 200 OK |
| jart-os-prometheus | 09 CONTROL | 10901 | 45h | ✅ 200 OK |

### Modelos LLM vía LiteLLM

| Modelo | Proveedor | Estado | Uso |
|--------|-----------|--------|-----|
| glm-5 | Z.AI | ✅ Funciona | Pensar — specs, arquitectura |
| glm-4.7 | Z.AI | ✅ Funciona | Hacer — ejecución de specs |
| phi3-local | Ollama | ✅ Funciona | Validar — checks offline |
| free-gemma4-31b | OpenRouter | 🔴 Key expirada | Hacer — bulk |
| free-llama33-70b | OpenRouter | 🔴 Key expirada | Hacer — bulk |
| free-nemotron-super | OpenRouter | 🔴 Key expirada | Hacer — bulk |
| free-qwen3-coder | OpenRouter | 🔴 Key expirada | Hacer — bulk |
| mimo-flash | Xiaomi | 🔴 Key expirada | Validar |
| mimo-plan | Xiaomi | 🔴 Key expirada | Hacer |

### Código Existente

| Archivo | Líneas | Estado | Qué hace |
|---------|--------|--------|----------|
| `agents/core/base.py` | 175 | ✅ Funcional | Clase AgentBase: HTTP, LLM, Redis PubSub, métricas |
| `agents/runtime/main.py` | 285 | 🟡 Skeleton | Runner de agentes, necesita migrar a NATS |
| `agents/Dockerfile.agent` | ~15 | ✅ OK | Imagen genérica Python para agentes |
| `scripts/boot.sh` | ~50 | ✅ OK | start/stop/status/logs/restart |
| `docs/JART-OS-CANONICAL-SPEC.md` | 1.108 | ✅ OK | Fuente única de verdad |
| `docs/ARCHITECTURE.md` | ~130 | ⚠️ Obsoleta | Reemplazada por CANONICAL-SPEC |

### Tamaño del Proyecto

```
Total en disco:  610 MB (mayoría = Grafana data + Prometheus)
Archivos:        27.636 (mayoría = MC estático assets)
Código propio:   460 líneas (base.py + main.py)
Compose files:   7 operativos
```

---

## Qué hay HECHO vs. qué FALTA

### ✅ Hecho

| # | Qué | Fecha | Detalle |
|---|-----|-------|---------|
| 1 | Evaluación de repos externos | 8-abr | mission-control, lacp, hermes, opencode-multiagent |
| 2 | Estructura 10 TIERS | 9-abr | Carpetas con patrón autocontenida |
| 3 | Docker Compose raíz | 9-abr | `include:` pattern, red compartida |
| 4 | Redis operativo | 9-abr | :10301, healthy, bind mount |
| 5 | NATS JetStream operativo | 9-abr | :10302-04, persistencia activa |
| 6 | LiteLLM proxy operativo | 10-abr | :10201, 9 modelos (3 funcionando) |
| 7 | Grafana operativo | 9-abr | :10702, admin/jart-os2026 |
| 8 | Prometheus operativo | 9-abr | :10901, scrape targets |
| 9 | Mission Control (estático) | 9-abr | :10701, nginx |
| 10 | boot.sh | 9-abr | start/stop/status/logs/restart |
| 11 | AgentBase Python | 10-abr | 175 líneas, heredable por todos los agentes |
| 12 | .env con API keys | 10-abr | Z.AI key activa, resto pendiente renovar |
| 13 | Spec canónica | 11-abr | 1.108 líneas, 25 secciones, 8 decisiones cerradas |
| 14 | Convenciones unificadas | 11-abr | IDs, puertos, NATS subjects, directorios |
| 15 | Firewall pf | 9-abr | Reglas para puertos Jart-OS via Tailscale |

### ⬜ Pendiente — Por Fase

#### FASE 1: Agent Core (Siguiente)

| # | Qué | Dónde | Estimación | Dependencias |
|---|-----|-------|------------|-------------|
| 1.1 | Migrar AgentBase a NATS | `agents/core/base.py` | 2h | Ninguna |
| 1.2 | Policy gate YAML: spec-gate | `agents/policies/` | 30min | Ninguna |
| 1.3 | Policy gate YAML: quality-gate | `agents/policies/` | 30min | Ninguna |
| 1.4 | Agente Director (study) | `TIER-04/10401-agent-director/` | 4h | 1.1 |
| 1.5 | Agente Executor (study) | `TIER-04/10402-agent-executor/` | 4h | 1.1 |
| 1.6 | Agente Guardian | `TIER-04/10403-agent-guardian/` | 4h | 1.1, 1.2, 1.3 |
| 1.7 | Agente Council | `TIER-04/10404-agent-council/` | 3h | 1.4, 1.5, 1.6 |
| 1.8 | NATS subject schema deploy | Script de creación | 1h | Ninguna |
| 1.9 | Renovar keys OpenRouter + MiMo | `.env` | 15min | Rubén |

#### FASE 2: Knowledge Pipeline

| # | Qué | Dónde | Estimación | Dependencias |
|---|-----|-------|------------|-------------|
| 2.1 | Pipeline PDF (PyMuPDF + Vision) | `pipelines/pdf/` | 8h | Fase 1 |
| 2.2 | Pipeline Fotos CEDE (Vision API) | `pipelines/photos/` | 6h | Fase 1 |
| 2.3 | Pipeline Vídeo (ffmpeg + Whisper) | `pipelines/video/` | 6h | Fase 1 |
| 2.4 | Pipeline RAG (LlamaIndex + Qdrant) | `pipelines/rag/` | 8h | 2.1, 2.2, 2.3 |
| 2.5 | Ingestar 872 PDFs | — | ~12h proceso | 2.1 |
| 2.6 | Ingestar 1.695 fotos CEDE | — | ~8h proceso | 2.2 |
| 2.7 | Transcribir 18 vídeos | — | ~18h proceso | 2.3 |
| 2.8 | Desplegar RAGFlow (UI exploración) | `TIER-08/10801-rag-ragflow/` | 3h | 2.4 |

#### FASE 3: Dominio Study

| # | Qué | Bloque | Dependencias |
|---|-----|-------|-------------|
| 3.1 | Pipeline contenido funcional | Bloque 1 | Fase 2 |
| 3.2 | Generador de Programación Didáctica | Bloque 2 | 3.1, Director + Executor |
| 3.3 | Simulador examen teórico (34 temas) | Bloque 3 | 3.1, Director + Examiner |
| 3.4 | Protocolos examen práctico | Bloque 4 | 3.1, Tri-unit Domain Subject |
| 3.5 | Simulador tribunal oral | Bloque 5 | 3.2, Director + Oral Coach |

#### FASE 4: Mission Control Real + Integraciones

| # | Qué | Dónde | Dependencias |
|---|-----|-------|-------------|
| 4.1 | Desplegar builderz-labs/mission-control | `TIER-07/10701-web-mission_control/` | Ninguna |
| 4.2 | Configurar workflows estudio | Mission Control | 4.1 |
| 4.3 | Integración email/calendario | Mission Control | 4.1 |
| 4.4 | Bot Telegram via OpenClaw | `TIER-02/10202-proxy-openclaw/` | OpenClaw deploy |
| 4.5 | Desplegar OpenClaw Gateway | `TIER-02/10202-proxy-openclaw/` | Ninguna |
| 4.6 | Integración 1Password `op` CLI | `scripts/boot.sh` | Ninguna |
| 4.7 | Notificaciones y asistente personal | OpenClaw + Telegram | 4.4, 4.5 |

#### FASE 5: Escalar

| # | Qué | Dependencias |
|---|-----|-------------|
| 5.1 | Dominios adicionales (/dev, /infra) | Fase 1 completa |
| 5.2 | PostgreSQL para audit trail | Cuando sea necesario |
| 5.3 | Estrategia backup | Cuando haya datos críticos |
| 5.4 | CI/CD si proyecto crece | Opcional |
| 5.5 | LM Studio + LM Link en LiteLLM | Más modelos locales |

---

## Mapa Visual — Qué existe vs. Qué falta

```
                    EXISTE ✅              SKELETON 🟡           FALTA ⬜
                    ──────────             ───────────           ──────────

TIER-00 METAL                              Ollama en host        Port monitor
                                           phi4, phi3            llama.cpp config

TIER-01 SECURITY                                                 fail2ban
                                                                  Infisical/1P
                                                                  Reverse proxy

TIER-02 GATEWAY   LiteLLM :10201                               OpenClaw :10202
                  3 modelos OK

TIER-03 SERVICES  Redis :10301
                  NATS :10302-04

TIER-04 AGENTS                           Carpetas 10401-04     4 agentes dockerizados
                  AgentBase.py                                 Policy gates YAML
                                                               NATS integration
                                                               Tri-unit configs

TIER-05 FRAMEWORKS                       hermes-agent/          Hermes integrado
                                         descargado             OpenClaw runtime

TIER-06 PROCESSES                        Carpetas pdf/photos/   Pipeline código
                                         video/rag              Whisper, Vision, LlamaIndex

TIER-07 INTERFACES MC estático :10701                          Mission Control real
                  Grafana :10702                               Workflows, estudio

TIER-08 KNOWLEDGE                                               RAGFlow :10801
                                                                  AnythingLLM
                                                                  LlamaIndex deploy
                                                                  Qdrant collection

TIER-09 CONTROL   Prometheus :10901                             Alertas configuradas
                  Grafana dashboards                            Audit logging
```

---

## Decisiones Tomadas

(Las 8 resueltas en la sesión del 11-abr-2026. Detalle completo en [CANONICAL-SPEC §24](JART-OS-CANONICAL-SPEC.md))

| # | Decisión | Resolución |
|---|----------|-----------|
| D1 | API keys | Rubén las gestiona. Pasar cuando se necesiten |
| D2 | Runtime de agentes | **AgentBase** propio. OpenClaw/Hermes como capas SOTA |
| D3 | Mensajería | **NATS** para TODO. Redis solo para estado/cache |
| D4 | Motor RAG | **LlamaIndex** (motor) + **RAGFlow** (UI) |
| D5 | Secrets | **1Password** con `op` CLI. Ya lo usas |
| D6 | Comunicación equipo | **Telegram** (vía OpenClaw) |
| D7 | Número de agentes | **12 inicial** → escalar a 30+ |
| D8 | Mission Control | **Real** (builderz-labs). Reemplazar estático |

---

## Próximos Pasos Inmediatos (Esta Semana)

```
PRIORIDAD 1 ─── Renovar API keys OpenRouter + Xiaomi
                → Desbloquea 6 modelos adicionales
                → 15 min

PRIORIDAD 2 ─── Migrar AgentBase a NATS
                → base.py usa Redis PubSub, necesita NATS
                → Desbloquea todos los agentes
                → ~2h

PRIORIDAD 3 ─── Policy Gate YAMLs
                → spec-gate.yaml + quality-gate.yaml
                → Desbloquea Guardian
                → ~1h

PRIORIDAD 4 ─── Primer agente: Director Study
                → Planifica, descompone, delega
                → El cerebro del sistema
                → ~4h

PRIORIDAD 5 ─── Deploy Mission Control real
                → builderz-labs/mission-control
                → Reemplazar estático
                → ~3h
```

---

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Disco lleno (55GB libre) | Media | Alto | Bind mounts, limpiar regulares, sin Docker volumes |
| RAM limitada (16GB) | Media | Medio | Agentes se levantan bajo demanda, dormants = 0 RAM |
| Keys caducan | Alta | Bajo | 1Password + renovar cuando fallen |
| Examen junio 2026 | Certeza | Crítico | Priorizar Bloques 2-5 sobre optimización |
| Over-engineering | Media | Medio | P3: "Only build what gets used" |

---

## Contacto y Referencias

| Concepto | Dónde |
|----------|-------|
| Spec canónica | `$JART_OS_HOME/docs/JART-OS-CANONICAL-SPEC.md` |
| Este documento | `$JART_OS_HOME/docs/STATUS-AND-PROGRESS.md` |
| Docs históricos | `$STUDY_DATA_DIR/PROJECT-Jart-OS/` |
| Boot manager | `./scripts/boot.sh start` |
| Dashboard | http://localhost:10701 |
| Grafana | http://localhost:10702 (admin / jart-os2026) |
| LiteLLM models | `curl -H "Authorization: Bearer REDACTED_LITELLM_MASTER_KEY" http://localhost:10201/models` |
| NATS monitor | http://localhost:10304 |

---

*Última actualización: 2026-04-11 18:30*
*Próxima revisión: Cuando se complete la Fase 1*
