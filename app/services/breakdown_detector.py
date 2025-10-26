"""
Breakdown Detection Service
Detects price breakdown below support levels for Nifty options trading
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BreakdownStatus(str, Enum):
    """Breakdown detection status"""
    MONITORING = "monitoring"
    BREAKDOWN_DETECTED = "breakdown_detected"
    CONSOLIDATION = "consolidation"
    RECOVERY = "recovery"


@dataclass
class SupportLevel:
    """Support level configuration"""
    price: float
    tolerance: float = 0.5  # Price tolerance in percentage
    min_touches: int = 2  # Minimum touches to consider as valid support
    consolidation_periods: int = 5  # Candles to watch for breakdown
    is_active: bool = True


@dataclass
class BreakdownAlert:
    """Breakdown alert data"""
    instrument: str
    strike_price: float
    breakdown_price: float
    support_level: float
    breakdown_time: datetime
    volume: float
    volume_increase: float  # Volume increase percentage
    candle_body_ratio: float  # Candle body vs total range


class BreakdownDetector:
    """Detects price breakdown below support levels"""
    
    def __init__(self):
        self.support_levels: Dict[str, List[SupportLevel]] = {}
        self.price_history: Dict[str, List[Dict[str, Any]]] = {}
        self.breakdown_history: Dict[str, List[BreakdownAlert]] = {}
        self.active_monitors: Dict[str, BreakdownStatus] = {}
    
    def add_support_level(self, instrument: str, price: float, **kwargs):
        """Add a support level to monitor"""
        if instrument not in self.support_levels:
            self.support_levels[instrument] = []
        
        support = SupportLevel(price=price, **kwargs)
        self.support_levels[instrument].append(support)
        
        logger.info(f"Added support level {price} for {instrument}")
        return support
    
    def update_price(self, instrument: str, price_data: Dict[str, Any]):
        """Update price data and check for breakdown"""
        if instrument not in self.price_history:
            self.price_history[instrument] = []
        
        # Add new price data
        self.price_history[instrument].append(price_data)
        
        # Keep only recent data (last 100 candles)
        if len(self.price_history[instrument]) > 100:
            self.price_history[instrument] = self.price_history[instrument][-100:]
        
        # Check for breakdown if support levels exist
        if instrument in self.support_levels:
            for support in self.support_levels[instrument]:
                if support.is_active:
                    breakdown = self._check_breakdown(instrument, support, price_data)
                    if breakdown:
                        return breakdown
        
        return None
    
    def _check_breakdown(self, instrument: str, support: SupportLevel, current_candle: Dict[str, Any]) -> Optional[BreakdownAlert]:
        """Check if current price action indicates a breakdown"""
        
        current_price = current_candle.get('close', 0)
        high = current_candle.get('high', 0)
        low = current_candle.get('low', 0)
        volume = current_candle.get('volume', 0)
        
        # Calculate support tolerance
        support_lower = support.price * (1 - support.tolerance / 100)
        
        # Condition 1: Price has broken below support level
        if current_price < support_lower:
            
            # Get recent candles for analysis
            recent_candles = self.price_history[instrument][-support.consolidation_periods:]
            
            # Condition 2: Check if this is a decisive breakdown (not just a dip)
            breakdown_confirmed = self._is_decisive_breakdown(recent_candles, support)
            
            if breakdown_confirmed:
                # Calculate breakdown metrics
                candle_body = abs(current_candle.get('close', 0) - current_candle.get('open', 0))
                candle_range = high - low
                body_ratio = candle_body / candle_range if candle_range > 0 else 0
                
                # Calculate volume increase
                avg_volume = sum(c.get('volume', 0) for c in recent_candles[:-1]) / max(len(recent_candles) - 1, 1)
                volume_increase = ((volume - avg_volume) / avg_volume * 100) if avg_volume > 0 else 0
                
                breakdown = BreakdownAlert(
                    instrument=instrument,
                    strike_price=support.price,
                    breakdown_price=current_price,
                    support_level=support.price,
                    breakdown_time=datetime.now(),
                    volume=volume,
                    volume_increase=volume_increase,
                    candle_body_ratio=body_ratio
                )
                
                logger.warning(f"🔴 BREAKDOWN DETECTED: {instrument} broke below {support.price} at {current_price}")
                
                return breakdown
        
        return None
    
    def _is_decisive_breakdown(self, recent_candles: List[Dict[str, Any]], support: SupportLevel) -> bool:
        """Determine if the breakdown is decisive (significant move)"""
        
        if len(recent_candles) < support.consolidation_periods:
            return False
        
        # Count how many candles are below support
        candles_below = 0
        for candle in recent_candles:
            close = candle.get('close', 0)
            if close < support.price * (1 - support.tolerance / 100):
                candles_below += 1
        
        # Require at least 60% of candles to be below support
        breakdown_threshold = int(support.consolidation_periods * 0.6)
        
        return candles_below >= breakdown_threshold
    
    def get_support_levels(self, instrument: str) -> List[SupportLevel]:
        """Get all support levels for an instrument"""
        return self.support_levels.get(instrument, [])
    
    def get_breakdowns(self, instrument: str) -> List[BreakdownAlert]:
        """Get breakdown history for an instrument"""
        return self.breakdown_history.get(instrument, [])
    
    def disable_support_level(self, instrument: str, price: float):
        """Disable a specific support level"""
        if instrument in self.support_levels:
            for support in self.support_levels[instrument]:
                if abs(support.price - price) < 0.1:
                    support.is_active = False
                    logger.info(f"Disabled support level {price} for {instrument}")
                    return True
        return False
    
    def clear_history(self, instrument: str):
        """Clear price and breakdown history for an instrument"""
        self.price_history[instrument] = []
        self.breakdown_history[instrument] = []
        logger.info(f"Cleared history for {instrument}")
