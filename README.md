# 🚧 ONGOING PROJECT — SNAPLECTURE

<p align="center">
  <img src="https://img.shields.io/badge/STATUS-ONGOING%20PROJECT-orange?style=for-the-badge" alt="Ongoing Project"/>
  <img src="https://img.shields.io/badge/PROJECT-SnapLecture-6366f1?style=for-the-badge" alt="SnapLecture"/>
</p>

<p align="center">
  <strong>Turn Video Lessons into Study-Ready PDFs.</strong>
</p>

<p align="center">
  SnapLecture is a privacy-focused web application designed to transform
  authorized video content into structured, downloadable PDF documents
  containing captured learning frames.
</p>

---

## 📌 Project Status

> 🚧 **SnapLecture is currently under active development.**

The project is being built with a production-oriented architecture, with a strong focus on:

* Clean frontend/backend separation
* Stateless processing
* Temporary file handling
* Privacy-first design
* Scalable video processing
* PDF generation
* API-driven architecture
* Usage analytics without storing user-generated documents

Features and architecture may evolve as development progresses.

---

# 🎯 What is SnapLecture?

Students often watch long-form lectures, tutorials, presentations, and educational videos while simultaneously taking notes.

SnapLecture aims to simplify this workflow.

The core idea is:

```text
Authorized Video / YouTube Stream URL
      ↓
Remote Input-Level Seek (No Full Download)
      ↓
Parallel Frame Extraction (ThreadPoolExecutor)
      ↓
Direct Lossless PDF Assembly (img2pdf)
      ↓
Instant Download & Ephemeral Cleanup
```

Instead of manually pausing a lecture and taking hundreds of screenshots, SnapLecture is designed to automate the process.

For example:

```text
Video
1:00:00 duration
       ↓
5-second interval
       ↓
~720 captured frames
       ↓
PDF document
       ↓
Download
```

The generated document is intended to provide a visual study reference that can be reviewed offline.

---

# ✨ Core Features

## 📸 Automated Frame Capture

Capture frames from authorized video content at configurable intervals.

Planned intervals include:

* 5 seconds
* 10 seconds
* 30 seconds

## ⚡ Direct YouTube Stream Seeking (Zero Full Download)

Transform public YouTube videos directly into study PDFs without downloading full media files:
* **Input-Level Remote Seeking**: Uses `yt-dlp` stream URLs with FFmpeg HTTP range requests.
* **Parallel Worker Threads**: Multi-threaded extraction via `ThreadPoolExecutor`.
* **Zero-Re-encoding PDF Assembly**: `img2pdf` directly embeds raw JPEG streams for instant rendering.
* **Resilient Throttling Mitigation**: Automatic retries with exponential backoff on CDN limits.

---

## 📄 Automatic PDF Generation

Captured frames are assembled into a PDF document automatically.

The intended workflow:

```text
Video → Frames → PDF → Download
```

Users do not need to manually combine screenshots.

---

## 🔒 Privacy-First Processing

SnapLecture is designed around a **no-permanent-storage architecture**.

The application is not intended to maintain:

* User accounts
* Passwords
* Personal profiles
* PDF history
* Permanent video files
* Permanent screenshots
* Permanent generated documents

Processing data can exist temporarily during the generation process and should be removed after the request is completed.

---

## ⚡ Stateless Processing

The backend is designed to process a request without requiring a traditional application database.

Conceptually:

```text
Request
   ↓
Temporary Processing
   ↓
PDF Generation
   ↓
Response
   ↓
Cleanup
```

This makes the core processing architecture simpler and reduces unnecessary data retention.

---

# 📊 Analytics

SnapLecture may use privacy-conscious analytics to understand product usage.

The analytics layer is intended to track aggregate product events such as:

```text
Page Visit
PDF Generation Started
PDF Generation Completed
PDF Generation Failed
PDF Downloaded
```

The purpose is to understand:

* Number of visitors
* Unique visitors
* Number of PDF generations
* Successful generations
* Failed generations
* General product usage

The analytics layer is separate from the generated PDF processing pipeline.

---

# 🏗️ Architecture

SnapLecture follows a modular full-stack architecture.

