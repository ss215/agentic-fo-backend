"""
Breakout Failure Monitor API Routes
Detects breakout failures and swing low breaks
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from database.connection import get_db
from app.services.breakout_failure_detector import (
    BreakoutFailureDetector, 
    BreakoutFailureAlert,
    BreakoutPhase
)
from app.services.telegram_notifier import TelegramNotifier
from app.services.market_data_fetcher import MarketDataFetcher
from app.services.momentum_entry_detector import MomentumEntryDetector
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/breakout-failure", tags=["Breakout Failure Monitor"])

# Global services
detector = BreakoutFailureDetector()
momentum_detector = MomentumEntryDetector()
notifier = TelegramNotifier(
    bot_token=getattr(settings, 'TELEGRAM_BOT_TOKEN', None),
    chat_id=getattr(settings, 'TELEGRAM_CHAT_ID', None)
)
data_fetcher = MarketDataFetcher()


class MonitorRequest(BaseModel):
    """Request to start monitoring"""
    instrument: str
    notify_on_failure: bool = True


class MonitorStatus(BaseModel):
    """Monitoring status"""
    instrument: str
    is_monitoring: bool
    current_phase: str
    range_detected: bool
    range_upper: Optional[float]
    range_lower: Optional[float]
    failure_count: int
    last_update: datetime


@router.post("/start", response_model=Dict[str, Any])
async def start_monitoring(request: MonitorRequest, background_tasks: BackgroundTasks):
    """Start monitoring an instrument for breakout failures"""
    
    # Start background monitoring
    background_tasks.add_task(monitor_instrument, request.instrument, request.notify_on_failure)
    
    return {
        "status": "monitoring_started",
        "instrument": request.instrument,
        "message": f"Monitoring started for {request.instrument} - detecting breakout failures and swing low breaks"
    }


@router.post("/stop")
async def stop_monitoring(instrument: str):
    """Stop monitoring an instrument"""
    
    if instrument in detector.current_phase:
        detector.current_phase.pop(instrument, None)
        detector.range_levels.pop(instrument, None)
        detector.breakout_prices.pop(instrument, None)
        
        return {"status": "stopped", "instrument": instrument}
    
    raise HTTPException(status_code=404, detail=f"No active monitoring for {instrument}")


@router.get("/status/{instrument}", response_model=MonitorStatus)
async def get_status(instrument: str):
    """Get monitoring status for an instrument"""
    
    phase = detector.current_phase.get(instrument, BreakoutPhase.CONSOLIDATION)
    range_level = detector.range_levels.get(instrument)
    failures = detector.failure_history.get(instrument, [])
    
    return MonitorStatus(
        instrument=instrument,
        is_monitoring=instrument in detector.current_phase or instrument in detector.range_levels,
        current_phase=phase.value,
        range_detected=range_level is not None,
        range_upper=range_level.upper_bound if range_level else None,
        range_lower=range_level.lower_bound if range_level else None,
        failure_count=len(failures),
        last_update=datetime.now()
    )


@router.get("/failures/{instrument}", response_model=List[Dict[str, Any]])
async def get_failures(instrument: str):
    """Get breakout failure history for an instrument"""
    
    failures = detector.failure_history.get(instrument, [])
    
    return [
        {
            "instrument": f.instrument,
            "range_upper": f.range_upper,
            "range_lower": f.range_lower,
            "breakout_price": f.breakout_price,
            "breakdown_price": f.breakdown_price,
            "percentage_drop": ((f.breakdown_price - f.breakout_price) / f.breakout_price) * 100,
            "swing_low_broken": f.swing_low_broken,
            "previous_swing_low": f.previous_swing_low,
            "candles_for_failure": f.candles_for_failure,
            "failure_time": f.breakdown_time.isoformat()
        }
        for f in failures
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
    """Background task to monitor instrument for breakout failures"""
    import asyncio
    
    while True:
        try:
            # Fetch latest OHLC data
            ohlc_data = await data_fetcher.get_ohlc_data(instrument, "1m", 100)
            
            if ohlc_data and len(ohlc_data) > 0:
                # Get latest candle
                latest_candle = ohlc_data[-1]
                
                # Process candle and check for breakout failure
                failure_alert = detector.process_candle(instrument, latest_candle)
                
                if failure_alert and notify:
                    # Get opposite instrument (CE <-> PE)
                    opposite_instrument = momentum_detector.get_opposite_instrument(instrument)
                    
                    # Calculate momentum entry point in opposite side
                    entry_info = None
                    try:
                        # Get recent candles for breakdown level marking
                        recent_candles = ohlc_data[-5:] if len(ohlc_data) >= 5 else ohlc_data
                        
                        # Identify the breakdown/failure candles
                        # For breakout failure: these would be the candles that reversed after breakout
                        failure_candles = []
                        for candle in recent_candles:
                            open_price = candle.get('open', 0)
                            close_price = candle.get('close', 0)
                            # Red candles for up failure, green for down failure
                            if failure_alert.direction == "up_failure" and close_price < open_price:
                                failure_candles.append(candle)
                            elif failure_alert.direction == "down_failure" and close_price > open_price:
                                failure_candles.append(candle)
                        
                        if len(failure_candles) >= 2:
                            # Fetch opposite side data
                            opposite_ohlc = await data_fetcher.get_ohlc_data(opposite_instrument, "1m", 50)
                            
                            if opposite_ohlc:
                                entry_info = momentum_detector.calculate_entry_point(
                                    instrument,
                                    opposite_ohlc,
                                    failure_alert.breakdown_time,
                                    failure_candles
                                )
                    except Exception as e:
                        logger.error(f"Error calculating momentum entry for breakout failure: {e}")
                    
                    # Send Telegram alert with momentum entry info
                    notifier.send_breakout_failure_alert_with_momentum(failure_alert, entry_info)
            
            # Wait 1 minute before next check
            await asyncio.sleep(60)
            
        except Exception as e:
            print(f"Error in breakout failure monitoring task: {e}")
            await asyncio.sleep(60)
