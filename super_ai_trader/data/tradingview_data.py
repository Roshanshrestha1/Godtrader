"""
Super AI Trader - TradingView Data Module
Fetches real-time technical analysis data from TradingView for USD currency pairs.
Uses the tradingview-ta library to get real market data and technical indicators.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from tradingview_ta import TA_Handler, Interval, Exchange

from config import TIMEFRAMES, SYMBOLS


class TradingViewDataFetcher:
    """Handles connection to TradingView and fetching of market data for USD pairs."""
    
    def __init__(self):
        self.connected = False
        self.screener = "forex"  # Default to forex screener
        self.exchange_type = "forex"  # Default exchange type for forex
        
        # Timeframe mapping for TradingView
        self.tv_intervals = {
            1: Interval.INTERVAL_1_MINUTE,
            5: Interval.INTERVAL_5_MINUTES,
            15: Interval.INTERVAL_15_MINUTES,
            30: Interval.INTERVAL_30_MINUTES,
            60: Interval.INTERVAL_1_HOUR,
            240: Interval.INTERVAL_4_HOURS,
            1440: Interval.INTERVAL_1_DAY,
            10080: Interval.INTERVAL_1_WEEK,
        }
        
        # Symbol mapping for TradingView (Forex pairs)
        self.symbol_map = {
            'EURUSD': 'EURUSD',
            'GBPUSD': 'GBPUSD',
            'USDJPY': 'USDJPY',
            'USDCHF': 'USDCHF',
            'AUDUSD': 'AUDUSD',
            'USDCAD': 'USDCAD',
            'NZDUSD': 'NZDUSD',
            'BTCUSD': 'BTCUSD',
            'ETHUSD': 'ETHUSD',
        }
        
        print("TradingView Data Fetcher initialized")
    
    def connect(self) -> bool:
        """Initialize connection to TradingView."""
        try:
            # Test connection by fetching analysis for a symbol
            test_symbol = self._get_tv_symbol('EURUSD')
            if test_symbol:
                self.connected = True
                print(f"Connected to TradingView (Screener: {self.screener})")
                return True
        except Exception as e:
            print(f"Failed to connect to TradingView: {e}")
            self.connected = False
        return False
    
    def disconnect(self):
        """Close connection."""
        self.connected = False
    
    def _get_tv_symbol(self, symbol: str) -> Optional[str]:
        """Convert symbol to TradingView format."""
        return self.symbol_map.get(symbol.upper(), symbol)
    
    def _setup_handler(self, symbol: str, timeframe_minutes: int) -> TA_Handler:
        """Setup TA_Handler for a specific symbol and timeframe."""
        handler = TA_Handler()
        
        # Determine screener type
        crypto_symbols = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOGE']
        
        if any(coin in symbol.upper() for coin in crypto_symbols):
            # Crypto
            handler.set_screener_as_crypto()
            handler.set_exchange_as_crypto_or_stock('BINANCE')
        else:
            # Forex
            handler.set_screener_as_forex()
            handler.set_exchange_as_forex()
        
        # Set interval
        interval = self.tv_intervals.get(timeframe_minutes, Interval.INTERVAL_1_HOUR)
        handler.set_interval_as(interval)
        
        # Set symbol
        tv_symbol = self._get_tv_symbol(symbol)
        handler.set_symbol_as(tv_symbol)
        
        return handler
    
    def fetch_technical_analysis(self, symbol: str, timeframe_minutes: int = 60) -> Optional[dict]:
        """
        Fetch technical analysis data from TradingView.
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD', 'BTCUSD')
            timeframe_minutes: Timeframe in minutes
        
        Returns:
            Dictionary with technical analysis summary and indicators
        """
        if not self.connected:
            if not self.connect():
                return None
        
        try:
            # Setup handler
            handler = self._setup_handler(symbol, timeframe_minutes)
            
            # Get technical analysis
            ta_data = handler.get_analysis()
            
            if ta_data:
                return {
                    'symbol': symbol,
                    'timeframe': timeframe_minutes,
                    'timestamp': datetime.now(),
                    'summary': ta_data.summary,
                    'indicators': ta_data.indicators,
                    'oscillators': ta_data.oscillators,
                    'moving_averages': ta_data.moving_averages
                }
        except Exception as e:
            print(f"TradingView fetch failed for {symbol}: {e}")
        
        return None
    
    def fetch_ohlcv(self, symbol: str, timeframe_minutes: int, 
                    bars: int = 100) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data by getting indicator data from TradingView.
        Note: TradingView TA doesn't provide raw OHLCV directly, but we can extract
        open, high, low, close from the indicators.
        
        Args:
            symbol: Trading symbol
            timeframe_minutes: Timeframe in minutes
            bars: Number of bars (TradingView provides limited historical data)
        
        Returns:
            DataFrame with OHLCV data
        """
        if not self.connected:
            if not self.connect():
                return None
        
        try:
            # Setup handler
            handler = self._setup_handler(symbol, timeframe_minutes)
            
            # Get analysis which includes OHLC data
            ta_data = handler.get_analysis()
            
            if ta_data and ta_data.indicators:
                indicators = ta_data.indicators
                
                # Extract available OHLC data
                # Note: TradingView TA provides limited historical candles
                # We'll create a single-row DataFrame with current candle data
                data = {
                    'open': [indicators.get('open', 0)],
                    'high': [indicators.get('high', 0)],
                    'low': [indicators.get('low', 0)],
                    'close': [indicators.get('close', 0)],
                    'volume': [indicators.get('volume', 0)],
                }
                
                df = pd.DataFrame(data)
                df.index = [datetime.now()]
                
                return df[['open', 'high', 'low', 'close', 'volume']]
                
        except Exception as e:
            print(f"TradingView OHLCV fetch failed for {symbol}: {e}")
        
        return None
    
    def fetch_multi_timeframe_analysis(self, symbol: str, 
                                       timeframes: List[int] = None) -> Dict[int, dict]:
        """
        Fetch technical analysis for multiple timeframes.
        
        Args:
            symbol: Trading symbol
            timeframes: List of timeframes in minutes
        
        Returns:
            Dictionary of analysis results keyed by timeframe
        """
        if timeframes is None:
            timeframes = list(TIMEFRAMES.values())
        
        results = {}
        for tf in timeframes:
            analysis = self.fetch_technical_analysis(symbol, tf)
            if analysis:
                results[tf] = analysis
        
        return results
    
    def get_current_price(self, symbol: str) -> Optional[dict]:
        """Get current price for a symbol."""
        if not self.connected:
            if not self.connect():
                return None
        
        try:
            # Use 1-minute interval for current price
            handler = self._setup_handler(symbol, 1)
            
            ta_data = handler.get_analysis()
            
            if ta_data and ta_data.indicators:
                indicators = ta_data.indicators
                close_price = indicators.get('close', 0)
                
                return {
                    'bid': close_price * 0.9999,
                    'ask': close_price * 1.0001,
                    'last': close_price,
                    'time': datetime.now(),
                    'volume': indicators.get('volume', 0)
                }
        except Exception as e:
            print(f"TradingView price fetch failed for {symbol}: {e}")
        
        return None
        return None
    
    def get_recommendation(self, symbol: str, timeframe_minutes: int = 60) -> Optional[str]:
        """
        Get TradingView's overall recommendation for a symbol.
        
        Args:
            symbol: Trading symbol
            timeframe_minutes: Timeframe in minutes
        
        Returns:
            Recommendation string: 'STRONG_BUY', 'BUY', 'NEUTRAL', 'SELL', 'STRONG_SELL'
        """
        analysis = self.fetch_technical_analysis(symbol, timeframe_minutes)
        if analysis:
            return analysis['summary'].get('RECOMMENDATION', 'NEUTRAL')
        return None
    
    def calculate_pip_value(self, symbol: str) -> float:
        """Calculate pip value for a symbol."""
        price_info = self.get_current_price(symbol)
        if price_info is None:
            return 0.0001
        
        price = price_info['last']
        if price < 100:  # Forex-like (EURUSD, GBPUSD, etc.)
            return 0.0001
        elif price < 10000:  # Mid-range
            return 0.01
        else:  # High-value (BTC, etc.)
            return 1.0


