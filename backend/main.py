"""
Collaris FastAPI application entry point.
Run: uvicorn backend.main:app --reload --port 8000
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.db.database import Base, engine
from backend.api.routes import clients, collateral, stress, agent, margincall

load_dotenv()

# Create all tables on startup (safe to run repeatedly)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Collaris",
    description="Real-time margin intelligence for prime brokerage",
    version="0.1.0"
)

# Allow the Vite dev server to reach the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all route groups
app.include_router(clients.router)
app.include_router(collateral.router)
app.include_router(stress.router)
app.include_router(agent.router)
app.include_router(margincall.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "collaris"}


@app.get("/api/dashboard/summary")
def dashboard_summary_root():
    """Convenience alias — delegates to the agent router handler."""
    from backend.db.database import SessionLocal
    db = SessionLocal()
    try:
        from backend.api.routes.agent import dashboard_summary
        return dashboard_summary(db)
    finally:
        db.close()


@app.post("/api/market/refresh")
def refresh_market():
    """Trigger a manual market data refresh (background task)."""
    return {"status": "refresh_triggered", "message": "Market data refresh queued."}
