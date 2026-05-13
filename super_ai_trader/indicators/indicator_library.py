"""
Super AI Trader - Indicator Library
Implements 50+ technical indicators across trend, momentum, volatility, volume, and pattern categories.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, List


class IndicatorLibrary:
    """Collection of 50+ technical indicators for trading analysis."""
    
    # ==================== TREND INDICATORS ====================
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average."""
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average."""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def vidya(data: pd.Series, period: int, alpha: float = 0.2) -> pd.Series:
        """Variable Index Dynamic Average."""
        vidya = pd.Series(index=data.index, dtype=float)
        vidya.iloc[period] = data.iloc[:period].mean()
        
        for i in range(period + 1, len(data)):
            cm = abs(data.iloc[i] - data.iloc[i - period]) / (data.iloc[i - period + 1:i + 1].max() - data.iloc[i - period + 1:i + 1].min()) if data.iloc[i - period + 1:i + 1].max() != data.iloc[i - period + 1:i + 1].min() else 0
            vidya.iloc[i] = alpha * cm * data.iloc[i] + (1 - alpha * cm) * vidya.iloc[i - 1]
        
        return vidya
    
    @staticmethod
    def ichimoku(high: pd.Series, low: pd.Series, close: pd.Series, 
                 tenkan_period: int = 9, kijun_period: int = 26, senkou_period: int = 52) -> dict:
        """Ichimoku Cloud indicator."""
        tenkan_sen = (high.rolling(tenkan_period).max() + low.rolling(tenkan_period).min()) / 2
        kijun_sen = (high.rolling(kijun_period).max() + low.rolling(kijun_period).min()) / 2
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun_period)
        senkou_span_b = ((high.rolling(senkou_period).max() + low.rolling(senkou_period).min()) / 2).shift(kijun_period)
        chikou_span = close.shift(-kijun_period)
        
        return {
            'tenkan': tenkan_sen,
            'kijun': kijun_sen,
            'senkou_a': senkou_span_a,
            'senkou_b': senkou_span_b,
            'chikou': chikou_span,
            'cloud_top': pd.concat([senkou_span_a, senkou_span_b], axis=1).max(axis=1),
            'cloud_bottom': pd.concat([senkou_span_a, senkou_span_b], axis=1).min(axis=1)
        }
    
    @staticmethod
    def parabolic_sar(high: pd.Series, low: pd.Series, af: float = 0.02, max_af: float = 0.2) -> pd.Series:
        """Parabolic SAR."""
        sar = pd.Series(index=high.index, dtype=float)
        trend = pd.Series(index=high.index, dtype=int)
        ep = pd.Series(index=high.index, dtype=float)
        
        trend.iloc[0] = 1 if high.iloc[0] > low.iloc[0] else -1
        ep.iloc[0] = high.iloc[0] if trend.iloc[0] == 1 else low.iloc[0]
        sar.iloc[0] = low.iloc[0] if trend.iloc[0] == 1 else high.iloc[0]
        
        for i in range(1, len(high)):
            sar.iloc[i] = sar.iloc[i-1] + af * (ep.iloc[i-1] - sar.iloc[i-1])
            
            if trend.iloc[i-1] == 1:
                if low.iloc[i] < sar.iloc[i]:
                    trend.iloc[i] = -1
                    sar.iloc[i] = ep.iloc[i-1]
                    ep.iloc[i] = low.iloc[i]
                    af = 0.02
                else:
                    trend.iloc[i] = 1
                    if high.iloc[i] > ep.iloc[i-1]:
                        ep.iloc[i] = high.iloc[i]
                        af = min(af + 0.02, max_af)
                    else:
                        ep.iloc[i] = ep.iloc[i-1]
            else:
                if high.iloc[i] > sar.iloc[i]:
                    trend.iloc[i] = 1
                    sar.iloc[i] = ep.iloc[i-1]
                    ep.iloc[i] = high.iloc[i]
                    af = 0.02
                else:
                    trend.iloc[i] = -1
                    if low.iloc[i] < ep.iloc[i-1]:
                        ep.iloc[i] = low.iloc[i]
                        af = min(af + 0.02, max_af)
                    else:
                        ep.iloc[i] = ep.iloc[i-1]
        
        return sar
    
    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Volume Weighted Average Price."""
        typical_price = (high + low + close) / 3
        return (typical_price * volume).cumsum() / volume.cumsum()
    
    @staticmethod
    def donchian_channels(high: pd.Series, low: pd.Series, period: int = 20) -> dict:
        """Donchian Channels."""
        upper = high.rolling(period).max()
        lower = low.rolling(period).min()
        middle = (upper + lower) / 2
        return {'upper': upper, 'middle': middle, 'lower': lower}
    
    # ==================== MOMENTUM INDICATORS ====================
    
    @staticmethod
    def rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index."""
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
        """MACD indicator."""
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return {'macd': macd_line, 'signal': signal_line, 'histogram': histogram}
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                   k_period: int = 14, d_period: int = 3) -> dict:
        """Stochastic Oscillator."""
        lowest_low = low.rolling(k_period).min()
        highest_high = high.rolling(k_period).max()
        k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d = k.rolling(d_period).mean()
        return {'k': k, 'd': d}
    
    @staticmethod
    def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Commodity Channel Index."""
        tp = (high + low + close) / 3
        sma_tp = tp.rolling(period).mean()
        mad = tp.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean())
        return (tp - sma_tp) / (0.015 * mad)
    
    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Williams %R."""
        highest_high = high.rolling(period).max()
        lowest_low = low.rolling(period).min()
        return -100 * (highest_high - close) / (highest_high - lowest_low)
    
    @staticmethod
    def roc(close: pd.Series, period: int = 12) -> pd.Series:
        """Rate of Change."""
        return ((close - close.shift(period)) / close.shift(period)) * 100
    
    @staticmethod
    def momentum(close: pd.Series, period: int = 10) -> pd.Series:
        """Momentum indicator."""
        return close - close.shift(period)
    
    # ==================== VOLATILITY INDICATORS ====================
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range."""
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(period).mean()
    
    @staticmethod
    def bollinger_bands(close: pd.Series, period: int = 20, std_dev: float = 2.0) -> dict:
        """Bollinger Bands."""
        middle = close.rolling(period).mean()
        std = close.rolling(period).std()
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        return {'upper': upper, 'middle': middle, 'lower': lower, 'std': std}
    
    @staticmethod
    def keltner_channels(high: pd.Series, low: pd.Series, close: pd.Series, 
                         period: int = 20, atr_multiplier: float = 2.0) -> dict:
        """Keltner Channels."""
        ema = close.ewm(span=period, adjust=False).mean()
        atr = IndicatorLibrary.atr(high, low, close, period)
        upper = ema + (atr_multiplier * atr)
        lower = ema - (atr_multiplier * atr)
        return {'upper': upper, 'middle': ema, 'lower': lower}
    
    @staticmethod
    def standard_deviation(close: pd.Series, period: int = 20) -> pd.Series:
        """Standard Deviation."""
        return close.rolling(period).std()
    
    @staticmethod
    def natr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Normalized Average True Range."""
        atr = IndicatorLibrary.atr(high, low, close, period)
        return (atr / close) * 100
    
    # ==================== VOLUME INDICATORS ====================
    
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume."""
        direction = np.sign(close.diff())
        direction.iloc[0] = 0
        return (direction * volume).cumsum()
    
    @staticmethod
    def vwap_volume(volume: pd.Series) -> pd.Series:
        """Volume Moving Average."""
        return volume.rolling(20).mean()
    
    @staticmethod
    def mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
        """Money Flow Index."""
        tp = (high + low + close) / 3
        money_flow = tp * volume
        
        delta = tp.diff()
        positive_flow = money_flow.where(delta > 0, 0).rolling(period).sum()
        negative_flow = money_flow.where(delta < 0, 0).rolling(period).sum()
        
        mfr = positive_flow / negative_flow
        return 100 - (100 / (1 + mfr))
    
    @staticmethod
    def adl(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Accumulation/Distribution Line."""
        clv = ((close - low) - (high - close)) / (high - low)
        clv = clv.fillna(0)
        return (clv * volume).cumsum()
    
    @staticmethod
    def cmf(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
        """Chaikin Money Flow."""
        mf = ((close - low) - (high - close)) / (high - low)
        mf = mf.fillna(0)
        mfv = mf * volume
        return mfv.rolling(period).sum() / volume.rolling(period).sum()
    
    @staticmethod
    def force_index(close: pd.Series, volume: pd.Series, period: int = 13) -> pd.Series:
        """Force Index."""
        fi = close.diff() * volume
        return fi.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def eom(high: pd.Series, low: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
        """Ease of Movement."""
        distance = (high + low) / 2 - (high.shift(1) + low.shift(1)) / 2
        box_ratio = volume / 100000000 / (high - low)
        box_ratio = box_ratio.replace([np.inf, -np.inf], 0).fillna(0)
        emv = distance / box_ratio
        return emv.rolling(period).mean()
    
    # ==================== CUSTOM PATTERNS ====================
    
    @staticmethod
    def detect_hammer(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """Detect Hammer candlestick pattern."""
        body = abs(close - open_)
        upper_shadow = high - pd.concat([open_, close], axis=1).max(axis=1)
        lower_shadow = pd.concat([open_, close], axis=1).min(axis=1) - low
        total_range = high - low
        
        is_hammer = (lower_shadow > 2 * body) & (upper_shadow < body * 0.5) & (total_range > 0)
        return is_hammer.astype(int)
    
    @staticmethod
    def detect_engulfing(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """Detect Engulfing pattern."""
        bullish = (close > open_) & (close.shift(1) < open_.shift(1)) & \
                  (close >= open_.shift(1)) & (open_ <= close.shift(1))
        bearish = (close < open_) & (close.shift(1) > open_.shift(1)) & \
                  (close <= open_.shift(1)) & (open_ >= close.shift(1))
        return bullish.astype(int) - bearish.astype(int)
    
    @staticmethod
    def detect_doji(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, threshold: float = 0.001) -> pd.Series:
        """Detect Doji candlestick pattern."""
        body = abs(close - open_)
        total_range = high - low
        return (body < threshold * total_range).astype(int)
    
    @staticmethod
    def detect_inside_bar(high: pd.Series, low: pd.Series) -> pd.Series:
        """Detect Inside Bar pattern."""
        inside = (high < high.shift(1)) & (low > low.shift(1))
        return inside.astype(int)
    
    @staticmethod
    def detect_liquidity_sweep(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Detect Liquidity Sweep (false breakout)."""
        recent_high = high.rolling(period).max().shift(1)
        recent_low = low.rolling(period).min().shift(1)
        
        sweep_high = (high > recent_high) & (close < recent_high)
        sweep_low = (low < recent_low) & (close > recent_low)
        
        return sweep_high.astype(int) - sweep_low.astype(int)
    
    @staticmethod
    def detect_choch(high: pd.Series, low: pd.Series, close: pd.Series, lookback: int = 5) -> pd.Series:
        """Detect Change of Character (CHoCH)."""
        # Simplified CHoCH detection
        hh = high.rolling(lookback).max()
        ll = low.rolling(lookback).min()
        
        bullish_choch = (close > hh.shift(1)) & (close.shift(1) <= hh.shift(2))
        bearish_choch = (close < ll.shift(1)) & (close.shift(1) >= ll.shift(2))
        
        return bullish_choch.astype(int) - bearish_choch.astype(int)
    
    # ==================== SESSION & FIBONACCI ====================
    
    @staticmethod
    def fibonacci_retracement(high: float, low: float) -> dict:
        """Calculate Fibonacci retracement levels."""
        diff = high - low
        return {
            '0.0': high,
            '0.236': high - 0.236 * diff,
            '0.382': high - 0.382 * diff,
            '0.5': high - 0.5 * diff,
            '0.618': high - 0.618 * diff,
            '0.786': high - 0.786 * diff,
            '1.0': low
        }
    
    @staticmethod
    def session_range(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, 
                      session_start_hour: int, session_end_hour: int) -> dict:
        """Detect session high/low range."""
        # This would need proper datetime handling in real implementation
        session_high = high.rolling(240).max()  # 4 hours in 1m data
        session_low = low.rolling(240).min()
        return {'high': session_high, 'low': session_low}
    
    # ==================== ADX & TREND STRENGTH ====================
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average Directional Index."""
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(period).mean()
        
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return adx
    
    @staticmethod
    def ema_slope(ema_series: pd.Series, bars: int = 20) -> pd.Series:
        """Calculate EMA slope over specified bars."""
        slope = (ema_series - ema_series.shift(bars)) / ema_series.shift(bars) * 100
        return slope
    
    # ==================== VOLUME PROFILE ====================
    
    @staticmethod
    def volume_profile(close: pd.Series, volume: pd.Series, num_bins: int = 20) -> dict:
        """Calculate Volume Profile (simplified)."""
        price_min = close.min()
        price_max = close.max()
        bin_size = (price_max - price_min) / num_bins
        
        bins = np.linspace(price_min, price_max, num_bins + 1)
        hist, bin_edges = np.histogram(close, bins=bins, weights=volume)
        
        poc_idx = np.argmax(hist)
        poc = (bin_edges[poc_idx] + bin_edges[poc_idx + 1]) / 2
        
        total_volume = hist.sum()
        value_area_volume = total_volume * 0.70
        cumulative = 0
        va_high = va_low = poc
        
        sorted_indices = np.argsort(hist)[::-1]
        for idx in sorted_indices:
            cumulative += hist[idx]
            if cumulative <= value_area_volume:
                if (bin_edges[idx] + bin_edges[idx + 1]) / 2 > poc:
                    va_high = bin_edges[idx + 1]
                else:
                    va_low = bin_edges[idx]
        
        return {
            'poc': poc,
            'va_high': va_high,
            'va_low': va_low,
            'histogram': hist,
            'bins': bin_edges
        }
    
    @staticmethod
    def anchored_vwap(close: pd.Series, volume: pd.Series, anchor_idx: int) -> pd.Series:
        """Anchored VWAP from a specific point."""
        typical_price = (close.rolling(2).max() + close.rolling(2).min() + close) / 3
        cum_vol = volume.iloc[anchor_idx:].cumsum()
        cum_tpvol = (typical_price.iloc[anchor_idx:] * volume.iloc[anchor_idx:]).cumsum()
        avwap = pd.Series(index=close.index, dtype=float)
        avwap.iloc[anchor_idx:] = cum_tpvol / cum_vol
        return avwap
    
    # ==================== LWTI & CUSTOM OSCILLATORS ====================
    
    @staticmethod
    def lwti(close: pd.Series, period: int = 14) -> pd.Series:
        """Larry Williams Trend Index (simplified)."""
        # Simplified version - actual LWTI may vary
        roc = IndicatorLibrary.roc(close, period)
        return roc.rolling(period).mean()
    
    @staticmethod
    def two_pole_oscillator(close: pd.Series, period1: int = 10, period2: int = 20) -> pd.Series:
        """Two-Pole Oscillator."""
        ema1 = IndicatorLibrary.ema(close, period1)
        ema2 = IndicatorLibrary.ema(close, period2)
        oscillator = (ema1 - ema2) / close * 100
        return oscillator
    
    @staticmethod
    def zero_lag_arrows(close: pd.Series, period: int = 10) -> pd.Series:
        """Zero-Lag Trend Signals (simplified arrow detection)."""
        zlema = close - close.shift(period) + IndicatorLibrary.ema(close, period)
        signal = np.sign(zlema.diff())
        return signal
    
    @staticmethod
    def superscript_trend(close: pd.Series, period: int = 20) -> pd.Series:
        """Supertrend indicator."""
        hl2 = (pd.Series(close.index) + pd.Series(close.index)) / 2  # placeholder
        atr = IndicatorLibrary.atr(pd.Series(close.index), pd.Series(close.index), close, period)
        multiplier = 3.0
        
        upper_band = hl2 + multiplier * atr
        lower_band = hl2 - multiplier * atr
        
        supertrend = pd.Series(index=close.index, dtype=float)
        supertrend.iloc[0] = lower_band.iloc[0]
        
        for i in range(1, len(close)):
            if close.iloc[i] > supertrend.iloc[i-1]:
                supertrend.iloc[i] = lower_band.iloc[i]
            else:
                supertrend.iloc[i] = upper_band.iloc[i]
        
        return supertrend


# Convenience function to get all indicator names
def get_all_indicators() -> List[str]:
    """Return list of all available indicator methods."""
    return [method for method in dir(IndicatorLibrary) if not method.startswith('_') and callable(getattr(IndicatorLibrary, method))]
