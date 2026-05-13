"""
Super AI Trader - Agent 5: Market Context & Safety Filter
Implements safety rules from modules: 20, 21, 22
- Trading Journal & Performance Tracking
- Consolidation Avoidance
- Trading Plan Builder
This agent can veto any trade if market conditions are unfavorable.
"""

import pandas as pd
from typing import Dict
from datetime import datetime, timedelta

from agents.base_agent import BaseAgent, SignalResult
from indicators.indicator_library import IndicatorLibrary


class MarketContextAgent(BaseAgent):
    """
    Market Context & Safety Filter
    Monitors market regime, news, and account guardrails. Can veto any trade.
    """
    
    def __init__(self):
        super().__init__(
            name="Market Context & Safety Filter",
            description="Monitors market regime, news, and account guardrails. Can veto any trade.",
            module_ids=[20, 21, 22]
        )
        self.il = IndicatorLibrary()
        
        # Account state (would be loaded from database in production)
        self.daily_pnl = 0.0
        self.account_balance = 10000.0
        self.daily_loss_limit = 0.03  # 3%
        self.trades_today = 0
        self.max_trades_per_day = 10
    
    def analyze(self, data: Dict[int, pd.DataFrame], current_price: dict) -> SignalResult:
        """
        Analyze market context and return NEUTRAL (all clear) or NO_TRADE (veto).
        
        Rules evaluated:
        - ADX consolidation filter
        - Flat EMA filter
        - High impact news filter (if enabled)
        - Daily loss limit check
        """
        reasons = []
        
        df_1m = data.get(1)
        
        if df_1m is None:
            return SignalResult('NO_TRADE', 100, ['No data available'], 0)
        
        close = df_1m['close']
        high = df_1m['high']
        low = df_1m['low']
        
        # === ADX CONSOLIDATION FILTER (Module 21) ===
        try:
            adx = self.il.adx(high, low, close, 14).iloc[-1]
            
            if adx < 25:
                reasons.append(f"ADX {adx:.1f} < 25: Market consolidating - NO TRADE")
                return SignalResult('NO_TRADE', 100, reasons, 0)
            else:
                reasons.append(f"ADX {adx:.1f} >= 25: Trending market OK")
        except Exception as e:
            reasons.append(f"ADX check error: {e}")
        
        # === FLAT EMA FILTER (Module 21) ===
        try:
            ema_200 = self.il.ema(close, 200)
            
            # Calculate slope over last 20 bars
            if len(ema_200) >= 20:
                ema_current = ema_200.iloc[-1]
                ema_20_bars_ago = ema_200.iloc[-20]
                
                if ema_20_bars_ago != 0:
                    slope = (ema_current - ema_20_bars_ago) / ema_20_bars_ago * 100
                    
                    if abs(slope) < 0.02:  # Less than 0.02% change over 20 bars
                        reasons.append(f"EMA200 flat (slope {slope:.4f}%) - NO TRADE")
                        return SignalResult('NO_TRADE', 100, reasons, 0)
                    else:
                        reasons.append(f"EMA200 slope {slope:.4f}%: Trending OK")
                else:
                    reasons.append("Unable to calculate EMA slope")
            else:
                reasons.append("Insufficient data for EMA slope")
        except Exception as e:
            reasons.append(f"Flat EMA check error: {e}")
        
        # === HIGH IMPACT NEWS FILTER (Module 22) ===
        # Simplified - in production would integrate with economic calendar API
        try:
            news_filter_enabled = False  # Set to True if using news API
            
            if news_filter_enabled:
                # Check if within 30 minutes of high-impact news
                # This would query an economic calendar API
                news_imminent = self._check_news_imminent()
                
                if news_imminent:
                    reasons.append("High-impact news within 30 minutes - NO TRADE")
                    return SignalResult('NO_TRADE', 100, reasons, 0)
                else:
                    reasons.append("No high-impact news imminent")
            else:
                reasons.append("News filter disabled")
        except Exception as e:
            reasons.append(f"News filter error: {e}")
        
        # === DAILY LOSS LIMIT CHECK (Module 20) ===
        try:
            max_daily_loss = self.account_balance * self.daily_loss_limit
            
            if self.daily_pnl < -max_daily_loss:
                reasons.append(f"Daily loss limit reached ({self.daily_pnl:.2f} < {-max_daily_loss:.2f}) - NO TRADE")
                return SignalResult('NO_TRADE', 100, reasons, 0)
            else:
                remaining_loss = max_daily_loss + self.daily_pnl
                reasons.append(f"Daily PnL: {self.daily_pnl:.2f}, remaining limit: {remaining_loss:.2f}")
        except Exception as e:
            reasons.append(f"Daily loss check error: {e}")
        
        # === MAX TRADES PER DAY CHECK ===
        try:
            if self.trades_today >= self.max_trades_per_day:
                reasons.append(f"Max trades per day reached ({self.trades_today}) - NO TRADE")
                return SignalResult('NO_TRADE', 100, reasons, 0)
            else:
                reasons.append(f"Trades today: {self.trades_today}/{self.max_trades_per_day}")
        except Exception as e:
            reasons.append(f"Trade count check error: {e}")
        
        # === TRADING SESSION CHECK ===
        try:
            current_hour = datetime.utcnow().hour
            current_minute = datetime.utcnow().minute
            
            # Avoid trading during low-liquidity periods (e.g., 22:00-01:00 UTC)
            if current_hour >= 22 or current_hour <= 1:
                reasons.append(f"Low liquidity session ({current_hour:02d}:{current_minute:02d} UTC) - CAUTION")
                # Don't veto, just warn
        except Exception as e:
            reasons.append(f"Session check error: {e}")
        
        # All checks passed
        reasons.append("All safety checks passed - trading allowed")
        return SignalResult('NEUTRAL', 100, reasons, 0)
    
    def _check_news_imminent(self) -> bool:
        """
        Check if high-impact news is within 30 minutes.
        In production, this would query an economic calendar API.
        """
        # Placeholder - return False by default
        return False
    
    def update_daily_pnl(self, pnl: float):
        """Update daily PnL after a trade."""
        self.daily_pnl += pnl
    
    def increment_trade_count(self):
        """Increment trade counter after executing a trade."""
        self.trades_today += 1
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at start of new trading day)."""
        self.daily_pnl = 0.0
        self.trades_today = 0
    
    def set_account_balance(self, balance: float):
        """Set the account balance."""
        self.account_balance = balance
    
    def get_status(self) -> dict:
        """Get current agent status."""
        return {
            'daily_pnl': self.daily_pnl,
            'account_balance': self.account_balance,
            'trades_today': self.trades_today,
            'daily_loss_limit_pct': self.daily_loss_limit * 100,
            'max_trades_per_day': self.max_trades_per_day
        }
