#!/usr/bin/env python3
"""
SANCHAY Database Initialization Script
Standalone script to initialize the database from scratch.

Usage:
    python init_local_db.py                  # Uses default path
    python init_local_db.py --fresh         # Deletes existing DB first
"""

import sys
import os
from pathlib import Path
import argparse

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))
from sanchay_db import init_database, DB_PATH


def main():
    parser = argparse.ArgumentParser(
        description='Initialize SANCHAY database'
    )
    parser.add_argument(
        '--fresh',
        action='store_true',
        help='Delete existing database before initialization'
    )
    parser.add_argument(
        '--path',
        type=str,
        default=None,
        help='Custom database path'
    )
    
    args = parser.parse_args()
    db_path = args.path or DB_PATH
    
    print("=" * 60)
    print("SANCHAY DATABASE INITIALIZATION")
    print("=" * 60)
    print(f"Database Path: {db_path}")
    
    if args.fresh and os.path.exists(db_path):
        print("\n[FRESH START] Removing existing database...")
        try:
            os.remove(db_path)
            print("✓ Existing database removed")
        except Exception as e:
            print(f"✗ Failed to remove database: {e}")
            sys.exit(1)
    
    print("\nInitializing database schema...")
    try:
        init_database(db_path)
        print("✓ Database initialized successfully")
        print(f"✓ Location: {db_path}")
        print("\n✓ SANCHAY database is ready to use!")
        return 0
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
