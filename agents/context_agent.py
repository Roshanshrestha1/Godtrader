"""
Agent 5: Context & Risk Agent
Evaluates market context, volatility, and provides veto power on risky trades.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from utils.indicators import atr


class ContextAgent:
    """
    Agent 5 - Context & Risk Analysis
    
    Responsibilities:
    - Assess overall market volatility (ATR)
    - Check for news/events context (simulated via volatility spikes)
    - Evaluate risk-reward potential
    - Provide veto power on excessively risky setups
    - Output: Status (APPROVE/VETO) with reasoning
    """
    
    def __init__(self, atr_period: int = 14, max_atr_pct: float = 3.0):
        self.atr_period = atr_period
        self.max_atr_pct = max_atr_pct
    
    def analyze(self, df: pd.DataFrame, proposed_signal: str, entry_price: float) -> Dict[str, Any]:
        """
        Analyze market context and risk factors.
        
        Args:
            df: DataFrame with OHLCV data
            proposed_signal: The signal proposed by other agents (BUY/SELL/HOLD)
            entry_price: Proposed entry price
        
        Returns:
            Dictionary with status (APPROVE/VETO), confidence, and reasoning
        """
        if len(df) < 20:
            return {
                'agent': 'ContextAgent',
                'status': 'VETO',
                'confidence': 100,
                'reasons': ['Insufficient data for context analysis'],
                'veto': True,
                'details': {}
            }
        
        reasons = []
        veto = False
        
        # Calculate ATR
        df['atr'] = atr(df, self.atr_period)
        current_atr = df['atr'].iloc[-1]
        avg_atr = df['atr'].iloc[-20:].mean()
        current_price = df['Close'].iloc[-1]
        
        # ATR as percentage of price
        atr_pct = (current_atr / current_price) * 100
        
        reasons.append(f"Current ATR: {current_atr:.4f} ({atr_pct:.2f}% of price)")
        
        # Condition 1: Excessive volatility
        if atr_pct > self.max_atr_pct:
            veto = True
            reasons.append(f"⚠️ VOLATILITY VETO: ATR ({atr_pct:.2f}%) exceeds maximum ({self.max_atr_pct}%) → Too risky")
        elif atr_pct > self.max_atr_pct * 0.7:
            reasons.append("High volatility detected → Consider reducing position size")
        else:
            reasons.append("Volatility within acceptable range")
        
        # Condition 2: Volatility spike (potential news event)
        recent_atr_values = df['atr'].iloc[-5:].values
        avg_recent_atr = np.mean(recent_atr_values)
        
        if avg_recent_atr > avg_atr * 1.5:
            reasons.append("Recent volatility spike detected → Possible news event, exercise caution")
            if proposed_signal in ['BUY', 'SELL']:
                reasons.append("Consider waiting for volatility to normalize before entering")
        
        # Condition 3: Price gap detection (between last two candles)
        prev_close = df['Close'].iloc[-2]
        current_open = df['Open'].iloc[-1]
        gap_pct = abs(current_open - prev_close) / prev_close * 100
        
        if gap_pct > 1.0:
            reasons.append(f"Price gap detected: {gap_pct:.2f}% → Increased uncertainty")
            if proposed_signal in ['BUY', 'SELL']:
                reasons.append("Gaps often get filled; wait for confirmation")
        
        # Condition 4: Trend exhaustion check
        # Count consecutive candles in same direction
        consecutive_up = 0
        consecutive_down = 0
        
        for i in range(-1, -6, -1):
            if len(df) >= abs(i):
                if df['Close'].iloc[i] > df['Open'].iloc[i]:
                    consecutive_up += 1
                    consecutive_down = 0
                elif df['Close'].iloc[i] < df['Open'].iloc[i]:
                    consecutive_down += 1
                    consecutive_up = 0
            else:
                break
        
        if consecutive_up >= 5:
            reasons.append(f"5 consecutive bullish candles → Potential exhaustion, be cautious with BUY")
            if proposed_signal == 'BUY':
                reasons.append("Consider waiting for pullback before entering long")
        elif consecutive_down >= 5:
            reasons.append(f"5 consecutive bearish candles → Potential exhaustion, be cautious with SELL")
            if proposed_signal == 'SELL':
                reasons.append("Consider waiting for bounce before entering short")
        
        # Condition 5: Support/Resistance proximity (simplified)
        # Check if price is near recent high/low
        recent_high = df['High'].iloc[-20:].max()
        recent_low = df['Low'].iloc[-20:].min()
        
        distance_to_high = (recent_high - current_price) / current_price * 100
        distance_to_low = (current_price - recent_low) / current_price * 100
        
        if distance_to_high < 1.0:
            reasons.append(f"Price near 20-period high ({distance_to_high:.2f}% away) → Resistance test")
            if proposed_signal == 'BUY':
                reasons.append("Buying at resistance is risky; wait for breakout confirmation")
        elif distance_to_low < 1.0:
            reasons.append(f"Price near 20-period low ({distance_to_low:.2f}% away) → Support test")
            if proposed_signal == 'SELL':
                reasons.append("Selling at support is risky; wait for breakdown confirmation")
        
        # Determine final status
        if veto:
            status = 'VETO'
            confidence = 90
            reasons.append("\n❌ FINAL DECISION: VETO - Trade too risky under current conditions")
        else:
            status = 'APPROVE'
            confidence = 70
            
            # Adjust confidence based on risk factors
            risk_factors = sum([
                atr_pct > self.max_atr_pct * 0.7,
                avg_recent_atr > avg_atr * 1.5,
                gap_pct > 1.0,
                consecutive_up >= 5 or consecutive_down >= 5,
                distance_to_high < 1.0 or distance_to_low < 1.0
            ])
            
            confidence -= risk_factors * 10
            confidence = max(50, confidence)
            
            if risk_factors == 0:
                reasons.append("\n✅ FINAL DECISION: APPROVE - Market conditions favorable")
            else:
                reasons.append(f"\n⚠️ FINAL DECISION: APPROVE with caution ({risk_factors} risk factors identified)")
        
        confidence = max(0, min(100, int(confidence)))
        
        return {
            'agent': 'ContextAgent',
            'status': status,
            'confidence': confidence,
            'reasons': reasons,
            'veto': veto,
            'details': {
                'atr': current_atr,
                'atr_pct': atr_pct,
                'avg_atr': avg_atr,
                'volatility_spike': avg_recent_atr > avg_atr * 1.5,
                'gap_detected': gap_pct > 1.0,
                'gap_pct': gap_pct,
                'consecutive_candles': consecutive_up if consecutive_up > 0 else -consecutive_down,
                'distance_to_high': distance_to_high,
                'distance_to_low': distance_to_low
            }
        }
