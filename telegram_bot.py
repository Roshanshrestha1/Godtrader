"""
Telegram Bot for AI Trading Analysis System.
Provides interactive menu for finding best trades and analyzing specific pairs.
"""

import logging
import asyncio
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)

from config import config
from master_brain import MasterBrain
from utils.formatter import (
    format_welcome_message,
    format_menu_message,
    format_best_trades_cards,
    format_single_analysis,
    format_holding_message,
    format_error_message,
    format_asset_group_message,
    format_timeframe_message
)

# Cache file path
CACHE_FILE = Path("/workspace/cache/best_trades.json")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(config.get_log_file()),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# User state storage (in production, use Redis or database)
user_states: Dict[int, Dict[str, Any]] = {}

# Conversation states
IDLE, CHOOSE_ASSET_GROUP, CHOOSE_ASSET, CHOOSE_TF = range(4)


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create main menu inline keyboard."""
    keyboard = [
        [InlineKeyboardButton('🔍 Find Best Trades by AI', callback_data='find_best_trades')],
        [InlineKeyboardButton('⚙️ Trading Settings', callback_data='trading_settings')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_asset_groups_keyboard() -> InlineKeyboardMarkup:
    """Create asset groups selection keyboard."""
    symbols_config = config.symbols
    
    keyboard = []
    for group_name in symbols_config.keys():
        display_name = config.get_group_display_name(group_name)
        keyboard.append([InlineKeyboardButton(display_name, callback_data=f'group_{group_name}')])
    
    keyboard.append([InlineKeyboardButton('🔙 Back', callback_data='main_menu')])
    
    return InlineKeyboardMarkup(keyboard)


def get_assets_keyboard(group_name: str) -> InlineKeyboardMarkup:
    """Create assets selection keyboard for a specific group."""
    symbols = config.symbols.get(group_name, [])
    
    keyboard = []
    # Create buttons in rows of 2
    for i in range(0, len(symbols), 2):
        row = []
        for symbol in symbols[i:i+2]:
            display_symbol = symbol.replace('=X', '').replace('=F', '').replace('-USD', '')
            row.append(InlineKeyboardButton(display_symbol, callback_data=f'asset_{symbol}'))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton('🔙 Back', callback_data='trading_settings')])
    
    return InlineKeyboardMarkup(keyboard)


def get_timeframe_keyboard() -> InlineKeyboardMarkup:
    """Create timeframe selection keyboard."""
    timeframes = config.supported_timeframes
    
    keyboard = []
    # Create buttons in rows of 3
    for i in range(0, len(timeframes), 3):
        row = []
        for tf in timeframes[i:i+3]:
            display_tf = tf.replace('1d', 'Daily').replace('1h', '1 Hour').replace('4h', '4 Hours')
            row.append(InlineKeyboardButton(display_tf, callback_data=f'tf_{tf}'))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton('🔙 Back', callback_data='select_asset_group')])
    
    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user_id = update.effective_user.id
    
    # Reset user state
    user_states[user_id] = {'state': IDLE}
    
    welcome_text = format_welcome_message()
    keyboard = get_main_menu_keyboard()
    
    await update.message.reply_text(
        text=welcome_text,
        reply_markup=keyboard
    )
    
    logger.info(f"User {user_id} started the bot")


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /menu command to return to main menu."""
    user_id = update.effective_user.id
    
    # Reset user state
    user_states[user_id] = {'state': IDLE}
    
    menu_text = format_menu_message()
    keyboard = get_main_menu_keyboard()
    
    await update.message.reply_text(
        text=menu_text,
        reply_markup=keyboard
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries from inline keyboards."""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer()  # Acknowledge the callback
    
    data = query.data
    
    # Main menu navigation
    if data == 'main_menu':
        user_states[user_id] = {'state': IDLE}
        menu_text = format_menu_message()
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(text=menu_text, reply_markup=keyboard)
        return
    
    # Find best trades
    elif data == 'find_best_trades':
        await handle_find_best_trades(query, context)
        return
    
    # Trading settings
    elif data == 'trading_settings':
        user_states[user_id] = {'state': CHOOSE_ASSET_GROUP}
        group_text = "╔═══════════════════════════════╗\n║ 📊 SELECT ASSET GROUP         ║\n╚═══════════════════════════════╝\n\nChoose an asset category:"
        keyboard = get_asset_groups_keyboard()
        await query.edit_message_text(text=group_text, reply_markup=keyboard)
        return
    
    # Asset group selection
    elif data.startswith('group_'):
        group_name = data.replace('group_', '')
        user_states[user_id]['selected_group'] = group_name
        user_states[user_id]['state'] = CHOOSE_ASSET
        
        group_text = format_asset_group_message(group_name)
        keyboard = get_assets_keyboard(group_name)
        await query.edit_message_text(text=group_text, reply_markup=keyboard)
        return
    
    # Asset selection
    elif data.startswith('asset_'):
        symbol = data.replace('asset_', '')
        user_states[user_id]['symbol'] = symbol
        user_states[user_id]['state'] = CHOOSE_TF
        
        tf_text = format_timeframe_message()
        keyboard = get_timeframe_keyboard()
        await query.edit_message_text(text=tf_text, reply_markup=keyboard)
        return
    
    # Timeframe selection
    elif data.startswith('tf_'):
        timeframe = data.replace('tf_', '')
        user_states[user_id]['timeframe'] = timeframe
        
        # Trigger analysis
        await perform_single_analysis(query, context, user_id)
        return
    
    # Back button from asset group selection
    elif data == 'select_asset_group':
        user_states[user_id]['state'] = CHOOSE_ASSET_GROUP
        group_text = "╔═══════════════════════════════╗\n║ 📊 SELECT ASSET GROUP         ║\n╚═══════════════════════════════╝\n\nChoose an asset category:"
        keyboard = get_asset_groups_keyboard()
        await query.edit_message_text(text=group_text, reply_markup=keyboard)
        return


def load_cached_trades() -> list:
    """Load best trades from cache file."""
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                
            # Check if cache is fresh (less than 10 minutes old)
            timestamp_str = data.get('timestamp')
            if timestamp_str:
                cache_time = datetime.fromisoformat(timestamp_str)
                age_minutes = (datetime.now() - cache_time).total_seconds() / 60
                
                if age_minutes < 10 and data.get('top_trades'):
                    logging.info(f"✅ Using cached trades (age: {age_minutes:.1f} min)")
                    return data['top_trades']
                else:
                    logging.warning(f"⚠️  Cache too old ({age_minutes:.1f} min), will scan live")
    except Exception as e:
        logging.error(f"❌ Error loading cache: {e}")
    
    return []


async def handle_find_best_trades(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'Find Best Trades' button click - INSTANT response using cache."""
    try:
        # First, try to load from cache (instant response)
        top_trades = load_cached_trades()
        
        if not top_trades:
            # No cache available, show message and trigger background scan
            await query.edit_message_text(
                text="🔍 No recent scan data available.\n\nThe market scanner is starting now...\nPlease wait ~2-3 minutes for the first complete scan.\n\n💡 Tip: Run the market_scanner.py in the background for instant results!"
            )
            return
        
        # Send introduction message
        intro_text = f"╔═══════════════════════════════╗\n║ 🎯 TOP {min(3, len(top_trades))} TRADE SIGNALS        ║\n╚═══════════════════════════════╝\n\nHere are the best opportunities right now:\n\n⏱️ Last scan: {datetime.fromisoformat(load_cache_data().get('timestamp', 'unknown')).strftime('%H:%M:%S')}"
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=intro_text
        )
        
        # Format and send trade cards
        trade_cards = format_best_trades_cards(top_trades[:3])
        
        for card in trade_cards:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=card
            )
            await asyncio.sleep(0.3)  # Small delay between messages
        
        # Send back to menu button
        keyboard = get_main_menu_keyboard()
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="\n━━━━━━━━━━━━━━━━━━━━━━━\nUse the buttons below for more actions:",
            reply_markup=keyboard
        )
        
        logger.info(f"Sent {len(trade_cards)} cached trade signals to user {query.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error in find_best_trades: {e}", exc_info=True)
        error_msg = format_error_message(str(e))
        await query.edit_message_text(text=error_msg)


