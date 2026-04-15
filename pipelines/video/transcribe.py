"""
Jart-OS Video Pipeline — Transcription with Whisper
Spec: §18 "Videos: 18, ffmpeg + Whisper large-v3"
     §12 "NATS subjects: jart-os.06.pipeline.video.{command,events}"
     §20 "Stack: ffmpeg, openai-whisper"
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

log = logging.getLogger("jart-os.pipeline.video")


class VideoPipelineAgent(AgentBase):
    """
    Video Pipeline Agent.
    Extracts audio from video via ffmpeg, transcribes with Whisper.
    — §18 "Videos: 18, ffmpeg + Whisper large-v3"
    """

    def __init__(self):
        super().__init__(role="pipeline", domain="video", tier=6)
        self.chunk_size = 512  # §18 "Chunking (512 tok, overlap 50)"
        self.chunk_overlap = 50
        self.whisper_model = os.getenv("WHISPER_MODEL", "base")  # base for speed, large-v3 for quality
        self.supported_formats = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"}

    def run(self):
        """Main loop: process videos from inbox. — §18 Block 1"""
        self.log.info("Video Pipeline running. Waiting for commands...")

        async def on_command(msg):
            try:
                data = json.loads(msg.data.decode())
                action = data.get("action", "process")

                if action == "process":
                    video_path = data.get("video_path")
                    if not video_path:
                        self.log.error("No video_path in command")
                        return

                    self.current_task = f"process_{Path(video_path).name}"
                    self.log.info(f"Processing video: {video_path}")

                    # Extract audio → transcribe → chunk
                    chunks = self.extract_and_chunk(video_path)

                    # Publish result
                    self.publish(self.subject_events, {
                        "event": "video_processed",
                        "video_path": video_path,
                        "chunks_count": len(chunks),
                        "chunks": chunks[:10],  # First 10 for preview
                    })

                    self.tasks_completed += 1
                    self.current_task = None

                elif action == "process_batch":
                    """Process a directory of videos."""
                    directory = data.get("directory")
                    if not directory:
                        self.log.error("No directory in batch command")
                        return

                    self.current_task = f"batch_{Path(directory).name}"
                    all_chunks = []

                    for vid_file in sorted(Path(directory).iterdir()):
                        if vid_file.suffix.lower() in self.supported_formats:
                            chunks = self.extract_and_chunk(str(vid_file))
                            all_chunks.extend(chunks)

                    self.publish(self.subject_events, {
                        "event": "batch_processed",
                        "directory": directory,
                        "videos_processed": len(all_chunks),
                        "total_chunks": len(all_chunks),
                    })

                    self.tasks_completed += 1
                    self.current_task = None

            except Exception as e:
                self.log.error(f"Video pipeline error: {e}")
                self.tasks_failed += 1

        # Subscribe to pipeline.video.command — §12
        if self._loop:
            self._loop.run_until_complete(
                self.nats_subscribe(self.subject_command, on_command)
            )

        # Keep alive
        while self._running:
            self.redis_heartbeat()
            time.sleep(10)

    def extract_and_chunk(self, video_path: str) -> list:
        """
        Extract audio from video, transcribe with Whisper, chunk.
        — §18 "Videos: 18, ffmpeg + Whisper large-v3"
        """
        # Step 1: Extract audio with ffmpeg
        audio_path = self._extract_audio(video_path)
        if not audio_path:
            return []

        # Step 2: Transcribe with Whisper
        transcript = self._transcribe(audio_path)

        # Step 3: Cleanup temp audio
        try:
            Path(audio_path).unlink(missing_ok=True)
        except Exception:
            pass

        if not transcript:
            self.log.warning(f"No transcript from {video_path}")
            return []

        # Step 4: Chunk
        return self._chunk_transcript(transcript, video_path)

    def _extract_audio(self, video_path: str) -> str | None:
        """Extract audio from video using ffmpeg. Returns path to WAV file."""
        import subprocess
        import tempfile

        try:
            # Create temp WAV file
            tmp_dir = Path(os.getenv("DATA_DIR", "./data"))
            tmp_dir.mkdir(parents=True, exist_ok=True)
            audio_path = str(tmp_dir / f"{Path(video_path).stem}_audio.wav")

            result = subprocess.run(
                [
                    "ffmpeg", "-i", video_path,
                    "-vn",                # No video
                    "-acodec", "pcm_s16le",  # PCM 16-bit
                    "-ar", "16000",       # 16kHz sample rate (Whisper optimal)
                    "-ac", "1",           # Mono
                    "-y",                 # Overwrite
                    audio_path
                ],
                capture_output=True,
                text=True,
                timeout=300,  # 5 min max
            )

            if result.returncode != 0:
                self.log.error(f"ffmpeg failed: {result.stderr[:500]}")
                return None

            self.log.info(f"Audio extracted: {audio_path}")
            return audio_path

        except FileNotFoundError:
            self.log.error("ffmpeg not found. Install: apt-get install ffmpeg")
            return None
        except subprocess.TimeoutExpired:
            self.log.error("ffmpeg timed out after 300s")
            return None
        except Exception as e:
            self.log.error(f"Audio extraction error: {e}")
            return None

    def _transcribe(self, audio_path: str) -> str | None:
        """Transcribe audio using Whisper. — §20"""
        try:
            import whisper

            self.log.info(f"Loading Whisper model: {self.whisper_model}")
            model = whisper.load_model(self.whisper_model)

            self.log.info(f"Transcribing: {audio_path}")
            result = model.transcribe(
                audio_path,
                language="es",  # Spanish primary
                verbose=False,
            )

            transcript = result.get("text", "").strip()
            self.log.info(f"Transcription: {len(transcript)} chars")
            return transcript

        except ImportError:
            self.log.error("openai-whisper not installed. pip install openai-whisper")
            return None
        except Exception as e:
            self.log.error(f"Whisper transcription error: {e}")
            return None

    def _chunk_transcript(self, transcript: str, source_path: str) -> list:
        """Chunk transcript into segments. — §18"""
        chunks = []
        chars_per_chunk = self.chunk_size * 4  # ~4 chars per token
        overlap_chars = self.chunk_overlap * 4

        start = 0
        chunk_num = 0
        while start < len(transcript):
            end = start + chars_per_chunk
            chunk_text = transcript[start:end].strip()

            if chunk_text:
                chunks.append({
                    "chunk_id": f"{Path(source_path).stem}_c{chunk_num}",
                    "text": chunk_text,
                    "source": source_path,
                    "type": "video_transcript",
                })
                chunk_num += 1

            start = end - overlap_chars

        self.log.info(f"Created {len(chunks)} chunks from {source_path}")
        return chunks


def main():
    """Entry point for Video pipeline agent."""
    agent = VideoPipelineAgent()
    agent.boot()


if __name__ == "__main__":
    main()
