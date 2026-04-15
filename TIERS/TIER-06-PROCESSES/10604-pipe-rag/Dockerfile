# Jart-OS RAG Pipeline Dockerfile
# Spec: §24 D4 "RAG → LlamaIndex + Qdrant"
#       §13 "RAG → Qdrant 'opo' collection"
#       §12 "NATS subjects: jart-os.06.pipeline.rag.{command,events,query}"

FROM python:3.12-slim

WORKDIR /app

# Install LlamaIndex + Qdrant client
RUN pip install --no-cache-dir llama-index qdrant-client

# Copy pipeline code and agent base
COPY pipelines/rag/ /app/
COPY agents/ /app/agents/

# Default: run RAG pipeline
ENV AGENT_ROLE=rag
ENV AGENT_PORT=10604
ENV NATS_URL=nats://jart-os-nats:4222
ENV REDIS_URL=redis://jart-os-redis:6379
ENV LITELLM_URL=http://jart-os-litellm:4000
ENV LITELLM_KEY=${LITELLM_KEY:-REDACTED_LITELLM_MASTER_KEY}
ENV QDRANT_URL=http://localhost:6333
ENV EMBEDDING_MODEL=${EMBEDDING_MODEL:-text-embedding-ada-002}

CMD ["python", "index.py"]
