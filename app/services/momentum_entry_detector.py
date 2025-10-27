"""
Momentum Entry Detector
Detects momentum in opposite side (CE/PE) and calculates entry point
Strategy 1: When breakdown happens in CE, detect momentum levels in PE (and vice versa)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MomentumLevel:
    """Momentum level detected in opposite side"""
    asset: str  # CE or PE
    strike: int
    breakdown_level: float
    momentum_candles: List[Dict[str, Any]]
    entry_point: float  # Average of momentum candle lows
    entry_time: datetime
    red_candles_count: int  # Number of red candles in breakdown


class MomentumEntryDetector:
    """Detects momentum in opposite side and calculates entry points"""
    
    def __init__(self):
        self.breakdown_levels: Dict[str, float] = {}
        self.momentum_levels: Dict[str, MomentumLevel] = {}
        self.price_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def mark_breakdown_level(self, instrument: str, breakdown_price: float, 
                             red_candles: List[Dict[str, Any]]):
        """
        Mark breakdown level from red candles
        
        Args:
            instrument: Instrument with breakdown (e.g., "NIFTY 25 Oct 28 26200 CE")
            breakdown_price: Price at which breakdown occurred
            red_candles: List of red candles (minimum 2 for confirmation)
        """
        if len(red_candles) < 2:
            logger.warning("Need at least 2 red candles to mark breakdown level")
            return
        
        # Extract lows from red candles and average them
        lows = [candle.get('low', 0) for candle in red_candles]
        avg_breakdown_level = sum(lows) / len(lows)
        
        self.breakdown_levels[instrument] = avg_breakdown_level
        
        logger.info(f"📊 Breakdown level marked: {instrument} at ₹{avg_breakdown_level:.2f} ({len(red_candles)} red candles)")
    
    def get_opposite_instrument(self, instrument: str) -> str:
        """
        Get opposite instrument (CE <-> PE)
        
        Args:
            instrument: "NIFTY 25 Oct 28 26200 CE" or "NIFTY 25 Oct 28 26200 PE"
            
        Returns:
            Opposite instrument: "NIFTY 25 Oct 28 26200 PE" or "NIFTY 25 Oct 28 26200 CE"
        """
        if " CE" in instrument:
            return instrument.replace(" CE", " PE")
        elif " PE" in instrument:
            return instrument.replace(" PE", " CE")
        else:
            return instrument  # Cannot determine, return as-is
    
    def detect_momentum_in_opposite_side(self, breakdown_instrument: str, 
                                        opposite_price_history: List[Dict[str, Any]],
                                        breakdown_time: datetime,
                                        lookback_minutes: int = 5) -> Optional[MomentumLevel]:
        """
        Detect momentum in opposite side when breakdown happens
        
        Args:
            breakdown_instrument: Instrument where breakdown happened
            opposite_price_history: Price history of opposite instrument (CE or PE)
            breakdown_time: Time when breakdown occurred
            lookback_minutes: Look back this many minutes for momentum detection
            
        Returns:
            MomentumLevel if momentum detected, None otherwise
        """
        if len(opposite_price_history) < 2:
            return None
        
        # Get opposite instrument
        opposite_instrument = self.get_opposite_instrument(breakdown_instrument)
        
        # Extract strike price from instrument name
        try:
            if " CE" in breakdown_instrument or " PE" in breakdown_instrument:
                strike = int(breakdown_instrument.split()[-2])
            else:
                strike = 0
        except:
            strike = 0
        
        # Find candles after breakdown time (momentum candles)
        momentum_candles = []
        for candle in opposite_price_history:
            candle_time = candle.get('timestamp', datetime.now())
            if isinstance(candle_time, str):
                try:
                    candle_time = datetime.fromisoformat(candle_time)
                except:
                    continue
            
            # Check if candle is after breakdown and within lookback window
            if candle_time >= breakdown_time:
                time_diff = (candle_time - breakdown_time).total_seconds() / 60
                if time_diff <= lookback_minutes:
                    momentum_candles.append(candle)
        
        if len(momentum_candles) < 2:
            logger.warning(f"Insufficient momentum candles for {opposite_instrument}")
            return None
        
        # Determine which type of candles to look for based on breakdown direction
        # If CE breaks down, PE gets momentum (green candles)
        # If PE breaks down, CE gets momentum (green candles)
        breakdown_asset = breakdown_instrument.split()[-1]  # "CE" or "PE"
        opposite_asset = opposite_instrument.split()[-1]   # "CE" or "PE"
        
        # For breakdown in CE/PE, we expect momentum in opposite side
        # Momentum = green candles (bullish)
        momentum_candles_to_use = []
        for candle in momentum_candles:
            open_price = candle.get('open', 0)
            close_price = candle.get('close', 0)
            
            # Green candle = bullish momentum
            if close_price > open_price:
                momentum_candles_to_use.append(candle)
        
        if len(momentum_candles_to_use) < 2:
            logger.info(f"No clear momentum (green candles) detected in {opposite_instrument}")
            return None
        
        # Calculate average of lows from momentum candles
        lows = [candle.get('low', 0) for candle in momentum_candles_to_use]
        entry_point = sum(lows) / len(lows)
        
        # Get breakdown level from original instrument
        breakdown_level = self.breakdown_levels.get(breakdown_instrument, 0)
        
        momentum_level = MomentumLevel(
            asset=opposite_instrument.split()[-1],  # "CE" or "PE"
            strike=strike,
            breakdown_level=breakdown_level,
            momentum_candles=momentum_candles_to_use,
            entry_point=entry_point,
            entry_time=momentum_candles[-1].get('timestamp', datetime.now()),
            red_candles_count=len(momentum_candles_to_use)
        )
        
        logger.warning(f"🎯 MOMENTUM DETECTED: {opposite_instrument}")
        logger.info(f"   Breakdown in: {breakdown_instrument} at ₹{breakdown_level:.2f}")
        logger.info(f"   Momentum in: {opposite_instrument} at ₹{entry_point:.2f}")
        logger.info(f"   Entry Point: ₹{entry_point:.2f} (average of {len(momentum_candles_to_use)} momentum candles)")
        
        return momentum_level
    
    def calculate_entry_point(self, breakdown_instrument: str, 
                            opposite_price_history: List[Dict[str, Any]],
                            breakdown_time: datetime,
                            red_candles: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Main method: Calculate entry point in opposite side
        
        Steps:
        1. Mark breakdown level from red candles
        2. Get opposite instrument
        3. Detect momentum in opposite side
        4. Calculate entry point (average of momentum candle lows)
        
        Args:
            breakdown_instrument: Instrument with breakdown
            opposite_price_history: Price history of opposite instrument
            breakdown_time: Time of breakdown
            red_candles: Red candles from breakdown (minimum 2)
            
        Returns:
            Dictionary with entry details
        """
        # Step 1: Mark breakdown level
        self.mark_breakdown_level(breakdown_instrument, red_candles[0].get('close', 0), red_candles)
        
        # Step 2: Detect momentum in opposite side
        momentum_level = self.detect_momentum_in_opposite_side(
            breakdown_instrument,
            opposite_price_history,
            breakdown_time
        )
        
        if momentum_level:
            # Store momentum level
            opposite_instrument = self.get_opposite_instrument(breakdown_instrument)
            self.momentum_levels[opposite_instrument] = momentum_level
            
            return {
                "breakdown_instrument": breakdown_instrument,
                "breakdown_level": momentum_level.breakdown_level,
                "breakdown_asset": breakdown_instrument.split()[-1],  # CE or PE
                "opposite_instrument": opposite_instrument,
                "momentum_asset": momentum_level.asset,
                "strike": momentum_level.strike,
                "entry_point": momentum_level.entry_point,
                "entry_time": momentum_level.entry_time.isoformat(),
                "momentum_candles_count": momentum_level.red_candles_count,
                "signal": f"{momentum_level.asset}"  # CE or PE
            }
        
        return None
    
    def get_entry_point(self, breakdown_instrument: str) -> Optional[MomentumLevel]:
        """Get calculated entry point for opposite instrument"""
        opposite_instrument = self.get_opposite_instrument(breakdown_instrument)
        return self.momentum_levels.get(opposite_instrument)
    
    def is_red_candle(self, candle: Dict[str, Any]) -> bool:
        """Check if candle is red (bearish)"""
        open_price = candle.get('open', 0)
        close_price = candle.get('close', 0)
        return close_price < open_price
    
    def is_green_candle(self, candle: Dict[str, Any]) -> bool:
        """Check if candle is green (bullish)"""
        open_price = candle.get('open', 0)
        close_price = candle.get('close', 0)
        return close_price > open_price
