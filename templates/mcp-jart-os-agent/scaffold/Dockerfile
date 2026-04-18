# ---- Stage 1: Build ----
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Stage 2: Runtime ----
FROM python:3.12-slim

LABEL org.jart-os.tier="4"
LABEL org.jart-os.domain="agents"
LABEL org.jart-os.role="backpack"
LABEL org.jart-os.function="{function}"

WORKDIR /app

# Copy installed dependencies
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ src/
COPY config/.env.example config/.env.example
COPY policies/ policies/

# Non-root user for security
RUN useradd -m -u 1000 jart-os && chown -R jart-os:jart-os /app
USER jart-os

# Default: stdio transport (MCP standard)
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=0
ENV MCP_HOST=0.0.0.0
ENV A2A_ENABLED=false
ENV NATS_URL=nats://nats:4222
ENV REDIS_URL=redis://redis:6379

# Health check (only useful in HTTP mode)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${HEALTH_PORT:-9090}/health')" || exit 1

ENTRYPOINT ["python", "-m", "src.main"]
