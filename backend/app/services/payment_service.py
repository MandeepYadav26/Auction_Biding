"""
Phase 12 — Payment + Invoice Service

Flow:
  1. Winner submits delivery address → payment simulated → PaymentStatus = 'paid'
  2. Invoice auto-generated with unique number (INV-YYYY-NNNN)
  3. Invoice details available for view/download

No real payment gateway — this is a university project simulation.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.won_auction import WonAuction, PaymentStatus
from app.models.invoice     import Invoice

logger = logging.getLogger(__name__)


# ── Invoice Number Generator ───────────────────────────────────

def _generate_invoice_number(db: Session) -> str:
    """
    Generate a unique invoice number: INV-YYYY-NNNN
    e.g. INV-2026-0001, INV-2026-0002 ...
    """
    year = datetime.now(timezone.utc).year
    # Count existing invoices this year to get the next sequence number
    prefix = f"INV-{year}-"
    count = (
        db.query(Invoice)
        .filter(Invoice.invoice_number.like(f"{prefix}%"))
        .count()
    )
    seq = count + 1
    return f"{prefix}{seq:04d}"


# ── Payment Processing ─────────────────────────────────────────

def process_payment(
    db: Session,
    won_auction_id: int,
    bidder_id: int,
    delivery_address: str,
) -> WonAuction:
    """
    Simulate payment for a won auction.
    - Validates ownership and pending status
    - Marks payment as 'paid' with timestamp
    - Auto-generates invoice
    Returns updated WonAuction.
    """
    # 1. Fetch the won auction
    won = (
        db.query(WonAuction)
        .filter(
            WonAuction.id == won_auction_id,
            WonAuction.bidder_id == bidder_id,
        )
        .first()
    )
    if not won:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Won auction not found or does not belong to you.",
        )

    # 2. Must be pending — cannot pay twice
    if won.payment_status == PaymentStatus.paid:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Payment has already been completed for this auction.",
        )

    # 3. Delivery address must not be empty
    delivery_address = delivery_address.strip()
    if not delivery_address:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Delivery address cannot be empty.",
        )

    # 4. Mark as paid
    won.payment_status   = PaymentStatus.paid
    won.delivery_address = delivery_address
    won.paid_at          = datetime.now(timezone.utc)

    # 5. Generate invoice (only if one doesn't already exist)
    if won.invoice is None:
        invoice_number = _generate_invoice_number(db)
        invoice = Invoice(
            won_auction_id=won.id,
            invoice_number=invoice_number,
            amount=Decimal(str(won.winning_amount)),
        )
        db.add(invoice)
        logger.info(
            "Invoice %s generated for won_auction_id=%d (₹%s)",
            invoice_number, won.id, won.winning_amount
        )

    db.commit()
    db.refresh(won)
    return won


# ── Invoice Retrieval ──────────────────────────────────────────

def get_invoice(
    db: Session,
    won_auction_id: int,
    bidder_id: int,
) -> Optional[Invoice]:
    """
    Fetch the invoice for a won auction.
    Returns None if not yet paid (invoice doesn't exist yet).
    """
    won = (
        db.query(WonAuction)
        .filter(
            WonAuction.id == won_auction_id,
            WonAuction.bidder_id == bidder_id,
        )
        .first()
    )
    if not won:
        return None
    return won.invoice
