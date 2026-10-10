# ResAI — An Evidence-Driven Autonomous Research Assistant

![ResAI Banner](https://img.shields.io/badge/ResAI-v1.0.0-0284c7?style=for-the-badge&logo=brain)
![License](https://img.shields.io/badge/License-MIT-emerald?style=for-the-badge)
![Build](https://img.shields.io/badge/Tests-Passing-brightgreen?style=for-the-badge)

ResAI is a complete, production-minded, end-to-end working AI Research Assistant. It accepts a research question, formulates a multi-step research plan for human approval, executes real web search and scholarly retrieval tool calls, extracts claim-level evidence records, performs cross-source contradiction checks, and generates a structured research report with 100% verified citations.

---

## 🌟 Key Features & Unique Differentiators

- 🤖 **Real Tool-Calling Agent Workflow**: State-driven workflow using 12 typed tools (`web_search`, `fetch_url`, `search_academic_sources`, `calculate_statistics`, `create_comparison_matrix`, `generate_chart`, `validate_citations`, etc.).
- 📜 **Interactive Research Plan Review, Approval & Regeneration**: Shows generated subquestions in the UI before execution. Users can Approve & Start, Edit, or Regenerate the plan with feedback.
- 🔗 **Evidence-to-Conclusion Relational Graph**: Tracks every claim to its supporting quotation, retrieval timestamp, confidence score, and canonical URL.
- ⚡ **Cross-Source Contradiction Lab**: Identifies competing claims across independent primary sources and displays side-by-side analysis.
- 📊 **Dynamic Research Coverage Map**: Calculates subquestion evidence coverage from actual database records.
- 🔍 **Claim-Level Citation Inspector**: Interactive drawer allowing users to inspect raw source quotations and verification timestamps for every report reference.
- 📄 **Multi-Format Exports**: Functional export of reports in PDF, DOCX, Markdown, JSON (Reproducibility Manifest), and CSV.
- 🛡️ **Multi-Layer SSRF & Upload Security**: Restricts URL fetching to public HTTP/HTTPS, blocks private/loopback/cloud metadata IP destinations, and sanitizes document uploads.

---

## 🏗️ Architecture & Technology Stack

### Backend
- **Python 3.12+** / **FastAPI**
- **SQLAlchemy 2.0** (Async ORM) + **Alembic** (Migrations)
- **PostgreSQL** (Production) / **SQLite** (Zero-config local fallback)
- **LangGraph** & Pydantic v2 structured state machine
- **LLM Provider Abstraction**: Gemini API, OpenAI API, or Mock Provider
- **ReportLab** (PDF) & **python-docx** (DOCX)
- **Trafilatura** & **BeautifulSoup** (Clean page extraction)
- **pandas** & **NumPy** (Data analysis)

### Frontend
- **React** + **Vite** + **TypeScript**
- **Tailwind CSS** (Custom glassmorphism design system)
- **Lucide React** icons
- **Recharts** (Performance & evidence visualizations)
- **TanStack Query** (`@tanstack/react-query`)
- **Server-Sent Events (SSE)** for real-time progress timeline updates

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.12+
- Node.js 20+
- npm 10+

### 1. Setup Environment
```bash
# Clone or navigate to directory
cd c:/Users/radha/Documents/AgentX

# Run automated setup script (Windows PowerShell)
.\scripts\setup.ps1

# Or Linux/macOS
bash scripts/setup.sh
```

### 2. Seed Demo Data & Run Tests
```bash
# Seed initial demo research run
.\.venv\Scripts\python.exe scripts/seed_demo.py

# Execute pytest automated test suite (Unit & Integration tests)
.\.venv\Scripts\pytest.exe
```

### 3. Launch Development Servers

**Backend API Server (Terminal 1):**
```bash
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

**Frontend App (Terminal 2):**
```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser!

---

## 🐳 Running with Docker Compose

```bash
docker-compose up --build -d
```
- **Frontend App**: [http://localhost:5173](http://localhost:5173)
- **Backend API Docs**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

---

## 📚 Documentation Links
- [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [API.md](docs/API.md)
- [SECURITY.md](docs/SECURITY.md)
- [DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## 📄 License
MIT License. Built for evidence-driven autonomous research.
