"""
Database seeder — loads synthetic_clients.json into all tables.
Run with: python -m backend.db.seed
"""
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Allow running as a module from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.db.database import Base, engine, SessionLocal
from backend.db.models import (
    Client, Portfolio, Position, CollateralItem,
    RiskScore, AgentAction, MarginCall
)


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "synthetic_clients.json"


def seed():
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Wipe existing seed data so the script is idempotent
        for model in [MarginCall, AgentAction, RiskScore, CollateralItem, Position, Portfolio, Client]:
            db.query(model).delete()
        db.commit()

        with open(DATA_FILE) as f:
            data = json.load(f)

        for c in data["clients"]:
            # Client
            client = Client(
                id=c["id"],
                name=c["name"],
                strategy=c["strategy"],
                aum_millions=c["aum_millions"],
                status=c["status"],
                created_at=datetime.utcnow() - timedelta(days=180)
            )
            db.add(client)
            db.flush()

            # Portfolio + Positions
            p = c["portfolio"]
            portfolio = Portfolio(
                client_id=c["id"],
                snapshot_time=datetime.utcnow(),
                nav=p["nav"],
                gross_exposure=p["gross_exposure"],
                net_exposure=p["net_exposure"],
                margin_used=p["margin_used"],
                margin_available=p["margin_available"],
                utilization_pct=p["utilization_pct"]
            )
            db.add(portfolio)
            db.flush()

            for pos in c["positions"]:
                db.add(Position(
                    portfolio_id=portfolio.id,
                    ticker=pos["ticker"],
                    asset_class=pos["asset_class"],
                    quantity=pos["quantity"],
                    market_value=pos["market_value"],
                    direction=pos["direction"]
                ))

            # Collateral
            for col in c["collateral"]:
                db.add(CollateralItem(
                    client_id=c["id"],
                    asset_type=col["asset_type"],
                    ticker=col["ticker"],
                    face_value=col["face_value"],
                    market_value=col["market_value"],
                    haircut_pct=col["haircut_pct"],
                    is_pledged=col["is_pledged"],
                    eligible=col["eligible"]
                ))

            # Risk Score
            r = c["risk"]
            db.add(RiskScore(
                client_id=c["id"],
                computed_at=datetime.utcnow(),
                mrs_score=r["mrs_score"],
                utilization_pct=r["utilization_pct"],
                shortfall_millions=r["shortfall_millions"],
                lead_time_hours=r["lead_time_hours"],
                trend=r["trend"],
                var_1d=r["var_1d"],
                stress_worst=r["stress_worst"]
            ))

            # Seed historical risk scores for the 30-day sparkline (7 samples).
            # Breach clients get a deliberate upward utilization trend so the
            # risk engine detects trend="up" (+10 MRS) and recomputes MRS >= 85.
            for i in range(1, 8):
                import random
                if c["status"] == "breach":
                    # Older scores have lower utilization → clear upward slope
                    hist_util = max(0, r["utilization_pct"] - (i * 2))
                    hist_mrs  = max(0, r["mrs_score"] - (i * 4))
                else:
                    noise = random.uniform(-4, 4)
                    hist_util = max(0, min(100, r["utilization_pct"] + noise * 0.5))
                    hist_mrs  = max(0, min(100, r["mrs_score"] + noise))
                db.add(RiskScore(
                    client_id=c["id"],
                    computed_at=datetime.utcnow() - timedelta(days=i * 4),
                    mrs_score=hist_mrs,
                    utilization_pct=hist_util,
                    shortfall_millions=max(0, r["shortfall_millions"]),
                    lead_time_hours=r["lead_time_hours"],
                    trend=r["trend"],
                    var_1d=r["var_1d"],
                    stress_worst=r["stress_worst"]
                ))

            # Seed margin calls for breach clients
            if c["status"] == "breach":
                # One ACTIVE (unresolved) call — shows in the Margin Call tab live view
                db.add(MarginCall(
                    client_id=c["id"],
                    issued_at=datetime.utcnow() - timedelta(minutes=28),
                    shortfall_millions=r["shortfall_millions"],
                    due_by=datetime.utcnow() + timedelta(hours=1, minutes=32),
                    resolved_at=None,
                    resolution_type=None
                ))
                # Ensure >= 4 historical calls so history_adj reaches 15 in MRS formula
                num_historical = max(r.get("call_history_30d", 0), 4)
                for call_num in range(num_historical):
                    issued = datetime.utcnow() - timedelta(days=call_num * 7 + 3)
                    db.add(MarginCall(
                        client_id=c["id"],
                        issued_at=issued,
                        shortfall_millions=r["shortfall_millions"] * 0.8,
                        due_by=issued + timedelta(hours=2),
                        resolved_at=issued + timedelta(hours=1, minutes=45),
                        resolution_type="deposit"
                    ))

        db.commit()
        print(f"Seeded {len(data['clients'])} clients successfully.")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
