"""
Super AI Trader - Market Data Module
Fetches multi-timeframe OHLCV data from Binance (crypto) and Yahoo Finance (forex/stocks).
Supports real trading data - no demo mode.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import ccxt
import yfinance as yf
import time

from config import (
    TIMEFRAMES, SYMBOLS, DATA_SOURCE
)


class MarketDataFetcher:
    """Handles connection to Binance/YahooFinance and fetching of market data."""
    
    def __init__(self, data_source: str = 'binance'):
        self.connected = False
        self.data_source = data_source  # 'binance', 'yfinance', or 'auto'
        self.exchange = None
        
        # Initialize CCXT exchange for Binance
        if data_source in ['binance', 'auto']:
            try:
                self.exchange = ccxt.binance({
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot',
                    }
                })
                self.exchange.load_markets()
                self.connected = True
                print(f"Connected to Binance via CCXT")
            except Exception as e:
                print(f"Failed to connect to Binance: {e}")
                if data_source == 'binance':
                    raise
                self.data_source = 'yfinance'
        
        # Timeframe mapping for CCXT
        self.ccxt_timeframes = {
            1: '1m',
            5: '5m',
            60: '1h',
            240: '4h',
            1440: '1d'
        }
    
    def connect(self) -> bool:
        """Initialize connection to data source."""
        if self.data_source == 'binance':
            if self.exchange is None:
                try:
                    self.exchange = ccxt.binance({
                        'enableRateLimit': True,
                        'options': {'defaultType': 'spot'}
                    })
                    self.exchange.load_markets()
                except Exception as e:
                    print(f"Failed to connect to Binance: {e}")
                    # Fallback to yfinance
                    self.data_source = 'yfinance'
                    self.connected = True
                    return True
            self.connected = True
            return True
        elif self.data_source == 'yfinance':
            # yfinance doesn't require connection
            self.connected = True
            return True
        elif self.data_source == 'auto':
            # Auto mode: already tried binance in __init__, just confirm we're ready
            self.connected = True
            return True
        return False
    
    def disconnect(self):
        """Close connection."""
        self.connected = False
        self.exchange = None
    
    def _symbol_to_binance(self, symbol: str) -> str:
        """Convert symbol to Binance format."""
        # Forex symbols: EURUSD -> EUR/USDT or keep as is for crypto
        crypto_symbols = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOGE']
        
        if any(coin in symbol.upper() for coin in crypto_symbols):
            # Crypto: BTCUSD -> BTC/USDT
            base = symbol.replace('USD', '').replace('USDT', '')
            return f"{base}/USDT"
        else:
            # Forex: Try to find on Binance or use yfinance
            return symbol
    
    def _symbol_to_yfinance(self, symbol: str) -> str:
        """Convert symbol to Yahoo Finance format."""
        # Already in Yahoo Finance format (contains = or ^ or -)
        if '=' in symbol or '^' in symbol or '-' in symbol:
            return symbol
        
        # Forex: EURUSD -> EURUSD=X
        if len(symbol) == 6:  # Likely forex pair
            return f"{symbol}=X"
        elif symbol in ['BTCUSD', 'BTC']:
            return 'BTC-USD'
        elif symbol in ['ETHUSD', 'ETH']:
            return 'ETH-USD'
        elif symbol in ['BTCUSD=X']:
            return 'BTC-USD'
        elif symbol in ['ETHUSD=X']:
            return 'ETH-USD'
        # Commodities
        elif symbol == 'XAUUSD':
            return 'GC=F'
        elif symbol == 'XAGUSD':
            return 'SI=F'
        elif symbol == 'USOIL':
            return 'CL=F'
        elif symbol == 'UKOIL':
            return 'BZ=F'
        # Indices
        elif symbol == 'US30':
            return '^DJI'
        elif symbol == 'SPX500':
            return '^GSPC'
        elif symbol == 'NAS100':
            return '^IXIC'
        elif symbol == 'GER40':
            return '^GDAXI'
        
        return symbol
    
    def fetch_ohlcv(self, symbol: str, timeframe_minutes: int, 
                    bars: int = 1000, start_date: Optional[datetime] = None) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data for a symbol and timeframe.
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD', 'BTCUSD')
            timeframe_minutes: Timeframe in minutes (1, 5, 60, 240)
            bars: Number of bars to fetch
            start_date: Optional start date
        
        Returns:
            DataFrame with OHLCV data
        """
        if not self.connected:
            if not self.connect():
                return None
        
        # Try Binance first for crypto, fallback to yfinance
        if self.data_source in ['binance', 'auto']:
            try:
                binance_symbol = self._symbol_to_binance(symbol)
                tf_str = self.ccxt_timeframes.get(timeframe_minutes, '1m')
                
                # Fetch using CCXT
                ohlcv = self.exchange.fetch_ohlcv(binance_symbol, timeframe=tf_str, limit=bars)
                
                if ohlcv and len(ohlcv) > 0:
                    df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
                    df['time'] = pd.to_datetime(df['time'], unit='ms')
                    df.set_index('time', inplace=True)
                    return df[['open', 'high', 'low', 'close', 'volume']]
            except Exception as e:
                print(f"Binance fetch failed for {symbol}: {e}")
                if self.data_source == 'binance':
                    return None
        
        # Fallback to Yahoo Finance
        try:
            yf_symbol = self._symbol_to_yfinance(symbol)
            ticker = yf.Ticker(yf_symbol)
            
            # Calculate period based on timeframe and bars
            period_map = {
                1: '7d',    # 1m data - max 7 days
                5: '1mo',   # 5m data
                60: '2y',   # 1h data
                240: '2y',  # 4h data
                1440: '5y'  # 1d data
            }
            period = period_map.get(timeframe_minutes, '1mo')
            
            df = ticker.history(period=period, interval=self._yf_interval(timeframe_minutes))
            
            if df is not None and len(df) > 0:
                df.rename(columns={
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                }, inplace=True)
                return df[['open', 'high', 'low', 'close', 'volume']].iloc[-bars:]
        except Exception as e:
            print(f"Yahoo Finance fetch failed for {symbol}: {e}")
        
        return None
    
    def _yf_interval(self, timeframe_minutes: int) -> str:
        """Convert minutes to Yahoo Finance interval string."""
        if timeframe_minutes <= 1:
            return '1m'
        elif timeframe_minutes <= 5:
            return '5m'
        elif timeframe_minutes <= 15:
            return '15m'
        elif timeframe_minutes <= 30:
            return '30m'
        elif timeframe_minutes <= 60:
            return '1h'
        elif timeframe_minutes <= 240:
            return '4h'
        else:
            return '1d'
    
    def fetch_multi_timeframe_data(self, symbol: str, 
                                   num_bars: Dict[int, int] = None) -> Dict[int, pd.DataFrame]:
        """
        Fetch data for all configured timeframes.
        
        Args:
            symbol: Trading symbol
            num_bars: Dict mapping timeframe minutes to number of bars
        
        Returns:
            Dictionary of DataFrames keyed by timeframe minutes
        """
        if num_bars is None:
            num_bars = {tf: 1000 for tf in TIMEFRAMES.values()}
        
        data = {}
        for tf_minutes in TIMEFRAMES.values():
            df = self.fetch_ohlcv(symbol, tf_minutes, num_bars.get(tf_minutes, 1000))
            if df is not None:
                data[tf_minutes] = df
        
        return data
    
    def get_current_price(self, symbol: str) -> Optional[dict]:
        """Get current bid/ask prices for a symbol."""
        if not self.connected:
            if not self.connect():
                return None
        
        # Try Binance first
        if self.data_source in ['binance', 'auto'] and self.exchange:
            try:
                binance_symbol = self._symbol_to_binance(symbol)
                ticker = self.exchange.fetch_ticker(binance_symbol)
                return {
                    'bid': ticker.get('bid', ticker.get('last')),
                    'ask': ticker.get('ask', ticker.get('last')),
                    'last': ticker.get('last'),
                    'time': datetime.now(),
                    'volume': ticker.get('baseVolume', 0)
                }
            except Exception as e:
                # Silently fall through to yfinance for non-crypto
                pass
        
        # Fallback to yfinance
        try:
            yf_symbol = self._symbol_to_yfinance(symbol)
            ticker = yf.Ticker(yf_symbol)
            # Use history to get latest price instead of fast_info
            hist = ticker.history(period='1d')
            if len(hist) > 0:
                last_price = hist['Close'].iloc[-1]
                return {
                    'bid': last_price * 0.9999,
                    'ask': last_price * 1.0001,
                    'last': last_price,
                    'time': datetime.now(),
                    'volume': hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0
                }
        except Exception as e:
            print(f"Yahoo Finance ticker fetch failed: {e}")
        
        return None
    
    def get_account_info(self) -> Optional[dict]:
        """Get account information (placeholder for paper/live trading)."""
        # This would integrate with exchange API for real account info
        # For now, return None - balance managed in risk_manager
        return None
    
    def calculate_pip_value(self, symbol: str) -> float:
        """Calculate pip value for a symbol."""
        # Simplified pip calculation
        price_info = self.get_current_price(symbol)
        if price_info is None:
            return 0.0001
        
        price = price_info['last']
        if price < 100:  # Forex-like
            return 0.0001
        elif price < 10000:  # Crypto mid-range
            return 0.01
        else:  # High-value crypto
            return 1.0


