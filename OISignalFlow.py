# ============================================================
#
#   ██████╗ ██╗    ███████╗██╗ ██████╗ ███╗   ██╗ █████╗ ██╗
#  ██╔═══██╗██║    ██╔════╝██║██╔════╝ ████╗  ██║██╔══██╗██║
#  ██║   ██║██║    ███████╗██║██║  ███╗██╔██╗ ██║███████║██║
#  ██║   ██║██║    ╚════██║██║██║   ██║██║╚██╗██║██╔══██║██║
#  ╚██████╔╝██║    ███████║██║╚██████╔╝██║ ╚████║██║  ██║███████╗
#   ╚═════╝ ╚═╝    ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝
#
#   ███████╗██╗      ██████╗ ██╗    ██╗
#   ██╔════╝██║     ██╔═══██╗██║    ██║
#   █████╗  ██║     ██║   ██║██║ █╗ ██║
#   ██╔══╝  ██║     ██║   ██║██║███╗██║
#   ██║     ███████╗╚██████╔╝╚███╔███╔╝
#   ╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝
#
#   Project   : OISignalFlow
#   Version   : v1.0.0
#   Purpose   : Free OI Screener for CE Call Buying
#   Data      : NSE India (Free — No paid API)
#   Alerts    : Telegram Bot
#   Interval  : Every 5 Minutes (Auto)
#   Author    : OISignalFlow
#   License   : Free to use
# ============================================================

import time
import json
import logging
import schedule
import requests
import pandas as pd
from datetime import datetime
from nselib import derivatives
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    from plyer import notification
    DESKTOP_NOTIFY = os.getenv('ENABLE_DESKTOP_NOTIFICATIONS', 'True').lower() == 'true'
except:
    DESKTOP_NOTIFY = False


# ============================================================
# 📝  FILE LOGGING  (Issue 5)
# Writes to OISignalFlow.log AND terminal simultaneously
# ============================================================

# Read LOG_LEVEL from .env BEFORE configuring logging so the setting takes effect
_log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(), logging.INFO)

