"""
Agent 2: Volume Analysis Agent
Analyzes volume patterns to confirm price movements and detect institutional activity.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from utils.indicators import volume_sma


class VolumeAgent:
    """
    Agent 2 - Volume Analysis
    
    Responsibilities:
    - Detect volume spikes relative to average
    - Confirm price moves with volume
    - Identify accumulation/distribution patterns
    - Output: BUY/SELL/HOLD with confidence score
    """
    
    def __init__(self, volume_sma_period: int = 20, spike_threshold: float = 2.0):
        self.volume_sma_period = volume_sma_period
        self.spike_threshold = spike_threshold
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze volume patterns from OHLCV data.
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            Dictionary with signal, confidence, and reasoning
        """
        if len(df) < self.volume_sma_period + 5:
            return {
                'agent': 'VolumeAgent',
                'signal': 'HOLD',
                'confidence': 0,
                'reasons': ['Insufficient data for volume analysis'],
                'details': {}
            }
        
        # Calculate volume SMA
        df['vol_sma'] = volume_sma(df, self.volume_sma_period)
        
        # Get recent values
        current_volume = df['Volume'].iloc[-1]
        avg_volume = df['vol_sma'].iloc[-1]
        prev_volume = df['Volume'].iloc[-2]
        prev_avg_volume = df['vol_sma'].iloc[-2]
        
        # Price data
        current_close = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        current_open = df['Open'].iloc[-1]
        prev_open = df['Open'].iloc[-2]
        
        reasons = []
        confidence = 0
        signal = 'HOLD'
        
        # Condition 1: Volume spike detection
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        is_volume_spike = volume_ratio >= self.spike_threshold
        
        if is_volume_spike:
            reasons.append(f"Volume spike detected: {volume_ratio:.2f}x average ({current_volume:.0f} vs {avg_volume:.0f})")
        else:
            reasons.append(f"Volume is {volume_ratio:.2f}x average (no significant spike)")
        
        # Condition 2: Price direction
        price_up = current_close > prev_close
        price_down = current_close < prev_close
        
        candle_body = abs(current_close - current_open)
        prev_candle_body = abs(prev_close - prev_open)
        
        # Condition 3: Volume confirming price move
        volume_confirms_price = False
        
        if price_up and is_volume_spike:
            volume_confirms_price = True
            reasons.append("High volume confirms bullish price movement → Institutional buying likely")
        elif price_down and is_volume_spike:
            volume_confirms_price = True
            reasons.append("High volume confirms bearish price movement → Institutional selling likely")
        elif not is_volume_spike:
            reasons.append("Volume does not confirm price move → Potential false breakout/breakdown")
        
        # Condition 4: Volume trend (accumulation/distribution)
        recent_volumes = df['Volume'].iloc[-5:].values
        recent_avg_volume = np.mean(recent_volumes)
        volume_trend_up = recent_avg_volume > avg_volume * 1.1
        volume_trend_down = recent_avg_volume < avg_volume * 0.9
        
        if volume_trend_up:
            reasons.append("Recent volume trend is increasing → Potential accumulation")
        elif volume_trend_down:
            reasons.append("Recent volume trend is decreasing → Potential distribution or lack of interest")
        
        # Determine signal and confidence
        if price_up and volume_confirms_price:
            signal = 'BUY'
            confidence = min(40 + (volume_ratio * 10), 85)
        elif price_down and volume_confirms_price:
            signal = 'SELL'
            confidence = min(40 + (volume_ratio * 10), 85)
        else:
            signal = 'HOLD'
            confidence = 25 if not is_volume_spike else 35
            
            if price_up and not is_volume_spike:
                reasons.append("Price rising on low volume → Weak bullish signal")
            elif price_down and not is_volume_spike:
                reasons.append("Price falling on low volume → Weak bearish signal")
        
        # Adjust confidence based on volume trend
        if volume_trend_up and signal == 'BUY':
            confidence += 5
        elif volume_trend_down and signal == 'SELL':
            confidence += 5
        
        # Ensure confidence is within bounds
        confidence = max(0, min(100, int(confidence)))
        
        return {
            'agent': 'VolumeAgent',
            'signal': signal,
            'confidence': confidence,
            'reasons': reasons,
            'details': {
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'volume_ratio': volume_ratio,
                'is_volume_spike': is_volume_spike,
                'volume_confirms_price': volume_confirms_price,
                'volume_trend_up': volume_trend_up,
                'price_up': price_up
            }
        }
