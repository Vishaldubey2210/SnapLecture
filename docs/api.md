# SnapLecture API Reference

## Endpoints

### 1. Health Check
`GET /api/health`
- Returns system status and operational health.

### 2. Upload Video to PDF
`POST /api/pdf/generate`
- **Form Data**:
  - `video`: File upload (MP4, MOV, WEBM, MKV, AVI, M4V)
  - `interval_seconds`: Frame interval (1-300 seconds, default: 5)
- **Response**: Generated PDF file (`SnapLecture.pdf`)

### 3. YouTube Info Metadata
`POST /api/pdf/youtube-info`
- **Form Data**:
  - `youtube_url`: Public YouTube video link
- **Response**: `{"duration_seconds": <int>}`

### 4. Direct YouTube Stream to PDF
`POST /api/pdf/generate-youtube`
- **Form Data**:
  - `youtube_url`: Public YouTube video link
  - `interval_seconds`: Frame interval (1-300 seconds, default: 5)
- **Response**: Stream-extracted PDF (`SnapLecture-YouTube.pdf`)
- **Headers**:
  - `X-SnapLecture-Ytdlp-Info-Seconds`: Metadata extraction duration
  - `X-SnapLecture-Frame-Extraction-Seconds`: Parallel frame seek duration
  - `X-SnapLecture-Pdf-Assembly-Seconds`: img2pdf conversion duration
  - `X-SnapLecture-Total-Seconds`: Total processing wall-time
  - `X-SnapLecture-Frame-Count`: Total frames embedded in PDF
