from sqlalchemy import select
from sqlalchemy.orm import Session
from models.domain_models import Grade, Inventory, InventoryAudit, Variety


def list_public(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 50,
    varietas: Variety | None = None,
    grade: Grade | None = None,
    lokasi: str | None = None,
) -> list[Inventory]:
    query = select(Inventory).where(
        Inventory.is_active.is_(True),
        Inventory.tonase_tersedia > 0,
    )
    if varietas is not None:
        query = query.where(Inventory.varietas == varietas)
    if grade is not None:
        query = query.where(Inventory.grade == grade)
    if lokasi:
        query = query.where(Inventory.lokasi_kebun.ilike(f"%{lokasi}%"))
    return list(db.scalars(query.order_by(Inventory.id).offset(offset).limit(limit)))


def get(db: Session, inventory_id: int, *, for_update: bool = False) -> Inventory | None:
    query = select(Inventory).where(Inventory.id == inventory_id)
    if for_update:
        query = query.with_for_update()
    return db.scalar(query)


def list_owned(db: Session, farmer_id: int, *, offset: int = 0, limit: int = 100) -> list[Inventory]:
    return list(
        db.scalars(
            select(Inventory)
            .where(Inventory.id_petani == farmer_id)
            .order_by(Inventory.id)
            .offset(offset)
            .limit(limit)
        )
    )


def add_audit(db: Session, item: Inventory, actor_id: int, action: str) -> None:
    db.add(
        InventoryAudit(
            inventory_id=item.id,
            actor_id=actor_id,
            action=action,
            tonase_tersedia=item.tonase_tersedia,
            harga_per_ton=item.harga_per_ton,
            is_active=item.is_active,
        )
    )


def create(db: Session, item: Inventory) -> Inventory:
    db.add(item)
    db.flush()
    return item
