"""
Super AI Trader - Agent 2: Volume & Order Flow Agent
Implements volume analysis rules from modules: 3, 4, 15, 16
- Indicator Ranking
- Volume + Price Action (manipulation detection)
- Volume Profile Trading (POC/Value Area)
- Volume Profile Shapes (P, b, D shapes)
"""

import pandas as pd
import numpy as np
from typing import Dict

from agents.base_agent import BaseAgent, SignalResult
from indicators.indicator_library import IndicatorLibrary


class VolumeOrderFlowAgent(BaseAgent):
    """
    Volume & Order Flow Agent
    Validates price moves with vertical/horizontal volume; detects conviction, absorption, and manipulation.
    """
    
    def __init__(self):
        super().__init__(
            name="Volume & Order Flow Agent",
            description="Validates price moves with vertical/horizontal volume; detects conviction, absorption, and manipulation.",
            module_ids=[3, 4, 15, 16]
        )
        self.il = IndicatorLibrary()
    
    def analyze(self, data: Dict[int, pd.DataFrame], current_price: dict) -> SignalResult:
        """
        Analyze market data and return a trading signal.
        
        Rules evaluated:
        - Absorption: Small body + huge volume = reversal signal
        - No Supply/Demand: Low volume on price moves
        - Volume Divergence: HH with lower volume / LL with lower volume
        - POC Reaction: Price reaction at Point of Control
        - Profile Shape: P-shape, b-shape, D-shape analysis
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
        volume = df_1m['volume']
        open_ = df_1m['open']
        
        # Calculate ATR and Volume MA
        atr = self.il.atr(high, low, close, 14).iloc[-1]
        vol_ma = volume.rolling(20).mean().iloc[-1]
        current_volume = volume.iloc[-1]
        
        # === ABSORPTION (Module 4) ===
        try:
            current_open = open_.iloc[-1]
            current_close = close.iloc[-1]
            candle_body = abs(current_close - current_open)
            
            # Check for absorption: small body (< 0.1 ATR) with huge volume (> 1.5x vol_ma)
            if candle_body < 0.1 * atr and current_volume > 1.5 * vol_ma:
                # Bullish absorption: red candle (close < open) on huge volume
                if current_close < current_open:
                    score += 3
                    reasons.append(f"Absorption: Red candle with huge volume (+3)")
                # Bearish absorption: green candle (close > open) on huge volume
                elif current_close > current_open:
                    score -= 3
                    reasons.append(f"Absorption: Green candle with huge volume (-3)")
            else:
                reasons.append("No absorption pattern detected")
        except Exception as e:
            reasons.append(f"Absorption calculation error: {e}")
        
        # === NO SUPPLY/DEMAND (Module 4) ===
        try:
            price_change = close.iloc[-1] - close.iloc[-5]  # 5-bar price change
            
            if price_change > 0 and current_volume < 0.5 * vol_ma:
                score += 1
                reasons.append("Price rising on low volume (weak move) (+1)")
            elif price_change < 0 and current_volume < 0.5 * vol_ma:
                score -= 1
                reasons.append("Price falling on low volume (weak move) (-1)")
            else:
                reasons.append("Volume confirms price move")
        except Exception as e:
            reasons.append(f"No Supply/Demand error: {e}")
        
        # === VOLUME DIVERGENCE (Module 4) ===
        try:
            # Check for higher high with lower volume (bearish divergence)
            recent_highs = high.rolling(20).max()
            prev_high_idx = high.iloc[:-1].argmax()
            prev_high_vol = volume.iloc[prev_high_idx] if len(volume) > prev_high_idx else current_volume
            
            # Check for lower low with lower volume (bullish divergence)
            recent_lows = low.rolling(20).min()
            prev_low_idx = low.iloc[:-1].argmin()
            prev_low_vol = volume.iloc[prev_low_idx] if len(volume) > prev_low_idx else current_volume
            
            # Higher high with lower volume
            if high.iloc[-1] > recent_highs.iloc[-2] and current_volume < prev_high_vol * 0.9:
                score -= 2
                reasons.append("Volume divergence: HH with lower volume (-2)")
            # Lower low with lower volume
            elif low.iloc[-1] < recent_lows.iloc[-2] and current_volume < prev_low_vol * 0.9:
                score += 2
                reasons.append("Volume divergence: LL with lower volume (+2)")
            else:
                reasons.append("No volume divergence")
        except Exception as e:
            reasons.append(f"Volume Divergence error: {e}")
        
        # === POC REACTION (Module 15) ===
        try:
            vp = self.il.volume_profile(close, volume, num_bins=20)
            poc = vp['poc']
            va_high = vp['va_high']
            va_low = vp['va_low']
            
            current_price_val = current_price.get('bid', current_close) if current_price else current_close.iloc[-1]
            
            # Check if price is reacting to POC or value area
            distance_to_poc = abs(current_price_val - poc) / poc * 100
            
            if distance_to_poc < 0.5:  # Within 0.5% of POC
                # First touch from above into heavy volume node = bullish
                if close.iloc[-5] > poc and current_close <= poc:
                    score += 3
                    reasons.append(f"POC reaction: Touch from above into POC ({poc:.5f}) (+3)")
                # First touch from below into heavy volume node = bearish
                elif close.iloc[-5] < poc and current_close >= poc:
                    score -= 3
                    reasons.append(f"POC reaction: Touch from below into POC ({poc:.5f}) (-3)")
                else:
                    reasons.append(f"Near POC ({poc:.5f}), no clear reaction")
            else:
                reasons.append(f"Price away from POC (distance: {distance_to_poc:.2f}%)")
        except Exception as e:
            reasons.append(f"POC Reaction error: {e}")
        
        # === PROFILE SHAPE (Module 16) ===
        try:
            # Determine profile shape based on close position in range
            session_high = high.iloc[-20:].max()
            session_low = low.iloc[-20:].min()
            session_range = session_high - session_low
            
            if session_range > 0:
                close_position = (current_close - session_low) / session_range
                
                # P-shape: close in upper 50% of range (buying tail below)
                if close_position > 0.5:
                    score += 2
                    reasons.append(f"P-shape profile (close at {close_position:.1%} of range) (+2)")
                # b-shape: close in lower 50% of range (selling tail above)
                elif close_position < 0.5:
                    score -= 2
                    reasons.append(f"b-shape profile (close at {close_position:.1%} of range) (-2)")
                # D-shape: balanced
                else:
                    reasons.append("D-shape profile (balanced)")
            else:
                reasons.append("No clear profile shape")
        except Exception as e:
            reasons.append(f"Profile Shape error: {e}")
        
        # === DETERMINE SIGNAL ===
        if score >= 3:
            signal = 'BUY'
        elif score <= -3:
            signal = 'SELL'
        else:
            signal = 'NEUTRAL'
        
        # Calculate confidence: min(50 + |score| * 10, 95)
        confidence = min(50 + abs(score) * 10, 95)
        
        return SignalResult(signal, confidence, reasons, score)
