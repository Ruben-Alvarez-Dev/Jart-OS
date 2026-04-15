# Changelog

All notable changes to Jart-OS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.1.0] - 2025-04-15

### Security

- **TIER-01 Security Hardening — Complete audit and remediation**
  - Bound 10 internal service ports to 127.0.0.1 (Redis :10301, NATS :10302-04, LiteLLM :10201, Prometheus :10901, Agents :10401-04, Pipes :10601-04)
  - Added requirepass authentication to Redis via REDIS_PASSWORD env variable
  - Added authorization token to NATS via NATS_TOKEN env variable
  - Enforced LiteLLM master_key validation via LITELLM_MASTER_KEY env variable
  - Prometheus metrics endpoint bound to localhost only
  - User-facing services (Mission Control :10701, Grafana :10702, Study Domain :10500) kept on 0.0.0.0 for Tailscale remote access
  - All agent services updated with authenticated REDIS_URL and NATS_URL connection strings
  - Verified macOS Application Firewall active and Grafana authentication enabled

### Fixed

- Redis crash loop caused by disk full (92% -> 20% after docker builder prune freed 30GB)
- Redis crash loop caused by stale dump.rdb created without password after requirepass added
- Redis healthcheck failure - moved password to environment: for healthcheck auth
- NATS FTL crash - removed stale data/jetstream/ directory
- Prometheus crash loop - removed stale queries.active lock file
- Grafana/Prometheus data directory permissions - chmod 777 for Docker Desktop macOS bind-mount compatibility
- .git/index ownership - changed from root back to jarvis:staff

### Added

- Agent compose files for Director (:10401), Executor (:10402), Guardian (:10403), Council (:10404)
- Processing pipes: PDF (:10601), Photos (:10602), Video (:10603), RAG (:10604)
- Study Domain service (:10500) for oposiciones exam preparation
- LACP v0.10.0 framework integration
- Pipeline scripts for PDF extraction and RAG indexing
- NATS schema deployment script
- Triunit flow integration test
- Phase 1 verification documentation
- Mission Control Dockerfile and API server
- Enhanced AgentBase class with health reporting and auth URL support
- Improved agent runtime with graceful shutdown
- Stricter quality-gate and spec-gate policies

### Changed

- Agent Dockerfile: multi-stage build with pinned Python 3.12-slim
- docker-compose.yml root: added security notice

## [5.0.0] - 2025-04-13

### Added

- Initial Jart-OS v5.0 project scaffold
- Complete English translation and documentation
- Comprehensive technical documentation
- Generalized domain terminology from Spanish to English
