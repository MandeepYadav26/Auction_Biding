"""
WonAuction model — records the winner after an auction ends
"""

from sqlalchemy import Column, Integer, Numeric, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base
import enum


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid    = "paid"


class WonAuction(Base):
    __tablename__ = "won_auctions"

    id               = Column(Integer, primary_key=True, index=True)
    auction_id       = Column(Integer, ForeignKey("auctions.id"), unique=True, nullable=False)
    bidder_id        = Column(Integer, ForeignKey("users.id"),    nullable=False)
    winning_amount   = Column(Numeric(12, 2), nullable=False)
    payment_status   = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    delivery_address = Column(String(500), nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    paid_at          = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    auction = relationship("Auction",    back_populates="won_auction")
    bidder  = relationship("User",       back_populates="won_auctions")
    invoice = relationship("Invoice",    back_populates="won_auction", uselist=False)

    def __repr__(self):
        return f"<WonAuction id={self.id} auction_id={self.auction_id} amount={self.winning_amount}>"
