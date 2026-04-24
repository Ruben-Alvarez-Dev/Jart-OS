"""
Jart-OS Photos Pipeline — OCR + Vision extraction from images
Spec: §18 "CEDE Photos: 1695, Vision Model OCR"
     §12 "NATS subjects: jart-os.06.pipeline.photos.{command,events}"
     §20 "Stack: Pillow, pytesseract, Vision API fallback"
"""

import os
import sys
import json
import logging
import asyncio
import time
import base64
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from agents.core.base import AgentBase

log = logging.getLogger("jart-os.pipeline.photos")


class PhotosPipelineAgent(AgentBase):
    """
    Photos Pipeline Agent.
    Extracts text from images using OCR (Tesseract) with Vision API fallback.
    — §18 "CEDE Photos: 1695, Vision Model OCR"
    """

    def __init__(self):
        super().__init__(role="pipeline", domain="photos", tier=6)
        self.chunk_size = 512  # §18 "Chunking (512 tok, overlap 50)"
        self.chunk_overlap = 50
        self.supported_formats = {".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".gif", ".webp"}

    def run(self):
        """Main loop: process images from inbox. — §18 Block 1"""
        self.log.info("Photos Pipeline running. Waiting for commands...")

        async def on_command(msg):
            try:
                data = json.loads(msg.data.decode())
                action = data.get("action", "process")

                if action == "process":
                    image_path = data.get("image_path")
                    if not image_path:
                        self.log.error("No image_path in command")
                        return

                    self.current_task = f"process_{Path(image_path).name}"
                    self.log.info(f"Processing image: {image_path}")

                    # Extract text via OCR
                    chunks = self.extract_and_chunk(image_path)

                    # Publish result
                    self.publish(self.subject_events, {
                        "event": "image_processed",
                        "image_path": image_path,
                        "chunks_count": len(chunks),
                        "chunks": chunks[:10],  # First 10 for preview
                    })

                    self.tasks_completed += 1
                    self.current_task = None

                elif action == "process_batch":
                    """Process a directory of images."""
                    directory = data.get("directory")
                    if not directory:
                        self.log.error("No directory in batch command")
                        return

                    self.current_task = f"batch_{Path(directory).name}"
                    all_chunks = []

                    for img_file in sorted(Path(directory).iterdir()):
                        if img_file.suffix.lower() in self.supported_formats:
                            chunks = self.extract_and_chunk(str(img_file))
                            all_chunks.extend(chunks)

                    self.publish(self.subject_events, {
                        "event": "batch_processed",
                        "directory": directory,
                        "images_processed": len(all_chunks),
                        "total_chunks": len(all_chunks),
                    })

                    self.tasks_completed += 1
                    self.current_task = None

            except Exception as e:
                self.log.error(f"Photos pipeline error: {e}")
                self.tasks_failed += 1

        # Subscribe to pipeline.photos.command — §12
        if self._loop:
            self._loop.run_until_complete(
                self.nats_subscribe(self.subject_command, on_command)
            )

        # Keep alive
        while self._running:
            self.redis_heartbeat()
            time.sleep(10)

    def extract_and_chunk(self, image_path: str) -> list:
        """
        Extract text from image using OCR, then chunk.
        — §18 "Output: Text + chunks"
        Strategy: Tesseract OCR → Vision API fallback → LLM fallback
        """
        text = None

        # Strategy 1: Tesseract OCR (local, fast)
        text = self._ocr_tesseract(image_path)

        # Strategy 2: Vision API via LiteLLM (if Tesseract fails or returns empty)
        if not text or len(text.strip()) < 20:
            self.log.info("Tesseract returned minimal text, trying Vision API...")
            text = self._ocr_vision_api(image_path)

        if not text:
            self.log.warning(f"No text extracted from {image_path}")
            return []

        # Chunk the extracted text
        return self._chunk_text(text, image_path)

    def _ocr_tesseract(self, image_path: str) -> str | None:
        """Extract text using Tesseract OCR."""
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang="spa+eng")
            self.log.info(f"Tesseract extracted {len(text)} chars from {image_path}")
            return text

        except ImportError:
            self.log.warning("pytesseract/Pillow not installed, skipping Tesseract")
            return None
        except Exception as e:
            self.log.warning(f"Tesseract OCR failed: {e}")
            return None

    def _ocr_vision_api(self, image_path: str) -> str | None:
        """Extract text using Vision API via LiteLLM proxy."""
        try:
            import requests
            from PIL import Image
            import io

            # Read and encode image
            img = Image.open(image_path)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            img_b64 = base64.b64encode(buf.getvalue()).decode()

            # Call LLM with vision capability
            litellm_url = os.getenv("LITELLM_URL", "http://litellm:4000")
            litellm_key = os.getenv("LITELLM_KEY")
            if not litellm_key:
                raise RuntimeError("LITELLM_KEY env var is required — no default for security")

            response = requests.post(
                f"{litellm_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {litellm_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",  # Vision-capable model via LiteLLM
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Extract ALL text from this image. Return only the extracted text, preserving structure and formatting. If it's a document in Spanish, maintain the original language."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{img_b64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 4096,
                },
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()
                text = result["choices"][0]["message"]["content"]
                self.log.info(f"Vision API extracted {len(text)} chars from {image_path}")
                return text
            else:
                self.log.warning(f"Vision API failed: {response.status_code}")
                return None

        except ImportError:
            self.log.warning("requests/Pillow not installed for Vision API")
            return None
        except Exception as e:
            self.log.warning(f"Vision API OCR failed: {e}")
            return None

    def _chunk_text(self, text: str, source_path: str) -> list:
        """Chunk extracted text into segments. — §18"""
        chunks = []
        chars_per_chunk = self.chunk_size * 4  # ~4 chars per token
        overlap_chars = self.chunk_overlap * 4

        start = 0
        chunk_num = 0
        while start < len(text):
            end = start + chars_per_chunk
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "chunk_id": f"{Path(source_path).stem}_c{chunk_num}",
                    "text": chunk_text,
                    "source": source_path,
                    "type": "image_ocr",
                })
                chunk_num += 1

            start = end - overlap_chars

        self.log.info(f"Created {len(chunks)} chunks from {source_path}")
        return chunks


def main():
    """Entry point for Photos pipeline agent."""
    agent = PhotosPipelineAgent()
    agent.boot()


if __name__ == "__main__":
    main()
