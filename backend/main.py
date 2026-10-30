"""
Auction Bidding Platform — Main Entry Point
Phase 9: Auction Ending Scheduler added
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

from app.config.database import engine, Base, test_connection

# Import all models so SQLAlchemy knows about them
from app.models import (
    User, Category, Auction, Bid,
    ProxyBid, Watchlist, WonAuction, Invoice
)

# Import routers
from app.routes.public  import router as public_router
from app.routes.auth    import router as auth_router
from app.routes.seller  import router as seller_router
from app.routes.admin   import router as admin_router
from app.routes.bidding import router as bidding_router

# Phase 9: background scheduler
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Lifespan (replaces deprecated @app.on_event) ──────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    # ── Startup ────────────────────────────────────────────────
    logger.info("Auction Platform starting...")
    Base.metadata.create_all(bind=engine)   # create tables if missing
    test_connection()
    start_scheduler()                        # Phase 9: start background closer
    logger.info("Server ready at http://127.0.0.1:8000  |  Docs: /docs")
    yield
    # ── Shutdown ───────────────────────────────────────────────
    stop_scheduler()
    logger.info("Auction Platform shut down cleanly.")


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
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (uploaded images) ────────────────────────────

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ── Routes ────────────────────────────────────────────────────

app.include_router(public_router)
app.include_router(auth_router)
app.include_router(seller_router)
app.include_router(admin_router)
app.include_router(bidding_router)

# ── Root endpoints ─────────────────────────────────────────────

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

