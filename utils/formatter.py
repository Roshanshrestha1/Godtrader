"""
Formatter utilities for the Stable Stock Analysis System.
Formats signals, trade cards, and analysis results for Telegram and console output.
"""

from typing import List, Dict, Any
from datetime import datetime
from utils.data_fetcher import format_price


def create_confidence_bar(confidence: int, max_length: int = 10) -> str:
    """
    Create a visual confidence bar.
    
    Args:
        confidence: Confidence percentage (0-100)
        max_length: Maximum length of the bar
    
    Returns:
        String representation of confidence bar
    """
    filled_length = int((confidence / 100) * max_length)
    empty_length = max_length - filled_length
    
    bar = '█' * filled_length + '░' * empty_length
    return f"[{bar}]"


def format_best_trades_cards(top_trades: List[Dict[str, Any]]) -> List[str]:
    """
    Format top trades as individual message cards.
    
    Args:
        top_trades: List of trade signal dictionaries
    
    Returns:
        List of formatted message strings
    """
    messages = []
    
    for rank, trade in enumerate(top_trades[:3], 1):
        symbol = trade.get('symbol', 'UNKNOWN')
        direction = trade.get('direction', 'HOLD')
        confidence = trade.get('confidence', 0)
        entry = trade.get('entry', 0)
        sl = trade.get('stop_loss', 0)
        tp = trade.get('take_profit', 0)
        timestamp = trade.get('timestamp', datetime.now())
        reasons = trade.get('reasons', [])
        
        # Calculate risk-reward ratio
        if entry > 0 and sl > 0:
            risk = abs(entry - sl)
            reward = abs(tp - entry) if tp > 0 else risk * 2
            rr_ratio = round(reward / risk, 2) if risk > 0 else 0
        else:
            rr_ratio = 0
        
        # Direction emoji and text
        if direction == 'BUY':
            emoji = '🟢'
            dir_text = 'CALL'
        elif direction == 'SELL':
            emoji = '🔴'
            dir_text = 'PUT'
        else:
            emoji = '⚪'
            dir_text = 'HOLD'
        
        # Format timestamp
        if isinstance(timestamp, datetime):
            time_str = timestamp.strftime('%Y-%m-%d %H:%M')
        else:
            time_str = str(timestamp)
        
        # Format reasons
        reasons_text = '\n'.join([f"• {r}" for r in reasons[:5]])  # Limit to 5 reasons
        
        # Build the card
        card = f"""╔═══════════════════════════════╗
║ 🤖 AI TOP TRADE #{rank:<2}          ║
╚═══════════════════════════════╝

📍 {symbol} • {format_price(entry, symbol)}
🕐 {time_str}

{emoji} {dir_text} | {confidence}% | {create_confidence_bar(confidence)}

━━━━━━━━━━━━━━━━━━━━━━━
📊 ENTRY: {format_price(entry, symbol)}
🛑 SL: {format_price(sl, symbol)}
🎯 TP: {format_price(tp, symbol)}
💰 R:R: 1:{rr_ratio}

━━━━━━━━━━━━━━━━━━━━━━━
📋 AGENT REASONS:
{reasons_text}
━━━━━━━━━━━━━━━━━━━━━━━"""
        
        messages.append(card)
    
    return messages


def format_single_analysis(analysis: Dict[str, Any]) -> str:
    """
    Format detailed single-pair analysis.
    
    Args:
        analysis: Analysis dictionary with agent votes and decision
    
    Returns:
        Formatted analysis string
    """
    symbol = analysis.get('symbol', 'UNKNOWN')
    timeframe = analysis.get('timeframe', 'Unknown')
    timestamp = analysis.get('timestamp', datetime.now())
    decision = analysis.get('decision', 'HOLD')
    avg_confidence = analysis.get('avg_confidence', 0)
    entry = analysis.get('entry', 0)
    sl = analysis.get('stop_loss', 0)
    tp = analysis.get('take_profit', 0)
    reasons = analysis.get('reasons', [])
    
    # Agent details
    agents = analysis.get('agents', {})
    agent1_signal = agents.get('agent1', {}).get('signal', 'N/A')
    agent1_conf = agents.get('agent1', {}).get('confidence', 0)
    agent2_signal = agents.get('agent2', {}).get('signal', 'N/A')
    agent3_signal = agents.get('agent3', {}).get('signal', 'N/A')
    agent4_signal = agents.get('agent4', {}).get('signal', 'N/A')
    agent5_status = agents.get('agent5', {}).get('status', 'N/A')
    
    # Format timestamp
    if isinstance(timestamp, datetime):
        time_str = timestamp.strftime('%Y-%m-%d %H:%M')
    else:
        time_str = str(timestamp)
    
    # Decision emoji
    if decision == 'BUY':
        decision_emoji = '🟢 BUY'
    elif decision == 'SELL':
        decision_emoji = '🔴 SELL'
    else:
        decision_emoji = '⚪ HOLD'
    
    # Format reasons
    reasons_text = '\n'.join([f"• {r}" for r in reasons[:7]])  # Limit to 7 reasons
    
    card = f"""╔═══════════════════════════════╗
║ 🧠 AI ANALYSIS                ║
╚═══════════════════════════════╝

📍 {symbol} • {timeframe}
🕐 {time_str}

🔹 Agent 1 (Trend): {agent1_signal} ({agent1_conf}%)
🔹 Agent 2 (Volume): {agent2_signal}
🔹 Agent 3 (PriceAction): {agent3_signal}
🔹 Agent 4 (Indicators): {agent4_signal}
🔹 Agent 5 (Context): {agent5_status}

━━━━━━━━━━━━━━━━━━━━━━━
📊 FINAL DECISION: {decision_emoji} (confidence {avg_confidence}%)
🟢 ENTRY: {format_price(entry, symbol)}
🛑 SL: {format_price(sl, symbol)}
🎯 TP: {format_price(tp, symbol)}

📋 REASONS:
{reasons_text}
━━━━━━━━━━━━━━━━━━━━━━━"""
    
    return card


