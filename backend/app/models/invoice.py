"""
Invoice model — generated after payment is made for a won auction
"""

from sqlalchemy import Column, Integer, Numeric, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id             = Column(Integer, primary_key=True, index=True)
    won_auction_id = Column(Integer, ForeignKey("won_auctions.id"), unique=True, nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False)  # e.g. INV-2024-0001
    amount         = Column(Numeric(12, 2), nullable=False)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    won_auction = relationship("WonAuction", back_populates="invoice")

    def __repr__(self):
        return f"<Invoice id={self.id} number={self.invoice_number} amount={self.amount}>"
