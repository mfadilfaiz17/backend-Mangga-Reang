from fastapi import HTTPException
from sqlalchemy.orm import Session

from crud import inventory, logistics, rfq
from models.domain_models import LogisticsMilestone, LogisticsTracking, RfqStatus, RfqTransaction
from schemas.rfq import RfqCreate


def create_rfq(db: Session, buyer_id: int, payload: RfqCreate) -> RfqTransaction:
    stock = inventory.get(db, payload.id_mangga)
    if stock is None or not stock.is_active or stock.tonase_tersedia <= 0:
        raise HTTPException(status_code=404, detail="Inventory not found or unavailable")
    if payload.tonase_diminta > stock.tonase_tersedia:
        raise HTTPException(status_code=409, detail="Requested tonnage exceeds available stock")
    order = RfqTransaction(
        id_buyer=buyer_id,
        id_mangga=stock.id,
        tonase_diminta=payload.tonase_diminta,
        status_nego=RfqStatus.PENDING,
        total_harga=payload.tonase_diminta * stock.harga_per_ton,
    )
    return rfq.create(db, order)


def approve_rfq(db: Session, rfq_id: int, admin_id: int) -> RfqTransaction:
    order = rfq.get(db, rfq_id, for_update=True)
    if order is None:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if order.status_nego is not RfqStatus.PENDING:
        raise HTTPException(status_code=409, detail="RFQ is no longer pending")
    stock = inventory.get(db, order.id_mangga, for_update=True)
    if stock is None or not stock.is_active or stock.tonase_tersedia < order.tonase_diminta:
        raise HTTPException(status_code=409, detail="Insufficient inventory")
    stock.tonase_tersedia -= order.tonase_diminta
    order.status_nego = RfqStatus.APPROVED
    logistics.create(
        db,
        LogisticsTracking(
            id_rfq=order.id,
            status_milestone=LogisticsMilestone.DIPROSES_PETANI,
            updated_by=admin_id,
        ),
    )
    db.flush()
    return order
