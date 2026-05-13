"""
Agent 4: Technical Indicators Agent
Combines multiple technical indicators (RSI, MACD, Bollinger Bands) for confluence.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from utils.indicators import rsi, macd, bollinger_bands, ema


class IndicatorAgent:
    """
    Agent 4 - Technical Indicators
    
    Responsibilities:
    - Analyze RSI for overbought/oversold conditions
    - Evaluate MACD for momentum and crossovers
    - Check Bollinger Bands for volatility and mean reversion
    - Combine signals for confluence
    - Output: BUY/SELL/HOLD with confidence score
    """
    
    def __init__(self, rsi_period: int = 14, rsi_oversold: int = 30, rsi_overbought: int = 70):
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze technical indicators from OHLCV data.
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            Dictionary with signal, confidence, and reasoning
        """
        if len(df) < 50:
            return {
                'agent': 'IndicatorAgent',
                'signal': 'HOLD',
                'confidence': 0,
                'reasons': ['Insufficient data for indicator analysis'],
                'details': {}
            }
        
        reasons = []
        signals = []
        confidences = []
        
        # Calculate indicators
        df['rsi'] = rsi(df['Close'], self.rsi_period)
        macd_line, signal_line, histogram = macd(df['Close'])
        df['macd'] = macd_line
        df['macd_signal'] = signal_line
        df['macd_hist'] = histogram
        
        upper_bb, middle_bb, lower_bb = bollinger_bands(df['Close'])
        df['bb_upper'] = upper_bb
        df['bb_middle'] = middle_bb
        df['bb_lower'] = lower_bb
        
        df['ema_50'] = ema(df['Close'], 50)
        
        # Get latest values
        current_price = df['Close'].iloc[-1]
        current_rsi = df['rsi'].iloc[-1]
        current_macd = df['macd'].iloc[-1]
        current_macd_signal = df['macd_signal'].iloc[-1]
        current_macd_hist = df['macd_hist'].iloc[-1]
        prev_macd_hist = df['macd_hist'].iloc[-2]
        
        current_bb_upper = df['bb_upper'].iloc[-1]
        current_bb_lower = df['bb_lower'].iloc[-1]
        current_bb_middle = df['bb_middle'].iloc[-1]
        
        current_ema_50 = df['ema_50'].iloc[-1]
        
        # RSI Analysis
        rsi_signal = 'NEUTRAL'
        rsi_confidence = 0
        
        if current_rsi < self.rsi_oversold:
            rsi_signal = 'BUY'
            rsi_confidence = 40 + (self.rsi_oversold - current_rsi)
            reasons.append(f"RSI is {current_rsi:.1f} (oversold < {self.rsi_oversold}) → Potential reversal up")
        elif current_rsi > self.rsi_overbought:
            rsi_signal = 'SELL'
            rsi_confidence = 40 + (current_rsi - self.rsi_overbought)
            reasons.append(f"RSI is {current_rsi:.1f} (overbought > {self.rsi_overbought}) → Potential reversal down")
        else:
            reasons.append(f"RSI is {current_rsi:.1f} (neutral zone)")
        
        signals.append(rsi_signal)
        confidences.append(min(60, rsi_confidence))
        
        # MACD Analysis
        macd_signal = 'NEUTRAL'
        macd_confidence = 0
        
        # MACD crossover
        if current_macd > current_macd_signal and prev_macd_hist <= 0:
            macd_signal = 'BUY'
            macd_confidence = 50
            reasons.append("MACD bullish crossover detected → Momentum shifting up")
        elif current_macd < current_macd_signal and prev_macd_hist >= 0:
            macd_signal = 'SELL'
            macd_confidence = 50
            reasons.append("MACD bearish crossover detected → Momentum shifting down")
        elif current_macd > current_macd_signal:
            macd_signal = 'BUY'
            macd_confidence = 30
            reasons.append("MACD above signal line → Bullish momentum")
        elif current_macd < current_macd_signal:
            macd_signal = 'SELL'
            macd_confidence = 30
            reasons.append("MACD below signal line → Bearish momentum")
        
        # MACD histogram divergence
        if current_macd_hist > prev_macd_hist and current_macd_hist < 0:
            reasons.append("MACD histogram showing bullish divergence → Weakening downtrend")
        elif current_macd_hist < prev_macd_hist and current_macd_hist > 0:
            reasons.append("MACD histogram showing bearish divergence → Weakening uptrend")
        
        signals.append(macd_signal)
        confidences.append(min(60, macd_confidence))
        
        # Bollinger Bands Analysis
        bb_signal = 'NEUTRAL'
        bb_confidence = 0
        
        bb_width = current_bb_upper - current_bb_lower
        price_position = (current_price - current_bb_lower) / bb_width if bb_width > 0 else 0.5
        
        if current_price <= current_bb_lower:
            bb_signal = 'BUY'
            bb_confidence = 45
            reasons.append("Price at or below lower Bollinger Band → Oversold, potential bounce")
        elif current_price >= current_bb_upper:
            bb_signal = 'SELL'
            bb_confidence = 45
            reasons.append("Price at or above upper Bollinger Band → Overbought, potential pullback")
        elif price_position < 0.3:
            bb_signal = 'BUY'
            bb_confidence = 25
            reasons.append("Price in lower third of Bollinger Bands → Mildly oversold")
        elif price_position > 0.7:
            bb_signal = 'SELL'
            bb_confidence = 25
            reasons.append("Price in upper third of Bollinger Bands → Mildly overbought")
        else:
            reasons.append("Price near middle of Bollinger Bands → Neutral")
        
        signals.append(bb_signal)
        confidences.append(min(55, bb_confidence))
        
        # EMA 50 relationship
        if current_price > current_ema_50:
            reasons.append("Price above 50 EMA → Short-term bullish")
            if rsi_signal != 'SELL' and macd_signal != 'SELL':
                signals.append('BUY')
                confidences.append(25)
        else:
            reasons.append("Price below 50 EMA → Short-term bearish")
            if rsi_signal != 'BUY' and macd_signal != 'BUY':
                signals.append('SELL')
                confidences.append(25)
        
        # Combine signals
        buy_signals = sum(1 for s in signals if s == 'BUY')
        sell_signals = sum(1 for s in signals if s == 'SELL')
        
        total_weight = sum(confidences)
        avg_confidence = total_weight / len(confidences) if confidences else 0
        
        if buy_signals > sell_signals:
            signal = 'BUY'
            confidence = min(85, avg_confidence + (buy_signals * 5))
        elif sell_signals > buy_signals:
            signal = 'SELL'
            confidence = min(85, avg_confidence + (sell_signals * 5))
        else:
            signal = 'HOLD'
            confidence = 30
        
        # Add summary reason
        if signal != 'HOLD':
            reasons.append(f"Indicator confluence: {buy_signals} buy, {sell_signals} sell signals")
        
        confidence = max(0, min(100, int(confidence)))
        
        return {
            'agent': 'IndicatorAgent',
            'signal': signal,
            'confidence': confidence,
            'reasons': reasons,
            'details': {
                'rsi': current_rsi,
                'macd': current_macd,
                'macd_signal': current_macd_signal,
                'macd_histogram': current_macd_hist,
                'bb_upper': current_bb_upper,
                'bb_lower': current_bb_lower,
                'price_position_in_bb': price_position,
                'ema_50': current_ema_50,
                'individual_signals': signals,
                'individual_confidences': confidences
            }
        }
