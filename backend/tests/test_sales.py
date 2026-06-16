import pytest
from decimal import Decimal
from pydantic import ValidationError

from app.models.product import Product
from app.models.sale import PaymentMethod
from app.models.stock_movement import MovementType  # noqa: F401


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


# ── service: create_sale ────────────────────────────────────────────────────

def test_create_sale_returns_sale_with_correct_total(db, admin_user):
    from app.services import sale_service
    prod = _make_product(db, precio="10.00")
    sale = sale_service.create_sale(
        db,
        user_id=admin_user.id,
        metodo_pago=PaymentMethod.efectivo,
        items=[{"product_id": prod.id, "cantidad": 2}],
    )
    assert sale.id is not None
    assert sale.total == Decimal("20.00")
    assert sale.user_id == admin_user.id
    assert sale.metodo_pago == PaymentMethod.efectivo


def test_create_sale_snapshots_precio_unitario(db, admin_user):
    from app.services import sale_service
    prod = _make_product(db, precio="7.50")
    sale = sale_service.create_sale(
        db,
        user_id=admin_user.id,
        metodo_pago=PaymentMethod.tarjeta,
        items=[{"product_id": prod.id, "cantidad": 1}],
    )
    assert len(sale.items) == 1
    assert sale.items[0].precio_unitario == Decimal("7.50")
    assert sale.items[0].cantidad == 1


def test_create_sale_decrements_stock(db, admin_user):
    from app.services import sale_service
    prod = _make_product(db, stock=10)
    sale_service.create_sale(
        db,
        user_id=admin_user.id,
        metodo_pago=PaymentMethod.tarjeta,
        items=[{"product_id": prod.id, "cantidad": 3}],
    )
    db.refresh(prod)
    assert prod.stock == 7


def test_create_sale_creates_stock_movement(db, admin_user):
    from app.services import sale_service
    prod = _make_product(db)
    sale = sale_service.create_sale(
        db,
        user_id=admin_user.id,
        metodo_pago=PaymentMethod.bizum,
        items=[{"product_id": prod.id, "cantidad": 5}],
    )
    db.refresh(prod)
    assert len(prod.stock_movements) == 1
    mov = prod.stock_movements[0]
    assert mov.tipo == MovementType.salida
    assert mov.cantidad == -5
    assert str(sale.id) in mov.motivo


def test_create_sale_multi_item_total(db, admin_user):
    from app.services import sale_service
    p1 = _make_product(db, nombre="A", precio="5.00", stock=10)
    p2 = _make_product(db, nombre="B", precio="3.00", stock=10)
    sale = sale_service.create_sale(
        db,
        user_id=admin_user.id,
        metodo_pago=PaymentMethod.efectivo,
        items=[
            {"product_id": p1.id, "cantidad": 2},
            {"product_id": p2.id, "cantidad": 4},
        ],
    )
    # 2 * 5.00 + 4 * 3.00 = 10.00 + 12.00 = 22.00
    assert sale.total == Decimal("22.00")
    assert len(sale.items) == 2


def test_create_sale_insufficient_stock_raises(db, admin_user):
    from app.services import sale_service
    from app.services.sale_service import InsufficientStockError
    prod = _make_product(db, stock=2)
    with pytest.raises(InsufficientStockError, match="Insufficient stock"):
        sale_service.create_sale(
            db,
            user_id=admin_user.id,
            metodo_pago=PaymentMethod.efectivo,
            items=[{"product_id": prod.id, "cantidad": 5}],
        )


def test_create_sale_insufficient_stock_does_not_modify_db(db, admin_user):
    from app.services import sale_service
    from app.services.sale_service import InsufficientStockError
    prod = _make_product(db, stock=2)
    original_stock = prod.stock
    with pytest.raises(InsufficientStockError):
        sale_service.create_sale(
            db,
            user_id=admin_user.id,
            metodo_pago=PaymentMethod.efectivo,
            items=[{"product_id": prod.id, "cantidad": 99}],
        )
    db.refresh(prod)
    assert prod.stock == original_stock


def test_create_sale_product_not_found_raises(db, admin_user):
    from app.services import sale_service
    from app.services.sale_service import ProductNotFoundError
    with pytest.raises(ProductNotFoundError, match="not found"):
        sale_service.create_sale(
            db,
            user_id=admin_user.id,
            metodo_pago=PaymentMethod.efectivo,
            items=[{"product_id": 99999, "cantidad": 1}],
        )


def test_create_sale_second_item_insufficient_stock_raises(db, admin_user):
    from app.services import sale_service
    from app.services.sale_service import InsufficientStockError
    p1 = _make_product(db, nombre="OK", stock=10)
    p2 = _make_product(db, nombre="Sin stock", stock=1)
    with pytest.raises(InsufficientStockError, match="Insufficient stock"):
        sale_service.create_sale(
            db,
            user_id=admin_user.id,
            metodo_pago=PaymentMethod.efectivo,
            items=[
                {"product_id": p1.id, "cantidad": 2},
                {"product_id": p2.id, "cantidad": 5},
            ],
        )
