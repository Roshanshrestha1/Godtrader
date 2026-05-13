# 🚀 AI Trading System - Setup & Usage Guide

## ✅ What's Been Implemented

### 🔧 Architecture Changes (Solves Slow Response Issue)

**BEFORE:** Telegram bot scanned all 108 assets on every user request → **2-3 minute delays**

**AFTER:** 
- **Market Scanner** runs independently in background, scanning all assets every 5 minutes
- **Telegram Bot** reads from cache → **Instant responses (<1 second)**
- Complete separation of concerns

```
┌─────────────────────┐         ┌──────────────────────┐
│  Market Scanner     │         │   Telegram Bot       │
│  (Background)       │         │   (Foreground)       │
│                     │         │                      │
│  • Scans 108 assets │────┐    │  • Listens to user   │
│  • Every 5 min      │    │    │  • Reads cache       │
│  • Saves to cache   │    ▼    │  • Responds instantly│
│                     │  ┌─────┐│                      │
│                     │  │CACHE││                      │
│                     │  └─────┘│                      │
└─────────────────────┘         └──────────────────────┘
```

---

## 📁 New Files Created

| File | Purpose |
|------|---------|
| `start.sh` | **One-command startup** - Creates venv, asks for token, starts both services |
| `market_scanner.py` | Background scanner that analyzes all 108 Exness assets |
| `cache/best_trades.json` | Cached scan results (auto-created) |
| `logs/scanner.log` | Scanner activity logs |

---

## 🚀 Quick Start (Recommended)

### Option 1: Use the Startup Script (Easiest)

```bash
cd /workspace
./start.sh
```

This script will:
1. ✅ Create virtual environment (if needed)
2. ✅ Install all dependencies
3. ✅ **Ask you for Telegram Bot Token** (interactive prompt)
4. ✅ Save token to `.env` file
5. ✅ Start market scanner in background
6. ✅ Start Telegram bot in foreground

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your bot token
export TELEGRAM_BOT_TOKEN="your_token_here"

# 4. Start market scanner (in background)
nohup python3 market_scanner.py > logs/scanner_output.log 2>&1 &

# 5. Start Telegram bot (in foreground)
python3 telegram_bot.py
```

---

## 🔑 Getting Your Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow instructions:
   - Choose a name (e.g., "AI Trading Assistant")
   - Choose a username (e.g., "my_ai_trader_bot")
4. Copy the token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Paste it when the `start.sh` script asks

---

## 📊 How It Works

### Market Scanner (Background Service)

- **Runs continuously** in background
- **Scans all 108 Exness assets** every 5 minutes:
  - Forex Majors/Minors/Exotics (36 pairs)
  - Cryptocurrencies (25 coins)
  - Metals (XAU, XAG, XPT, XPD)
  - Energies (Oil, Gas)
  - Indices (US30, NAS100, GER40, etc.)
  - US Stocks (30 major companies)
- **Analyzes each symbol** with 5 AI agents + 22+ indicators
- **Filters** for high-confidence trades (4+ agents agree, >65% confidence)
- **Ranks** by score and saves top 10 to cache
- **Logs** all activity to `/workspace/logs/scanner.log`

### Telegram Bot (User Interface)

- **Instant response** using cached data
- When user clicks "🔍 Find Best Trades":
  1. Reads cache file (instant)
  2. Checks if data is fresh (<10 min old)
  3. Displays top 3 trades with full analysis
  4. Shows last scan timestamp
- **No waiting** for market analysis!

---

## 🎯 Features

### Main Menu
```
🔍 Find Best Trades by AI
⚙️ Trading Settings
```

### Find Best Trades
- Shows **TOP 3** highest-confidence trades
- Each card includes:
  - 📍 Symbol & Entry price
  - 🟢 CALL / 🔴 PUT direction
  - 📊 Confidence bar & percentage
  - 🛑 Stop Loss & 🎯 Take Profit
  - 💰 Risk:Reward ratio
  - 📋 Agent reasons summary
- Shows **last scan timestamp**

### Trading Settings
1. **Select Asset Group** (Forex, Crypto, Metals, etc.)
2. **Choose Specific Symbol** (EURUSD, BTCUSD, etc.)
3. **Pick Timeframe** (1m, 5m, 15m, 1h, 4h, Daily)
4. **Get Full Analysis** with all 5 agent votes

---

## 📈 Monitoring

### Check Scanner Status
```bash
# View scanner logs
tail -f /workspace/logs/scanner.log