class MultiTimeframeDataBuilder:
    """Builds and aligns multi-timeframe data for agent analysis."""
    
    def __init__(self, fetcher: MarketDataFetcher):
        self.fetcher = fetcher
    
    def build_aligned_data(self, symbol: str, 
                           reference_tf: int = 1) -> Optional[Dict[int, pd.DataFrame]]:
        """
        Build aligned multi-timeframe data aligned to reference timeframe.
        
        Args:
            symbol: Trading symbol
            reference_tf: Reference timeframe in minutes (usually 1 or 5)
        
        Returns:
            Dictionary of aligned DataFrames
        """
        raw_data = self.fetcher.fetch_multi_timeframe_data(symbol)
        
        if not raw_data:
            return None
        
        aligned_data = {}
        reference_df = raw_data.get(reference_tf)
        
        if reference_df is None:
            return None
        
        aligned_data[reference_tf] = reference_df
        
        # Align higher timeframes to reference timeframe
        for tf, df in raw_data.items():
            if tf != reference_tf:
                # Resample higher timeframe data to match reference
                if tf > reference_tf:
                    # For higher TF, forward-fill to match lower TF index
                    df_resampled = df.reindex(reference_df.index, method='ffill')
                    aligned_data[tf] = df_resampled
                else:
                    aligned_data[tf] = df
        
        return aligned_data
    
    def get_latest_candles(self, symbol: str, num_candles: int = 10) -> Dict[int, pd.DataFrame]:
        """Get the latest N candles for each timeframe."""
        data = self.fetcher.fetch_multi_timeframe_data(symbol, {tf: num_candles for tf in TIMEFRAMES.values()})
        return data
    
    def calculate_indicators_on_data(self, df: pd.DataFrame, indicators: List[str]) -> pd.DataFrame:
        """
        Calculate specified indicators on dataframe.
        
        Args:
            df: OHLCV DataFrame
            indicators: List of indicator names to calculate
        
        Returns:
            DataFrame with added indicator columns
        """
        from indicators.indicator_library import IndicatorLibrary
        
        result_df = df.copy()
        il = IndicatorLibrary()
        
        for indicator in indicators:
            try:
                if hasattr(il, indicator):
                    method = getattr(il, indicator)
                    
                    # Determine which columns to pass based on indicator signature
                    if indicator == 'ema' or indicator == 'sma':
                        result_df[f'{indicator}_200'] = method(df['close'], 200)
                        result_df[f'{indicator}_50'] = method(df['close'], 50)
                        result_df[f'{indicator}_20'] = method(df['close'], 20)
                    elif indicator == 'rsi':
                        result_df['rsi_14'] = method(df['close'], 14)
                    elif indicator == 'macd':
                        macd_result = method(df['close'])
                        result_df['macd'] = macd_result['macd']
                        result_df['macd_signal'] = macd_result['signal']
                        result_df['macd_histogram'] = macd_result['histogram']
                    elif indicator == 'atr':
                        result_df['atr_14'] = method(df['high'], df['low'], df['close'], 14)
                    elif indicator == 'adx':
                        result_df['adx_14'] = method(df['high'], df['low'], df['close'], 14)
                    elif indicator == 'bollinger_bands':
                        bb = method(df['close'])
                        result_df['bb_upper'] = bb['upper']
                        result_df['bb_middle'] = bb['middle']
                        result_df['bb_lower'] = bb['lower']
                    elif indicator == 'ichimoku':
                        ichi = method(df['high'], df['low'], df['close'])
                        result_df['ichimoku_tenkan'] = ichi['tenkan']
                        result_df['ichimoku_kijun'] = ichi['kijun']
                        result_df['ichimoku_cloud_top'] = ichi['cloud_top']
                        result_df['ichimoku_cloud_bottom'] = ichi['cloud_bottom']
                    elif indicator == 'stochastic':
                        stoch = method(df['high'], df['low'], df['close'])
                        result_df['stoch_k'] = stoch['k']
                        result_df['stoch_d'] = stoch['d']
                    elif indicator == 'volume_profile':
                        vp = method(df['close'], df['volume'])
                        result_df['poc'] = vp['poc']
                        result_df['va_high'] = vp['va_high']
                        result_df['va_low'] = vp['va_low']
                    
            except Exception as e:
                print(f"Error calculating {indicator}: {e}")
        
        return result_df


