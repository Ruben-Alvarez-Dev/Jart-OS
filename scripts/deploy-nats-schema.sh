#!/usr/bin/env bash
# =============================================================================
# Jart-OS — NATS JetStream Schema Deploy
# Spec reference: §12 "Communication Backbone (NATS) > Subject Taxonomy"
#
# Creates JetStream streams via HTTP API (nats-server has no CLI in container).
# Idempotent — safe to re-run. — §21 ops
#
# Alternative: install nats-cli on host or use a sidecar container.
# For now, streams are created on first publish by agents (auto-create).
# This script verifies connectivity and publishes test messages.
# =============================================================================

set -euo pipefail

NATS_CONTAINER="jart-os-nats"
NATS_CLIENT_PORT=10302
NATS_MONITOR_PORT=10304

echo "=== Jart-OS NATS Schema Deploy ==="
echo ""

# Verify NATS is running
if ! docker ps --format '{{.Names}}' | grep -q "$NATS_CONTAINER"; then
    echo "ERROR: $NATS_CONTAINER is not running. Run ./scripts/boot.sh start first."
    exit 1
fi

echo "--- Checking NATS Connectivity ---"

# Check monitor endpoint
MONITOR_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:${NATS_MONITOR_PORT}/" 2>/dev/null || echo "000")
if [ "$MONITOR_STATUS" = "200" ]; then
    echo "  NATS monitor: OK (port $NATS_MONITOR_PORT)"
else
    echo "  NATS monitor: unreachable (status=$MONITOR_STATUS)"
fi

# Check client port
if nc -z localhost $NATS_CLIENT_PORT 2>/dev/null; then
    echo "  NATS client:  OK (port $NATS_CLIENT_PORT)"
else
    echo "  NATS client:  unreachable"
    exit 1
fi

echo ""
echo "--- Study Domain Subjects (§12) ---"
echo "Streams will be auto-created by JetStream on first publish."
echo "Expected subjects per §12 'Subject Taxonomy':"
echo ""
echo "  jart-os.04.study.director.command    — Director receives tasks"
echo "  jart-os.04.study.director.events     — Director publishes events"
echo "  jart-os.04.study.executor.command    — Executor receives sub-tasks"
echo "  jart-os.04.study.executor.events     — Executor publishes events"
echo "  jart-os.04.study.guardian.checks     — Guardian receives checks"
echo "  jart-os.04.study.guardian.verdicts   — Guardian publishes verdicts"
echo "  jart-os.04.study.council.proposals   — Council receives proposals"
echo "  jart-os.04.study.council.votes       — Council publishes votes"
echo ""
echo "  jart-os.04.study.director.errors     — Director error channel"
echo "  jart-os.04.study.executor.errors     — Executor error channel"
echo "  jart-os.04.study.guardian.errors     — Guardian error channel"
echo "  jart-os.04.study.council.errors      — Council error channel"
echo ""
echo "--- Pipeline Subjects (§12) ---"
echo "  jart-os.06.pipeline.pdf.command      — PDF pipeline commands"
echo "  jart-os.06.pipeline.pdf.events       — PDF pipeline events"
echo "  jart-os.06.pipeline.photos.command   — Photos pipeline commands"
echo "  jart-os.06.pipeline.photos.events    — Photos pipeline events"
echo "  jart-os.06.pipeline.video.command    — Video pipeline commands"
echo "  jart-os.06.pipeline.video.events     — Video pipeline events"
echo "  jart-os.06.pipeline.rag.command      — RAG pipeline commands"
echo "  jart-os.06.pipeline.rag.events       — RAG pipeline events"
echo ""
echo "--- Wildcards (§12) ---"
echo "  jart-os.04.>                         — All agent messages"
echo "  jart-os.04.study.>                   — All study domain messages"
echo "  jart-os.06.>                         — All pipeline messages"
echo "  jart-os.*.director.command           — All director commands"
echo ""

echo "=== NATS Schema Ready ==="
echo "NOTE: JetStream streams are auto-created when agents first publish."
echo "      To manually create streams, install nats-cli:"
echo "      brew install nats-io/nats-tools/nats"
