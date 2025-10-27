"""
Telegram Notification Service
Sends breakdown alerts via Telegram bot
"""

import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime

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
    
    def send_breakdown_alert(self, alert) -> bool:
        """Send breakdown alert to Telegram"""
        if not self.api_url or not self.chat_id:
            logger.warning("Telegram not configured, skipping breakdown alert")
            return False
        
        # Format breakdown alert message
        message = self._format_breakdown_alert(alert)
        
        return self.send_message(message)
    
    def send_breakout_failure_alert(self, alert) -> bool:
        """Send breakout failure alert to Telegram"""
        if not self.api_url or not self.chat_id:
            logger.warning("Telegram not configured, skipping breakout failure alert")
            return False
        
        message = self._format_breakout_failure_alert(alert)
        return self.send_message(message)
    
    def send_breakdown_alert_with_momentum(self, breakdown_alert, entry_info: Optional[Dict[str, Any]] = None) -> bool:
        """Send breakdown alert with momentum entry point"""
        if not self.api_url or not self.chat_id:
            logger.warning("Telegram not configured, skipping breakdown alert")
            return False
        
        message = self._format_breakdown_alert(breakdown_alert)
        
        # Add momentum entry info if available
        if entry_info:
            momentum_msg = f"""

🎯 *MOMENTUM ENTRY DETECTED*

*Opposite Side:*
• Instrument: {entry_info['opposite_instrument']}
• Entry Point: ₹{entry_info['entry_point']:.2f}
• Momentum Candles: {entry_info['momentum_candles_count']}
• Breakdown Level (Orig): ₹{entry_info['breakdown_level']:.2f}

*Signal:* {entry_info['signal']}
*Time:* {entry_info['entry_time']}

_Entry point calculated from momentum candles!_"""
            message = message + momentum_msg
        
        return self.send_message(message)
    
    def send_breakout_failure_alert_with_momentum(self, failure_alert, entry_info: Optional[Dict[str, Any]] = None) -> bool:
        """Send breakout failure alert with momentum entry point"""
        if not self.api_url or not self.chat_id:
            logger.warning("Telegram not configured, skipping breakout failure alert")
            return False
        
        message = self._format_breakout_failure_alert(failure_alert)
        
        # Add momentum entry info if available
        if entry_info:
            momentum_msg = f"""

🎯 *MOMENTUM ENTRY DETECTED*

*Opposite Side:*
• Instrument: {entry_info['opposite_instrument']}
• Entry Point: ₹{entry_info['entry_point']:.2f}
• Momentum Candles: {entry_info['momentum_candles_count']}
• Breakdown Level (Orig): ₹{entry_info['breakdown_level']:.2f}

*Signal:* {entry_info['signal']}
*Time:* {entry_info['entry_time']}

_Entry point calculated from momentum candles!_"""
            message = message + momentum_msg
        
        return self.send_message(message)
    
    def _format_breakdown_alert(self, alert) -> str:
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
    
    def _format_breakout_failure_alert(self, alert) -> str:
        """Format breakout failure alert as Telegram message"""
        
        # Calculate percentage change
        if alert.direction == "up_failure":
            percentage_change = ((alert.breakdown_price - alert.breakout_price) / alert.breakout_price) * 100
            signal = "SELL" if alert.swing_low_broken else "WATCH"
            direction_emoji = "🔴"
        else:
            percentage_change = ((alert.breakdown_price - alert.breakout_price) / alert.breakout_price) * 100
            signal = "BUY" if alert.swing_high_broken else "WATCH"
            direction_emoji = "🟢"
        
        swing_msg = ""
        if alert.swing_low_broken:
            swing_msg = f"\n🔴 *SWING LOW BROKEN:* ₹{alert.previous_swing_low:.2f}"
        elif alert.swing_high_broken:
            swing_msg = f"\n🟢 *SWING HIGH BROKEN:* ₹{alert.previous_swing_high:.2f}"
        
        message = f"""{direction_emoji} *BREAKOUT FAILURE DETECTED* ({alert.direction})

*Instrument:* `{alert.instrument}`

*Range:*
• Upper: ₹{alert.range_upper:.2f}
• Lower: ₹{alert.range_lower:.2f}

*Breakout & Breakdown:*
• Breakout Price: ₹{alert.breakout_price:.2f}
• Breakdown Price: ₹{alert.breakdown_price:.2f}
• Change: {percentage_change:.2f}%
{swing_msg}

*Details:*
• Candles to Fail: {alert.candles_for_failure}
• Volume Spike: {alert.volume_spike:.1f}%
• Time: {alert.breakdown_time.strftime('%Y-%m-%d %H:%M:%S')}
• Signal: {signal}

_Price broke out but immediately reversed!_"""
        
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
