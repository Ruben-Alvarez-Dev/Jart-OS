# Contributing to Jart-OS

> Thank you for your interest in contributing! This guide covers everything you need to know.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Git Workflow](#git-workflow)
- [Commit Message Format](#commit-message-format)
- [Pull Request Process](#pull-request-process)
- [Branch Naming Convention](#branch-naming-convention)
- [Code Style](#code-style)
- [Definition of Done](#definition-of-done)
- [Issue Templates](#issue-templates)

---

## Code of Conduct

### Our Standards

- **Be respectful** — Treat everyone with dignity and professionalism
- **Be constructive** — Focus on solutions, not blame
- **Be inclusive** — Welcome newcomers and diverse perspectives
- **Be patient** — Not everyone has the same level of experience
- **Be collaborative** — Share knowledge and help others grow

### Unacceptable Behavior

- Harassment, discrimination, or offensive language
- Personal attacks or trolling
- Publishing others' private information
- Any conduct that would be inappropriate in a professional setting

### Enforcement

Report issues to the project maintainer via GitHub Issues or direct message.

---

## How to Contribute

### Quick Start

```bash
# 1. Fork the repository
gh repo fork Ruben-Alvarez-Dev/Jart-OS --clone

# 2. Create a feature branch
git checkout -b feature/my-contribution

# 3. Make your changes
# ... code ...

# 4. Run tests
pytest tests/ -v

# 5. Commit and push
git add -A
git commit -m "feat(scope): description of change"
git push -u origin feature/my-contribution

# 6. Create a Pull Request
gh pr create --title "feat(scope): description" --body "## Changes
- What changed
- Why it changed
- How to test it"
```

### Types of Contributions

| Type | Description | Example |
|------|-------------|---------|
| Bug fix | Fix an existing issue | `fix(redis): handle connection timeout` |
| Feature | Add new functionality | `feat(agents): add council voting` |
| Documentation | Improve docs | `docs(api): add NATS subject reference` |
| Refactor | Improve code quality | `refactor(base): simplify agent lifecycle` |
| Test | Add or improve tests | `test(e2e): add governance flow test` |
| Chore | Maintenance tasks | `chore(deps): update Docker images` |

---

## Git Workflow

Jart-OS uses **trunk-based development** with a protected `main` branch.

```
main (protected, requires PR)
  │
  ├── feature/new-agent
  │     └── commits
  │
  ├── fix/redis-reconnect
  │     └── commits
  │
  └── documentation/api-reference
        └── commits
```

### Rules

1. **Never push directly to `main`** — All changes go through PRs
2. **Keep branches short-lived** — Merge within 3 days
3. **Rebase before merging** — Keep history clean
4. **One concern per PR** — Don't mix features and fixes
5. **Squash merge** — One commit per PR on `main`

### Syncing Your Fork

```bash
# Add upstream remote (one-time)
git remote add upstream https://github.com/Ruben-Alvarez-Dev/Jart-OS.git

# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main
```

---

## Commit Message Format

Jart-OS follows [Conventional Commits](https://www.conventionalcommits.org/) v1.0.0.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(agents): add retry logic to NATS reconnection` |
| `fix` | Bug fix | `fix(redis): handle connection timeout gracefully` |
| `docs` | Documentation | `docs(api): add message envelope specification` |
| `refactor` | Code restructuring | `refactor(base): extract common agent lifecycle` |
| `test` | Tests | `test(e2e): add full pipeline integration test` |
| `chore` | Maintenance | `chore(deps): update LiteLLM to v1.40` |
| `ci` | CI/CD changes | `ci: add pytest to GitHub Actions` |
| `perf` | Performance | `perf(nats): batch message processing` |
| `style` | Formatting | `style: fix linting errors` |
| `build` | Build system | `build: optimize Docker layer caching` |

### Scopes

| Scope | Description |
|-------|-------------|
| `agents` | Agent framework and implementations |
| `base` | AgentBase class |
| `runtime` | Production runtime |
| `nats` | NATS messaging |
| `redis` | Redis state management |
| `litellm` | LLM proxy configuration |
| `policies` | Policy gates |
| `monitoring` | Prometheus, Grafana |
| `docker` | Docker Compose, Dockerfiles |
| `scripts` | Boot and utility scripts |
| `deps` | Dependencies |

### Examples

```bash
# Feature
git commit -m "feat(agents): add exponential backoff to LLM retries"

# Bug fix with breaking change
git commit -m "fix(runtime): correct NATS subject routing

BREAKING CHANGE: NATS subjects now use dot notation instead of dashes"

# Multiple paragraphs
git commit -m "feat(governance): implement council voting mechanism

- Add quorum-based voting
- Support REGULATORY, PEDAGOGICAL, TECHNICAL aspects
- Include timeout-based auto-resolution

Closes #42"
```

---

## Pull Request Process

### PR Template

Every PR should include:

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring

## Changes Made
- Change 1
- Change 2

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated (if applicable)
- [ ] No new warnings generated
```

### Review Process

1. **Automated checks** — Linting, tests, and build must pass
2. **Peer review** — At least one approval required
3. **DoD verification** — Reviewer checks Definition of Done
4. **Squash merge** — Maintainer squashes and merges

### Review Checklist (for Reviewers)

- [ ] Code is readable and well-documented
- [ ] Follows project conventions (naming, structure)
- [ ] No obvious bugs or security issues
- [ ] Tests cover the new/changed functionality
- [ ] No unnecessary complexity
- [ ] Error handling is appropriate
- [ ] Performance implications are acceptable

---

## Branch Naming Convention

| Pattern | Purpose | Example |
|---------|---------|---------|
| `feature/<description>` | New functionality | `feature/council-voting` |
| `fix/<description>` | Bug fixes | `fix/redis-timeout` |
| `documentation/<description>` | Documentation | `documentation/api-reference` |
| `refactor/<description>` | Code restructuring | `refactor/agent-lifecycle` |
| `test/<description>` | Test additions | `test/e2e-pipeline` |
| `chore/<description>` | Maintenance | `chore/update-deps` |

### Rules

- Use lowercase with hyphens
- Keep descriptions concise (2-4 words)
- Include issue number if applicable: `fix/redis-timeout-#42`

---

## Code Style

### Python (PEP 8)

```python
# Good
class MyAgent(AgentBase):
    """Agent that processes study tasks."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self.task_count = 0

    async def process_task(self, task_id: str, payload: dict) -> dict:
        """Process a single task and return the result."""
        result = await self.call_llm(
            prompt=payload.get("prompt", ""),
            model="glm-5",
            temperature=0.3,
        )
        self.task_count += 1
        return {"task_id": task_id, "result": result}


# Bad
class myAgent(AgentBase):
    def __init__(self,name,**kw):
        super().__init__(name=name,**kw)
        self.taskCount=0
    async def ProcessTask(self,task_id,p):
        r=await self.call_llm(prompt=p.get("prompt",""),model="glm-5",temperature=0.3)
        self.taskCount+=1
        return{"task_id":task_id,"result":r}
```

### Key Rules

- **Indentation**: 4 spaces (no tabs)
- **Line length**: 100 characters max
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Type hints**: Required for all function signatures
- **Docstrings**: Required for all public classes and methods
- **Imports**: Standard library → third-party → local, alphabetized within groups

### YAML (2-Space Indent)

```yaml
# Good
services:
  my-service:
    image: my-image:latest
    ports:
      - "10401:8080"
    environment:
      - KEY=value
    networks:
      - jart-os-net

# Bad
services:
    my-service:
      image: my-image:latest
      ports:
        - "10401:8080"
```

### Linting

```bash
# Python
ruff check agents/ tests/
ruff format agents/ tests/

# YAML (if yamllint installed)
yamllint services/
```

---

## Definition of Done

A task is considered **Done** when ALL of the following criteria are met:

### Code Quality

1. [ ] Code follows PEP 8 style guidelines
2. [ ] No linting errors or warnings
3. [ ] Type hints are present on all public functions
4. [ ] Docstrings are present on all public classes and methods
5. [ ] No commented-out code or debug statements

### Testing

6. [ ] Unit tests cover new/changed functionality
7. [ ] All tests pass (unit, integration, e2e)
8. [ ] Test coverage meets minimum threshold (80%)
9. [ ] Edge cases are tested

### Documentation

10. [ ] README updated (if applicable)
11. [ ] API documentation updated (if applicable)
12. [ ] Inline comments explain complex logic

### Review

13. [ ] Self-review completed
14. [ ] Peer review approved
15. [ ] No open issues or TODOs

---

## Issue Templates

### Bug Report

```markdown
## Bug Description
A clear description of the bug.

## Steps to Reproduce
1. Start services with `./scripts/boot.sh start`
2. Send a message to `jart-os.04.task.executor.dispatch`
3. Observe error in logs

## Expected Behavior
Task should be processed successfully.

## Actual Behavior
Agent crashes with `ConnectionError: NATS unavailable`.

## Environment
- OS: macOS 14.2
- Docker: 24.0.7
- Python: 3.12.1

## Logs
```
[paste relevant logs]
```

## Additional Context
Any other information that might help.
```

### Feature Request

```markdown
## Feature Description
A clear description of the proposed feature.

## Problem Statement
What problem does this feature solve?

## Proposed Solution
How should this feature work?

## Alternatives Considered
What other approaches were considered?

## Additional Context
Any mockups, references, or examples.
```
