"""
Super AI Trader - Telegram Signal Formatter
Formats trading signals for Telegram messages.
"""

from datetime import datetime
from typing import List


class SignalFormatter:
    """Formats trading signals into Telegram-compatible messages."""
    
    @staticmethod
    def generate_confidence_bar(confidence: int) -> str:
        """
        Generate a visual confidence bar using emojis.
        
        Args:
            confidence: Confidence percentage (0-100)
        
        Returns:
            String with 🟩 and ⬛ emojis representing confidence
        """
        filled_bars = confidence // 10
        empty_bars = 10 - filled_bars
        
        return '🟩' * filled_bars + '⬛' * empty_bars
    
    @staticmethod
    def format_signal(symbol: str, direction: str, entry: float, 
                     stop_loss: float, take_profit: float, 
                     lots: float, confidence: int, reasons: List[str],
                     timestamp: datetime = None) -> str:
        """
        Format a complete trading signal for Telegram.
        
        Args:
            symbol: Trading symbol
            direction: 'BUY' or 'SELL'
            entry: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            lots: Position size in lots
            confidence: Confidence percentage
            reasons: List of reasons for the signal
            timestamp: Signal timestamp (defaults to now)
        
        Returns:
            Formatted Telegram message string
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Choose emoji based on direction
        emoji = "🟢" if direction == "BUY" else "🔴"
        direction_arrow = "⬆️" if direction == "BUY" else "⬇️"
        
        # Generate confidence bar
        confidence_bar = SignalFormatter.generate_confidence_bar(confidence)
        
        # Format reasons
        reasons_text = "\n".join([f"• {r}" for r in reasons[:5]])  # Limit to 5 reasons
        if len(reasons) > 5:
            reasons_text += f"\n• ... and {len(reasons) - 5} more"
        
        # Build the message
        message = f"""╔═══════════════════════════════╗
║ ⚡️ Super AI Trader SIGNAL ║
╚═══════════════════════════════╝

📍 {symbol} • {entry:.5f}
🕐 {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

{emoji} {direction_arrow} {direction} | {confidence}% | {confidence_bar}

━━━━━━━━━━━━━━━━━━━━━━━
📊 ENTRY: {entry:.5f}
🛑 SL: {stop_loss:.5f}
🎯 TP: {take_profit:.5f}
💰 Size: {lots:.2f} lots

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 REASONS:
{reasons_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ Risk Management: 1% per trade
📈 R:R Ratio: ~1:2 (SL: 1.5 ATR, TP: 3 ATR)
"""
        
        return message
    
    @staticmethod
    def format_status_message(system_status: dict) -> str:
        """
        Format system status for Telegram.
        
        Args:
            system_status: Dictionary with system status information
        
        Returns:
            Formatted status message
        """
        status_emoji = "🟢" if system_status.get('trading_enabled', False) else "🔴"
        
        message = f"""╔═══════════════════════════════╗
║ 📊 Super AI Trader STATUS ║
╚═══════════════════════════════╝

{status_emoji} System: {'ACTIVE' if system_status.get('trading_enabled') else 'STOPPED'}

━━━━━━━━━━━━━━━━━━━━━━━
💼 Account Info:
• Balance: ${system_status.get('balance', 0):,.2f}
• Daily PnL: ${system_status.get('daily_pnl', 0):,.2f} ({system_status.get('daily_pnl_pct', 0):.2f}%)
• Trades Today: {system_status.get('trades_today', 0)}

━━━━━━━━━━━━━━━━━━━━━━━
🤖 Agent Status:
"""
        
        agents = system_status.get('agents', [])
        for agent in agents:
            agent_emoji = "✅" if agent.get('enabled', False) else "❌"
            message += f"• {agent_emoji} {agent.get('name', 'Unknown')}\n"
        
        message += f"""
━━━━━━━━━━━━━━━━━━━━━━━
📈 Market Analysis:
• Symbols Monitored: {', '.join(system_status.get('symbols', []))}
• Last Update: {system_status.get('last_update', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use /help for available commands
"""
        
        return message
    
    @staticmethod
    def format_risk_message(risk_summary: dict) -> str:
        """
        Format risk management summary for Telegram.
        
        Args:
            risk_summary: Dictionary with risk management data
        
        Returns:
            Formatted risk message
        """
        can_trade_emoji = "✅" if risk_summary.get('can_trade', False) else "⚠️"
        
        message = f"""╔═══════════════════════════════╗
║ 🛡️ Risk Management Report ║
╚═══════════════════════════════╝

{can_trade_emoji} Trading Allowed: {'Yes' if risk_summary.get('can_trade') else 'No'}
Reason: {risk_summary.get('daily_limit_reason', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━
💰 Account:
• Balance: ${risk_summary.get('account_balance', 0):,.2f}
• Risk/Trade: {risk_summary.get('risk_per_trade_pct', 0):.1f}% (${risk_summary.get('risk_amount_per_trade', 0):,.2f})

━━━━━━━━━━━━━━━━━━━━━━━
📊 Today's Activity:
• PnL: ${risk_summary.get('daily_pnl', 0):,.2f} ({risk_summary.get('daily_pnl_pct', 0):.2f}%)
• Trades: {risk_summary.get('trades_today', 0)}/{risk_summary.get('max_trades_per_day', 0)}
• Max DD: {risk_summary.get('max_daily_drawdown_pct', 0):.1f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return message
    
    @staticmethod
    def format_evolution_message(evolution_data: dict) -> str:
        """
        Format self-learning evolution update for Telegram.
        
        Args:
            evolution_data: Dictionary with evolution/generation data
        
        Returns:
            Formatted evolution message
        """
        message = f"""╔═══════════════════════════════╗
║ 🧬 Strategy Evolution Update ║
╚═══════════════════════════════╝

Generation: {evolution_data.get('generation', 0)}

━━━━━━━━━━━━━━━━━━━━━━━
📊 Top Strategies:
"""
        
        strategies = evolution_data.get('top_strategies', [])
        for i, strategy in enumerate(strategies, 1):
            pf = strategy.get('profit_factor', 0)
            dd = strategy.get('max_drawdown', 0)
            trades = strategy.get('num_trades', 0)
            message += f"{i}. PF: {pf:.2f} | DD: {dd:.1f}% | Trades: {trades}\n"
        
        message += f"""
━━━━━━━━━━━━━━━━━━━━━━━
🔄 Status: {evolution_data.get('status', 'Running')}
Next Cycle: {evolution_data.get('next_cycle', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return message
    
    @staticmethod
    def format_help_message() -> str:
        """Return help message with available commands."""
        return """╔═══════════════════════════════╗
║ ❓ Super AI Trader Help ║
╚═══════════════════════════════╝

Available Commands:

/start - Start the trading system
/stop - Stop the trading system
/status - Get current system status
/risk - View risk management report
/evolution - View strategy evolution status
/help - Show this help message

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

System Features:
• 5 Specialist AI Agents
• 50+ Technical Indicators
• Multi-Timeframe Analysis
• Genetic Self-Learning
• Automatic Risk Management

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
