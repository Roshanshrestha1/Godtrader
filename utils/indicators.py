"""
Technical indicator calculations for the Stable Stock Analysis System.
All indicators are implemented using pandas for efficiency and clarity.
"""

import pandas as pd
import numpy as np
from typing import Tuple


def ema(series: pd.Series, length: int) -> pd.Series:
    """
    Calculate Exponential Moving Average.
    
    Args:
        series: Price series (typically Close)
        length: EMA period
    
    Returns:
        EMA series
    """
    return series.ewm(span=length, adjust=False).mean()


def sma(series: pd.Series, length: int) -> pd.Series:
    """
    Calculate Simple Moving Average.
    
    Args:
        series: Price series
        length: SMA period
    
    Returns:
        SMA series
    """
    return series.rolling(window=length).mean()


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR).
    
    Args:
        df: DataFrame with High, Low, Close columns
        period: ATR period (default 14)
    
    Returns:
        ATR series
    """
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr_series = true_range.rolling(period).mean()
    
    return atr_series


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average Directional Index (ADX).
    
    Args:
        df: DataFrame with High, Low, Close columns
        period: ADX period (default 14)
    
    Returns:
        ADX series
    """
    # Calculate directional movement
    up_move = df['High'].diff()
    down_move = df['Low'].diff().abs()
    
    # Plus DM and Minus DM
    plus_dm = pd.Series(0.0, index=df.index)
    minus_dm = pd.Series(0.0, index=df.index)
    
    plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
    minus_dm[(down_move > up_move) & (down_move > 0)] = down_move
    
    # Calculate True Range
    tr = atr(df, period)
    
    # Smoothed DM and TR
    plus_di = 100 * (plus_dm.rolling(period).mean() / tr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / tr)
    
    # DX and ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx_series = dx.rolling(period).mean()
    
    return adx_series


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        series: Price series (typically Close)
        period: RSI period (default 14)
    
    Returns:
        RSI series
    """
    delta = series.diff()
    
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    
    rs = avg_gain / avg_loss
    rsi_series = 100 - (100 / (1 + rs))
    
    return rsi_series


def macd(
    series: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        series: Price series (typically Close)
        fast_period: Fast EMA period (default 12)
        slow_period: Slow EMA period (default 26)
        signal_period: Signal line EMA period (default 9)
    
    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    fast_ema = ema(series, fast_period)
    slow_ema = ema(series, slow_period)
    
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def bollinger_bands(
    series: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.
    
    Args:
        series: Price series (typically Close)
        period: SMA period (default 20)
        std_dev: Standard deviation multiplier (default 2.0)
    
    Returns:
        Tuple of (Upper Band, Middle Band, Lower Band)
    """
    middle_band = sma(series, period)
    std = series.rolling(period).std()
    
    upper_band = middle_band + (std_dev * std)
    lower_band = middle_band - (std_dev * std)
    
    return upper_band, middle_band, lower_band


def volume_sma(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    Calculate Simple Moving Average of Volume.
    
    Args:
        df: DataFrame with Volume column
        period: SMA period (default 20)
    
    Returns:
        Volume SMA series
    """
    return df['Volume'].rolling(window=period).mean()


def is_bullish_engulfing(df: pd.DataFrame) -> pd.Series:
    """
    Detect Bullish Engulfing candlestick pattern.
    
    A bullish engulfing pattern occurs when:
    - Current candle's body completely engulfs previous candle's body
    - Current candle closes higher than it opens (bullish)
    - Previous candle closed lower than it opened (bearish)
    
    Args:
        df: DataFrame with Open, High, Low, Close columns
    
    Returns:
        Boolean series indicating bullish engulfing pattern
    """
    # Current candle is bullish
    current_bullish = df['Close'] > df['Open']
    
    # Previous candle is bearish
    prev_bearish = df['Close'].shift(1) < df['Open'].shift(1)
    
    # Current body engulfs previous body
    engulfs_open = df['Open'] < df['Close'].shift(1)
    engulfs_close = df['Close'] > df['Open'].shift(1)
    
    bullish_engulfing = (
        current_bullish & 
        prev_bearish & 
        engulfs_open & 
        engulfs_close
    )
    
    return bullish_engulfing


def is_hammer(df: pd.DataFrame) -> pd.Series:
    """
    Detect Hammer candlestick pattern.
    
    A hammer has:
    - Small real body at the upper end of the trading range
    - Long lower shadow (at least 2x the body)
    - Little or no upper shadow
    
    Args:
        df: DataFrame with Open, High, Low, Close columns
    
    Returns:
        Boolean series indicating hammer pattern
    """
    body = abs(df['Close'] - df['Open'])
    upper_shadow = df['High'] - df[['Open', 'Close']].max(axis=1)
    lower_shadow = df[['Open', 'Close']].min(axis=1) - df['Low']
    
    # Body is small relative to range
    small_body = body < (df['High'] - df['Low']) * 0.3
    
    # Lower shadow is at least 2x the body
    long_lower_shadow = lower_shadow >= (body * 2)
    
    # Upper shadow is small
    small_upper_shadow = upper_shadow < body
    
    hammer = small_body & long_lower_shadow & small_upper_shadow
    
    return hammer


def is_shooting_star(df: pd.DataFrame) -> pd.Series:
    """
    Detect Shooting Star candlestick pattern (bearish reversal).
    
    A shooting star has:
    - Small real body at the lower end of the trading range
    - Long upper shadow (at least 2x the body)
    - Little or no lower shadow
    
    Args:
        df: DataFrame with Open, High, Low, Close columns
    
    Returns:
        Boolean series indicating shooting star pattern
    """
    body = abs(df['Close'] - df['Open'])
    upper_shadow = df['High'] - df[['Open', 'Close']].max(axis=1)
    lower_shadow = df[['Open', 'Close']].min(axis=1) - df['Low']
    
    # Body is small relative to range
    small_body = body < (df['High'] - df['Low']) * 0.3
    
    # Upper shadow is at least 2x the body
    long_upper_shadow = upper_shadow >= (body * 2)
    
    # Lower shadow is small
    small_lower_shadow = lower_shadow < body
    
    shooting_star = small_body & long_upper_shadow & small_lower_shadow
    
    return shooting_star


def is_bearish_engulfing(df: pd.DataFrame) -> pd.Series:
    """
    Detect Bearish Engulfing candlestick pattern.
    
    Args:
        df: DataFrame with Open, High, Low, Close columns
    
    Returns:
        Boolean series indicating bearish engulfing pattern
    """
    # Current candle is bearish
    current_bearish = df['Close'] < df['Open']
    
    # Previous candle is bullish
    prev_bullish = df['Close'].shift(1) > df['Open'].shift(1)
    
    # Current body engulfs previous body
    engulfs_open = df['Open'] > df['Close'].shift(1)
    engulfs_close = df['Close'] < df['Open'].shift(1)
    
    bearish_engulfing = (
        current_bearish & 
        prev_bullish & 
        engulfs_open & 
        engulfs_close
    )
    
    return bearish_engulfing


def calculate_slope(series: pd.Series, lookback: int = 5) -> pd.Series:
    """
    Calculate the slope of a series using linear regression.
    
    Args:
        series: Series to calculate slope for
        lookback: Number of periods to use for slope calculation
    
    Returns:
        Slope series
    """
    def calc_slope(window):
        if len(window) < 2:
            return np.nan
        x = np.arange(len(window))
        y = window.values
        slope = np.polyfit(x, y, 1)[0]
        return slope
    
    slope_series = series.rolling(window=lookback).apply(calc_slope, raw=False)
    return slope_series
