# Pipelines Specification
# Jart-OS Content Processing Pipelines — Complete Reference

**Version:** 1.0.0
**Date:** 2026-04-16
**Status:** CANONICAL for TIER-06 PROCESSES
**Source:** Distilled from PIPELINES-Y-ORGANIZACION.md + CANONICAL-SPEC §18-19

---

## Table of Contents

1. [Overview](#1-overview)
2. [Pipeline 1: PDF Processing](#2-pipeline-1-pdf-processing)
3. [Pipeline 2: Photo Processing](#3-pipeline-2-photo-processing)
4. [Pipeline 3: Video Processing](#4-pipeline-3-video-processing)
5. [Pipeline 4: RAG Indexing](#5-pipeline-4-rag-indexing)
6. [Docker Services](#6-docker-services)
7. [Tool Dependencies](#7-tool-dependencies)
8. [Cost Estimates](#8-cost-estimates)
9. [Processing Plan](#9-processing-plan)
10. [File Organization](#10-file-organization)

---

## 1. Overview

### Current Status

| Pipeline | Container | Port | Status |
|----------|-----------|------|--------|
| PDF | pipe-pdf | 10601 | 🔧 Built, not processing |
| Photos | pipe-photos | 10602 | 🔧 Built, not processing |
| Video | pipe-video | 10603 | 🔧 Built, not processing |
| RAG | pipe-rag | 10604 | 🔧 Built, not processing |

### Processing Progress

| Source | Total | Processed | Remaining | % Done |
|--------|-------|-----------|-----------|--------|
| PDFs | 872 | 0 | 872 | 0% |
| Photos | 1,695 | 0 | 1,695 | 0% |
| Videos | 66 (18 key) | 0 | 66 | 0% |

### Data Flow

```
Raw Material (33GB, 3,636 files)
       │
       ├──► PIPE-PDF (:10601) ──► Clean text
       ├──► PIPE-PHOTOS (:10602) ──► Clean text
       └──► PIPE-VIDEO (:10603) ──► Structured guides
                    │
                    ▼
              PIPE-RAG (:10604)
              ├── Chunking (512 tokens, overlap 50)
              ├── Embeddings (bge-m3 / nomic-embed-text)
              └── Qdrant collection "study"
                    │
                    ▼
              Agent queries via NATS
              jart-os.06.pipeline.rag.*
```

---

## 2. Pipeline 1: PDF Processing

### Service: pipe-pdf (`$JART_OS_HOME/TIERS/TIER-06-PROCESSES/10601-pipe-pdf/`)

### Flow

```
PDF (872 files, mixed types)
      │
      ▼
┌─────────────────────────────────────────┐
│  STEP 1: CLASSIFICATION                 │
│                                         │
│  PDF with selectable text?              │
│  ├── YES → Direct text extraction       │
│  ├── NO (scanned) → pdf2image + Vision  │
│  └── MIXED → Separate + process each    │
│                                         │
│  Tool: PyMuPDF (fitz), pdf2image        │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  STEP 2: TEXT EXTRACTION                │
│                                         │
│  Text PDFs: PyMuPDF.getText()           │
│  Scanned PDFs: pdf2image + Vision OCR   │
│  Mixed: Hybrid approach                 │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  STEP 3: TEXT CLEANING                  │
│                                         │
│  • Remove repetitive headers/footers    │
│  • Remove page numbers                  │
│  • Fix encoding (ñ, á, é, í, ó, ú)     │
│  • Remove excessive blank lines         │
│  • Fix common OCR errors                │
│  • Join cut paragraphs                  │
│  • Remove watermarks                    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  STEP 4: DEDUPLICATION                  │
│                                         │
│  • 4-5 copies of same temario exist     │
│  • Compare content (similarity hash)    │
│  • Keep best version                    │
│  • Mark duplicates as "reference"       │
│  • Identify unique content from each    │
│  • Tool: rapidfuzz                      │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  STEP 5: STRUCTURING                    │
│                                         │
│  • Assign to TEMA (1-34)               │
│  • Identify content type:               │
│    - temario (topic exposition)         │
│    - ejercicio (solved exercise)        │
│    - programacion (sample syllabus)     │
│    - normativa (legal/regulatory)       │
│    - practica (practice/exam)           │
│  • Extract metadata (author, year)      │
└──────────────────┬──────────────────────┘
                   │
                   ▼
              Output: Structured text chunks
              → Sent to PIPE-RAG for indexing
```

### PDF Tools

| Tool | Purpose | Install |
|------|---------|---------|
| `PyMuPDF (fitz)` | Extract text from text PDFs | `pip install PyMuPDF` |
| `pdf2image` | Convert scanned PDFs to images | `pip install pdf2image` |
| `poppler` | Backend for pdf2image | `brew install poppler` |
| `Pillow` | Image pre-processing | `pip install Pillow` |
| `rapidfuzz` | Duplicate detection | `pip install rapidfuzz` |
| `langdetect` | Language detection | `pip install langdetect` |
| `chardet` | Encoding detection | `pip install chardet` |

---

## 3. Pipeline 2: Photo Processing

### Service: pipe-photos (`$JART_OS_HOME/TIERS/TIER-06-PROCESSES/10602-pipe-photos/`)

### Flow

```
Photo.jpg (1,695 CEDE photos, Office Lens)
      │
      ▼
┌─────────────────────────────────────────┐
│  STEP 1: PRE-PROCESSING                 │
│                                         │
│  • Deskew: straighten curved pages      │
│  • Crop: remove excess borders          │
│  • Contrast: improve readability        │
│  • Resize: normalize dimensions         │
│  • Binarize: B&W for text-only pages    │
│                                         │
│  Tool: Pillow, opencv-python            │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  STEP 2: OCR + COMPREHENSION            │
│                                         │
│  Option A: Vision Model (GLM-4V/GPT-4V)│
│  • More expensive but understands       │
│  • Identifies tables, diagrams          │
│  • Interprets text in context           │
│                                         │
│  Option B: Tesseract OCR (local/free)   │
│  • Text only, no comprehension          │
│  • Cheaper, works offline               │
│  • Worse with curved images             │
│                                         │
│  RECOMMENDATION: Vision for complex,    │
│  Tesseract for simple text              │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  STEP 3: ORGANIZATION BY TOPIC          │
│                                         │
│  Photos named: Tomo_X_Tema_YY (N).jpg  │
│  • Group by tema                        │
│  • Join pages of same topic             │
│  • Remove duplicate pages               │
│  • Verify completeness (missing pages?) │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  STEP 4: TEXT CLEANING                  │
│                                         │
│  • Fix OCR errors (rn→m, cl→d, 0→O)   │
│  • Fix character encoding               │
│  • Join consecutive page text           │
│  • Remove page numbering                │
└──────────────────┬──────────────────────┘
                   │
                   ▼
              Output: Clean text per topic
              → Sent to PIPE-RAG for indexing
```

### Photo Tools

| Tool | Purpose | Install |
|------|---------|---------|
| `Pillow` | Pre-processing | `pip install Pillow` |
| `opencv-python` | Advanced deskew | `pip install opencv-python` |
| `pytesseract` | Local OCR (Tesseract) | `brew install tesseract` + `pip install pytesseract` |
| Vision API | OCR + comprehension | Z.AI GLM-4V / OpenRouter |

---

## 4. Pipeline 3: Video Processing

### Service: pipe-video (`$JART_OS_HOME/TIERS/TIER-06-PROCESSES/10603-pipe-video/`)

### Flow

```
Video.mp4 (18 key videos, 48-55MB each)
      │
      ├──► ffmpeg extracts audio → .wav
      │          │
      │          ▼
      │     Whisper large-v3
      │          │
      │          ▼
      │     Transcription with timestamps (.srt/.txt)
      │
      ├──► ffmpeg extracts frames (1 every 30 seconds)
      │          │
      │          ▼
      │     Vision Model (GLM-4V / GPT-4V)
      │          │
      │          ▼
      │     Screen text + visual context
      │
      └────► Fusion: Transcription + Visual
                   │
                   ▼
             Structured video guide
             (what is said + what is shown + when)
                   │
                   ▼
             18 guides → Master guide
             "How to create a FP Syllabus"
```

### Hardware Considerations

| Factor | Detail |
|--------|--------|
| RAM for Whisper large-v3 | ~3GB (fits on Mini M1) |
| Processing | 1 video at a time (limited RAM) |
| Time per video | ~30-60 min on M1 |
| Total time | ~10-18 hours for all 18 videos |

### Video Tools

| Tool | Purpose | Install |
|------|---------|---------|
| `ffmpeg` | Extract audio + frames | `brew install ffmpeg` |
| `openai-whisper` | Batch transcription | `pip install openai-whisper` |
| Vision API | Frame OCR | Z.AI GLM-4V / OpenRouter |

---

## 5. Pipeline 4: RAG Indexing

### Service: pipe-rag (`$JART_OS_HOME/TIERS/TIER-06-PROCESSES/10601-pipe-rag/`)

### Flow

```
All clean text (from PDF + Photos + Video pipelines)
      │
      ▼
┌─────────────────────────────────────────┐
│  STEP 1: SEMANTIC CHUNKING              │
│                                         │
│  • Chunk size: 512 tokens               │
│  • Overlap: 50 tokens                   │
│  • Preserve context (title, topic)      │
│  • Metadata per chunk:                  │
│    {tema: 15, tipo: "temario",          │
│     fuente: "CEDE_Tomo2", pagina: 3}    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  STEP 2: EMBEDDING GENERATION           │
│                                         │
│  Model: bge-m3 or nomic-embed-text      │
│  Batch processing for efficiency        │
│  Store: Qdrant collection "study"       │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  STEP 3: VECTOR STORAGE                 │
│                                         │
│  Qdrant collection: "study"             │
│  Total estimated chunks: ~15,000-25,000 │
│  Index: HNSW (default)                  │
│  Distance: Cosine                       │
└──────────────────┬──────────────────────┘
                   │
                   ▼
              Ready for agent queries
              NATS: jart-os.06.pipeline.rag.query
```

### Query Flow

```
Agent needs info about "Topic 15 - wines"
      │
      ▼
NATS: jart-os.06.pipeline.rag.query
      {query: "vinos tema 15", top_k: 5, filter: {tema: 15}}
      │
      ▼
PIPE-RAG → Qdrant search → Returns top 5 chunks
      │
      ▼
Agent receives context → Generates response
```

---

## 6. Docker Services

### Compose Files

| Pipeline | Path |
|----------|------|
| PDF | `TIERS/TIER-06-PROCESSES/10601-pipe-pdf/docker-compose.yml` |
| Photos | `TIERS/TIER-06-PROCESSES/10602-pipe-photos/docker-compose.yml` |
| Video | `TIERS/TIER-06-PROCESSES/10603-pipe-video/docker-compose.yml` |
| RAG | `TIERS/TIER-06-PROCESSES/10604-pipe-rag/docker-compose.yml` |

### Implementation Files

| Pipeline | Script | Dockerfile |
|----------|--------|------------|
| PDF | `pipelines/pdf/extract.py` | `TIERS/.../Dockerfile` |
| Photos | `pipelines/photos/extract.py` | `TIERS/.../Dockerfile` |
| Video | `pipelines/video/transcribe.py` | `TIERS/.../Dockerfile` |
| RAG | `pipelines/rag/index.py` | `TIERS/.../Dockerfile` |

### NATS Integration

```
Subjects:
  jart-os.06.pipeline.pdf.command    → Start PDF processing
  jart-os.06.pipeline.pdf.events     → PDF progress events
  jart-os.06.pipeline.photos.command → Start photo processing
  jart-os.06.pipeline.photos.events  → Photo progress events
  jart-os.06.pipeline.video.command  → Start video processing
  jart-os.06.pipeline.video.events   → Video progress events
  jart-os.06.pipeline.rag.command    → Start RAG indexing
  jart-os.06.pipeline.rag.query      → Query RAG store
  jart-os.06.pipeline.rag.events     → RAG indexing events
```

---

## 7. Tool Dependencies

### System-Level (brew)

```bash
brew install ffmpeg poppler tesseract
```

### Python Packages

```bash
pip install PyMuPDF pdf2image Pillow opencv-python pytesseract
pip install openai-whisper rapidfuzz langdetect chardet
pip install qdrant-client llama-index
```

### Current Python Version Issue

- **System Python:** 3.9.6 (macOS default)
- **Required:** 3.11+ (for modern llama-index, qdrant-client)
- **Solution:** `brew install python@3.12` or use Docker Python images

---

## 8. Cost Estimates

### Vision API for Photos

| Option | Cost per photo | Total (1,695) | Quality |
|--------|---------------|---------------|---------|
| GLM-4V (Z.AI) | ~$0.01 | ~$17 | High |
| GPT-4V (OpenAI) | ~$0.01-0.03 | ~$17-50 | High |
| Tesseract (local) | $0 | $0 | Medium |
| Mixed (Vision complex + Tesseract simple) | ~$0.005 | ~$8-10 | Good |

### Whisper Transcription

| Option | Cost | Quality |
|--------|------|---------|
| Local Whisper large-v3 | $0 | High (10-18h total) |
| API Whisper (OpenAI) | ~$0.006/min | High |

### Total Estimated Processing Cost

| Approach | Cost | Time |
|----------|------|------|
| All local (Whisper + Tesseract) | $0 | ~30-40h |
| Vision API + Whisper local | ~$8-17 | ~15-25h |
| All API | ~$30-60 | ~5-10h |

---

## 9. Processing Plan

### Recommended Order

```
PHASE 2.1: PDF Pipeline (highest volume, easiest to automate)
├── Week 1: Process first 50 PDFs (test pipeline)
├── Week 2: Process remaining 822 PDFs (batch)
└── Output: ~8,000-12,000 chunks in Qdrant

PHASE 2.2: Photo Pipeline (medium volume, needs Vision API)
├── Week 3: Process first 100 photos (test deskew + OCR)
├── Week 4: Process remaining 1,595 photos
└── Output: ~5,000-8,000 chunks in Qdrant

PHASE 2.3: Video Pipeline (lowest volume, longest per file)
├── Week 5: Process first 3 videos (test Whisper + Vision)
├── Week 6: Process remaining 15 videos (overnight batches)
└── Output: ~500-1,000 chunks in Qdrant

PHASE 2.4: RAG Indexing (continuous, alongside above)
├── Continuous: Index processed chunks
├── Verify: Search quality tests
└── Total: ~15,000-25,000 chunks indexed
```

---

## 10. File Organization

### Data Directory Structure

```
$JART_OS_HOME/data/
├── raw/                          # Original material (read-only)
│   ├── pdfs/                     # 872 PDFs
│   ├── photos/                   # 1,695 CEDE photos
│   └── videos/                   # 66 videos
├── processed/                    # Pipeline output
│   ├── pdfs/
│   │   ├── text/                 # Extracted text per PDF
│   │   ├── metadata/             # Classification metadata
│   │   └── chunks/               # Pre-chunked text (pre-RAG)
│   ├── photos/
│   │   ├── enhanced/             # Pre-processed images
│   │   ├── text/                 # OCR output per photo
│   │   └── chunks/
│   └── videos/
│       ├── transcripts/          # Whisper .srt/.txt
│       ├── frames/               # Extracted key frames
│       ├── guides/               # Structured video guides
│       └── chunks/
└── qdrant/                       # Qdrant storage
    └── study/                    # Collection data
```

---

*Distilled from PIPELINES-Y-ORGANIZACION.md (506 lines) + CANONICAL-SPEC §18-19 + TIER-06 compose files.*
*Source: $STUDY_DATA_DIR/PROJECT-JartOS/PIPELINES-Y-ORGANIZACION.md*
