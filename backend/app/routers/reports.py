from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.report import DailyCloseOut, LowStockProductOut, TopProductOut
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily-close", response_model=DailyCloseOut)
def get_daily_close(
    fecha: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    target = fecha if fecha is not None else date.today()
    return report_service.daily_close(db, target)


@router.get("/low-stock", response_model=list[LowStockProductOut])
def get_low_stock(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return report_service.get_low_stock_products(db)


@router.get("/top-products", response_model=list[TopProductOut])
def get_top_products(
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return report_service.get_top_products(db, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)


@router.get("/restock-csv", response_class=Response)
def get_restock_csv(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    content = report_service.get_restock_csv(db)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=restock.csv"},
    )