logging.basicConfig(
    level=_log_level,
    format='%(asctime)s [OISignalFlow] %(levelname)s — %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S',
    handlers=[
        logging.FileHandler('OISignalFlow.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# Silence noisy third-party loggers
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)


# ============================================================
# ⚙️  CONFIGURATION — LOADED FROM .env FILE
# ============================================================

# Telegram Settings
TELEGRAM_TOKEN    = os.getenv('TELEGRAM_TOKEN', 'YOUR_BOT_TOKEN_HERE')
TELEGRAM_CHAT_ID  = os.getenv('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID_HERE')

# Scan Parameters
OI_CHANGE_MIN     = float(os.getenv('OI_CHANGE_MIN',    '2.0'))   # Min OI change %
PRICE_CHANGE_MIN  = float(os.getenv('PRICE_CHANGE_MIN', '0.3'))   # Min price change %
VOLUME_MULT       = float(os.getenv('VOLUME_MULT',      '1.5'))   # Volume multiplier
SCAN_INTERVAL     = int(os.getenv('SCAN_INTERVAL',      '5'))     # Scan interval (minutes)
OUTPUT_FILE       = os.getenv('OUTPUT_FILE', 'OISignalFlow_Results.xlsx')

# Rate Limiting  (Issue 3)
REQUEST_DELAY     = float(os.getenv('REQUEST_DELAY', '0.3'))      # Seconds between NSE requests

# ADX Trend Filter  (Issue 8)
ENABLE_ADX_FILTER = os.getenv('ENABLE_ADX_FILTER', 'False') == 'True'
ADX_MIN           = float(os.getenv('ADX_MIN', '25.0'))           # Min ADX for strong trend

# Logging
LOG_LEVEL         = os.getenv('LOG_LEVEL', 'INFO')


# ============================================================
# 🎨  TERMINAL COLORS
# ============================================================

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


# ============================================================
# 📋  FNO STOCKS WATCHLIST — FETCHED FROM API
# ============================================================

FALLBACK_FNO_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "SBIN", "BAJFINANCE", "HINDUNILVR", "AXISBANK", "WIPRO",
    "TATAMOTORS", "MARUTI", "SUNPHARMA", "ONGC", "POWERGRID",
    "NTPC", "TECHM", "ULTRACEMCO", "TITAN", "ASIANPAINT",
    "BAJAJFINSV", "HCLTECH", "ITC", "LTIM", "M&M",
    "NESTLEIND", "DRREDDY", "DIVISLAB", "CIPLA", "BRITANNIA",
    "ADANIENT", "ADANIPORTS", "COALINDIA", "BPCL", "GRASIM",
    "HEROMOTOCO", "INDUSINDBK", "JSWSTEEL", "TATASTEEL", "LT"
]

def fetch_fno_stocks():
    """Fetch all FNO stocks from NSE API"""
    try:
        url = "https://nse-result-calendar.netlify.app/api/fno-list"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            stocks = data.get('symbols', [])
            if stocks:
                print(f"  {GREEN}✅ Fetched {len(stocks)} FNO stocks from API{RESET}")
                log.info(f"Fetched {len(stocks)} FNO stocks from API")
                return sorted(stocks)
        return None
    except Exception as e:
        print(f"  {YELLOW}⚠️  Could not fetch FNO list from API: {e}{RESET}")
        log.warning(f"FNO API fetch failed: {e}")
        return None

FNO_STOCKS = fetch_fno_stocks() or FALLBACK_FNO_STOCKS


# ============================================================
# 🎌  NSE HOLIDAY LIST 2026  (Issue 6)
# ============================================================

NSE_HOLIDAYS_2026 = [
    "26-01-2026",   # Republic Day
    "19-02-2026",   # Chhatrapati Shivaji Maharaj Jayanti
    "25-03-2026",   # Holi
    "14-04-2026",   # Dr. Baba Saheb Ambedkar Jayanti
    "01-05-2026",   # Maharashtra Day
    "15-08-2026",   # Independence Day
    "02-10-2026",   # Gandhi Jayanti / Mahatma Gandhi Jayanti
    "20-10-2026",   # Diwali Laxmi Puja
    "21-10-2026",   # Diwali Balipratipada
    "25-12-2026",   # Christmas
]


# ============================================================
# 📡  TELEGRAM FUNCTIONS
# ============================================================

def send_telegram(message):
    """Core function to send any message to Telegram"""
    try:
        url     = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id"    : TELEGRAM_CHAT_ID,
            "text"       : message,
            "parse_mode" : "HTML"
        }
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            print(f"  {GREEN}✅ Telegram alert sent!{RESET}")
        else:
            print(f"  {RED}❌ Telegram error: {response.text}{RESET}")
            log.error(f"Telegram send failed: {response.text}")
    except Exception as e:
        print(f"  {RED}❌ Telegram failed: {e}{RESET}")
        log.error(f"Telegram exception: {e}")


def telegram_startup():
    """Sent once when OISignalFlow starts"""
    msg = (
        "🚀 <b>OISignalFlow v1.0.0 is LIVE!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Date      : {datetime.now().strftime('%d-%m-%Y')}\n"
        f"🕐 Started   : {datetime.now().strftime('%H:%M:%S')}\n"
        f"📊 Watching  : {len(FNO_STOCKS)} FNO Stocks\n"
        f"⏰ Interval  : Every {SCAN_INTERVAL} minutes\n"
        f"📈 OI Filter : Min {OI_CHANGE_MIN}% change\n"
        f"💹 Price Min : +{PRICE_CHANGE_MIN}%\n"
        f"📦 Volume    : {VOLUME_MULT}x above normal\n"
        f"⏳ API Delay : {REQUEST_DELAY}s between requests\n"
    )
    if ENABLE_ADX_FILTER:
        msg += f"📉 ADX Filter : Enabled (min {ADX_MIN})\n"
    msg += (
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Scanning for Long Buildup signals\n"
        "🎯 CE Call Buy candidates will be alerted!"
    )
    send_telegram(msg)


