# Architecture

## Definition

Jart-OS is an agentic operating system architecture.

It separates:
- host-level capabilities that belong close to the machine
- containerized platform services that belong inside the operational bubble

## Core structure

Jart-OS is organized as a tiered system.

- **TIER-00**: host boundary and metal-coupled services
- **TIER-01+**: containerized platform layers with specific responsibilities
- each service is self-contained
- each tier exists for a clear architectural reason

## Architectural principle

> Jart-OS is not a collection of containers.
> It is a layered system with explicit boundaries, responsibilities, and runtime relationships.

## Main capabilities

The architecture is designed to host:
- model gateways
- shared services
- agent runtimes
- workflow pipelines
- interfaces
- knowledge systems
- operational control layers

## Boundary model

The system is intentionally split into two zones:

### Metal boundary
Typical examples:
- local LLM engines
- model runtimes
- host security services
- host monitoring services
- machine-coupled proxy or border components

### Containerized platform boundary
Typical examples:
- gateways
- shared services
- agents
- frameworks
- processes
- dashboards
- control systems

These two layers communicate through explicit interfaces, usually APIs.

## Documentation map

- `README.md` explains the public entry point
- `VISION.md` explains why the system exists
- `REPOSITORY-POLICY.md` defines public, private, and implementation repositories
- `docs/` contains the structured foundation, architecture, operations, and product documentation
