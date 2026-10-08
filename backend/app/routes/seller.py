"""
Seller routes: Create, Update, and Manage Auctions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.models.user import User, UserRole
from app.models.auction import AuctionStatus
from app.schemas.auction import AuctionCreate, AuctionUpdate, AuctionDetail, AuctionListItem
from app.services.auction_crud import (
    create_auction, 
    get_seller_auctions, 
    update_auction, 
    get_auction_by_id
)
from app.utils.auth_dependency import require_role

# Prefix all routes with /seller
router = APIRouter(prefix="/seller", tags=["Seller"])

# Dependency that ensures only sellers can access these routes
get_seller_user = require_role(UserRole.seller)


@router.post("/auctions", response_model=AuctionDetail, status_code=status.HTTP_201_CREATED)
def create_new_auction(
    auction_data: AuctionCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_seller_user)
):
    """
    Seller creates a new auction.
    The auction is initially set to 'pending' status for admin approval.
    """
    return create_auction(db=db, seller_id=current_user.id, data=auction_data)


@router.get("/auctions", response_model=List[AuctionListItem])
def get_my_auctions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_seller_user)
):
    """
    Get all auctions created by the currently logged-in seller.
    """
    return get_seller_auctions(db=db, seller_id=current_user.id)


@router.put("/auctions/{auction_id}", response_model=AuctionDetail)
def update_existing_auction(
    auction_id: int, 
    auction_data: AuctionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_seller_user)
):
    """
    Update an existing auction.
    Sellers can only update their own auctions, and usually only before they are 'active'.
    """
    auction = get_auction_by_id(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found.")
    
    if auction.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not the owner of this auction.")
        
    # Prevent updating if bidding has started (active/ended/sold)
    if auction.status not in [AuctionStatus.draft, AuctionStatus.pending]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot update auction in '{auction.status}' status."
        )
        
    updated_auction = update_auction(db=db, auction_id=auction_id, data=auction_data)
    return updated_auction
