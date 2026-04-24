# Jart-OS Photos Pipeline Dockerfile
# Spec: §18 "CEDE Photos: 1695, Vision Model OCR"
#       §12 "NATS subjects: jart-os.06.pipeline.photos.{command,events}"

FROM python:3.12-slim

WORKDIR /app

# Copy pipeline code and agent base
COPY pipelines/photos/ /app/
COPY agents/ /app/agents/

# Default: run photos pipeline
ENV AGENT_ROLE=photos
ENV AGENT_PORT=10602
ENV NATS_URL=nats://jart-os-nats:4222
ENV REDIS_URL=redis://jart-os-redis:6379
ENV LITELLM_URL=http://jart-os-litellm:4000
ENV LITELLM_KEY=${LITELLM_KEY:-}

CMD ["python", "extract.py"]
