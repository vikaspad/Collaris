"""
Agent routes — trigger runs, stream reasoning, generate memos, fetch logs.
POST /api/agent/run/{client_id}
GET  /api/agent/log/{client_id}
POST /api/agent/memo/{client_id}
GET  /api/agent/stream/{client_id}   ← SSE
"""
import asyncio
import json
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.db.database import get_db
from backend.db.models import Client, AgentAction
from backend.api.schemas.client import AgentActionSchema
from backend.api.schemas.agent import MemoRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/run/{client_id}")
async def run_agent(client_id: str, db: Session = Depends(get_db)):
    """
    Trigger the LangGraph agent for a specific client.
    Runs asynchronously and saves results to AgentAction table.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    try:
        from backend.agent.graph import run_agent_for_client
        result = await run_agent_for_client(client_id, db)
        return {
            "status": "completed",
            "client_id": client_id,
            "action_tier": result.get("action_tier"),
            "memo_draft": result.get("memo_draft", ""),
            "agent_log": result.get("agent_log", []),
            "recommendations": result.get("recommendations", []),
        }
    except Exception as e:
        logger.error(f"Agent run failed for {client_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Agent run failed: {str(e)}")


@router.get("/log/{client_id}", response_model=list[AgentActionSchema])
def get_agent_log(client_id: str, limit: int = 20, db: Session = Depends(get_db)):
    """Recent agent actions for a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    return (
        db.query(AgentAction)
        .filter(AgentAction.client_id == client_id)
        .order_by(desc(AgentAction.triggered_at))
        .limit(limit)
        .all()
    )


@router.post("/memo/{client_id}")
async def generate_memo(client_id: str, req: MemoRequest, db: Session = Depends(get_db)):
    """
    Generate a margin call or advisory memo for a client using the LLM.
    Saves the result as an AgentAction and returns the text.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    try:
        from backend.agent.nodes.memo_node import generate_memo_text
        memo = await generate_memo_text(client_id, req.type, db)
        return {"memo_text": memo, "type": req.type, "client_id": client_id}
    except Exception as e:
        logger.error(f"Memo generation failed for {client_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Memo generation failed: {str(e)}")


@router.get("/stream/{client_id}")
async def stream_agent(client_id: str, db: Session = Depends(get_db)):
    """
    SSE stream of agent reasoning steps.
    Frontend connects here to get real-time thought process updates.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    async def event_generator():
        """Pulls from the agent graph and yields SSE-formatted events."""
        try:
            from backend.agent.graph import stream_agent_for_client
            async for step in stream_agent_for_client(client_id, db):
                data = json.dumps(step)
                yield f"data: {data}\n\n"
                await asyncio.sleep(0)   # yield control to the event loop
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: {\"done\": true}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    """Global metrics for the StatBar."""
    from sqlalchemy import func
    from backend.db.models import RiskScore

    clients = db.query(Client).all()
    breach = sum(1 for c in clients if c.status == "breach")
    warning = sum(1 for c in clients if c.status == "warning")
    normal = sum(1 for c in clients if c.status == "normal")

    # Sum shortfalls from latest risk scores
    subq = (
        db.query(RiskScore.client_id, func.max(RiskScore.computed_at).label("latest"))
        .group_by(RiskScore.client_id)
        .subquery()
    )
    latest_risks = (
        db.query(RiskScore)
        .join(subq, (RiskScore.client_id == subq.c.client_id) & (RiskScore.computed_at == subq.c.latest))
        .all()
    )

    total_shortfall = sum(r.shortfall_millions for r in latest_risks)
    top = max(latest_risks, key=lambda r: r.mrs_score, default=None)

    return {
        "total_clients": len(clients),
        "breach_count": breach,
        "warning_count": warning,
        "normal_count": normal,
        "total_shortfall_millions": round(total_shortfall, 2),
        "highest_mrs_client": top.client_id if top else None,
        "highest_mrs_score": top.mrs_score if top else None
    }
