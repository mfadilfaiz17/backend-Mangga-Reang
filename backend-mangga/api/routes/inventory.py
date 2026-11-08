from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.deps import get_current_user, require_roles
from crud import inventory
from crud.users import get_by_id
from db.session import get_db
from models.domain_models import Grade, Inventory, Role, User, Variety
from schemas.inventory import InventoryCreate, InventoryResponse, InventoryUpdate


router = APIRouter()


@router.get("/", response_model=list[InventoryResponse])
def list_inventory(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    varietas: Variety | None = Query(default=None),
    grade: Grade | None = Query(default=None),
    lokasi: str | None = Query(default=None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
) -> list[InventoryResponse]:
    return inventory.list_public(
        db,
        offset=offset,
        limit=limit,
        varietas=varietas,
        grade=grade,
        lokasi=lokasi,
    )


@router.get("/me", response_model=list[InventoryResponse])
def list_my_inventory(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.PETANI)),
) -> list[InventoryResponse]:
    return inventory.list_owned(db, user.id, offset=offset, limit=limit)


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
    inventory.add_audit(db, item, user.id, "CREATE")
    db.commit()
    db.refresh(item)
    return item


@router.put("/{inventory_id}", response_model=InventoryResponse)
def update_inventory(
    inventory_id: int,
    payload: InventoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.PETANI, Role.ADMIN_GUDANG)),
) -> InventoryResponse:
    item = inventory.get(db, inventory_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory not found")
    if user.role is not Role.ADMIN_GUDANG and item.id_petani != user.id:
        raise HTTPException(status_code=403, detail="Cannot update this inventory")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    inventory.add_audit(db, item, user.id, "UPDATE")
    db.commit()
    db.refresh(item)
    return item
