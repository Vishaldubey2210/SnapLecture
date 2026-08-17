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
- **Performance Headers**:
  - `X-SnapLecture-Ytdlp-Info-Seconds`: Metadata extraction duration
  - `X-SnapLecture-Frame-Extraction-Seconds`: Parallel frame seek duration
  - `X-SnapLecture-Pdf-Assembly-Seconds`: img2pdf conversion duration
  - `X-SnapLecture-Total-Seconds`: Total processing wall-time
  - `X-SnapLecture-Frame-Count`: Total frames embedded in PDF

### Timing Breakdown Example
```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="SnapLecture-YouTube.pdf"
X-SnapLecture-Ytdlp-Info-Seconds: 0.812
X-SnapLecture-Frame-Extraction-Seconds: 4.231
X-SnapLecture-Pdf-Assembly-Seconds: 0.124
X-SnapLecture-Total-Seconds: 5.167
X-SnapLecture-Frame-Count: 48
```
