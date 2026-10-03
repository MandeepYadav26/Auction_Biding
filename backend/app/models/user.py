"""
User model — stores all users (Admin, Seller, Bidder)
"""

from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    seller = "seller"
    bidder = "bidder"


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, nullable=False, index=True)
    password   = Column(String(255), nullable=False)          # hashed
    role       = Column(Enum(UserRole), nullable=False)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    auctions    = relationship("Auction", back_populates="seller", foreign_keys="Auction.seller_id")
    bids        = relationship("Bid",     back_populates="bidder")
    proxy_bids  = relationship("ProxyBid", back_populates="bidder")
    watchlist   = relationship("Watchlist", back_populates="bidder")
    won_auctions = relationship("WonAuction", back_populates="bidder")

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"
