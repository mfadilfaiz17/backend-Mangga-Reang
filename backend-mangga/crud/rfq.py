from sqlalchemy import select
from sqlalchemy.orm import Session

from models.domain_models import RfqTransaction


def get(db: Session, rfq_id: int, *, for_update: bool = False) -> RfqTransaction | None:
    query = select(RfqTransaction).where(RfqTransaction.id == rfq_id)
    if for_update:
        query = query.with_for_update()
    return db.scalar(query)


def list_for_buyer(db: Session, buyer_id: int) -> list[RfqTransaction]:
    return list(
        db.scalars(
            select(RfqTransaction)
            .where(RfqTransaction.id_buyer == buyer_id)
            .order_by(RfqTransaction.tanggal_pesanan.desc())
        )
    )


def list_all(db: Session) -> list[RfqTransaction]:
    return list(db.scalars(select(RfqTransaction).order_by(RfqTransaction.tanggal_pesanan.desc())))


def create(db: Session, order: RfqTransaction) -> RfqTransaction:
    db.add(order)
    db.flush()
    return order