def format_holding_message(symbol: str, reasons: List[str]) -> str:
    """
    Format a HOLD/no-trade message.
    
    Args:
        symbol: Trading symbol
        reasons: List of reasons for holding
    
    Returns:
        Formatted hold message
    """
    reasons_text = '\n'.join([f"• {r}" for r in reasons])
    
    message = f"""╔═══════════════════════════════╗
║ ⚠️  NO TRADE SIGNAL           ║
╚═══════════════════════════════╝

📍 {symbol}

📋 REASONS TO HOLD:
{reasons_text}

━━━━━━━━━━━━━━━━━━━━━━━
💡 Wait for better setup before entering.
━━━━━━━━━━━━━━━━━━━━━━━"""
    
    return message


def format_error_message(error: str) -> str:
    """
    Format an error message for Telegram.
    
    Args:
        error: Error description
    
    Returns:
        Formatted error message
    """
    return f"""╔═══════════════════════════════╗
║ ❌ ERROR                      ║
╚═══════════════════════════════╝

An error occurred during analysis:

{error}

━━━━━━━━━━━━━━━━━━━━━━━
Please try again later or contact support.
━━━━━━━━━━━━━━━━━━━━━━━"""


def format_welcome_message() -> str:
    """
    Format the welcome message for /start command.
    
    Returns:
        Formatted welcome message
    """
    return """╔═══════════════════════════════╗
║ 🤖 AI TRADING ASSISTANT       ║
╚═══════════════════════════════╝

Welcome! I'm your AI-powered trading analysis bot.

I use a sophisticated multi-agent system with:
✅ 5 specialized AI agents
✅ 22+ technical indicators
✅ Multi-timeframe analysis
✅ Liquidity sweep detection
✅ Volume confirmation

━━━━━━━━━━━━━━━━━━━━━━━

Choose an option below to get started:
• 🔍 Find Best Trades by AI - Get top 3 high-confidence signals
• ⚙️ Trading Settings - Analyze specific pairs manually

━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Disclaimer: This is for educational purposes only. Always do your own research and manage risk properly."""


def format_menu_message() -> str:
    """
    Format the main menu message.
    
    Returns:
        Formatted menu message
    """
    return """╔═══════════════════════════════╗
║ 📱 MAIN MENU                  ║
╚═══════════════════════════════╝

Select an option:

━━━━━━━━━━━━━━━━━━━━━━━
💡 Tip: Use "Find Best Trades" for quick high-probability setups, or "Trading Settings" for detailed analysis of specific pairs."""


def format_asset_group_message(group_name: str) -> str:
    """
    Format asset group selection message.
    
    Args:
        group_name: Name of the asset group
    
    Returns:
        Formatted group selection message
    """
    return f"""╔═══════════════════════════════╗
║ 📊 SELECT ASSET               ║
╚═══════════════════════════════╝

Group: {group_name.replace('_', ' ').title()}

Choose a symbol from the options below:

━━━━━━━━━━━━━━━━━━━━━━━
🔙 Use the Back button to return to previous menu."""


def format_timeframe_message() -> str:
    """
    Format timeframe selection message.
    
    Returns:
        Formatted timeframe selection message
    """
    return """╔═══════════════════════════════╗
║ ⏱️ SELECT TIMEFRAME           ║
╚═══════════════════════════════╝

Choose your analysis timeframe:

• 1m, 5m, 15m - Scalping
• 1h, 4h - Day/Swing Trading
• 1D - Position Trading

━━━━━━━━━━━━━━━━━━━━━━━
🔙 Use the Back button to return."""


def format_back_button_callback() -> str:
    """Format callback data for back button."""
    return "back_to_menu"
