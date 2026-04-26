# Metal vs Docker Boundary

## Principle

Jart-OS is split into two major zones:

1. the metal boundary
2. the containerized platform boundary

This is not an implementation detail. It is a core architectural rule.

## Metal boundary

The metal side is where host-coupled capabilities live.

Typical examples:
- local LLM engines
- local model runtimes
- host security services
- host monitoring services
- reverse proxy or border components tightly coupled to the machine

These services are placed near the host because they:
- depend on host resources directly
- should remain available even if platform containers fail
- often need privileged or low-level access
- form part of the platform’s operational foundation

## Docker boundary

Inside the main Jart-OS platform bubble live the services that benefit from container isolation and declarative orchestration.

Typical examples:
- gateways
- shared services
- agents
- frameworks
- processes
- interfaces
- knowledge services
- control services

These services are easier to:
- version
- isolate
- compose
- redeploy
- migrate

## Communication model

Metal and Docker layers communicate through explicit APIs.

This keeps the boundary clean:
- host engines expose services
- the platform consumes them
- coupling stays visible and intentional

## Architectural consequence

TIER-00 belongs to the metal side.

The remaining tiers form the structured platform space.

This makes Jart-OS installable across environments while preserving a stable conceptual model.
