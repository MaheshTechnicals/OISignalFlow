# 📁 OISignalFlow Project Files

## Repository Contents

### Main Application
- **OISignalFlow.py** — Core screener script that scans NSE stocks for OI buildup signals and sends alerts via Telegram

### Configuration Files
- **.env** — Environment variables for your Telegram credentials and scan parameters (do NOT commit to git)
- **.env.example** — Template file showing example configuration structure
- **.gitignore** — Git ignore rules to prevent committing sensitive files

### Documentation
- **README.md** — Project overview and description
- **requirements.txt** — Python package dependencies (install with: `pip install -r requirements.txt`)
- **FILES.md** — This file, documenting all files in the repository

### Data Output
- **OISignalFlow_Results.xlsx** — Generated Excel file with scan results (created after first run)

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your Telegram credentials
```

### 3. Run the Scanner
```bash
python OISignalFlow.py
```

## Configuration Variables

All variables are loaded from `.env` file:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| TELEGRAM_TOKEN | string | - | Bot token from @BotFather |
| TELEGRAM_CHAT_ID | string | - | Your Telegram chat ID |
| OI_CHANGE_MIN | float | 2.0 | Min OI change % to trigger alert |
| PRICE_CHANGE_MIN | float | 0.3 | Min price change % to trigger alert |
| VOLUME_MULT | float | 1.5 | Volume multiplier threshold |
| SCAN_INTERVAL | int | 5 | Scan frequency in minutes |
| OUTPUT_FILE | string | OISignalFlow_Results.xlsx | Excel output filename |
| LOG_LEVEL | string | INFO | Logging level (DEBUG/INFO/WARNING/ERROR) |
| ENABLE_DESKTOP_NOTIFICATIONS | bool | True | Desktop notification toggle |

## Dependencies

- **schedule** — Job scheduling
- **requests** — HTTP requests for Telegram API
- **pandas** — Data manipulation and Excel operations
- **python-dotenv** — Load .env configuration
- **nselib** — NSE India stock data
- **plyer** — Desktop notifications
- **openpyxl** — Excel file support

## Security

⚠️ **IMPORTANT:**
- Never commit `.env` file to git (already in .gitignore)
- Keep your TELEGRAM_TOKEN and TELEGRAM_CHAT_ID private
- Use `.env.example` as a template

## Output Files

After running, you'll get:
- **OISignalFlow_Results.xlsx** — Contains two sheets:
  - "All Stocks" — Complete scan results
  - "CE Buy Signals" — High probability CE call buy candidates
