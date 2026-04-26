# Core Principles

## P1 — Structure Before Scale
Jart-OS prioritizes clear architectural boundaries before accumulating features. Every component must know where its responsibility starts and ends.

## P2 — One System, Not Many Fragments
The goal is for the system to behave as a coherent operational whole. Services are not islands; they are part of a larger orchestration with defined protocols and hierarchies.

## P3 — Host-Aware by Design
We recognize that not everything can or should be inside Docker. Some capabilities (LLM engines, base security, hardware monitoring) belong to the host (Metal). The architecture must respect and explicitly manage this boundary.

## P4 — Self-Contained Services
Every service must be a deployable unit that owns its definition (Compose), configuration, data persistence, and operational context. Dependencies between services are declared, not improvised.

## P5 — Documentation Sync
A complex system without a narrative becomes unmanageable. Public documentation must explain the architecture clearly and truthfully, while the private workshop preserves deep reasoning and history.

## P6 — Public Canon, Private Workshop
We maintain a strict separation:
- The **Canon** (Jart-OS) is the public, sanitized truth.
- The **Workshop** (PROJECT-Jart-OS) is the private construction and archive space.

## P7 — English Everywhere
All technical documentation, service naming, variables, and repository structure in the canonical repo remain in English to ensure interoperability and professional standards.
