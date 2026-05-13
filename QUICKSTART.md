# 🚀 Quick Start Guide

## One-Command Setup & Run

```bash
./run.sh
```

This script will:
1. ✅ Create a Python virtual environment (`venv/`)
2. ✅ Install all required dependencies
3. ✅ Prompt you for your Telegram Bot Token (optional)
4. ✅ Start the Telegram bot

---

## 📋 Available Commands

| Command | Description |
|---------|-------------|
| `./run.sh` or `./run.sh start` | Start the Telegram bot (default) |
| `./run.sh test --symbol EURUSD --timeframe 1h` | Test analysis on a single symbol |
| `./run.sh scan` | Scan all 108 Exness symbols |
| `./run.sh shell` | Activate virtual environment only |
| `./run.sh update` | Update Python dependencies |
| `./run.sh clean` | Remove cache files and logs |
| `./run.sh help` | Show all available commands |

---

## 🔧 Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Telegram Bot Token
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

Or create a `.env` file:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 4. Run the Bot
```bash
python telegram_bot.py
```

---

## 🤖 Getting Your Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow the instructions to name your bot
4. Copy the API token provided (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Set it as environment variable or in `.env` file

---

## 🧪 Testing

### Test a Single Symbol
```bash
./run.sh test --symbol EURUSD --timeframe 1h
./run.sh test --symbol BTCUSD --timeframe 1h
./run.sh test --symbol XAUUSD --timeframe 4h
```

### Scan All Symbols
```bash
./run.sh scan
```
*Note: This may take several minutes as it analyzes all 108 symbols.*

---

## 📁 Project Structure

```
/workspace/
├── run.sh                 # Main setup & run script
├── config.py              # Configuration loader
├── config.yaml            # All settings & 108 Exness symbols
├── telegram_bot.py        # Telegram bot with interactive menu
├── master_brain.py        # AI Master Brain (5 agents)
├── test_analysis.py       # CLI testing tool
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── venv/                  # Virtual environment (created by run.sh)
├── agents/                # 5 AI agents
│   ├── trend_agent.py
│   ├── volume_agent.py
│   ├── price_action_agent.py
│   ├── indicator_agent.py
│   └── context_agent.py
└── utils/
    ├── data_fetcher.py    # Yahoo Finance API wrapper
    ├── indicators.py      # Technical indicators
    └── formatter.py       # Message formatting
```

---

## ⚠️ Important Notes

- **Virtual Environment**: The script creates a `venv/` directory to isolate dependencies
- **Token Security**: Never commit your `.env` file to Git (it's in `.gitignore`)
- **First Run**: The first run may take longer as it downloads dependencies
- **Data Caching**: Recent data is cached to avoid excessive API calls

---

## 🐛 Troubleshooting

### "Permission denied" when running ./run.sh
```bash
chmod +x run.sh
```

### "Python not found"
Install Python 3.8+ from https://www.python.org/downloads/

### "Module not found"
```bash
./run.sh update
```

### "Invalid bot token"
Double-check your token from @BotFather and ensure no extra spaces

---

## 📞 Support

For issues or questions, check:
- `README.md` - Full documentation
- `signals.log` - Runtime logs for debugging
