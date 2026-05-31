# Collaris — Margin & Collateral Intelligence Agent

Real-time margin intelligence for prime brokerage.
Why Collaris:
- A Collar around risk exposure
- Controls margin utilization
- Holds collateral in check
- Tightens when breach approaches

---

## Quick Start

### 1. Backend

```bash
cd collaris

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# or: source .venv/bin/activate  (Mac/Linux)

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
copy .env.example .env
# Edit .env — set OPENAI_API_KEY at minimum
# DATABASE_URL defaults to SQLite (collaris.db) if left as-is

# Seed the database (creates tables + loads 20 synthetic clients)
python -m backend.db.seed

# Start the API server
uvicorn backend.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend

npm install
npm run dev
```

App runs at: http://localhost:5173

---

## Architecture

```
Collaris
├── backend/          FastAPI + LangGraph agent
│   ├── core/         Risk engine, collateral optimizer, stress engine
│   ├── agent/        LangGraph nodes + graph definition
│   ├── api/          REST routes + Pydantic schemas
│   └── db/           SQLAlchemy models + seeder
├── frontend/         React 18 + Vite + Tailwind
│   └── src/
│       ├── components/   UI components (Sidebar, TopBar, tabs)
│       ├── store/        Zustand state
│       ├── hooks/        Data polling + agent stream
│       └── api/          Axios client
└── data/             Seed JSON files
```

## Running Tests

```bash
pytest backend/tests/ -v
```

## Environment Variables

See `.env.example` for all variables. Only `OPENAI_API_KEY` is required for basic operation. `DATABASE_URL` defaults to SQLite.

## Database

The app defaults to **SQLite** (`./collaris.db`) so it works out of the box without PostgreSQL. To use PostgreSQL, set `DATABASE_URL=postgresql://user:pass@host/db` in `.env`.
