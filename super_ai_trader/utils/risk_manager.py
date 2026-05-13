"""
Super AI Trader - Risk Manager Module
Handles position sizing, stop loss, and take profit calculations.
"""

from typing import Optional


class RiskManager:
    """
    Manages risk parameters for trades including position sizing,
    stop loss, and take profit calculations.
    """
    
    def __init__(self, account_balance: float = 10000.0, 
                 risk_per_trade: float = 0.01,
                 atr_multiplier_sl: float = 1.5,
                 atr_multiplier_tp: float = 3.0):
        """
        Initialize risk manager.
        
        Args:
            account_balance: Current account balance
            risk_per_trade: Percentage of account to risk per trade (default 1%)
            atr_multiplier_sl: ATR multiplier for stop loss (default 1.5)
            atr_multiplier_tp: ATR multiplier for take profit (default 3.0)
        """
        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade
        self.atr_multiplier_sl = atr_multiplier_sl
        self.atr_multiplier_tp = atr_multiplier_tp
        
        # Daily limits
        self.max_daily_drawdown = 0.03  # 3%
        self.daily_pnl = 0.0
        self.trades_today = 0
        self.max_trades_per_day = 10
    
    def calculate_position_size(self, entry_price: float, stop_loss: float, 
                                pip_value: float = 10.0) -> float:
        """
        Calculate position size based on risk parameters.
        
        Formula: lots = risk_amount / (abs(entry - sl) * pip_value)
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            pip_value: Value per pip per lot (default 10 for EURUSD standard lot)
        
        Returns:
            Number of lots to trade
        """
        risk_amount = self.account_balance * self.risk_per_trade
        distance = abs(entry_price - stop_loss)
        
        if distance == 0:
            return 0.0
        
        lots = risk_amount / (distance * pip_value)
        
        # Round to 2 decimal places (standard lot precision)
        return round(lots, 2)
    
    def calculate_stop_loss(self, entry_price: float, atr: float, 
                           direction: str) -> float:
        """
        Calculate stop loss price based on ATR.
        
        Args:
            entry_price: Entry price
            atr: Average True Range value
            direction: 'BUY' or 'SELL'
        
        Returns:
            Stop loss price
        """
        sl_distance = atr * self.atr_multiplier_sl
        
        if direction == 'BUY':
            return entry_price - sl_distance
        else:  # SELL
            return entry_price + sl_distance
    
    def calculate_take_profit(self, entry_price: float, atr: float,
                             direction: str) -> float:
        """
        Calculate take profit price based on ATR.
        
        Args:
            entry_price: Entry price
            atr: Average True Range value
            direction: 'BUY' or 'SELL'
        
        Returns:
            Take profit price
        """
        tp_distance = atr * self.atr_multiplier_tp
        
        if direction == 'BUY':
            return entry_price + tp_distance
        else:  # SELL
            return entry_price - tp_distance
    
    def calculate_risk_reward_ratio(self, entry_price: float, 
                                    stop_loss: float, 
                                    take_profit: float) -> float:
        """
        Calculate risk-reward ratio for a trade.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
        
        Returns:
            Risk-reward ratio (e.g., 2.0 means 2:1 reward to risk)
        """
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk == 0:
            return 0.0
        
        return reward / risk
    
    def check_daily_limit(self) -> tuple:
        """
        Check if daily trading limits have been reached.
        
        Returns:
            Tuple of (can_trade: bool, reason: str)
        """
        max_daily_loss = self.account_balance * self.max_daily_drawdown
        
        if self.daily_pnl < -max_daily_loss:
            return False, f"Daily loss limit reached ({self.daily_pnl:.2f})"
        
        if self.trades_today >= self.max_trades_per_day:
            return False, f"Max trades per day reached ({self.trades_today})"
        
        return True, "Within daily limits"
    
    def update_after_trade(self, pnl: float):
        """
        Update statistics after a trade is completed.
        
        Args:
            pnl: Profit/loss from the trade
        """
        self.daily_pnl += pnl
        self.trades_today += 1
    
    def reset_daily_stats(self):
        """Reset daily statistics for new trading day."""
        self.daily_pnl = 0.0
        self.trades_today = 0
    
    def set_account_balance(self, balance: float):
        """Update account balance."""
        self.account_balance = balance
    
    def get_risk_summary(self) -> dict:
        """Get current risk management summary."""
        can_trade, reason = self.check_daily_limit()
        
        return {
            'account_balance': self.account_balance,
            'risk_per_trade_pct': self.risk_per_trade * 100,
            'risk_amount_per_trade': self.account_balance * self.risk_per_trade,
            'daily_pnl': self.daily_pnl,
            'daily_pnl_pct': (self.daily_pnl / self.account_balance) * 100,
            'trades_today': self.trades_today,
            'max_trades_per_day': self.max_trades_per_day,
            'max_daily_drawdown_pct': self.max_daily_drawdown * 100,
            'can_trade': can_trade,
            'daily_limit_reason': reason
        }
    
    def format_trade_details(self, symbol: str, direction: str, entry: float,
                            stop_loss: float, take_profit: float, 
                            lots: float, atr: float) -> dict:
        """
        Format complete trade details with all risk parameters.
        
        Args:
            symbol: Trading symbol
            direction: 'BUY' or 'SELL'
            entry: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            lots: Position size in lots
            atr: ATR value used
        
        Returns:
            Dictionary with formatted trade details
        """
        risk_amount = abs(entry - stop_loss) * lots * 10  # Approximate pip value
        reward_amount = abs(take_profit - entry) * lots * 10
        rr_ratio = self.calculate_risk_reward_ratio(entry, stop_loss, take_profit)
        
        return {
            'symbol': symbol,
            'direction': direction,
            'entry': entry,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'lots': lots,
            'atr': atr,
            'risk_amount': risk_amount,
            'reward_amount': reward_amount,
            'risk_reward_ratio': rr_ratio,
            'risk_pct': (risk_amount / self.account_balance) * 100
        }
