#!/usr/bin/env python3
"""
Background Market Scanner Service
Scans all Exness assets periodically and caches the best trades.
This runs independently from the Telegram bot to ensure fast responses.
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import project modules
import sys
sys.path.insert(0, '/workspace')

from config import config as global_config
from master_brain import MasterBrain

# Note: format_signal_card is not used, removed from import


def get_all_symbols():
    """Get all Exness symbols from config."""
    return global_config.get_all_symbols()


def get_symbol_mapping(symbol: str) -> str:
    """Get Yahoo Finance ticker for an Exness symbol."""
    return global_config.get_yahoo_ticker(symbol)

# Configuration
SCAN_INTERVAL_MINUTES = 5  # How often to scan all markets
CACHE_FILE = Path("/workspace/cache/best_trades.json")
LOG_FILE = Path("/workspace/logs/scanner.log")

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


class MarketScanner:
    """Background service that continuously scans all markets."""
    
    def __init__(self):
        self.config = ConfigLoader()
        self.brain = MasterBrain()
        self.is_running = False
        self.last_scan_time: Optional[datetime] = None
        self.cached_results: Dict[str, Any] = {
            "timestamp": None,
            "top_trades": [],
            "scan_status": "pending",
            "total_symbols_scanned": 0
        }
        
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
    
    async def scan_all_markets(self) -> Dict[str, Any]:
        """Scan all available Exness assets and find best trades."""
        start_time = time.time()
        logger.info("🔍 Starting full market scan...")
        
        symbols = get_all_symbols()
        total_symbols = len(symbols)
        logger.info(f"📊 Scanning {total_symbols} symbols across all asset classes")
        
        all_signals = []
        scanned_count = 0
        
        for symbol in symbols:
            try:
                # Get Yahoo Finance ticker mapping
                yahoo_ticker = get_symbol_mapping(symbol)
                
                # Analyze symbol with master brain
                signal = await self.brain.analyze_single(yahoo_ticker, "1h")
                
                if signal and signal.get('signal') in ['BUY', 'SELL']:
                    # Add symbol info
                    signal['exness_symbol'] = symbol
                    signal['yahoo_ticker'] = yahoo_ticker
                    
                    # Calculate score for ranking
                    confidence = signal.get('confidence', 0)
                    agents_agree = signal.get('agents_agreeing', 0)
                    score = confidence * (agents_agree / 5.0)
                    signal['score'] = score
                    
                    all_signals.append(signal)
                
                scanned_count += 1
                if scanned_count % 10 == 0:
                    logger.info(f"⏳ Progress: {scanned_count}/{total_symbols} symbols scanned")
                    
            except Exception as e:
                logger.warning(f"⚠️  Failed to analyze {symbol}: {e}")
                scanned_count += 1
                continue
            
            # Rate limiting: small delay between symbols to avoid API bans
            await asyncio.sleep(0.5)
        
        # Sort by score (highest first)
        all_signals.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Take top 10 (cache more than we show)
        top_trades = all_signals[:10]
        
        scan_duration = time.time() - start_time
        logger.info(f"✅ Scan complete in {scan_duration:.2f}s | Found {len(top_trades)} high-confidence trades")
        
        # Prepare cache data
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "top_trades": top_trades,
            "scan_status": "complete",
            "total_symbols_scanned": scanned_count,
            "scan_duration_seconds": round(scan_duration, 2),
            "next_scan_in_minutes": SCAN_INTERVAL_MINUTES
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
