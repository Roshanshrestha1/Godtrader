"""
Super AI Trader - Main Entry Point
Runs the async trading loop and initializes all components including Telegram bot.
"""

import asyncio
import logging
import signal
from datetime import datetime

from config import LOG_LEVEL, LOG_FILE, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from master_brain import MasterBrain
from telegram_bot import TelegramBot


# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SuperAITrader:
    """
    Main application class for Super AI Trader.
    Handles initialization, shutdown, and main loop.
    """
    
    def __init__(self):
        from config import DATA_SOURCE
        self.master_brain = MasterBrain(data_source=DATA_SOURCE)
        self.telegram_bot = None
        self.running = False
        self._shutdown_event = asyncio.Event()
        
        # Initialize Telegram bot if token is configured
        if TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
            self.telegram_bot = TelegramBot(
                token=TELEGRAM_BOT_TOKEN,
                chat_id=TELEGRAM_CHAT_ID
            )
            self.telegram_bot.set_master_brain(self.master_brain)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.running = False
        self._shutdown_event.set()
    
    async def run(self):
        """Main application entry point."""
        logger.info("=" * 60)
        logger.info("🚀 Super AI Trader v2.0 Starting...")
        logger.info("=" * 60)
        
        # Initialize system
        try:
            # Connect to data source (Binance/YahooFinance)
            connected = self.master_brain.data_fetcher.connect()
            if connected:
                logger.info(f"✅ Connected to {self.master_brain.data_fetcher.data_source.upper()} - Real Trading Data")
            else:
                logger.error("❌ Failed to connect to data source")
                return
            
            # Start Telegram bot if configured
            if self.telegram_bot:
                await self.telegram_bot.start()
                logger.info("✅ Telegram Bot started - Use /menu for interactive commands")
            
            # Display system configuration
            self._display_config()
            
            # Start trading
            self.master_brain.start_trading()
            self.running = True
            
            logger.info("\n" + "=" * 60)
            logger.info("✅ System Ready - Trading Enabled")
            logger.info("=" * 60 + "\n")
            
            # Run main trading loop
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            raise
        
        finally:
            await self.shutdown()
    
    def _display_config(self):
        """Display system configuration."""
        logger.info("\n📋 System Configuration:")
        logger.info(f"  • Symbols: {', '.join(self.master_brain.data_fetcher.fetcher.SYMBOLS if hasattr(self.master_brain.data_fetcher, 'fetcher') else ['EURUSD', 'GBPUSD', 'USDJPY'])}")
        logger.info(f"  • Risk per Trade: {self.master_brain.risk_manager.risk_per_trade * 100}%")
        logger.info(f"  • Min Agreeing Agents: {self.master_brain.min_agreeing_agents}/4")
        logger.info(f"  • Confidence Threshold: {self.master_brain.confidence_threshold}%")
        logger.info(f"  • Agent 5 Block: {'Enabled' if self.master_brain.agent5_block_enabled else 'Disabled'}")
        
        logger.info("\n🤖 Active Agents:")
        for agent_id, agent in self.master_brain.agents.items():
            info = agent.get_info()
            logger.info(f"  • {info['name']} (Modules: {info['modules']})")
    
    async def _main_loop(self):
        """Main analysis and trading loop."""
        cycle_count = 0
        analysis_interval = 60  # seconds between analysis cycles
        status_interval = 300  # seconds between status updates
        
        while self.running:
            try:
                cycle_count += 1
                
                # Run analysis cycle
                logger.debug(f"\n--- Analysis Cycle {cycle_count} ---")
                signals = await self.master_brain.run_analysis_cycle()
                
                if signals:
                    logger.info(f"Generated {len(signals)} signal(s) this cycle")
                    for sig in signals:
                        # Format and log signal
                        message = self.master_brain.format_and_send_signal(sig)
                        logger.info(f"SIGNAL: {sig['symbol']} {sig['direction']} @ {sig['entry']:.5f}")
                        
                        # Send signal via Telegram bot
                        if self.telegram_bot:
                            await self.telegram_bot.send_signal(sig)
                else:
                    logger.debug("No signals generated this cycle")
                
                # Periodic status update
                if cycle_count % (status_interval // analysis_interval) == 0:
                    status = self.master_brain.get_system_status()
                    logger.info(f"\n📊 Status Update:")
                    logger.info(f"  • Signals Today: {status['signals_today']}")
                    logger.info(f"  • Daily PnL: ${status['daily_pnl']:.2f} ({status['daily_pnl_pct']:.2f}%)")
                    logger.info(f"  • Trades Today: {status['trades_today']}")
                
                # Wait for next cycle or shutdown
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=analysis_interval
                    )
                    break  # Shutdown event was set
                except asyncio.TimeoutError:
                    pass  # Continue to next cycle
                    
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(analysis_interval)
    
    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("\n" + "=" * 60)
        logger.info("🛑 Shutting down Super AI Trader...")
        logger.info("=" * 60)
        
        # Stop trading
        self.master_brain.stop_trading()
        
        # Stop Telegram bot
        if self.telegram_bot:
            await self.telegram_bot.stop()
            logger.info("Telegram Bot stopped")
        
        # Disconnect from MT5
        self.master_brain.data_fetcher.disconnect()
        logger.info("Disconnected from MetaTrader 5")
        
        # Log final summary
        status = self.master_brain.get_system_status()
        logger.info(f"\n📊 Final Summary:")
        logger.info(f"  • Total Signals Sent: {len(self.master_brain.signals_sent)}")
        logger.info(f"  • Daily PnL: ${status['daily_pnl']:.2f}")
        logger.info(f"  • Trades Executed: {status['trades_today']}")
        
        logger.info("\n✅ Shutdown complete")


async def main():
    """Async main function."""
    trader = SuperAITrader()
    await trader.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
