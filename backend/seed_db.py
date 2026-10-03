"""
Seed script — inserts default data into the database.
Run ONCE after init_db.py

Inserts:
  - Default categories (Electronics, Books, etc.)
  - One Admin user

Usage:
    python seed_db.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.database import SessionLocal
from app.models.user     import User, UserRole
from app.models.category import Category
import bcrypt


def hash_password(plain: str) -> str:
    """Hash a password using bcrypt directly."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


DEFAULT_CATEGORIES = [
    {"name": "Electronics",   "description": "Phones, laptops, gadgets"},
    {"name": "Books",         "description": "Textbooks, novels, magazines"},
    {"name": "Clothing",      "description": "Clothes, shoes, accessories"},
    {"name": "Furniture",     "description": "Home and office furniture"},
    {"name": "Sports",        "description": "Sports equipment and gear"},
    {"name": "Vehicles",      "description": "Cars, bikes, scooters"},
    {"name": "Art & Crafts",  "description": "Paintings, handmade items"},
    {"name": "Other",         "description": "Miscellaneous items"},
]

ADMIN_USER = {
    "name":     "Admin",
    "email":    "admin@auction.com",
    "password": "Admin@123",          # plain text — will be hashed below
    "role":     UserRole.admin,
}


def seed():
    print("=" * 50)
    print("  Auction Platform — Seed Data")
    print("=" * 50)

    db = SessionLocal()
    try:
        # --- Categories ---
        print("\n[1] Seeding categories...")
        added = 0
        for cat_data in DEFAULT_CATEGORIES:
            existing = db.query(Category).filter_by(name=cat_data["name"]).first()
            if not existing:
                cat = Category(**cat_data)
                db.add(cat)
                added += 1
                print(f"    + {cat_data['name']}")
            else:
                print(f"    ~ {cat_data['name']} (already exists)")
        db.commit()
        print(f"  Categories: {added} added.")

        # --- Admin user ---
        print("\n[2] Seeding admin user...")
        existing_admin = db.query(User).filter_by(email=ADMIN_USER["email"]).first()
        if not existing_admin:
            hashed_pw = hash_password(ADMIN_USER["password"])
            admin = User(
                name=ADMIN_USER["name"],
                email=ADMIN_USER["email"],
                password=hashed_pw,
                role=ADMIN_USER["role"],
            )
            db.add(admin)
            db.commit()
            print(f"    + Admin created: {ADMIN_USER['email']} / {ADMIN_USER['password']}")
        else:
            print(f"    ~ Admin already exists: {ADMIN_USER['email']}")

        print("\nSeed complete!")
        print("=" * 50)
        print(f"  Admin login -> email: {ADMIN_USER['email']}")
        print(f"                 password: {ADMIN_USER['password']}")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
