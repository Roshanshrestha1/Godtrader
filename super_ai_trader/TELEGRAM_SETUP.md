# Super AI Trader - Telegram Bot Setup Guide

## 🤖 Setting Up Your Telegram Bot

### Step 1: Create a Bot with @BotFather

1. Open Telegram and search for `@BotFather`
2. Start a chat with @BotFather
3. Send the command `/newbot`
4. Follow the prompts:
   - Choose a name for your bot (e.g., "Super AI Trader")
   - Choose a username for your bot (must end in 'bot', e.g., "super_ai_trader_bot")
5. @BotFather will give you a **BOT TOKEN** (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
6. **Save this token securely!**

### Step 2: Get Your Chat ID (Optional)

If you want to receive signals only on your personal chat:

1. Search for `@userinfobot` on Telegram
2. Start the bot and it will show you your **Chat ID** (a number like: `123456789`)
3. Alternatively, send a message to your bot, then visit:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   Look for `"chat":{"id":123456789}` in the response

### Step 3: Configure Your Bot

Edit the `config.py` file:

```python
# Replace with your actual bot token from @BotFather
TELEGRAM_BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"

# Optional: Set to your chat ID to receive signals privately
# Leave as None to broadcast to all chats that interact with the bot
TELEGRAM_CHAT_ID = 123456789  # or None
```

### Step 4: Start Your Bot

Run the trading system:

```bash
cd /workspace/super_ai_trader
python run.py
```

You should see:
```
✅ Telegram Bot started - Use /menu for interactive commands
```

### Step 5: Interact with Your Bot

1. Open Telegram and find your bot
2. Start a chat with your bot
3. Type `/start` to begin
4. Type `/menu` to see all available commands

## 📱 Available Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/menu` | Show interactive control menu |
| `/status` | View system status |
| `/signals` | View recent trading signals |
| `/balance` | Check account balance |
| `/start_trading` | Enable trading |
| `/stop_trading` | Disable trading |
| `/refresh` | Trigger immediate market analysis |
| `/help` | Show help guide |

## 🎛️ Interactive Menu Features

The `/menu` command provides buttons for:
- 📊 System Status - Real-time system metrics
- 📈 Recent Signals - Last 5 trading signals
- ▶️ Start Trading - Enable the trading system
- ⏹️ Stop Trading - Pause the trading system
- 💰 Account Balance - View balance and risk metrics
- 🔄 Refresh Analysis - Run immediate analysis
- ❓ Help - Detailed help guide

## 🔔 Signal Notifications

When the AI generates a trading signal, you'll receive:

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

## 🔒 Security Tips

1. **Never share your bot token** publicly
2. Store your token in environment variables for production
3. Use `TELEGRAM_CHAT_ID` to restrict access to your personal chat
4. Regularly rotate your bot token if needed via @BotFather

## 🛠️ Troubleshooting

### Bot doesn't start
- Check if the token is correct
- Ensure `python-telegram-bot` is installed: `pip install python-telegram-bot`

### Not receiving signals
- Make sure you've started a chat with the bot
- Check if `TELEGRAM_BOT_TOKEN` is configured correctly
- Verify the bot is running (check logs)

### Menu buttons not working
- Update to latest version of `python-telegram-bot`
- Restart the bot after configuration changes

## 📦 Installation

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

The key package for Telegram is:
```
python-telegram-bot>=20.0
```

This uses the official [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) library from GitHub.
