# Repository Policy

## Repository roles

### `Jart-OS`
This is the public canonical repository.

Its purpose is to publish:
- the clean architectural definition of Jart-OS
- stable public documentation
- sanitized technical structure
- reusable patterns and operational conventions

### `PROJECT-Jart-OS`
This is the private design and editorial workspace.

Its purpose is to hold:
- historical context
- raw architecture thinking
- documentation recovery work
- sensitive notes
- intermediate drafts
- restructuring plans

It is the workshop, not the public artifact.

### `Jart-OS-*`
These names identify concrete implementations, not the canon.

Examples:
- `Jart-OS-Macbook-Pro`
- `Jart-OS-Mac-Mini`
- `Jart-OS-VPS-IONOS`

Their purpose is to represent environment-specific deployment state and real infrastructure adaptations.

## Flow of truth

The official flow is:

`PROJECT-Jart-OS` → `Jart-OS` → `Jart-OS-* implementations`

Meaning:
1. ideas are explored privately
2. public-safe material is distilled into the canonical repository
3. implementations consume or adapt the canon

## Source of truth rule

- **Public source of truth:** `Jart-OS`
- **Private source of exploration:** `PROJECT-Jart-OS`
- **Operational source of runtime reality:** each `Jart-OS-*` implementation

No repository should try to be all three at once.
