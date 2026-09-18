"""
SANCHAY Database Module
Manages SQLite connections and schema initialization.
Production-ready with proper path handling.
"""

import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path

# Get the data directory - one level up from backend
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "sanchay_local.db"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection(path=None):
    """
    Context manager for database connections.
    
    Args:
        path: Optional custom database path (defaults to DB_PATH)
        
    Yields:
        sqlite3.Connection with Row factory enabled
    """
    if path is None:
        path = DB_PATH
        
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON;')
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database(path=None):
    """
    Initialize database schema with all required tables.
    Safe to run multiple times (uses CREATE TABLE IF NOT EXISTS).
    
    Args:
        path: Optional custom database path (defaults to DB_PATH)
    """
    if path is None:
        path = DB_PATH
        
    with get_connection(path) as conn:
        # Users & Authentication
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT,
                role TEXT CHECK(role IN ('advisor','client','admin')),
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Advisors
        conn.execute('''
            CREATE TABLE IF NOT EXISTS advisors (
                advisor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                firm_name TEXT,
                license_no TEXT,
                experience_years INTEGER
            );
        ''')

        # Clients
        conn.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                client_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                advisor_id INTEGER REFERENCES advisors(advisor_id) ON DELETE SET NULL,
                dob DATE,
                income NUMERIC,
                net_worth NUMERIC,
                occupation TEXT,
                onboarding_date DATE
            );
        ''')

        # Goals
        conn.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
                goal_type TEXT,
                target_amount NUMERIC,
                current_corpus NUMERIC,
                target_date DATE,
                monthly_sip NUMERIC,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Transactions
        conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
                asset_id INTEGER,
                transaction_type TEXT,
                quantity NUMERIC,
                price NUMERIC,
                amount NUMERIC,
                transaction_date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Asset Master
        conn.execute('''
            CREATE TABLE IF NOT EXISTS asset_master (
                asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_name TEXT NOT NULL UNIQUE,
                asset_type TEXT,
                category_id INTEGER,
                risk_level TEXT,
                liquidity_type TEXT
            );
        ''')

        # Asset Categories
        conn.execute('''
            CREATE TABLE IF NOT EXISTS asset_categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT NOT NULL UNIQUE,
                description TEXT
            );
        ''')

        # Price History
        conn.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                price_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL REFERENCES asset_master(asset_id),
                price NUMERIC,
                market_date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        print(f"✓ Database initialized at: {path}")


if __name__ == '__main__':
    init_database()
