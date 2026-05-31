"""
SQLAlchemy ORM models for Collaris.
Every table maps 1-to-1 with a business concept defined in CLAUDE.md §4.
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Boolean, Integer,
    DateTime, ForeignKey, JSON, Text
)
from sqlalchemy.orm import relationship
from .database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(String(10), primary_key=True)          # "C001"
    name = Column(String(100), nullable=False)
    strategy = Column(String(100), nullable=False)
    aum_millions = Column(Float, nullable=False)
    status = Column(String(20), default="normal")       # breach | warning | normal
    created_at = Column(DateTime, default=datetime.utcnow)

    portfolios = relationship("Portfolio", back_populates="client", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScore", back_populates="client", cascade="all, delete-orphan")
    collateral_items = relationship("CollateralItem", back_populates="client", cascade="all, delete-orphan")
    agent_actions = relationship("AgentAction", back_populates="client", cascade="all, delete-orphan")
    margin_calls = relationship("MarginCall", back_populates="client", cascade="all, delete-orphan")


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(10), ForeignKey("clients.id"), nullable=False)
    snapshot_time = Column(DateTime, default=datetime.utcnow)
    nav = Column(Float)
    gross_exposure = Column(Float)
    net_exposure = Column(Float)
    margin_used = Column(Float)
    margin_available = Column(Float)
    utilization_pct = Column(Float)

    client = relationship("Client", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    ticker = Column(String(20))
    asset_class = Column(String(30))   # equity | bond | etf | fx | commodity
    quantity = Column(Float)
    market_value = Column(Float)       # negative = short
    direction = Column(String(10))     # long | short

    portfolio = relationship("Portfolio", back_populates="positions")


class CollateralItem(Base):
    __tablename__ = "collateral_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(10), ForeignKey("clients.id"), nullable=False)
    asset_type = Column(String(50))    # matches keys in haircut_tables.json
    ticker = Column(String(20))
    face_value = Column(Float)
    market_value = Column(Float)
    haircut_pct = Column(Float)
    is_pledged = Column(Boolean, default=False)
    eligible = Column(Boolean, default=True)

    client = relationship("Client", back_populates="collateral_items")


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(10), ForeignKey("clients.id"), nullable=False)
    computed_at = Column(DateTime, default=datetime.utcnow)
    mrs_score = Column(Float)
    utilization_pct = Column(Float)
    shortfall_millions = Column(Float, default=0.0)
    lead_time_hours = Column(Float)
    trend = Column(String(10))         # up | down | stable
    var_1d = Column(Float)
    stress_worst = Column(Float)

    client = relationship("Client", back_populates="risk_scores")


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(10), ForeignKey("clients.id"), nullable=False)
    action_type = Column(String(30))   # monitor | alert | memo | escalate | optimize
    triggered_at = Column(DateTime, default=datetime.utcnow)
    memo_text = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)
    status = Column(String(20), default="pending")   # pending | sent | acknowledged

    client = relationship("Client", back_populates="agent_actions")


class MarginCall(Base):
    __tablename__ = "margin_calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(10), ForeignKey("clients.id"), nullable=False)
    issued_at = Column(DateTime, default=datetime.utcnow)
    shortfall_millions = Column(Float)
    due_by = Column(DateTime)
    resolved_at = Column(DateTime, nullable=True)
    resolution_type = Column(String(30), nullable=True)  # deposit | substitution | reduction

    client = relationship("Client", back_populates="margin_calls")
