"""
Database initialization script
Run this ONCE to create all tables in MySQL.

Usage:
    python init_db.py
"""

import sys
import os

# Add backend folder to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.database import engine, Base, test_connection

# Import ALL models so Base knows about all tables
from app.models import (
    User, Category, Auction, Bid,
    ProxyBid, Watchlist, WonAuction, Invoice
)


def init_db():
    print("=" * 50)
    print("  Auction Platform — Database Initializer")
    print("=" * 50)

    # Step 1: Test connection
    print("\n[1] Testing MySQL connection...")
    if not test_connection():
        print("ERROR: Cannot connect to MySQL. Check your .env file.")
        sys.exit(1)

    # Step 2: Create tables
    print("\n[2] Creating tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("  Tables created successfully!")
    except Exception as e:
        print(f"  ERROR creating tables: {e}")
        sys.exit(1)

    # Step 3: Show tables created
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n[3] Tables in 'auction_platform' database:")
    for t in tables:
        print(f"      {t}")

    print("\nDatabase setup complete!")
    print("=" * 50)


if __name__ == "__main__":
    init_db()