def telegram_ce_signals(ce_candidates, scan_num):
    """Sent when CE buy candidates are found — chunked max 10 per message (Issue 4)"""
    CHUNK_SIZE    = 10
    now           = datetime.now().strftime("%d-%m-%Y %H:%M")
    chunks        = [ce_candidates[i:i+CHUNK_SIZE]
                     for i in range(0, len(ce_candidates), CHUNK_SIZE)]
    total_chunks  = len(chunks)

    for part, chunk in enumerate(chunks, 1):
        msg = ""

        # ── Header (first part only) ──
        if part == 1:
            msg += (
                f"🟢 <b>OISignalFlow v1.0.0 — CE BUY ALERT!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🕐 Time   : {now}\n"
                f"🔍 Scan # : {scan_num}\n"
                f"📊 Found  : {len(ce_candidates)} stock(s)\n"
            )
            if total_chunks > 1:
                msg += f"📄 Part   : {part} of {total_chunks}\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        else:
            msg += (
                f"🟢 <b>CE BUY ALERT — Part {part}/{total_chunks}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            )

        # ── Stock details ──
        offset = (part - 1) * CHUNK_SIZE
        for i, s in enumerate(chunk, offset + 1):
            if s['OI_Chg_%'] >= 5 and s['Vol_Ratio'] >= 3:
                strength = "🔥🔥 VERY STRONG"
            elif s['OI_Chg_%'] >= 3 and s['Vol_Ratio'] >= 2:
                strength = "🔥 STRONG"
            else:
                strength = "✅ MODERATE"

            adx_line = (f"   📉 ADX       : {s.get('ADX', 0):.1f}\n"
                        if ENABLE_ADX_FILTER else "")

            msg += (
                f"<b>{i}. {s['Symbol']}</b>\n"
                f"   💰 Price     : ₹{s['Price']}  "
                f"({s['Price_Chg_%']:+.2f}%)\n"
                f"   📈 OI Change : {s['OI_Chg_%']:+.2f}%\n"
                f"   📊 Volume    : {s['Vol_Ratio']:.1f}x normal\n"
                + adx_line +
                f"   🔰 Signal    : {s['Signal']}\n"
                f"   ⚡ Strength  : {strength}\n"
                f"   🎯 Action    : BUY ATM CE\n"
                f"   🛑 Stop Loss : Close below VWAP\n"
                f"   ⏱ Scan Time : {s['Time']}\n\n"
            )

        # ── Footer (last part only) ──
        if part == total_chunks:
            msg += (
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📌 <b>Strike Selection Guide:</b>\n"
                "   ATM = Best if strong signal\n"
                "   1 OTM = If volume very high\n"
                "   Avoid 2+ OTM strikes\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "⚠️ <i>OISignalFlow v1.0.0 — for education.\n"
                "Not financial advice. Trade carefully.</i>"
            )

        send_telegram(msg)


def telegram_no_signal(scan_num):
    """Sent every 3rd scan when no signal found"""
    now = datetime.now().strftime("%H:%M")
    msg = (
        f"🔍 <b>OISignalFlow v1.0.0 — Scan #{scan_num}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 Time   : {now}\n"
        f"⚪ Result  : No CE signals found\n"
        f"⏰ Next   : In {SCAN_INTERVAL} minutes\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 Tip: Wait for strong Long Buildup\n"
        "   Price↑ + OI↑ = Best CE entry"
    )
    send_telegram(msg)


def telegram_summary(results, scan_num):
    """Sent every 30 minutes as market overview"""
    if not results:
        return

    df        = pd.DataFrame(results)
    long_bu   = len(df[df['Signal'].str.contains('LONG BUILDUP')])
    short_bu  = len(df[df['Signal'].str.contains('SHORT BUILDUP')])
    covering  = len(df[df['Signal'].str.contains('SHORT COVERING')])
    unwinding = len(df[df['Signal'].str.contains('LONG UNWINDING')])

    if long_bu > short_bu:
        mood = "🟢 BULLISH"
    elif short_bu > long_bu:
        mood = "🔴 BEARISH"
    else:
        mood = "🟡 NEUTRAL"

    now = datetime.now().strftime("%d-%m-%Y %H:%M")
    msg = (
        f"📊 <b>OISignalFlow v1.0.0 — Market Summary</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 Time          : {now}\n"
        f"🔍 Scan #        : {scan_num}\n"
        f"📋 Total Scanned : {len(results)} stocks\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 Long Buildup  : {long_bu} stocks\n"
        f"🔴 Short Buildup : {short_bu} stocks\n"
        f"🟡 Short Covering: {covering} stocks\n"
        f"⚪ Long Unwinding: {unwinding} stocks\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌡 Market Mood   : {mood}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Powered by OISignalFlow v1.0.0</i>"
    )
    send_telegram(msg)


def telegram_market_closed():
    """Sent when market closes"""
    msg = (
        "🔴 <b>OISignalFlow v1.0.0 — Market Closed</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 Closed at : {datetime.now().strftime('%H:%M')}\n"
        "📅 Scanner will resume:\n"
        "   Next trading day at 9:15 AM\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Have a great evening!\n"
        "<i>— OISignalFlow v1.0.0</i>"
    )
    send_telegram(msg)


def telegram_holiday(today_str):
    """Sent once on NSE market holiday (Issue 6)"""
    msg = (
        "🎌 <b>OISignalFlow v1.0.0 — Market Holiday</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Today ({today_str}) is an NSE trading holiday.\n"
        "⏰ OISignalFlow will resume next trading day at 9:15 AM.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Enjoy the holiday! 🎉\n"
        "<i>— OISignalFlow v1.0.0</i>"
    )
    send_telegram(msg)


# ============================================================
# 📊  OI DATA FETCHER
# ============================================================

def calculate_adx(data, period=14):
    """
    Calculate ADX (Average Directional Index) from OHLCV data.
    Returns ADX value (float) or 0.0 if data is insufficient.
    (Issue 8)
    """
    try:
        if len(data) < period * 2:
            return 0.0

        # Support both nselib column name conventions
        high  = pd.to_numeric(
            data.get('High Price', data.get('High', pd.Series(dtype=float))),
            errors='coerce')
        low   = pd.to_numeric(
            data.get('Low Price',  data.get('Low',  pd.Series(dtype=float))),
            errors='coerce')
        close = pd.to_numeric(
            data.get('Close Price',data.get('Close',pd.Series(dtype=float))),
            errors='coerce')

        if high.empty or low.empty or close.empty:
            return 0.0

        high  = high.reset_index(drop=True)
        low   = low.reset_index(drop=True)
        close = close.reset_index(drop=True)

        # True Range
        prev_close = close.shift(1)
        tr = pd.concat([
            (high - low).abs(),
            (high - prev_close).abs(),
            (low  - prev_close).abs()
        ], axis=1).max(axis=1)

        # +DM and -DM
        up   = high.diff()
        down = -low.diff()
        plus_dm  = up.where((up > down)   & (up > 0),   0.0)
        minus_dm = down.where((down > up) & (down > 0), 0.0)

        # Wilder's smoothing (alpha = 1/period)
        alpha    = 1.0 / period
        atr      = tr.ewm(      alpha=alpha, adjust=False).mean()
        plus_di  = 100 * plus_dm.ewm( alpha=alpha, adjust=False).mean() / atr.replace(0, 1)
        minus_di = 100 * minus_dm.ewm(alpha=alpha, adjust=False).mean() / atr.replace(0, 1)

        dx  = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1)
        adx = dx.ewm(alpha=alpha, adjust=False).mean()

        return round(float(adx.iloc[-1]), 2)

    except Exception:
        return 0.0


