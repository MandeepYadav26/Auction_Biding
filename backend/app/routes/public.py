"""
Public auction routes — no login required
GET  /auctions            → browse all active auctions
GET  /auctions/{id}       → auction detail
GET  /auctions/ending-soon → homepage "ending soon" section
GET  /categories          → list all categories
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config.database      import get_db
from app.models.auction       import AuctionStatus
from app.schemas.auction      import AuctionListItem, AuctionDetail
from app.schemas.category     import CategoryResponse
from app.services.auction_crud import (
    get_all_auctions, get_auction_by_id,
    get_ending_soon_auctions
)
from app.services.category_crud import get_all_categories

router = APIRouter(tags=["Public"])


# ── Auctions ──────────────────────────────────────────────────

@router.get("/auctions", response_model=List[AuctionListItem])
def browse_auctions(
    category_id: Optional[int] = Query(None, description="Filter by category"),
    search:      Optional[str] = Query(None, description="Search by title"),
    skip:        int           = Query(0,    ge=0),
    limit:       int           = Query(20,   ge=1, le=100),
    db:          Session       = Depends(get_db),
):
    """
    Browse all active auctions.
    Supports: ?category_id=1  ?search=laptop  ?skip=0&limit=20
    """
    auctions = get_all_auctions(
        db,
        status=AuctionStatus.active,
        category_id=category_id,
        search=search,
        skip=skip,
        limit=limit,
    )
    return auctions


@router.get("/auctions/ending-soon", response_model=List[AuctionListItem])
def ending_soon(db: Session = Depends(get_db)):
    """Active auctions ending soonest — for homepage."""
    return get_ending_soon_auctions(db, limit=6)


@router.get("/auctions/{auction_id}", response_model=AuctionDetail)
def auction_detail(auction_id: int, db: Session = Depends(get_db)):
    """Full auction details including category info."""
    auction = get_auction_by_id(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    return auction


# ── Categories ────────────────────────────────────────────────

@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    """All active categories — used to populate dropdowns."""
    return get_all_categories(db, active_only=True)
