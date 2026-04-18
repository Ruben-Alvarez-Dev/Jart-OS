# Jart-OS Entity Taxonomy

> **Status**: Stable  
> **Version**: 2.0.0  
> **Last updated**: 2026-04-18

This document defines the canonical classification system for ALL elements in the Jart-OS ecosystem.

---

## Naming Convention

```
{TYPE}-{compound-name}
```

| Component | Case | Description |
|-----------|------|-------------|
| `TYPE` | UPPERCASE | Entity type — what kind of thing it IS |
| `compound-name` | lowercase, hyphenated | Descriptive name — what it DOES, N parts |

**No suffixes.** The TYPE is the classification. The name describes function.

**Rationale**: Industry standard (npm, Docker Hub, PyPI, Go modules, Kubernetes) uses type-as-namespace + name-as-description. Context and metadata handle role disambiguation.

---

## 9 Canonical Entities

### Runtime — Things that RUN

| TYPE | Entity | Description | Example |
|------|--------|-------------|---------|
| `MCP-` | Model Context Protocol component | Server, lib, or bridge implementing the MCP protocol | `MCP-memory`, `MCP-search` |
| `AGENT-` | Autonomous Agent | Container-based process that performs tasks autonomously | `AGENT-director`, `AGENT-guardian` |
| `CLI-` | Command-Line Tool | Terminal utility for interacting with the system | `CLI-jart-os` |
| `PIPELINE-` | Workflow / Orchestration | Sequenced set of operations | `PIPELINE-deploy`, `PIPELINE-heal` |

### Meta — Things that CONFIGURE

| TYPE | Entity | Description | Example |
|------|--------|-------------|---------|
| `SKILL-` | Reusable Capability | Instruction set defining an agent capability | `SKILL-go-testing` |
| `HOOK-` | Lifecycle Trigger | Action that fires at a specific point in execution | `HOOK-pre-commit` |
| `RULE-` | Behavioral Constraint | Policy governing agent or system behavior | `RULE-no-secrets` |

### Structural — Things that ORGANIZE

| TYPE | Entity | Description | Example |
|------|--------|-------------|---------|
| `TEMPLATE-` | Scaffold / Generator | Project template that generates new entities | `TEMPLATE-mcp` |
| `SPEC-` | Formal Contract | Schema or specification governing entity behavior | `SPEC-agent-schema` |

---

## What is NOT an Entity

These are roles, relationships, or attributes — not independent entities:

| Concept | What it actually is | Why not an entity |
|---------|--------------------|-------------------|
| Tool | Part of an MCP (composition) | Tools live inside MCP servers; a tool is a function, not a deployable unit |
| Bridge | Role an MCP plays | A bridge IS an MCP that translates between protocols |
| Dashboard | MCP-server serving HTML | Mission Control is an MCP that happens to serve a web UI |
| Tier | Structural categorization | Tiers organize the architecture; they don't have independent lifecycles |
| Module | Part of agents/core/ (composition) | Modules are shared code imported by agents, not standalone elements |

---

## Template System

Every entity type has an associated template that ensures consistency.

### Directory Structure

```
templates/
├── mcp/
│   ├── VERSION           # Current template version (semver)
│   ├── CHANGELOG.md      # What changed in each version
│   ├── scaffold/         # The actual template files
│   │   ├── src/
│   │   ├── tests/
│   │   ├── README.md
│   │   └── .jart-os-manifest
│   └── schema.json       # What this template produces
├── agent/
│   ├── VERSION
│   ├── CHANGELOG.md
│   ├── scaffold/
│   └── schema.json
└── ... (one per entity type)
```

### Versioning

- **Git tags**: `template/{type}/v{semver}` (e.g., `template/mcp/v1.0.0`)
- **VERSION file**: Inside each template directory, tracks current version
- **History**: Preserved in git — old versions always accessible via tag checkout

### Maturity Channels

| Channel | Meaning | CLI flag |
|---------|---------|----------|
| `stable` | Validated and production-ready | Default (no flag needed) |
| `draft` | Work in progress, available for testing | `--channel draft` |
| `planned` | Spec only, not yet scaffoldable | Not accessible via CLI |

### CLI Resolution

```bash
CLI-jart-os scaffold mcp my-new-server                    # Latest stable
CLI-jart-os scaffold mcp my-new-server --version 1.2.0    # Specific version
CLI-jart-os scaffold mcp my-new-server --channel draft    # Latest draft
```

---

## Evolution

This taxonomy is designed to be **minimal but extensible**:

- New entities are added only when a genuinely new family of elements emerges
- The template system ensures each entity type follows the same interface
- The CLI validates against this taxonomy to prevent drift

### Change Process

1. Propose new entity in `SPEC-taxonomy-evolution`
2. Document with use cases and examples
3. Create template for the new entity type
4. Update this document and `schema.json`
5. Release via git tag

---

## Current Repo Mapping

| Repo | Entity | Notes |
|------|--------|-------|
| `Jart-OS` | — | Monorepo: agents, pipelines, core modules, docs |
| `MCP-memory` | MCP | Memory server (currently `MCP-memory-server`) |
| `MCP-search` | MCP | Search server (currently `MCP-search-server`) |
| `MCP-core` | MCP | Shared library (currently `MCP-core-lib`) |
| `MCP-blueprint` | MCP/TEMPLATE | Generator for new MCPs (currently `MCP-blueprint-template`) |

> **Note**: Repo renames to drop suffixes are planned but low priority.

---

## Mandatory Standards Compliance

ALL entities in Jart-OS must comply with the 3-industry-standards stack defined in [STANDARDS.md](STANDARDS.md):

1. **MCP Protocol** — Tool exposure (Anthropic / Linux Foundation)
2. **A2A Protocol** — Agent-to-Agent communication (Google / Linux Foundation)
3. **MCP Apps** — Interactive UI for tools (Anthropic)

No Jart-OS specific code without FULL standards compliance first. See [STANDARDS.md](STANDARDS.md) for the complete compliance checklist.
