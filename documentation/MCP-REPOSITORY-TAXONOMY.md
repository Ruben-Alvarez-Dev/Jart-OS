# Jart-OS MCP Repository Taxonomy

> **Status:** CANONICAL — Ratified 2026-04-18
> **Applies to:** Every repository in the Jart-OS MCP ecosystem
> **Enforcement:** No repository may exist without a valid category suffix

---

## 1. Naming Convention

### Format

```
MCP-{domain}[-{subdomain}]-{suffix}
```

| Segment | Rules | Example |
|---------|-------|---------|
| `MCP-` | Mandatory prefix. **UPPERCASE**. Identifies ecosystem membership. | `MCP-` |
| `{domain}` | **Lowercase**, hyphenated. Primary functional area. | `memory`, `search`, `infra`, `core` |
| `-{subdomain}` | Optional. Only when disambiguation is needed. Max 1 level. | `-governance`, `-gateway`, `-a2a` |
| `-{suffix}` | **Mandatory**. One of the 4 registered categories. **Lowercase**. | `-server`, `-lib`, `-template`, `-bridge` |

### Rules

1. **`MCP-` prefix is UPPERCASE.** Everything else is lowercase. No exceptions.
2. **Hyphens only.** No underscores, no dots, no spaces, no camelCase.
3. **Suffix is mandatory.** Every repo declares what it IS.
4. **Domain is singular.** `MCP-memory-server`, not `MCP-memories-server`.
5. **Compound domains allowed** (max 2 parts) when a single word doesn't suffice.
6. **No abbreviations.** `MCP-infrastructure-server`, not `MCP-infra-server` in the official repo name. Short aliases allowed in internal references.

---

## 2. Category Definitions

### Category: `-server`

**Definition:** Runtime MCP server. Exposes Tools, Resources, and/or Prompts via the MCP protocol (JSON-RPC 2.0 over stdio or HTTP). May serve as an agent backpack.

| Property | Value |
|----------|-------|
| Runtime | Yes — standalone process |
| MCP-compliant | Yes — implements JSON-RPC 2.0 |
| Backpack-eligible | Yes — can be assigned to an agent |
| Federation-aware | Yes — reports identity to governance |
| Has `.jart-os-manifest` | Yes |
| Has `src/`, `config/`, `scripts/` | Yes |
| Has `tests/` | Yes |

**Naming examples:**
```
MCP-memory-server           → Hierarchical memory (L0-L5)
MCP-search-server           → Unified search (11 providers)
MCP-infrastructure-server   → SSH, filesystem, Docker operations
MCP-governance-server       → Central audit, compliance, risk control
MCP-documents-server        → Document production pipeline
MCP-notifications-server    → Push alerts (Discord, email, etc.)
MCP-discord-server          → Discord bridge (if dedicated)
```

**Required structure:**
```
MCP-{domain}-server/
├── .gitignore
├── .jart-os-manifest
├── LICENSE
├── README.md
├── VERSION
├── bin/                # Self-contained binaries
├── config/             # .env.example, mcp.json
├── data/               # Persistent local state
├── docs/               # Specifications
│   └── JART-OS-CANON.md
├── scripts/            # install.sh, lifecycle scripts
├── src/                # Source code
│   ├── tools/          # MCP Tools
│   ├── resources/      # MCP Resources (optional)
│   ├── apps/           # MCP Apps UI (optional)
│   ├── protocol/       # A2A + MCP handshake logic
│   └── main.{py,ts}    # Entrypoint
├── skills/             # Agent instruction sets (optional)
└── tests/              # Laboratory + E2E tests
```

---

### Category: `-lib`

**Definition:** Shared code library. Importable by other repos. No standalone runtime. Contains reusable types, utilities, and framework code.

| Property | Value |
|----------|-------|
| Runtime | No — imported by others |
| MCP-compliant | Indirect — enables others to comply |
| Backpack-eligible | No — not a standalone MCP server |
| Has `.jart-os-manifest` | Yes |
| Has `src/` | Yes |
| Has `tests/` | Yes |

**Naming examples:**
```
MCP-core-lib              → UUID v7, tracing, enriched types, server factory
MCP-validators-lib        → Shared validation schemas
MCP-providers-lib         → Provider interface definitions (if extracted)
```

**Required structure:**
```
MCP-{domain}-lib/
├── .gitignore
├── .jart-os-manifest
├── LICENSE
├── README.md
├── VERSION
├── package.json          # or pyproject.toml
├── src/
│   └── index.{ts,py}     # Public API exports
├── tests/
└── tsconfig.json         # if TypeScript
```

---

### Category: `-template`

**Definition:** Scaffolding generator. Used to create new repositories. Contains canonical directory structures, boilerplate code, and install scripts. Not runtime code.

| Property | Value |
|----------|-------|
| Runtime | No — generates other repos |
| MCP-compliant | N/A — ensures generated repos comply |
| Has `.jart-os-manifest` | Yes |
| Has `scripts/` | Yes — generation scripts |