```text
                         ┌──────────────────┐
                         │      USER        │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   Next.js Web    │
                         │    Frontend      │
                         └────────┬─────────┘
                                  │
                             HTTPS / API
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    FastAPI       │
                         │     Backend      │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
              Validation     Processing       PDF
                    │             │             │
                    │             ▼             │
                    │       Frame Service      │
                    │             │             │
                    │             ▼             │
                    │       PDF Service         │
                    │             │             │
                    └─────────────┼─────────────┘
                                  │
                                  ▼
                         Temporary Response
                                  │
                                  ▼
                         ┌──────────────────┐
                         │      USER        │
                         │  Download PDF    │
                         └──────────────────┘
```

---

# 🧱 Technology Stack

## Frontend

| Technology   | Purpose                     |
| ------------ | --------------------------- |
| Next.js      | React-based web application |
| TypeScript   | Type-safe development       |
| Tailwind CSS | UI styling                  |
| ESLint       | Code quality                |
| App Router   | Modern Next.js routing      |

---

## Backend

| Technology | Purpose                     |
| ---------- | --------------------------- |
| Python     | Core processing language    |
| FastAPI    | REST API framework          |
| Pydantic   | Request/response validation |
| Uvicorn    | ASGI server                 |

---

## Video & Image Processing

| Technology | Purpose                               |
| ---------- | ------------------------------------- |
| FFmpeg     | Video processing and frame extraction |
| OpenCV     | Image/frame processing                |
| Pillow     | Image manipulation and optimization   |

---

## PDF Generation

| Technology | Purpose                     |
| ---------- | --------------------------- |
| ReportLab  | Programmatic PDF generation |

---

## Analytics

Potential analytics layer:

* PostHog
* Aggregate usage events
* Product analytics

---

## DevOps

Planned deployment stack:

```text
Frontend → Vercel
Backend  → Railway / Render / equivalent
```

Containerization and CI/CD configuration are also part of the project architecture.

---

# 📁 Project Structure

```text
SnapLecture/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── backend/
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── health.py
│   │   │       └── pdf.py
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── logging.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── video_service.py
│   │   │   ├── frame_service.py
│   │   │   └── pdf_service.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── pdf.py
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── cleanup.py
│   │   │   └── validators.py
│   │   │
│   │   └── models/
│   │       └── __init__.py
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_health.py
│   │
│   ├── temp/
│   ├── .env.example
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   └── ...
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── development.md
│
├── scripts/
│   ├── setup.ps1
│   └── cleanup.ps1
│
├── .dockerignore
├── .editorconfig
├── .gitignore
├── docker-compose.yml
├── LICENSE
└── README.md
```

---

# 🔄 Application Workflow

## Step 1 — User Input

The user provides an authorized video source.

```text
Video Source
     ↓
URL / Supported Input
```

---

## Step 2 — Validation

The backend validates the request.

Validation can include:

* Input format
* Supported source
* Processing interval
* File/video limits
* Request constraints

---

## Step 3 — Processing

The backend creates a temporary processing workspace.

```text
Temporary Workspace
        ↓
Video Processing
        ↓
Frame Extraction
```

---

## Step 4 — Frame Selection

Frames are captured according to the selected interval.

Example:

```text
00:00 → Frame 01
00:05 → Frame 02
00:10 → Frame 03
00:15 → Frame 04
...
```

---

## Step 5 — PDF Creation

The PDF service assembles the processed frames.

```text
Frame 01
   ↓
Frame 02
   ↓
Frame 03
   ↓
Frame 04
   ↓
   ...
   ↓
PDF
```

---

## Step 6 — Response

The generated PDF is returned to the user.

```text
Backend
   ↓
HTTP Response
   ↓
Browser
   ↓
Download
```

---

## Step 7 — Cleanup

Temporary processing data is removed after processing.

```text
Temporary Frames
       ↓
Generated PDF
       ↓
Response
       ↓
Cleanup
       ↓
DELETE TEMP DATA
```

This is a core design principle of SnapLecture.

---

# 🔐 Privacy & Data Handling

SnapLecture is designed with data minimization in mind.

