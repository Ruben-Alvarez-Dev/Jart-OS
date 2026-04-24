# Deployment Guide

> How to deploy, configure, and operate Jart-OS in development and production.

## Table of Contents

- [System Requirements](#system-requirements)
- [Docker Compose Architecture](#docker-compose-architecture)
- [Tier Deployment](#tier-deployment)
- [Adding a New Service](#adding-a-new-service)
- [Network Architecture](#network-architecture)
- [Volume Management](#volume-management)
- [Monitoring Stack Deployment](#monitoring-stack-deployment)
- [Scaling Considerations](#scaling-considerations)
- [Production Hardening Checklist](#production-hardening-checklist)
- [Rollback Procedures](#rollback-procedures)

---

## System Requirements

### Hardware

| Resource | Minimum | Recommended | Production |
|----------|---------|-------------|------------|
| CPU | 2 cores | 4 cores (Apple M1+) | 8+ cores |
| RAM | 4 GB | 8 GB | 16+ GB |
| Disk | 10 GB free | 30 GB free | 100+ GB SSD |
| Network | Local | Tailscale VPN | Dedicated VPC |

### Software

| Software | Version | Purpose |
|----------|---------|---------|
| OS | macOS 12+ / Ubuntu 22.04+ | Host operating system |
| Docker Engine | 24.0+ | Container runtime |
| Docker Compose | v2.20+ | Service orchestration |
| Git | 2.40+ | Version control |
| Tailscale | Latest | Secure remote access (optional) |

### Current Reference Environment

- **Host**: Mac Mini M1, 16 GB RAM, macOS
- **Networking**: Tailscale mesh VPN
- **Docker**: Docker Desktop for Mac

---

## Docker Compose Architecture

Jart-OS uses a **root compose file** that includes tier-level compose files:

```
docker-compose.yml (root)
  ├── services/TIER-01/docker-compose.yml  (LiteLLM)
  ├── services/TIER-03/docker-compose.yml  (Redis, NATS)
  ├── services/TIER-04/docker-compose.yml  (Agents)
  ├── services/TIER-07/docker-compose.yml  (Dashboards)
  └── services/TIER-09/docker-compose.yml  (Monitoring)
```

### Root docker-compose.yml

```yaml
version: "3.8"

include:
  - services/TIER-01/docker-compose.yml
  - services/TIER-03/docker-compose.yml
  - services/TIER-04/docker-compose.yml
  - services/TIER-07/docker-compose.yml
  - services/TIER-09/docker-compose.yml
```

### Managing All Services

```bash
# Start everything
docker compose up -d

# Stop everything
docker compose down

# Restart a specific tier
docker compose -f services/TIER-01/docker-compose.yml restart

# View all logs
docker compose logs -f

# View logs for a specific service
docker compose logs -f litellm
```

### Using the Boot Script

```bash
./scripts/boot.sh start     # Start all services
./scripts/boot.sh stop      # Stop all services
./scripts/boot.sh restart   # Restart all services
./scripts/boot.sh status    # Show service status
./scripts/boot.sh logs      # Tail all logs
```

---

## Tier Deployment

Each tier is self-contained with its own `docker-compose.yml`.

### TIER-01: LLM Proxy

```yaml
services:
  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    container_name: jart-os-litellm
    ports:
      - "10201:4000"
    volumes:
      - ./config.yaml:/app/config.yaml
    networks:
      - jart-os-net
    restart: unless-stopped
```

| Setting | Value |
|---------|-------|
| Port | 10201 |
| Image | `ghcr.io/berriai/litellm:main-latest` |
| Config | `config.yaml` (model definitions) |

### TIER-03: Messaging

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: jart-os-redis
    ports:
      - "10301:6379"
    networks:
      - jart-os-net
    restart: unless-stopped

  nats:
    image: nats:2-alpine
    container_name: jart-os-nats
    ports:
      - "10302:4222"
      - "10303:6222"
      - "10304:8222"
    command: "--jetstream --store_dir /data"
    networks:
      - jart-os-net
    restart: unless-stopped
```

| Service | Port(s) | Image |
|---------|---------|-------|
| Redis | 10301 | `redis:7-alpine` |
| NATS | 10302–10304 | `nats:2-alpine` |

### TIER-07: Dashboards

```yaml
services:
  mission-control:
    image: nginx:alpine
    container_name: jart-os-mission-control
    ports:
      - "10701:80"
    networks:
      - jart-os-net

  grafana:
    image: grafana/grafana:latest
    container_name: jart-os-grafana
    ports:
      - "10702:3000"
    networks:
      - jart-os-net
    volumes:
      - grafana-data:/var/lib/grafana
```

### TIER-09: Monitoring

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: jart-os-prometheus
    ports:
      - "10901:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - jart-os-net
```

---

## Adding a New Service

Follow these steps to add a service to an existing tier.

### Step 1: Create the Service Definition

Add the service to the tier's `docker-compose.yml`:

```yaml
# services/TIER-07/docker-compose.yml
services:
  # ... existing services ...

  my-new-dashboard:
    image: my-dashboard:latest
    container_name: jart-os-my-dashboard
    ports:
      - "10703:8080"    # Follow port convention: 1XXYY
    environment:
      - API_URL=http://jart-os-litellm:4000
    networks:
      - jart-os-net
    restart: unless-stopped
```

### Step 2: Assign a Port

Use the port convention `1XXYY`:

- `XX` = tier number (e.g., `07` for TIER-07)
- `YY` = service sequence (e.g., `03` for the third service)

### Step 3: Connect to the Network

All services must join `jart-os-net`:

```yaml
networks:
  jart-os-net:
    external: true
```

### Step 4: Add Environment Variables

Update `.env` with any new configuration:

```bash
# My New Dashboard
MY_DASHBOARD_PORT=10703
MY_dashboard_API_KEY=...
```

### Step 5: Deploy

```bash
# Rebuild and start
docker compose up -d my-new-dashboard

# Verify
docker compose ps my-new-dashboard
curl http://localhost:10703/health
```

### Step 6: Update Documentation

- Add the service to this deployment guide
- Update `API-REFERENCE.md` with new endpoints
- Update `README.md` service table

---

## Network Architecture

### Docker Network

All services communicate through a shared Docker bridge network:

```
jart-os-net (bridge)
├── jart-os-litellm        (TIER-01)
├── jart-os-redis          (TIER-03)
├── jart-os-nats           (TIER-03)
├── jart-os-agents         (TIER-04)
├── jart-os-mission-control (TIER-07)
├── jart-os-grafana        (TIER-07)
└── jart-os-prometheus     (TIER-09)
```

### Inter-Service Communication

Inside the Docker network, services resolve each other by container name:

```python
# Inside a container
LITELLM_URL=http://jart-os-litellm:4000    # Not localhost:10201
REDIS_URL=redis://jart-os-redis:6379/0     # Not localhost:10301
NATS_URL=nats://jart-os-nats:4222          # Not localhost:10302
```

### Tailscale Integration

For remote access, Tailscale provides a mesh VPN:

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate
tailscale up

# Access services remotely (using Tailscale IP)
tailscale ip -4  # e.g., 100.64.0.1

# Access from another machine
curl http://100.64.0.1:10702  # Grafana
```

### Port Map (External Access)

| Port | Service | External Access |
|------|---------|-----------------|
| 10201 | LiteLLM | Tailscale only |
| 10301 | Redis | Tailscale only |
| 10302–10304 | NATS | Tailscale only |
| 10701 | Mission Control | Tailscale |
| 10702 | Grafana | Tailscale |
| 10901 | Prometheus | Tailscale only |

---

## Volume Management

### Named Volumes

| Volume | Service | Purpose | Backup Priority |
|--------|---------|---------|-----------------|
| `redis-data` | Redis | State, caches | Low (ephemeral) |
| `nats-data` | NATS | JetStream messages | Medium |
| `grafana-data` | Grafana | Dashboards, config | High |
| `prometheus-data` | Prometheus | Metrics (15-day retention) | Medium |

### Backup

```bash
# Backup all volumes
docker compose down
tar -czf jart-os-backup-$(date +%Y%m%d).tar.gz \
  /var/lib/docker/volumes/jart-os_*

# Backup specific volume
docker run --rm -v jart-os_grafana-data:/data -v $(pwd):/backup \
  alpine tar -czf /backup/grafana-backup.tar.gz /data
```

### Restore

```bash
# Restore from backup
docker run --rm -v jart-os_grafana-data:/data -v $(pwd):/backup \
  alpine tar -xzf /backup/grafana-backup.tar.gz -C /

docker compose up -d
```

### Cleanup

```bash
# Remove unused volumes (safe cleanup)
docker volume prune

# Remove specific volume (WARNING: data loss)
docker volume rm jart-os_redis-data
```

---

## Monitoring Stack Deployment

### Prometheus Configuration

```yaml
# services/TIER-09/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "jart-os-agents"
    static_configs:
      - targets:
          - "jart-os-director:10401"
          - "jart-os-executor:10402"
          - "jart-os-guardian:10403"
          - "jart-os-council:10404"
    metrics_path: /metrics

  - job_name: "jart-os-infrastructure"
    static_configs:
      - targets:
          - "jart-os-litellm:4000"
          - "jart-os-redis:6379"
    metrics_path: /metrics
```

### Grafana Dashboard Setup

1. Access Grafana at `http://localhost:10702`
2. Login with $MC_AUTH_USER / $MC_AUTH_PASS (set via env vars in docker-compose)
3. Add Prometheus data source:
   - URL: `http://jart-os-prometheus:9090`
   - Access: Server (proxy)
4. Import or create dashboards

---

## Scaling Considerations

### Horizontal Scaling

Agents can be scaled by running multiple instances:

```yaml
# Scale executors
services:
  executor:
    build: ./agents/tiers/TIER-04/executor
    deploy:
      replicas: 3
    environment:
      - NATS_URL=nats://jart-os-nats:4222
    networks:
      - jart-os-net
```

### Resource Limits

```yaml
services:
  executor:
    build: .
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
        reservations:
          cpus: "0.5"
          memory: 256M
```

### NATS JetStream Scaling

```bash
# Increase max memory for JetStream
nats-server --jetstream --store_dir /data \
  --max_mem_store 2GB \
  --max_file_store 10GB
```

---

## Production Hardening Checklist

### Security

- [ ] Change all default passwords (Grafana, Redis)
- [ ] Enable Redis AUTH with a strong password
- [ ] Restrict Docker network access (no host mode)
- [ ] Enable TLS for NATS connections
- [ ] Set up firewall rules (only expose necessary ports)
- [ ] Rotate API keys regularly
- [ ] Use Docker secrets instead of environment variables for sensitive data

### Reliability

- [ ] Configure `restart: unless-stopped` on all services
- [ ] Set up health checks in Docker Compose
- [ ] Configure log rotation
- [ ] Set up automated backups for persistent volumes
- [ ] Monitor disk space and set alerts
- [ ] Configure Prometheus alerting rules

### Performance

- [ ] Tune Redis `maxmemory` and eviction policy
- [ ] Set Prometheus retention period appropriately
- [ ] Configure LiteLLM connection pooling
- [ ] Set resource limits on all containers
- [ ] Enable Docker BuildKit for faster builds

### Monitoring

- [ ] Configure Prometheus alerting rules
- [ ] Set up Grafana alert notifications (Discord, email)
- [ ] Monitor container health with `docker compose ps`
- [ ] Track resource usage with `docker stats`

---

## Rollback Procedures

### Quick Rollback (Single Service)

```bash
# Stop the problematic service
docker compose stop litellm

# Revert to previous image version
docker compose pull litellm:previous-version

# Restart
docker compose up -d litellm
```

### Full System Rollback

```bash
# 1. Stop all services
./scripts/boot.sh stop

# 2. Revert to a known-good commit
git log --oneline -10  # Find the good commit
git checkout <good-commit-hash>

# 3. Restart all services
./scripts/boot.sh start

# 4. Verify
./scripts/boot.sh status
```

### Data Recovery

```bash
# Restore from backup
docker compose down
tar -xzf jart-os-backup-YYYYMMDD.tar.gz -C /
docker compose up -d
```

### Emergency Procedures

```bash
# Nuclear option — reset everything
docker compose down -v    # WARNING: deletes all volumes
docker system prune -a    # WARNING: removes all unused images
git checkout main
./scripts/boot.sh start
```
