from decimal import Decimal
import pytest
from app.models.product import Product
from app.models.sale import PaymentMethod


# ── helpers ─────────────────────────────────────────────────────────────────

def _make_product(db, nombre="Prod", precio="10.00", stock=50, stock_minimo=5):
    prod = Product(
        nombre=nombre,
        precio=Decimal(precio),
        stock=stock,
        stock_minimo=stock_minimo,
    )
    db.add(prod)
    db.flush()
    return prod


def _make_sale(db, user_id, metodo_pago, items):
    """items: list of (product, cantidad)"""
    from app.services import sale_service
    return sale_service.create_sale(
        db,
        user_id=user_id,
        metodo_pago=metodo_pago,
        items=[{"product_id": p.id, "cantidad": q} for p, q in items],
    )


# ── daily_close ──────────────────────────────────────────────────────────────

def test_daily_close_no_sales_returns_zeros(db):
    from datetime import date
    from app.services.report_service import daily_close
    result = daily_close(db, date.today())
    assert result.num_tickets == 0
    assert result.total_ventas == Decimal("0")
    assert result.desglose_pago.efectivo == Decimal("0")
    assert result.desglose_pago.tarjeta == Decimal("0")
    assert result.desglose_pago.bizum == Decimal("0")
    assert result.desglose_pago.otro == Decimal("0")


def test_daily_close_counts_todays_sales(db, admin_user):
    from datetime import date
    from app.services.report_service import daily_close
    prod = _make_product(db, precio="10.00", stock=100)
    _make_sale(db, admin_user.id, PaymentMethod.efectivo, [(prod, 2)])   # 20.00
    _make_sale(db, admin_user.id, PaymentMethod.tarjeta, [(prod, 1)])    # 10.00
    result = daily_close(db, date.today())
    assert result.num_tickets == 2
    assert result.total_ventas == Decimal("30.00")


def test_daily_close_desglose_por_metodo_pago(db, admin_user):
    from datetime import date
    from app.services.report_service import daily_close
    prod = _make_product(db, precio="5.00", stock=100)
    _make_sale(db, admin_user.id, PaymentMethod.efectivo, [(prod, 2)])   # 10.00
    _make_sale(db, admin_user.id, PaymentMethod.tarjeta, [(prod, 3)])    # 15.00
    _make_sale(db, admin_user.id, PaymentMethod.bizum, [(prod, 1)])      # 5.00
    result = daily_close(db, date.today())
    assert result.desglose_pago.efectivo == Decimal("10.00")
    assert result.desglose_pago.tarjeta == Decimal("15.00")
    assert result.desglose_pago.bizum == Decimal("5.00")
    assert result.desglose_pago.otro == Decimal("0")


def test_daily_close_excludes_other_days(db, admin_user):
    from datetime import date, datetime, timedelta, UTC
    from app.services.report_service import daily_close
    prod = _make_product(db, stock=100)
    sale = _make_sale(db, admin_user.id, PaymentMethod.efectivo, [(prod, 1)])
    sale.fecha = datetime.now(UTC) - timedelta(days=1)
    db.commit()
    result = daily_close(db, date.today())
    assert result.num_tickets == 0
    assert result.total_ventas == Decimal("0")


# ── get_low_stock_products ───────────────────────────────────────────────────

def test_low_stock_empty_when_all_above_min(db):
    from app.services.report_service import get_low_stock_products
    _make_product(db, stock=10, stock_minimo=5)
    result = get_low_stock_products(db)
    assert result == []


def test_low_stock_returns_product_below_min(db):
    from app.services.report_service import get_low_stock_products
    prod = _make_product(db, nombre="Crítico", stock=3, stock_minimo=10)
    result = get_low_stock_products(db)
    assert len(result) == 1
    assert result[0].id == prod.id
    assert result[0].stock == 3
    assert result[0].stock_minimo == 10


def test_low_stock_excludes_product_at_exact_minimum(db):
    from app.services.report_service import get_low_stock_products
    _make_product(db, stock=5, stock_minimo=5)
    result = get_low_stock_products(db)
    assert result == []


def test_low_stock_multiple_only_returns_below_min(db):
    from app.services.report_service import get_low_stock_products
    p_low = _make_product(db, nombre="Low", stock=2, stock_minimo=10)
    _make_product(db, nombre="OK", stock=20, stock_minimo=10)
    _make_product(db, nombre="Exact", stock=10, stock_minimo=10)
    result = get_low_stock_products(db)
    assert len(result) == 1
    assert result[0].id == p_low.id


