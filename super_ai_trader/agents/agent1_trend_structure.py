"""
Super AI Trader - Agent 1: Trend & Structure Agent
Implements trend-following rules from modules: 1, 5, 8, 13, 17, 18
- Ichimoku Cloud system
- Multi-Timeframe Analysis (MTFA)
- Turtle Trading
- CHoCH detection
- EMA strategies
- 3 EMA + Stochastic
"""

import pandas as pd
from typing import Dict

from agents.base_agent import BaseAgent, SignalResult
from indicators.indicator_library import IndicatorLibrary


class TrendStructureAgent(BaseAgent):
    """
    Trend & Structure Agent
    Determines dominant trend direction using trend-following tools across multiple timeframes.
    """
    
    def __init__(self):
        super().__init__(
            name="Trend & Structure Agent",
            description="Determines dominant trend direction using trend-following tools across multiple timeframes.",
            module_ids=[1, 5, 8, 13, 17, 18]
        )
        self.il = IndicatorLibrary()
    
    def analyze(self, data: Dict[int, pd.DataFrame], current_price: dict) -> SignalResult:
        """
        Analyze market data and return a trading signal.
        
        Rules evaluated:
        - Ichimoku: close vs cloud position
        - EMA200: close relative to 200 EMA
        - 20/200 Cross: Golden/Death cross detection
        - MTF Alignment: 1H and 4H trend alignment
        - Turtle Breakout: 20-period high/low breakout
        - CHoCH: Change of Character detection
        - 3 EMA Stack: EMA 21 > 34 > 144 alignment
        """
        reasons = []
        score = 0
        
        # Get data for different timeframes
        df_1m = data.get(1)
        df_5m = data.get(5)
        df_1h = data.get(60)
        df_4h = data.get(240)
        
        if df_1m is None:
            return SignalResult('NEUTRAL', 0, ['No data available'], 0)
        
        # Calculate required indicators
        close = df_1m['close']
        high = df_1m['high']
        low = df_1m['low']
        
        # === ICHIMOKU CLOUD (Module 1) ===
        try:
            ichi = self.il.ichimoku(high, low, close)
            cloud_top = ichi['cloud_top'].iloc[-1]
            cloud_bottom = ichi['cloud_bottom'].iloc[-1]
            current_close = close.iloc[-1]
            
            if current_close > cloud_top:
                score += 2
                reasons.append("Ichimoku: Price above cloud (+2)")
            elif current_close < cloud_bottom:
                score -= 2
                reasons.append("Ichimoku: Price below cloud (-2)")
            else:
                reasons.append("Ichimoku: Price inside cloud (0)")
        except Exception as e:
            reasons.append(f"Ichimoku calculation error: {e}")
        
        # === EMA 200 (Module 17) ===
        try:
            ema_200 = self.il.ema(close, 200).iloc[-1]
            if current_close > ema_200:
                score += 1
                reasons.append(f"EMA200: Price above ({current_close:.5f} > {ema_200:.5f}) (+1)")
            else:
                score -= 1
                reasons.append(f"EMA200: Price below ({current_close:.5f} < {ema_200:.5f}) (-1)")
        except Exception as e:
            reasons.append(f"EMA200 calculation error: {e}")
        
        # === 20/200 CROSS (Module 17) ===
        try:
            ema_20 = self.il.ema(close, 20)
            ema_200_series = self.il.ema(close, 200)
            
            current_ema20 = ema_20.iloc[-1]
            prev_ema20 = ema_20.iloc[-2]
            current_ema200 = ema_200_series.iloc[-1]
            prev_ema200 = ema_200_series.iloc[-2]
            
            # Check for golden cross (20 crosses above 200)
            if prev_ema20 <= prev_ema200 and current_ema20 > current_ema200:
                score += 2
                reasons.append("Golden Cross detected (+2)")
            # Check for death cross (20 crosses below 200)
            elif prev_ema20 >= prev_ema200 and current_ema20 < current_ema200:
                score -= 2
                reasons.append("Death Cross detected (-2)")
            # Already positioned
            elif current_ema20 > current_ema200:
                score += 1
                reasons.append("EMA20 already above EMA200 (+1)")
            else:
                score -= 1
                reasons.append("EMA20 already below EMA200 (-1)")
        except Exception as e:
            reasons.append(f"20/200 Cross calculation error: {e}")
        
        # === MULTI-TIMEFRAME ALIGNMENT (Module 5) ===
        mtf_score = 0
        if df_1h is not None:
            try:
                ema_200_1h = self.il.ema(df_1h['close'], 200).iloc[-1]
                if df_1h['close'].iloc[-1] > ema_200_1h:
                    mtf_score += 1
                    reasons.append("1H: Price above EMA200 (+1)")
                else:
                    mtf_score -= 1
                    reasons.append("1H: Price below EMA200 (-1)")
            except Exception as e:
                reasons.append(f"1H EMA200 error: {e}")
        
        if df_4h is not None:
            try:
                ema_200_4h = self.il.ema(df_4h['close'], 200).iloc[-1]
                if df_4h['close'].iloc[-1] > ema_200_4h:
                    mtf_score += 1
                    reasons.append("4H: Price above EMA200 (+1)")
                else:
                    mtf_score -= 1
                    reasons.append("4H: Price below EMA200 (-1)")
            except Exception as e:
                reasons.append(f"4H EMA200 error: {e}")
        
        score += mtf_score
        
        # === TURTLE BREAKOUT (Module 8) ===
        try:
            highest_20 = high.rolling(20).max().iloc[-1]
            lowest_20 = low.rolling(20).min().iloc[-1]
            prev_high = high.rolling(20).max().iloc[-2]
            prev_low = low.rolling(20).min().iloc[-2]
            
            if current_close > prev_high:
                score += 2
                reasons.append(f"Turtle Breakout: Above 20-period high ({highest_20:.5f}) (+2)")
            elif current_close < prev_low:
                score -= 2
                reasons.append(f"Turtle Breakout: Below 20-period low ({lowest_20:.5f}) (-2)")
            else:
                reasons.append("Turtle: No breakout")
        except Exception as e:
            reasons.append(f"Turtle Breakout error: {e}")
        
        # === CHoCH DETECTION (Module 13) ===
        try:
            choch = self.il.detect_choch(high, low, close, lookback=5).iloc[-1]
            if choch == 1:
                score += 2
                reasons.append("Bullish CHoCH detected (+2)")
            elif choch == -1:
                score -= 2
                reasons.append("Bearish CHoCH detected (-2)")
            else:
                reasons.append("No CHoCH pattern")
        except Exception as e:
            reasons.append(f"CHoCH detection error: {e}")
        
        # === THREE EMA STACK (Module 18) ===
        try:
            ema_21 = self.il.ema(close, 21).iloc[-1]
            ema_34 = self.il.ema(close, 34).iloc[-1]
            ema_144 = self.il.ema(close, 144).iloc[-1]
            
            if ema_21 > ema_34 > ema_144:
                score += 2
                reasons.append("3 EMA Stack: Bullish alignment (21>34>144) (+2)")
            elif ema_21 < ema_34 < ema_144:
                score -= 2
                reasons.append("3 EMA Stack: Bearish alignment (21<34<144) (-2)")
            else:
                reasons.append("3 EMA Stack: Mixed alignment")
        except Exception as e:
            reasons.append(f"3 EMA Stack error: {e}")
        
        # === DETERMINE SIGNAL ===
        if score >= 4:
            signal = 'BUY'
        elif score <= -4:
            signal = 'SELL'
        else:
            signal = 'NEUTRAL'
        
        # Calculate confidence: min(60 + |score| * 5, 98)
        confidence = min(60 + abs(score) * 5, 98)
        
        return SignalResult(signal, confidence, reasons, score)