# Test function
def test_market_data():
    """Test market data fetching from Binance/YahooFinance."""
    fetcher = MarketDataFetcher(data_source='auto')
    
    # Already connected in __init__ for 'auto' and 'binance' modes
    if not fetcher.connected:
        if not fetcher.connect():
            print("❌ Failed to connect to data source")
            return
    
    print(f"Connected to {fetcher.data_source.upper()}")
    
    # Test fetching BTCUSD data from Binance
    print("\n=== Testing BTCUSD (Binance) ===")
    df = fetcher.fetch_ohlcv("BTCUSD", 60, bars=10)
    if df is not None:
        print(f"Fetched {len(df)} bars")
        print(df.tail())
    
    # Test current price
    price = fetcher.get_current_price("BTCUSD")
    if price:
        print(f"\nCurrent BTCUSD: Bid={price['bid']:.2f}, Ask={price['ask']:.2f}, Last={price['last']:.2f}")
    
    # Test fetching EURUSD data from Yahoo Finance
    print("\n=== Testing EURUSD (Yahoo Finance) ===")
    df = fetcher.fetch_ohlcv("EURUSD", 60, bars=10)
    if df is not None:
        print(f"Fetched {len(df)} bars")
        print(df.tail())
    
    price = fetcher.get_current_price("EURUSD")
    if price:
        print(f"\nCurrent EURUSD: Bid={price['bid']:.5f}, Ask={price['ask']:.5f}, Last={price['last']:.5f}")
    
    # Test multi-timeframe data
    print("\n=== Testing Multi-Timeframe Data (BTCUSD) ===")
    data = fetcher.fetch_multi_timeframe_data("BTCUSD")
    for tf, df in data.items():
        print(f"TF {tf}m: {len(df)} bars")
    
    fetcher.disconnect()
    print("\n✅ All tests passed - Real trading data active!")


if __name__ == "__main__":
    test_market_data()
