from sqlalchemy import select
from sqlalchemy.orm import Session

from models.domain_models import Inventory


def list_public(db: Session) -> list[Inventory]:
    return list(
        db.scalars(
            select(Inventory)
            .where(Inventory.is_active.is_(True), Inventory.tonase_tersedia > 0)
            .order_by(Inventory.id)
        )
    )


def get(db: Session, inventory_id: int, *, for_update: bool = False) -> Inventory | None:
    query = select(Inventory).where(Inventory.id == inventory_id)
    if for_update:
        query = query.with_for_update()
    return db.scalar(query)


def create(db: Session, item: Inventory) -> Inventory:
    db.add(item)
    db.flush()
    return item
