import csv
import io
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


def get_low_stock_products(db: Session) -> list[LowStockProductOut]:
    products = (
        db.query(Product)
        .filter(Product.stock < Product.stock_minimo)
        .order_by(Product.nombre)
        .all()
    )
    return [LowStockProductOut.model_validate(p) for p in products]


def get_top_products(
    db: Session,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
) -> list[TopProductOut]:
    q = (
        db.query(
            SaleItem.product_id,
            Product.nombre,
            func.sum(SaleItem.cantidad).label("total_cantidad"),
            func.sum(SaleItem.cantidad * SaleItem.precio_unitario).label("total_importe"),
        )
        .join(Product, SaleItem.product_id == Product.id)
        .join(Sale, SaleItem.sale_id == Sale.id)
    )
    if fecha_desde is not None:
        q = q.filter(
            Sale.fecha >= datetime.combine(fecha_desde, time.min).replace(tzinfo=timezone.utc)
        )
    if fecha_hasta is not None:
        q = q.filter(
            Sale.fecha <= datetime.combine(fecha_hasta, time.max).replace(tzinfo=timezone.utc)
        )
    rows = (
        q.group_by(SaleItem.product_id, Product.nombre)
        .order_by(func.sum(SaleItem.cantidad).desc())
        .all()
    )
    return [
        TopProductOut(
            product_id=row.product_id,
            nombre=row.nombre,
            total_cantidad=row.total_cantidad,
            total_importe=row.total_importe,
        )
        for row in rows
    ]


def get_restock_csv(db: Session) -> str:
    products = (
        db.query(Product)
        .filter(Product.stock < Product.stock_minimo)
        .order_by(Product.nombre)
        .all()
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["nombre", "stock_actual", "stock_minimo", "cantidad_sugerida"])
    for p in products:
        cantidad_sugerida = p.stock_minimo * 2 - p.stock
        writer.writerow([p.nombre, p.stock, p.stock_minimo, cantidad_sugerida])
    return output.getvalue()
