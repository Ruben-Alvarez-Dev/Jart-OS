# Repository Map

## Purpose

This file explains how the repository is organized and where to look first.

## Top-level files

- `README.md` — public entry point
- `VISION.md` — purpose and mission
- `ARCHITECTURE.md` — system-level overview
- `REPOSITORY-POLICY.md` — repository roles and truth flow
- `PUBLIC-DOCS-POLICY.md` — public documentation constraints

## Main directories

### `TIERS/`
The tiered service structure of the system.

Expected contents:
- `TIER-00-*`
- `TIER-01-*` through `TIER-09-*`
- self-contained service folders

### `agents/`
Agent runtime code, templates, and policies.

### `pipelines/`
Transformation and ingestion processes.

### `docs/`
Canonical documentation grouped by purpose:
- foundations
- architecture
- operations
- product

### `scripts/`
Operational scripts such as boot helpers and maintenance tooling.

## Tier folder pattern

Each service should follow a self-contained structure:

```text
TIER-XX-NAME/1XXYY-category-app/
├── docker-compose.yml
├── Dockerfile          # if needed
├── config/
├── data/
├── logs/
└── service.conf        # if registry-driven
```

## Documentation rule

If a document explains:
- purpose → put it in `docs/01-foundations`
- system structure → put it in `docs/02-architecture`
- execution or maintenance → put it in `docs/03-operations`
- use cases or roadmap → put it in `docs/04-product`

## Public boundary

This repository is the public-facing documentation and architectural canon for Jart-OS.

Private history, sensitive planning context, raw notes, and unpublished rationale should remain outside the public repository.
