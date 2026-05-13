"""
CLI script for testing the Master Brain analysis without Telegram.
Useful for development and debugging.
"""

import argparse
import json
import logging
from datetime import datetime
from config import config
from master_brain import MasterBrain
from utils.formatter import format_single_analysis, format_best_trades_cards

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_single(symbol: str, timeframe: str = None, verbose: bool = False):
    """Analyze a single symbol."""
    brain = MasterBrain()
    
    print(f"\n{'='*60}")
    print(f"Analyzing {symbol}...")
    print(f"{'='*60}\n")
    
    result = brain.analyze_single(symbol, timeframe)
    
    if verbose:
        # Print full JSON
        print(json.dumps(result, indent=2, default=str))
    else:
        # Print formatted output
        if result['decision'] == 'HOLD':
            print(f"Symbol: {result['symbol']}")
            print(f"Timeframe: {result['timeframe']}")
            print(f"Decision: HOLD")
            print(f"\nReasons:")
            for reason in result['reasons']:
                print(f"  • {reason}")
        else:
            formatted = format_single_analysis(result)
            print(formatted)
    
    return result


def analyze_all(verbose: bool = False):
    """Analyze all configured symbols and show top trades."""
    brain = MasterBrain()
    
    print(f"\n{'='*60}")
    print("Scanning all markets...")
    print(f"{'='*60}\n")
    
    results = brain.analyze_all_symbols()
    
    if not results:
        print("No high-confidence trade signals found at this time.")
        return
    
    print(f"Found {len(results)} valid signals\n")
    
    # Show top 3
    top_trades = results[:3]
    cards = format_best_trades_cards(top_trades)
    
    for i, card in enumerate(cards, 1):
        print(card)
        print("\n")
    
    # Optionally show all
    if verbose and len(results) > 3:
        print(f"\n{'='*60}")
        print(f"Additional signals ({len(results) - 3} more):")
        print(f"{'='*60}\n")
        
        for result in results[3:]:
            print(f"{result['symbol']}: {result['decision']} ({result['avg_confidence']}%)")


def test_specific_agent(symbol: str, agent_num: int, timeframe: str = None):
    """Test a specific agent in isolation."""
    from utils.data_fetcher import fetch_ohlcv
    from agents.trend_agent import TrendAgent
    from agents.volume_agent import VolumeAgent
    from agents.price_action_agent import PriceActionAgent
    from agents.indicator_agent import IndicatorAgent
    from agents.context_agent import ContextAgent
    
    print(f"\n{'='*60}")
    print(f"Testing Agent {agent_num} on {symbol}...")
    print(f"{'='*60}\n")
    
    # Fetch data
    tf = timeframe or config.get_main_timeframe()
    df = fetch_ohlcv(symbol, interval=tf, period='7d')
    
    # Select and run agent
    agents = {
        1: TrendAgent(),
        2: VolumeAgent(),
        3: PriceActionAgent(),
        4: IndicatorAgent(),
        5: ContextAgent()
    }
    
    if agent_num not in agents:
        print(f"Invalid agent number. Choose 1-5.")
        return
    
    agent = agents[agent_num]
    
    if agent_num == 5:
        # Context agent needs additional parameters
        result = agent.analyze(df.copy(), 'HOLD', df['Close'].iloc[-1])
    else:
        result = agent.analyze(df.copy())
    
    print(f"Agent: {result['agent']}")
    print(f"Signal/Status: {result.get('signal', result.get('status'))}")
    print(f"Confidence: {result.get('confidence', 0)}%")
    print(f"\nReasons:")
    for reason in result['reasons']:
        print(f"  • {reason}")
    
    if result.get('details'):
        print(f"\nDetails:")
        for key, value in result['details'].items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")


def main():
    parser = argparse.ArgumentParser(
        description='AI Trading Analysis System - CLI Test Tool'
    )
    
    parser.add_argument(
        '--mode',
        choices=['single', 'all', 'agent'],
        default='single',
        help='Analysis mode: single (one symbol), all (scan all), agent (test specific agent)'
    )
    
    parser.add_argument(
        '--symbol',
        type=str,
        default='AAPL',
        help='Symbol to analyze (default: AAPL)'
    )
    
    parser.add_argument(
        '--timeframe',
        type=str,
        choices=['1m', '5m', '15m', '1h', '4h', '1d'],
        default=None,
        help='Timeframe for analysis'
    )
    
    parser.add_argument(
        '--agent',
        type=int,
        choices=[1, 2, 3, 4, 5],
        help='Agent number to test (1-5, only used with --mode agent)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output (full JSON)'
    )
    
    args = parser.parse_args()
    
    print("\n╔═══════════════════════════════════════════════════════╗")
    print("║     🤖 AI TRADING ANALYSIS SYSTEM - CLI TOOL         ║")
    print("╚═══════════════════════════════════════════════════════╝")
    
    try:
        if args.mode == 'single':
            analyze_single(args.symbol, args.timeframe, args.verbose)
        
        elif args.mode == 'all':
            analyze_all(args.verbose)
        
        elif args.mode == 'agent':
            if not args.agent:
                print("Error: --agent is required when using --mode agent")
                return
            analyze_specific_agent(args.symbol, args.agent, args.timeframe)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")


if __name__ == '__main__':
    main()
