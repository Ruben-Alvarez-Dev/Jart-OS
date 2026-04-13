# Jart-OS Agent Protocol

## MANDATORY — Read before working on Jart-OS

Every AI agent (LobeChat, OpenCode, Claude Code, Maestro, AIDER, etc.) MUST follow these rules.

### Step 1: Read the Law

```
Read: /Users/jarvis/Jart-OS/docs/JARTOS-CANONICAL-SPEC.md
```

This is the single source of truth. All naming, ports, tiers, and conventions are defined there.

### Step 2: Check the Board

```
Read: /Users/jarvis/Jart-OS/TASKBOARD.md
```

See what others are doing. Find your task. Do not duplicate work.

### Step 3: Lock Before Edit

```bash
# Before editing ANY file
echo "YOUR_NAME | $(date -u +%Y-%m-%dT%H:%M) | What you are doing" \
  > /Users/jarvis/Jart-OS/.agent-lock/$(echo FILEPATH | tr / -).lock

# When done
rm /Users/jarvis/Jart-OS/.agent-lock/$(echo FILEPATH | tr / -).lock
```

### Step 4: Update the Board

After completing work, update TASKBOARD.md with your progress.

### Conventions

| Rule | Value |
|------|-------|
| Project root | `/Users/jarvis/Jart-OS/` |
| Brand name | `jart-os` (lowercase), `Jart-OS` (title) |
| Docker project | `jart-os` |
| Containers | `jart-os-<name>` |
| Network | `jart-os-net` |
| NATS subjects | `jart-os.<tier>.<domain>.<role>.<action>` |
| Port format | `1XXYY` (XX=tier, YY=sequence) |
| Agent messaging | NATS JetStream :10302 |
| State/cache | Redis :10301 |
| LLM gateway | LiteLLM :10201 (key: sk-jart-os2026) |
| Language | English for code/structure, Spanish OK in docs |
| File writes | Use `sudo` (agent user = simba, owner = jarvis) |

### Available Models (via LiteLLM :10201)

| Model | Use for |
|-------|---------|
| glm-5 | Complex reasoning, specs, architecture |
| glm-4.7 | Execution, code generation |
| phi3-local | Quick validation, offline fallback |

### Directory Structure

```
TIER-XX-NAME/1XXYY-category-appname/
├── docker-compose.yml
├── Dockerfile
├── config/
├── data/
├── db/
├── engine/
└── logs/
```

### Key Files

| File | Purpose |
|------|---------|
| docs/JARTOS-CANONICAL-SPEC.md | THE law (1100+ lines) |
| docs/STATUS-AND-PROGRESS.md | What works, what is missing |
| docs/AGENT_PROTOCOL.md | This file — how to work here |
| TASKBOARD.md | Who does what |
| .agent-lock/ | Conflict prevention |
| agents/policies/spec-gate.yaml | Pre-execution validation rules |
| agents/policies/quality-gate.yaml | Post-execution quality checks |

### Communication

- **NATS** (`jart-os.04.*`) for inter-agent runtime messaging
- **Discord webhook** for notifications (configure later)
- **TASKBOARD.md** for async coordination between coding agents
- **Git commits** for code changes
