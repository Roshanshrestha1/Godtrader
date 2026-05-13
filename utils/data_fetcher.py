"""
Utility functions for the Stable Stock Analysis System.
Includes data fetching with retries, rate limiting, and caching.
"""

import time
import logging
from functools import wraps
from typing import Optional, Callable, Any, Dict
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Import config for symbol mapping
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config

logger = logging.getLogger(__name__)


def get_yahoo_ticker(symbol: str) -> str:
    """
    Get the Yahoo Finance ticker for a given Exness symbol.
    
    Args:
        symbol: Symbol in Exness format (e.g., 'EURUSD', 'BTCUSD', 'XAUUSD')
    
    Returns:
        Symbol in Yahoo Finance format (e.g., 'EURUSD=X', 'BTC-USD', 'GC=F')
    """
    return config.get_yahoo_ticker(symbol)


class DataCache:
    """In-memory cache for OHLCV data to avoid redundant API calls."""
    
    def __init__(self, max_age_seconds: int = 120):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.max_age_seconds = max_age_seconds
    
    def get(self, symbol: str, interval: str) -> Optional[pd.DataFrame]:
        """Get cached data if it exists and is not stale."""
        key = f"{symbol}_{interval}"
        if key in self._cache:
            cached = self._cache[key]
            age = (datetime.now() - cached['timestamp']).total_seconds()
            if age < self.max_age_seconds:
                logger.debug(f"Cache hit for {symbol} {interval}")
                return cached['data']
            else:
                logger.debug(f"Cache expired for {symbol} {interval}")
                del self._cache[key]
        return None
    
    def set(self, symbol: str, interval: str, data: pd.DataFrame) -> None:
        """Store data in cache."""
        key = f"{symbol}_{interval}"
        self._cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }
        logger.debug(f"Cached data for {symbol} {interval}")
    
    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        logger.info("Data cache cleared")


# Global cache instance
data_cache = DataCache()


def rate_limit(calls_per_minute: int = 30):
    """
    Decorator to rate-limit function calls.
    
    Args:
        calls_per_minute: Maximum number of calls allowed per minute
    """
    interval = 60.0 / calls_per_minute
    last_call = {'time': 0}
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            elapsed = time.time() - last_call['time']
            if elapsed < interval:
                sleep_time = interval - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            result = func(*args, **kwargs)
            last_call['time'] = time.time()
            return result
        return wrapper
    return decorator


