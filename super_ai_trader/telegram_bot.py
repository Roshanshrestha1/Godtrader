"""
Super AI Trader - Telegram Bot Module
Provides real-time signal notifications and interactive menu for the trading system.
Uses python-telegram-bot library from GitHub.
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

from config import MENU_SYMBOLS, SUPPORTED_TIMEFRAMES
from utils.formatter import SignalFormatter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# User state storage for session management
user_states = {}  # dict[user_id] = {'state': ..., 'symbol': ..., 'timeframe': ...}


class TelegramBot:
    """
    Telegram Bot for Super AI Trader
    
    Features:
    - Real-time signal notifications
    - Interactive menu with commands
    - System status monitoring
    - Manual signal requests
    - Trading control (start/stop)
    """
    
    def __init__(self, token: str, chat_id: Optional[int] = None):
        """
        Initialize Telegram Bot
        
        Args:
            token: Telegram Bot API token from @BotFather
            chat_id: Optional specific chat ID for notifications
        """
        self.token = token
        self.chat_id = chat_id
        self.application: Optional[Application] = None
        self.master_brain = None
        self.running = False
        
        # Store last signals for quick access
        self.last_signals = []
        
    def set_master_brain(self, master_brain):
        """Set reference to MasterBrain for status queries."""
        self.master_brain = master_brain
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = (
            "🤖 *Welcome to Super AI Trader!*\n\n"
            "Your AI-powered trading assistant is ready.\n\n"
            "Use /menu to see all available commands.\n"
            "Use /help for detailed information."
        )
        await self._send_message(update.effective_chat.id, welcome_message, parse_mode='Markdown')
        
        # Send main menu inline keyboard
        keyboard = [
            [InlineKeyboardButton('🔍 Find Best Trades by AI', callback_data='find_best_trades')],
            [InlineKeyboardButton('⚙️ Trading Settings', callback_data='trading_settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await self._send_message(
            update.effective_chat.id,
            "🎛️ *Main Menu*\n\nSelect an option:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = (
            "📚 *Super AI Trader - Help Guide*\n\n"
            "*Commands:*\n"
            "/menu - Show main menu\n"
            "/status - Show system status\n"
            "/signals - View recent signals\n"
            "/start_trading - Enable trading\n"
            "/stop_trading - Disable trading\n"
            "/balance - Show account balance\n"
            "/refresh - Get latest analysis\n\n"
            "*Features:*\n"
            "• Real-time signal notifications\n"
            "• Multi-agent AI analysis\n"
            "• Risk management\n"
            "• Support for Forex, Crypto, Stocks"
        )
        await self._send_message(update.effective_chat.id, help_text, parse_mode='Markdown')
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command - Show interactive menu."""
        keyboard = [
            [InlineKeyboardButton("🔍 Find Best Trades by AI", callback_data='find_best_trades')],
            [InlineKeyboardButton("⚙️ Trading Settings", callback_data='trading_settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        menu_text = (
            "🎛️ *Super AI Trader - Control Menu*\n\n"
            "Select an option below to interact with the system."
        )
        await self._send_message(
            update.effective_chat.id, 
            menu_text, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        if not self.master_brain:
            await self._send_message(
                update.effective_chat.id,
                "❌ Master Brain not initialized yet."
            )
            return
        
        status = self.master_brain.get_system_status()
        
        status_text = (
            "📊 *System Status*\n\n"
            f"{'✅ Trading Enabled' if status['trading_enabled'] else '⏸️ Trading Disabled'}\n"
            f"💰 Balance: ${status['balance']:,.2f}\n"
            f"📈 Daily PnL: ${status['daily_pnl']:.2f} ({status['daily_pnl_pct']:+.2f}%)\n"
            f"📊 Trades Today: {status['trades_today']}\n"
            f"🔔 Signals Today: {status['signals_today']}\n\n"
            f"*Active Agents:* {len(status['agents'])}/5\n"
            f"*Symbols:* {', '.join(status['symbols'])}\n\n"
            f"Last Update: {status['last_update']}"
        )
        await self._send_message(update.effective_chat.id, status_text, parse_mode='Markdown')
    
    async def signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command - Show recent signals."""
        if not self.last_signals:
            await self._send_message(
                update.effective_chat.id,
                "📭 No signals generated yet."
            )
            return
        
        # Show last 5 signals
        recent_signals = self.last_signals[-5:]
        
        signals_text = "📈 *Recent Signals*\n\n"
        for i, signal in enumerate(reversed(recent_signals), 1):
            direction_emoji = "🟢" if signal['direction'] == 'BUY' else "🔴"
            signals_text += (
                f"{i}. {direction_emoji} *{signal['symbol']}* {signal['direction']}\n"
                f"   Entry: {signal['entry']:.5f}\n"
                f"   SL: {signal['stop_loss']:.5f} | TP: {signal['take_profit']:.5f}\n"
                f"   Confidence: {signal['confidence']}%\n"
                f"   Time: {signal['timestamp'].strftime('%H:%M:%S')}\n\n"
            )
        
        await self._send_message(update.effective_chat.id, signals_text, parse_mode='Markdown')
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command."""
        if not self.master_brain:
            await self._send_message(
                update.effective_chat.id,
                "❌ Master Brain not initialized yet."
            )
            return
        
        status = self.master_brain.get_system_status()
        risk_summary = status['risk_summary']
        
        balance_text = (
            "💰 *Account Balance*\n\n"
            f"Current Balance: *${status['balance']:,.2f}*\n"
            f"Daily PnL: *${status['daily_pnl']:.2f}* ({status['daily_pnl_pct']:+.2f}%)\n\n"
            f"*Risk Management:*\n"
            f"• Risk per Trade: {risk_summary['risk_per_trade']*100:.1f}%\n"
            f"• Max Daily Loss: ${risk_summary['max_daily_loss']:.2f}\n"
            f"• Trades Today: {risk_summary['trades_today']}\n"
            f"• Daily Loss Limit Reached: {'Yes ⚠️' if risk_summary['daily_loss_limit_reached'] else 'No ✅'}"
        )
        await self._send_message(update.effective_chat.id, balance_text, parse_mode='Markdown')
    
    async def start_trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start_trading command."""
        if not self.master_brain:
            await self._send_message(
                update.effective_chat.id,
                "❌ Master Brain not initialized yet."
            )
            return
        
        self.master_brain.start_trading()
        await self._send_message(
            update.effective_chat.id,
            "✅ *Trading Enabled*\n\nThe system is now actively analyzing markets and sending signals.",
            parse_mode='Markdown'
        )
    
    async def stop_trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop_trading command."""
        if not self.master_brain:
            await self._send_message(
                update.effective_chat.id,
                "❌ Master Brain not initialized yet."
            )
            return
        
        self.master_brain.stop_trading()
        await self._send_message(
            update.effective_chat.id,
            "⏹️ *Trading Disabled*\n\nThe system has stopped analyzing markets. No new signals will be sent.",
            parse_mode='Markdown'
        )
    
    async def refresh_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /refresh command - Trigger immediate analysis."""
        if not self.master_brain:
            await self._send_message(
                update.effective_chat.id,
                "❌ Master Brain not initialized yet."
            )
            return
        
        await self._send_message(
            update.effective_chat.id,
            "🔄 Running analysis on all symbols... Please wait."
        )
        
        try:
            signals = await self.master_brain.run_analysis_cycle()
            
            if signals:
                message = f"✅ Analysis complete! Generated *{len(signals)}* signal(s):\n\n"
                for signal in signals:
                    direction_emoji = "🟢" if signal['direction'] == 'BUY' else "🔴"
                    message += (
                        f"{direction_emoji} *{signal['symbol']}* {signal['direction']}\n"
                        f"Entry: {signal['entry']:.5f} | SL: {signal['stop_loss']:.5f} | TP: {signal['take_profit']:.5f}\n"
                        f"Confidence: {signal['confidence']}%\n\n"
                    )
                await self._send_message(update.effective_chat.id, message, parse_mode='Markdown')
            else:
                await self._send_message(
                    update.effective_chat.id,
                    "✅ Analysis complete. No signals generated at this time."
                )
        except Exception as e:
            logger.error(f"Error during refresh: {e}")
            await self._send_message(
                update.effective_chat.id,
                f"❌ Error during analysis: {str(e)}"
            )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks from menu."""
        query = update.callback_query
        user_id = update.effective_user.id
        await query.answer()
        
        action = query.data
        
        # Main menu actions
        if action == 'find_best_trades':
            await self.handle_find_best_trades(update, context)
        elif action == 'trading_settings':
            await self.handle_trading_settings(update, context)
        # Asset group selection
        elif action.startswith('group_'):
            group = action.replace('group_', '')
            await self.handle_asset_group_selection(update, context, group)
        # Asset selection
        elif action.startswith('asset_'):
            symbol = action.replace('asset_', '')
            await self.handle_asset_selection(update, context, user_id, symbol)
        # Timeframe selection
        elif action.startswith('tf_'):
            tf = action.replace('tf_', '')
            await self.handle_timeframe_selection(update, context, user_id, tf)
        # Analyze selected pair
        elif action == 'analyze_pair':
            await self.handle_analyze_pair(update, context, user_id)
        # Back buttons
        elif action == 'main_menu':
            await self.handle_back_to_main_menu(update, context)
        elif action == 'back_to_settings':
            await self.handle_back_to_settings(update, context)
        # Legacy actions (keep for backward compatibility)
        elif action == 'status':
            await self.status_command(update, context)
        elif action == 'signals':
            await self.signals_command(update, context)
        elif action == 'start_trading':
            await self.start_trading_command(update, context)
        elif action == 'stop_trading':
            await self.stop_trading_command(update, context)
        elif action == 'balance':
            await self.balance_command(update, context)
        elif action == 'refresh':
            await self.refresh_command(update, context)
        elif action == 'help':
            await self.help_command(update, context)
    
    async def handle_find_best_trades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle 'Find Best Trades by AI' button."""
        if not self.master_brain:
            await query.edit_message_text('❌ Master Brain not initialized.')
            return
        
        query = update.callback_query
        await query.edit_message_text('🔍 Analyzing all symbols... Please wait.')
        
        try:
            top_trades = await self.master_brain.analyze_all_symbols()
            
            if not top_trades:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text='No high-confidence trades found at this time. Please check later.'
                )
                return
            
            # Format and send top 3 trades
            messages = SignalFormatter.format_best_trades_cards(top_trades[:3])
            
            for msg in messages:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=msg,
                    parse_mode='HTML'
                )
                
        except Exception as e:
            logger.error(f"Error in find best trades: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'❌ Error: {str(e)}'
            )
    
    async def handle_trading_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle 'Trading Settings' button - show asset groups."""
        keyboard = []
        
        for group_name in MENU_SYMBOLS.keys():
            keyboard.append([InlineKeyboardButton(f"📊 {group_name}", callback_data=f'group_{group_name}')])
        
        keyboard.append([InlineKeyboardButton('🔙 Back', callback_data='main_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text="⚙️ *Trading Settings*\n\nSelect an asset group:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_asset_group_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, group: str):
        """Handle asset group selection - show symbols in group."""
        symbols = MENU_SYMBOLS.get(group, [])
        
        keyboard = []
        for symbol in symbols:
            keyboard.append([InlineKeyboardButton(symbol, callback_data=f'asset_{symbol}')])
        
        keyboard.append([InlineKeyboardButton('🔙 Back', callback_data='back_to_settings')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=f"📊 *{group}*\n\nSelect a symbol:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_asset_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, symbol: str):
        """Handle symbol selection - store in session and prompt for timeframe."""
        # Store symbol in user session
        if user_id not in user_states:
            user_states[user_id] = {}
        
        user_states[user_id]['symbol'] = symbol
        user_states[user_id]['state'] = 'CHOOSE_TF'
        
        # Show timeframe selection
        keyboard = []
        for tf in SUPPORTED_TIMEFRAMES:
            keyboard.append([InlineKeyboardButton(tf, callback_data=f'tf_{tf}')])
        
        keyboard.append([InlineKeyboardButton('🔙 Back', callback_data='back_to_settings')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=f"✅ Selected: *{symbol}*\n\n⏱️ Now select a timeframe:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_timeframe_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, tf: str):
        """Handle timeframe selection - store in session and show analyze button."""
        # Store timeframe in user session
        if user_id not in user_states:
            user_states[user_id] = {}
        
        user_states[user_id]['timeframe'] = tf
        user_states[user_id]['state'] = 'READY_TO_ANALYZE'
        
        symbol = user_states[user_id].get('symbol', 'Unknown')
        
        # Show analyze button
        keyboard = [
            [InlineKeyboardButton("🧠 Analyze Selected Pair", callback_data='analyze_pair')],
            [InlineKeyboardButton('🔙 Back', callback_data='back_to_settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=f"✅ Symbol: *{symbol}*\n✅ Timeframe: *{tf}*\n\nReady to analyze!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_analyze_pair(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Trigger analysis on selected symbol+timeframe."""
        state = user_states.get(user_id, {})
        symbol = state.get('symbol')
        tf = state.get('timeframe')
        
        if not symbol or not tf:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='❌ Please select a currency and timeframe first.'
            )
            return
        
        await update.callback_query.edit_message_text('🧠 Analyzing... Please wait.')
        
        try:
            if not self.master_brain:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text='❌ Master Brain not initialized.'
                )
                return
            
            analysis = await self.master_brain.analyze_single(symbol, tf)
            msg = SignalFormatter.format_single_analysis(analysis)
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=msg,
                parse_mode='HTML'
            )
            
            # Reset user state
            user_states[user_id] = {}
            
        except Exception as e:
            logger.error(f"Error in analyze pair: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'❌ Error: {str(e)}'
            )
    
    async def handle_back_to_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle back to main menu."""
        keyboard = [
            [InlineKeyboardButton('🔍 Find Best Trades by AI', callback_data='find_best_trades')],
            [InlineKeyboardButton('⚙️ Trading Settings', callback_data='trading_settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text="🎛️ *Main Menu*\n\nSelect an option:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_back_to_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle back to trading settings."""
        await self.handle_trading_settings(update, context)
    
    async def send_signal(self, signal: dict):
        """
        Send a trading signal notification to Telegram.
        
        Args:
            signal: Signal dictionary with trade details
        """
        direction_emoji = "🟢" if signal['direction'] == 'BUY' else "🔴"
        
        message = (
            f"{direction_emoji} *NEW SIGNAL* {direction_emoji}\n\n"
            f"📊 *Symbol:* {signal['symbol']}\n"
            f"📈 *Direction:* {signal['direction']}\n\n"
            f"💰 *Entry:* {signal['entry']:.5f}\n"
            f"🛑 *Stop Loss:* {signal['stop_loss']:.5f}\n"
            f"🎯 *Take Profit:* {signal['take_profit']:.5f}\n\n"
            f"📊 *Lots:* {signal['lots']:.2f}\n"
            f"🎯 *Confidence:* {signal['confidence']}%\n\n"
            f"📝 *Reasons:*\n"
        )
        
        for reason in signal['reasons'][:3]:
            message += f"• {reason}\n"
        
        message += f"\n⏰ *Time:* {signal['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"📊 *Votes:* {signal['buy_votes']} BUY / {signal['sell_votes']} SELL"
        
        # Send to chat_id if specified, otherwise broadcast
        target_chat_id = self.chat_id if self.chat_id else None
        
        if self.application and self.running:
            try:
                if target_chat_id:
                    await self.application.bot.send_message(
                        chat_id=target_chat_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                else:
                    # Broadcast to all chats that have interacted with the bot
                    logger.info(f"Signal ready to send: {signal['symbol']} {signal['direction']}")
            except Exception as e:
                logger.error(f"Failed to send signal: {e}")
        
        # Store for later retrieval
        self.last_signals.append(signal)
        if len(self.last_signals) > 20:
            self.last_signals.pop(0)
        
        logger.info(f"Signal notification prepared: {signal['symbol']} {signal['direction']}")
    
    async def _send_message(self, chat_id: int, text: str, reply_markup=None, parse_mode=None):
        """Send a message to a specific chat."""
        if not self.application or not self.running:
            logger.warning("Bot not running, cannot send message")
            return
        
        try:
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def start(self):
        """Start the Telegram bot."""
        if self.running:
            logger.warning("Bot already running")
            return
        
        logger.info("Starting Telegram Bot...")
        
        # Build application
        self.application = Application.builder().token(self.token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("signals", self.signals_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("start_trading", self.start_trading_command))
        self.application.add_handler(CommandHandler("stop_trading", self.stop_trading_command))
        self.application.add_handler(CommandHandler("refresh", self.refresh_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Start the bot
        await self.application.initialize()
        await self.application.start()
        
        if self.application.updater:
            await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        self.running = True
        logger.info("✅ Telegram Bot started successfully!")
        logger.info("Use /menu to see all available commands")
    
    async def stop(self):
        """Stop the Telegram bot."""
        if not self.running:
            return
        
        logger.info("Stopping Telegram Bot...")
        
        if self.application and self.application.updater:
            await self.application.updater.stop()
        if self.application:
            await self.application.stop()
        if self.application:
            await self.application.shutdown()
        
        self.running = False
        logger.info("Telegram Bot stopped")


# Example usage and testing
if __name__ == "__main__":
    # This is for testing purposes only
    # Replace with your actual bot token from @BotFather
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    
    async def test_bot():
        bot = TelegramBot(token=BOT_TOKEN)
        await bot.start()
        
        # Keep running
        while True:
            await asyncio.sleep(60)
    
    # Uncomment to test
    # asyncio.run(test_bot())
