# 🤖 Quick Start: Telegram Bot with Menu

## Yes! Your Telegram bot can give you a menu! 🎉

The Super AI Trader now includes a fully functional Telegram bot with an **interactive menu** that lets you control the entire trading system from your phone.

## 🚀 Setup in 3 Minutes

### Step 1: Get Your Bot Token (1 minute)

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Name it: `Super AI Trader`
4. Username: `super_ai_trading_bot` (must end with 'bot')
5. Copy the token (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Configure (30 seconds)

Edit `config.py`:
```python
TELEGRAM_BOT_TOKEN = "paste_your_token_here"
TELEGRAM_CHAT_ID = None  # or your chat ID for private messages
```

### Step 3: Run (10 seconds)

```bash
cd /workspace/super_ai_trader
python run.py
```

You'll see:
```
✅ Telegram Bot started - Use /menu for interactive commands
```

## 📱 Your Interactive Menu

In Telegram, type `/menu` and you'll get buttons for:

```
🎛️ Super AI Trader - Control Menu

[📊 System Status]  [📈 Recent Signals]
[▶️ Start Trading]  [⏹️ Stop Trading]
[💰 Account Balance] [🔄 Refresh Analysis]
[❓ Help]
```

## 🎯 What You Can Do

| Button | What It Does |
|--------|--------------|
| 📊 System Status | Shows if trading is active, balance, daily PnL, active agents |
| 📈 Recent Signals | Last 5 trading signals with entry, SL, TP |
| ▶️ Start Trading | Enables the AI to analyze and send signals |
| ⏹️ Stop Trading | Pauses all trading activity |
| 💰 Account Balance | Shows balance, risk per trade, daily limits |
| 🔄 Refresh Analysis | Runs immediate analysis on all symbols |
| ❓ Help | Full command reference |

## 🔔 Automatic Signal Notifications

When the AI finds a trade, you get:

```
🟢 NEW SIGNAL 🟢

📊 Symbol: EURUSD
📈 Direction: BUY

💰 Entry: 1.08500
🛑 Stop Loss: 1.08200
🎯 Take Profit: 1.09100

📊 Lots: 0.15
🎯 Confidence: 78%

📝 Reasons:
• Uptrend confirmed on H1
• Support level holding
• RSI showing bullish divergence

⏰ Time: 2024-01-15 14:30:00
📊 Votes: 4 BUY / 0 SELL
```

## 📋 All Commands

Type these directly in chat:

- `/start` - Welcome message
- `/menu` - Show interactive menu
- `/status` - System status
- `/signals` - Recent signals
- `/balance` - Account info
- `/start_trading` - Enable trading
- `/stop_trading` - Disable trading
- `/refresh` - Run analysis now
- `/help` - Help guide

## ✅ Tested & Working

The bot uses the official [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) library from GitHub and has been tested with:
- ✅ Interactive inline buttons
- ✅ Real-time signal notifications
- ✅ Multi-agent status updates
- ✅ Risk management reports
- ✅ Trading control commands

## 🔒 Security Tips

1. Never share your bot token publicly
2. Set `TELEGRAM_CHAT_ID` to restrict access to your chat only
3. The bot only sends signals - it doesn't execute trades automatically

---

**Need help?** Check `TELEGRAM_SETUP.md` for detailed instructions!
