from datetime import date, datetime, time, timezone
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.sale import Sale, SaleItem, PaymentMethod
from app.models.product import Product
from app.schemas.report import DailyCloseOut, PaymentBreakdown, LowStockProductOut, TopProductOut


def daily_close(db: Session, fecha: date) -> DailyCloseOut:
    start = datetime.combine(fecha, time.min).replace(tzinfo=timezone.utc)
    end = datetime.combine(fecha, time.max).replace(tzinfo=timezone.utc)
    sales = db.query(Sale).filter(Sale.fecha >= start, Sale.fecha <= end).all()

    total_ventas = sum((s.total for s in sales), Decimal("0"))
    breakdown: dict[str, Decimal] = {m.value: Decimal("0") for m in PaymentMethod}
    for s in sales:
        breakdown[s.metodo_pago.value] += s.total

    return DailyCloseOut(
        fecha=fecha,
        total_ventas=total_ventas,
        num_tickets=len(sales),
        desglose_pago=PaymentBreakdown(**breakdown),
    )
