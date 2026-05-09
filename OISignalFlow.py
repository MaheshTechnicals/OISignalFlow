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
#   Version   : 1.0.0
#   Purpose   : Free OI Screener for CE Call Buying
#   Data      : NSE India (Free — No paid API)
#   Alerts    : Telegram Bot
#   Interval  : Every 5 Minutes (Auto)
#   Author    : OISignalFlow
#   License   : Free to use
# ============================================================

import time
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
# ⚙️  CONFIGURATION — LOADED FROM .env FILE
# ============================================================

# Telegram Settings
TELEGRAM_TOKEN    = os.getenv('TELEGRAM_TOKEN', 'YOUR_BOT_TOKEN_HERE')
TELEGRAM_CHAT_ID  = os.getenv('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID_HERE')

# Scan Parameters
OI_CHANGE_MIN     = float(os.getenv('OI_CHANGE_MIN', '2.0'))        # Min OI change %
PRICE_CHANGE_MIN  = float(os.getenv('PRICE_CHANGE_MIN', '0.3'))     # Min price change %
VOLUME_MULT       = float(os.getenv('VOLUME_MULT', '1.5'))          # Volume multiplier
SCAN_INTERVAL     = int(os.getenv('SCAN_INTERVAL', '5'))            # Scan interval in minutes
OUTPUT_FILE       = os.getenv('OUTPUT_FILE', 'OISignalFlow_Results.xlsx')  # Excel output

# Logging
LOG_LEVEL         = os.getenv('LOG_LEVEL', 'INFO')                  # DEBUG, INFO, WARNING, ERROR


# ============================================================
# 📋  FNO STOCKS WATCHLIST — FETCHED FROM API
# ============================================================

# Fallback list if API is unavailable
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
                return sorted(stocks)
        return None
    except Exception as e:
        print(f"  {YELLOW}⚠️  Could not fetch from API: {e}{RESET}")
        return None

# Fetch FNO stocks from API, fallback to hardcoded list
FNO_STOCKS = fetch_fno_stocks() or FALLBACK_FNO_STOCKS


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
    except Exception as e:
        print(f"  {RED}❌ Telegram failed: {e}{RESET}")


def telegram_startup():
    """Sent once when OISignalFlow starts"""
    msg = (
        "🚀 <b>OISignalFlow is LIVE!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Date      : {datetime.now().strftime('%d-%m-%Y')}\n"
        f"🕐 Started   : {datetime.now().strftime('%H:%M:%S')}\n"
        f"📊 Watching  : {len(FNO_STOCKS)} FNO Stocks\n"
        f"⏰ Interval  : Every {SCAN_INTERVAL} minutes\n"
        f"📈 OI Filter : Min {OI_CHANGE_MIN}% change\n"
        f"💹 Price Min : +{PRICE_CHANGE_MIN}%\n"
        f"📦 Volume    : {VOLUME_MULT}x above normal\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Scanning for Long Buildup signals\n"
        "🎯 CE Call Buy candidates will be alerted!"
    )
    send_telegram(msg)


