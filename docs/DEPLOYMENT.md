# ResAI Deployment Guide

## Quick Local Startup

### Option A: Local Development (SQLite + Mock/Live APIs)
```bash
# 1. Setup virtual environment & dependencies
python -m venv .venv
.\.venv\Scripts\pip.exe install -r backend\requirements.txt

# 2. Setup frontend dependencies
cd frontend && npm install && cd ..

# 3. Seed demo data
.\.venv\Scripts\python.exe scripts/seed_demo.py

# 4. Start backend (Terminal 1)
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000

# 5. Start frontend (Terminal 2)
cd frontend && npm run dev
```

### Option B: Production Docker Compose Stack
```bash
docker-compose up --build -d
```
Services:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api/v1/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
