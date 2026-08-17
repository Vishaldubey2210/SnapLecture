# SnapLecture Development Guide

## Local Development Setup

### Backend (FastAPI)
1. Navigate to `backend/` directory:
   ```bash
   cd backend
   ```
2. Activate python virtual environment:
   ```bash
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend (Next.js)
1. Navigate to `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install node dependencies:
   ```bash
   npm install
   ```
3. Run Next.js development server:
   ```bash
   npm run dev
   ```

### Running Tests
Execute python unit tests from the backend directory:
```bash
python -m unittest discover tests
```