### Intended architecture

```text
                USER DATA
                    │
                    ▼
             Request Processing
                    │
                    ▼
             Temporary Data
                    │
                    ▼
              PDF Response
                    │
                    ▼
                 Cleanup
                    │
                    ▼
              Data Removed
```

The application is not designed to maintain a user document library.

### No traditional user system

The MVP does not require:

```text
❌ User registration
❌ Password authentication
❌ User profiles
❌ Saved PDF history
❌ Personal dashboard
```

The goal is to make the application usable immediately without creating an account.

---

# 🛡️ Security Considerations

The backend is being designed with basic production security practices including:

* Input validation
* Request size limits
* Processing time limits
* Temporary file isolation
* Automatic cleanup
* CORS configuration
* Environment variable configuration
* Structured logging
* Error handling
* API-level validation

Additional protections will be introduced as the application moves toward production.

---

# 🚀 Development Roadmap

## Phase 1 — Foundation

* [x] Repository created
* [x] Project structure
* [x] Frontend initialized
* [x] FastAPI backend initialized
* [x] Environment configuration
* [x] Logging configuration
* [x] Health API
* [x] Temporary file architecture

## Phase 2 — Core Processing

* [ ] Processing request schema
* [ ] Input validation
* [ ] Video processing service
* [ ] Frame extraction service
* [ ] PDF generation service
* [ ] Temporary workspace management
* [ ] Automatic cleanup
* [ ] Error handling

## Phase 3 — Frontend

* [ ] Landing page
* [ ] Video input interface
* [ ] Processing interval selector
* [ ] Generate button
* [ ] Processing state
* [ ] Progress UI
* [ ] PDF download
* [ ] Responsive design
* [ ] Mobile optimization

## Phase 4 — Product Experience

* [ ] Modern dashboard-style interface
* [ ] Empty states
* [ ] Error states
* [ ] Loading states
* [ ] Processing progress
* [ ] User-friendly validation
* [ ] Accessibility improvements

## Phase 5 — Analytics

* [ ] Visitor analytics
* [ ] PDF generation events
* [ ] Success/failure metrics
* [ ] Download events
* [ ] Product usage dashboard

## Phase 6 — Production

* [ ] Docker configuration
* [ ] CI/CD pipeline
* [ ] Production environment
* [ ] API rate limiting
* [ ] Monitoring
* [ ] Performance optimization
* [ ] Resource limits
* [ ] Production deployment

---

# 🧠 Future Features

Once the core system is stable, SnapLecture can evolve beyond simple frame capture.

Potential features include:

### Smart Slide Detection

Instead of taking a screenshot every fixed interval:

```text
Video
 ↓
Scene / Slide Change Detection
 ↓
Important Frame
 ↓
PDF
```

This can significantly reduce duplicate frames.

---

### AI-Powered Notes

Potential future pipeline:

```text
Video
 ↓
Frames + Audio/Transcript
 ↓
AI Processing
 ↓
Structured Notes
 ↓
PDF
```

---

### Study Material Generation

Future versions could potentially generate:

* Lecture notes
* Summaries
* Flashcards
* Questions
* Revision sheets
* Chapter-wise PDFs
* Key concept extraction

---

# ⚡ Performance Considerations

Long videos can produce a large number of frames.

For example:

```text
1 hour video
60 × 60 seconds
= 3600 seconds

3600 / 5
= 720 frames
```

Therefore, SnapLecture will need to optimize:

* Frame resolution
* JPEG/WebP compression
* Memory usage
* CPU utilization
* PDF generation
* Processing time
* Concurrent requests

Resource limits will be applied to prevent a single request from consuming excessive server resources.

---

# 🧪 Testing Strategy

The backend will use automated tests for important components.

Planned testing areas:

```text
API
 ├── Health endpoint
 ├── Input validation
 └── Error handling

Processing
 ├── Frame extraction
 ├── Image processing
 └── PDF generation

Cleanup
 ├── Temporary directory creation
 ├── File cleanup
 └── Failure cleanup
```

Testing tools may include:

* Pytest
* FastAPI TestClient
* Integration tests
* Frontend component tests

---

