# Troubleshooting Guide

> Common issues, diagnostic commands, and recovery procedures for Jart-OS.

## Table of Contents

- [Docker Issues](#docker-issues)
- [LiteLLM Issues](#litellm-issues)
- [Redis Issues](#redis-issues)
- [NATS Issues](#nats-issues)
- [Agent Issues](#agent-issues)
- [Network Issues](#network-issues)
- [Performance Issues](#performance-issues)
- [Git Issues](#git-issues)
- [Diagnostic Commands](#diagnostic-commands)
- [Recovery Procedures](#recovery-procedures)

---

## Docker Issues

### Containers Won't Start

**Symptoms**: `docker compose up` fails, containers exit immediately.

```bash
# Check container status
docker compose ps -a

# View exit logs
docker compose logs <service-name>

# Common causes:
# 1. Port already in use
lsof -i :10201  # Check specific port

# 2. Volume mount issues
docker volume ls | grep jart-os

# 3. Image pull failure
docker pull ghcr.io/berriai/litellm:main-latest
```

**Solution**:

```bash
# Free the conflicting port
kill $(lsof -t -i :10201)

# Remove orphaned containers
docker compose down --remove-orphans

# Rebuild and restart
docker compose up -d --build
```

### Port Conflicts

**Symptoms**: `Bind for 0.0.0.0:10201 failed: port is already allocated`.

```bash
# Find what's using the port
lsof -i :10201
# or
netstat -vanp tcp | grep 10201

# Option 1: Stop the conflicting container
docker stop <conflicting-container>

# Option 2: Change the port in docker-compose.yml
ports:
  - "10202:4000"  # Use a different host port
```

### Volume Permission Errors

**Symptoms**: `Permission denied` when accessing mounted volumes.

```bash
# Check volume permissions
docker volume inspect jart-os_redis-data

# Fix permissions (macOS)
docker compose down
sudo chown -R $(id -u):$(id -g) ./data/
docker compose up -d

# Nuclear option — recreate volumes
docker compose down -v
docker compose up -d
```

### Docker Desktop Issues

**Symptoms**: Docker Desktop is unresponsive or slow.

```bash
# Restart Docker Desktop (macOS)
osascript -e 'quit app "Docker"'
open -a Docker

# Reset Docker (WARNING: removes all containers/images)
# Docker Desktop → Troubleshoot → Clean / Purge data

# Check Docker resources
docker system info | grep -i memory
docker system info | grep -i cpu
```

---

## LiteLLM Issues

### Model Not Found

**Symptoms**: `Model 'glm-5' not found` error.

```bash
# Check available models
curl http://localhost:10201/v1/models

# Check LiteLLM config
docker exec jart-os-litellm cat /app/config.yaml

# Verify model is configured
curl -X POST http://localhost:10201/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "glm-5", "messages": [{"role": "user", "content": "test"}]}'
```

**Solution**: Update `config.yaml` with the correct model definition:

```yaml
model_list:
  - model_name: glm-5
    litellm_params:
      model: zhipu/glm-5
      api_key: os.environ/GLM_API_KEY
```

### API Key Errors

**Symptoms**: `401 Unauthorized` or `AuthenticationError`.

```bash
# Check if API key is set
docker exec jart-os-litellm env | grep API_KEY

# Verify in .env
grep API_KEY /Users/jarvis/Jart-OS/.env

# Test with explicit key
curl -X POST http://localhost:10201/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "glm-5", "messages": [{"role": "user", "content": "test"}]}'
```

### Timeout Errors

**Symptoms**: `TimeoutError` or `504 Gateway Timeout`.

```bash
# Check LiteLLM health
curl -w "%{time_total}s\n" http://localhost:10201/health

# Check LiteLLM logs for errors
docker logs jart-os-litellm --tail 50 | grep -i error

# Increase timeout in agent configuration
call_llm(prompt="...", model="glm-5", timeout=60.0)
```

### LiteLLM Won't Start

```bash
# Check logs
docker logs jart-os-litellm 2>&1

# Common issue: invalid config.yaml
docker exec jart-os-litellm python -c "import yaml; yaml.safe_load(open('/app/config.yaml'))"

# Restart with fresh state
docker compose -f services/TIER-01/docker-compose.yml down
docker compose -f services/TIER-01/docker-compose.yml up -d
```

---

## Redis Issues

### Connection Refused

**Symptoms**: `redis.exceptions.ConnectionError: Error connecting to Redis`.

```bash
# Check if Redis is running
docker compose ps redis

# Check Redis logs
docker logs jart-os-redis --tail 50

# Test connection
docker exec jart-os-redis redis-cli -p 10301 PING
# Expected: PONG

# Check from host
redis-cli -p 10301 PING
```

**Solution**:

```bash
# Restart Redis
docker compose restart redis

# If still failing, check network
docker network inspect jart-os-net | grep redis
```

### High Memory Usage

**Symptoms**: Redis using excessive memory, OOM errors.

```bash
# Check memory usage
docker exec jart-os-redis redis-cli -p 10301 INFO memory

# Check key count
docker exec jart-os-redis redis-cli -p 10301 DBSIZE

# Find large keys
docker exec jart-os-redis redis-cli -p 10301 \
  --bigkeys

# Set memory limit and eviction policy
docker exec jart-os-redis redis-cli -p 10301 \
  CONFIG SET maxmemory 512mb
docker exec jart-os-redis redis-cli -p 10301 \
  CONFIG SET maxmemory-policy allkeys-lru
```

### Pub/Sub Not Working

**Symptoms**: Messages not being received on subscribed channels.

```bash
# Check active channels
docker exec jart-os-redis redis-cli -p 10301 PUBSUB CHANNELS

# Check subscribers
docker exec jart-os-redis redis-cli -p 10301 PUBSUB NUMSUB jart-os:events:task

# Test pub/sub manually
# Terminal 1:
docker exec -it jart-os-redis redis-cli -p 10301
SUBSCRIBE jart-os:events:task

# Terminal 2:
docker exec -it jart-os-redis redis-cli -p 10301
PUBLISH jart-os:events:task '{"test": "hello"}'
```

---

## NATS Issues

### JetStream Not Starting

**Symptoms**: `JetStream not available` or stream creation fails.

```bash
# Check NATS health
curl http://localhost:10304/healthz

# Check JetStream status
curl http://localhost:10304/jsz

# Check NATS logs
docker logs jart-os-nats --tail 50

# Restart with explicit JetStream flag
docker compose -f services/TIER-03/docker-compose.yml down
docker compose -f services/TIER-03/docker-compose.yml up -d
```

### Connection Issues

**Symptoms**: `nats.errors.ConnectionClosedError` or `TimeoutError`.

```bash
# Test NATS connectivity
docker exec jart-os-nats nats pub test.subject "hello"
docker exec jart-os-nats nats sub test.subject

# Check connections
curl http://localhost:10304/connz

# Check subscriptions
curl http://localhost:10304/subsz

# Verify port accessibility
nc -zv localhost 10302
```

### Message Delivery Failures

**Symptoms**: Messages published but not received.

```bash
# Check active subscriptions
curl http://localhost:10304/subsz

# Verify subject matching
# Remember: * matches one token, > matches multiple
# jart-os.04.task.*.dispatch  — matches one word between task and dispatch
# jart-os.04.task.>            — matches everything after task

# Check JetStream consumers
curl http://localhost:10304/jsz?consumers=true
```

---

## Agent Issues

### Agent Won't Start

**Symptoms**: Agent container exits immediately or crashes on startup.

```bash
# Check agent logs
docker logs jart-os-<agent-name> --tail 100

# Common causes:
# 1. Missing environment variables
docker exec jart-os-<agent-name> env | grep -E "NATS|REDIS|LITELLM"

# 2. Python import errors
docker logs jart-os-<agent-name> 2>&1 | grep ImportError

# 3. Port already in use
lsof -i :10401
```

### NATS Disconnect During Runtime

**Symptoms**: Agent loses NATS connection, stops receiving messages.

```bash
# Check NATS connection from agent
docker exec jart-os-<agent-name> curl -s http://localhost:10304/connz

# Check agent health endpoint
curl http://localhost:10401/health

# Restart the agent
docker compose -f services/TIER-04/docker-compose.yml restart <agent-name>
```

### Redis Offline

**Symptoms**: Agent can't store/retrieve state.

```bash
# Check Redis connectivity from agent container
docker exec jart-os-<agent-name> python -c "
import redis
r = redis.Redis(host='jart-os-redis', port=6379)
print(r.ping())
"

# Verify Redis is running
docker compose ps redis
```

### Agent Stuck in Loop

**Symptoms**: Agent consuming high CPU, not making progress.

```bash
# Check agent metrics
curl http://localhost:10401/metrics

# Check recent logs
docker logs jart-os-<agent-name> --tail 50

# Check Redis for stuck locks
docker exec jart-os-redis redis-cli -p 10301 KEYS "jart-os:*:lock:*"

# Force-release stuck locks
docker exec jart-os-redis redis-cli -p 10301 DEL "jart-os:04:lock:task-001"
```

---

## Network Issues

### Tailscale Problems

**Symptoms**: Can't access services remotely via Tailscale.

```bash
# Check Tailscale status
tailscale status

# Get Tailscale IP
tailscale ip -4

# Verify connectivity
ping <tailscale-ip>
curl http://<tailscale-ip>:10702  # Grafana

# Restart Tailscale
sudo tailscale down
sudo tailscale up
```

### DNS Resolution Issues

**Symptoms**: Containers can't resolve each other by name.

```bash
# Test DNS from inside a container
docker exec jart-os-redis nslookup jart-os-nats
docker exec jart-os-redis nslookup jart-os-litellm

# Check Docker network
docker network inspect jart-os-net

# Recreate the network
docker compose down
docker network rm jart-os-net
docker compose up -d
```

### Firewall Blocking Ports

**Symptoms**: Can't connect to services from host or remote.

```bash
# macOS: Check firewall
/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Check if port is listening
lsof -i :10201
netstat -an | grep 10201

# Test connectivity
curl -v http://localhost:10201/health
```

---

## Performance Issues

### High CPU Usage

**Symptoms**: Docker Desktop consuming excessive CPU.

```bash
# Check per-container resource usage
docker stats --no-stream

# Identify the heavy container
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Limit CPU for a service (in docker-compose.yml)
deploy:
  resources:
    limits:
      cpus: "0.5"
```

### High Memory Usage

**Symptoms**: System running low on memory, containers being killed.

```bash
# Check memory per container
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}"

# Check Redis memory
docker exec jart-os-redis redis-cli -p 10301 INFO memory | grep used_memory_human

# Check Prometheus memory
docker exec jart-os-prometheus df -h /prometheus

# Add memory limits
deploy:
  resources:
    limits:
      memory: 512M
```

### Slow LLM Responses

**Symptoms**: Agent tasks taking too long, timeouts.

```bash
# Measure LLM response time
time curl -s -X POST http://localhost:10201/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "glm-5", "messages": [{"role": "user", "content": "test"}]}' \
  | jq '.usage'

# Try a faster model
curl -X POST http://localhost:10201/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "glm-4.7", "messages": [{"role": "user", "content": "test"}]}'

# Reduce max_tokens
# In agent code: call_llm(prompt="...", max_tokens=256)
```

---

## Git Issues

### Push Rejected

**Symptoms**: `! [rejected] main -> main (non-fast-forward)`.

```bash
# Pull and rebase
git pull --rebase origin main
git push origin main

# If rebase has conflicts
git status
# Edit conflicted files
git add -A
git rebase --continue
```

### Merge Conflicts

**Symptoms**: `CONFLICT (content): Merge conflict in file.py`.

```bash
# View conflicted files
git status

# Open each file and resolve markers:
# <<<<<<< HEAD
# your changes
# =======
# their changes
# >>>>>>> branch-name

# After resolving
git add -A
git commit -m "fix: resolve merge conflicts"
```

### Authentication Issues

**Symptoms**: `remote: Permission denied` or `Authentication failed`.

```bash
# Check GitHub CLI auth
gh auth status

# Re-authenticate
gh auth login

# Check SSH key
ssh -T git@github.com

# Use HTTPS with token
git remote set-url origin https://<token>@github.com/Ruben-Alvarez-Dev/Jart-OS.git
```

---

## Diagnostic Commands

### Full Health Check

```bash
#!/bin/bash
# scripts/health-check.sh — Run a comprehensive system health check

echo "=== Jart-OS Health Check ==="
echo ""

echo "📦 Docker Containers:"
docker compose ps
echo ""

echo "🔍 LiteLLM (port 10201):"
curl -s http://localhost:10201/health | jq . 2>/dev/null || echo "UNREACHABLE"
echo ""

echo "🔍 Redis (port 10301):"
docker exec jart-os-redis redis-cli -p 10301 PING 2>/dev/null || echo "UNREACHABLE"
echo ""

echo "🔍 NATS (port 10302):"
curl -s http://localhost:10304/healthz 2>/dev/null || echo "UNREACHABLE"
echo ""

echo "🔍 Prometheus (port 10901):"
curl -s http://localhost:10901/api/v1/query?query=up | jq . 2>/dev/null || echo "UNREACHABLE"
echo ""

echo "🔍 Grafana (port 10702):"
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:10702 2>/dev/null || echo "UNREACHABLE"
echo ""

echo "🔍 Mission Control (port 10701):"
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:10701 2>/dev/null || echo "UNREACHABLE"
echo ""

echo "📊 Resource Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
echo ""

echo "💾 Disk Usage:"
df -h | grep -E "Filesystem|/System/Volumes/Data|/$"
echo ""

echo "✅ Health check complete."
```

### Log Aggregation

```bash
# Collect all logs into a single file
echo "=== Jart-OS Log Dump $(date) ===" > jart-os-debug.log
echo "" >> jart-os-debug.log

for service in litellm redis nats prometheus grafana; do
    echo "=== $service ===" >> jart-os-debug.log
    docker logs jart-os-$service --tail 100 >> jart-os-debug.log 2>&1
    echo "" >> jart-os-debug.log
done

echo "Logs saved to jart-os-debug.log"
```

### Network Diagnostics

```bash
# Check Docker network
docker network inspect jart-os-net --format '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}'

# Test inter-container connectivity
docker exec jart-os-redis ping -c 3 jart-os-nats
docker exec jart-os-redis ping -c 3 jart-os-litellm

# Check port bindings
docker compose ps --format "table {{.Name}}\t{{.Ports}}"
```

---

## Recovery Procedures

### Full System Restart

```bash
# Graceful restart
./scripts/boot.sh stop
sleep 5
./scripts/boot.sh start
./scripts/boot.sh status
```

### Nuclear Reset

```bash
# WARNING: This removes all data

# 1. Stop everything
docker compose down -v

# 2. Clean up
docker system prune -f

# 3. Rebuild from scratch
docker compose up -d --build

# 4. Verify
./scripts/boot.sh status
```

### Data Recovery from Backup

```bash
# 1. Stop services
docker compose down

# 2. Restore volumes
tar -xzf jart-os-backup-YYYYMMDD.tar.gz -C /var/lib/docker/volumes/

# 3. Restart
docker compose up -d

# 4. Verify data integrity
docker exec jart-os-redis redis-cli -p 10301 DBSIZE
```

### Corrupted NATS JetStream

```bash
# 1. Stop NATS
docker compose stop nats

# 2. Remove JetStream data
docker volume rm jart-os_nats-data

# 3. Restart NATS
docker compose up -d nats

# 4. Verify JetStream is healthy
curl http://localhost:10304/jsz
```

### Redis Data Corruption

```bash
# 1. Flush Redis (WARNING: deletes all data)
docker exec jart-os-redis redis-cli -p 10301 FLUSHALL

# 2. Restart Redis
docker compose restart redis

# 3. Agents will repopulate state as they process new tasks
```

### Agent Recovery

```bash
# Restart a specific agent
docker compose restart <agent-name>

# Restart all agents
docker compose -f services/TIER-04/docker-compose.yml restart

# Force rebuild an agent
docker compose -f services/TIER-04/docker-compose.yml up -d --build --force-recreate <agent-name>
```
