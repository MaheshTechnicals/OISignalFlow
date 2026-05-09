# 🚀 Quick Setup Guide for OISignalFlow

## Step 1: Install Dependencies

First, install all required Python packages:

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install schedule requests pandas python-dotenv nselib plyer openpyxl
```

## Step 2: Configure Your Credentials

### Get Telegram Bot Token
1. Open Telegram and search for **@BotFather**
2. Send `/start` and then `/newbot`
3. Follow the prompts to create a new bot
4. Copy the **HTTP API token** (format: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Get Your Chat ID
1. Search for **@userinfobot** on Telegram
2. Send `/start`
3. Copy your **User ID** number

### Setup .env File
```bash
cp .env.example .env
```

Edit `.env` and replace:
```ini
TELEGRAM_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh
TELEGRAM_CHAT_ID=123456789
```

## Step 3: Customize Scan Parameters (Optional)

In `.env`, adjust these to match your trading strategy:

```ini
# Alert when OI increases by at least 2%
OI_CHANGE_MIN=2.0

# Alert when price increases by at least 0.3%
PRICE_CHANGE_MIN=0.3

# Alert when volume is 1.5x higher than previous candle
VOLUME_MULT=1.5

# Scan every 5 minutes
SCAN_INTERVAL=5

# Output Excel file name
OUTPUT_FILE=OISignalFlow_Results.xlsx
```

## Step 4: Run OISignalFlow

```bash
python OISignalFlow.py
```

You should see:
- ✅ Telegram connection test passed
- 🚀 Scanner starting with your settings
- 📊 Live scan results every 5 minutes
- 💾 Excel file updated with results

## Telegram Alerts

You'll receive Telegram messages for:
- 🚀 **Startup** — Confirms scanner is running
- 🟢 **CE Buy Signals** — When stock meets all criteria
- 📊 **Market Summary** — Every 30 minutes with market mood
- 🔴 **Market Closed** — When NSE closes

## Output Files

After running, you'll see:
- **OISignalFlow_Results.xlsx** — Two sheets:
  - "All Stocks" — Complete scan results
  - "CE Buy Signals" — High probability trades

## Security Checklist

✅ **DO:**
- Keep your `.env` file private
- Never share your TELEGRAM_TOKEN
- Use `.env.example` as a template

❌ **DON'T:**
- Commit `.env` to git (already in .gitignore)
- Share your credentials in code
- Modify `.env.example` with real tokens

## Troubleshooting

### "ModuleNotFoundError: No module named 'dotenv'"
```bash
pip install python-dotenv
```

### "Telegram error: Unauthorized"
- Double-check your TELEGRAM_TOKEN in `.env`
- Verify it's from @BotFather, not @userinfobot

### "Telegram error: Bad Request"
- Verify TELEGRAM_CHAT_ID is correct (should be just numbers)
- Check for extra spaces in `.env` values

### No Alerts Received
1. Test your bot: Send a message to your bot on Telegram
2. Verify SCAN_INTERVAL doesn't prevent runs during market hours
3. Check OISignalFlow_Results.xlsx — do you have any CE signals?

## Environment Variables Reference

| Variable | Type | Range | Notes |
|----------|------|-------|-------|
| TELEGRAM_TOKEN | string | - | From @BotFather |
| TELEGRAM_CHAT_ID | string | - | Your user ID |
| OI_CHANGE_MIN | float | 0.1-10% | Lower = more alerts |
| PRICE_CHANGE_MIN | float | 0.1-5% | Lower = more alerts |
| VOLUME_MULT | float | 1.0-5.0 | Lower = more alerts |
| SCAN_INTERVAL | int | 1-60 min | Market hours: 9:15 AM - 3:30 PM |
| OUTPUT_FILE | string | .xlsx | Any Excel filename |
| LOG_LEVEL | string | DEBUG/INFO/WARNING/ERROR | For logging |
| ENABLE_DESKTOP_NOTIFICATIONS | bool | True/False | Windows/Mac only |

## Support

- **Issue?** Check your `.env` file first
- **Questions?** Refer to [nselib](https://github.com/spartan737/nselib) documentation
- **Telegram?** Visit [Telegram Bot API](https://core.telegram.org/bots/api)

---

**Happy Scanning!** 📈⚡
