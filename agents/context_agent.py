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
        risk_score = 0  # Start with low risk, add points for each risk factor
        
        # Calculate ATR
        df['atr'] = atr(df, self.atr_period)
        current_atr = df['atr'].iloc[-1]
        avg_atr = df['atr'].iloc[-20:].mean()
        current_price = df['Close'].iloc[-1]
        
        # ATR as percentage of price
        atr_pct = (current_atr / current_price) * 100
        
        reasons.append(f"Current ATR: {current_atr:.4f} ({atr_pct:.2f}% of price)")
        
        # Condition 1: Excessive volatility (Fix #4 - Risk Score instead of hard veto)
        if atr_pct > self.max_atr_pct:
            risk_score += 40  # High volatility adds significant risk
            reasons.append(f"⚠️ HIGH VOLATILITY: ATR ({atr_pct:.2f}%) exceeds maximum ({self.max_atr_pct}%) → +40 risk score")
        elif atr_pct > self.max_atr_pct * 0.7:
            risk_score += 20  # Medium volatility adds moderate risk
            reasons.append("Medium volatility detected → +20 risk score")
        else:
            reasons.append("Volatility within acceptable range → +0 risk score")
        
        # Condition 2: Volatility spike (potential news event)
        recent_atr_values = df['atr'].iloc[-5:].values
        avg_recent_atr = np.mean(recent_atr_values)
        
        if avg_recent_atr > avg_atr * 1.5:
            risk_score += 15  # Volatility spike adds risk
            reasons.append("Recent volatility spike detected → Possible news event, +15 risk score")
            if proposed_signal in ['BUY', 'SELL']:
                reasons.append("Consider waiting for volatility to normalize before entering")
        
        # Condition 3: Price gap detection (between last two candles)
        prev_close = df['Close'].iloc[-2]
        current_open = df['Open'].iloc[-1]
        gap_pct = abs(current_open - prev_close) / prev_close * 100
        
        if gap_pct > 1.0:
            risk_score += 15  # Gap adds risk
            reasons.append(f"Price gap detected: {gap_pct:.2f}% → Increased uncertainty, +15 risk score")
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
            risk_score += 10  # Trend exhaustion adds risk
            reasons.append(f"5 consecutive bullish candles → Potential exhaustion, +10 risk score")
            if proposed_signal == 'BUY':
                reasons.append("Consider waiting for pullback before entering long")
        elif consecutive_down >= 5:
            risk_score += 10  # Trend exhaustion adds risk
            reasons.append(f"5 consecutive bearish candles → Potential exhaustion, +10 risk score")
            if proposed_signal == 'SELL':
                reasons.append("Consider waiting for bounce before entering short")
        
        # Condition 5: Support/Resistance proximity (simplified)
        # Check if price is near recent high/low
        recent_high = df['High'].iloc[-20:].max()
        recent_low = df['Low'].iloc[-20:].min()
        
        distance_to_high = (recent_high - current_price) / current_price * 100
        distance_to_low = (current_price - recent_low) / current_price * 100
        
        if distance_to_high < 1.0:
            risk_score += 10  # Near resistance adds risk
            reasons.append(f"Price near 20-period high ({distance_to_high:.2f}% away) → Resistance test, +10 risk score")
            if proposed_signal == 'BUY':
                reasons.append("Buying at resistance is risky; wait for breakout confirmation")
        elif distance_to_low < 1.0:
            risk_score += 10  # Near support adds risk
            reasons.append(f"Price near 20-period low ({distance_to_low:.2f}% away) → Support test, +10 risk score")
            if proposed_signal == 'SELL':
                reasons.append("Selling at support is risky; wait for breakdown confirmation")
        
        # Cap risk score at 100
        risk_score = min(100, risk_score)
        
        # Determine final status based on risk score (Fix #4)
        if risk_score > 80:
            status = 'VETO'
            veto = True
            confidence = 90
            reasons.append(f"\n🚫 FINAL DECISION: VETO - Extreme risk (Risk Score: {risk_score}/100)")
        elif risk_score > 50:
            status = 'APPROVE'
            confidence = 60
            reasons.append(f"\n⚠️ FINAL DECISION: APPROVE with HIGH RISK (Risk Score: {risk_score}/100) - Reduce position size")
        else:
            status = 'APPROVE'
            confidence = 70 + (50 - risk_score)  # Higher confidence for lower risk
            confidence = min(90, confidence)
            reasons.append(f"\n✅ FINAL DECISION: APPROVE - Low risk environment (Risk Score: {risk_score}/100)")
        
        confidence = max(0, min(100, int(confidence)))
        
        return {
            'agent': 'ContextAgent',
            'status': status,
            'risk_score': risk_score,  # New: Risk score for position sizing
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
