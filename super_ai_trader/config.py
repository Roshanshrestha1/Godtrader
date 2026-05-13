"""
Super AI Trader - Configuration Module
Central configuration for tokens, risk parameters, symbols, and system settings.
"""

# Telegram Configuration
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

# Data Source Configuration
# Options: 'binance', 'yfinance', 'auto' (auto tries binance first, falls back to yfinance)
DATA_SOURCE = 'auto'

# Trading Symbols
SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "BTCUSD", "ETHUSD"]

# Timeframes
TIMEFRAMES = {
    "m1": 1,
    "m5": 5,
    "h1": 60,
    "h4": 240
}

# Risk Management Parameters
RISK_PER_TRADE = 0.01  # 1% of account per trade
MAX_DAILY_DRAWDOWN = 0.03  # 3% max daily loss
ATR_MULTIPLIER_SL = 1.5
ATR_MULTIPLIER_TP = 3.0
ACCOUNT_BALANCE = 10000  # Starting account balance

# Master Brain Voting Rules
MIN_AGREEING_AGENTS = 4
CONFIDENCE_THRESHOLD = 65
AGENT5_BLOCK_ENABLED = True

# Self-Learning Engine
GENETIC_CYCLE_DAYS = 7
BACKTEST_DAYS = 180
PAPER_TRADING_DAYS = 7
MIN_PROFIT_FACTOR_FOR_PROMOTION = 1.2

# Database
DATABASE_PATH = "super_ai_trader.db"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "super_ai_trader.log"

# Trading Hours (UTC)
TRADING_SESSION_START = 0  # 00:00 UTC
TRADING_SESSION_END = 23  # 23:59 UTC

# News Filter (optional integration with economic calendar API)
NEWS_FILTER_ENABLED = False
NEWS_API_KEY = ""  # Economic calendar API key if using news filter