def retry_with_backoff(max_attempts: int = 3, base_delay: float = 1.0):
    """
    Decorator to retry failed function calls with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds for backoff calculation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed: {e}")
            
            raise last_exception
        return wrapper
    return decorator


@rate_limit(calls_per_minute=30)
@retry_with_backoff(max_attempts=3, base_delay=1.0)
def fetch_ohlcv(
    symbol: str,
    interval: str = "1h",
    period: str = "7d",
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Fetch OHLCV data from Yahoo Finance with caching, rate limiting, and retries.
    
    Args:
        symbol: Trading symbol (e.g., 'AAPL', 'EURUSD=X', 'BTC-USD')
               Can be Exness format (e.g., 'EURUSD', 'BTCUSD') - will be auto-converted
        interval: Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)
        period: Data history period (1d, 5d, 7d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        use_cache: Whether to use cached data if available
    
    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume
    
    Raises:
        ValueError: If no data is available for the symbol
        Exception: If all retry attempts fail
    """
    # Convert Exness symbol format to Yahoo Finance format
    yahoo_symbol = get_yahoo_ticker(symbol)
    
    # Check cache first (use original symbol for cache key to avoid confusion)
    if use_cache:
        cached_data = data_cache.get(symbol, interval)
        if cached_data is not None:
            return cached_data
    
    logger.info(f"Fetching data for {symbol} ({yahoo_symbol}) on {interval} timeframe")
    
    try:
        # Use direct Yahoo Finance API with proper headers (more reliable than yfinance wrapper)
        import requests
        
        # Calculate timestamps based on period
        end_ts = int(datetime.now().timestamp())
        
        # Parse period to get start timestamp
        period_value = int(''.join(filter(str.isdigit, period)))
        period_unit = ''.join(filter(str.isalpha, period)) or 'd'
        
        if period_unit == 'd':
            days = period_value
        elif period_unit == 'mo':
            days = period_value * 30
        elif period_unit == 'y':
            days = period_value * 365
        else:
            days = 7  # default
        
        start_ts = int((datetime.now() - timedelta(days=days)).timestamp())
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
        params = {
            'interval': interval,
            'period1': start_ts,
            'period2': end_ts,
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'chart' not in data or 'result' not in data['chart'] or not data['chart']['result']:
            raise ValueError(f"No data available for symbol: {symbol} ({yahoo_symbol})")
        
        result = data['chart']['result'][0]
        quotes = result['indicators']['quote'][0]
        timestamps = result.get('timestamp', [])
        
        if not timestamps:
            raise ValueError(f"No data available for symbol: {symbol} ({yahoo_symbol})")
        
        # Create DataFrame
        df = pd.DataFrame({
            'Open': quotes.get('open', []),
            'High': quotes.get('high', []),
            'Low': quotes.get('low', []),
            'Close': quotes.get('close', []),
            'Volume': quotes.get('volume', [])
        })
        
        # Add datetime index
        df.index = pd.to_datetime(timestamps, unit='s')
        
        if df.empty or len(df) == 0:
            raise ValueError(f"No data available for symbol: {symbol} ({yahoo_symbol})")
        
        # Validate data quality
        if len(df) < 10:
            logger.warning(f"Only {len(df)} candles received for {symbol}")
        
        # Check for stale data
        latest_timestamp = df.index[-1]
        current_time = datetime.now()
        
        # Convert to timezone-naive for comparison
        if latest_timestamp.tzinfo is not None:
            latest_timestamp = latest_timestamp.replace(tzinfo=None)
        
        age_seconds = (current_time - latest_timestamp).total_seconds()
        
        # For intraday data, check staleness
        if interval in ['1m', '5m', '15m', '30m', '1h']:
            max_staleness = 120  # 2 minutes
            if age_seconds > max_staleness * 10:  # Allow some slack
                logger.warning(
                    f"Data may be stale: last candle is {age_seconds/60:.1f} minutes old"
                )
        
        # Cache the data (using original symbol as key)
        if use_cache:
            data_cache.set(symbol, interval, df)
        
        logger.info(f"Successfully fetched {len(df)} candles for {symbol}")
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch data for {symbol}: {e}")
        raise


def validate_symbol(symbol: str) -> bool:
    """
    Basic validation of symbol format.
    
    Args:
        symbol: Trading symbol to validate
    
    Returns:
        True if symbol appears valid, False otherwise
    """
    if not symbol or not isinstance(symbol, str):
        return False
    
    # Remove common suffixes for validation
    clean_symbol = symbol.replace('=X', '').replace('-USD', '').replace('=F', '')
    
    # Basic checks
    if len(clean_symbol) < 2 or len(clean_symbol) > 10:
        return False
    
    if not clean_symbol.replace('.', '').replace('-', '').isalnum():
        return False
    
    return True


def sanitize_timeframe(timeframe: str) -> str:
    """
    Sanitize and normalize timeframe string.
    
    Args:
        timeframe: Timeframe string (e.g., '1m', '5min', '1hour')
    
    Returns:
        Normalized timeframe string
    
    Raises:
        ValueError: If timeframe is invalid
    """
    # Mapping of common variations
    timeframe_map = {
        '1m': '1m', '1min': '1m', '1minute': '1m',
        '5m': '5m', '5min': '5m', '5minute': '5m',
        '15m': '15m', '15min': '15m', '15minute': '15m',
        '30m': '30m', '30min': '30m', '30minute': '30m',
        '1h': '1h', '1hour': '1h', '60m': '1h',
        '4h': '4h', '4hour': '4h',
        '1d': '1d', '1day': '1d', 'daily': '1d',
        '1w': '1wk', '1week': '1wk', 'weekly': '1wk',
        '1mo': '1mo', '1month': '1mo', 'monthly': '1mo'
    }
    
    tf_lower = timeframe.lower().strip()
    
    if tf_lower in timeframe_map:
        return timeframe_map[tf_lower]
    
    # If already in correct format
    if tf_lower in ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1wk', '1mo']:
        return tf_lower
    
    raise ValueError(f"Invalid timeframe: {timeframe}")


def format_price(price: float, symbol: str = "") -> str:
    """
    Format price based on symbol type.
    
    Args:
        price: Price value
        symbol: Trading symbol (used to determine precision)
    
    Returns:
        Formatted price string
    """
    # Crypto typically needs more decimals
    if 'BTC' in symbol or 'ETH' in symbol or 'USD=X' in symbol:
        if price > 1000:
            return f"{price:,.2f}"
        elif price > 1:
            return f"{price:.4f}"
        else:
            return f"{price:.6f}"
    
    # Forex pairs
    if '=X' in symbol or len(symbol) == 7:  # EURUSD etc.
        return f"{price:.5f}"
    
    # Stocks and commodities
    if price > 100:
        return f"{price:.2f}"
    elif price > 1:
        return f"{price:.3f}"
    else:
        return f"{price:.4f}"


def calculate_time_difference(timestamp1: datetime, timestamp2: datetime) -> timedelta:
    """
    Calculate absolute time difference between two timestamps.
    
    Args:
        timestamp1: First timestamp
        timestamp2: Second timestamp
    
    Returns:
        Timedelta representing the difference
    """
    # Ensure both are timezone-naive
    if timestamp1.tzinfo is not None:
        timestamp1 = timestamp1.replace(tzinfo=None)
    if timestamp2.tzinfo is not None:
        timestamp2 = timestamp2.replace(tzinfo=None)
    
    return abs(timestamp1 - timestamp2)
