from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import get_current_user, require_roles
from crud import inventory
from crud.users import get_by_id
from db.session import get_db
from models.domain_models import Inventory, Role, User
from schemas.inventory import InventoryCreate, InventoryResponse, InventoryUpdate


router = APIRouter()


@router.get("/", response_model=list[InventoryResponse])
def list_inventory(db: Session = Depends(get_db)) -> list[InventoryResponse]:
    return inventory.list_public(db)


@router.post("/", response_model=InventoryResponse, status_code=201)
def create_inventory(
    payload: InventoryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.PETANI, Role.ADMIN_GUDANG)),
) -> InventoryResponse:
    farmer_id = payload.id_petani if user.role is Role.ADMIN_GUDANG and payload.id_petani else user.id
    if farmer_id != user.id and user.role is not Role.ADMIN_GUDANG:
        raise HTTPException(status_code=403, detail="Cannot assign inventory to another farmer")
    farmer = get_by_id(db, farmer_id)
    if farmer is None or farmer.role is not Role.PETANI:
        raise HTTPException(status_code=422, detail="Inventory owner must be an existing farmer")
    item = inventory.create(
        db,
        Inventory(
            id_petani=farmer_id,
            varietas=payload.varietas,
            grade=payload.grade,
            tonase_tersedia=payload.tonase_tersedia,
            harga_per_ton=payload.harga_per_ton,
            lokasi_kebun=payload.lokasi_kebun,
        ),
    )
    db.commit()
    db.refresh(item)
    return item


@router.put("/{inventory_id}", response_model=InventoryResponse)
def update_inventory(
    inventory_id: int,
    payload: InventoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InventoryResponse:
    item = inventory.get(db, inventory_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory not found")
    if user.role is not Role.ADMIN_GUDANG and item.id_petani != user.id:
        raise HTTPException(status_code=403, detail="Cannot update this inventory")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item
