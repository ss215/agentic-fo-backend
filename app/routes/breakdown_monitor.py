"""
Breakdown Monitor API Routes
Real-time breakdown detection and alerts
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from database.connection import get_db
from app.services.breakdown_detector import BreakdownDetector, SupportLevel, BreakdownAlert
from app.services.telegram_notifier import TelegramNotifier
from app.services.market_data_fetcher import MarketDataFetcher
from app.core.config import settings

router = APIRouter(prefix="/api/v1/breakdown", tags=["Breakdown Monitor"])

# Global services
detector = BreakdownDetector()
notifier = TelegramNotifier(
    bot_token=getattr(settings, 'TELEGRAM_BOT_TOKEN', None),
    chat_id=getattr(settings, 'TELEGRAM_CHAT_ID', None)
)
data_fetcher = MarketDataFetcher()


class SupportLevelRequest(BaseModel):
    """Request to add a support level"""
    instrument: str
    price: float
    tolerance: float = 0.5
    consolidation_periods: int = 5
    notify_on_breakdown: bool = True


class MonitorStatus(BaseModel):
    """Monitoring status"""
    instrument: str
    is_monitoring: bool
    support_levels: List[float]
    breakdown_count: int
    last_update: datetime


@router.post("/start", response_model=Dict[str, Any])
async def start_monitoring(request: SupportLevelRequest, background_tasks: BackgroundTasks):
    """Start monitoring an instrument for breakdowns"""
    
    # Add support level
    detector.add_support_level(
        instrument=request.instrument,
        price=request.price,
        tolerance=request.tolerance,
        consolidation_periods=request.consolidation_periods
    )
    
    # Start background monitoring
    background_tasks.add_task(monitor_instrument, request.instrument, request.notify_on_breakdown)
    
    return {
        "status": "monitoring_started",
        "instrument": request.instrument,
        "support_level": request.price,
        "tolerance": request.tolerance,
        "message": f"Monitoring started for {request.instrument} at support level {request.price}"
    }


@router.post("/stop")
async def stop_monitoring(instrument: str):
    """Stop monitoring an instrument"""
    
    if instrument in detector.support_levels:
        for support in detector.support_levels[instrument]:
            support.is_active = False
        return {"status": "stopped", "instrument": instrument}
    
    raise HTTPException(status_code=404, detail=f"No active monitoring for {instrument}")


@router.get("/status/{instrument}", response_model=MonitorStatus)
async def get_status(instrument: str):
    """Get monitoring status for an instrument"""
    
    support_levels = detector.get_support_levels(instrument)
    breakdowns = detector.get_breakdowns(instrument)
    
    active_supports = [s.price for s in support_levels if s.is_active]
    
    return MonitorStatus(
        instrument=instrument,
        is_monitoring=len(active_supports) > 0,
        support_levels=active_supports,
        breakdown_count=len(breakdowns),
        last_update=datetime.now()
    )


@router.get("/breakdowns/{instrument}", response_model=List[Dict[str, Any]])
async def get_breakdowns(instrument: str):
    """Get breakdown history for an instrument"""
    
    breakdowns = detector.get_breakdowns(instrument)
    
    return [
        {
            "instrument": b.instrument,
            "support_level": b.support_level,
            "breakdown_price": b.breakdown_price,
            "percentage_drop": ((b.breakdown_price - b.support_level) / b.support_level) * 100,
            "volume": b.volume,
            "volume_increase": b.volume_increase,
            "breakdown_time": b.breakdown_time.isoformat()
        }
        for b in breakdowns
    ]


@router.post("/test-telegram")
async def test_telegram():
    """Test Telegram notification"""
    
    success = notifier.test_connection()
    
    if success:
        return {"status": "success", "message": "Telegram notification sent successfully"}
    else:
        return {"status": "failed", "message": "Failed to send Telegram notification"}


async def monitor_instrument(instrument: str, notify: bool = True):
    """Background task to monitor instrument for breakdowns"""
    import asyncio
    
    while True:
        try:
            # Fetch latest OHLC data
            ohlc_data = await data_fetcher.get_ohlc_data(instrument, "1m", 10)
            
            if ohlc_data:
                # Process latest candle
                latest_candle = ohlc_data[-1]
                
                # Update detector and check for breakdown
                breakdown = detector.update_price(instrument, latest_candle)
                
                if breakdown and notify:
                    # Send Telegram alert
                    notifier.send_breakdown_alert(breakdown)
                    
                    # Store breakdown
                    if instrument not in detector.breakdown_history:
                        detector.breakdown_history[instrument] = []
                    detector.breakdown_history[instrument].append(breakdown)
            
            # Wait 1 minute before next check
            await asyncio.sleep(60)
            
        except Exception as e:
            print(f"Error in monitoring task: {e}")
            await asyncio.sleep(60)
