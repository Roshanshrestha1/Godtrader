"""
Super AI Trader - Agent 3: Price Action / Supply & Demand Agent
Implements price action rules from modules: 2, 10, 14, 19
- Supply/Demand Price Action
- Check Mark Pattern
- Liquidity Strategy (3 Steps)
- First 15 Minutes Manipulation & Reversal
"""

import pandas as pd
from typing import Dict

from agents.base_agent import BaseAgent, SignalResult
from indicators.indicator_library import IndicatorLibrary


class PriceActionSDAgent(BaseAgent):
    """
    Price Action / Supply & Demand Agent
    Identifies high-probability zones and candlestick patterns after liquidity sweeps and opening range manipulation.
    """
    
    def __init__(self):
        super().__init__(
            name="Price Action / Supply & Demand Agent",
            description="Identifies high-probability zones and candlestick patterns after liquidity sweeps and opening range manipulation.",
            module_ids=[2, 10, 14, 19]
        )
        self.il = IndicatorLibrary()
    
    def analyze(self, data: Dict[int, pd.DataFrame], current_price: dict) -> SignalResult:
        """
        Analyze market data and return a trading signal.
        
        Rules evaluated:
        - Supply/Demand zone touch with reversal patterns
        - Liquidity sweep detection
        - First 15-minute manipulation pattern
        - Checkmark pattern (sweep + double bottom/top)
        """
        reasons = []
        score = 0
        
        df_1m = data.get(1)
        df_5m = data.get(5)
        
        if df_1m is None:
            return SignalResult('NEUTRAL', 0, ['No data available'], 0)
        
        close = df_1m['close']
        high = df_1m['high']
        low = df_1m['low']
        open_ = df_1m['open']
        
        current_close = close.iloc[-1]
        current_open = open_.iloc[-1]
        
        # Calculate ATR for reference
        atr = self.il.atr(high, low, close, 14).iloc[-1]
        
        # === SUPPLY/DEMAND ZONE TOUCH (Module 2) ===
        try:
            # Identify recent supply/demand zones (simplified)
            # Demand zone: recent swing low area
            # Supply zone: recent swing high area
            
            lookback = 20
            recent_low = low.rolling(lookback).min().iloc[-1]
            recent_high = high.rolling(lookback).max().iloc[-1]
            
            # Check for bullish engulfing or hammer at demand zone
            hammer = self.il.detect_hammer(open_, high, low, close).iloc[-1]
            engulfing = self.il.detect_engulfing(open_, high, low, close).iloc[-1]
            
            # Distance to recent low (demand zone)
            distance_to_demand = abs(current_close - recent_low) / recent_low * 100
            
            if distance_to_demand < 0.3:  # Within 0.3% of demand zone
                if hammer == 1 or engulfing == 1:
                    score += 3
                    reasons.append(f"Demand zone touch + bullish pattern (+3)")
                else:
                    reasons.append(f"Near demand zone ({recent_low:.5f}), no pattern")
            
            # Distance to recent high (supply zone)
            distance_to_supply = abs(current_close - recent_high) / recent_high * 100
            
            if distance_to_supply < 0.3:  # Within 0.3% of supply zone
                if engulfing == -1:  # Bearish engulfing
                    score -= 3
                    reasons.append(f"Supply zone touch + bearish pattern (-3)")
                else:
                    reasons.append(f"Near supply zone ({recent_high:.5f}), no pattern")
            
            if distance_to_demand >= 0.3 and distance_to_supply >= 0.3:
                reasons.append("Price away from S/D zones")
                
        except Exception as e:
            reasons.append(f"Supply/Demand error: {e}")
        
        # === LIQUIDITY SWEEP (Module 14) ===
        try:
            # Detect sweep below recent low with bullish reversal
            recent_low_20 = low.rolling(20).min().shift(1).iloc[-1]
            recent_high_20 = high.rolling(20).max().shift(1).iloc[-1]
            
            # Sweep low: price goes below recent low but closes above
            if low.iloc[-1] < recent_low_20 and current_close > recent_low_20:
                # Check for bullish reversal candle
                if current_close > current_open:  # Green candle
                    score += 4
                    reasons.append(f"Liquidity sweep below low ({recent_low_20:.5f}) + reversal (+4)")
            
            # Sweep high: price goes above recent high but closes below
            if high.iloc[-1] > recent_high_20 and current_close < recent_high_20:
                # Check for bearish reversal candle
                if current_close < current_open:  # Red candle
                    score -= 4
                    reasons.append(f"Liquidity sweep above high ({recent_high_20:.5f}) + reversal (-4)")
            
            if not (low.iloc[-1] < recent_low_20 or high.iloc[-1] > recent_high_20):
                reasons.append("No liquidity sweep detected")
                
        except Exception as e:
            reasons.append(f"Liquidity Sweep error: {e}")
        
        # === FIRST 15 MINUTES MANIPULATION (Module 19) ===
        try:
            # This works best on intraday data - simplified implementation
            # Look for manipulation candle in first 15 bars of session
            
            if len(df_1m) >= 15:
                first_15_range = high.iloc[-15:].max() - low.iloc[-15:].min()
                avg_range = atr * 5  # Approximate 5-candle average range
                
                # Check if first 15 min range is significant (>20% of expected range)
                if first_15_range >= 0.2 * avg_range:
                    # Red manipulation candle (large red candle)
                    first_candle_open = open_.iloc[-15]
                    first_candle_close = close.iloc[-15]
                    first_candle_range = high.iloc[-15] - low.iloc[-15]
                    
                    if first_candle_close < first_candle_open and first_candle_range >= 0.2 * atr:
                        # Look for break above hammer outside the range
                        if current_close > high.iloc[-15:].max():
                            score += 3
                            reasons.append("15-min red manipulation + breakout (+3)")
                    
                    # Green manipulation candle
                    elif first_candle_close > first_candle_open and first_candle_range >= 0.2 * atr:
                        if current_close < low.iloc[-15:].min():
                            score -= 3
                            reasons.append("15-min green manipulation + breakdown (-3)")
                    else:
                        reasons.append("15-min range formed, waiting for confirmation")
                else:
                    reasons.append("15-min range too small")
            else:
                reasons.append("Insufficient data for 15-min analysis")
                
        except Exception as e:
            reasons.append(f"First 15-min error: {e}")
        
        # === CHECKMARK PATTERN (Module 10) ===
        try:
            # Checkmark: Sweep low of day + double bottom on 5m
            if df_5m is not None and len(df_5m) >= 10:
                m5_low = df_5m['low'].iloc[-1]
                m5_high = df_5m['high'].iloc[-1]
                
                # Find lowest point in recent 5m data
                recent_m5_low = df_5m['low'].rolling(10).min().iloc[-1]
                
                # Check for double bottom pattern
                lows = df_5m['low'].iloc[-10:].values
                middle_idx = len(lows) // 2
                
                # Simple double bottom detection: two similar lows with higher low in between
                if len(lows) >= 6:
                    left_low = lows[:middle_idx].min()
                    middle_high = lows[middle_idx-1:middle_idx+2].max()
                    right_low = lows[middle_idx:].min()
                    
                    # Double bottom: similar lows with higher middle
                    if abs(left_low - right_low) / left_low < 0.002 and middle_high > max(left_low, right_low):
                        # If we had a sweep before this
                        if m5_low < recent_m5_low:
                            score += 3
                            reasons.append("Checkmark: Sweep + double bottom on 5m (+3)")
                
                # Check for double top
                highs = df_5m['high'].iloc[-10:].values
                if len(highs) >= 6:
                    left_high = highs[:middle_idx].max()
                    middle_low = highs[middle_idx-1:middle_idx+2].min()
                    right_high = highs[middle_idx:].max()
                    
                    if abs(left_high - right_high) / left_high < 0.002 and middle_low < min(left_high, right_high):
                        if m5_high > df_5m['high'].rolling(10).max().iloc[-1]:
                            score -= 3
                            reasons.append("Checkmark: Sweep + double top on 5m (-3)")
            else:
                reasons.append("Insufficient 5m data for checkmark")
                
        except Exception as e:
            reasons.append(f"Checkmark pattern error: {e}")
        
        # === DETERMINE SIGNAL ===
        if score >= 3:
            signal = 'BUY'
        elif score <= -3:
            signal = 'SELL'
        else:
            signal = 'NEUTRAL'
        
        # Calculate confidence: min(50 + |score| * 8, 92)
        confidence = min(50 + abs(score) * 8, 92)
        
        return SignalResult(signal, confidence, reasons, score)
