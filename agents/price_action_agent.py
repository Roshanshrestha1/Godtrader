"""
Agent 3: Price Action Agent
Detects candlestick patterns, liquidity sweeps, and key support/resistance levels.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from utils.indicators import is_bullish_engulfing, is_hammer, is_shooting_star, is_bearish_engulfing


class PriceActionAgent:
    """
    Agent 3 - Price Action Analysis
    
    Responsibilities:
    - Detect candlestick reversal patterns (engulfing, hammer, shooting star)
    - Identify liquidity sweeps (stop hunts)
    - Find key support/resistance levels
    - Output: BUY/SELL/HOLD with confidence score
    """
    
    def __init__(self, sweep_lookback_hours: int = 24):
        self.sweep_lookback_hours = sweep_lookback_hours
    
    def detect_liquidity_sweep(self, df: pd.DataFrame) -> Tuple[bool, str, float]:
        """
        Detect liquidity sweep (stop hunt) patterns.
        
        A liquidity sweep occurs when:
        - Price wicks below previous low (for bullish sweep) or above previous high (for bearish)
        - Then closes back above/below that level
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            Tuple of (is_sweep, sweep_type, sweep_level)
        """
        if len(df) < 10:
            return False, 'none', 0.0
        
        # Get recent candles (last 5)
        recent_df = df.iloc[-5:].copy()
        
        # Calculate previous 24h high/low (approximate using last 24 candles on 1h chart)
        lookback_candles = min(24, len(df) - 1)
        prev_high = df['High'].iloc[-lookback_candles:-1].max()
        prev_low = df['Low'].iloc[-lookback_candles:-1].min()
        
        current_high = df['High'].iloc[-1]
        current_low = df['Low'].iloc[-1]
        current_close = df['Close'].iloc[-1]
        current_open = df['Open'].iloc[-1]
        
        # Bullish sweep: price wicks below prev low but closes above it
        if current_low < prev_low and current_close > prev_low:
            if current_close > current_open:  # Bullish candle
                return True, 'bullish', prev_low
        
        # Bearish sweep: price wicks above prev high but closes below it
        if current_high > prev_high and current_close < prev_high:
            if current_close < current_open:  # Bearish candle
                return True, 'bearish', prev_high
        
        return False, 'none', 0.0
    
    def detect_patterns(self, df: pd.DataFrame) -> Dict[str, bool]:
        """
        Detect candlestick patterns in recent data.
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            Dictionary of pattern detections
        """
        patterns = {
            'bullish_engulfing': False,
            'bearish_engulfing': False,
            'hammer': False,
            'shooting_star': False
        }
        
        if len(df) < 3:
            return patterns
        
        # Check last 3 candles for patterns
        for i in range(-1, -4, -1):
            if i + len(df) < 2:
                continue
            
            subset = df.iloc[i-1:i+1]
            
            if len(subset) >= 2:
                if is_bullish_engulfing(subset).iloc[-1]:
                    patterns['bullish_engulfing'] = True
                if is_bearish_engulfing(subset).iloc[-1]:
                    patterns['bearish_engulfing'] = True
                
                single_candle = df.iloc[i:i+1]
                if is_hammer(single_candle).iloc[-1] if len(single_candle) > 0 else False:
                    patterns['hammer'] = True
                if is_shooting_star(single_candle).iloc[-1] if len(single_candle) > 0 else False:
                    patterns['shooting_star'] = True
        
        # Simplified pattern detection for latest candle
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Bullish engulfing
        if (current['Close'] > current['Open'] and 
            prev['Close'] < prev['Open'] and
            current['Open'] < prev['Close'] and
            current['Close'] > prev['Open']):
            patterns['bullish_engulfing'] = True
        
        # Bearish engulfing
        if (current['Close'] < current['Open'] and 
            prev['Close'] > prev['Open'] and
            current['Open'] > prev['Close'] and
            current['Close'] < prev['Open']):
            patterns['bearish_engulfing'] = True
        
        # Hammer
        body = abs(current['Close'] - current['Open'])
        lower_shadow = min(current['Open'], current['Close']) - current['Low']
        upper_shadow = current['High'] - max(current['Open'], current['Close'])
        
        if body < (current['High'] - current['Low']) * 0.3 and lower_shadow >= body * 2:
            patterns['hammer'] = True
        
        # Shooting star
        if body < (current['High'] - current['Low']) * 0.3 and upper_shadow >= body * 2:
            patterns['shooting_star'] = True
        
        return patterns
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze price action from OHLCV data.
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            Dictionary with signal, confidence, and reasoning
        """
        if len(df) < 10:
            return {
                'agent': 'PriceActionAgent',
                'signal': 'HOLD',
                'confidence': 0,
                'reasons': ['Insufficient data for price action analysis'],
                'details': {}
            }
        
        reasons = []
        confidence = 0
        signal = 'HOLD'
        
        # Detect liquidity sweep
        is_sweep, sweep_type, sweep_level = self.detect_liquidity_sweep(df)
        
        # Detect candlestick patterns
        patterns = self.detect_patterns(df)
        
        # Analyze sweep
        if is_sweep:
            if sweep_type == 'bullish':
                reasons.append(f"Bullish liquidity sweep detected at {sweep_level:.2f} → Stop hunt complete, potential reversal up")
                signal = 'BUY'
                confidence = 60
            else:
                reasons.append(f"Bearish liquidity sweep detected at {sweep_level:.2f} → Stop hunt complete, potential reversal down")
                signal = 'SELL'
                confidence = 60
        
        # Analyze patterns
        if patterns['bullish_engulfing']:
            reasons.append("Bullish engulfing pattern detected → Strong reversal signal")
            if signal == 'BUY':
                confidence += 15
            else:
                signal = 'BUY'
                confidence = 50
        
        if patterns['bearish_engulfing']:
            reasons.append("Bearish engulfing pattern detected → Strong reversal signal")
            if signal == 'SELL':
                confidence += 15
            else:
                signal = 'SELL'
                confidence = 50
        
        if patterns['hammer']:
            reasons.append("Hammer candlestick pattern detected → Potential bullish reversal")
            if signal == 'BUY' or signal == 'HOLD':
                signal = 'BUY'
                confidence = max(confidence, 45)
        
        if patterns['shooting_star']:
            reasons.append("Shooting star candlestick pattern detected → Potential bearish reversal")
            if signal == 'SELL' or signal == 'HOLD':
                signal = 'SELL'
                confidence = max(confidence, 45)
        
        # No significant patterns
        if not is_sweep and not any(patterns.values()):
            reasons.append("No significant price action patterns detected")
            signal = 'HOLD'
            confidence = 20
        
        # Cap confidence
        confidence = max(0, min(100, int(confidence)))
        
        return {
            'agent': 'PriceActionAgent',
            'signal': signal,
            'confidence': confidence,
            'reasons': reasons,
            'details': {
                'liquidity_sweep': is_sweep,
                'sweep_type': sweep_type,
                'sweep_level': sweep_level,
                'patterns': patterns
            }
        }
