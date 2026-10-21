"""
Auction Bidding Platform — Main Entry Point
Phase 3: FastAPI + SQLAlchemy connected
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from app.config.database import engine, Base, test_connection

# Import all models so SQLAlchemy knows about them
from app.models import (
    User, Category, Auction, Bid,
    ProxyBid, Watchlist, WonAuction, Invoice
)

# Import routers
from app.routes.public import router as public_router
from app.routes.auth import router as auth_router
from app.routes.seller import router as seller_router
from app.routes.admin import router as admin_router

# ── App setup ─────────────────────────────────────────────────

app = FastAPI(
    title="Auction Bidding Platform",
    description="""
## University Semester Project

A full-stack auction platform built with:
- **FastAPI** (Python backend)
- **MySQL** (database)
- **SQLAlchemy** (ORM)
- **JWT** (authentication)

### User Roles
- 🔴 **Admin** — manages platform, approves auctions
- 🟡 **Seller** — creates and manages auction listings
- 🟢 **Bidder** — browses auctions, places bids
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ─────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # In production: replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (uploaded images) ────────────────────────────

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ── Startup event ──────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    """Runs once when the server starts."""
    print("\nAuction Platform starting...")
    # Create tables if they don't exist (safe — won't drop existing data)
    Base.metadata.create_all(bind=engine)
    test_connection()
    print("Server ready at http://127.0.0.1:8000")
    print("API Docs:   http://127.0.0.1:8000/docs\n")


# ── Routes ────────────────────────────────────────────────────

# Public (no auth)
app.include_router(public_router)
app.include_router(auth_router)
app.include_router(seller_router)
app.include_router(admin_router)

# Phase 7+ will add:
# app.include_router(bidder_router)




# ── Root endpoint ──────────────────────────────────────────────

@app.get("/", tags=["Root"])
def root():
    return {
        "message":  "Welcome to Auction Bidding Platform",
        "version":  "1.0.0",
        "status":   "running",
        "docs":     "http://127.0.0.1:8000/docs",
    }


@app.get("/health", tags=["Root"])
def health_check():
    return {"status": "OK"}


# ── Run ────────────────────────────────────────────────────────
# Command: uvicorn main:app --reload