def telegram_ce_signals(ce_candidates, scan_num):
    """Sent when CE buy candidates are found"""
    now = datetime.now().strftime("%d-%m-%Y %H:%M")

    msg = (
        f"🟢 <b>OISignalFlow — CE BUY ALERT!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 Time   : {now}\n"
        f"🔍 Scan # : {scan_num}\n"
        f"📊 Found  : {len(ce_candidates)} stock(s)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    for i, s in enumerate(ce_candidates, 1):
        # Signal strength rating
        if s['OI_Chg_%'] >= 5 and s['Vol_Ratio'] >= 3:
            strength = "🔥🔥 VERY STRONG"
        elif s['OI_Chg_%'] >= 3 and s['Vol_Ratio'] >= 2:
            strength = "🔥 STRONG"
        else:
            strength = "✅ MODERATE"

        msg += (
            f"<b>{i}. {s['Symbol']}</b>\n"
            f"   💰 Price     : ₹{s['Price']}  "
            f"({s['Price_Chg_%']:+.2f}%)\n"
            f"   📈 OI Change : {s['OI_Chg_%']:+.2f}%\n"
            f"   📊 Volume    : {s['Vol_Ratio']:.1f}x normal\n"
            f"   🔰 Signal    : {s['Signal']}\n"
            f"   ⚡ Strength  : {strength}\n"
            f"   🎯 Action    : BUY ATM CE\n"
            f"   🛑 Stop Loss : Close below VWAP\n"
            f"   ⏱ Scan Time : {s['Time']}\n\n"
        )

    msg += (
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 <b>Strike Selection Guide:</b>\n"
        "   ATM = Best if strong signal\n"
        "   1 OTM = If volume very high\n"
        "   Avoid 2+ OTM strikes\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ <i>OISignalFlow is for education.\n"
        "Not financial advice. Trade carefully.</i>"
    )
    send_telegram(msg)


def telegram_no_signal(scan_num):
    """Sent every 3rd scan when no signal found"""
    now = datetime.now().strftime("%H:%M")
    msg = (
        f"🔍 <b>OISignalFlow — Scan #{scan_num}</b>\n"
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

    df       = pd.DataFrame(results)
    long_bu  = len(df[df['Signal'].str.contains('LONG BUILDUP')])
    short_bu = len(df[df['Signal'].str.contains('SHORT BUILDUP')])
    covering = len(df[df['Signal'].str.contains('SHORT COVERING')])
    unwinding= len(df[df['Signal'].str.contains('LONG UNWINDING')])

    # Market mood
    if long_bu > short_bu:
        mood = "🟢 BULLISH"
    elif short_bu > long_bu:
        mood = "🔴 BEARISH"
    else:
        mood = "🟡 NEUTRAL"

    now = datetime.now().strftime("%d-%m-%Y %H:%M")
    msg = (
        f"📊 <b>OISignalFlow — Market Summary</b>\n"
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
        f"<i>Powered by OISignalFlow v1.0</i>"
    )
    send_telegram(msg)


def telegram_market_closed():
    """Sent when market closes"""
    msg = (
        "🔴 <b>OISignalFlow — Market Closed</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 Closed at : {datetime.now().strftime('%H:%M')}\n"
        "📅 Scanner will resume:\n"
        "   Next trading day at 9:15 AM\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Have a great evening!\n"
        "<i>— OISignalFlow</i>"
    )
    send_telegram(msg)


# ============================================================
# 📊  OI DATA FETCHER
# ============================================================

def get_oi_data(symbol):
    """Fetch OI, Price and Volume data for one stock from NSE"""
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

        oi_chg_pct    = ((current_oi - prev_oi) / prev_oi) * 100
        price_chg_pct = ((current_price - prev_price) / prev_price) * 100
        vol_ratio     = current_vol / prev_vol

        return {
            'Symbol'       : symbol,
            'Price'        : round(current_price, 2),
            'Price_Chg_%'  : round(price_chg_pct, 2),
            'OI'           : int(current_oi),
            'OI_Chg_%'     : round(oi_chg_pct, 2),
            'Volume'       : int(current_vol),
            'Vol_Ratio'    : round(vol_ratio, 2),
            'Signal'       : classify_signal(price_chg_pct, oi_chg_pct),
            'Time'         : datetime.now().strftime("%H:%M")
        }

    except Exception as e:
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
# 💾  EXCEL SAVER
# ============================================================

def save_to_excel(all_df, ce_df):
    """Save all results and CE signals to Excel"""
    try:
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
            all_df.to_excel(
                writer,
                sheet_name='All Stocks',
                index=False
            )
            if not ce_df.empty:
                ce_df.to_excel(
                    writer,
                    sheet_name='CE Buy Signals',
                    index=False
                )
        print(f"  {GREEN}💾 Saved → {OUTPUT_FILE}{RESET}")
    except Exception as e:
        print(f"  {RED}❌ Excel save error: {e}{RESET}")


# ============================================================
# 🔍  MAIN SCANNER ENGINE
# ============================================================

scan_count = 0

def run_scanner():
    global scan_count
    scan_count += 1

    now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    # Header
    print(f"\n{BOLD}{CYAN}{'═'*55}{RESET}")
    print(f"{BOLD}{CYAN}  ⚡ OISignalFlow  |  Scan #{scan_count}  |  {now}{RESET}")
    print(f"{BOLD}{CYAN}{'═'*55}{RESET}")

    results       = []
    ce_candidates = []

    # Scan each stock
    for symbol in FNO_STOCKS:
        print(f"  {CYAN}Scanning {symbol}...{RESET}      ", end="\r")
        row = get_oi_data(symbol)
        if row:
            results.append(row)

            # Apply CE filter conditions
            is_long_buildup = row['Signal'] == "🟢 LONG BUILDUP"
            oi_ok           = row['OI_Chg_%']    >= OI_CHANGE_MIN
            price_ok        = row['Price_Chg_%'] >= PRICE_CHANGE_MIN
            volume_ok       = row['Vol_Ratio']   >= VOLUME_MULT

            if is_long_buildup and oi_ok and price_ok and volume_ok:
                ce_candidates.append(row)

    # ── CE Candidates Output ──
    print(f"\n  {BOLD}{GREEN}✅ CE BUY SIGNALS: "
          f"{len(ce_candidates)} found{RESET}")
    print(f"  {'─'*53}")

    if ce_candidates:
        for s in ce_candidates:
            strength = (
                "🔥🔥 VERY STRONG" if s['OI_Chg_%'] >= 5
                else "🔥 STRONG"   if s['OI_Chg_%'] >= 3
                else "✅ MODERATE"
            )
            print(f"\n  {BOLD}{GREEN}▶ {s['Symbol']}{RESET}")
            print(f"    💰 Price     : ₹{s['Price']}  "
                  f"({s['Price_Chg_%']:+.2f}%)")
            print(f"    📈 OI Change : {s['OI_Chg_%']:+.2f}%")
            print(f"    📊 Volume    : {s['Vol_Ratio']:.1f}x normal")
            print(f"    🔰 Signal    : {s['Signal']}")
            print(f"    ⚡ Strength  : {strength}")
            print(f"    🎯 Action    : BUY ATM CE")
            print(f"    🛑 Stop Loss : Below VWAP")

        # Send Telegram signal alert
        telegram_ce_signals(ce_candidates, scan_count)

        # Desktop notification
        if DESKTOP_NOTIFY:
            names = ", ".join([s['Symbol'] for s in ce_candidates])
            notification.notify(
                title   = "⚡ OISignalFlow — CE Buy Signal!",
                message = f"Stocks: {names}",
                timeout = 10
            )
    else:
        print(f"\n  {YELLOW}  No CE signals this scan. "
              f"Market may be choppy.{RESET}")
        # Send no-signal message every 3rd scan only (avoid spam)
        if scan_count % 3 == 0:
            telegram_no_signal(scan_count)

    # ── Full Results Table ──
    print(f"\n  {BOLD}{CYAN}📊 FULL SCAN TABLE{RESET}")
    print(f"  {'─'*53}")

    if results:
        df = pd.DataFrame(results)
        df = df.sort_values('OI_Chg_%', ascending=False)
        print(df[['Symbol', 'Price', 'Price_Chg_%',
                  'OI_Chg_%', 'Vol_Ratio', 'Signal']
                 ].to_string(index=False))

        ce_df = pd.DataFrame(ce_candidates) \
            if ce_candidates else pd.DataFrame()
        save_to_excel(df, ce_df)

        # Send market summary every 6th scan (~30 minutes)
        if scan_count % 6 == 0:
            telegram_summary(results, scan_count)

    print(f"\n  {CYAN}⏰ Next scan in "
          f"{SCAN_INTERVAL} minutes...{RESET}")
    print(f"  {CYAN}{'═'*53}{RESET}\n")


# ============================================================
# 🕐  MARKET HOURS CHECKER
# ============================================================

def is_market_open():
    """Returns True only during NSE market hours"""
    now = datetime.now()
    h, m = now.hour, now.minute

    # Skip weekends
    if now.weekday() >= 5:
        return False
    # Before 9:15 AM
    if h < 9 or (h == 9 and m < 15):
        return False
    # After 3:30 PM
    if h > 15 or (h == 15 and m > 30):
        return False

    return True


# ============================================================
# ⏰  SCHEDULER JOB
# ============================================================

market_was_open = False

def job():
    global market_was_open
    if is_market_open():
        market_was_open = True
        run_scanner()
    else:
        if market_was_open:
            # Market just closed — send alert once
            telegram_market_closed()
            market_was_open = False
        print(f"  {YELLOW}⏸  Market closed. "
              f"OISignalFlow waiting...{RESET}")


# ============================================================
# 🚀  LAUNCH OISignalFlow
# ============================================================

if __name__ == "__main__":

    # Startup Banner
    print(f"\n{BOLD}{CYAN}")
    print("╔══════════════════════════════════════════════╗")
    print("║                                              ║")
    print("║        ⚡  O I S i g n a l F l o w          ║")
    print("║                                              ║")
    print("║   Free OI Screener for CE Call Buying        ║")
    print("║   Data  : NSE India  (100% Free)             ║")
    print("║   Alerts: Telegram Bot                       ║")
    print("║   Scan  : Every 5 Minutes                    ║")
    print("║   Version: 1.0.0                             ║")
    print("║                                              ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"{RESET}\n")

    # Validate settings from .env
    if "YOUR_BOT_TOKEN_HERE" in TELEGRAM_TOKEN:
        print(f"{RED}⚠️  Please set TELEGRAM_TOKEN in .env file!{RESET}\n")
        exit(1)
    if "YOUR_CHAT_ID_HERE" in TELEGRAM_CHAT_ID:
        print(f"{RED}⚠️  Please set TELEGRAM_CHAT_ID in .env file!{RESET}\n")
        exit(1)

    print(f"{GREEN}✅ OISignalFlow starting...{RESET}\n")
    print(f"  📁 Config   : .env")
    print(f"  📊 Stocks   : {len(FNO_STOCKS)} FNO stocks (from API)")
    print(f"  ⏱ Interval  : Every {SCAN_INTERVAL} minutes")
    print(f"  📈 OI Min   : {OI_CHANGE_MIN}%")
    print(f"  💹 Price Min: {PRICE_CHANGE_MIN}%")
    print(f"  📦 Volume   : {VOLUME_MULT}x normal")
    print(f"  💾 Excel    : {OUTPUT_FILE}")
    print(f"  📱 Telegram : Enabled\n")

    # Send Telegram startup message
    print(f"{CYAN}Testing Telegram connection...{RESET}")
    telegram_startup()

    # First scan immediately
    job()

    # Schedule every 5 minutes
    schedule.every(SCAN_INTERVAL).minutes.do(job)

    print(f"\n{GREEN}✅ OISignalFlow is running! "
          f"Press Ctrl+C to stop.{RESET}\n")

    # Keep running forever
    while True:
        schedule.run_pending()
        time.sleep(30)

# ============================================================
# END OF OISignalFlow v1.0.0
# ============================================================
