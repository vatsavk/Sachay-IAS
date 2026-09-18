"""
SANCHAY - Data Ingestion Engine
Fetches live market data from free sources and persists to database.
Runs as a background process alongside api_server.py.
"""

import requests
import time
import sqlite3
import os
import pandas as pd
from datetime import date, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from sanchay_db import get_connection, DB_PATH

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

# Equity symbols to track (NSE format)
SYMBOLS = ["INFY", "TCS", "RELIANCE", "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "LT"]

# Refresh interval in seconds (3600 = 1 hour)
REFRESH_INTERVAL = int(os.getenv('DATA_REFRESH_INTERVAL', 3600))

# API endpoints for free data
YFINANCE_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/"
NSE_PRICE_API = "https://www.nseindia.com/api/quote-equity?symbol="

# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def ensure_categories():
    """Ensure standard asset categories exist"""
    categories = [
        ('Equity', 'Indian equity shares'),
        ('Debt', 'Bond and debt instruments'),
        ('MutualFund', 'Mutual fund schemes'),
        ('Gold', 'Gold and precious metals'),
    ]
    
    with get_connection() as conn:
        for cat_name, description in categories:
            exists = conn.execute(
                'SELECT category_id FROM asset_categories WHERE category_name = ?',
                (cat_name,)
            ).fetchone()
            if not exists:
                conn.execute(
                    'INSERT INTO asset_categories (category_name, description) VALUES (?, ?)',
                    (cat_name, description)
                )
        conn.commit()


def get_or_create_asset(symbol, asset_type='Equity', category_name='Equity', 
                       risk_level='Medium', liquidity_type='High'):
    """
    Look up asset by symbol or create if missing.
    
    Args:
        symbol: Asset symbol (e.g., 'INFY')
        asset_type: Type of asset
        category_name: Category name
        risk_level: Risk classification
        liquidity_type: Liquidity classification
        
    Returns:
        int: asset_id
    """
    with get_connection() as conn:
        # Check if asset exists
        row = conn.execute(
            'SELECT asset_id FROM asset_master WHERE asset_name = ?',
            (symbol,)
        ).fetchone()
        
        if row:
            return row['asset_id']
        
        # Ensure category exists
        cat = conn.execute(
            'SELECT category_id FROM asset_categories WHERE category_name = ?',
            (category_name,)
        ).fetchone()
        
        if not cat:
            raise ValueError(f"Category {category_name} not found. Run ensure_categories() first.")
        
        cat_id = cat['category_id']
        
        # Create new asset
        conn.execute('''
            INSERT INTO asset_master (asset_name, asset_type, category_id, risk_level, liquidity_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (symbol, asset_type, cat_id, risk_level, liquidity_type))
        
        conn.commit()
        
        # Return new asset_id
        row = conn.execute(
            'SELECT asset_id FROM asset_master WHERE asset_name = ?',
            (symbol,)
        ).fetchone()
        
        return row['asset_id']


def fetch_price(symbol):
    """
    Fetch current price for a symbol from Yahoo Finance.
    
    Args:
        symbol: Stock symbol (NSE format, e.g., 'INFY.NS')
        
    Returns:
        dict: {symbol, price, date} or None if fetch fails
    """
    try:
        full_symbol = f"{symbol}.NS" if not symbol.endswith('.NS') else symbol
        response = requests.get(
            f"{YFINANCE_BASE}{full_symbol}",
            timeout=5,
            params={'interval': '1d', 'range': '1d'}
        )
        response.raise_for_status()
        
        data = response.json()
        if 'chart' in data and data['chart']['result']:
            result = data['chart']['result'][0]
            latest_close = result['indicators']['quote'][0]['close'][-1]
            timestamp = result['timestamp'][-1]
            
            return {
                'symbol': symbol,
                'price': latest_close,
                'date': datetime.fromtimestamp(timestamp).date()
            }
    except Exception as e:
        print(f"[WARNING] Failed to fetch price for {symbol}: {e}")
    
    return None


def store_price(symbol, price, market_date):
    """
    Store price in database.
    
    Args:
        symbol: Asset symbol
        price: Price value
        market_date: Date of price
    """
    try:
        asset_id = get_or_create_asset(symbol)
        
        with get_connection() as conn:
            # Check if price already exists for this date
            existing = conn.execute('''
                SELECT price_id FROM price_history 
                WHERE asset_id = ? AND market_date = ?
            ''', (asset_id, market_date)).fetchone()
            
            if existing:
                # Update existing
                conn.execute('''
                    UPDATE price_history SET price = ? WHERE price_id = ?
                ''', (price, existing['price_id']))
            else:
                # Insert new
                conn.execute('''
                    INSERT INTO price_history (asset_id, price, market_date)
                    VALUES (?, ?, ?)
                ''', (asset_id, price, market_date))
            
            conn.commit()
            print(f"✓ Stored price: {symbol} @ ₹{price} on {market_date}")
    except Exception as e:
        print(f"[ERROR] Failed to store price for {symbol}: {e}")


def ingest_prices():
    """
    Fetch prices for all symbols and store in database.
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting price ingestion...")
    
    ensure_categories()
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(fetch_price, symbol) for symbol in SYMBOLS]
        
        for future in futures:
            result = future.result()
            if result:
                store_price(result['symbol'], result['price'], result['date'])
    
    print("✓ Price ingestion completed")


def run_continuous_ingestion():
    """
    Run continuous data ingestion at regular intervals.
    """
    print(f"[INGESTION ENGINE] Started with {REFRESH_INTERVAL}s refresh interval")
    print(f"[INGESTION ENGINE] Database: {DB_PATH}")
    
    while True:
        try:
            ingest_prices()
        except Exception as e:
            print(f"[ERROR] Ingestion failed: {e}")
        
        print(f"[INGESTION ENGINE] Sleeping for {REFRESH_INTERVAL} seconds...")
        time.sleep(REFRESH_INTERVAL)


if __name__ == '__main__':
    # One-time ingestion if run directly
    ingest_prices()
    print("\n✓ Direct ingestion completed")
