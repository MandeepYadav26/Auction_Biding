"""
Pydantic schemas for Admin operations and statistics
"""

from pydantic import BaseModel
from typing import Optional


class AdminStats(BaseModel):
    """Platform statistics for Admin Dashboard"""
    total_users:        int
    total_sellers:      int
    total_bidders:      int
    total_auctions:     int
    active_auctions:    int
    pending_auctions:   int
    ended_auctions:     int
    cancelled_auctions: int


class UserStatusUpdate(BaseModel):
    """Admin updating user active status"""
    is_active: bool
