from datetime import date, datetime, time, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.sale import Sale, SaleItem, PaymentMethod
from app.models.stock_movement import StockMovement, MovementType


class ProductNotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


def create_sale(
    db: Session,
    user_id: int,
    metodo_pago: PaymentMethod,
    items: list[dict],
) -> Sale:
    # Phase 1: validate — collect all products before touching anything
    line_data: list[tuple[Product, int]] = []
    for item in items:
        product = db.query(Product).filter(Product.id == item["product_id"]).first()
        if product is None:
            raise ProductNotFoundError(f"Product {item['product_id']} not found")
        if product.stock < item["cantidad"]:
            raise InsufficientStockError(
                f"Insufficient stock for '{product.nombre}': "
                f"available {product.stock}, requested {item['cantidad']}"
            )
        line_data.append((product, item["cantidad"]))

    # Phase 2: create sale header
    total = sum(p.precio * Decimal(str(q)) for p, q in line_data)
    sale = Sale(total=total, metodo_pago=metodo_pago, user_id=user_id)
    db.add(sale)
    db.flush()  # populate sale.id before creating items

    # Phase 3: create items, deduct stock, log movements
    for product, cantidad in line_data:
        db.add(SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            cantidad=cantidad,
            precio_unitario=product.precio,
        ))
        product.stock -= cantidad
        db.add(StockMovement(
            product_id=product.id,
            cantidad=-cantidad,
            tipo=MovementType.salida,
            motivo=f"Venta #{sale.id}",
        ))

    db.commit()
    db.refresh(sale)
    return sale


def get_sales(
    db: Session,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
) -> list[Sale]:
    q = db.query(Sale)
    if fecha_inicio is not None:
        q = q.filter(
            Sale.fecha >= datetime.combine(fecha_inicio, time.min).replace(tzinfo=timezone.utc)
        )
    if fecha_fin is not None:
        q = q.filter(
            Sale.fecha <= datetime.combine(fecha_fin, time.max).replace(tzinfo=timezone.utc)
        )
    return q.order_by(Sale.fecha.desc()).all()


def get_sale(db: Session, sale_id: int) -> Sale | None:
    return db.query(Sale).filter(Sale.id == sale_id).first()
