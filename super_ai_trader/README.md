# Super AI Trader v2.0
## Self-Improving Multi-Agent Trading Brain

A sophisticated multi-agent AI trading system that fuses 22 expert trading modules, 50+ indicators, and a genetic self-learning engine. It analyzes multiple timeframes, generates high-confidence BUY/SELL signals, sends them via Telegram, and evolves its own strategies over time.

## 🚀 Features

### Core Architecture
- **5 Specialist AI Agents** - Each embodies a distinct trading discipline
- **Master Brain Orchestrator** - Aggregates votes and enforces thresholds
- **50+ Technical Indicators** - Comprehensive indicator library
- **Multi-Timeframe Analysis** - 1m, 5m, 1H, 4H data fusion
- **Genetic Self-Learning Engine** - Weekly strategy evolution
- **Risk Management** - Mechanical 1% risk per trade, daily loss limits

### The 5 Agents

| Agent | Name | Modules | Function |
|-------|------|---------|----------|
| Agent 1 | Trend & Structure | 1, 5, 8, 13, 17, 18 | Ichimoku, MTFA, Turtle Trading, CHoCH, EMA strategies |
| Agent 2 | Volume & Order Flow | 3, 4, 15, 16 | Absorption, Volume Profile, POC reactions |
| Agent 3 | Price Action / S&D | 2, 10, 14, 19 | Supply/Demand zones, Liquidity sweeps, Checkmark patterns |
| Agent 4 | Indicator Confluence | 6, 9, 11, 12, 21 | Fibonacci, Sessions, Oscillators, ADX filter |
| Agent 5 | Market Context | 20, 21, 22 | Safety filter, News check, Daily limits (VETO power) |

### Voting Rules
- **Minimum agreeing agents**: 4 out of 5
- **Confidence threshold**: ≥65%
- **Agent 5 block**: Enabled (can veto any trade)

## 📁 Project Structure

```
super_ai_trader/
├── config.py                 # Configuration settings
├── master_brain.py           # Core orchestrator
├── run.py                    # Main entry point
├── telegram_bot.py           # Telegram interface with interactive menu ✅
├── self_learning.py          # Genetic algorithm engine (TODO)
├── agents/
│   ├── base_agent.py         # Abstract base class
│   ├── agent1_trend_structure.py
│   ├── agent2_volume_orderflow.py
│   ├── agent3_price_action_sd.py
│   ├── agent4_indicator_confluence.py
│   └── agent5_market_context.py
├── indicators/
│   └── indicator_library.py  # 50+ technical indicators
├── data/
│   └── market_data.py        # MT5 data fetcher
├── utils/
│   ├── formatter.py          # Telegram signal formatter
│   └── risk_manager.py       # Position sizing, SL/TP
├── backtesting/
│   └── backtest_engine.py    # Strategy evaluation (TODO)
├── requirements.txt
└── README.md
```

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- MetaTrader 5 (optional, for live trading)
- Telegram Bot Token (for signal notifications)

### Setup Steps

1. **Clone the repository**
```bash
cd /workspace/super_ai_trader
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure settings**
Edit `config.py` with your settings:
```python
TELEGRAM_BOT_TOKEN = "your_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"
MT5_LOGIN = 12345678
MT5_PASSWORD = "your_password"
MT5_SERVER = "YourBroker-Server"
ACCOUNT_BALANCE = 10000
```

4. **Run the system**
```bash
python run.py
```

## 📊 Usage

### Running in Demo Mode
The system will automatically run in demo mode if MT5 connection fails, generating synthetic data for testing.

### Telegram Commands
- `/start` - Welcome message and bot introduction
- `/menu` - Show interactive control menu with buttons 🎛️
- `/status` - Get system status and metrics
- `/signals` - View recent trading signals
- `/balance` - View account balance and risk report
- `/start_trading` - Enable trading system
- `/stop_trading` - Disable trading system
- `/refresh` - Trigger immediate market analysis
- `/help` - Show help message

### Signal Format
Signals are sent to Telegram in this format:
```
╔═══════════════════════════════╗
║ ⚡️ Super AI Trader SIGNAL ║
╚═══════════════════════════════╝

📍 EURUSD • 1.08750
🕐 2025-01-15 14:30:00 UTC

🟢 ⬆️ BUY | 78% | 🟩🟩🟩🟩🟩🟩🟩🟩⬛⬛

━━━━━━━━━━━━━━━━━━━━━━━
📊 ENTRY: 1.08750
🛑 SL: 1.08530
🎯 TP: 1.09190
💰 Size: 0.45 lots

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 REASONS:
• Ichimoku: Price above cloud (+2)
• EMA200: Price above (+1)
• Golden Cross detected (+2)
...
```

## 🔧 Configuration

### Risk Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| RISK_PER_TRADE | 1% | Account risk per trade |
| MAX_DAILY_DRAWDOWN | 3% | Maximum daily loss limit |
| ATR_MULTIPLIER_SL | 1.5 | Stop loss distance (ATR multiples) |
| ATR_MULTIPLIER_TP | 3.0 | Take profit distance (ATR multiples) |

### Voting Thresholds
| Parameter | Default | Description |
|-----------|---------|-------------|
| MIN_AGREEING_AGENTS | 4 | Minimum agents that must agree |
| CONFIDENCE_THRESHOLD | 65% | Minimum confidence percentage |
| AGENT5_BLOCK_ENABLED | True | Allow Agent 5 to veto trades |

## 🧬 Self-Learning Engine (Planned)

The genetic algorithm runs weekly:
1. **Candidate Generation** - Create new strategy combinations
2. **Backtesting** - Test on 180 days of historical data
3. **Selection** - Keep top 5 by fitness score
4. **Paper Trading** - Forward-test for 1 week
5. **Promotion** - Replace weakest agent if PF > 1.2x average

## 📝 Logging

All activity is logged to `super_ai_trader.log`:
- Signal generation events
- Agent decisions and scores
- Risk management checks
- System errors and warnings

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading financial instruments involves substantial risk of loss. Past performance does not guarantee future results. Always test thoroughly on a demo account before live trading.

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

---

**Built with ❤️ by the Super AI Trader Team**
