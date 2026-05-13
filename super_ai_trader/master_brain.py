"""
Super AI Trader - Master Brain Module
Core orchestrator that aggregates agent votes, applies risk management,
and dispatches signals to Telegram.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

from config import (
    MIN_AGREEING_AGENTS, CONFIDENCE_THRESHOLD, AGENT5_BLOCK_ENABLED,
    SYMBOLS, RISK_PER_TRADE, ACCOUNT_BALANCE
)
from agents.base_agent import SignalResult
from agents.agent1_trend_structure import TrendStructureAgent
from agents.agent2_volume_orderflow import VolumeOrderFlowAgent
from agents.agent3_price_action_sd import PriceActionSDAgent
from agents.agent4_indicator_confluence import IndicatorConfluenceAgent
from agents.agent5_market_context import MarketContextAgent
from data.market_data import MarketDataFetcher, MultiTimeframeDataBuilder
from utils.risk_manager import RiskManager
from utils.formatter import SignalFormatter


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MasterBrain:
    """
    Master Brain - Core orchestrator for the Super AI Trader system.
    
    Responsibilities:
    - Orchestrate trading session loop for each symbol
    - Collect and validate agent outputs
    - Enforce voting thresholds
    - Apply Agent 5 veto
    - Calculate position sizing
    - Format and dispatch Telegram signals
    - Maintain system state
    """
    
    def __init__(self, data_source: str = 'auto'):
        # Initialize all 5 agents
        self.agents = {
            'agent1': TrendStructureAgent(),
            'agent2': VolumeOrderFlowAgent(),
            'agent3': PriceActionSDAgent(),
            'agent4': IndicatorConfluenceAgent(),
            'agent5': MarketContextAgent()
        }
        
        # Initialize components with data source configuration
        self.data_fetcher = MarketDataFetcher(data_source=data_source)
        self.data_builder = MultiTimeframeDataBuilder(self.data_fetcher)
        self.risk_manager = RiskManager(
            account_balance=ACCOUNT_BALANCE,
            risk_per_trade=RISK_PER_TRADE
        )
        self.formatter = SignalFormatter()
        
        # System state
        self.trading_enabled = False
        self.active_positions = {}
        self.daily_pnl = 0.0
        self.signals_sent = []
        
        # Voting configuration
        self.min_agreeing_agents = MIN_AGREEING_AGENTS
        self.confidence_threshold = CONFIDENCE_THRESHOLD
        self.agent5_block_enabled = AGENT5_BLOCK_ENABLED
    
    def start_trading(self):
        """Enable trading."""
        self.trading_enabled = True
        logger.info("Trading enabled by Master Brain")
    
    def stop_trading(self):
        """Disable trading."""
        self.trading_enabled = False
        logger.info("Trading disabled by Master Brain")
    
    async def analyze_symbol(self, symbol: str) -> Optional[dict]:
        """
        Analyze a single symbol through all agents and aggregate results.
        
        Args:
            symbol: Trading symbol to analyze
        
        Returns:
            Dictionary with signal details or None if no signal
        """
        if not self.trading_enabled:
            logger.debug(f"Trading disabled, skipping {symbol}")
            return None
        
        try:
            # Fetch multi-timeframe data
            data = self.data_builder.build_aligned_data(symbol, reference_tf=1)
            
            if not data:
                logger.warning(f"No data available for {symbol}")
                return None
            
            # Get current price
            current_price = self.data_fetcher.get_current_price(symbol)
            
            if not current_price:
                logger.warning(f"Cannot get current price for {symbol}")
                return None
            
            # Collect signals from all agents
            agent_signals = {}
            for agent_id, agent in self.agents.items():
                if agent.enabled:
                    signal = agent.analyze(data, current_price)
                    agent_signals[agent_id] = signal
                    logger.debug(f"{agent.name}: {signal.signal} (confidence: {signal.confidence}%)")
            
            # Check Agent 5 veto first
            agent5_signal = agent_signals.get('agent5')
            if agent5_signal and agent5_signal.signal == 'NO_TRADE':
                logger.info(f"Agent 5 veto for {symbol}: {' | '.join(agent5_signal.reasons[:2])}")
                return None
            
            # Aggregate votes from agents 1-4
            buy_votes = 0
            sell_votes = 0
            total_confidence = 0
            vote_count = 0
            all_reasons = []
            
            for agent_id in ['agent1', 'agent2', 'agent3', 'agent4']:
                signal = agent_signals.get(agent_id)
                if signal:
                    vote_count += 1
                    if signal.signal == 'BUY':
                        buy_votes += 1
                        total_confidence += signal.confidence
                        all_reasons.extend(signal.reasons[:2])
                    elif signal.signal == 'SELL':
                        sell_votes += 1
                        total_confidence += signal.confidence
                        all_reasons.extend(signal.reasons[:2])
            
            # Check if minimum agreeing agents threshold is met
            max_votes = max(buy_votes, sell_votes)
            
            if max_votes < self.min_agreeing_agents:
                logger.debug(f"{symbol}: Only {max_votes}/{self.min_agreeing_agents} agents agree")
                return None
            
            # Determine direction
            direction = 'BUY' if buy_votes > sell_votes else 'SELL'
            
            # Calculate average confidence
            avg_confidence = total_confidence / vote_count if vote_count > 0 else 0
            
            if avg_confidence < self.confidence_threshold:
                logger.debug(f"{symbol}: Confidence {avg_confidence:.1f}% below threshold {self.confidence_threshold}%")
                return None
            
            # Calculate trade parameters
            entry_price = current_price['ask'] if direction == 'BUY' else current_price['bid']
            
            # Get ATR for SL/TP calculation
            df_1m = data.get(1)
            atr = self._calculate_atr(df_1m)
            
            stop_loss = self.risk_manager.calculate_stop_loss(entry_price, atr, direction)
            take_profit = self.risk_manager.calculate_take_profit(entry_price, atr, direction)
            lots = self.risk_manager.calculate_position_size(entry_price, stop_loss)
            
            # Build signal result
            signal_result = {
                'symbol': symbol,
                'direction': direction,
                'entry': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'lots': lots,
                'confidence': int(avg_confidence),
                'reasons': all_reasons,
                'timestamp': datetime.now(),
                'buy_votes': buy_votes,
                'sell_votes': sell_votes,
                'atr': atr
            }
            
            logger.info(f"Signal generated for {symbol}: {direction} @ {entry_price:.5f}")
            return signal_result
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate ATR from dataframe."""
        if df is None or len(df) < period:
            return 0.001  # Default small value
        
        from indicators.indicator_library import IndicatorLibrary
        il = IndicatorLibrary()
        atr_series = il.atr(df['high'], df['low'], df['close'], period)
        return atr_series.iloc[-1]
    
    async def run_analysis_cycle(self) -> List[dict]:
        """
        Run analysis cycle for all configured symbols.
        
        Returns:
            List of signal dictionaries
        """
        signals = []
        
        for symbol in SYMBOLS:
            signal = await self.analyze_symbol(symbol)
            if signal:
                signals.append(signal)
                self.signals_sent.append(signal)
        
        return signals
    
    def format_and_send_signal(self, signal: dict, telegram_bot=None) -> str:
        """
        Format signal for Telegram and optionally send it.
        
        Args:
            signal: Signal dictionary
            telegram_bot: Optional Telegram bot instance
        
        Returns:
            Formatted message string
        """
        message = self.formatter.format_signal(
            symbol=signal['symbol'],
            direction=signal['direction'],
            entry=signal['entry'],
            stop_loss=signal['stop_loss'],
            take_profit=signal['take_profit'],
            lots=signal['lots'],
            confidence=signal['confidence'],
            reasons=signal['reasons'],
            timestamp=signal['timestamp']
        )
        
        logger.info(f"Signal formatted: {signal['symbol']} {signal['direction']}")
        
        # In production, would send via telegram_bot
        # if telegram_bot:
        #     await telegram_bot.send_message(message)
        
        return message
    
    def get_system_status(self) -> dict:
        """Get comprehensive system status."""
        agent_status = []
        for agent_id, agent in self.agents.items():
            info = agent.get_info()
            agent_status.append(info)
        
        risk_summary = self.risk_manager.get_risk_summary()
        
        return {
            'trading_enabled': self.trading_enabled,
            'balance': self.risk_manager.account_balance,
            'daily_pnl': self.risk_manager.daily_pnl,
            'daily_pnl_pct': (self.risk_manager.daily_pnl / self.risk_manager.account_balance) * 100,
            'trades_today': self.risk_manager.trades_today,
            'agents': agent_status,
            'symbols': SYMBOLS,
            'last_update': datetime.now().isoformat(),
            'risk_summary': risk_summary,
            'signals_today': len([s for s in self.signals_sent 
                                 if s['timestamp'].date() == datetime.now().date()])
        }
    
    async def execute_trading_loop(self, interval_seconds: int = 60):
        """
        Main trading loop that runs continuously.
        
        Args:
            interval_seconds: Time between analysis cycles
        """
        logger.info(f"Starting trading loop with {interval_seconds}s interval")
        
        while self.trading_enabled:
            try:
                # Run analysis for all symbols
                signals = await self.run_analysis_cycle()
                
                # Process any signals generated
                for signal in signals:
                    formatted_message = self.format_and_send_signal(signal)
                    logger.info(f"Signal sent: {formatted_message[:100]}...")
                    
                    # Update risk manager
                    self.risk_manager.increment_trade_count()
                
                # Wait for next cycle
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(interval_seconds)
        
        logger.info("Trading loop stopped")
