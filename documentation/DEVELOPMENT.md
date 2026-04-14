# Development Guide

> Everything you need to set up, develop, and debug Jart-OS locally.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Development Workflow](#development-workflow)
- [Toolchain](#toolchain)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Local Development Without Docker](#local-development-without-docker)
- [Debugging Tips](#debugging-tips)

---

## Prerequisites

| Tool | Minimum Version | Purpose |
|------|----------------|---------|
| Docker Desktop | 24.0+ | Container runtime |
| Docker Compose | v2.20+ | Multi-service orchestration |
| Python | 3.10+ | Agent runtime |
| Git | 2.40+ | Version control |
| GitHub CLI (`gh`) | 2.40+ | PR/issue management |
| curl | any | Health checks and API testing |

### macOS Setup (Recommended)

```bash
# Install Homebrew (if not present)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install all prerequisites
brew install --cask docker
brew install python@3.12 git gh

# Verify installations
docker --version
python3 --version
git --version
gh --version
```

### Verify Docker Resources

Jart-OS runs 6+ containers simultaneously. Ensure Docker Desktop has:

- **Memory**: ≥ 4 GB (Preferences → Resources → Memory)
- **CPUs**: ≥ 2 cores
- **Disk**: ≥ 10 GB free

---

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Ruben-Alvarez-Dev/Jart-OS.git
cd Jart-OS
```

### 2. Configure Environment

```bash
# Copy the example env file
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# LLM Configuration
LITELLM_URL=http://localhost:10201
DEFAULT_MODEL=glm-5

# Redis
REDIS_URL=redis://localhost:10301/0

# NATS
NATS_URL=nats://localhost:10302

# Discord Notifications (optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# GitHub
GITHUB_TOKEN=ghp_...

# Logging
LOG_LEVEL=INFO
```

### 3. First Boot

```bash
# Start all services
./scripts/boot.sh start

# Verify everything is running
./scripts/boot.sh status
```

### 4. Verify Services

```bash
# LiteLLM health
curl http://localhost:10201/health

# Redis ping
docker exec jart-os-redis redis-cli -p 10301 PING

# NATS health
curl http://localhost:10302/healthz

# Prometheus targets
curl http://localhost:10901/api/v1/targets
```

---

## Development Workflow

Jart-OS follows a **trunk-based development** model with short-lived feature branches.

```
main (protected)
  │
  ├── feature/add-new-agent      ← your branch
  │     │
  │     └── commits (conventional)
  │
  └── fix/redis-reconnect
        │
        └── commits (conventional)
```

### Step-by-Step

```bash
# 1. Sync with main
git checkout main
git pull origin main

# 2. Create a feature branch
git checkout -b feature/my-feature

# 3. Develop (code, test, repeat)
# ... make changes ...

# 4. Run tests locally
pytest tests/ -v

# 5. Commit with conventional format
git add -A
git commit -m "feat(agents): add retry logic to NATS reconnection"

# 6. Push and create PR
git push -u origin feature/my-feature
gh pr create --title "feat(agents): add retry logic to NATS reconnection" \
             --body "## Changes
- Added exponential backoff to NATS reconnection
- Unit tests for retry scenarios

## Testing
- [x] Unit tests pass
- [x] Integration tests pass
- [x] Manual verification"

# 7. After review and approval, merge via GitHub
gh pr merge --squash
```

### Branch Naming Convention

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feature/` | New functionality | `feature/council-voting` |
| `fix/` | Bug fixes | `fix/redis-timeout` |
| `documentation/` | Documentation | `documentation/api-reference` |
| `refactor/` | Code restructuring | `refactor/agent-base` |
| `test/` | Test additions | `test/e2e-pipeline` |
| `chore/` | Maintenance | `chore/update-deps` |

---

## Toolchain

### Recommended IDE: VS Code

```bash
# Install VS Code
brew install --cask visual-studio-code
```

### Essential Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "redhat.vscode-yaml",
    "docker.docker",
    "ms-azuretools.vscode-docker",
    "GitHub.vscode-pull-request-github",
    "charliermarsh.ruff",
    "ms-python.pytest"
  ]
}
```

### Linters and Formatters

```bash
# Install Python tools
pip install ruff pytest pytest-asyncio pytest-cov

# Run linter
ruff check agents/ tests/

# Run formatter
ruff format agents/ tests/

# Run type checking (optional)
pip install mypy
mypy agents/ --ignore-missing-imports
```

### Pre-commit Hooks (Recommended)

```bash
pip install pre-commit
pre-commit install
```

---

## Project Structure

```
Jart-OS/
├── agents/                     # Agent framework
│   ├── core/
│   │   └── base.py            # AgentBase abstract class
│   ├── runtime/
│   │   └── main.py            # Production runtime
│   ├── policies/
│   │   ├── spec-gate.yaml     # Pre-execution policy gate
│   │   └── quality-gate.yaml  # Post-execution policy gate
│   └── tiers/
│       └── TIER-04/           # Agent implementations
│           ├── director/
│           ├── executor/
│           ├── guardian/
│           └── council/
├── control/
│   └── mission-plan.json      # System configuration
├── documentation/             # Technical documentation (canonical)
├── scripts/
│   └── boot.sh               # Start/stop/restart/status/logs
├── TIERS/                     # 10-tier self-contained services
│   ├── TIER-00-METAL/         # Bare metal host
│   ├── TIER-01-SECURITY/      # Security layer
│   ├── TIER-02-GATEWAY/       # LLM gateway (LiteLLM)
│   ├── TIER-03-SERVICES/      # Messaging (Redis, NATS)
│   ├── TIER-04-AGENTS/        # Agent runtime
│   ├── TIER-05-FRAMEWORKS/    # Agent frameworks (Hermes)
│   ├── TIER-06-PROCESSES/     # Data pipelines
│   ├── TIER-07-INTERFACES/    # Dashboards (Mission Control, Grafana)
│   ├── TIER-08-KNOWLEDGE/     # RAG systems
│   └── TIER-09-CONTROL/       # Monitoring (Prometheus)
├── tests/
│   └── test_e2e.py           # End-to-end tests
├── docker-compose.yml         # Root compose (includes all tiers)
├── .env                       # Environment configuration
└── README.md
```

### Tier Architecture

Each tier is self-contained with its own `docker-compose.yml`:

| Tier | Purpose | Services | Ports |
|------|---------|----------|-------|
| TIER-02 | LLM Gateway | LiteLLM | 10201 |
| TIER-03 | Services | Redis, NATS | 10301–10304 |
| TIER-07 | Interfaces | Mission Control, Grafana | 10701–10702 |
| TIER-09 | Control | Prometheus | 10901 |

**Port Convention**: `1XXYY` where `XX` = tier number, `YY` = service sequence.

---

## Environment Variables

### Core Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LITELLM_URL` | Yes | `http://localhost:10201` | LiteLLM proxy endpoint |
| `DEFAULT_MODEL` | No | `glm-5` | Default LLM model |
| `REDIS_URL` | Yes | `redis://localhost:10301/0` | Redis connection URL |
| `NATS_URL` | Yes | `nats://localhost:10302` | NATS server URL |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `ENVIRONMENT` | No | `development` | Runtime environment (development, staging, production) |

### Agent Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGENT_NAME` | Yes | — | Unique agent identifier |
| `AGENT_ROLE` | Yes | — | Role: director, executor, guardian, council |
| `AGENT_TIER` | Yes | `04` | Tier number |
| `AGENT_PORT` | No | `10400` | HTTP server port |

### Notification Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_WEBHOOK_URL` | No | — | Discord webhook for notifications |
| `GITHUB_TOKEN` | No | — | GitHub API token |

### LiteLLM Model Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LITELLM_MASTER_KEY` | No | — | API key for LiteLLM proxy |
| `GLM_API_KEY` | No | — | API key for GLM models |
| `LOCAL_MODEL_PATH` | No | — | Path to local model weights |

---

## Local Development Without Docker

For rapid iteration on agent code, you can run agents natively while connecting to containerized services.

### 1. Start Infrastructure Only

```bash
# Start just Redis, NATS, and LiteLLM
docker compose -f services/TIER-01/docker-compose.yml up -d
docker compose -f services/TIER-03/docker-compose.yml up -d
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Set Environment Variables

```bash
export LITELLM_URL=http://localhost:10201
export REDIS_URL=redis://localhost:10301/0
export NATS_URL=nats://localhost:10302
export AGENT_NAME=dev-agent
export AGENT_ROLE=executor
export LOG_LEVEL=DEBUG
```

### 4. Run Agent Directly

```bash
python -m agents.runtime.main \
  --name dev-agent \
  --role executor \
  --tier 04
```

### 5. Run Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_e2e.py -v

# With coverage
pytest tests/ -v --cov=agents --cov-report=html
```

---

## Debugging Tips

### Docker Logs

```bash
# All services
./scripts/boot.sh logs

# Specific service
docker logs jart-os-litellm -f
docker logs jart-os-redis -f
docker logs jart-os-nats -f

# Last 100 lines
docker logs jart-os-litellm --tail 100
```

### Redis CLI

```bash
# Connect to Redis
docker exec -it jart-os-redis redis-cli -p 10301

# Useful commands inside redis-cli
KEYS jart-os:*          # List all Jart-OS keys
GET jart-os:agent:state # Get agent state
PUBSUB CHANNELS         # List active channels
INFO memory             # Memory usage
```

### NATS Monitoring

```bash
# NATS server info
curl http://localhost:10302/healthz

# JetStream info
curl http://localhost:10302/jsz

# Connection details
curl http://localhost:10302/connz

# Subscription details
curl http://localhost:10302/subsz

# Account info
curl http://localhost:10302/accountz
```

### LiteLLM Debugging

```bash
# Health check
curl http://localhost:10201/health

# List available models
curl http://localhost:10201/v1/models

# Test a completion
curl -X POST http://localhost:10201/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-5",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Prometheus Queries

```bash
# Check targets
curl http://localhost:10901/api/v1/targets

# Query metrics
curl 'http://localhost:10901/api/v1/query?query=up'

# Agent-specific metrics
curl 'http://localhost:10901/api/v1/query?query=jart_os_agent_tasks_total'
```

### Network Debugging

```bash
# Check Docker network
docker network inspect jart-os-net

# DNS resolution inside containers
docker exec jart-os-redis nslookup jart-os-nats

# Port conflicts
lsof -i :10201  # LiteLLM
lsof -i :10301  # Redis
lsof -i :10302  # NATS
```

### Log Aggregation

```bash
# All container logs with timestamps
docker compose logs --timestamps --tail 50

# Filter by service
docker compose logs litellm --since 30m

# Export logs to file
docker compose logs > debug-logs.txt 2>&1
```
