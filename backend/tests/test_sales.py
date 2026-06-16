import pytest
from decimal import Decimal
from pydantic import ValidationError

from app.models.product import Product
from app.models.sale import PaymentMethod
from app.models.stock_movement import MovementType


# ── helpers ────────────────────────────────────────────────────────────────

def _make_product(db, nombre="Producto Test", precio="10.00", stock=50):
    """Insert a Product and flush so it's visible in the same session."""
    prod = Product(nombre=nombre, precio=Decimal(precio), stock=stock, stock_minimo=0)
    db.add(prod)
    db.flush()
    return prod


# ── schema tests ────────────────────────────────────────────────────────────

def test_sale_item_create_valid():
    from app.schemas.sale import SaleItemCreate
    item = SaleItemCreate(product_id=1, cantidad=3)
    assert item.product_id == 1
    assert item.cantidad == 3


def test_sale_item_create_rejects_zero_cantidad():
    from app.schemas.sale import SaleItemCreate
    with pytest.raises(ValidationError):
        SaleItemCreate(product_id=1, cantidad=0)


def test_sale_item_create_rejects_negative_cantidad():
    from app.schemas.sale import SaleItemCreate
    with pytest.raises(ValidationError):
        SaleItemCreate(product_id=1, cantidad=-2)


def test_sale_create_valid():
    from app.schemas.sale import SaleCreate, SaleItemCreate
    sc = SaleCreate(
        metodo_pago="efectivo",
        items=[SaleItemCreate(product_id=1, cantidad=2)],
    )
    assert sc.metodo_pago == PaymentMethod.efectivo
    assert len(sc.items) == 1


def test_sale_create_rejects_empty_items():
    from app.schemas.sale import SaleCreate
    with pytest.raises(ValidationError):
        SaleCreate(metodo_pago="efectivo", items=[])