**Naming examples:**
```
MCP-blueprint-template      → Canonical Python MCP server template
MCP-blueprint-ts-template   → Canonical TypeScript MCP server template
MCP-blueprint-app-template  → MCP server template with Apps UI included
```

**Required structure:**
```
MCP-{domain}-template/
├── .gitignore
├── .jart-os-manifest
├── LICENSE
├── README.md
├── VERSION
├── docs/
│   └── JART-OS-CANON.md
├── scripts/
│   └── generate.sh        # Creates new repo from template
├── src/                   # Boilerplate source code
└── tests/                 # Template validation tests
```

---

### Category: `-bridge`

**Definition:** Protocol translator or proxy. Connects different systems or protocols. Has runtime but its primary purpose is translation/routing, not business logic.

| Property | Value |
|----------|-------|
| Runtime | Yes — standalone process |
| MCP-compliant | Yes — exposes MCP interface on at least one side |
| Backpack-eligible | No — infrastructure component, not agent tooling |
| Has `.jart-os-manifest` | Yes |
| Has `src/`, `config/`, `scripts/` | Yes |

**Naming examples:**
```
MCP-gateway-bridge         → HTTP ↔ stdio proxy (1MCP gateway)
MCP-a2a-bridge             → MCP ↔ A2A protocol translator
MCP-legacy-bridge          → Adapter for non-MCP systems
```

**Required structure:**
```
MCP-{domain}-bridge/
├── .gitignore
├── .jart-os-manifest
├── LICENSE
├── README.md
├── VERSION
├── config/
├── scripts/
├── src/
│   ├── protocol/          # Protocol translation logic
│   └── main.{py,ts}
└── tests/
```

---

## 3. Category Registry

The authoritative list of all categories. **No new category may be created without an amendment to this document.**

| Suffix | Category | Purpose | Backpack? | Runtime? |
|--------|----------|---------|:---------:|:--------:|
| `-server` | MCP Server | Exposes tools/resources/prompts | ✅ | ✅ |
| `-lib` | Shared Library | Reusable code, types, utilities | ❌ | ❌ |
| `-template` | Scaffolding | Generates new repos | ❌ | ❌ |
| `-bridge` | Protocol Bridge | Translates between systems | ❌ | ✅ |

**Total categories: 4.** No expansion without ratified amendment.

---

## 4. Migration Map (Current → Canonical)

| Current Name | Category | Canonical Name |
|---|---|---|
| `MCP-Memory-Server` | server | `MCP-memory-server` |
| `MCP-search-server` | server | `MCP-search-server` |
| `MCP-core` | lib | `MCP-core-lib` |
| `MCP-blueprint` | template | `MCP-blueprint-template` |
| `Jart-OS` | *(OS, not MCP)* | `Jart-OS` — unchanged |
| `JartOS` | *(archived)* | `JartOS` — archived, unchanged |

---

## 5. `.jart-os-manifest` Schema

Every repository MUST include a `.jart-os-manifest` with this structure:

```json
{
  "version": "x.y.z",
  "category": "server|lib|template|bridge",
  "stack": "python|typescript|go",
  "compliance": ["mcp", "a2a", "mcp-apps"],
  "depends": ["mcp-core-lib"]
}
```

The `category` field MUST match the repository's suffix.

---

## 6. Ecosystem Membership — The `jart-os` Topic Rule

A repository belongs to the Jart-OS MCP ecosystem **if and only if** it carries the GitHub topic `jart-os`.

### Rule

```
IF repo has topic "jart-os":
  → MUST follow naming convention (MCP-{domain}-{suffix})
  → MUST have .jart-os-manifest with category field
  → MUST have LICENSE
  → MUST have README.md
  → MUST mirror to Jart-OS GitHub account
  → MUST follow Jart-OS Canon

IF repo does NOT have topic "jart-os":
  → Not part of Jart-OS ecosystem
  → No rules apply
  → Personal/independent project
```

### Dual-Account Mirror

Every repo with the `jart-os` topic is maintained in **dual accounts**:
- `Ruben-Alvarez-Dev/{canonical-name}` — **source of truth** (primary)
- `Jart-OS/{canonical-name}` — **mirror** (auto-synced via GitHub Actions)

The mirror workflow (`.github/workflows/mirror-to-jart-os.yml`) is automatically created in every Jart-OS-tagged repo and triggers on every push to `main`.

---

## 7. Governance

This document is maintained in:
- `Jart-OS/documentation/MCP-REPOSITORY-TAXONOMY.md` (source of truth)
- Replicated to each MCP repo's `docs/JART-OS-CANON.md` as a section

**Amendment process:** Any new category requires:
1. Written proposal with rationale
2. Impact analysis on existing repos
3. Approval before any repo is created with the new category

---

*Last ratified: 2026-04-18*
*Next review: When the 10th MCP repository is created*
