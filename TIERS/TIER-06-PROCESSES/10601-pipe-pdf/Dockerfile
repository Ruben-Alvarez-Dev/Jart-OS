# Jart-OS PDF Pipeline Dockerfile
# Spec: §18 "BLOCK 1: CONTENT PIPELINE", §20 "PyMuPDF / Vision API"
#       §12 "NATS subjects: jart-os.06.pipeline.pdf.{command,events}"

FROM python:3.12-slim

WORKDIR /app

# Install PyMuPDF + requests
RUN pip install --no-cache-dir pymupdf requests

# Copy pipeline code and agent base
COPY pipelines/pdf/ /app/
COPY agents/ /app/agents/

# Default: run PDF pipeline
ENV AGENT_ROLE=pdf
ENV AGENT_PORT=10601
ENV NATS_URL=nats://jart-os-nats:4222
ENV REDIS_URL=redis://jart-os-redis:6379
ENV LITELLM_URL=http://jart-os-litellm:4000
ENV LITELLM_KEY=${LITELLM_KEY:-}

CMD ["python", "extract.py"]