class TradingViewDataBuilder:
    """Builds multi-timeframe data from TradingView for agent analysis."""
    
    def __init__(self, fetcher: TradingViewDataFetcher):
        self.fetcher = fetcher
    
    def build_analysis_summary(self, symbol: str) -> Optional[dict]:
        """
        Build a comprehensive analysis summary across all timeframes.
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Dictionary with multi-timeframe analysis summary
        """
        multi_tf_analysis = self.fetcher.fetch_multi_timeframe_analysis(symbol)
        
        if not multi_tf_analysis:
            return None
        
        summary = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'timeframes': {}
        }
        
        for tf, analysis in multi_tf_analysis.items():
            summary['timeframes'][tf] = {
                'recommendation': analysis['summary'].get('RECOMMENDATION', 'NEUTRAL'),
                'buy_signals': analysis['summary'].get('BUY', 0),
                'sell_signals': analysis['summary'].get('SELL', 0),
                'neutral_signals': analysis['summary'].get('NEUTRAL', 0),
                'current_price': analysis['indicators'].get('close', 0),
                'rsi': analysis['indicators'].get('RSI', 50),
                'macd': analysis['indicators'].get('MACD.macd', 0),
            }
        
        return summary
    
    def get_latest_candles(self, symbol: str, num_candles: int = 10) -> Dict[int, pd.DataFrame]:
        """Get the latest candles for each timeframe."""
        data = {}
        for tf in TIMEFRAMES.values():
            df = self.fetcher.fetch_ohlcv(symbol, tf, num_candles)
            if df is not None:
                data[tf] = df
        return data


