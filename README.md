# Jart-OS

**Jart-OS** is an agentic operating system architecture for running AI agents, workflows, infrastructure services, memory systems, and operational interfaces in a structured, tiered environment.

It is designed to separate:
- **host-level capabilities** such as model engines, security, and monitoring
- **containerized platform services** such as gateways, agents, workflows, interfaces, and control systems

## What Jart-OS is

Jart-OS is not a single application.  
It is a **layered system architecture** for building and operating agent-based platforms with:

- explicit service boundaries
- tier-based responsibility separation
- self-contained deployable units
- operational observability
- controlled interfaces between host services and containerized services

## High-level architecture

- **Metal boundary**: LLM engines, host security, host monitoring
- **Gateway layer**: API and model routing
- **Service layer**: messaging, cache, core shared services
- **Agent layer**: orchestrators, executors, validators
- **Process layer**: ingestion and transformation pipelines
- **Interface layer**: dashboards and operational UIs
- **Knowledge layer**: memory, RAG, semantic stores
- **Control layer**: metrics, health, operational supervision

## Repository entry points

- `VISION.md` — why Jart-OS exists
- `ARCHITECTURE.md` — system structure and tier model
- `REPOSITORY-POLICY.md` — repository roles and truth flow
- `docs/` — detailed technical and operational documentation

## Documentation policy

This public repository documents architecture, operational structure, tier model, and generic use cases. It does **not** document personal contexts or sensitive deployment history.
