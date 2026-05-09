# 🚀 Setup Guide — OISignalFlow

Complete setup instructions for the Python scanner and the live monitoring dashboard.

---

## Step 1 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install schedule requests pandas python-dotenv nselib plyer openpyxl
```

Requires **Python 3.7+**

---

## Step 2 — Get Telegram Credentials

### Bot Token
1. Open Telegram → search **@BotFather**
2. Send `/newbot` and follow prompts
3. Copy the **HTTP API token** → looks like: `123456:ABCDEFGabcdef`

### Chat ID
1. Search **@userinfobot** on Telegram
2. Send `/start`
3. Copy the **User ID** number

---

## Step 3 — Configure `.env`

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```ini
# ── Telegram (required) ──────────────────────────────
TELEGRAM_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh
TELEGRAM_CHAT_ID=123456789

# ── Scan Parameters ───────────────────────────────────
OI_CHANGE_MIN=2.0          # Alert when OI rises ≥ 2%
PRICE_CHANGE_MIN=0.3       # Alert when price rises ≥ 0.3%
VOLUME_MULT=1.5            # Alert when volume ≥ 1.5x normal
SCAN_INTERVAL=5            # Scan every 5 minutes

# ── Output ────────────────────────────────────────────
OUTPUT_FILE=OISignalFlow_Results.xlsx
LOG_LEVEL=INFO
ENABLE_DESKTOP_NOTIFICATIONS=True
```

### Tuning Tips

| Goal | Setting |
|------|---------|
| More alerts | Lower `OI_CHANGE_MIN` to 1.0 |
| Fewer alerts | Raise `OI_CHANGE_MIN` to 3.0+ |
| Higher quality signals | Raise `VOLUME_MULT` to 2.0 |
| Faster scanning | Keep `SCAN_INTERVAL=5` (one candle) |

---

## Step 4 — Run the Scanner

```bash
python OISignalFlow.py
```

Expected output:
```
╔══════════════════════════════════════════════╗
║        ⚡  O I S i g n a l F l o w          ║
╚══════════════════════════════════════════════╝

✅ OISignalFlow starting...
  📊 Stocks   : 209 FNO stocks (from API)
  ⏱ Interval  : Every 5 minutes
  📈 OI Min   : 2.0%
  📱 Telegram : Enabled

Testing Telegram connection...
✅ Telegram alert sent!
```

The scanner will:
- Scan all FNO stocks every 5 minutes (during market hours)
- Write `config.json` after every stock scan (live dashboard bridge)
- Save `OISignalFlow_Results.xlsx` after each full scan cycle
- Send Telegram alerts when CE signals are found

---

## Step 5 — Open the Live Dashboard

The dashboard requires **no installation** — it's pure HTML/CSS/JS.

### Option A — Direct file open

Double-click `index.html` in your file manager, or from terminal:
```bash
# macOS
open index.html

# Linux
xdg-open index.html

# Windows
start index.html
```

### Option B — Local HTTP server (recommended)

Some browsers block `fetch()` on `file://` URLs. Use this method if the dashboard shows "Connecting..." indefinitely:

```bash
# From the OISignalFlow directory
python3 -m http.server 8000
```

Then open: **http://localhost:8000**

> Keep this terminal running alongside `OISignalFlow.py`

---

## How the Dashboard Works

```
OISignalFlow.py  ──writes──▶  config.json  ◀──reads (every 2s)──  index.html
```

- The scanner writes `config.json` after every stock scanned and after every scan cycle
- The dashboard polls `config.json` every 2 seconds and updates all UI in real-time
- No WebSocket, no database, no backend — just file polling

---

## Dashboard Navigation

| Section | Shortcut | What it Shows |
|---------|----------|---------------|
| Overview | Click sidebar | KPIs, market info, scanner mini, latest signals |
| Live Signals | Click sidebar | All CE buy signal cards |
| Scanner | Click sidebar | Ring animation, progress bar, per-stock filter table |
| Statistics | Click sidebar | Breakdown chart, mood gauge, scan metrics |
| All Results | Click sidebar | Full sortable table with search and filter |
| Configuration | Click sidebar | All settings + system status |

**On mobile/tablet (≤900px):** tap the ☰ button in the top-left to open the sidebar.

**Keyboard:** `Alt+S` toggles sound on/off.

---

## Output Files

### `config.json`
Auto-generated runtime data file. Updated live by the scanner. Used exclusively by the dashboard. Do not edit manually.

### `OISignalFlow_Results.xlsx`
Updated after each complete scan cycle. Contains two sheets:

| Sheet | Contents |
|-------|---------|
| All Stocks | Every scanned stock with OI%, Price%, Volume Ratio, Signal |
| CE Buy Signals | Only stocks that passed all 4 CE filter criteria |

---

## Security Checklist

| Do | Don't |
|----|-------|
| Keep `.env` private | Commit `.env` to git |
| Use `.env.example` as template | Share your `TELEGRAM_TOKEN` |
| Add `.env` to `.gitignore` | Put secrets in `OISignalFlow.py` |

The `.gitignore` already excludes `.env` and `.xlsx` files.

---

## FNO Stocks Source

At startup, the scanner:
1. Fetches the full FNO stock list from: `https://nse-result-calendar.netlify.app/api/fno-list`
2. Falls back to 40 hardcoded major stocks if the API is unavailable
3. Displays the count at startup: `📊 Stocks : 209 FNO stocks (from API)`

No manual update of stock lists is needed.

---

## Environment Variables Reference

| Variable | Type | Example | Notes |
|----------|------|---------|-------|
| `TELEGRAM_TOKEN` | string | `123456:ABC...` | From @BotFather |
| `TELEGRAM_CHAT_ID` | string | `987654321` | Numbers only |
| `OI_CHANGE_MIN` | float | `2.0` | Lower = more alerts |
| `PRICE_CHANGE_MIN` | float | `0.3` | Lower = more alerts |
| `VOLUME_MULT` | float | `1.5` | Lower = more alerts |
| `SCAN_INTERVAL` | int | `5` | Minutes between scans |
| `OUTPUT_FILE` | string | `results.xlsx` | Any `.xlsx` filename |
| `LOG_LEVEL` | string | `INFO` | DEBUG/INFO/WARNING/ERROR |
| `ENABLE_DESKTOP_NOTIFICATIONS` | bool | `True` | Windows/macOS only |

---

## Troubleshooting

### Scanner Issues

| Error | Solution |
|-------|---------|
| `ModuleNotFoundError: No module named 'dotenv'` | `pip install python-dotenv` |
| `ModuleNotFoundError: No module named 'nselib'` | `pip install nselib` |
| Telegram: `Unauthorized` | Re-check `TELEGRAM_TOKEN` from @BotFather |
| Telegram: `Bad Request` | `TELEGRAM_CHAT_ID` must be numbers only, no quotes |
| No signals received | Lower thresholds in `.env`; check market hours 9:15–15:30 |

### Dashboard Issues

| Problem | Solution |
|---------|---------|
| Shows "Connecting..." forever | `OISignalFlow.py` is not running |
| No data updates | Verify `config.json` is being updated (check modification time) |
| Empty after direct file open | Use `python3 -m http.server 8000` instead |
| Sounds not working | Click anywhere on the page first; check 🔊 is not 🔇 |
| Layout looks broken | Hard-refresh with `Ctrl+Shift+R`; ensure all 3 files are in the same folder |

---

**Ready?** → `python OISignalFlow.py` + open `index.html` 🚀
