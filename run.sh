#!/bin/bash

# 🚀 Stable Stock Analysis System - Setup & Run Script
# This script creates a virtual environment, installs dependencies, and runs the Telegram bot

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🤖 AI Trading Analysis System Setup      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_status "Found Python $PYTHON_VERSION"

# Check if venv already exists
if [ -d "$VENV_DIR" ]; then
    # Skip prompt in non-interactive mode or help command
    if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ] || [ ! -t 0 ]; then
        print_status "Using existing virtual environment"
    else
        print_warning "Virtual environment already exists at: $VENV_DIR"
        read -p "Do you want to recreate it? (y/n): " RECREATE
        if [[ "$RECREATE" =~ ^[Yy]$ ]]; then
            print_status "Removing old virtual environment..."
            rm -rf "$VENV_DIR"
        else
            print_status "Using existing virtual environment"
        fi
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    print_status "Virtual environment created at: $VENV_DIR"
else
    print_status "Virtual environment ready"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"
print_status "Virtual environment activated"

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1
print_status "Pip upgraded"

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    pip install -r "$PROJECT_DIR/requirements.txt" > /dev/null 2>&1
    print_status "Dependencies installed successfully"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Check for Telegram bot token (skip interactive prompt in non-interactive mode)
echo ""
echo -e "${YELLOW}Checking configuration...${NC}"

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    # Check if running in non-interactive mode or help command
    if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ] || [ ! -t 0 ]; then
        print_warning "TELEGRAM_BOT_TOKEN not set"
        echo ""
        print_warning "Set the token by running:"
        echo "  export TELEGRAM_BOT_TOKEN='your_token_here'"
        echo "Or create a .env file with: TELEGRAM_BOT_TOKEN=your_token_here"
    else
        # Interactive mode - ask for token
        print_warning "TELEGRAM_BOT_TOKEN environment variable is not set"
        echo ""
        echo "To get your bot token:"
        echo "1. Open Telegram and search for @BotFather"
        echo "2. Send /newbot and follow the instructions"
        echo "3. Copy the API token provided"
        echo ""
        
        read -p "Enter your Telegram Bot Token (or press Enter to skip and set manually later): " USER_TOKEN
        
        if [ -n "$USER_TOKEN" ]; then
            export TELEGRAM_BOT_TOKEN="$USER_TOKEN"
            print_status "Token set for this session"
            
            # Optionally save to .env file
            read -p "Save token to .env file for future use? (y/n): " SAVE_TOKEN
            if [[ "$SAVE_TOKEN" =~ ^[Yy]$ ]]; then
                echo "TELEGRAM_BOT_TOKEN=$USER_TOKEN" > "$PROJECT_DIR/.env"
                print_status "Token saved to .env file"
            fi
        else
            echo ""
            print_warning "You can set the token later by running:"
            echo "  export TELEGRAM_BOT_TOKEN='your_token_here'"
            echo "Or create a .env file with: TELEGRAM_BOT_TOKEN=your_token_here"
        fi
    fi
else
    print_status "TELEGRAM_BOT_TOKEN found in environment"
fi

# Load .env file if it exists
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
    print_status "Loaded configuration from .env file"
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Setup Complete! 🎉               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Show available commands
echo -e "${GREEN}Available Commands:${NC}"
echo "  1) Run Telegram Bot:     ./run.sh start"
echo "  2) Test Single Symbol:   ./run.sh test --symbol EURUSD --timeframe 1h"
echo "  3) Scan All Symbols:     ./run.sh scan"
echo "  4) Activate Venv Only:   ./run.sh shell"
echo ""

# Handle command line arguments
case "${1:-start}" in
    start|bot)
        echo -e "${YELLOW}Starting Telegram Bot...${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        python3 "$PROJECT_DIR/telegram_bot.py"
        ;;
    test|analyze)
        shift
        echo -e "${YELLOW}Running analysis...${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        python3 "$PROJECT_DIR/test_analysis.py" "$@"
        ;;
    scan|all)
        echo -e "${YELLOW}Scanning all symbols (this may take a while)...${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        python3 "$PROJECT_DIR/test_analysis.py" --mode all
        ;;
    shell|activate)
        echo -e "${GREEN}Virtual environment activated.${NC}"
        echo "Type 'deactivate' to exit."
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        bash
        ;;
    update|upgrade)
        echo -e "${YELLOW}Updating dependencies...${NC}"
        pip install -r "$PROJECT_DIR/requirements.txt" --upgrade
        print_status "Dependencies updated"
        ;;
    clean)
        echo -e "${YELLOW}Cleaning up...${NC}"
        rm -rf "$PROJECT_DIR/__pycache__"
        rm -rf "$PROJECT_DIR/agents/__pycache__"
        rm -rf "$PROJECT_DIR/utils/__pycache__"
        rm -f "$PROJECT_DIR/signals.log"
        print_status "Cache files cleaned"
        ;;
    help|--help|-h)
        echo -e "${GREEN}Usage:${NC} ./run.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start, bot       - Start the Telegram bot (default)"
        echo "  test, analyze    - Test analysis on a symbol (pass additional args)"
        echo "  scan, all        - Scan all configured symbols"
        echo "  shell, activate  - Activate virtual environment only"
        echo "  update, upgrade  - Update Python dependencies"
        echo "  clean            - Remove cache files and logs"
        echo "  help, --help     - Show this help message"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use './run.sh help' to see available commands"
        exit 1
        ;;
esac
