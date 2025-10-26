"""
Market Data Fetcher
Fetches real-time and historical data from broker APIs
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class MarketDataFetcher:
    """Fetches market data from broker APIs"""
    
    def __init__(self, broker_api=None):
        self.broker_api = broker_api
    
    async def get_ohlc_data(self, instrument: str, interval: str = "1m", count: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch OHLC (Open, High, Low, Close) data
        
        Args:
            instrument: Instrument symbol (e.g., NIFTY 25 Oct 28 25600 CE)
            interval: Time interval (1m, 5m, 15m, 1h, 1d)
            count: Number of candles to fetch
            
        Returns:
            List of OHLC data dictionaries
        """
        try:
            if self.broker_api:
                # Use real broker API
                data = await self._fetch_from_broker(instrument, interval, count)
            else:
                # Mock data for testing
                data = self._generate_mock_data(instrument, interval, count)
            
            logger.info(f"Fetched {len(data)} candles for {instrument}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching OHLC data: {e}")
            return []
    
    async def _fetch_from_broker(self, instrument: str, interval: str, count: int) -> List[Dict[str, Any]]:
        """Fetch data from real broker API (Kite/Zerodha)"""
        # TODO: Implement real broker API integration
        # Example structure:
        # data = broker_api.historical(instrument, from_date, to_date, interval)
        return []
    
    def _generate_mock_data(self, instrument: str, interval: str, count: int) -> List[Dict[str, Any]]:
        """Generate mock OHLC data for testing"""
        
        base_time = datetime.now() - timedelta(minutes=count)
        interval_minutes = self._parse_interval(interval)
        
        mock_data = []
        base_price = 267.5  # Example support level
        
        for i in range(count):
            timestamp = base_time + timedelta(minutes=i * interval_minutes)
            
            # Generate realistic candle with occasional breakdowns
            open_price = base_price + (i * 0.5) - 30  # Slight upward trend with volatility
            close_price = open_price + (i % 7 - 3) * 2  # Some volatility
            
            # Simulate breakdown around candle 50-60
            if 50 <= i <= 60:
                close_price = open_price - 10  # Breakdown simulation
            elif i > 60:
                close_price = open_price - 15  # Continued breakdown
            
            high = max(open_price, close_price) + abs(i % 5 - 2)
            low = min(open_price, close_price) - abs(i % 5 - 2)
            
            candle = {
                'timestamp': timestamp,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close_price, 2),
                'volume': int(10000 + (i % 20) * 500),  # Varying volume
            }
            
            mock_data.append(candle)
        
        return mock_data
    
    def _parse_interval(self, interval: str) -> int:
        """Parse interval string to minutes"""
        interval_map = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '1d': 1440
        }
        return interval_map.get(interval.lower(), 1)
    
    async def get_live_price(self, instrument: str) -> Optional[Dict[str, Any]]:
        """Get current live price"""
        try:
            # Get latest candle
            ohlc_data = await self.get_ohlc_data(instrument, "1m", 1)
            if ohlc_data:
                latest = ohlc_data[-1]
                return {
                    'bid': latest.get('close', 0) - 0.5,
                    'ask': latest.get('close', 0) + 0.5,
                    'last': latest.get('close', 0),
                    'timestamp': latest.get('timestamp', datetime.now())
                }
        except Exception as e:
            logger.error(f"Error fetching live price: {e}")
        
        return None
