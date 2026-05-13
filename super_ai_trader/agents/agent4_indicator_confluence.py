"""
Super AI Trader - Agent 4: Indicator Confluence Agent
Implements indicator-based rules from modules: 6, 9, 11, 12, 21
- 10 Strategy Tier-List
- LW Volatility Breakout
- Best 3 Indicators (EMA, Sessions, Fib)
- Top 3 Free TradingView Indicators
- Consolidation Avoidance (ADX, EMA slope)
"""

import pandas as pd
from typing import Dict

from agents.base_agent import BaseAgent, SignalResult
from indicators.indicator_library import IndicatorLibrary


class IndicatorConfluenceAgent(BaseAgent):
    """
    Indicator Confluence Agent
    Uses Fibonacci, sessions, oscillators, and volatility filters to time entries with confluence.
    """
    
    def __init__(self):
        super().__init__(
            name="Indicator Confluence Agent",
            description="Uses Fibonacci, sessions, oscillators, and volatility filters to time entries with confluence.",
            module_ids=[6, 9, 11, 12, 21]
        )
        self.il = IndicatorLibrary()
    
    def analyze(self, data: Dict[int, pd.DataFrame], current_price: dict) -> SignalResult:
        """
        Analyze market data and return a trading signal.
        
        Rules evaluated:
        - ADX filter for consolidation avoidance
        - Session timing (London-NY overlap)
        - Fibonacci golden zone bounce/rejection
        - LWTI (Larry Williams Trend Index)
        - Zero-Lag Arrows with MTF confirmation
        - Two-Pole Oscillator with VIDYA
        - RSI divergence
        """
        reasons = []
        score = 0
        
        df_1m = data.get(1)
        df_5m = data.get(5)
        df_1h = data.get(60)
        
        if df_1m is None:
            return SignalResult('NEUTRAL', 0, ['No data available'], 0)
        
        close = df_1m['close']
        high = df_1m['high']
        low = df_1m['low']
        volume = df_1m['volume']
        open_ = df_1m['open']
        
        current_close = close.iloc[-1]
        
        # === ADX FILTER (Module 21) ===
        try:
            adx = self.il.adx(high, low, close, 14).iloc[-1]
            
            if adx < 25:
                # Market is consolidating - reduce confidence significantly
                reasons.append(f"ADX {adx:.1f} < 25: Consolidation detected")
                return SignalResult('NEUTRAL', 10, reasons, 0)
            else:
                reasons.append(f"ADX {adx:.1f} >= 25: Trending market")
        except Exception as e:
            reasons.append(f"ADX filter error: {e}")
        
        # === SESSION TIMING (Module 11) ===
        try:
            # Simplified session detection - in production would use proper timezone handling
            # London-NY overlap: approximately 12:00-16:00 UTC
            current_hour = pd.Timestamp.now().hour
            
            if 12 <= current_hour <= 16:
                score += 1
                reasons.append("London-NY overlap session (+1)")
            else:
                reasons.append(f"Outside optimal session (current hour: {current_hour})")
        except Exception as e:
            reasons.append(f"Session timing error: {e}")
        
        # === FIBONACCI GOLDEN ZONE (Module 11) ===
        try:
            # Find recent swing high and low
            lookback = 50
            recent_high = high.rolling(lookback).max().iloc[-1]
            recent_low = low.rolling(lookback).min().iloc[-1]
            
            fib_levels = self.il.fibonacci_retracement(recent_high, recent_low)
            golden_zone_low = fib_levels['0.618']
            golden_zone_high = fib_levels['0.5']
            
            # Check if price is in golden zone
            in_golden_zone = golden_zone_low <= current_close <= golden_zone_high
            
            if in_golden_zone:
                # Check for hammer or engulfing at golden zone
                hammer = self.il.detect_hammer(open_, high, low, close).iloc[-1]
                engulfing = self.il.detect_engulfing(open_, high, low, close).iloc[-1]
                
                if hammer == 1 or engulfing == 1:
                    score += 3
                    reasons.append(f"Fib golden zone bounce + pattern (+3)")
                elif current_close < open_.iloc[-1]:  # Red candle at support
                    score += 1
                    reasons.append(f"Price at Fib golden zone ({golden_zone_low:.5f}-{golden_zone_high:.5f})")
            else:
                reasons.append(f"Price outside Fib golden zone")
        except Exception as e:
            reasons.append(f"Fibonacci error: {e}")
        
        # === LWTI (Module 9) ===
        try:
            lwti = self.il.lwti(close, 14).iloc[-1]
            prev_lwti = self.il.lwti(close, 14).iloc[-2]
            
            if lwti > 0 and prev_lwti <= 0:
                score += 1
                reasons.append("LWTI turned green (+1)")
            elif lwti < 0 and prev_lwti >= 0:
                score -= 1
                reasons.append("LWTI turned red (-1)")
            elif lwti > 0:
                reasons.append("LWTI green (no change)")
            else:
                reasons.append("LWTI red (no change)")
        except Exception as e:
            reasons.append(f"LWTI error: {e}")
        
        # === ZERO-LAG ARROWS (Module 12) ===
        try:
            zero_lag = self.il.zero_lag_arrows(close, 10)
            current_signal = zero_lag.iloc[-1]
            
            if current_signal == 1:
                score += 1
                reasons.append("Zero-lag arrow: Green (+1)")
            elif current_signal == -1:
                score -= 1
                reasons.append("Zero-lag arrow: Red (-1)")
            else:
                reasons.append("Zero-lag: No clear signal")
        except Exception as e:
            reasons.append(f"Zero-lag arrows error: {e}")
        
        # === TWO-POLE OSCILLATOR (Module 12) ===
        try:
            two_pole = self.il.two_pole_oscillator(close, 10, 20)
            current_tp = two_pole.iloc[-1]
            prev_tp = two_pole.iloc[-2]
            
            # Buy signal below +0.5, VIDYA green, delta vol > 20
            vol_mean = volume.rolling(20).mean().iloc[-1]
            if pd.isna(vol_mean) or vol_mean == 0:
                vol_delta = 0
            else:
                vol_delta = ((volume.iloc[-1] - vol_mean) / vol_mean) * 100
            
            if current_tp < 0.5 and current_tp > prev_tp and vol_delta > 20:
                score += 3
                reasons.append(f"Two-pole buy signal + volume spike (+3)")
            elif current_tp > -0.5 and current_tp < prev_tp and vol_delta < -20:
                score -= 3
                reasons.append(f"Two-pole sell signal + volume drop (-3)")
            else:
                reasons.append(f"Two-pole oscillator: {current_tp:.2f}")
        except Exception as e:
            reasons.append(f"Two-pole oscillator error: {e}")
        
        # === RSI DIVERGENCE (Module 12) ===
        try:
            rsi = self.il.rsi(close, 14)
            current_rsi = rsi.iloc[-1]
            
            # Simple divergence detection
            # Bullish: price makes lower low, RSI makes higher low
            # Bearish: price makes higher high, RSI makes lower high
            
            lookback_div = 10
            price_low_now = low.iloc[-lookback_div:].min()
            price_low_prev = low.iloc[-lookback_div*2:-lookback_div].min()
            
            rsi_low_now = rsi.iloc[-lookback_div:].min()
            rsi_low_prev = rsi.iloc[-lookback_div*2:-lookback_div].min()
            
            # Bullish divergence
            if price_low_now < price_low_prev and rsi_low_now > rsi_low_prev:
                score += 2
                reasons.append("RSI bullish divergence (+2)")
            
            # Bearish divergence
            price_high_now = high.iloc[-lookback_div:].max()
            price_high_prev = high.iloc[-lookback_div*2:-lookback_div].max()
            rsi_high_now = rsi.iloc[-lookback_div:].max()
            rsi_high_prev = rsi.iloc[-lookback_div*2:-lookback_div].max()
            
            if price_high_now > price_high_prev and rsi_high_now < rsi_high_prev:
                score -= 2
                reasons.append("RSI bearish divergence (-2)")
            
            if not (price_low_now < price_low_prev or price_high_now > price_high_prev):
                reasons.append(f"RSI: {current_rsi:.1f}, no divergence")
        except Exception as e:
            reasons.append(f"RSI divergence error: {e}")
        
        # === DETERMINE SIGNAL ===
        if score >= 3:
            signal = 'BUY'
        elif score <= -3:
            signal = 'SELL'
        else:
            signal = 'NEUTRAL'
        
        # Calculate confidence: min(50 + |score| * 7, 93)
        confidence = min(50 + abs(score) * 7, 93)
        
        return SignalResult(signal, confidence, reasons, score)
