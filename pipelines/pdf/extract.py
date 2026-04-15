"""
Jart-OS PDF Pipeline — Extract text from PDFs
Spec: §18 "BLOCK 1: CONTENT PIPELINE"
     §20 "PyMuPDF / Vision API"
     §12 "NATS subjects: jart-os.06.pipeline.pdf.{command,events}"
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

log = logging.getLogger("jart-os.pipeline.pdf")


class PDFPipelineAgent(AgentBase):
    """
    PDF Pipeline Agent.
    Extracts text from PDFs using PyMuPDF, chunks into 512-token segments.
    — §18 "PDFs: 872, Tool: PyMuPDF / Vision API"
    """

    def __init__(self):
        super().__init__(role="pipeline", domain="pdf", tier=6)
        self.chunk_size = 512  # §18 "Chunking (512 tok, overlap 50)"
        self.chunk_overlap = 50

    def run(self):
        """Main loop: process PDFs from inbox. — §18 Block 1"""
        self.log.info("PDF Pipeline running. Waiting for commands...")

        async def on_command(msg):
            try:
                data = json.loads(msg.data.decode())
                action = data.get("action", "process")

                if action == "process":
                    pdf_path = data.get("pdf_path")
                    if not pdf_path:
                        self.log.error("No pdf_path in command")
                        return

                    self.current_task = f"process_{Path(pdf_path).name}"
                    self.log.info(f"Processing PDF: {pdf_path}")

                    # Extract and chunk
                    chunks = self.extract_and_chunk(pdf_path)

                    # Publish result
                    self.publish(self.subject_events, {
                        "event": "pdf_processed",
                        "pdf_path": pdf_path,
                        "chunks_count": len(chunks),
                        "chunks": chunks[:10],  # First 10 for preview
                    })

                    self.tasks_completed += 1
                    self.current_task = None

            except Exception as e:
                self.log.error(f"PDF pipeline error: {e}")
                self.tasks_failed += 1

        # Subscribe to pipeline.pdf.command — §12
        if self._loop:
            self._loop.run_until_complete(
                self.nats_subscribe(self.subject_command, on_command)
            )

        # Keep alive
        while self._running:
            self.redis_heartbeat()
            time.sleep(10)

    def extract_and_chunk(self, pdf_path: str) -> list:
        """
        Extract text from PDF and chunk into segments.
        — §18 "Output: Text + chunks"
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            self.log.error("PyMuPDF not installed. pip install pymupdf")
            return []

        chunks = []
        doc = fitz.open(pdf_path)

        for page_num, page in enumerate(doc):
            text = page.get_text()
            if not text.strip():
                continue

            # Simple chunking by character count (approximate tokens)
            chars_per_chunk = self.chunk_size * 4  # ~4 chars per token
            overlap_chars = self.chunk_overlap * 4

            start = 0
            chunk_num = 0
            while start < len(text):
                end = start + chars_per_chunk
                chunk_text = text[start:end].strip()

                if chunk_text:
                    chunks.append({
                        "chunk_id": f"{Path(pdf_path).stem}_p{page_num}_c{chunk_num}",
                        "page": page_num,
                        "text": chunk_text,
                        "source": pdf_path,
                        "type": "pdf_text",
                    })
                    chunk_num += 1

                start = end - overlap_chars

        doc.close()
        self.log.info(f"Extracted {len(chunks)} chunks from {pdf_path}")
        return chunks


def main():
    """Entry point for PDF pipeline agent."""
    agent = PDFPipelineAgent()
    agent.boot()


if __name__ == "__main__":
    main()
