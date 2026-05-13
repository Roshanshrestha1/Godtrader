#!/bin/bash

# ==========================================
# 🚀 AI Trading Bot - Complete Startup Script
# ==========================================
# This script:
# 1. Creates virtual environment if needed
# 2. Installs dependencies (using system packages if venv fails)
# 3. Asks for Telegram bot token
# 4. Starts the market scanner in background
# 5. Starts the Telegram bot in foreground
# ==========================================

echo "╔═══════════════════════════════════════════╗"
echo "║   🤖 AI TRADING SYSTEM STARTUP            ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# Navigate to workspace (use absolute path from script location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Create necessary directories early
mkdir -p logs cache

# 1. Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed."
    exit 1
fi
echo "✅ Python 3 found: $(python3 --version)"

# 2. Setup Python environment
# Try venv first, fall back to system packages if disk space is low
VENV_SUCCESS=false
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    if python3 -m venv venv 2>/dev/null; then
        VENV_SUCCESS=true
        echo "✅ Virtual environment created."
    else
        echo "⚠️  Could not create venv (likely disk space issue)."
        echo "   Using system Python packages instead."
    fi
else
    echo "✅ Virtual environment already exists."
    VENV_SUCCESS=true
fi

# 3. Activate Virtual Environment or use system
if [ "$VENV_SUCCESS" = true ]; then
    source venv/bin/activate
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
    echo "✅ Using system Python environment."
fi

# 4. Install Dependencies
echo ""
echo "📥 Installing/Updating dependencies..."
$PIP_CMD install -q --upgrade pip 2>/dev/null || true

# Install required packages
$PIP_CMD install -q python-telegram-bot yfinance pandas numpy pyyaml aiohttp python-dotenv requests 2>&1 | grep -v "WARNING\|notice" || true

echo "✅ Dependencies installed."

# 5. Handle Bot Token
if [ ! -f ".env" ]; then
    echo ""
    echo "╔═══════════════════════════════════════════╗"
    echo "║   🔑 TELEGRAM BOT TOKEN SETUP             ║"
    echo "╚═══════════════════════════════════════════╝"
    echo ""
    echo "Please enter your Telegram Bot Token."
    echo "Get it from @BotFather on Telegram"
    echo ""
    read -p "Token: " BOT_TOKEN
    
    # Validate basic format (starts with digits:)
    if [[ ! "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
        echo "⚠️  Warning: Token format looks unusual, but proceeding..."
    fi

    # Create .env file
    cat > .env <<EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
LOG_LEVEL=INFO
EOF
    echo ""
    echo "✅ Token saved to .env file."
else
    echo "✅ .env file already exists. Using stored token."
fi

# 6. Create necessary directories (already done above, but ensure they exist)
mkdir -p logs cache
chmod 755 logs cache

# 7. Start Market Scanner in Background
echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║   📡 STARTING MARKET SCANNER (Background) ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# Kill any existing scanner process
pkill -f "python.*market_scanner.py" 2>/dev/null || true

# Start scanner in background with nohup
nohup $PYTHON_CMD market_scanner.py > logs/scanner_output.log 2>&1 &
SCANNER_PID=$!

echo "✅ Market Scanner started (PID: $SCANNER_PID)"
echo "   - Scanning all 108 Exness assets"
echo "   - Updates every 5 minutes"
echo "   - Logs: logs/scanner.log"
echo ""

# Wait a moment for initial scan to start
sleep 2

# 8. Start Telegram Bot in Foreground
echo "╔═══════════════════════════════════════════╗"
echo "║   💬 STARTING TELEGRAM BOT (Foreground)   ║"
echo "╚═══════════════════════════════════════════╝"
echo ""
echo "🚀 System Ready!"
echo ""
echo "   ✅ Market Scanner: Running (PID: $SCANNER_PID)"
echo "   ✅ Telegram Bot: Starting..."
echo ""
echo "💡 Commands:"
echo "   - Press Ctrl+C to stop the bot"
echo "   - Scanner will continue running in background"
echo "   - To stop scanner: kill $SCANNER_PID"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run the Telegram bot
$PYTHON_CMD telegram_bot.py