def get_oi_data(symbol):
    """Fetch OI, Price, Volume and ADX data for one stock from NSE"""
    try:
        data = derivatives.future_price_volume_data(
            symbol     = symbol,
            instrument = 'FUTSTK',
            period     = '1D'
        )

        if data is None or data.empty or len(data) < 2:
            return None

        latest = data.iloc[-1]
        prev   = data.iloc[-2]

        current_oi    = float(latest.get('Open Interest', 0))
        prev_oi       = float(prev.get('Open Interest', 0))
        current_price = float(latest.get('Close Price', 0))
        prev_price    = float(prev.get('Close Price', 0))
        current_vol   = float(latest.get('Volume', 0))
        prev_vol      = float(prev.get('Volume', 0))

        if prev_oi == 0 or prev_price == 0 or prev_vol == 0:
            return None

        oi_chg_pct    = ((current_oi - prev_oi)     / prev_oi)     * 100
        price_chg_pct = ((current_price - prev_price) / prev_price) * 100
        vol_ratio     = current_vol / prev_vol

        # ADX — only compute when filter is enabled (saves CPU)  (Issue 8)
        adx_value = calculate_adx(data) if ENABLE_ADX_FILTER else 0.0

        return {
            'Symbol'       : symbol,
            'Price'        : round(current_price, 2),
            'Price_Chg_%'  : round(price_chg_pct, 2),
            'OI'           : int(current_oi),
            'OI_Chg_%'     : round(oi_chg_pct, 2),
            'Volume'       : int(current_vol),
            'Vol_Ratio'    : round(vol_ratio, 2),
            'ADX'          : adx_value,
            'Signal'       : classify_signal(price_chg_pct, oi_chg_pct),
            'Time'         : datetime.now().strftime("%H:%M")
        }

    except Exception as e:
        log.warning(f"NSE data fetch failed for {symbol}: {e}")
        return None


