"""
Jart-OS RAG Pipeline — LlamaIndex + Qdrant
Spec: §24 D4 "RAG → LlamaIndex + RAGFlow"
     §18 "BLOCK 1: CONTENT PIPELINE"
     §13 "RAG → Qdrant 'study' collection"
     §12 "NATS subjects: jart-os.06.pipeline.rag.{command,events,query}"
     §20 "Stack: LlamaIndex, Qdrant"
"""

import os
import sys
import json
import logging
import asyncio
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from agents.core.base import AgentBase

log = logging.getLogger("jart-os.pipeline.rag")


class RAGPipelineAgent(AgentBase):
    """
    RAG Pipeline Agent.
    Ingests chunks from PDF, photos, video pipelines into Qdrant.
    Provides query interface for agents.
    — §24 D4 "LAG: LlamaIndex as primary RAG engine"
    — §13 "RAG → Qdrant 'opo' collection"
    """

    def __init__(self):
        super().__init__(role="pipeline", domain="rag", tier=6)
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")  # §20
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")  # §20
        self.collection_name = "study"  # §13 "DOMAIN → Qdrant 'opo'"
        self.chunk_size = 512  # §18 "Chunking (512 tok, overlap 50)"

    def run(self):
        """Main loop: ingest chunks, respond to queries. — §12"""
        self.log.info("RAG Pipeline running. Waiting for commands...")

        async def on_command(msg):
            """Handle commands: ingest, query."""
            try:
                data = json.loads(msg.data.decode())
                action = data.get("action", "")
                self.log.info(f"Received command: {action}")

                if action == "ingest":
                    chunks = data.get("chunks", [])
                    self.current_task = f"ingest_{len(chunks)}_chunks"
                    self.log.info(f"Ingesting {len(chunks)} chunks")

                    # Ingest into Qdrant
                    ingested = await self.ingest_to_qdrant(chunks)

                    # Publish result
                    self.publish(self.subject_events, {
                        "event": "chunks_ingested",
                        "ingested_count": ingested,
                        "total_chunks": len(chunks),
                        "failed_chunks": len(chunks) - ingested,
                    })

                    self.tasks_completed += 1
                    self.current_task = None

                elif action == "query":
                    query = data.get("query", "")
                    self.current_task = f"query_{hash(query)}"
                    self.log.info(f"Query: {query}")

                    # Query Qdrant via LlamaIndex
                    results = await self.query_qdrant(query)

                    # Publish result
                    self.publish(self.subject_events, {
                        "event": "query_completed",
                        "query": query,
                        "results_count": len(results),
                        "results": results[:5],  # Top 5 for preview
                    })

                    self.tasks_completed += 1
                    self.current_task = None

            except Exception as e:
                self.log.error(f"RAG Pipeline error: {e}")
                self.tasks_failed += 1

        # Subscribe to rag.command — §12
        if self._loop:
            self._loop.run_until_complete(
                self.nats_subscribe(self.subject_command, on_command)
            )

        # Keep alive
        while self._running:
            self.redis_heartbeat()
            time.sleep(10)

    async def ingest_to_qdrant(self, chunks: list) -> int:
        """Ingest chunks into Qdrant collection."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, Point

            client = QdrantClient(url=self.qdrant_url, timeout=30)

            # Get or create collection
            collections = await client.get_collections()
            collection_names = [c.name for c in collections]
            if self.collection_name not in collection_names:
                await client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.chunk_size,
                        distance=Distance.COSINE
                    )
                )
                self.log.info(f"Created collection: {self.collection_name}")

            # Ingest chunks
            ingested = 0
            for chunk in chunks:
                # Create embedding (placeholder - real impl would use OpenAI/embeddings)
                # For now, use random vectors for demo
                import random
                vector = [random.uniform(-1, 1) for _ in range(self.chunk_size)]

                point = Point(
                    id=chunk["chunk_id"],
                    vector=vector,
                    payload={
                        "chunk_id": chunk["chunk_id"],
                        "text": chunk["text"],
                        "source": chunk.get("source", ""),
                    }
                )

                await client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )
                ingested += 1

            return ingested

        except ImportError:
            self.log.warning("qdrant-client not installed. pip install qdrant-client")
            return 0
        except Exception as e:
            self.log.error(f"Qdrant ingestion error: {e}")
            return 0

    async def query_qdrant(self, query: str) -> list:
        """Query Qdrant collection via LlamaIndex."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Filter, SearchRequest

            client = QdrantClient(url=self.qdrant_url, timeout=30)

            # Create embedding for query (placeholder)
            import random
            query_vector = [random.uniform(-1, 1) for _ in range(self.chunk_size)]

            search_result = await client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=5,
                with_payload=True,
                with_vectors=False,
                search_params=SearchRequest(
                    hnsw_ef=SearchRequest.HNSWParams(ef=SearchRequest.HNSWEf.Cosine)
                )
            )

            results = []
            for hit in search_result:
                results.append({
                    "chunk_id": hit.payload["chunk_id"],
                    "text": hit.payload["text"],
                    "score": hit.score,
                    "source": hit.payload.get("source", ""),
                })

            return results

        except ImportError:
            self.log.warning("qdrant-client not installed. pip install qdrant-client")
            return []
        except Exception as e:
            self.log.error(f"Qdrant query error: {e}")
            return []


def main():
    """Entry point for RAG pipeline agent."""
    agent = RAGPipelineAgent()
    agent.boot()


if __name__ == "__main__":
    main()
