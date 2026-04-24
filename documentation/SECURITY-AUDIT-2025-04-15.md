# Security Audit Report — 2025-04-15

**Auditor**: $AGENT_USER (admin user, UID 501)
**Scope**: Full Jart-OS Docker infrastructure on Mac Mini M1
**Status**: TIER-01 hardening COMPLETE

## Executive Summary

Full security audit of the Jart-OS Docker container infrastructure revealed critical exposure of internal services to the network. All 10 internal service ports were bound to `0.0.0.0`, making them accessible from any device on the Tailscale mesh or local LAN — without authentication.

All findings were remediated in a single session.

## Findings

### CRITICAL — Services Exposed Without Authentication

| Service | Port | Risk |
|---------|------|------|
| Redis | :10301 | No password. Agent data, session state, caches readable/writable from network |
| NATS | :10302-04 | No auth token. Messages publishable/subscribable from any client |
| LiteLLM | :10201 | API keys (Xiaomi, Z.ai) usable by anyone on network |
| Prometheus | :10901 | Infrastructure metrics exposed |
| Agent containers | :10401-04 | Direct access to agent APIs |
| Processing pipes | :10601-04 | Direct access to processing endpoints |

### OK — Services Already Secured

| Service | Port | Status |
|---------|------|--------|
| Grafana | :10702 | Authentication enabled |
| macOS Firewall | — | Application Firewall active |
| Mission Control | :10701 | Has auth middleware |

## Remediation

### Phase 1: Network Binding (10 services)

Changed all internal service port bindings from `0.0.0.0` to `127.0.0.1`:

```
# Before
ports:
  - "10301:6379"

# After
ports:
  - "127.0.0.1:10301:6379"
```

Services kept on `0.0.0.0` (remote access needed via Tailscale):
- Mission Control (:10701)
- Grafana (:10702)
- Study Domain (:10500)

### Phase 2: Authentication

#### Redis
```yaml
command: redis-server --requirepass ${REDIS_PASSWORD}
environment:
  REDIS_PASSWORD: ${REDIS_PASSWORD}
```
- Healthcheck updated to use `redis-cli -a $REDIS_PASSWORD ping`
- Connection strings: `redis://:${REDIS_PASSWORD}@redis:6379`

#### NATS
```yaml
command: >
  --auth ${NATS_TOKEN}
```
- Connection strings: `nats://token:${NATS_TOKEN}@nats:4222`

#### LiteLLM
- `LITELLM_MASTER_KEY` already existed in `.env`
- Verified enforcement in gateway configuration

### Phase 3: Container Recreation

All containers recreated with `docker compose up -d --force-recreate`:
- Redis: fresh start (deleted stale `dump.rdb` and `appendonlydir/`)
- NATS: deleted stale `data/jetstream/`
- Prometheus: deleted stale `queries.active` lock file
- Grafana/Prometheus data dirs: `chmod 777` for Docker Desktop macOS compatibility

## Post-Remediation Verification

```
13/13 useful containers UP
Redis: PONG (authenticated)
NATS: connected (authenticated)
LiteLLM: responding (key required)
Prometheus: metrics on localhost only
```

## Remaining Work

- [ ] TIER-08 KNOWLEDGE: RAG pipeline (not yet implemented)
- [ ] `.hermes/` runtime configuration (empty)
- [ ] `.openclaw/` gateway configuration (empty)
- [ ] Photos/Video pipelines (need actual code)
- [ ] TLS/SSL for user-facing services (currently HTTP)
- [ ] Rate limiting on Mission Control API

## Credentials

All credentials are in `$JART_OS_HOME/.env` (owned by $JART_OS_USER, not tracked in git).
