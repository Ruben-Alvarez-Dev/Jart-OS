# Jart-OS Video Pipeline Dockerfile
# Spec: §18 "Videos: 18, ffmpeg + Whisper large-v3"
#       §12 "NATS subjects: jart-os.06.pipeline.video.{command,events}"

FROM python:3.12-slim

WORKDIR /app

# Install ffmpeg + Whisper
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg && \
    python3 && \
    pip install --no-cache-dir openai-whisper

# Copy pipeline code and agent base
COPY pipelines/video/ /app/
COPY agents/ /app/agents/

# Default: run video pipeline
ENV AGENT_ROLE=video
ENV AGENT_PORT=10603
ENV NATS_URL=nats://jart-os-nats:4222
ENV REDIS_URL=redis://jart-os-redis:6379
ENV LITELLM_URL=http://jart-os-litellm:4000
ENV LITELLM_KEY=${LITELLM_KEY:-REDACTED_LITELLM_MASTER_KEY}

CMD ["python", "transcribe.py"]
