#!/usr/bin/env bash
# Jart-OS boot manager — start/stop/status/logs/restart
set -euo pipefail

PROJECT="/Users/jarvis/Jart-OS"
cd "$PROJECT"

case "${1:-status}" in
  start|up)
    docker compose up -d
    echo ""
    docker compose ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    ;;
  stop|down)
    docker compose down
    echo "All services stopped"
    ;;
  restart)
    docker compose restart
    echo ""
    docker compose ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    ;;
  status|ps)
    echo "=== Jart-OS Services ==="
    echo ""
    docker compose ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "=== Health ==="
    echo -n "Redis:      "; docker exec Jart-OS-redis redis-cli ping 2>/dev/null || echo "DOWN"
    echo -n "NATS:       "; curl -sf http://localhost:10302/ >/dev/null 2>&1 && echo "UP" || echo "DOWN"
    echo -n "LiteLLM:    "; curl -sf http://localhost:10201/health >/dev/null 2>&1 && echo "UP" || echo "starting"
    echo -n "MC:         "; curl -sf -o /dev/null -w "%{http_code}" http://localhost:10701/ 2>/dev/null || echo "DOWN"
    echo -n "Grafana:    "; curl -sf -o /dev/null -w "%{http_code}" http://localhost:10702/ 2>/dev/null || echo "DOWN"
    echo -n "Prometheus: "; curl -sf -o /dev/null -w "%{http_code}" http://localhost:10901/-/healthy 2>/dev/null || echo "DOWN"
    ;;
  logs)
    SERVICE="${2:-}"
    if [ -n "$SERVICE" ]; then
      docker logs -f "Jart-OS-$SERVICE" 2>&1
    else
      docker compose logs --tail=50 -f 2>&1
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs [service]}"
    echo ""
    echo "Services: redis, nats, litellm, mc, grafana, prometheus"
    exit 1
    ;;
esac
