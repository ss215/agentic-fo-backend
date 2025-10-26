"""
Telegram Notification Service
Sends breakdown alerts via Telegram bot
"""

import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from app.services.breakdown_detector import BreakdownAlert

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Send notifications to Telegram"""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}" if bot_token else None
        
    def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """Send a text message to Telegram"""
        if not self.api_url or not self.chat_id:
            logger.warning("Telegram not configured, skipping notification")
            return False
        
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Telegram notification sent successfully")
                return True
            else:
                logger.error(f"Failed to send Telegram notification: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
            return False
    
    def send_breakdown_alert(self, alert: BreakdownAlert) -> bool:
        """Send breakdown alert to Telegram"""
        if not self.api_url or not self.chat_id:
            logger.warning("Telegram not configured, skipping breakdown alert")
            return False
        
        # Format breakdown alert message
        message = self._format_breakdown_alert(alert)
        
        return self.send_message(message)
    
    def _format_breakdown_alert(self, alert: BreakdownAlert) -> str:
        """Format breakdown alert as Telegram message"""
        
        # Calculate percentage drop
        percentage_drop = ((alert.breakdown_price - alert.support_level) / alert.support_level) * 100
        
        message = f"""🔴 *BREAKDOWN DETECTED*

*Instrument:* `{alert.instrument}`
*Support Level:* ₹{alert.support_level:.2f}
*Breakdown Price:* ₹{alert.breakdown_price:.2f}
*Drop:* {percentage_drop:.2f}%

*Details:*
• Volume: {alert.volume:,.0f}
• Volume Increase: {alert.volume_increase:.1f}%
• Candle Body Ratio: {alert.candle_body_ratio:.2f}
• Time: {alert.breakdown_time.strftime('%Y-%m-%d %H:%M:%S')}

_Price has broken below key support level!_"""
        
        return message
    
    def send_summary(self, instrument: str, breakdowns: list) -> bool:
        """Send daily summary of breakdowns"""
        if not breakdowns:
            return True
        
        message = f"""📊 *Daily Breakdown Summary*

*Instrument:* `{instrument}`
*Total Breakdowns:* {len(breakdowns)}

*Recent Breakdowns:*
"""
        
        for breakdown in breakdowns[-5:]:  # Last 5 breakdowns
            percentage_drop = ((breakdown.breakdown_price - breakdown.support_level) / breakdown.support_level) * 100
            message += f"• ₹{breakdown.support_level:.2f} → ₹{breakdown.breakdown_price:.2f} ({percentage_drop:.2f}%) @ {breakdown.breakdown_time.strftime('%H:%M')}\n"
        
        return self.send_message(message)
    
    def test_connection(self) -> bool:
        """Test Telegram connection"""
        try:
            message = f"✅ Breakdown Detector is online!\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            return self.send_message(message)
        except Exception as e:
            logger.error(f"Telegram test failed: {e}")
            return False