def load_cache_data() -> dict:
    """Load full cache data."""
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}


async def perform_single_analysis(query, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Perform analysis on selected symbol and timeframe."""
    state = user_states.get(user_id, {})
    symbol = state.get('symbol')
    timeframe = state.get('timeframe')
    
    if not symbol or not timeframe:
        await query.edit_message_text(text="❌ Error: Missing symbol or timeframe. Please start over.")
        return
    
    await query.edit_message_text(text=f"🧠 Analyzing {symbol} on {timeframe} timeframe... Please wait.")
    
    try:
        brain: MasterBrain = context.bot_data['brain']
        
        # Run analysis
        analysis = brain.analyze_single(symbol, timeframe)
        
        # Format and send result
        if analysis['decision'] == 'HOLD':
            hold_text = format_holding_message(symbol, analysis['reasons'])
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=hold_text
            )
        else:
            analysis_text = format_single_analysis(analysis)
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=analysis_text
            )
        
        # Reset user state
        user_states[user_id] = {'state': IDLE}
        
        # Send back to menu button
        keyboard = get_main_menu_keyboard()
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="\n━━━━━━━━━━━━━━━━━━━━━━━\nWhat would you like to do next?",
            reply_markup=keyboard
        )
        
        logger.info(f"Completed analysis for {symbol} ({timeframe}) for user {user_id}: {analysis['decision']}")
        
    except Exception as e:
        logger.error(f"Error in single analysis: {e}", exc_info=True)
        error_msg = format_error_message(str(e))
        await query.edit_message_text(text=error_msg)
        
        # Reset state on error
        user_states[user_id] = {'state': IDLE}


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Update {update} caused error: {context.error}")
    
    if update and update.effective_message:
        error_msg = format_error_message("An unexpected error occurred. Please try again.")
        await update.effective_message.reply_text(text=error_msg)


def create_application() -> Application:
    """Create and configure the Telegram bot application."""
    # Initialize Master Brain
    brain = MasterBrain()
    
    # Create application
    app_builder = Application.builder().token(config.get_bot_token())
    app = app_builder.build()
    
    # Store brain in bot_data for access in handlers
    app.bot_data['brain'] = brain
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    return app


def run_bot() -> None:
    """Run the Telegram bot."""
    logger.info("Starting Telegram bot...")
    
    # Check if bot token is configured
    if not config.get_bot_token():
        logger.error("TELEGRAM_BOT_TOKEN not found. Please set it in environment or config.yaml")
        raise ValueError("Telegram bot token is required")
    
    # Create and run application
    app = create_application()
    
    # Run bot until stopped
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    run_bot()