# ============================================================
# 🔰  SIGNAL CLASSIFIER
# ============================================================

def classify_signal(price_chg, oi_chg):
    """Classify OI buildup type"""
    if price_chg > 0 and oi_chg > 0:
        return "🟢 LONG BUILDUP"      # ✅ Best — Buy CE
    elif price_chg < 0 and oi_chg > 0:
        return "🔴 SHORT BUILDUP"     # ❌ Avoid CE — Buy PE
    elif price_chg > 0 and oi_chg < 0:
        return "🟡 SHORT COVERING"    # ⚠️ Weak — Risky CE
    else:
        return "⚪ LONG UNWINDING"    # ❌ Avoid all


# ============================================================
# 💾  EXCEL SAVER  (Issue 7)
# ============================================================

def save_to_excel(all_df, ce_df):
    """Save all results and CE signals to Excel"""
    try:
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
            all_df.to_excel(writer, sheet_name='All Stocks', index=False)
            if not ce_df.empty:
                ce_df.to_excel(writer, sheet_name='CE Buy Signals', index=False)
        print(f"  {GREEN}💾 Saved → {OUTPUT_FILE}{RESET}")
        log.info(f"Excel saved: {OUTPUT_FILE}")

    except PermissionError:
        # File is open in Excel — give clear, actionable message
        print(f"  {RED}❌ Cannot save Excel — file is open!{RESET}")
        print(f"     Close '{OUTPUT_FILE}' in Excel and it")
        print(f"     will save automatically on the next scan.")
        log.warning(f"Excel save failed — file locked (open in Excel): {OUTPUT_FILE}")

    except Exception as e:
        print(f"  {RED}❌ Excel save error: {e}{RESET}")
        log.error(f"Excel save error: {e}")


# ============================================================
# 📡  REAL-TIME CONFIG UPDATER  (Issue 2 — reduced call frequency)
# ============================================================

