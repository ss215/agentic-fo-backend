"""
Database Schemas for Agentic F&O Execution System
Production-ready database models with proper relationships
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User management table"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trading_sessions = relationship("TradingSession", back_populates="user")
    orders = relationship("Order", back_populates="user")

class TradingSession(Base):
    """Trading session management"""
    __tablename__ = "trading_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_name = Column(String(100), nullable=False)
    broker_type = Column(String(20), nullable=False)  # KITE, UPSTOX
    broker_config = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    is_paper_trading = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="trading_sessions")
    orders = relationship("Order", back_populates="trading_session")
    positions = relationship("Position", back_populates="trading_session")
    portfolio_snapshots = relationship("PortfolioSnapshot", back_populates="trading_session")

class Order(Base):
    """Order management table"""
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    trading_session_id = Column(UUID(as_uuid=True), ForeignKey("trading_sessions.id"), nullable=False)
    
    # Order details
    client_order_id = Column(String(100), unique=True, nullable=False, index=True)
    broker_order_id = Column(String(100), nullable=True, index=True)
    instrument_token = Column(String(50), nullable=False)
    instrument_name = Column(String(100), nullable=False)
    exchange = Column(String(20), nullable=False)  # NSE, BSE
    
    # Order parameters
    order_type = Column(String(20), nullable=False)  # BUY, SELL
    product_type = Column(String(20), nullable=False)  # MIS, NRML, CNC
    variety = Column(String(20), nullable=False)  # regular, bracket, cover
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=True)
    trigger_price = Column(Float, nullable=True)
    
    # Order status
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING, OPEN, COMPLETE, CANCELLED, REJECTED
    filled_quantity = Column(Integer, default=0)
    average_price = Column(Float, nullable=True)
    
    # Risk management
    algo_id = Column(String(50), nullable=False, index=True)
    strategy_name = Column(String(100), nullable=True)
    risk_parameters = Column(JSONB, nullable=True)
    
    # Timestamps
    order_timestamp = Column(DateTime, default=datetime.utcnow)
    filled_timestamp = Column(DateTime, nullable=True)
    cancelled_timestamp = Column(DateTime, nullable=True)
    
    # Broker response
    broker_response = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    trading_session = relationship("TradingSession", back_populates="orders")
    fills = relationship("OrderFill", back_populates="order")
    
    # Indexes
    __table_args__ = (
        Index('idx_orders_user_session', 'user_id', 'trading_session_id'),
        Index('idx_orders_status', 'status'),
        Index('idx_orders_timestamp', 'order_timestamp'),
        Index('idx_orders_algo_id', 'algo_id'),
    )

class OrderFill(Base):
    """Order fill details"""
    __tablename__ = "order_fills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    
    fill_quantity = Column(Integer, nullable=False)
    fill_price = Column(Float, nullable=False)
    fill_timestamp = Column(DateTime, default=datetime.utcnow)
    broker_fill_id = Column(String(100), nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="fills")

class Position(Base):
    """Current positions"""
    __tablename__ = "positions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trading_session_id = Column(UUID(as_uuid=True), ForeignKey("trading_sessions.id"), nullable=False)
    
    instrument_token = Column(String(50), nullable=False)
    instrument_name = Column(String(100), nullable=False)
    exchange = Column(String(20), nullable=False)
    
    # Position details
    quantity = Column(Integer, nullable=False)  # Positive for long, negative for short
    average_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    
    # Risk metrics
    margin_used = Column(Float, default=0.0)
    exposure = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trading_session = relationship("TradingSession", back_populates="positions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('trading_session_id', 'instrument_token', name='uq_position_session_instrument'),
        Index('idx_positions_session', 'trading_session_id'),
        Index('idx_positions_instrument', 'instrument_token'),
    )

class PortfolioSnapshot(Base):
    """Portfolio snapshots for historical tracking"""
    __tablename__ = "portfolio_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trading_session_id = Column(UUID(as_uuid=True), ForeignKey("trading_sessions.id"), nullable=False)
    
    # Portfolio metrics
    total_value = Column(Float, nullable=False)
    available_cash = Column(Float, nullable=False)
    used_margin = Column(Float, nullable=False)
    total_pnl = Column(Float, nullable=False)
    day_pnl = Column(Float, nullable=False)
    
    # Risk metrics
    var_95 = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    
    # Timestamp
    snapshot_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    trading_session = relationship("TradingSession", back_populates="portfolio_snapshots")
    
    # Indexes
    __table_args__ = (
        Index('idx_portfolio_session_timestamp', 'trading_session_id', 'snapshot_timestamp'),
    )

class RiskEvent(Base):
    """Risk management events and alerts"""
    __tablename__ = "risk_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trading_session_id = Column(UUID(as_uuid=True), ForeignKey("trading_sessions.id"), nullable=False)
    
    event_type = Column(String(50), nullable=False)  # MARGIN_CALL, EXPOSURE_LIMIT, VAR_BREACH
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    message = Column(Text, nullable=False)
    parameters = Column(JSONB, nullable=True)
    
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_risk_events_session', 'trading_session_id'),
        Index('idx_risk_events_type', 'event_type'),
        Index('idx_risk_events_severity', 'severity'),
    )

class AuditLog(Base):
    """Immutable audit log for compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Audit details
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    trading_session_id = Column(UUID(as_uuid=True), ForeignKey("trading_sessions.id"), nullable=True)
    
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=True)
    
    # Request details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True)
    
    # Data changes
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_session', 'trading_session_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_timestamp', 'created_at'),
    )

class SystemMetrics(Base):
    """System performance metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # System metrics
    cpu_usage = Column(Float, nullable=False)
    memory_usage = Column(Float, nullable=False)
    disk_usage = Column(Float, nullable=False)
    
    # Trading metrics
    orders_per_second = Column(Float, nullable=False)
    active_orders = Column(Integer, nullable=False)
    total_orders = Column(Integer, nullable=False)
    
    # API metrics
    api_response_time = Column(Float, nullable=False)
    api_requests_per_second = Column(Float, nullable=False)
    api_error_rate = Column(Float, nullable=False)
    
    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_metrics_timestamp', 'recorded_at'),
    )

class Configuration(Base):
    """System configuration"""
    __tablename__ = "configurations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSONB, nullable=False)
    description = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_config_key', 'key'),
        Index('idx_config_active', 'is_active'),
    )
