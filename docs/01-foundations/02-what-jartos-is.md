# What Jart-OS Is

## Definition

Jart-OS is a tiered agentic systems architecture.

It provides a way to organize:
- model access
- gateways
- services
- agents
- workflows
- interfaces
- knowledge systems
- operational control

## Not just Docker

Jart-OS is not defined by Docker.

Docker is one execution mechanism inside the platform boundary.

The real system is defined by:
- tiers
- service declarations
- responsibilities
- boundaries
- runtime relationships

## Not just agents

Jart-OS is also not just an agent project.

Agents are one subsystem inside a larger architecture that also includes:
- gateways
- shared services
- ingestion processes
- observability
- host-integrated engines
- operational interfaces

## Host and platform boundary

Jart-OS distinguishes between:

### Host-level services
These stay close to the operating system:
- LLM engines
- model runtimes
- host monitoring
- host-coupled security services

### Platform services
These run inside the main Jart-OS containerized environment:
- gateways
- agents
- workflows
- dashboards
- control planes
- data services

They communicate through explicit interfaces, usually APIs.

## Why this matters

This model keeps the system:
- easier to reason about
- safer to operate
- easier to document
- easier to migrate between machines
