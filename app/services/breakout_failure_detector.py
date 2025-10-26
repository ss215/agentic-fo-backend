"""
Breakout Failure Detection Service
Detects when price breaks out of a range but then immediately fails and breaks down
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BreakoutPhase(str, Enum):
    """Breakout detection phases"""
    CONSOLIDATION = "consolidation"  # Range-bound period
    BREAKOUT_UP = "breakout_up"  # Price breaks above range
    BREAKOUT_DOWN = "breakout_down"  # Price breaks below range
    BREAKOUT_FAILURE_UP = "breakout_failure_up"  # Price breaks down after upside breakout
    BREAKOUT_FAILURE_DOWN = "breakout_failure_down"  # Price breaks up after downside breakout
    SWING_LOW_BROKEN = "swing_low_broken"  # Price breaks previous swing low
    SWING_HIGH_BROKEN = "swing_high_broken"  # Price breaks previous swing high


@dataclass
class RangeLevel:
    """Range consolidation level"""
    upper_bound: float
    lower_bound: float
    start_time: datetime
    end_time: Optional[datetime]
    touch_count: int = 0


@dataclass
class SwingLow:
    """Previous swing low"""
    price: float
    time: datetime
    is_broken: bool = False


@dataclass
class SwingHigh:
    """Previous swing high"""
    price: float
    time: datetime
    is_broken: bool = False


@dataclass
class BreakoutFailureAlert:
    """Breakout failure alert"""
    instrument: str
    range_upper: float
    range_lower: float
    breakout_price: float
    breakdown_price: float
    previous_swing_low: float
    previous_swing_high: float
    swing_low_broken: bool
    swing_high_broken: bool
    breakdown_time: datetime
    candles_for_failure: int  # How many candles it took to fail
    volume_spike: float
    direction: str  # "up_failure" or "down_failure"


class BreakoutFailureDetector:
    """Detects breakout failure patterns"""
    
    def __init__(self):
        self.range_levels: Dict[str, RangeLevel] = {}
        self.swing_lows: Dict[str, SwingLow] = {}
        self.swing_highs: Dict[str, SwingHigh] = {}
        self.breakout_prices: Dict[str, float] = {}
        self.breakout_direction: Dict[str, str] = {}  # "up" or "down"
        self.price_history: Dict[str, List[Dict[str, Any]]] = {}
        self.failure_history: Dict[str, List[BreakoutFailureAlert]] = {}
        self.current_phase: Dict[str, BreakoutPhase] = {}
        
    def detect_range(self, instrument: str, price_data: List[Dict[str, Any]], 
                    lookback_periods: int = 50, min_range_candles: int = 20) -> Optional[RangeLevel]:
        """
        Detect if price is in a consolidation range
        
        Args:
            instrument: Instrument symbol
            price_data: List of OHLC candles
            lookback_periods: Number of candles to analyze
            min_range_candles: Minimum candles in range to be considered
            
        Returns:
            RangeLevel if detected, None otherwise
        """
        if len(price_data) < lookback_periods:
            return None
        
        # Get recent candles
        recent = price_data[-lookback_periods:]
        
        # Find highest high and lowest low in period
        highs = [candle.get('high', 0) for candle in recent]
        lows = [candle.get('low', 0) for candle in recent]
        
        range_upper = max(highs)
        range_lower = min(lows)
        range_width = range_upper - range_lower
        
        # Check if range is tight (consolidation)
        avg_price = (range_upper + range_lower) / 2
        range_percentage = (range_width / avg_price) * 100 if avg_price > 0 else 0
        
        # Consolidation criteria: range should be less than 2% of average price
        if range_percentage < 2.0 and len(recent) >= min_range_candles:
            
            # Count touches of upper and lower bounds
            touch_count = sum(1 for c in recent if c.get('high') >= range_upper * 0.99 or c.get('low') <= range_lower * 1.01)
            
            range_level = RangeLevel(
                upper_bound=range_upper,
                lower_bound=range_lower,
                start_time=recent[0].get('timestamp', datetime.now()),
                end_time=None,
                touch_count=touch_count
            )
            
            logger.info(f"📊 Range detected: {range_lower:.2f} - {range_upper:.2f} ({range_percentage:.2f}% width, {touch_count} touches)")
            
            return range_level
        
        return None
    
    def detect_breakout(self, instrument: str, current_candle: Dict[str, Any], 
                       range_level: RangeLevel) -> bool:
        """
        Detect if price has broken out of the range (up or down)
        
        Args:
            instrument: Instrument symbol
            current_candle: Current OHLC candle
            range_level: Current range consolidation
            
        Returns:
            True if breakout detected
        """
        close_price = current_candle.get('close', 0)
        high_price = current_candle.get('high', 0)
        low_price = current_candle.get('low', 0)
        
        # Check for upside breakout (above upper bound)
        if high_price > range_level.upper_bound:
            range_level.end_time = current_candle.get('timestamp', datetime.now())
            self.breakout_prices[instrument] = close_price
            self.breakout_direction[instrument] = "up"
            self.current_phase[instrument] = BreakoutPhase.BREAKOUT_UP
            
            logger.warning(f"🟢 UPWARD BREAKOUT: {instrument} broke above {range_level.upper_bound:.2f} at {close_price:.2f}")
            
            return True
        
        # Check for downside breakout (below lower bound)
        if low_price < range_level.lower_bound:
            range_level.end_time = current_candle.get('timestamp', datetime.now())
            self.breakout_prices[instrument] = close_price
            self.breakout_direction[instrument] = "down"
            self.current_phase[instrument] = BreakoutPhase.BREAKOUT_DOWN
            
            logger.warning(f"🔴 DOWNWARD BREAKOUT: {instrument} broke below {range_level.lower_bound:.2f} at {close_price:.2f}")
            
            return True
        
        return False
    
    def detect_breakdown_after_breakout(self, instrument: str, current_candle: Dict[str, Any],
                                       range_level: RangeLevel) -> Optional[BreakoutFailureAlert]:
        """
        Detect if price has broken down after breakout (breakout failure)
        
        Handles both patterns:
        - Upward breakout → falls back down (up_failure)
        - Downward breakout → rises back up (down_failure)
        
        Args:
            instrument: Instrument symbol
            current_candle: Current OHLC candle
            range_level: The range that was broken out of
            
        Returns:
            BreakoutFailureAlert if breakdown detected
        """
        if instrument not in self.breakout_prices:
            return None
        
        close_price = current_candle.get('close', 0)
        low_price = current_candle.get('low', 0)
        high_price = current_candle.get('high', 0)
        volume = current_candle.get('volume', 0)
        direction = self.breakout_direction.get(instrument, "up")
        
        # For UPWARD breakout: check if price has fallen back below range upper bound
        # For DOWNWARD breakout: check if price has risen back above range lower bound
        is_failure = False
        
        if direction == "up" and close_price < range_level.upper_bound:
            is_failure = True
        elif direction == "down" and close_price > range_level.lower_bound:
            is_failure = True
        
        if is_failure:
            
            # This is a breakout failure!
            range_level.end_time = current_candle.get('timestamp', datetime.now())
            
            # Count how many candles it took to fail
            candles_for_failure = len(self.price_history.get(instrument, []))
            
            # Calculate average volume
            recent_candles = self.price_history.get(instrument, [])
            if len(recent_candles) > 1:
                avg_volume = sum(c.get('volume', 0) for c in recent_candles[:-1]) / (len(recent_candles) - 1)
                volume_spike = ((volume - avg_volume) / avg_volume * 100) if avg_volume > 0 else 0
            else:
                volume_spike = 0
            
            # Check if it broke previous swing low (for up failures) or swing high (for down failures)
            swing_low_broken = False
            swing_high_broken = False
            previous_swing_low = 0
            previous_swing_high = 0
            
            if direction == "up":
                # Upward breakout failure - check if swing low broken
                if instrument in self.swing_lows:
                    swing_low = self.swing_lows[instrument]
                    if close_price < swing_low.price:
                        swing_low.is_broken = True
                        swing_low_broken = True
                        previous_swing_low = swing_low.price
                        logger.error(f"🔴 SWING LOW BROKEN: Price {close_price:.2f} below swing low {swing_low.price:.2f}")
            elif direction == "down":
                # Downward breakout failure - check if swing high broken
                if instrument in self.swing_highs:
                    swing_high = self.swing_highs[instrument]
                    if close_price > swing_high.price:
                        swing_high.is_broken = True
                        swing_high_broken = True
                        previous_swing_high = swing_high.price
                        logger.warning(f"🟢 SWING HIGH BROKEN: Price {close_price:.2f} above swing high {swing_high.price:.2f}")
            
            alert = BreakoutFailureAlert(
                instrument=instrument,
                range_upper=range_level.upper_bound,
                range_lower=range_level.lower_bound,
                breakout_price=self.breakout_prices[instrument],
                breakdown_price=close_price,
                previous_swing_low=previous_swing_low,
                previous_swing_high=previous_swing_high,
                swing_low_broken=swing_low_broken,
                swing_high_broken=swing_high_broken,
                breakdown_time=current_candle.get('timestamp', datetime.now()),
                candles_for_failure=candles_for_failure,
                volume_spike=volume_spike,
                direction="up_failure" if direction == "up" else "down_failure"
            )
            
            # Store failure
            if instrument not in self.failure_history:
                self.failure_history[instrument] = []
            self.failure_history[instrument].append(alert)
            
            if direction == "up":
                self.current_phase[instrument] = BreakoutPhase.BREAKOUT_FAILURE_UP
                if swing_low_broken:
                    self.current_phase[instrument] = BreakoutPhase.SWING_LOW_BROKEN
            else:
                self.current_phase[instrument] = BreakoutPhase.BREAKOUT_FAILURE_DOWN
                if swing_high_broken:
                    self.current_phase[instrument] = BreakoutPhase.SWING_HIGH_BROKEN
            
            logger.error(f"🔴 BREAKOUT FAILURE DETECTED: {instrument} ({'up' if direction == 'up' else 'down'}) breakout failed")
            
            return alert
        
        return None
    
    def update_swing_low(self, instrument: str, price_data: List[Dict[str, Any]]):
        """Update previous swing low"""
        if len(price_data) < 10:
            return
        
        # Find lowest point in recent history (swing low)
        recent = price_data[-30:]  # Look back 30 candles
        lows = [(c.get('low', 0), c.get('timestamp', datetime.now())) for c in recent]
        lowest = min(lows, key=lambda x: x[0])
        
        swing_low = SwingLow(
            price=lowest[0],
            time=lowest[1],
            is_broken=False
        )
        
        self.swing_lows[instrument] = swing_low
        logger.info(f"📉 Swing low updated: {instrument} at {swing_low.price:.2f}")
    
    def update_swing_high(self, instrument: str, price_data: List[Dict[str, Any]]):
        """Update previous swing high"""
        if len(price_data) < 10:
            return
        
        # Find highest point in recent history (swing high)
        recent = price_data[-30:]  # Look back 30 candles
        highs = [(c.get('high', 0), c.get('timestamp', datetime.now())) for c in recent]
        highest = max(highs, key=lambda x: x[0])
        
        swing_high = SwingHigh(
            price=highest[0],
            time=highest[1],
            is_broken=False
        )
        
        self.swing_highs[instrument] = swing_high
        logger.info(f"📈 Swing high updated: {instrument} at {swing_high.price:.2f}")
    
    def process_candle(self, instrument: str, current_candle: Dict[str, Any]) -> Optional[BreakoutFailureAlert]:
        """
        Process a new candle and check for breakout failure pattern
        
        This is the main method that ties everything together:
        1. Detect if in consolidation range
        2. Detect breakout from range
        3. Detect breakdown after breakout
        4. Check if swing low broken
        5. Alert on swing low break
        
        Returns:
            BreakoutFailureAlert if pattern detected
        """
        # Update price history
        if instrument not in self.price_history:
            self.price_history[instrument] = []
        
        self.price_history[instrument].append(current_candle)
        
        # Keep only recent data
        if len(self.price_history[instrument]) > 200:
            self.price_history[instrument] = self.price_history[instrument][-200:]
        
        # Update swing low and swing high periodically
        if len(self.price_history[instrument]) > 30 and len(self.price_history[instrument]) % 10 == 0:
            self.update_swing_low(instrument, self.price_history[instrument])
            self.update_swing_high(instrument, self.price_history[instrument])
        
        # Check current phase
        phase = self.current_phase.get(instrument, BreakoutPhase.CONSOLIDATION)
        
        # Phase 1: Detect consolidation range
        if phase == BreakoutPhase.CONSOLIDATION:
            range_level = self.detect_range(instrument, self.price_history[instrument])
            if range_level:
                if instrument not in self.range_levels or range_level != self.range_levels[instrument]:
                    self.range_levels[instrument] = range_level
        
        # Phase 2: Detect breakout
        if instrument in self.range_levels:
            range_level = self.range_levels[instrument]
            if self.detect_breakout(instrument, current_candle, range_level):
                return None  # Breakout detected, wait for breakdown
        
        # Phase 3: Detect breakdown after breakout (both up and down breakouts)
        if phase in [BreakoutPhase.BREAKOUT_UP, BreakoutPhase.BREAKOUT_DOWN] and instrument in self.range_levels:
            range_level = self.range_levels[instrument]
            alert = self.detect_breakdown_after_breakout(instrument, current_candle, range_level)
            
            if alert:
                # Reset for next pattern
                self.range_levels.pop(instrument, None)
                self.breakout_prices.pop(instrument, None)
                self.current_phase[instrument] = BreakoutPhase.CONSOLIDATION
                
                return alert
        
        return None
