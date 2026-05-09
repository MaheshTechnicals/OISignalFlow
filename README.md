# ⚡ OISignalFlow — Free OI Screener for NSE Options

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.7%2B-brightgreen)
![License](https://img.shields.io/badge/license-free%20to%20use-green)

> **Free, automated Open Interest screener for NSE FNO stocks.** Scans for CE call buying opportunities using real-time OI + Price + Volume analysis. Sends alerts via Telegram every 5 minutes.

## 🎯 What is OISignalFlow?

OISignalFlow is an intelligent options screener that detects **long buildup signals** in NSE FNO stocks:

- 📊 **Real-time Analysis** — Scans 40 FNO stocks every 5 minutes
- 🟢 **CE Buy Signals** — Identifies high-probability call buying opportunities  
- 📈 **OI Buildup Detection** — Combines OI + Price + Volume analysis
- 📱 **Telegram Alerts** — Get instant notifications on your phone
- 💾 **Excel Export** — All results saved automatically
- 🎨 **Zero Cost** — Free NSE data (no paid APIs)

### Signal Types

| Signal | Meaning | Action |
|--------|---------|--------|
| 🟢 **LONG BUILDUP** | Price ↑ + OI ↑ | ✅ **BUY CE** (Best) |
| 🔴 **SHORT BUILDUP** | Price ↓ + OI ↑ | ⚠️ Consider PE |
| 🟡 **SHORT COVERING** | Price ↑ + OI ↓ | ⚠️ Weak signal |
| ⚪ **LONG UNWINDING** | Price ↓ + OI ↓ | ❌ Avoid |

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Telegram account (for alerts)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Telegram Credentials
- **Telegram Token** → Chat with [@BotFather](https://t.me/BotFather) → `/newbot`
- **Chat ID** → Chat with [@userinfobot](https://t.me/userinfobot) → `/start`

### 3. Configure `.env`
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```ini
TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=987654321

# Optional: Adjust scan parameters
OI_CHANGE_MIN=2.0
PRICE_CHANGE_MIN=0.3
VOLUME_MULT=1.5
SCAN_INTERVAL=5
```

### 4. Run the Scanner
```bash
python OISignalFlow.py
```

You'll see:
```
✅ OISignalFlow starting...
📁 Config   : .env
📊 Stocks   : 40 FNO stocks
⏱ Interval  : Every 5 minutes
📈 OI Min   : 2.0%
💾 Excel    : OISignalFlow_Results.xlsx
📱 Telegram : Enabled

Testing Telegram connection...
✅ Telegram alert sent!
```

## 📋 Configuration

All settings are managed via `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_TOKEN` | - | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | - | Your Telegram user ID |
| `OI_CHANGE_MIN` | 2.0 | Min OI change % for alert |
| `PRICE_CHANGE_MIN` | 0.3 | Min price change % for alert |
| `VOLUME_MULT` | 1.5 | Volume must be X times normal |
| `SCAN_INTERVAL` | 5 | Scan frequency (minutes) |
| `OUTPUT_FILE` | OISignalFlow_Results.xlsx | Excel output filename |
| `LOG_LEVEL` | INFO | Logging level (DEBUG/INFO/WARNING) |
| `ENABLE_DESKTOP_NOTIFICATIONS` | True | Desktop notifications on/off |

**Example:** Sensitive? Want more alerts?
```ini
OI_CHANGE_MIN=1.0        # Alert at 1% OI change (more alerts)
VOLUME_MULT=1.0          # Alert even at normal volume
PRICE_CHANGE_MIN=0.1     # Very sensitive to price moves
```

## 📱 Telegram Alerts

You'll receive automated messages:

### 🚀 Startup Alert
Sent once when scanner starts:
```
🚀 OISignalFlow is LIVE!
━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date      : 09-05-2026
🕐 Started   : 09:15:00
📊 Watching  : 40 FNO Stocks
⏰ Interval  : Every 5 minutes
[...]
```

### 🟢 CE Buy Signal Alert
When a stock meets all criteria:
```
🟢 OISignalFlow — CE BUY ALERT!
━━━━━━━━━━━━━━━━━━━━━━━━━
🕐 Time   : 09-05-2026 09:20
🔍 Scan # : 1
📊 Found  : 2 stock(s)
━━━━━━━━━━━━━━━━━━━━━━━━━

1. RELIANCE
   💰 Price     : ₹2850.50  (+1.25%)
   📈 OI Change : +3.45%
   📊 Volume    : 2.1x normal
   🔰 Signal    : 🟢 LONG BUILDUP
   ⚡ Strength  : 🔥 STRONG
   🎯 Action    : BUY ATM CE
   🛑 Stop Loss : Below VWAP
```

### 📊 Market Summary
Every 30 minutes with market sentiment:
```
📊 OISignalFlow — Market Summary
━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 Long Buildup  : 8 stocks
🔴 Short Buildup : 3 stocks
🌡 Market Mood   : 🟢 BULLISH
```

## 📊 Stocks Monitored

40 major FNO stocks across sectors:

**Banking:** HDFCBANK, ICICIBANK, SBIN, INDUSINDBK
**IT:** TCS, INFY, WIPRO, HCLTECH, TECHM
**Pharma:** SUNPHARMA, DRREDDY, CIPLA, DIVISLAB
**Auto:** TATAMOTORS, MARUTI, HEROMOTOCO, M&M
**Energy:** ONGC, BPCL, COALINDIA
**Infra & Others:** RELIANCE, POWERGRID, NTPC, LT, LTIM, JSWSTEEL, ULTRACEMCO, etc.

See `OISignalFlow.py` for complete list.

## 📁 Project Structure

```
OISignalFlow/
├── OISignalFlow.py              # Main scanner script
├── requirements.txt             # Python dependencies
├── .env                         # Your config (NEVER commit!)
├── .env.example                 # Config template
├── .gitignore                   # Git ignore rules
├── README.md                    # This file
├── SETUP.md                     # Detailed setup guide
├── FILES.md                     # File documentation
└── OISignalFlow_Results.xlsx    # Auto-generated results
```

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `schedule` | Job scheduling |
| `requests` | Telegram API calls |
| `pandas` | Data analysis & Excel |
| `python-dotenv` | Load .env config |
| `nselib` | NSE India data fetcher |
| `plyer` | Desktop notifications |
| `openpyxl` | Excel file support |

Install all with:
```bash
pip install -r requirements.txt
```

## 🎯 How It Works

### Scan Process (Every 5 Minutes)

1. **Fetch Data** → Get latest OI, Price, Volume from NSE for 40 stocks
2. **Calculate Changes** → Compare with previous candle
   - OI Change % = (Current OI - Previous OI) / Previous OI × 100
   - Price Change % = (Current Price - Previous Price) / Previous Price × 100
   - Volume Ratio = Current Volume / Previous Volume
3. **Classify Signal** → Determine signal type
4. **Filter Candidates** → Check if meets all criteria:
   - Signal = "LONG BUILDUP" ✅
   - OI Change ≥ 2.0% ✅
   - Price Change ≥ 0.3% ✅
   - Volume ≥ 1.5x normal ✅
5. **Alert** → Send Telegram & Excel update
6. **Wait** → Resume in 5 minutes

### Signal Strength Rating

| Condition | Rating |
|-----------|--------|
| OI ≥ 5% AND Volume ≥ 3x | 🔥🔥 VERY STRONG |
| OI ≥ 3% AND Volume ≥ 2x | 🔥 STRONG |
| Otherwise | ✅ MODERATE |

## 💾 Output Files

### OISignalFlow_Results.xlsx

Auto-generated Excel file with:

**Sheet 1: All Stocks** — Complete scan results
| Symbol | Price | Price_Chg% | OI_Chg% | Vol_Ratio | Signal |
|--------|-------|-----------|---------|-----------|--------|
| RELIANCE | 2850.50 | +1.25 | +3.45 | 2.1 | 🟢 LONG BUILDUP |
| TCS | 4125.00 | -0.85 | +1.50 | 0.8 | 🔴 SHORT BUILDUP |

**Sheet 2: CE Buy Signals** — High probability trades only

## 🔒 Security

**Important:**
- ⚠️ `.env` file is in `.gitignore` — never committed
- ⚠️ Never share your TELEGRAM_TOKEN
- ⚠️ Use `.env.example` as template
- ⚠️ Keep credentials private

## ⏰ Market Hours

Scanner runs only during NSE trading hours:
- **Start:** 9:15 AM IST
- **End:** 3:30 PM IST
- **Holidays:** Skips weekends & market holidays
- **Interval:** Every 5 minutes (default)

Outside market hours, scanner waits silently.

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'dotenv'"
```bash
pip install python-dotenv
```

### Issue: "Telegram error: Unauthorized"
- Check TELEGRAM_TOKEN is correct (from @BotFather)
- Verify no extra spaces in `.env`

### Issue: "Telegram error: Bad Request"  
- Verify TELEGRAM_CHAT_ID is correct (just numbers)
- Check for quotes around values in `.env`

### Issue: No alerts even during market hours
1. Check `OISignalFlow_Results.xlsx` — any CE signals?
2. Verify settings in `.env` (too strict filters?)
3. Check market hours: 9:15 AM - 3:30 PM IST only
4. Adjust `OI_CHANGE_MIN` to lower value

### Issue: Too many alerts
Adjust `.env` settings:
```ini
OI_CHANGE_MIN=3.0        # Increase to reduce alerts
VOLUME_MULT=2.0          # Higher volume requirement
```

## 📚 Learn More

- **NSE Data:** [nselib Documentation](https://github.com/spartan737/nselib)
- **Telegram Bot:** [Telegram Bot API](https://core.telegram.org/bots/api)
- **Options Trading:** [NSE Options Guide](https://www.nseindia.com/)
- **Setup Guide:** See [SETUP.md](SETUP.md)
- **File Reference:** See [FILES.md](FILES.md)

## ⚡ Pro Tips

1. **Start Conservative** — Begin with default settings, adjust after 2-3 days
2. **Monitor Telegram** — Alerts show signal strength; focus on "VERY STRONG" (🔥🔥)
3. **Cross-verify** — Check VWAP on your chart before entry
4. **Peak Hours** — Best signals usually 9:30-11:30 AM IST
5. **Excel Review** — Check `OISignalFlow_Results.xlsx` daily for patterns

## ⚠️ Disclaimer

**OISignalFlow is for education only.** Not financial advice.

- Past performance ≠ future results
- OI buildup doesn't guarantee profit
- Always verify signals on charts
- Risk management is YOUR responsibility
- Trade with proper stop losses

## 📝 License

Free to use and modify. No restrictions.

## 🎉 Credits

Built with ❤️ for NSE options traders.

---

**Questions?** Check [SETUP.md](SETUP.md) or [FILES.md](FILES.md)

**Ready?** Run `python OISignalFlow.py` and start receiving alerts! 🚀