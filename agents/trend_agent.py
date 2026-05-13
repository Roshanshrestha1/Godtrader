"""
Agent 1: Trend Analysis Agent
Analyzes market trend using EMA, ADX, and price position.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from utils.indicators import ema, adx, calculate_slope


class TrendAgent:
    """
    Agent 1 - Trend Analysis
    
    Responsibilities:
    - Determine primary trend direction using 200 EMA
    - Assess trend strength using ADX
    - Calculate EMA slope for momentum
    - Output: BUY/SELL/HOLD with confidence score
    """
    
    def __init__(self, ema_period: int = 200, adx_period: int = 14, adx_threshold: int = 25):
        self.ema_period = ema_period
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze trend from OHLCV data.
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            Dictionary with signal, confidence, and reasoning
        """
        if len(df) < self.ema_period + 10:
            return {
                'agent': 'TrendAgent',
                'signal': 'HOLD',
                'confidence': 0,
                'reasons': ['Insufficient data for trend analysis'],
                'details': {}
            }
        
        # Calculate indicators
        df['ema_200'] = ema(df['Close'], self.ema_period)
        df['adx'] = adx(df, self.adx_period)
        
        # Get latest values
        current_price = df['Close'].iloc[-1]
        current_ema = df['ema_200'].iloc[-1]
        current_adx = df['adx'].iloc[-1]
        
        # Calculate EMA slope (last 5 periods)
        ema_slope = calculate_slope(df['ema_200'].iloc[-10:], lookback=5).iloc[-1]
        
        reasons = []
        confidence = 0
        signal = 'HOLD'
        
        # Condition 1: Price position relative to 200 EMA
        price_above_ema = current_price > current_ema
        price_below_ema = current_price < current_ema
        
        price_position_pct = ((current_price - current_ema) / current_ema) * 100
        
        if price_above_ema:
            reasons.append(f"Price ({current_price:.2f}) is above 200 EMA ({current_ema:.2f}) → Bullish")
        elif price_below_ema:
            reasons.append(f"Price ({current_price:.2f}) is below 200 EMA ({current_ema:.2f}) → Bearish")
        else:
            reasons.append(f"Price is at 200 EMA → Neutral")
        
        # Condition 2: ADX threshold (trend strength)
        is_trending = current_adx > self.adx_threshold
        
        if is_trending:
            reasons.append(f"ADX is {current_adx:.1f} (> {self.adx_threshold}) → Strong trend present")
        else:
            reasons.append(f"ADX is {current_adx:.1f} (< {self.adx_threshold}) → Market is ranging")
        
        # Condition 3: EMA slope (momentum)
        if ema_slope > 0.001:
            reasons.append(f"200 EMA slope is positive → Upward momentum")
        elif ema_slope < -0.001:
            reasons.append(f"200 EMA slope is negative → Downward momentum")
        else:
            reasons.append(f"200 EMA is flat → No clear momentum")
        
        # Determine signal and confidence
        if price_above_ema and is_trending:
            signal = 'BUY'
            # Base confidence from ADX strength
            confidence = min(50 + (current_adx - self.adx_threshold), 85)
            
            # Boost confidence if EMA slope is positive
            if ema_slope > 0.001:
                confidence += 10
                confidence = min(confidence, 95)
        
        elif price_below_ema and is_trending:
            signal = 'SELL'
            # Base confidence from ADX strength
            confidence = min(50 + (current_adx - self.adx_threshold), 85)
            
            # Boost confidence if EMA slope is negative
            if ema_slope < -0.001:
                confidence += 10
                confidence = min(confidence, 95)
        
        else:
            signal = 'HOLD'
            confidence = 30 if not is_trending else 40
            reasons.append("Market conditions do not support a clear directional trade")
        
        # Ensure confidence is within bounds
        confidence = max(0, min(100, int(confidence)))
        
        return {
            'agent': 'TrendAgent',
            'signal': signal,
            'confidence': confidence,
            'reasons': reasons,
            'details': {
                'price': current_price,
                'ema_200': current_ema,
                'adx': current_adx,
                'ema_slope': ema_slope,
                'price_position_pct': price_position_pct,
                'is_trending': is_trending
            }
        }
