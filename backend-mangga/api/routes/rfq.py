from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import require_roles
from crud import rfq
from db.session import get_db
from models.domain_models import Role, User
from schemas.rfq import RfqCreate, RfqResponse
from services.rfq import approve_rfq, create_rfq


router = APIRouter()


@router.post("/", response_model=RfqResponse, status_code=201)
def create_order(
    payload: RfqCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.BUYER_B2B)),
) -> RfqResponse:
    order = create_rfq(db, user.id, payload)
    db.commit()
    db.refresh(order)
    return order


@router.get("/me", response_model=list[RfqResponse])
def get_my_orders(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.BUYER_B2B)),
) -> list[RfqResponse]:
    return rfq.list_for_buyer(db, user.id)


@router.get("/all", response_model=list[RfqResponse])
def get_all_orders(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN_GUDANG)),
) -> list[RfqResponse]:
    return rfq.list_all(db)


@router.put("/{rfq_id}/approve", response_model=RfqResponse)
def approve_order(
    rfq_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(Role.ADMIN_GUDANG)),
) -> RfqResponse:
    order = approve_rfq(db, rfq_id, admin.id)
    db.commit()
    db.refresh(order)
    return order
