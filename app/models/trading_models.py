"""
Pydantic models for trading operations
Type-safe data models with validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class OrderType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class ProductType(str, Enum):
    MIS = "MIS"  # Intraday
    NRML = "NRML"  # Normal
    CNC = "CNC"  # Cash and Carry

class OrderVariety(str, Enum):
    REGULAR = "regular"
    BRACKET = "bracket"
    COVER = "cover"

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class OrderCreate(BaseModel):
    """Order creation request"""
    instrument_token: str = Field(..., description="Broker instrument token")
    instrument_name: str = Field(..., description="Instrument name")
    exchange: str = Field(..., description="Exchange (NSE/BSE)")
    order_type: OrderType = Field(..., description="BUY or SELL")
    product_type: ProductType = Field(..., description="MIS/NRML/CNC")
    variety: OrderVariety = Field(default=OrderVariety.REGULAR, description="Order variety")
    quantity: int = Field(..., gt=0, description="Order quantity")
    price: Optional[float] = Field(None, ge=0, description="Order price (for limit orders)")
    trigger_price: Optional[float] = Field(None, ge=0, description="Trigger price")
    strategy_name: Optional[str] = Field(None, description="Strategy name")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v
    
    @validator('price')
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Price must be positive')
        return v

class OrderResponse(BaseModel):
    """Order response"""
    id: str
    client_order_id: str
    broker_order_id: Optional[str]
    instrument_token: str
    instrument_name: str
    exchange: str
    order_type: OrderType
    product_type: ProductType
    variety: OrderVariety
    quantity: int
    price: Optional[float]
    trigger_price: Optional[float]
    status: OrderStatus
    filled_quantity: int
    average_price: Optional[float]
    algo_id: str
    strategy_name: Optional[str]
    order_timestamp: datetime
    filled_timestamp: Optional[datetime]
    cancelled_timestamp: Optional[datetime]
    error_message: Optional[str]

class PositionResponse(BaseModel):
    """Position response"""
    id: str
    instrument_token: str
    instrument_name: str
    exchange: str
    quantity: int
    average_price: float
    current_price: Optional[float]
    unrealized_pnl: float
    realized_pnl: float
    margin_used: float
    exposure: float
    created_at: datetime
    updated_at: datetime

class PortfolioResponse(BaseModel):
    """Portfolio response"""
    total_value: float
    available_cash: float
    used_margin: float
    total_pnl: float
    day_pnl: float
    var_95: Optional[float]
    max_drawdown: Optional[float]
    sharpe_ratio: Optional[float]
    positions: List[PositionResponse]
    last_updated: datetime

class TradingMetrics(BaseModel):
    """Trading metrics"""
    active_orders: int
    orders_per_second: float
    total_orders_today: int
    filled_orders_today: int
    rejected_orders_today: int
    success_rate: float
    average_fill_time: float
    total_pnl: float
    day_pnl: float
    margin_usage_percent: float
    exposure_percent: float
    system_health: str
    last_order_time: Optional[datetime]

class RiskMetrics(BaseModel):
    """Risk management metrics"""
    var_95: float
    var_99: float
    max_drawdown: float
    current_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    margin_usage_percent: float
    exposure_percent: float
    concentration_risk: float
    correlation_risk: float
    risk_events_count: int
    last_risk_check: datetime

class SystemHealth(BaseModel):
    """System health status"""
    status: str
    timestamp: datetime
    database_health: str
    redis_health: str
    broker_connection: str
    model_api_connection: str
    uptime_seconds: float
    memory_usage_percent: float
    cpu_usage_percent: float
    disk_usage_percent: float

class AuditLogResponse(BaseModel):
    """Audit log response"""
    id: str
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    ip_address: Optional[str]
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    created_at: datetime

class ConfigurationResponse(BaseModel):
    """Configuration response"""
    key: str
    value: Dict[str, Any]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