# Test function
def test_tradingview_data():
    """Test TradingView data fetching for USD currency pairs."""
    print("=" * 60)
    print("Testing TradingView Data Fetcher for USD Currency Pairs")
    print("=" * 60)
    
    fetcher = TradingViewDataFetcher()
    
    if not fetcher.connect():
        print("❌ Failed to connect to TradingView")
        return
    
    # Test EURUSD
    print("\n=== Testing EURUSD ===")
    analysis = fetcher.fetch_technical_analysis('EURUSD', 60)
    if analysis:
        print(f"Recommendation: {analysis['summary'].get('RECOMMENDATION', 'N/A')}")
        print(f"Buy signals: {analysis['summary'].get('BUY', 0)}")
        print(f"Sell signals: {analysis['summary'].get('SELL', 0)}")
        print(f"Neutral signals: {analysis['summary'].get('NEUTRAL', 0)}")
        print(f"Current Price: {analysis['indicators'].get('close', 'N/A')}")
        print(f"RSI: {analysis['indicators'].get('RSI', 'N/A')}")
    
    # Test GBPUSD
    print("\n=== Testing GBPUSD ===")
    analysis = fetcher.fetch_technical_analysis('GBPUSD', 60)
    if analysis:
        print(f"Recommendation: {analysis['summary'].get('RECOMMENDATION', 'N/A')}")
        print(f"Current Price: {analysis['indicators'].get('close', 'N/A')}")
    
    # Test USDJPY
    print("\n=== Testing USDJPY ===")
    analysis = fetcher.fetch_technical_analysis('USDJPY', 60)
    if analysis:
        print(f"Recommendation: {analysis['summary'].get('RECOMMENDATION', 'N/A')}")
        print(f"Current Price: {analysis['indicators'].get('close', 'N/A')}")
    
    # Test BTCUSD (Crypto)
    print("\n=== Testing BTCUSD (Crypto) ===")
    analysis = fetcher.fetch_technical_analysis('BTCUSD', 60)
    if analysis:
        print(f"Recommendation: {analysis['summary'].get('RECOMMENDATION', 'N/A')}")
        print(f"Current Price: {analysis['indicators'].get('close', 'N/A')}")
    
    # Test multi-timeframe
    print("\n=== Testing Multi-Timeframe Analysis for EURUSD ===")
    multi_tf = fetcher.fetch_multi_timeframe_analysis('EURUSD', [5, 60, 240])
    for tf, data in multi_tf.items():
        print(f"{tf}min: {data['summary'].get('RECOMMENDATION', 'N/A')} - Price: {data['indicators'].get('close', 'N/A')}")
    
    # Test current price
    print("\n=== Testing Current Price Fetch ===")
    price = fetcher.get_current_price('EURUSD')
    if price:
        print(f"EURUSD - Bid: {price['bid']:.5f}, Ask: {price['ask']:.5f}, Last: {price['last']:.5f}")
    
    print("\n" + "=" * 60)
    print("✅ TradingView Data Fetcher Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_tradingview_data()