def update_config_json(scan_num, current_symbol, results, ce_candidates):
    """Update config.json with real-time scan data for live dashboard"""
    try:
        # Compute market mood from current results
        long_bu  = len([r for r in results if "LONG BUILDUP"  in r['Signal']])
        short_bu = len([r for r in results if "SHORT BUILDUP" in r['Signal']])
        if long_bu > short_bu:
            mood = "BULLISH"
        elif short_bu > long_bu:
            mood = "BEARISH"
        else:
            mood = "NEUTRAL"

        config = {
            "version": "v1.0.0",
            "status": {
                "system_status" : "scanning" if current_symbol else "ready",
                "market_open"   : is_market_open(),
                "last_update"   : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "scanner_running": True,
                "current_scan"  : scan_num,
                "current_stock" : current_symbol
            },
            "configuration": {
                "fno_stocks_total"      : len(FNO_STOCKS),
                "scan_interval"         : SCAN_INTERVAL,
                "oi_change_min"         : OI_CHANGE_MIN,
                "price_change_min"      : PRICE_CHANGE_MIN,
                "volume_mult"           : VOLUME_MULT,
                "request_delay"         : REQUEST_DELAY,
                "adx_filter_enabled"    : ENABLE_ADX_FILTER,
                "adx_min"               : ADX_MIN,
                "output_file"           : OUTPUT_FILE,
                "telegram_enabled"      : True,
                "desktop_notifications" : DESKTOP_NOTIFY,
                "api_source"            : "NSE nselib",
                "data_type"             : "Futures (FUTSTK)",
                "period"                : "1D Candles",
                "api_status"            : "Connected"
            },
            "statistics": {
                "total_scans"          : scan_num,
                "stocks_scanned"       : len(results),
                "signals_found"        : len(ce_candidates),
                "ce_candidates"        : len(ce_candidates),
                "market_mood"          : mood,
                "long_buildup_count"   : long_bu,
                "short_buildup_count"  : short_bu,
                "short_covering_count" : len([r for r in results if "SHORT COVERING"  in r['Signal']]),
                "long_unwinding_count" : len([r for r in results if "LONG UNWINDING"  in r['Signal']])
            },
            "recent_signals": [
                {
                    "symbol"       : s['Symbol'],
                    "price"        : s['Price'],
                    "price_change" : s['Price_Chg_%'],
                    "oi_change"    : s['OI_Chg_%'],
                    "volume_ratio" : s['Vol_Ratio'],
                    "adx"          : s.get('ADX', 0),
                    "signal"       : s['Signal'],
                    "strength"     : (
                        "🔥🔥 VERY STRONG" if s['OI_Chg_%'] >= 5 and s['Vol_Ratio'] >= 3
                        else "🔥 STRONG"   if s['OI_Chg_%'] >= 3
                        else "✅ MODERATE"
                    ),
                    "time"         : s['Time']
                }
                for s in ce_candidates
            ],
            "all_scan_results": [
                {
                    "symbol"       : r['Symbol'],
                    "price"        : r['Price'],
                    "price_change" : r['Price_Chg_%'],
                    "oi_change"    : r['OI_Chg_%'],
                    "volume_ratio" : r['Vol_Ratio'],
                    "adx"          : r.get('ADX', 0),
                    "signal"       : r['Signal'],
                    "filters": {
                        "signal_ok" : "🟢 LONG BUILDUP" in r['Signal'],
                        "oi_ok"     : r['OI_Chg_%']    >= OI_CHANGE_MIN,
                        "price_ok"  : r['Price_Chg_%'] >= PRICE_CHANGE_MIN,
                        "volume_ok" : r['Vol_Ratio']   >= VOLUME_MULT,
                        "adx_ok"    : (not ENABLE_ADX_FILTER) or (r.get('ADX', 0) >= ADX_MIN)
                    },
                    "time"         : r['Time']
                }
                for r in sorted(results, key=lambda x: x['OI_Chg_%'], reverse=True)
            ]
        }

        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)

    except Exception as e:
        print(f"  {RED}❌ Config update error: {e}{RESET}")
        log.error(f"config.json update error: {e}")


# ============================================================
# 🔍  MAIN SCANNER ENGINE
# ============================================================

scan_count = 0

