# 🗺️ SnapLecture Product Roadmap

## 🎯 Vision
SnapLecture is the privacy-first, blazing-fast bridge between video learning and study-ready PDF lecture notes.

---

## 📅 Roadmap Stages

```text
┌───────────────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
│         Phase 1           │      │         Phase 2           │      │         Phase 3           │
│      Core MVP & PDF       │ ───► │  Direct YouTube Stream    │ ───► │  Smart Slide Extraction   │
│  (Uploads, Interval, PDF) │      │  (Seek, Parallel, img2pdf)│      │  (Deduplication, OCR AI)  │
└───────────────────────────┘      └───────────────────────────┘      └───────────────────────────┘
                                                                                    │
                                                                                    ▼
                                                                      ┌───────────────────────────┐
                                                                      │         Phase 4           │
                                                                      │  Ecosystem & Extensions   │
                                                                      │  (Chrome Ext, Cloud API)  │
                                                                      └───────────────────────────┘
```

---

### ✅ Phase 1: Core Foundation (Completed)
- [x] FastAPI stateless backend architecture
- [x] Next.js frontend upload and conversion interface
- [x] Video extension and size validation
- [x] Interval-based frame capture
- [x] Ephemeral file cleanup via BackgroundTask
- [x] Privacy-first design (no permanent video or PDF persistence)

### 🚀 Phase 2: Direct YouTube Streaming & High Performance (Current)
- [x] Direct stream URL resolution with `yt-dlp` (`download=False`)
- [x] Input-level fast seeking via `ffmpeg -ss` (no full video download)
- [x] Parallel frame extraction with `ThreadPoolExecutor` (CPU-bound scaling)
- [x] Order preservation with pre-allocated indexing
- [x] Zero-re-encoding PDF assembly via `img2pdf`
- [x] Resilient reconnects & 403/429 exponential backoff retries
- [x] In-memory short-term stream cache (240s TTL)
- [x] Millisecond execution telemetry headers (`X-SnapLecture-*`)

### 🔮 Phase 3: Intelligent Frame Selection (Upcoming)
- [ ] **Slide Change Detection (Perceptual Hashing / SSIM)**: Filter out duplicate or blurry frames when speaker doesn't change slides.
- [ ] **OCR & Text Searchable PDFs**: Embed searchable text layers using Tesseract / lightweight OCR models.
- [ ] **AI Lecture Summarization**: Optional slide title and key takeaway summaries.
- [ ] **Dark Mode / Contrast Optimization**: Clean up low-contrast whiteboard recordings.

### 🌐 Phase 4: Platform & Cloud Ecosystem (Future)
- [ ] **Chrome / Firefox Extension**: One-click "Snap to PDF" button directly inside YouTube & Coursera players.
- [ ] **Webhook / Cloud Storage Integrations**: Direct export to Notion, Google Drive, or Obsidian.
- [ ] **Multi-Format Export**: Markdown with inline screenshots, EPUB, and Anki flashcard exports.
