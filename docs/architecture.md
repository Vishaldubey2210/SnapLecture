# SnapLecture Architecture & Optimization Pipeline

## Direct YouTube Stream-to-PDF Pipeline

### 1. No Full Video Download
- Direct stream URL resolution via `yt-dlp` (`download=False`).
- Video files are never written to disk; frames are piped directly into memory.

### 2. Fast Input-Level Seeking
- `ffmpeg -ss {timestamp} -i "{stream_url}"` allows HTTP range requests directly on CDN chunks.
- Avoids decoding entire video stream linearly.

### 3. Parallel Extraction with Ordered Assembly
- `ThreadPoolExecutor` with `min(cpu_count * 2, 12)` workers.
- Pre-allocated results array `results[i] = frame_bytes` guarantees strict chronological frame sequence in generated PDF.

### 4. Resilient Network & Throttling Mitigation
- FFmpeg flags: `-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -http_persistent 1`.
- Up to 3 attempts per frame with exponential backoff (`2^attempt` delay) on HTTP 403 / 429 CDN throttling.
- Individual frame extraction failures do not abort the entire document pipeline.

### 5. High-Throughput PDF Assembly
- `img2pdf` embeds raw JPEG byte buffers directly into PDF pages without re-encoding pixels.
- Eliminates heavy Pillow/Canvas render passes for massive speedup.

### 6. In-Memory Stream URL Cache
- 240-second TTL cache for resolved `googlevideo` URLs eliminates duplicate metadata fetches.
- Preserves signed stream tokens across duration queries and PDF generation calls.
