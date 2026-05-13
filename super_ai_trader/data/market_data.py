"""
Super AI Trader - Market Data Module
Fetches multi-timeframe OHLCV data from MetaTrader 5.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, List

# Try to import MetaTrader5, use mock if not available
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None  # Mock placeholder

from config import (
    MT5_LOGIN, MT5_PASSWORD, MT5_SERVER, MT5_PATH,
    TIMEFRAMES, SYMBOLS
)


class MarketDataFetcher:
    """Handles connection to MT5 and fetching of market data."""
    
    def __init__(self):
        self.connected = False
        if MT5_AVAILABLE:
            self.mt5_timeframes = {
                1: mt5.TIMEFRAME_M1,
                5: mt5.TIMEFRAME_M5,
                60: mt5.TIMEFRAME_H1,
                240: mt5.TIMEFRAME_H4
            }
        else:
            # Demo mode timeframe mapping (just use minute values)
            self.mt5_timeframes = {
                1: 1,
                5: 5,
                60: 60,
                240: 240
            }
    
    def connect(self) -> bool:
        """Initialize connection to MetaTrader 5."""
        if not MT5_AVAILABLE:
            print("MetaTrader5 not available - running in demo mode")
            self.connected = True
            return True
        
        if not mt5.initialize(path=MT5_PATH, login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
            print(f"MT5 initialization failed: {mt5.last_error()}")
            return False
        
        self.connected = True
        print(f"Connected to MT5: {mt5.account_info().login}")
        return True
    
    def disconnect(self):
        """Close MT5 connection."""
        if self.connected and MT5_AVAILABLE:
            mt5.shutdown()
        self.connected = False
    
    def get_symbol_info(self, symbol: str) -> Optional[dict]:
        """Get symbol information."""
        info = mt5.symbol_info(symbol)
        if info is None:
            return None
        
        if not info.visible:
            if not mt5.symbol_select(symbol, True):
                return None
            info = mt5.symbol_info(symbol)
        
        return {
            'name': info.name,
            'description': info.description,
            'point': info.point,
            'digits': info.digits,
            'spread': info.spread,
            'trade_contract_size': info.trade_contract_size,
            'volume_min': info.volume_min,
            'volume_max': info.volume_max,
            'volume_step': info.volume_step
        }
    
    def fetch_ohlcv(self, symbol: str, timeframe_minutes: int, 
                    bars: int = 1000, start_date: Optional[datetime] = None) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data for a symbol and timeframe.
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframe_minutes: Timeframe in minutes (1, 5, 60, 240)
            bars: Number of bars to fetch
            start_date: Optional start date
        
        Returns:
            DataFrame with OHLCV data
        """
        if not self.connected:
            if not self.connect():
                return None
        
        tf = self.mt5_timeframes.get(timeframe_minutes)
        if tf is None:
            print(f"Unsupported timeframe: {timeframe_minutes} minutes")
            return None
        
        if start_date:
            rates = mt5.copy_rates_from(symbol, tf, start_date, bars)
        else:
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
        
        if rates is None or len(rates) == 0:
            print(f"No data received for {symbol} TF:{timeframe_minutes}")
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        df.rename(columns={
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'tick_volume': 'volume'
        }, inplace=True)
        
        return df[['open', 'high', 'low', 'close', 'volume']]
    
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
        
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        
        return {
            'bid': tick.bid,
            'ask': tick.ask,
            'last': tick.last,
            'time': datetime.fromtimestamp(tick.time),
            'volume': tick.volume
        }
    
    def get_account_info(self) -> Optional[dict]:
        """Get MT5 account information."""
        if not self.connected:
            return None
        
        info = mt5.account_info()
        if info is None:
            return None
        
        return {
            'login': info.login,
            'balance': info.balance,
            'equity': info.equity,
            'margin': info.margin,
            'margin_free': info.margin_free,
            'margin_level': info.margin_level,
            'profit': info.profit,
            'leverage': info.leverage
        }
    
    def calculate_pip_value(self, symbol: str) -> float:
        """Calculate pip value for a symbol."""
        info = self.get_symbol_info(symbol)
        if info is None:
            return 0.0001
        
        if info['digits'] == 5 or info['digits'] == 3:
            return 0.00001 * info['trade_contract_size']
        else:
            return 0.0001 * info['trade_contract_size']


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


# Demo/test function
def test_market_data():
    """Test market data fetching (requires MT5 connection)."""
    fetcher = MarketDataFetcher()
    
    if fetcher.connect():
        # Test fetching EURUSD data
        df = fetcher.fetch_ohlcv("EURUSD", 60, bars=100)
        if df is not None:
            print(f"Fetched {len(df)} bars")
            print(df.tail())
        
        # Test current price
        price = fetcher.get_current_price("EURUSD")
        if price:
            print(f"Current EURUSD: Bid={price['bid']}, Ask={price['ask']}")
        
        # Test account info
        account = fetcher.get_account_info()
        if account:
            print(f"Account Balance: {account['balance']}")
        
        fetcher.disconnect()
    else:
        print("Failed to connect to MT5 - running in demo mode")
        # Create sample data for testing without MT5
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=1000, freq='1H')
        sample_data = pd.DataFrame({
            'open': np.random.randn(1000).cumsum() + 1.1,
            'high': np.random.randn(1000).cumsum() + 1.1 + np.abs(np.random.randn(1000)),
            'low': np.random.randn(1000).cumsum() + 1.1 - np.abs(np.random.randn(1000)),
            'close': np.random.randn(1000).cumsum() + 1.1,
            'volume': np.random.randint(100, 1000, 1000)
        }, index=dates)
        return sample_data


if __name__ == "__main__":
    test_market_data()