# ── get_top_products ─────────────────────────────────────────────────────────

def test_top_products_no_sales_returns_empty(db):
    from app.services.report_service import get_top_products
    result = get_top_products(db)
    assert result == []


def test_top_products_sorted_by_quantity_desc(db, admin_user):
    from app.services.report_service import get_top_products
    p1 = _make_product(db, nombre="A", stock=100)
    p2 = _make_product(db, nombre="B", stock=100)
    _make_sale(db, admin_user.id, PaymentMethod.efectivo, [(p1, 3), (p2, 7)])
    result = get_top_products(db)
    assert len(result) == 2
    assert result[0].product_id == p2.id   # 7 units — top
    assert result[1].product_id == p1.id   # 3 units


def test_top_products_calculates_total_importe(db, admin_user):
    from app.services.report_service import get_top_products
    prod = _make_product(db, precio="5.00", stock=100)
    _make_sale(db, admin_user.id, PaymentMethod.efectivo, [(prod, 4)])  # 4 × 5.00 = 20.00
    result = get_top_products(db)
    assert len(result) == 1
    assert result[0].total_cantidad == 4
    assert result[0].total_importe == Decimal("20.00")


def test_top_products_aggregates_across_multiple_sales(db, admin_user):
    from app.services.report_service import get_top_products
    prod = _make_product(db, precio="3.00", stock=100)
    _make_sale(db, admin_user.id, PaymentMethod.efectivo, [(prod, 2)])
    _make_sale(db, admin_user.id, PaymentMethod.tarjeta, [(prod, 5)])
    result = get_top_products(db)
    assert len(result) == 1
    assert result[0].total_cantidad == 7
    assert result[0].total_importe == Decimal("21.00")


def test_top_products_fecha_desde_excludes_older_sales(db, admin_user):
    from datetime import date, datetime, timedelta, UTC
    from app.services.report_service import get_top_products
    prod = _make_product(db, stock=100)
    sale = _make_sale(db, admin_user.id, PaymentMethod.efectivo, [(prod, 2)])
    sale.fecha = datetime.now(UTC) - timedelta(days=10)
    db.commit()
    fecha_desde = date.today() - timedelta(days=3)
    result = get_top_products(db, fecha_desde=fecha_desde)
    assert result == []


def test_top_products_fecha_hasta_excludes_future_sales(db, admin_user):
    from datetime import date, datetime, timedelta, UTC
    from app.services.report_service import get_top_products
    prod = _make_product(db, stock=100)
    sale = _make_sale(db, admin_user.id, PaymentMethod.efectivo, [(prod, 2)])
    sale.fecha = datetime.now(UTC) + timedelta(days=5)
    db.commit()
    fecha_hasta = date.today()
    result = get_top_products(db, fecha_hasta=fecha_hasta)
    assert result == []


# ── API: GET /reports/daily-close ────────────────────────────────────────────

def test_daily_close_requires_auth(client):
    resp = client.get("/reports/daily-close")
    assert resp.status_code == 401