def run_scanner():
    global scan_count
    scan_count += 1

    now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    # ── Header ──
    print(f"\n{BOLD}{CYAN}{'═'*55}{RESET}")
    print(f"{BOLD}{CYAN}  ⚡ OISignalFlow v1.0.0  |  Scan #{scan_count}  |  {now}{RESET}")
    print(f"{BOLD}{CYAN}{'═'*55}{RESET}")
    log.info(f"Scan #{scan_count} started")

    results       = []
    ce_candidates = []

    # ── Scan Each Stock ──
    for idx, symbol in enumerate(FNO_STOCKS):
        print(f"  {CYAN}Scanning {symbol}... [{idx+1}/{len(FNO_STOCKS)}]{RESET}      ", end="\r")

        row = get_oi_data(symbol)

        cfg_updated = False   # track if config was already written this iteration

        if row:
            results.append(row)

            # CE filter conditions
            is_long_buildup = row['Signal'] == "🟢 LONG BUILDUP"
            oi_ok    = row['OI_Chg_%']    >= OI_CHANGE_MIN
            price_ok = row['Price_Chg_%'] >= PRICE_CHANGE_MIN
            volume_ok= row['Vol_Ratio']   >= VOLUME_MULT
            # ADX filter — always True when filter is disabled  (Issue 8)
            adx_ok   = (not ENABLE_ADX_FILTER) or (row.get('ADX', 0) >= ADX_MIN)

            if is_long_buildup and oi_ok and price_ok and volume_ok and adx_ok:
                ce_candidates.append(row)
                log.info(
                    f"CE signal: {symbol} | "
                    f"OI: {row['OI_Chg_%']:+.2f}% | "
                    f"Price: {row['Price_Chg_%']:+.2f}% | "
                    f"Vol: {row['Vol_Ratio']:.1f}x"
                    + (f" | ADX: {row.get('ADX',0):.1f}" if ENABLE_ADX_FILTER else "")
                )
                # Update dashboard immediately on new CE signal  (Issue 2)
                update_config_json(scan_count, symbol, results, ce_candidates)
                cfg_updated = True

        # Rate limit — avoid hammering NSE API  (Issue 3)
        time.sleep(REQUEST_DELAY)

        # Update dashboard every 10 stocks — skip if already updated this iteration  (Issue 2)
        if idx % 10 == 0 and not cfg_updated:
            update_config_json(scan_count, symbol, results, ce_candidates)

    # ── CE Candidates Output ──
    print(f"\n  {BOLD}{GREEN}✅ CE BUY SIGNALS: {len(ce_candidates)} found{RESET}")
    print(f"  {'─'*53}")
    log.info(f"Scan #{scan_count} complete — {len(ce_candidates)} CE signals from {len(results)} stocks")

    if ce_candidates:
        for s in ce_candidates:
            strength = (
                "🔥🔥 VERY STRONG" if s['OI_Chg_%'] >= 5
                else "🔥 STRONG"   if s['OI_Chg_%'] >= 3
                else "✅ MODERATE"
            )
            print(f"\n  {BOLD}{GREEN}▶ {s['Symbol']}{RESET}")
            print(f"    💰 Price     : ₹{s['Price']}  ({s['Price_Chg_%']:+.2f}%)")
            print(f"    📈 OI Change : {s['OI_Chg_%']:+.2f}%")
            print(f"    📊 Volume    : {s['Vol_Ratio']:.1f}x normal")
            if ENABLE_ADX_FILTER:
                print(f"    📉 ADX       : {s.get('ADX', 0):.1f} (trend strength)")
            print(f"    🔰 Signal    : {s['Signal']}")
            print(f"    ⚡ Strength  : {strength}")
            print(f"    🎯 Action    : BUY ATM CE")
            print(f"    🛑 Stop Loss : Below VWAP")

        # Send Telegram signal alert (chunked)
        telegram_ce_signals(ce_candidates, scan_count)

        # Desktop notification
        if DESKTOP_NOTIFY:
            names = ", ".join([s['Symbol'] for s in ce_candidates])
            notification.notify(
                title   = "⚡ OISignalFlow v1.0.0 — CE Buy Signal!",
                message = f"Stocks: {names}",
                timeout = 10
            )
    else:
        print(f"\n  {YELLOW}  No CE signals this scan. Market may be choppy.{RESET}")
        if scan_count % 3 == 0:
            telegram_no_signal(scan_count)

    # ── Full Results Table ──
    print(f"\n  {BOLD}{CYAN}📊 FULL SCAN TABLE{RESET}")
    print(f"  {'─'*53}")

    if results:
        df = pd.DataFrame(results)
        df = df.sort_values('OI_Chg_%', ascending=False)
        print(df[['Symbol', 'Price', 'Price_Chg_%',
                  'OI_Chg_%', 'Vol_Ratio', 'Signal']].to_string(index=False))

        ce_df = pd.DataFrame(ce_candidates) if ce_candidates else pd.DataFrame()
        save_to_excel(df, ce_df)

        # Send market summary every 6th scan (~30 minutes)
        if scan_count % 6 == 0:
            telegram_summary(results, scan_count)

        # Final complete update after scan ends  (Issue 2)
        update_config_json(scan_count, "", results, ce_candidates)

    print(f"\n  {CYAN}⏰ Next scan in {SCAN_INTERVAL} minutes...{RESET}")
    print(f"  {CYAN}{'═'*53}{RESET}\n")


# ============================================================
# 🕐  MARKET HOURS CHECKER  (Issue 6)
# ============================================================

def is_market_open():
    """Returns True only during NSE market hours (excludes holidays)"""
    now   = datetime.now()
    h, m  = now.hour, now.minute
    today = now.strftime("%d-%m-%Y")

    if now.weekday() >= 5:              return False   # Weekend
    if today in NSE_HOLIDAYS_2026:      return False   # NSE Holiday
    if h < 9 or (h == 9 and m < 15):   return False   # Before 9:15 AM
    if h > 15 or (h == 15 and m > 30): return False   # After 3:30 PM
    return True


# ============================================================
# ⏰  SCHEDULER JOB
# ============================================================

market_was_open    = False
holiday_alerted_date = None   # tracks which date we already sent holiday alert

