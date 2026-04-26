# What Jart-OS Is

## Brief Definition

Jart-OS is a tiered agentic systems architecture organized by layers and responsibilities.

It serves to coherently structure:
- model access
- gateways
- shared services
- agent runtimes
- ingestion and transformation processes
- operational interfaces
- memory and knowledge systems
- observability and control

## What It Is Not

Jart-OS is not just Docker.

Docker is one of the platform's execution mechanisms, but it does not define the system by itself.

Jart-OS is also not just an agent project.

Agents are a capability within the system, not the entire system.

And Jart-OS should not be presented as a specific installation, because the canon is not a particular machine: it is the structural definition that different implementations then adopt.

## How It Should Be Understood

The best way to understand Jart-OS is as an architecture with three levels of reality:

1. **the workshop** — where ideas are refined and prepared
2. **the canon** — where the clean system definition is published
3. **implementations** — where the system is embodied on specific machines

## Primary Boundary

The system's foundational boundary separates:

### Metal Side
Capabilities close to the host:
- LLM engines
- model runtimes
- host-level security
- host monitoring

### Platform Side
Capabilities inside the operational bubble:
- gateways
- shared services
- agents
- frameworks
- workflows
- interfaces
- control planes

Both sides must communicate through explicit interfaces, usually APIs.

## Why This Definition Matters

This definition avoids three common errors:

1. believing the system is just a collection of services
2. believing everything must live inside Docker
3. believing a specific implementation equals the canon
