#!/usr/bin/env python3
"""
Background Market Scanner Service
Scans all Exness assets periodically and caches the best trades.
This runs independently from the Telegram bot to ensure fast responses.

ENHANCED FEATURES:
- Parallel scanning for speed
- Multi-timeframe confirmation
- Advanced scoring algorithm
- Best-of-best categorization
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import aiohttp

# Import project modules
import sys
sys.path.insert(0, '/workspace')

from config import config as global_config
from master_brain import MasterBrain

# Configuration
SCAN_INTERVAL_MINUTES = 5  # How often to scan all markets
CACHE_FILE = Path("/workspace/cache/best_trades.json")
LOG_FILE = Path("/workspace/logs/scanner.log")
MAX_CONCURRENT_SCANS = 10  # Number of parallel scans to run

# Setup Logging
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MarketScanner")


def get_all_symbols():
    """Get all Exness symbols from config."""
    return global_config.get_all_symbols()


def get_symbol_mapping(symbol: str) -> str:
    """Get Yahoo Finance ticker for an Exness symbol."""
    return global_config.get_yahoo_ticker(symbol)


def get_symbol_group(symbol: str) -> str:
    """Get the group/category for a symbol."""
    symbol_groups = global_config.get_symbol_groups()
    return symbol_groups.get(symbol, "Unknown")


class MarketScanner:
    """Background service that continuously scans all markets."""
    
    def __init__(self):
        self.brain = MasterBrain()
        self.is_running = False
        self.last_scan_time: Optional[datetime] = None
        self.cached_results: Dict[str, Any] = {
            "timestamp": None,
            "top_trades": [],
            "scan_status": "pending",
            "total_symbols_scanned": 0,
            "best_buy": None,
            "best_sell": None,
            "highest_confidence": None
        }
        
    def calculate_advanced_score(self, signal: Dict[str, Any]) -> float:
        """
        Calculate advanced score for ranking trades.
        
        Scoring factors:
        - Base: confidence * agents_agreeing
        - Bonus: Tier 1 signals (+20%), strong trend (+10%)
        - Penalty: High risk score (-20% if >70)
        """
        confidence = signal.get('confidence', 0)
        agents_agree = signal.get('agents_agreeing', 0)
        tier_level = signal.get('tier_level', '')
        risk_score = signal.get('risk_score', 50)
        
        # Base score
        base_score = confidence * (agents_agree / 4.0)
        
        # Tier bonus
        tier_multiplier = 1.0
        if tier_level == "TIER_1_STRONG":
            tier_multiplier = 1.2  # +20% bonus
        elif tier_level == "TIER_2_MODERATE":
            tier_multiplier = 1.0
        
        # Risk penalty
        risk_penalty = 1.0
        if risk_score > 70:
            risk_penalty = 0.8  # -20% penalty
        elif risk_score > 50:
            risk_penalty = 0.9  # -10% penalty
        
        final_score = base_score * tier_multiplier * risk_penalty
        return round(final_score, 2)
    
    def save_cache(self, data: Dict[str, Any]):
        """Save scan results to cache file."""
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"✅ Cache saved: {len(data.get('top_trades', []))} trades found")
        except Exception as e:
            logger.error(f"❌ Failed to save cache: {e}")
    
    def load_cache(self) -> Dict[str, Any]:
        """Load cached results."""
        try:
            if CACHE_FILE.exists():
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"❌ Failed to load cache: {e}")
        return self.cached_results
    
    async def analyze_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Analyze a single symbol with multi-timeframe confirmation."""
        try:
            # Get Yahoo Finance ticker mapping
            yahoo_ticker = get_symbol_mapping(symbol)
            symbol_group = get_symbol_group(symbol)
            
            # Primary analysis on main timeframe (1h)
            signal = await asyncio.to_thread(
                lambda: self.brain.analyze_single(yahoo_ticker, "1h")
            )
            
            if not signal or signal.get('decision') not in ['BUY', 'SELL']:
                return None
            
            # Multi-timeframe confirmation: check 15m for entry timing
            if signal['decision'] in ['BUY', 'SELL']:
                try:
                    short_tf_signal = await asyncio.to_thread(
                        lambda: self.brain.analyze_single(yahoo_ticker, "15m")
                    )
                    
                    # If short-term agrees, boost confidence
                    if short_tf_signal and short_tf_signal.get('decision') == signal['decision']:
                        signal['multi_tf_confirmed'] = True
                        signal['confidence'] = min(100, signal['confidence'] + 5)
                        signal['reasons'].append("✅ Multi-timeframe confirmation (1H + 15M)")
                    else:
                        signal['multi_tf_confirmed'] = False
                except Exception as e:
                    logger.debug(f"Could not get short TF confirmation for {symbol}: {e}")
                    signal['multi_tf_confirmed'] = False
            
            # Add symbol metadata
            signal['exness_symbol'] = symbol
            signal['yahoo_ticker'] = yahoo_ticker
            signal['symbol_group'] = symbol_group
            
            # Calculate advanced score
            signal['score'] = self.calculate_advanced_score(signal)
            
            return signal
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to analyze {symbol}: {e}")
            return None
    
    async def scan_all_markets(self) -> Dict[str, Any]:
        """
        Scan all available Exness assets using parallel processing.
        Finds the absolute best trades across all markets.
        """
        start_time = time.time()
        logger.info("🔍 Starting COMPREHENSIVE market scan...")
        
        symbols = get_all_symbols()
        total_symbols = len(symbols)
        logger.info(f"📊 Scanning {total_symbols} symbols across all asset classes")
        logger.info(f"🚀 Using parallel processing (max {MAX_CONCURRENT_SCANS} concurrent)")
        
        all_signals = []
        scanned_count = 0
        failed_count = 0
        
        # Process symbols in batches for parallel execution
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_SCANS)
        
        async def bounded_analyze(symbol):
            async with semaphore:
                result = await self.analyze_symbol(symbol)
                return symbol, result
        
        # Create tasks for all symbols
        tasks = [bounded_analyze(symbol) for symbol in symbols]
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            symbol = symbols[i]
            
            if isinstance(result, Exception):
                logger.warning(f"⚠️ Error analyzing {symbol}: {result}")
                failed_count += 1
                scanned_count += 1
                continue
            
            sym, signal = result
            scanned_count += 1
            
            if signal:
                all_signals.append(signal)
            
            # Progress logging
            if scanned_count % 20 == 0:
                logger.info(f"⏳ Progress: {scanned_count}/{total_symbols} | Found {len(all_signals)} signals so far")
        
        # Categorize signals
        buy_signals = [s for s in all_signals if s.get('decision') == 'BUY']
        sell_signals = [s for s in all_signals if s.get('decision') == 'SELL']
        
        # Sort by score
        buy_signals.sort(key=lambda x: x.get('score', 0), reverse=True)
        sell_signals.sort(key=lambda x: x.get('score', 0), reverse=True)
        all_signals.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Find best of each category
        best_buy = buy_signals[0] if buy_signals else None
        best_sell = sell_signals[0] if sell_signals else None
        highest_confidence = max(all_signals, key=lambda x: x.get('confidence', 0)) if all_signals else None
        
        # Take top 15 overall (show more options)
        top_trades = all_signals[:15]
        
        scan_duration = time.time() - start_time
        success_rate = ((scanned_count - failed_count) / scanned_count * 100) if scanned_count > 0 else 0
        
        logger.info("=" * 60)
        logger.info(f"✅ SCAN COMPLETE in {scan_duration:.2f}s")
        logger.info(f"📈 BUY signals: {len(buy_signals)} | 📉 SELL signals: {len(sell_signals)}")
        logger.info(f"🎯 Success rate: {success_rate:.1f}% ({scanned_count - failed_count}/{scanned_count})")
        
        if best_buy:
            logger.info(f"🟢 BEST BUY: {best_buy['exness_symbol']} (Score: {best_buy['score']}, Conf: {best_buy['confidence']}%)")
        if best_sell:
            logger.info(f"🔴 BEST SELL: {best_sell['exness_symbol']} (Score: {best_sell['score']}, Conf: {best_sell['confidence']}%)")
        logger.info("=" * 60)
        
        # Prepare comprehensive cache data
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "top_trades": top_trades,
            "all_buy_signals": buy_signals[:20],  # Top 20 buys
            "all_sell_signals": sell_signals[:20],  # Top 20 sells
            "best_buy": best_buy,
            "best_sell": best_sell,
            "highest_confidence": highest_confidence,
            "scan_status": "complete",
            "total_symbols_scanned": scanned_count,
            "failed_scans": failed_count,
            "success_rate_pct": round(success_rate, 1),
            "scan_duration_seconds": round(scan_duration, 2),
            "next_scan_in_minutes": SCAN_INTERVAL_MINUTES,
            "summary": {
                "total_signals": len(all_signals),
                "buy_count": len(buy_signals),
                "sell_count": len(sell_signals),
                "avg_confidence": round(sum(s.get('confidence', 0) for s in all_signals) / len(all_signals), 1) if all_signals else 0
            }
        }
        
        # Save to cache
        self.save_cache(cache_data)
        self.cached_results = cache_data
        self.last_scan_time = datetime.now()
        
        return cache_data
    
    async def run_continuous_scan(self):
        """Run continuous scanning loop."""
        self.is_running = True
        logger.info(f"🚀 Market Scanner started | Scan interval: {SCAN_INTERVAL_MINUTES} minutes")
        
        # Initial scan
        await self.scan_all_markets()
        
        # Continuous loop
        while self.is_running:
            await asyncio.sleep(SCAN_INTERVAL_MINUTES * 60)
            await self.scan_all_markets()
    
    def stop(self):
        """Stop the scanner."""
        self.is_running = False
        logger.info("🛑 Market Scanner stopped")


async def main():
    """Main entry point."""
    scanner = MarketScanner()
    
    try:
        await scanner.run_continuous_scan()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        scanner.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