def test_daily_close_api_default_is_today(client, admin_headers):
    from datetime import date
    resp = client.get("/reports/daily-close", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["fecha"] == date.today().isoformat()
    assert data["num_tickets"] == 0
    assert Decimal(data["total_ventas"]) == Decimal("0")


def test_daily_close_api_accepts_fecha_param(client, admin_headers):
    resp = client.get("/reports/daily-close?fecha=2024-03-15", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["fecha"] == "2024-03-15"
    assert data["num_tickets"] == 0


def test_daily_close_api_response_includes_desglose(client, admin_headers, db):
    prod = _make_product(db, precio="20.00", stock=100)
    client.post(
        "/sales",
        json={"metodo_pago": "tarjeta", "items": [{"product_id": prod.id, "cantidad": 1}]},
        headers=admin_headers,
    )
    resp = client.get("/reports/daily-close", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["num_tickets"] == 1
    assert data["total_ventas"] == "20.00"
    assert data["desglose_pago"]["tarjeta"] == "20.00"
    assert Decimal(data["desglose_pago"]["efectivo"]) == Decimal("0")


# ── API: GET /reports/low-stock ──────────────────────────────────────────────

def test_low_stock_requires_auth(client):
    resp = client.get("/reports/low-stock")
    assert resp.status_code == 401


def test_low_stock_api_returns_empty_list(client, admin_headers):
    resp = client.get("/reports/low-stock", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_low_stock_api_returns_low_stock_products(client, admin_headers, db):
    _make_product(db, nombre="Crítico", stock=1, stock_minimo=10)
    _make_product(db, nombre="OK", stock=20, stock_minimo=5)
    resp = client.get("/reports/low-stock", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["nombre"] == "Crítico"
    assert data[0]["stock"] == 1
    assert data[0]["stock_minimo"] == 10


# ── API: GET /reports/top-products ───────────────────────────────────────────

def test_top_products_requires_auth(client):
    resp = client.get("/reports/top-products")
    assert resp.status_code == 401


def test_top_products_api_returns_empty_when_no_sales(client, admin_headers):
    resp = client.get("/reports/top-products", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_top_products_api_returns_sorted_products(client, admin_headers, db):
    p1 = _make_product(db, nombre="Poco", stock=100)
    p2 = _make_product(db, nombre="Mucho", stock=100)
    client.post(
        "/sales",
        json={
            "metodo_pago": "efectivo",
            "items": [
                {"product_id": p1.id, "cantidad": 2},
                {"product_id": p2.id, "cantidad": 8},
            ],
        },
        headers=admin_headers,
    )
    resp = client.get("/reports/top-products", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["product_id"] == p2.id   # 8 units first
    assert data[0]["total_cantidad"] == 8
    assert data[1]["product_id"] == p1.id


def test_top_products_api_date_filter(client, admin_headers, db):
    from datetime import date, timedelta
    prod = _make_product(db, stock=100)
    client.post(
        "/sales",
        json={"metodo_pago": "efectivo", "items": [{"product_id": prod.id, "cantidad": 3}]},
        headers=admin_headers,
    )
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    resp = client.get(f"/reports/top-products?fecha_hasta={yesterday}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json() == []


# ── get_restock_csv ──────────────────────────────────────────────────────────

def test_restock_csv_only_header_when_no_low_stock(db):
    import csv, io
    from app.services.report_service import get_restock_csv
    _make_product(db, nombre="OK", stock=20, stock_minimo=10)
    content = get_restock_csv(db)
    lines = content.strip().splitlines()
    assert len(lines) == 1
    assert lines[0] == "nombre,stock_actual,stock_minimo,cantidad_sugerida"


def test_restock_csv_excludes_products_at_or_above_min(db):
    import csv, io
    from app.services.report_service import get_restock_csv
    _make_product(db, nombre="Bajo", stock=3, stock_minimo=10)
    _make_product(db, nombre="Justo", stock=10, stock_minimo=10)
    _make_product(db, nombre="Bien", stock=20, stock_minimo=10)
    content = get_restock_csv(db)
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["nombre"] == "Bajo"


def test_restock_csv_calculates_cantidad_sugerida(db):
    import csv, io
    from app.services.report_service import get_restock_csv
    # stock=3, stock_minimo=10 → cantidad_sugerida = 10*2 - 3 = 17
    _make_product(db, nombre="Leche", stock=3, stock_minimo=10)
    content = get_restock_csv(db)
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    assert rows[0]["nombre"] == "Leche"
    assert int(rows[0]["stock_actual"]) == 3
    assert int(rows[0]["stock_minimo"]) == 10
    assert int(rows[0]["cantidad_sugerida"]) == 17


# ── API: GET /reports/restock-csv ────────────────────────────────────────────

def test_restock_csv_requires_auth(client):
    resp = client.get("/reports/restock-csv")
    assert resp.status_code == 401


def test_restock_csv_api_only_header_row_when_no_low_stock(client, admin_headers):
    resp = client.get("/reports/restock-csv", headers=admin_headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    lines = resp.text.strip().splitlines()
    assert len(lines) == 1
    assert lines[0] == "nombre,stock_actual,stock_minimo,cantidad_sugerida"


def test_restock_csv_api_contains_low_stock_rows(client, admin_headers, db):
    # stock=1, stock_minimo=10 → cantidad_sugerida = 10*2 - 1 = 19
    _make_product(db, nombre="Crítico", stock=1, stock_minimo=10)
    _make_product(db, nombre="OK", stock=20, stock_minimo=10)
    resp = client.get("/reports/restock-csv", headers=admin_headers)
    assert resp.status_code == 200
    lines = resp.text.strip().splitlines()
    assert len(lines) == 2   # header + 1 product
    assert "Crítico" in lines[1]
    assert "1" in lines[1]
    assert "10" in lines[1]
    assert "19" in lines[1]  # cantidad_sugerida
    assert "content-disposition" in resp.headers
    assert "attachment" in resp.headers["content-disposition"]