# Check if scanner is running
ps aux | grep market_scanner

# View cache file
cat /workspace/cache/best_trades.json | jq
```

### Cache File Structure
```json
{
  "timestamp": "2025-01-15T14:30:00",
  "top_trades": [
    {
      "exness_symbol": "EURUSD",
      "yahoo_ticker": "EURUSD=X",
      "signal": "BUY",
      "confidence": 87,
      "agents_agreeing": 5,
      "entry": 1.0850,
      "sl": 1.0820,
      "tp": 1.0910,
      "score": 87.0
    }
  ],
  "total_symbols_scanned": 108,
  "scan_duration_seconds": 145.3
}
```

---

## 🛠️ Troubleshooting

### Problem: "No recent scan data available"
**Solution:** Wait 2-3 minutes for first scan to complete, or check:
```bash
# Check if scanner is running
ps aux | grep market_scanner

# Check scanner logs
tail -n 50 /workspace/logs/scanner.log

# Restart scanner
pkill -f market_scanner
nohup python3 market_scanner.py > logs/scanner_output.log 2>&1 &
```

### Problem: Bot not responding
**Solution:**
1. Check if bot is running
2. Verify token in `.env` file
3. Check bot logs: `tail -f signals.log`

### Problem: API rate limits
**Solution:** The scanner already has built-in rate limiting (0.5s between symbols). If issues persist, increase delay in `market_scanner.py`:
```python
await asyncio.sleep(1.0)  # Increase from 0.5 to 1.0
```

---

## ⚙️ Configuration

### Adjust Scan Frequency
Edit `market_scanner.py`:
```python
SCAN_INTERVAL_MINUTES = 5  # Change to 10 for less frequent scans
```

### Change Number of Cached Trades
Edit `market_scanner.py`:
```python
top_trades = all_signals[:10]  # Change 10 to cache more
```

### Modify Confidence Thresholds
Edit `config.yaml`:
```yaml
master_brain:
  min_agents_agree: 4
  min_confidence: 65
```

---

## 📝 Commands Reference

```bash
# Start everything (recommended)
./start.sh

# Start only scanner
python3 market_scanner.py

# Start only bot (scanner must be running separately)
python3 telegram_bot.py

# Stop scanner
pkill -f market_scanner

# Check processes
ps aux | grep python

# View real-time logs
tail -f logs/scanner.log
tail -f signals.log
```

---

## 🎯 Performance Metrics

| Metric | Before | After |
|--------|--------|-------|
| Response time | 2-3 min | <1 sec |
| User experience | Poor | Excellent |
| Market coverage | On-demand | Continuous |
| Data freshness | Variable | <5 min |
| System load | Spiky | Steady |

---

## ⚠️ Important Notes

1. **Always run the scanner** before using the bot
2. **Cache expires after 10 minutes** - ensures fresh data
3. **First scan takes 2-3 minutes** - subsequent scans are faster
4. **Scanner uses rate limiting** to avoid API bans
5. **Both services can run on a cheap VPS** (1GB RAM sufficient)

---

## 🚀 Production Deployment

For 24/7 operation on a VPS:

```bash
# Use systemd service (create /etc/systemd/system/trading-scanner.service)
[Unit]
Description=AI Trading Market Scanner
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/workspace
ExecStart=/workspace/venv/bin/python3 market_scanner.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable trading-scanner
sudo systemctl start trading-scanner
sudo systemctl status trading-scanner
```

---

## 📞 Support

If you encounter issues:
1. Check logs in `/workspace/logs/`
2. Verify all dependencies: `pip list`
3. Test with CLI first: `python3 test_analysis.py --symbol EURUSD`
4. Ensure stable internet connection for API calls

---

**Happy Trading! 🚀📈**

*Remember: This is an analysis tool, not financial advice. Always verify signals manually.*
