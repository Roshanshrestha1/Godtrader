"""
Master Brain - Orchestrates all 5 AI agents and makes final trading decisions.
Aggregates signals, calculates confidence, and applies veto logic.
"""

import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from config import config

from agents.trend_agent import TrendAgent
from agents.volume_agent import VolumeAgent
from agents.price_action_agent import PriceActionAgent
from agents.indicator_agent import IndicatorAgent
from agents.context_agent import ContextAgent

from utils.data_fetcher import fetch_ohlcv, validate_symbol, sanitize_timeframe
from utils.indicators import atr

logger = logging.getLogger(__name__)


class MasterBrain:
    """
    Master Brain - Central orchestrator for all AI agents.
    
    Responsibilities:
    - Fetch and validate market data
    - Run all 5 agents on the data
    - Aggregate signals using voting mechanism
    - Apply thresholds and veto logic
    - Calculate entry, stop-loss, and take-profit levels
    - Return final decision with full reasoning
    """
    
    def __init__(self):
        # Initialize all agents with config parameters
        self.trend_agent = TrendAgent(
            ema_period=config.get_ema_period(),
            adx_threshold=config.get_adx_threshold()
        )
        
        self.volume_agent = VolumeAgent(
            volume_sma_period=config.get_volume_sma_period()
        )
        
        self.price_action_agent = PriceActionAgent(
            sweep_lookback_hours=config.get_sweep_lookback_hours()
        )
        
        self.indicator_agent = IndicatorAgent()
        
        self.context_agent = ContextAgent()
        
        # Thresholds from config
        self.min_agents_agree = config.get_min_agents_agree()
        self.min_confidence = config.get_min_confidence()
        self.agent5_veto_enabled = config.is_agent5_veto_enabled()
    
    def analyze_single(
        self,
        symbol: str,
        timeframe: str = None,
        override_tf: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze a single symbol with specified timeframe.
        
        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'EURUSD=X')
            timeframe: Timeframe for analysis (uses config default if None)
            override_tf: If True, use provided timeframe; otherwise use multi-TF analysis
        
        Returns:
            Dictionary with complete analysis results
        """
        timestamp = datetime.now()
        
        # Validate inputs
        if not validate_symbol(symbol):
            logger.error(f"Invalid symbol: {symbol}")
            return self._create_error_result(symbol, "Invalid symbol format")
        
        try:
            tf = sanitize_timeframe(timeframe) if timeframe else config.get_main_timeframe()
        except ValueError as e:
            logger.error(f"Invalid timeframe: {timeframe}")
            return self._create_error_result(symbol, str(e))
        
        logger.info(f"Analyzing {symbol} on {tf} timeframe")
        
        try:
            # Fetch data for main timeframe
            df_main = fetch_ohlcv(symbol, interval=tf, period='7d')
            
            if len(df_main) < 10:
                return self._create_error_result(symbol, "Insufficient data received")
            
            # Fetch higher timeframe for context (if applicable)
            df_higher = None
            if tf in ['1m', '5m', '15m', '30m']:
                higher_tf = '1h'
            elif tf == '1h':
                higher_tf = '4h'
            elif tf == '4h':
                higher_tf = '1d'
            else:
                higher_tf = None
            
            if higher_tf:
                try:
                    df_higher = fetch_ohlcv(symbol, interval=higher_tf, period='1mo')
                except Exception as e:
                    logger.warning(f"Could not fetch higher TF data: {e}")
            
            # Run all agents
            agent_results = self._run_agents(df_main, df_higher)
            
            # Aggregate results
            final_decision = self._aggregate_signals(agent_results, df_main, symbol)
            
            # Build complete result
            result = {
                'symbol': symbol,
                'timeframe': tf,
                'timestamp': timestamp,
                'agents': agent_results,
                'decision': final_decision['signal'],
                'avg_confidence': final_decision['confidence'],
                'entry': final_decision.get('entry', 0),
                'stop_loss': final_decision.get('stop_loss', 0),
                'take_profit': final_decision.get('take_profit', 0),
                'reasons': final_decision['reasons'],
                'veto_applied': final_decision.get('veto_applied', False),
                'agents_agreeing': final_decision.get('agents_agreeing', 0)
            }
            
            logger.info(f"Analysis complete for {symbol}: {result['decision']} ({result['avg_confidence']}%)")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed for {symbol}: {e}", exc_info=True)
            return self._create_error_result(symbol, str(e))
    
    def analyze_all_symbols(self) -> List[Dict[str, Any]]:
        """
        Analyze all configured symbols and return sorted list of trade opportunities.
        
        Returns:
            List of trade signals sorted by (confidence * agreeing_agents), filtered by thresholds
        """
        all_symbols = config.get_all_symbols()
        results = []
        
        logger.info(f"Starting batch analysis of {len(all_symbols)} symbols")
        
        for symbol in all_symbols:
            try:
                result = self.analyze_single(symbol, config.get_main_timeframe())
                
                # Only include valid BUY/SELL signals
                if result['decision'] in ['BUY', 'SELL']:
                    # Calculate score for sorting
                    score = result['avg_confidence'] * result.get('agents_agreeing', 0)
                    result['_score'] = score
                    results.append(result)
                    
            except Exception as e:
                logger.error(f"Failed to analyze {symbol}: {e}")
                continue
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x['_score'], reverse=True)
        
        # Remove internal score field
        for result in results:
            del result['_score']
        
        logger.info(f"Found {len(results)} valid signals from {len(all_symbols)} symbols")
        return results
    
    def _run_agents(
        self,
        df_main: pd.DataFrame,
        df_higher: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Run all 5 agents on the provided data.
        
        Args:
            df_main: Main timeframe data
            df_higher: Higher timeframe data (optional)
        
        Returns:
            Dictionary with all agent results
        """
        results = {}
        
        # Agent 1: Trend (use higher TF if available for better trend context)
        trend_df = df_higher if df_higher is not None else df_main
        results['agent1'] = self.trend_agent.analyze(trend_df.copy())
        
        # Agent 2: Volume
        results['agent2'] = self.volume_agent.analyze(df_main.copy())
        
        # Agent 3: Price Action
        results['agent3'] = self.price_action_agent.analyze(df_main.copy())
        
        # Agent 4: Indicators
        results['agent4'] = self.indicator_agent.analyze(df_main.copy())
        
        # Agent 5: Context (needs proposed signal from other agents)
        # First, get preliminary signal from agents 1-4
        preliminary_signal = self._get_preliminary_signal(results)
        current_price = df_main['Close'].iloc[-1]
        
        results['agent5'] = self.context_agent.analyze(
            df_main.copy(),
            preliminary_signal,
            current_price
        )
        
        return results
    
    def _get_preliminary_signal(self, agent_results: Dict[str, Any]) -> str:
        """Get preliminary signal from agents 1-4 (before agent 5)."""
        signals = []
        
        for i in range(1, 5):
            key = f'agent{i}'
            if key in agent_results:
                signals.append(agent_results[key]['signal'])
        
        buy_count = sum(1 for s in signals if s == 'BUY')
        sell_count = sum(1 for s in signals if s == 'SELL')
        
        if buy_count > sell_count:
            return 'BUY'
        elif sell_count > buy_count:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _aggregate_signals(
        self,
        agent_results: Dict[str, Any],
        df: pd.DataFrame,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Aggregate signals from all agents and make final decision.
        
        Implements Tiered Consensus (Fix #2):
        - Tier 1 (Strong): 4/5 Agents Agree (Confidence > 75%)
        - Tier 2 (Moderate): 3/5 Agents Agree (Confidence > 60%)
        
        Args:
            agent_results: Results from all 5 agents
            df: Price data DataFrame
            symbol: Trading symbol
        
        Returns:
            Final decision dictionary
        """
        reasons = []
        
        # Debug: Print all agent signals (Diagnostic Tool)
        logger.info("--- SIGNAL DEBUGGER ---")
        for agent, vote in agent_results.items():
            logger.info(f"{agent}: {vote.get('signal', 'N/A')} ({vote.get('confidence', 0)}%)")
        
        # Count votes
        buy_votes = 0
        sell_votes = 0
        hold_votes = 0
        confidences = []
        
        for i in range(1, 5):  # Agents 1-4 vote on direction
            key = f'agent{i}'
            result = agent_results.get(key, {})
            signal = result.get('signal', 'HOLD')
            confidence = result.get('confidence', 0)
            
            if signal == 'BUY':
                buy_votes += 1
                confidences.append(confidence)
            elif signal == 'SELL':
                sell_votes += 1
                confidences.append(confidence)
            else:
                hold_votes += 1
        
        # Agent 5 (Context) - Now provides Risk Score instead of hard veto (Fix #4)
        agent5_result = agent_results.get('agent5', {})
        agent5_veto = agent5_result.get('veto', False)
        agent5_status = agent5_result.get('status', 'APPROVE')
        agent5_risk_score = agent5_result.get('risk_score', 50)  # New: 0-100 risk score
        
        # Determine preliminary signal with Tiered Consensus
        max_votes = max(buy_votes, sell_votes)
        dominant_signal = 'BUY' if buy_votes > sell_votes else ('SELL' if sell_votes > buy_votes else 'HOLD')
        
        # Tiered Consensus Logic (Fix #2)
        preliminary_signal = 'HOLD'
        tier_level = None
        
        if max_votes >= 4:
            # Tier 1 (Strong): 4+ agents agree
            preliminary_signal = dominant_signal
            tier_level = "TIER_1_STRONG"
            reasons.append(f"🎯 TIER 1 SIGNAL: {max_votes}/4 agents agree (Strong Consensus)")
        elif max_votes >= 3:
            # Tier 2 (Moderate): 3 agents agree
            preliminary_signal = dominant_signal
            tier_level = "TIER_2_MODERATE"
            reasons.append(f"📊 TIER 2 SIGNAL: {max_votes}/4 agents agree (Moderate Consensus)")
        else:
            preliminary_signal = 'HOLD'
            reasons.append(f"📊 Votes: {buy_votes} BUY, {sell_votes} SELL, {hold_votes} HOLD - No consensus")
        
        # Check for blocker reason (Diagnostic)
        if preliminary_signal == 'HOLD' and max_votes < self.min_agents_agree:
            logger.info(f"REASON FOR HOLD: Only {max_votes} {'BUY' if buy_votes > sell_votes else 'SELL'} votes. Need {self.min_agents_agree}.")
        
        # Apply Agent 5 Risk Score adjustment (Fix #4) - No hard veto when disabled
        veto_applied = False
        position_size_adjustment = 1.0  # Default: 100% position size
        
        if self.agent5_veto_enabled and agent5_veto and preliminary_signal != 'HOLD':
            # Legacy: Hard veto still applies if enabled in config
            veto_applied = True
            preliminary_signal = 'HOLD'
            reasons.append("⚠️ Agent 5 (Context) VETO applied - Trade rejected due to risk factors")
        elif not self.agent5_veto_enabled and preliminary_signal != 'HOLD':
            # Fix #4: Instead of veto, adjust position size based on risk score
            if agent5_risk_score > 70:
                position_size_adjustment = 0.25  # High risk: 25% position
                reasons.append(f"⚠️ High Risk Score ({agent5_risk_score}) - Position reduced to 25%")
            elif agent5_risk_score > 50:
                position_size_adjustment = 0.50  # Medium risk: 50% position
                reasons.append(f"📊 Medium Risk Score ({agent5_risk_score}) - Position reduced to 50%")
            else:
                reasons.append(f"✅ Low Risk Score ({agent5_risk_score}) - Full position allowed")
            
            if agent5_status == 'REJECT' and agent5_risk_score > 80:
                # Extreme risk - still reject the trade
                preliminary_signal = 'HOLD'
                reasons.append("🚫 EXTREME RISK - Trade rejected by Agent 5")
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Apply minimum confidence threshold
        if preliminary_signal != 'HOLD' and avg_confidence < self.min_confidence:
            preliminary_signal = 'HOLD'
            reasons.append(f"Confidence ({avg_confidence:.1f}%) below threshold ({self.min_confidence}%)")
        
        # Calculate entry, SL, TP
        current_price = df['Close'].iloc[-1]
        entry, sl, tp = self._calculate_levels(df, preliminary_signal, symbol)
        
        # Build reasons list
        if preliminary_signal == 'BUY':
            reasons.append(f"✅ {buy_votes} agents voted BUY")
            reasons.append(f"📊 Average confidence: {avg_confidence:.1f}%")
        elif preliminary_signal == 'SELL':
            reasons.append(f"✅ {sell_votes} agents voted SELL")
            reasons.append(f"📊 Average confidence: {avg_confidence:.1f}%")
        else:
            reasons.append(f"📊 Votes: {buy_votes} BUY, {sell_votes} SELL, {hold_votes} HOLD")
        
        # Add agent summaries
        for i in range(1, 6):
            key = f'agent{i}'
            result = agent_results.get(key, {})
            if i <= 4:
                sig = result.get('signal', 'N/A')
                conf = result.get('confidence', 0)
                reasons.append(f"• Agent {i}: {sig} ({conf}%)")
            else:
                status = result.get('status', 'N/A')
                reasons.append(f"• Agent 5 (Context): {status}")
        
        return {
            'signal': preliminary_signal,
            'confidence': int(avg_confidence),
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'reasons': reasons,
            'veto_applied': veto_applied,
            'agents_agreeing': max(buy_votes, sell_votes),
            'tier_level': tier_level,
            'position_size_adjustment': position_size_adjustment,
            'risk_score': agent5_risk_score
        }
    
    def _calculate_levels(
        self,
        df: pd.DataFrame,
        signal: str,
        symbol: str
    ) -> Tuple[float, float, float]:
        """
        Calculate entry, stop-loss, and take-profit levels.
        
        Args:
            df: Price data DataFrame
            signal: BUY or SELL
            symbol: Trading symbol
        
        Returns:
            Tuple of (entry, stop_loss, take_profit)
        """
        if signal == 'HOLD':
            return 0.0, 0.0, 0.0
        
        current_price = df['Close'].iloc[-1]
        
        # Calculate ATR for stop loss
        current_atr = atr(df, 14).iloc[-1]
        
        # Get recent swing high/low
        lookback = 20
        recent_high = df['High'].iloc[-lookback:].max()
        recent_low = df['Low'].iloc[-lookback:].min()
        
        stop_multiplier = config.get_stop_atr_multiplier()
        target_multiplier = config.get_target_atr_multiplier()
        
        if signal == 'BUY':
            # Entry: current price
            entry = current_price
            
            # Stop loss: below recent low or ATR-based
            sl_atr = current_price - (current_atr * stop_multiplier)
            sl_structural = recent_low * 0.998  # Just below recent low
            stop_loss = min(sl_atr, sl_structural)
            
            # Take profit: R:R based
            risk = entry - stop_loss
            take_profit = entry + (risk * target_multiplier)
            
        else:  # SELL
            # Entry: current price
            entry = current_price
            
            # Stop loss: above recent high or ATR-based
            sl_atr = current_price + (current_atr * stop_multiplier)
            sl_structural = recent_high * 1.002  # Just above recent high
            stop_loss = max(sl_atr, sl_structural)
            
            # Take profit: R:R based
            risk = stop_loss - entry
            take_profit = entry - (risk * target_multiplier)
        
        return round(entry, 4), round(stop_loss, 4), round(take_profit, 4)
    
    def _create_error_result(self, symbol: str, error: str) -> Dict[str, Any]:
        """Create error result dictionary."""
        return {
            'symbol': symbol,
            'timeframe': 'N/A',
            'timestamp': datetime.now(),
            'agents': {},
            'decision': 'HOLD',
            'avg_confidence': 0,
            'entry': 0,
            'stop_loss': 0,
            'take_profit': 0,
            'reasons': [f'Error: {error}'],
            'veto_applied': False,
            'agents_agreeing': 0
        }