def job():
    global market_was_open, holiday_alerted_date
    now   = datetime.now()
    today = now.strftime("%d-%m-%Y")

    # ── Holiday check  (Issue 6) ──
    if today in NSE_HOLIDAYS_2026 and now.weekday() < 5:
        if holiday_alerted_date != today:
            holiday_alerted_date = today
            print(f"  {YELLOW}🎌 NSE Holiday today ({today}). "
                  f"OISignalFlow waiting...{RESET}")
            log.info(f"NSE Holiday: {today} — skipping scan")
            telegram_holiday(today)
        market_was_open = False
        return

    # ── Normal market hours check ──
    if is_market_open():
        market_was_open = True
        run_scanner()
    else:
        if market_was_open:
            telegram_market_closed()
            log.info("Market closed — sent market-closed alert")
            market_was_open = False
        print(f"  {YELLOW}⏸  Market closed. OISignalFlow waiting...{RESET}")


# ============================================================
# 🚀  LAUNCH OISignalFlow v1.0.0
# ============================================================

if __name__ == "__main__":

    # ── Startup Banner ──
    print(f"\n{BOLD}{CYAN}")
    print("╔══════════════════════════════════════════════╗")
    print("║                                              ║")
    print("║        ⚡  O I S i g n a l F l o w          ║")
    print("║                                              ║")
    print("║   Free OI Screener for CE Call Buying        ║")
    print("║   Data  : NSE India  (100% Free)             ║")
    print("║   Alerts: Telegram Bot                       ║")
    print("║   Scan  : Every 5 Minutes                    ║")
    print("║   Version: v1.0.0                            ║")
    print("║                                              ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"{RESET}\n")

    # ── Validate .env credentials ──
    if "YOUR_BOT_TOKEN_HERE" in TELEGRAM_TOKEN:
        print(f"{RED}⚠️  Please set TELEGRAM_TOKEN in .env file!{RESET}\n")
        log.error("TELEGRAM_TOKEN not set in .env")
        exit(1)
    if "YOUR_CHAT_ID_HERE" in TELEGRAM_CHAT_ID:
        print(f"{RED}⚠️  Please set TELEGRAM_CHAT_ID in .env file!{RESET}\n")
        log.error("TELEGRAM_CHAT_ID not set in .env")
        exit(1)

    print(f"{GREEN}✅ OISignalFlow v1.0.0 starting...{RESET}\n")
    print(f"  📁 Config    : .env")
    print(f"  📊 Stocks    : {len(FNO_STOCKS)} FNO stocks (from API)")
    print(f"  ⏱ Interval   : Every {SCAN_INTERVAL} minutes")
    print(f"  📈 OI Min    : {OI_CHANGE_MIN}%")
    print(f"  💹 Price Min : {PRICE_CHANGE_MIN}%")
    print(f"  📦 Volume    : {VOLUME_MULT}x normal")
    print(f"  ⏳ API Delay : {REQUEST_DELAY}s between requests")
    if ENABLE_ADX_FILTER:
        print(f"  📉 ADX Filter: Enabled (min {ADX_MIN})")
    else:
        print(f"  📉 ADX Filter: Disabled")
    print(f"  💾 Excel     : {OUTPUT_FILE}")
    print(f"  📝 Log File  : OISignalFlow.log")
    print(f"  📱 Telegram  : Enabled\n")

    log.info(f"OISignalFlow v1.0.0 starting | "
             f"{len(FNO_STOCKS)} stocks | interval {SCAN_INTERVAL}min | "
             f"OI≥{OI_CHANGE_MIN}% | Price≥{PRICE_CHANGE_MIN}% | "
             f"Vol≥{VOLUME_MULT}x | delay={REQUEST_DELAY}s")

    # ── Send Telegram startup message ──
    print(f"{CYAN}Testing Telegram connection...{RESET}")
    telegram_startup()

    # ── First scan immediately ──
    job()

    # ── Schedule every N minutes ──
    schedule.every(SCAN_INTERVAL).minutes.do(job)

    print(f"\n{GREEN}✅ OISignalFlow v1.0.0 is running! "
          f"Press Ctrl+C to stop.{RESET}\n")

    while True:
        schedule.run_pending()
        time.sleep(30)

# ============================================================
# END OF OISignalFlow v1.0.0
# ============================================================
