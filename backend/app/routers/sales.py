from datetime import date as DateType

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.sale import SaleCreate, SaleListOut, SaleOut
from app.services import sale_service
from app.services.sale_service import InsufficientStockError, ProductNotFoundError

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("", response_model=SaleOut, status_code=status.HTTP_201_CREATED)
def create_sale(
    payload: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return sale_service.create_sale(
            db,
            user_id=current_user.id,
            metodo_pago=payload.metodo_pago,
            items=[item.model_dump() for item in payload.items],
        )
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InsufficientStockError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("", response_model=list[SaleListOut])
def list_sales(
    fecha_inicio: DateType | None = None,
    fecha_fin: DateType | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return sale_service.get_sales(db, fecha_inicio, fecha_fin)


@router.get("/{sale_id}", response_model=SaleOut)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    sale = sale_service.get_sale(db, sale_id)
    if sale is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
    return sale
