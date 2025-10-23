"""
Trading API Routes
Real-time trading operations with SEBI/NSE compliance
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
import asyncio

from database.connection import get_db
from database.schemas import Order, Position, PortfolioSnapshot, RiskEvent
from app.core.config import settings
from app.services.trading_service import TradingService
from app.services.risk_service import RiskService
from app.models.trading_models import (
    OrderCreate, OrderResponse, OrderStatus, 
    PositionResponse, PortfolioResponse,
    TradingMetrics, RiskMetrics
)

router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                self.active_connections.remove(connection)

manager = ConnectionManager()

@router.get("/health")
async def trading_health():
    """Trading system health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "algo_id": settings.ALGO_ID,
        "strategy_name": settings.STRATEGY_NAME
    }

@router.get("/metrics", response_model=TradingMetrics)
async def get_trading_metrics(db: Session = Depends(get_db)):
    """Get real-time trading metrics"""
    trading_service = TradingService(db)
    return await trading_service.get_trading_metrics()

@router.post("/orders", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):
    """Create a new trading order"""
    trading_service = TradingService(db)
    risk_service = RiskService(db)
    
    # Risk check before order creation
    risk_check = await risk_service.validate_order(order_data)
    if not risk_check["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Risk check failed: {risk_check['reason']}"
        )
    
    # Create order
    order = await trading_service.create_order(order_data)
    
    # Log audit event
    await trading_service.log_audit_event(
        action="ORDER_CREATED",
        resource_type="ORDER",
        resource_id=str(order.id),
        new_values=order_data.dict()
    )
    
    return order

@router.get("/orders", response_model=List[OrderResponse])
async def get_orders(
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get trading orders"""
    trading_service = TradingService(db)
    return await trading_service.get_orders(limit=limit, status=status)

@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, db: Session = Depends(get_db)):
    """Get specific order details"""
    trading_service = TradingService(db)
    order = await trading_service.get_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order

@router.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: str, db: Session = Depends(get_db)):
    """Cancel an order"""
    trading_service = TradingService(db)
    success = await trading_service.cancel_order(order_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to cancel order"
        )
    
    return {"message": "Order cancelled successfully"}

@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(db: Session = Depends(get_db)):
    """Get current positions"""
    trading_service = TradingService(db)
    return await trading_service.get_positions()

@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(db: Session = Depends(get_db)):
    """Get portfolio summary"""
    trading_service = TradingService(db)
    return await trading_service.get_portfolio()

@router.get("/risk", response_model=RiskMetrics)
async def get_risk_metrics(db: Session = Depends(get_db)):
    """Get risk management metrics"""
    risk_service = RiskService(db)
    return await risk_service.get_risk_metrics()

@router.post("/halt")
async def halt_trading(db: Session = Depends(get_db)):
    """Emergency halt all trading"""
    trading_service = TradingService(db)
    await trading_service.halt_trading()
    
    # Broadcast halt message to all WebSocket connections
    await manager.broadcast(json.dumps({
        "type": "SYSTEM_HALT",
        "message": "Trading halted by user",
        "timestamp": datetime.utcnow().isoformat()
    }))
    
    return {"message": "Trading halted successfully"}

@router.post("/resume")
async def resume_trading(db: Session = Depends(get_db)):
    """Resume trading"""
    trading_service = TradingService(db)
    await trading_service.resume_trading()
    
    # Broadcast resume message to all WebSocket connections
    await manager.broadcast(json.dumps({
        "type": "SYSTEM_RESUME",
        "message": "Trading resumed by user",
        "timestamp": datetime.utcnow().isoformat()
    }))
    
    return {"message": "Trading resumed successfully"}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time trading data"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Send real-time data every 2 seconds
            trading_service = TradingService(next(get_db()))
            metrics = await trading_service.get_trading_metrics()
            
            data = {
                "type": "TRADING_METRICS",
                "timestamp": datetime.utcnow().isoformat(),
                "data": metrics.dict()
            }
            
            await manager.send_personal_message(json.dumps(data), websocket)
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