# 🐳 Docker

SnapLecture is being structured to support containerized deployment.

Planned architecture:

```text
┌─────────────────────────────┐
│          Frontend           │
│          Next.js            │
└──────────────┬──────────────┘
               │
               │ API
               ▼
┌─────────────────────────────┐
│          Backend            │
│          FastAPI            │
│                             │
│  Python + FFmpeg + OpenCV   │
└─────────────────────────────┘
```

Containerization helps maintain consistent development and production environments.

---

# 💻 Local Development

## Requirements

Before running SnapLecture locally, install:

* Node.js
* npm
* Python 3.11+
* FFmpeg
* Git

---

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

## Backend

```bash
cd backend

python -m venv venv
```

### Windows

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run API:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 🔌 API Design

The backend follows REST-oriented API principles.

Current foundation:

```text
GET /api/health
```

Planned core endpoint:

```text
POST /api/pdf/generate
```

Potential request flow:

```text
POST /api/pdf/generate
        ↓
Validate Request
        ↓
Process Source
        ↓
Extract Frames
        ↓
Generate PDF
        ↓
Return PDF
        ↓
Cleanup
```

The exact API contract will evolve during implementation.

---

# 📈 Product Goals

SnapLecture aims to provide a workflow that is:

### Simple

No unnecessary account creation or complicated setup.

### Fast

Efficient frame processing and PDF generation.

### Private

Minimize data retention.

### Scalable

Keep processing services modular so they can be independently optimized.

### Maintainable

Use a clean separation between:

```text
API
Business Logic
Processing
PDF Generation
Utilities
Configuration
```

---

# ⚠️ Content & Platform Compliance

SnapLecture is intended for **authorized or otherwise legally permitted video content**.

Users are responsible for ensuring that the content they process and export is permitted by the applicable copyright, license, and platform terms.

The application should not be designed to bypass access controls, DRM, or platform restrictions.

Before production deployment, the supported video-source workflow should be reviewed against the applicable platform terms and policies.

---

# 🤝 Contributing

Contributions are welcome once the project reaches a stable open-development stage.

Suggested contribution workflow:

```bash
git clone <repository>
cd SnapLecture

git checkout -b feature/your-feature

# Make changes

git add .
git commit -m "feat: add your feature"

git push origin feature/your-feature
```

Then open a Pull Request.

---

# 📝 Commit Convention

SnapLecture follows a conventional commit style.

Examples:

```text
feat: add pdf generation endpoint
fix: cleanup temporary frames
docs: update architecture documentation
refactor: improve frame processing
test: add pdf service tests
chore: update dependencies
style: improve landing page
perf: optimize frame extraction
```

---

# 📄 License

This project is licensed under the MIT License.

See [`LICENSE`](./LICENSE) for more information.

---

# 👨‍💻 Author

**Vishal Kumar**

Computer Science & Engineering Student
Interested in Data Science, Machine Learning, AI, and Software Development.

---

# ⭐ Project Vision

SnapLecture started with a simple idea:

> **Make learning from long-form video content easier.**

The long-term vision is to evolve SnapLecture from a simple video-to-PDF utility into a privacy-conscious **video learning assistant** capable of turning educational content into useful study material.

```text
        VIDEO
          │
          ▼
     UNDERSTANDING
          │
          ▼
       NOTES
          │
          ▼
      STUDY MATERIAL
```

---

<p align="center">
  <strong>🚧 SnapLecture is actively being built.</strong>
</p>

<p align="center">
  More features, optimizations, and production improvements are coming.
</p>

---

## Development Update

SnapLecture MVP development is actively progressing.

### Current Implementation

- FastAPI backend foundation
- Video input validation
- Frame extraction service
- PDF generation service
- Video-to-PDF processing pipeline
- PDF generation API
- Next.js frontend interface
- Configurable frame capture intervals
- Temporary processing architecture
- Privacy-focused no-permanent-storage design

### Current Status

**?? MVP UNDER ACTIVE DEVELOPMENT**

The next development stage focuses on production hardening, temporary-file lifecycle cleanup, request limits, analytics, testing, Docker configuration, and deployment preparation.

