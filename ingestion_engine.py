# ============================================================
# SANCHAY - UNIFIED DATA INGESTION ENGINE (FREE SOURCES ONLY)
# Fetches live market data and persists to sanchay_local.db
# Runs as a background process alongside api_server.py
# ============================================================

import requests
import time
import sqlite3
import os
import pandas as pd
from datetime import date, datetime
from concurrent.futures import ThreadPoolExecutor

# -------------------------------
# CONFIG
# -------------------------------

# Equity symbols to track (NSE format)
SYMBOLS = ["INFY", "TCS", "RELIANCE", "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "LT"]

# Database path — same DB the API server uses
DB_PATH = os.path.join(os.path.dirname(__file__), 'sanchay_local.db')

# -------------------------------
# DB HELPERS
# -------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn


def get_or_create_asset(conn, symbol, category_name='Equity', risk_level='Medium', liquidity_type='High'):
    """Look up asset_id by symbol. Create asset_master + category records if missing."""
    row = conn.execute(
        'SELECT asset_id FROM asset_master WHERE asset_name = ?', (symbol,)
    ).fetchone()
    if row:
        return row['asset_id']

    # Ensure category exists
    cat = conn.execute(
        'SELECT category_id FROM asset_categories WHERE category_name = ?', (category_name,)
    ).fetchone()
    if cat:
        cat_id = cat['category_id']
    else:
        cur = conn.execute(
            'INSERT INTO asset_categories (category_name) VALUES (?)', (category_name,)
        )
        cat_id = cur.lastrowid

    cur = conn.execute(
        'INSERT INTO asset_master (asset_name, category_id, base_currency, risk_level, liquidity_type) '
        'VALUES (?, ?, ?, ?, ?)',
        (symbol, cat_id, 'INR', risk_level, liquidity_type)
    )
    return cur.lastrowid


def save_asset_price(symbol, price, price_date, source='NSE', category='Equity'):
    """Upsert a price record for a symbol into asset_prices."""
    try:
        with get_db() as conn:
            asset_id = get_or_create_asset(conn, symbol, category_name=category)
            conn.execute('''
                INSERT INTO asset_prices (asset_id, price, price_date, source)
                VALUES (?, ?, ?, ?)
            ''', (asset_id, float(price), price_date, source))
            conn.commit()
    except Exception as e:
        print(f'[DB ERROR] save_asset_price({symbol}): {e}')


def save_fx_rate(from_currency, rate, rate_date, source='RBI'):
    """Upsert FX rate into fx_rates_daily."""
    try:
        with get_db() as conn:
            # Check if active record exists for this date/currency pair
            existing = conn.execute('''
                SELECT fx_id FROM fx_rates_daily
                WHERE date = ? AND from_currency = ? AND to_currency = 'INR' AND is_active = 1
            ''', (rate_date, from_currency)).fetchone()

            if existing:
                conn.execute('''
                    UPDATE fx_rates_daily
                    SET rate = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE fx_id = ?
                ''', (float(rate), existing['fx_id']))
            else:
                conn.execute('''
                    INSERT INTO fx_rates_daily
                    (date, from_currency, to_currency, rate, version, is_active, source)
                    VALUES (?, ?, 'INR', ?, 1, 1, ?)
                ''', (rate_date, from_currency, float(rate), source))

            conn.commit()
            print(f'[FX] {from_currency}/INR = {rate} ({rate_date})')
    except Exception as e:
        print(f'[DB ERROR] save_fx_rate({from_currency}): {e}')


def log_ingestion(run_date, status, records_inserted, error_message=None):
    try:
        with get_db() as conn:
            conn.execute('''
                INSERT INTO fx_ingestion_logs (run_date, status, records_inserted, error_message)
                VALUES (?, ?, ?, ?)
            ''', (run_date, status, records_inserted, error_message))
            conn.commit()
    except Exception:
        pass


# -------------------------------
# BASE SCHEDULER ENGINE
# -------------------------------

TASKS = []
executor = ThreadPoolExecutor(max_workers=10)


def register_task(func, interval_sec):
    TASKS.append({
        "func": func,
        "interval": interval_sec,
        "last_run": 0
    })


def scheduler():
    print('[SANCHAY INGESTION] Scheduler started.')
    while True:
        now = time.time()
        for task in TASKS:
            if now - task["last_run"] >= task["interval"]:
                task["last_run"] = now
                executor.submit(task["func"])
        time.sleep(5)


# ============================================================
# 1. NSE ADAPTER (PRIMARY PRICE SOURCE)
# ============================================================

class NSEAdapter:

    BASE = "https://www.nseindia.com"
    QUOTE = "https://www.nseindia.com/api/quote-equity"

    def __init__(self):
        self.session = requests.Session()
        self._init_session()

    def _init_session(self):
        """Prime the NSE session cookie."""
        try:
            self.session.get(
                self.BASE,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
        except Exception as e:
            print(f'[NSE] Session init failed: {e}')

    def get_price(self, symbol):
        url = f"{self.QUOTE}?symbol={symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": self.BASE,
            "Accept": "application/json"
        }
        r = self.session.get(url, headers=headers, timeout=8)
        r.raise_for_status()
        data = r.json()
        return {
            "symbol": symbol,
            "price": data["priceInfo"]["lastPrice"],
            "timestamp": data["priceInfo"].get("lastUpdateTime", str(date.today()))
        }


# ============================================================
# 2. YAHOO FALLBACK ADAPTER
# ============================================================

class YahooAdapter:

    QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"
    SUMMARY_URL = "https://query2.finance.yahoo.com/v10/finance/quoteSummary"

    def get_price(self, symbol):
        r = requests.get(
            self.QUOTE_URL,
            params={"symbols": f"{symbol}.NS"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8
        )
        r.raise_for_status()
        data = r.json()["quoteResponse"]["result"][0]
        return {
            "symbol": symbol,
            "price": data["regularMarketPrice"],
            "timestamp": str(date.today())
        }

    def get_fundamentals(self, symbol):
        url = f"{self.SUMMARY_URL}/{symbol}.NS"
        params = {"modules": "financialData,defaultKeyStatistics"}
        r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        r.raise_for_status()
        data = r.json()["quoteSummary"]["result"][0]
        return {
            "symbol": symbol,
            "pe": data["defaultKeyStatistics"].get("trailingPE", {}).get("raw"),
            "eps": data["defaultKeyStatistics"].get("trailingEps", {}).get("raw"),
            "market_cap": data["financialData"].get("marketCap", {}).get("raw")
        }


# ============================================================
# 3. PRICE PIPELINE (NSE PRIMARY → YAHOO FALLBACK)
# ============================================================

nse = NSEAdapter()
yahoo = YahooAdapter()


def fetch_stock_prices():
    """Fetch equity prices every 30 minutes and persist to asset_prices."""
    print('[PRICE] Starting stock price fetch...')
    count = 0
    today = str(date.today())

    for symbol in SYMBOLS:
        try:
            data = nse.get_price(symbol)
        except Exception as nse_err:
            print(f'[NSE FAIL] {symbol}: {nse_err}. Trying Yahoo...')
            try:
                data = yahoo.get_price(symbol)
                data['source'] = 'YAHOO'
            except Exception as yahoo_err:
                print(f'[YAHOO FAIL] {symbol}: {yahoo_err}')
                continue

        price = data['price']
        source = data.get('source', 'NSE')
        save_asset_price(symbol, price, today, source=source, category='Equity')
        print(f'[PRICE] {symbol}: ₹{price} ({source})')
        count += 1
        time.sleep(1)  # Polite delay between requests

    print(f'[PRICE] Done. {count}/{len(SYMBOLS)} prices updated.')


# ============================================================
# 4. FUNDAMENTALS PIPELINE (YAHOO — DAILY)
# ============================================================

def fetch_fundamentals():
    """Fetch fundamentals daily and log to console (extend to DB if needed)."""
    print('[FUNDAMENTALS] Starting fundamentals fetch...')
    for symbol in SYMBOLS:
        try:
            result = yahoo.get_fundamentals(symbol)
            print(f'[FUNDAMENTALS] {symbol}: PE={result["pe"]} | EPS={result["eps"]} | MCap={result["market_cap"]}')
            # TODO: Persist to extended asset_master columns when schema is extended
            time.sleep(1)
        except Exception as e:
            print(f'[FUNDAMENTALS FAIL] {symbol}: {e}')


# ============================================================
# 5. CORPORATE ACTIONS (NSE — EVERY 2 HOURS)
# ============================================================

def fetch_corporate_actions():
    """Fetch corporate actions from NSE and log."""
    print('[CORP ACTIONS] Fetching corporate actions...')
    try:
        url = "https://www.nseindia.com/api/corporates-corporateActions?index=equities"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.nseindia.com"
        }
        r = nse.session.get(url, headers=headers, timeout=8)
        r.raise_for_status()
        data = r.json().get("data", [])
        actions = [
            {"symbol": x.get("symbol"), "action": x.get("purpose"), "ex_date": x.get("exDate")}
            for x in data[:10]  # top 10
        ]
        print(f'[CORP ACTIONS] {len(actions)} actions fetched. Sample: {actions[:2]}')
    except Exception as e:
        print(f'[CORP ACTIONS FAIL]: {e}')


# ============================================================
# 6. AMFI NAV PIPELINE (MUTUAL FUND NAVs — DAILY)
# ============================================================

def fetch_nav():
    """Fetch all MF NAVs from AMFI and persist to asset_prices."""
    print('[NAV] Fetching AMFI NAVs...')
    try:
        url = "https://www.amfiindia.com/spages/NAVAll.txt"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        lines = r.text.split("\n")

        nav_data = []
        for line in lines:
            parts = line.strip().split(";")
            if len(parts) >= 6:
                try:
                    nav_val = float(parts[4])
                    nav_date = parts[5].strip()
                    scheme_name = parts[3].strip()[:80]  # Truncate for DB
                    if nav_val > 0 and nav_date and scheme_name:
                        nav_data.append({
                            "scheme_code": parts[0].strip(),
                            "scheme_name": scheme_name,
                            "nav": nav_val,
                            "date": nav_date
                        })
                except (ValueError, IndexError):
                    continue

        # Persist top 100 schemes to DB (full ingestion would be thousands)
        count = 0
        for item in nav_data[:100]:
            save_asset_price(
                item['scheme_name'], item['nav'],
                item['date'], source='AMFI', category='Mutual Fund'
            )
            count += 1

        print(f'[NAV] {count} NAV records persisted. Total available: {len(nav_data)}')
        log_ingestion(str(date.today()), 'success', count)

    except Exception as e:
        print(f'[NAV FAIL]: {e}')
        log_ingestion(str(date.today()), 'error', 0, str(e))


# ============================================================
# 7. MF PORTFOLIO (PDF PARSER — ON DEMAND)
# ============================================================

def parse_mf_portfolio(pdf_path):
    """Parse MF portfolio PDF (CAS statement) using tabula."""
    try:
        import tabula
        tables = tabula.read_pdf(pdf_path, pages="all")
        holdings = []
        for table in tables:
            for _, row in table.iterrows():
                holdings.append({
                    "stock": row.get("Name"),
                    "allocation": row.get("% to Net Assets")
                })
        print(f'[MF PARSER] {len(holdings)} holdings extracted from {pdf_path}')
        return holdings
    except ImportError:
        print('[MF PARSER] tabula-py not installed. Run: pip install tabula-py')
        return []
    except Exception as e:
        print(f'[MF PARSER FAIL]: {e}')
        return []


# ============================================================
# 8. RBI EXCHANGE RATES (DAILY)
# ============================================================

def fetch_rbi_rates():
    """Fetch RBI reference exchange rates and persist to fx_rates_daily."""
    print('[RBI FX] Fetching RBI exchange rates...')
    try:
        url = "https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx"
        tables = pd.read_html(url, flavor='lxml')
        if not tables:
            raise ValueError("No tables found on RBI page")

        df = tables[0]
        today = str(date.today())

        # Common RBI table columns: Date | USD | EUR | GBP | JPY (per 100 ¥)
        currency_map = {
            'USD': 'USD',
            'EUR': 'EUR',
            'GBP': 'GBP',
            'JPY (Per 100 Yen)': 'JPY'
        }

        count = 0
        for col, currency in currency_map.items():
            matching = [c for c in df.columns if col in str(c)]
            if matching:
                try:
                    rate_val = float(str(df[matching[0]].iloc[0]).replace(',', ''))
                    if currency == 'JPY':
                        rate_val = rate_val / 100  # Convert per-100 to per-1
                    save_fx_rate(currency, rate_val, today, source='RBI')
                    count += 1
                except (ValueError, IndexError):
                    pass

        print(f'[RBI FX] {count} currency rates persisted.')
        log_ingestion(today, 'fx_success', count)

    except Exception as e:
        print(f'[RBI FX FAIL]: {e}')
        log_ingestion(str(date.today()), 'fx_error', 0, str(e))


# ============================================================
# TASK REGISTRATION (FREQUENCY CONTROL)
# ============================================================

# High frequency (intraday)
register_task(fetch_stock_prices, 1800)       # Every 30 minutes
register_task(fetch_corporate_actions, 7200)  # Every 2 hours

# Low frequency (daily)
register_task(fetch_fundamentals, 86400)      # Once per day
register_task(fetch_nav, 86400)               # Once per day
register_task(fetch_rbi_rates, 86400)         # Once per day


# ============================================================
# START ENGINE
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SANCHAY INGESTION ENGINE — Starting")
    print(f"Database: {DB_PATH}")
    print(f"Tracking {len(SYMBOLS)} equity symbols")
    print("=" * 60)

    # Run an immediate fetch on startup
    print("[STARTUP] Running initial data fetch...")
    fetch_stock_prices()
    fetch_nav()
    fetch_rbi_rates()
    print("[STARTUP] Initial fetch complete. Starting scheduler...")

    scheduler()
